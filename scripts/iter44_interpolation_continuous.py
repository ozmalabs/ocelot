"""iter44_interpolation_continuous — the INTERPOLATION sub-node on the CONTINUOUS
gold-span venue (the second venue iter-41 flagged: where coarticulation degrades the
strong gammatone channels, modeling the cloud has the most room to help).

The SAME interpolation manifold sub-node (domains/interpolation_subnodes) on the SAME
cue-graph, scored on LibriSpeech gold-span WORD clips (faster-whisper forced
alignment), reusing iter36's gold-span gathering + shared-vocab restriction and the
iter44 score_fold (interp vs 1-NN vs centroid vs frozen + drop-it + error-overlap +
shuffle). skip_axs — the AxS top-down node is irrelevant to the feature verdict.

Run:
  PYTHONUNBUFFERED=1 python -m scripts.iter44_interpolation_continuous \
      [n_spk] [utts] [min_ex] [max_vocab] [rank]
"""
import os
import random
import sys

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.iter36_continuous_graph as IC
from scripts.iter44_interpolation_subnodes import score_fold, _report


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    max_vocab = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    rank = int(sys.argv[5]) if len(sys.argv) > 5 else 3
    rounds = int(os.environ.get("ROUNDS", "2"))
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-44 — INTERPOLATION sub-node on CONTINUOUS gold-span words", flush=True)
    print(f"  n_spk={n_spk} utts/spk={utts} min_exemplars={min_ex} "
          f"max_vocab={max_vocab} rank={rank} rounds={rounds}", flush=True)
    print("  three reads of the cloud: 1-NN ignores / centroid averages / "
          "MANIFOLD models the spread", flush=True)
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
        r = score_fold(va, held, rounds, shuffle=False, rank=rank)
        _report(r); real.append(r)
        sr = score_fold(va, held, rounds, shuffle=True, rank=rank)
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
    interp = mean(real, "interp"); nn = mean(real, "nn")
    cent = mean(real, "cent"); fr = mean(real, "frozen")
    sfi = mean(real, "sf_interp"); sfn = mean(real, "sf_nn"); sfc = mean(real, "sf_cent")
    si = mean(shuf, "interp"); snn = mean(shuf, "nn"); scent = mean(shuf, "cent")
    dropit = mean(real, "interp_dropit")

    print(f"  INTERPOLATION graph (models the spread) {interp:.3f}", flush=True)
    print(f"  1-NN graph (ignores the spread, CURRENT) {nn:.3f}", flush=True)
    print(f"  CENTROID graph (averages, iter-41) {cent:.3f}   frozen {fr:.3f}", flush=True)
    print(f"  *** interp vs 1-NN  Δ {interp-nn:+.3f}  "
          f"=> {'INTERPOLATION LIFTS' if interp > nn else 'NO LIFT (null)' if interp==nn else 'HURTS'}",
          flush=True)
    print(f"  *** interp vs centroid Δ {interp-cent:+.3f}", flush=True)
    print(f"  single-flat: interp {sfi:.3f}  1-NN {sfn:.3f}  centroid {sfc:.3f}  "
          f"Δ(interp-1NN) {sfi-sfn:+.3f}", flush=True)
    print(f"  *** interp sub-node DROP-IT (added to 1-NN graph) Δ {dropit:+.3f}",
          flush=True)
    print(f"\n  SHUFFLE control:", flush=True)
    print(f"    interp real {interp:.3f} shuffle {si:.3f} => margin {interp-si:+.3f} "
          f"({'CLEAN' if interp > si else 'NOT CLEAN'})", flush=True)
    print(f"    1-NN   real {nn:.3f} shuffle {snn:.3f} => margin {nn-snn:+.3f}",
          flush=True)

    nn_err = sum(r["nn_err"] for r in real)
    interp_fix = sum(r["interp_fixes_nn_err"] for r in real)
    interp_err = sum(r["interp_err"] for r in real)
    nn_fix = sum(r["nn_fixes_interp_err"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): interp fixes {interp_fix}/{nn_err} of 1-NN's "
          f"errors; 1-NN fixes {nn_fix}/{interp_err} of interp's errors  "
          f"(net {interp_fix - nn_fix:+d} in interp's favour)", flush=True)

    print("\n  PER-CHANNEL interp Δ (mean over folds):", flush=True)
    names = real[0]["names"]
    chan_deltas = []
    for nm in names:
        raws = [r["per_chan"][nm][0] for r in real]
        mans = [r["per_chan"][nm][1] for r in real]
        chan_deltas.append((nm, float(np.mean(mans)) - float(np.mean(raws)),
                            float(np.mean(raws)), float(np.mean(mans))))
    for nm, d, raw, man in sorted(chan_deltas, key=lambda t: -t[1]):
        print(f"    {nm:22s} 1-NN {raw:.3f} -> manifold {man:.3f}  Δ {d:+.3f}",
              flush=True)


if __name__ == "__main__":
    main()
