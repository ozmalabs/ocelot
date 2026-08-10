"""context_invariant_librispeech_accept — link-2 (context/coarticulation) on
continuous speech. Does CMVN+context handling push the forward chunker further
than CMVN-only?

Mirrors invariant_units_librispeech_accept exactly (same framing, same codebook
protocol, same chunker, same boundary-F1), adding a THIRD frame variant:
    raw  ->  CMVN  ->  CMVN + context-norm (the agent's composed ctxnorm Term).
Everything downstream is held FIXED; the only changed variable is the frame
features. Honest isolation.

Also measures CROSS-CONTEXT UNIT INVARIANCE: for the SAME quantized unit, how much
does its frame vector vary as a function of its NEIGHBOUR units (the left/right
context)? Lower across-context variance = the unit clusters the same regardless of
context = coarticulation removed. Reported raw vs CMVN vs CMVN+context.

Run: python -m scripts.context_invariant_librispeech_accept [n_utts] [n_speakers] [K] [window]
"""
import os
import re
import sys
import time
import random
import numpy as np
from collections import defaultdict

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.sentence_learning as SL
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import cmvn, canonical_log_centroid
from domains.context_invariant_units import apply_context_norm
from domains.forward_segmentation import forward_segment, estimate_tp
from substrate_rs import Substrate


def words_of(t):
    return [w for w in re.findall(r"[\w']+", t.lower()) if w]


def frames_of(x, fs, hop_frames=64):
    n = max(8, min(hop_frames, int(len(x) / fs * 50)))
    return band_trajectory_matrix(x, fs, n_frames=n)


def kmeans(X, K, iters=15, seed=0):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X), size=min(K, len(X)), replace=False)
    C = X[idx].copy()
    for _ in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(2)
        a = d.argmin(1)
        newC = np.array([X[a == k].mean(0) if (a == k).any() else C[k]
                         for k in range(len(C))])
        if np.allclose(newC, C):
            C = newC
            break
        C = newC
    return C


def quantize(M, C):
    d = ((M[:, None, :] - C[None, :, :]) ** 2).sum(2)
    return list(d.argmin(1))


def tp_within_across(unit_seqs, time_seqs, word_seqs, span_seqs):
    tp = estimate_tp(unit_seqs)
    within, across = [], []
    for seq, times, words, (ts, te) in zip(unit_seqs, time_seqs, word_seqs,
                                           span_seqs):
        if te <= ts or not words:
            continue
        lens = [len(w) + 1 for w in words]
        tot = sum(lens)
        ends, acc = [], 0
        for L in lens:
            acc += L
            ends.append(ts + (te - ts) * acc / tot)
        def wid(t):
            wi = 0
            while wi < len(ends) - 1 and t > ends[wi]:
                wi += 1
            return wi
        for i in range(len(seq) - 1):
            p = tp.get((seq[i], seq[i + 1]), 0.0)
            (within if wid(times[i]) == wid(times[i + 1]) else across).append(p)
    mw = float(np.median(within)) if within else 0.0
    ma = float(np.median(across)) if across else 0.0
    return mw, ma, len(within), len(across)


def proportional_word_boundaries(words, t0, t1):
    if not words or t1 <= t0:
        return []
    lens = [len(w) + 1 for w in words]
    tot = sum(lens)
    b, acc = [], 0
    for L in lens[:-1]:
        acc += L
        b.append(t0 + (t1 - t0) * acc / tot)
    return b


def chunk_boundary_times(times, chunk_lengths):
    b, idx = [], 0
    for L in chunk_lengths[:-1]:
        idx += L
        if idx < len(times):
            b.append(times[idx])
    return b


def boundary_f1(pred, true, tol):
    if not pred and not true:
        return 1.0, 1.0, 1.0
    used = [False] * len(true)
    hits = 0
    for pt in pred:
        bj, bd = -1, tol
        for j, tt in enumerate(true):
            if used[j]:
                continue
            d = abs(pt - tt)
            if d <= bd:
                bd, bj = d, j
        if bj >= 0:
            used[bj] = True
            hits += 1
    prec = hits / len(pred) if pred else 0.0
    rec = hits / len(true) if true else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def flat_len(c):
    return sum(flat_len(x) for x in c) if isinstance(c, tuple) else 1


def chunk_to_word_purity(unit_seqs, time_seqs, word_seqs, span_seqs, chunked):
    """Each constructed chunk spans a time interval; the word that interval mostly
    overlaps is its 'majority word'. Purity = fraction of chunks whose span lands
    predominantly inside ONE transcript word (proportional alignment). A proxy for
    chunk->word agreement when no phone alignment exists."""
    pure, total = 0, 0
    for seq, times, words, (ts, te), chunks in zip(
            unit_seqs, time_seqs, word_seqs, span_seqs, chunked):
        if te <= ts or not words:
            continue
        ends = proportional_word_boundaries(words, ts, te) + [te]
        def wid(t):
            wi = 0
            while wi < len(ends) - 1 and t > ends[wi]:
                wi += 1
            return wi
        idx = 0
        for c in chunks:
            L = flat_len(c)
            if idx >= len(times):
                break
            t_start = times[idx]
            t_end = times[min(idx + L - 1, len(times) - 1)]
            # chunk is "pure" if its start and end fall in the same word
            if wid(t_start) == wid(t_end):
                pure += 1
            total += 1
            idx += L
    return pure / total if total else 0.0


def cross_context_invariance(frame_seqs, unit_seqs):
    """For each unit symbol, group its frame vectors by LEFT-neighbour context;
    measure how much the unit's mean vector varies ACROSS those contexts vs WITHIN
    a context. Returns the ratio of across-context spread to within-context spread
    (lower = more context-invariant: the unit looks the same whatever sits beside
    it). Also returns the raw across-context spread (mean L2 dispersion of
    per-context means around the unit's grand mean)."""
    # collect frame vectors per (unit, left-context unit)
    by_unit_ctx = defaultdict(lambda: defaultdict(list))
    by_unit_all = defaultdict(list)
    for M, seq in zip(frame_seqs, unit_seqs):
        for i in range(1, len(seq)):
            u = seq[i]
            left = seq[i - 1]
            by_unit_ctx[u][left].append(M[i])
            by_unit_all[u].append(M[i])
    across_spreads, within_spreads = [], []
    for u, all_vecs in by_unit_all.items():
        ctxs = by_unit_ctx[u]
        # need >= 2 distinct contexts each with >= 2 samples for a fair ratio
        usable = {c: np.array(v) for c, v in ctxs.items() if len(v) >= 2}
        if len(usable) < 2:
            continue
        grand = np.mean(np.array(all_vecs), axis=0)
        ctx_means = np.array([v.mean(axis=0) for v in usable.values()])
        # across: dispersion of per-context means around the grand mean
        across = float(np.mean(np.linalg.norm(ctx_means - grand, axis=1)))
        # within: mean dispersion of samples around their own context mean
        within = float(np.mean([
            np.mean(np.linalg.norm(v - v.mean(axis=0), axis=1)) for v in usable.values()
        ]))
        across_spreads.append(across)
        within_spreads.append(within)
    if not across_spreads:
        return {"across": 0.0, "within": 0.0, "ratio": 0.0, "n_units": 0}
    a = float(np.mean(across_spreads))
    w = float(np.mean(within_spreads))
    return {"across": a, "within": w, "ratio": a / (w + 1e-9),
            "n_units": len(across_spreads)}


def run_variant(tag, frame_seqs, time_seqs, word_seqs, span_seqs, C, sub,
                tol=0.06):
    unit_seqs = [quantize(M, C) for M in frame_seqs]
    mw, ma, nw, na = tp_within_across(unit_seqs, time_seqs, word_seqs, span_seqs)
    res = forward_segment(sub, unit_seqs, n_passes=1)
    chunked = res["chunked"]
    if chunked is None:
        chunked = [[(u,) for u in s] for s in unit_seqs]
    rf = cf = 0.0
    n = 0
    for seq, times, words, (ts, te), chunks in zip(
            unit_seqs, time_seqs, word_seqs, span_seqs, chunked):
        true_b = proportional_word_boundaries(words, ts, te)
        raw_b = chunk_boundary_times(times, [1] * len(seq))
        con_b = chunk_boundary_times(times, [flat_len(c) for c in chunks])
        rf += boundary_f1(raw_b, true_b, tol)[2]
        cf += boundary_f1(con_b, true_b, tol)[2]
        n += 1
    n = max(n, 1)
    purity = chunk_to_word_purity(unit_seqs, time_seqs, word_seqs, span_seqs,
                                  chunked)
    inv = cross_context_invariance(frame_seqs, unit_seqs)
    print(f"\n--- {tag} ---")
    print(f"  TP within-word median = {mw:.4f}  ({nw} pairs)")
    print(f"  TP across-word median = {ma:.4f}  ({na} pairs)")
    print(f"  TP separation (within - across) = {mw - ma:+.4f}")
    print(f"  chunker boundary F1 = {cf / n:.3f}  "
          f"(raw-unit boundary F1 {rf / n:.3f})")
    print(f"  chunk->word purity  = {purity:.3f}")
    print(f"  cross-context unit invariance: across/within spread = "
          f"{inv['ratio']:.3f}  (across {inv['across']:.4f}, within "
          f"{inv['within']:.4f}, {inv['n_units']} units)")
    return {"tag": tag, "sep": mw - ma, "f1": cf / n, "purity": purity,
            "ctx_ratio": inv["ratio"], "ctx_across": inv["across"]}


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 48
    window = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    random.seed(1)

    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    sel = [p for p in pairs if p[1] in speakers]
    random.shuffle(sel)
    sel = sel[:n_utts]
    print(f"LibriSpeech dev-clean: {len(sel)} utts, "
          f"{len(set(p[1] for p in sel))} speakers, K={K} units, "
          f"context window=+-{window} frames")

    frame_seqs, time_seqs, word_seqs, span_seqs = [], [], [], []
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(sel):
        words = words_of(transcript)
        if not words:
            continue
        try:
            x, fs = SL.load_flac_8k(path)
        except Exception:
            continue
        M = frames_of(x, fs)
        if M.shape[0] < 4:
            continue
        dur = len(x) / fs
        times = [dur * k / M.shape[0] for k in range(M.shape[0])]
        frame_seqs.append(M)
        time_seqs.append(times)
        word_seqs.append(words)
        span_seqs.append((times[0], times[-1]))
        if (i + 1) % 30 == 0:
            print(f"  framed {i+1}/{len(sel)}  ({time.time()-t0:.0f}s)",
                  flush=True)
    print(f"Framed {len(frame_seqs)} utts in {time.time()-t0:.0f}s")
    if len(frame_seqs) < 4:
        print("Too few utterances.")
        return

    # Build the three frame variants.
    raw_frames = frame_seqs
    cmvn_frames = [cmvn(M, do_variance=True) for M in frame_seqs]
    # CMVN then the agent's composed context-norm Term (link-1 then link-2).
    print("Applying agent's composed context-norm Term-tree (native eval) ...",
          flush=True)
    tc = time.time()
    ctx_frames = [apply_context_norm(M, window=window) for M in cmvn_frames]
    print(f"  context-norm applied to {len(ctx_frames)} utts "
          f"in {time.time()-tc:.0f}s")

    def codebook(framelist):
        pool = np.concatenate(framelist, axis=0)
        if len(pool) > 8000:
            pool = pool[np.random.default_rng(0).choice(len(pool), 8000,
                                                        replace=False)]
        return kmeans(pool, K, seed=0)

    sub = Substrate()
    print("\n========= CHUNKER F1 + PURITY + CROSS-CONTEXT INVARIANCE "
          "(raw vs CMVN vs CMVN+context) =========")
    r = run_variant("RAW units (no norm)", raw_frames, time_seqs,
                    word_seqs, span_seqs, codebook(raw_frames), sub)
    c = run_variant("CMVN units", cmvn_frames, time_seqs,
                    word_seqs, span_seqs, codebook(cmvn_frames), sub)
    x = run_variant("CMVN + context units", ctx_frames, time_seqs,
                    word_seqs, span_seqs, codebook(ctx_frames), sub)

    print("\n================= SUMMARY =================")
    print(f"{'variant':24s}{'F1':>8s}{'purity':>9s}{'TP-sep':>10s}"
          f"{'ctx across/within':>20s}")
    for row in (r, c, x):
        print(f"{row['tag']:24s}{row['f1']:>8.3f}{row['purity']:>9.3f}"
              f"{row['sep']:>+10.4f}{row['ctx_ratio']:>20.3f}")
    print(f"\nChunker F1 : CMVN {c['f1']:.3f} -> CMVN+context {x['f1']:.3f}  "
          f"(Δ {x['f1'] - c['f1']:+.3f})")
    print(f"Purity     : CMVN {c['purity']:.3f} -> CMVN+context {x['purity']:.3f}"
          f"  (Δ {x['purity'] - c['purity']:+.3f})")
    print(f"Cross-context invariance (lower=better): "
          f"CMVN {c['ctx_ratio']:.3f} -> CMVN+context {x['ctx_ratio']:.3f}  "
          f"(Δ {x['ctx_ratio'] - c['ctx_ratio']:+.3f})")
    better = x['f1'] > c['f1'] + 1e-6
    print(f"\nVERDICT: context handling {'ADVANCES' if better else 'does NOT advance'}"
          f" link-2 on chunker F1 "
          f"({'+' if better else ''}{x['f1'] - c['f1']:+.3f} over CMVN-only).")


if __name__ == "__main__":
    main()
