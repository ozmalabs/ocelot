"""iter48_weighted_continuous — the WEIGHTED ADMISSIBILITY RULE GRAPH on the CONTINUOUS
gold-span venue (the second venue: coarticulation degrades the strong channels, so the
per-node reliabilities differ more — the weighting has the most to act on).

The SAME weighted product (domains/weighted_admissibility) + the SAME inner-LOSO
reliability measurement (scripts/iter48_weighted_admissibility) on LibriSpeech gold-span
WORD clips (faster-whisper forced alignment), reusing iter36's gold-span gathering +
shared-vocab restriction and the iter48 score_fold. skip_axs.

Run DETACHED (setsid) — the per-fold inner-LOSO reliability measurement is heavy:
  PYTHONUNBUFFERED=1 python -m scripts.iter48_weighted_continuous \
      [n_spk] [utts] [min_ex] [max_vocab] [n_max] [ridge]
"""
import os
import random
import sys

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.iter36_continuous_graph as IC
from scripts.iter48_weighted_admissibility import score_fold, _report


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
    print("ITER-48 — WEIGHTED ADMISSIBILITY on CONTINUOUS gold-span words", flush=True)
    print(f"  n_spk={n_spk} utts/spk={utts} min_exemplars={min_ex} "
          f"max_vocab={max_vocab} n_max={n_max} ridge={ridge} rounds={rounds}", flush=True)
    print("  score(w) = PROD_i P_i(w)^weight_i ; weight = inner-LOSO train reliability",
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
    w = mean(real, "weighted"); eq = mean(real, "equal")
    i44 = mean(real, "interp44"); nn = mean(real, "nn"); fr = mean(real, "frozen")
    sw = mean(shuf, "weighted"); seq = mean(shuf, "equal")
    si44 = mean(shuf, "interp44"); snn = mean(shuf, "nn")

    print(f"  WEIGHTED admissibility graph    {w:.3f}", flush=True)
    print(f"  EQUAL combine-all (iter-45)     {eq:.3f}", flush=True)
    print(f"  iter-44 single-interp (order-1) {i44:.3f}", flush=True)
    print(f"  1-NN graph (order-0)            {nn:.3f}   frozen {fr:.3f}", flush=True)
    print(f"  *** weighted vs EQUAL    Δ {w-eq:+.3f}  "
          f"=> {'WEIGHTING LIFTS' if w > eq else 'NO LIFT' if w==eq else 'HURTS'}", flush=True)
    print(f"  *** weighted vs iter-44  Δ {w-i44:+.3f}", flush=True)
    print(f"  *** weighted vs 1-NN     Δ {w-nn:+.3f}", flush=True)

    print("\n  SHUFFLE control:", flush=True)
    print(f"    WEIGHTED real {w:.3f} shuffle {sw:.3f} => margin {w-sw:+.3f} "
          f"({'CLEAN' if w > sw else 'NOT CLEAN'})", flush=True)
    print(f"    EQUAL    real {eq:.3f} shuffle {seq:.3f} => margin {eq-seq:+.3f}", flush=True)
    print(f"    iter-44  real {i44:.3f} shuffle {si44:.3f} => margin {i44-si44:+.3f}", flush=True)
    print(f"    1-NN     real {nn:.3f} shuffle {snn:.3f} => margin {nn-snn:+.3f}", flush=True)

    eq_err = sum(r["eq_err"] for r in real)
    w_fix = sum(r["weighted_fixes_eq"] for r in real)
    w_err = sum(r["w_err"] for r in real)
    eq_fix = sum(r["eq_fixes_w"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): weighted fixes {w_fix}/{eq_err} of equal's "
          f"errors; equal fixes {eq_fix}/{w_err} of weighted's  "
          f"(net {w_fix - eq_fix:+d} in weighted's favour)", flush=True)

    print("\n  MEASURED WEIGHTS by order (mean over folds x channels):", flush=True)
    orders = real[0]["orders"]
    from collections import defaultdict
    agg = defaultdict(lambda: ([], []))
    for r in real:
        for (ci, o, acc), wt in zip(r["accs"], r["weights"]):
            agg[o][0].append(acc); agg[o][1].append(wt)
    for o in orders:
        accs, wts = agg[o]
        print(f"    order-{o}: measured-acc mean {np.mean(accs):.3f}  "
              f"weight mean {np.mean(wts):.3f}", flush=True)


if __name__ == "__main__":
    main()
