"""invariant_units_librispeech_accept — criteria 2 & 3 on continuous speech.

Does normalizing the agent's per-frame units with CMVN(+VTLN), mined from Kaldi,
produce (2) SHARPER transitional-probability structure (within-word TP >> across-
word TP) and (3) BETTER forward-chunker word boundaries (F1) than RAW units?

The chunker (domains/forward_segmentation) reads DISCRETE sub-word unit
sequences. So unit FORMATION is the lever: we quantize each per-frame band vector
to a shared codebook (the agent's clustering step). If the frame features are
speaker-normalized (CMVN warps every speaker's spectrum to the canonical mean),
the SAME phone across speakers maps to the SAME unit -> cleaner recurrence ->
sharper TP troughs at real word boundaries. We hold the codebook + chunker FIXED
and swap only RAW vs INVARIANT frame features. Honest isolation of the variable.

Codebook = k-means over a sample of frames (the unsupervised unit inventory,
like HuBERT's k-means clustering). Same K, same seed for raw and invariant; the
only change is whether frames were CMVN-normalized first. No tuning of the
chunker (its level is the running TP median, derived not swept).

Run: python -m scripts.invariant_units_librispeech_accept [n_utts] [n_speakers] [K]
"""
import os
import re
import sys
import time
import math
import random
import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.sentence_learning as SL
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import (cmvn, warp_bands, estimate_vtl_logalpha,
                                     canonical_log_centroid)
from domains.forward_segmentation import forward_segment, estimate_tp
from substrate_rs import Substrate


def words_of(t):
    return [w for w in re.findall(r"[\w']+", t.lower()) if w]


def frames_of(x, fs, hop_frames=64):
    """Per-frame band matrix at a finer time grid (continuous speech needs more
    than 32 frames). Returns frames x bands."""
    n = max(8, min(hop_frames, int(len(x) / fs * 50)))   # ~50 fps, capped
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
    """Within-word vs across-word transitional probability separation. For each
    adjacent unit pair, label it WITHIN (both units in the same proportional
    transcript word) or ACROSS (straddles a word boundary). Compare the TP of
    within-pairs vs across-pairs. A working unit stream has within >> across."""
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


def run_variant(tag, frame_seqs, time_seqs, word_seqs, span_seqs, C, sub,
                tol=0.06):
    unit_seqs = [quantize(M, C) for M in frame_seqs]
    mw, ma, nw, na = tp_within_across(unit_seqs, time_seqs, word_seqs, span_seqs)
    res = forward_segment(sub, unit_seqs, n_passes=1)
    chunked = res["chunked"]
    if chunked is None:               # degenerate TP -> treat each unit as a chunk
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
    print(f"\n--- {tag} ---")
    print(f"  TP within-word median = {mw:.4f}  ({nw} pairs)")
    print(f"  TP across-word median = {ma:.4f}  ({na} pairs)")
    print(f"  TP separation (within - across) = {mw - ma:+.4f}  "
          f"(ratio {mw / (ma + 1e-9):.2f}x)")
    print(f"  chunker boundary F1 = {cf / n:.3f}  (raw-unit boundary F1 "
          f"{rf / n:.3f})")
    return mw - ma, cf / n


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 48
    random.seed(1)

    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    sel = [p for p in pairs if p[1] in speakers]
    random.shuffle(sel)
    sel = sel[:n_utts]
    print(f"LibriSpeech dev-clean: {len(sel)} utts, "
          f"{len(set(p[1] for p in sel))} speakers, K={K} units")

    frame_seqs = []
    time_seqs = []
    word_seqs = []
    span_seqs = []
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
        # per-frame times along the utterance
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

    canonical = canonical_log_centroid(frame_seqs)

    # Build the INVARIANT frame sets.
    def to_inv(M, do_vtln=False):
        out = M
        if do_vtln:
            out = warp_bands(out, estimate_vtl_logalpha(out, canonical))
        return cmvn(out, do_variance=True)
    raw_frames = frame_seqs
    cmvn_frames = [to_inv(M, do_vtln=False) for M in frame_seqs]
    inv_frames = [to_inv(M, do_vtln=True) for M in frame_seqs]

    # Shared codebook per variant (k-means over a frame sample; same K+seed).
    def codebook(framelist):
        pool = np.concatenate(framelist, axis=0)
        if len(pool) > 8000:
            pool = pool[np.random.default_rng(0).choice(len(pool), 8000,
                                                        replace=False)]
        return kmeans(pool, K, seed=0)

    sub = Substrate()
    print("\n================= TP SEPARATION + CHUNKER F1 "
          "(raw vs invariant) =================")
    rsep, rf1 = run_variant("RAW units (no norm)", raw_frames, time_seqs,
                            word_seqs, span_seqs, codebook(raw_frames), sub)
    csep, cf1 = run_variant("CMVN units", cmvn_frames, time_seqs,
                            word_seqs, span_seqs, codebook(cmvn_frames), sub)
    isep, if1 = run_variant("VTLN + CMVN units", inv_frames, time_seqs,
                            word_seqs, span_seqs, codebook(inv_frames), sub)

    print("\n================= SUMMARY =================")
    print(f"{'variant':22s}{'TP-sep':>10s}{'chunker F1':>12s}")
    print(f"{'raw':22s}{rsep:>+10.4f}{rf1:>12.3f}")
    print(f"{'CMVN':22s}{csep:>+10.4f}{cf1:>12.3f}")
    print(f"{'VTLN+CMVN':22s}{isep:>+10.4f}{if1:>12.3f}")
    print(f"\nTP separation: raw {rsep:+.4f} -> CMVN {csep:+.4f}  "
          f"(Δ {csep - rsep:+.4f})")
    print(f"Chunker F1   : raw {rf1:.3f} -> CMVN {cf1:.3f}  "
          f"(Δ {cf1 - rf1:+.3f})")


if __name__ == "__main__":
    main()
