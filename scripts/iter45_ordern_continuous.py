"""iter45_ordern_continuous — the ARBITRARY ORDER-N interpolation on the CONTINUOUS
gold-span venue (the second venue: where coarticulation degrades the strong gammatone
channels, modeling the cloud at multiple orders has the most room).

The SAME order-N cloud nodes (domains/order_n_interpolation) on the SAME cue-graph,
scored on LibriSpeech gold-span WORD clips (faster-whisper forced alignment), reusing
iter36's gold-span gathering + shared-vocab restriction and the iter45 score_fold
(order-N vs iter-44 vs 1-NN vs centroid vs frozen + per-order drop-it + per-channel
best-order + shuffle). skip_axs — the AxS top-down node is irrelevant to the verdict.

Run:
  PYTHONUNBUFFERED=1 python -m scripts.iter45_ordern_continuous \
      [n_spk] [utts] [min_ex] [max_vocab] [n_max] [ridge]
"""
import os
import random
import sys

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.iter36_continuous_graph as IC
from scripts.iter45_ordern_interpolation import score_fold, _report


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    max_vocab = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    n_max = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    ridge = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
    rounds = int(os.environ.get("ROUNDS", "2"))
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-45 — ARBITRARY ORDER-N interpolation on CONTINUOUS gold-span words",
          flush=True)
    print(f"  n_spk={n_spk} utts/spk={utts} min_exemplars={min_ex} "
          f"max_vocab={max_vocab} n_max={n_max} ridge={ridge} rounds={rounds}", flush=True)
    print("  EVERY (order × channel) cloud node in the combine-all product; the graph",
          flush=True)
    print("  self-selects the order per channel. NO hand-pick, NO fit, NO net, NO donkey",
          flush=True)
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
    ordern = mean(real, "ordern"); interp44 = mean(real, "interp44")
    nn = mean(real, "nn"); cent = mean(real, "cent"); fr = mean(real, "frozen")
    son = mean(shuf, "ordern"); si44 = mean(shuf, "interp44")
    snn = mean(shuf, "nn")

    print(f"  ORDER-N combine-all {ordern:.3f}", flush=True)
    print(f"  iter-44 single-interp (order-1) {interp44:.3f}", flush=True)
    print(f"  1-NN graph (order-0, CURRENT) {nn:.3f}", flush=True)
    print(f"  CENTROID (iter-41) {cent:.3f}   frozen {fr:.3f}", flush=True)
    print(f"  *** order-N vs 1-NN     Δ {ordern-nn:+.3f}  "
          f"=> {'ORDER-N LIFTS' if ordern > nn else 'NO LIFT' if ordern==nn else 'HURTS'}",
          flush=True)
    print(f"  *** order-N vs iter-44  Δ {ordern-interp44:+.3f}", flush=True)

    print("\n  PER-ORDER DROP-IT (mean over folds):", flush=True)
    orders = real[0]["orders"]
    for o in orders:
        d = float(np.mean([r["per_order_drop"][o] for r in real]))
        a = float(np.mean([r["per_order_alone"][o] for r in real]))
        print(f"    order-{o}: drop-it Δ {d:+.3f} (alone {a:.3f})  "
              f"=> {'graph USES this order' if d > 0 else 'redundant/neutral' if d==0 else 'hurts'}",
              flush=True)

    print("\n  SHUFFLE control:", flush=True)
    print(f"    order-N real {ordern:.3f} shuffle {son:.3f} => margin {ordern-son:+.3f} "
          f"({'CLEAN' if ordern > son else 'NOT CLEAN'})", flush=True)
    print(f"    iter-44 real {interp44:.3f} shuffle {si44:.3f} => margin {interp44-si44:+.3f}",
          flush=True)
    print(f"    1-NN   real {nn:.3f} shuffle {snn:.3f} => margin {nn-snn:+.3f}", flush=True)
    print(f"    => order-N margin {'WIDER' if (ordern-son) > (interp44-si44) else 'NOT wider'} "
          f"than iter-44", flush=True)

    nn_err = sum(r["nn_err"] for r in real)
    on_fix = sum(r["ordern_fixes_nn_err"] for r in real)
    on_err = sum(r["ordern_err"] for r in real)
    nn_fix = sum(r["nn_fixes_ordern_err"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): order-N fixes {on_fix}/{nn_err} of 1-NN's "
          f"errors; 1-NN fixes {nn_fix}/{on_err} of order-N's errors  "
          f"(net {on_fix - nn_fix:+d} in order-N's favour)", flush=True)

    print("\n  PER-CHANNEL BEST-ORDER (each channel finding its own order):", flush=True)
    from collections import Counter
    names = real[0]["names"]
    spread = Counter()
    for nm in names:
        accs = {o: float(np.mean([r["per_chan_best"][nm][1][o] for r in real]))
                for o in orders}
        best_o = max(accs, key=accs.get)
        spread[best_o] += 1
        accstr = " ".join(f"o{o}:{accs[o]:.3f}" for o in orders)
        print(f"    {nm:22s} best order-{best_o}   ({accstr})", flush=True)
    print(f"    => channels distribute across orders {dict(sorted(spread.items()))}",
          flush=True)


if __name__ == "__main__":
    main()
