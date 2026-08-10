"""coarticulation_predict_remove_accept — link-2b. Does the agent's richer
PREDICT-AND-REMOVE coarticulation mechanism beat the linear flat-mean context-norm
on the residual, WITHOUT degrading the unit stream's own structure?

The agent's own bar (from docs/agent_next_decision.md / the brief):
  1. CROSS-CONTEXT INVARIANCE RATIO must MOVE toward more-invariant (lower). The
     linear context-norm FAILED this (0.678 -> 0.728, wrong way).
  2. perception_self_assessment on the RAW quantized units must NOT flip to
     frontier='perception'; predict_over_freq should hold/recover (the linear
     context-norm dropped it to ~1.26, AT the floor; compress_ratio rose over 0.85).
  3. forward chunker F1 / chunk->word purity must hold or improve on 0.335 / 0.73.

Variants (everything downstream held FIXED; only frame features change):
    CMVN              (link-1, speaker)
    CMVN + context    (link-2, the current default, linear flat-mean)
    CMVN + context + predict-remove  (link-2b, the agent's richer Term) — swept
                                     over k ONLY to REPORT the curve honestly.

Mirrors context_invariant_librispeech_accept's framing/codebook/chunker/F1/purity
+ cross-context invariance, and ADDS the perception_self_assessment yardstick run on
each variant's raw quantized unit sequences (the load-bearing signal the agent's
RULE flips on).

Run: python -m scripts.coarticulation_predict_remove_accept [n_utts] [n_speakers] [K] [window] [k_csv]
  k_csv default "0.25,0.5,1.0" — the gains to report (mechanism-first, NOT tuned).
"""
import re
import sys
import time
import random
import numpy as np
from collections import defaultdict

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.sentence_learning as SL
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import cmvn
from domains.context_invariant_units import apply_context_norm
from domains.coarticulation_predict_remove import apply_predict_remove
from domains.forward_segmentation import forward_segment, estimate_tp
from domains.perception_self_assessment import (
    measure_unit_predictability, record_perception_quality,
    install_perception_frontier_rule, agent_flag_perception)
from substrate_rs import Substrate

# reuse the proven measurement helpers from the link-2 accept (identical protocol)
from scripts.context_invariant_librispeech_accept import (
    words_of, frames_of, kmeans, quantize, tp_within_across,
    proportional_word_boundaries, chunk_boundary_times, boundary_f1, flat_len,
    chunk_to_word_purity, cross_context_invariance)


def yardstick(unit_seqs):
    """Run the agent's labels-free perception_self_assessment on the RAW quantized
    unit sequences and fire its graph-resident flagging RULE. Returns the signal +
    the agent's frontier verdict ('perception' or 'none'). This is the load-bearing
    check: the richer mechanism must NOT flip this to 'perception'."""
    seqs = [list(s) for s in unit_seqs if len(s) >= 2]
    sig = measure_unit_predictability(seqs)
    sub = Substrate()
    record_perception_quality(sub, sig)
    fr = install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    verdict = agent_flag_perception(sub, fr["rule_index"])
    return sig, verdict


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
    sig, verdict = yardstick(unit_seqs)
    print(f"\n--- {tag} ---")
    print(f"  TP separation (within - across) = {mw - ma:+.4f}")
    print(f"  chunker boundary F1 = {cf / n:.3f}  (raw-unit F1 {rf / n:.3f})")
    print(f"  chunk->word purity  = {purity:.3f}")
    print(f"  cross-context invariance ratio (lower=better) = {inv['ratio']:.3f}"
          f"  (across {inv['across']:.4f}, within {inv['within']:.4f}, "
          f"{inv['n_units']} units)")
    print(f"  YARDSTICK (raw units): predict_over_freq = "
          f"{sig['predict_over_freq']:.3f} (floor 1.25), compress_ratio = "
          f"{sig['compress_ratio']:.4f} (ceiling 0.85)  -> agent frontier = "
          f"'{verdict}'")
    return {"tag": tag, "sep": mw - ma, "f1": cf / n, "purity": purity,
            "ctx_ratio": inv["ratio"], "pof": sig["predict_over_freq"],
            "compress": sig["compress_ratio"], "frontier": verdict}


def codebook(framelist, K):
    pool = np.concatenate(framelist, axis=0)
    if len(pool) > 8000:
        pool = pool[np.random.default_rng(0).choice(len(pool), 8000,
                                                    replace=False)]
    return kmeans(pool, K, seed=0)


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 48
    window = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    ks = [float(x) for x in (sys.argv[5] if len(sys.argv) > 5
                             else "0.25,0.5,1.0").split(",")]
    random.seed(1)

    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    sel = [p for p in pairs if p[1] in speakers]
    random.shuffle(sel)
    sel = sel[:n_utts]
    print(f"LibriSpeech dev-clean: {len(sel)} utts, "
          f"{len(set(p[1] for p in sel))} speakers, K={K}, "
          f"context window=+-{window}, predict-remove k in {ks}")

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
        times = [dur * kk / M.shape[0] for kk in range(M.shape[0])]
        frame_seqs.append(M)
        time_seqs.append(times)
        word_seqs.append(words)
        span_seqs.append((times[0], times[-1]))
    print(f"Framed {len(frame_seqs)} utts in {time.time()-t0:.0f}s")
    if len(frame_seqs) < 4:
        print("Too few utterances.")
        return

    cmvn_frames = [cmvn(M, do_variance=True) for M in frame_seqs]
    print("Applying agent's context-norm Term (native eval) ...", flush=True)
    tc = time.time()
    ctx_frames = [apply_context_norm(M, window=window) for M in cmvn_frames]
    print(f"  context-norm applied in {time.time()-tc:.0f}s")

    sub = Substrate()
    print("\n========= CMVN / CMVN+context / CMVN+context+predict-remove =========")
    c = run_variant("CMVN", cmvn_frames, time_seqs, word_seqs, span_seqs,
                    codebook(cmvn_frames, K), sub)
    x = run_variant("CMVN+context (current default, linear)", ctx_frames,
                    time_seqs, word_seqs, span_seqs, codebook(ctx_frames, K), sub)

    # Two ways to use the richer mechanism, both reported honestly:
    #  (A) STACKED on the current default: CMVN+context+predict-remove (the brief's
    #      acceptance comparison, base = CMVN+context).
    #  (B) REPLACING flat-mean: CMVN+predict-remove (no flat-mean context-norm) —
    #      the cleaner test of whether the richer, structure-preserving mechanism
    #      removes coarticulation WITHOUT the flat-mean structure cost.
    rich_rows = []
    for k in ks:
        print(f"\nApplying predict-remove on CMVN+context (stacked, k={k}) ...",
              flush=True)
        tr = time.time()
        pr_frames = [apply_predict_remove(M, window=window, k=k)
                     for M in ctx_frames]
        print(f"  applied in {time.time()-tr:.0f}s")
        r = run_variant(f"CMVN+context+predict-remove (k={k})", pr_frames,
                        time_seqs, word_seqs, span_seqs,
                        codebook(pr_frames, K), sub)
        rich_rows.append(r)
    repl_rows = []
    for k in ks:
        print(f"\nApplying predict-remove on CMVN directly (replaces flat-mean, "
              f"k={k}) ...", flush=True)
        tr = time.time()
        pr_frames = [apply_predict_remove(M, window=window, k=k)
                     for M in cmvn_frames]
        print(f"  applied in {time.time()-tr:.0f}s")
        r = run_variant(f"CMVN+predict-remove (no flat-mean, k={k})", pr_frames,
                        time_seqs, word_seqs, span_seqs,
                        codebook(pr_frames, K), sub)
        repl_rows.append(r)

    print("\n================= SUMMARY =================")
    hdr = (f"{'variant':40s}{'F1':>7s}{'purity':>8s}{'ctx_ratio':>11s}"
           f"{'pof':>7s}{'compress':>10s}{'frontier':>12s}")
    print(hdr)
    for row in [c, x] + rich_rows + repl_rows:
        print(f"{row['tag']:40s}{row['f1']:>7.3f}{row['purity']:>8.3f}"
              f"{row['ctx_ratio']:>11.3f}{row['pof']:>7.3f}"
              f"{row['compress']:>10.4f}{row['frontier']:>12s}")

    print("\n--- (A) STACKED bar: base = CMVN+context (the brief's comparison) ---")
    base = x
    for r in rich_rows:
        d_ratio = r["ctx_ratio"] - base["ctx_ratio"]
        d_f1 = r["f1"] - base["f1"]
        d_pur = r["purity"] - base["purity"]
        ratio_ok = d_ratio < -1e-6                      # moved more-invariant
        struct_ok = r["frontier"] != "perception"       # yardstick held
        chunk_ok = (r["f1"] >= base["f1"] - 1e-6) and (
            r["purity"] >= base["purity"] - 1e-6)
        verdict = ("MEETS" if (ratio_ok and struct_ok and chunk_ok)
                   else "partial" if (ratio_ok or struct_ok) else "FAILS")
        print(f"  k={r['tag'].split('k=')[-1].rstrip(')')}: "
              f"ctx_ratio Δ {d_ratio:+.3f} ({'OK' if ratio_ok else 'no'}), "
              f"frontier='{r['frontier']}' ({'OK' if struct_ok else 'FLIPPED'}), "
              f"F1 Δ {d_f1:+.3f} / purity Δ {d_pur:+.3f} "
              f"({'OK' if chunk_ok else 'down'})  -> {verdict}")

    print("\n--- (B) REPLACING flat-mean: base = CMVN (does richer alone remove "
          "coarticulation while holding the yardstick?) ---")
    base = c
    print(f"  reference CMVN: ctx_ratio {c['ctx_ratio']:.3f}, frontier "
          f"'{c['frontier']}', F1 {c['f1']:.3f}, purity {c['purity']:.3f}")
    for r in repl_rows:
        d_ratio = r["ctx_ratio"] - base["ctx_ratio"]
        d_f1 = r["f1"] - base["f1"]
        d_pur = r["purity"] - base["purity"]
        ratio_ok = d_ratio < -1e-6
        struct_ok = r["frontier"] != "perception"
        chunk_ok = (r["f1"] >= base["f1"] - 1e-6) and (
            r["purity"] >= base["purity"] - 1e-6)
        verdict = ("MEETS" if (ratio_ok and struct_ok and chunk_ok)
                   else "partial" if (ratio_ok or struct_ok) else "FAILS")
        print(f"  k={r['tag'].split('k=')[-1].rstrip(')')}: "
              f"ctx_ratio Δ {d_ratio:+.3f} ({'OK' if ratio_ok else 'no'}), "
              f"frontier='{r['frontier']}' ({'OK' if struct_ok else 'FLIPPED'}), "
              f"F1 Δ {d_f1:+.3f} / purity Δ {d_pur:+.3f} "
              f"({'OK' if chunk_ok else 'down'})  -> {verdict}")


if __name__ == "__main__":
    main()
