"""iter49_node_admissibility_continuous — ADMISSIBILITY GRAPHS ON THE NODES THEMSELVES,
on the CONTINUOUS gold-span venue.

The SAME per-contrast weighted product (domains/node_admissibility_graphs) + the SAME
inner-LOSO per-WORD precision measurement (scripts/iter49_node_admissibility_graphs) on
LibriSpeech gold-span WORD clips (faster-whisper forced alignment), reusing iter36's
gold-span gathering + shared-vocab restriction and the iter49 score_fold. skip_axs.

Run DETACHED (setsid) — the per-fold inner-LOSO per-word reliability measurement is heavy:
  PYTHONUNBUFFERED=1 python -m scripts.iter49_node_admissibility_continuous \
      [n_spk] [utts] [min_ex] [max_vocab] [n_max] [ridge]
"""
import os
import random
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.iter36_continuous_graph as IC
from scripts.iter49_node_admissibility_graphs import score_fold, _report


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    max_vocab = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    n_max = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    ridge = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
    rounds = int(os.environ.get("ROUNDS", "2"))
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-49 — NODE ADMISSIBILITY GRAPHS on CONTINUOUS gold-span words", flush=True)
    print(f"  n_spk={n_spk} utts/spk={utts} min_exemplars={min_ex} "
          f"max_vocab={max_vocab} n_max={n_max} ridge={ridge} rounds={rounds}", flush=True)
    print("  score(w) = PROD_i P_i(w)^weight_i(w) ; weight_i(w) PER candidate word", flush=True)
    print("  weight_i(w) = inner-LOSO PER-WORD precision (each node's admissibility graph)",
          flush=True)
    print("  MEASURED not searched; LOSO-clean; NO fit, NO sweep, NO donkey", flush=True)
    print("=" * 72, flush=True)

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")

    print("\nForced alignment + gold-word slicing...", flush=True)
    va_raw = IC.gather_gold_words(n_spk, utts, wmodel)
    va, vocab = IC.restrict_to_shared_vocab(va_raw, min_ex, max_vocab)
    n_clips = sum(len(c) for c in va.values())
    chance = 1.0 / max(len(vocab), 1)
    print(f"\nshared cross-speaker vocab ({len(vocab)} words, chance {chance:.3f}): "
          f"{sorted(vocab)}", flush=True)
    print(f"speakers kept: {sorted(va)}  total clips: {n_clips}", flush=True)

    speakers = sorted(va)
    real, shuf = [], []
    for held in speakers:
        if len(va.get(held, [])) < 2:
            continue
        r = score_fold(va, held, rounds, shuffle=False, n_max=n_max, ridge=ridge)
        _report(r); real.append(r)
        sr = score_fold(va, held, rounds, shuffle=True, n_max=n_max, ridge=ridge)
        _report(sr); shuf.append(sr)

    if not real:
        print("\nNo valid folds (insufficient cross-speaker shared vocab).", flush=True)
        return

    def mean(rs, k):
        return float(np.mean([x[k] for x in rs]))

    print("\n" + "=" * 72, flush=True)
    print(f"VERDICT (mean over {len(real)} held-out speakers, continuous gold-span, "
          f"chance {chance:.3f})", flush=True)
    print("=" * 72, flush=True)
    pc = mean(real, "per_contrast"); pn = mean(real, "per_node"); eq = mean(real, "equal")
    i44 = mean(real, "interp44"); nn = mean(real, "nn"); fr = mean(real, "frozen")
    spc = mean(shuf, "per_contrast"); spn = mean(shuf, "per_node")
    seq = mean(shuf, "equal"); si44 = mean(shuf, "interp44"); snn = mean(shuf, "nn")

    print(f"  PER-CONTRAST admissibility graphs  {pc:.3f}", flush=True)
    print(f"  PER-NODE weighted (iter-48)        {pn:.3f}", flush=True)
    print(f"  EQUAL combine-all (iter-45)        {eq:.3f}", flush=True)
    print(f"  iter-44 single-interp (order-1)    {i44:.3f}", flush=True)
    print(f"  1-NN graph (order-0)               {nn:.3f}   frozen {fr:.3f}", flush=True)
    print(f"  *** per-contrast vs PER-NODE  Δ {pc-pn:+.3f}  "
          f"=> {'FINER GRAIN LIFTS' if pc > pn else 'NO LIFT' if pc==pn else 'HURTS'}", flush=True)
    print(f"  *** per-contrast vs EQUAL     Δ {pc-eq:+.3f}", flush=True)
    print(f"  *** per-contrast vs iter-44   Δ {pc-i44:+.3f}", flush=True)
    print(f"  *** per-contrast vs 1-NN      Δ {pc-nn:+.3f}", flush=True)

    print("\n  SHUFFLE control:", flush=True)
    print(f"    PER-CONTRAST real {pc:.3f} shuffle {spc:.3f} => margin {pc-spc:+.3f} "
          f"({'CLEAN' if pc > spc else 'NOT CLEAN'})", flush=True)
    print(f"    PER-NODE     real {pn:.3f} shuffle {spn:.3f} => margin {pn-spn:+.3f}", flush=True)
    print(f"    EQUAL        real {eq:.3f} shuffle {seq:.3f} => margin {eq-seq:+.3f}", flush=True)
    print(f"    iter-44      real {i44:.3f} shuffle {si44:.3f} => margin {i44-si44:+.3f}", flush=True)
    print(f"    1-NN         real {nn:.3f} shuffle {snn:.3f} => margin {nn-snn:+.3f}", flush=True)

    pn_err = sum(r["pn_err"] for r in real)
    pc_fix = sum(r["pc_fixes_pn"] for r in real)
    pc_err = sum(r["pc_err"] for r in real)
    pn_fix = sum(r["pn_fixes_pc"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): per-contrast fixes {pc_fix}/{pn_err} of "
          f"per-node's errors; per-node fixes {pn_fix}/{pc_err} of per-contrast's  "
          f"(net {pc_fix - pn_fix:+d} in per-contrast's favour)", flush=True)

    cm = mean(real, "claim_mean"); cmed = mean(real, "claim_median")
    fnc = mean(real, "frac_no_claim")
    print(f"\n  PER-CONTRAST MEASUREMENT SPARSITY (the scale-the-venue probe):", flush=True)
    print(f"    precision sample per (node,word) cell: mean {cm:.1f} claims, median "
          f"{cmed:.0f}; {fnc*100:.0f}% of cells had ZERO claims (fell back to per-node)",
          flush=True)
    print(f"    => {'ADEQUATE' if cmed >= 5 and fnc < 0.25 else 'THIN'} per-contrast "
          f"measurement on this venue", flush=True)


if __name__ == "__main__":
    main()
