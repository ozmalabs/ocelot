"""iter43_sharp_continuous_accept — the SHARP all-pole front-end on the CONTINUOUS
gold-span venue (the second venue the iter-43 task requires).

The bound's other venue: LibriSpeech gold-span WORD clips (faster-whisper forced
alignment), where coarticulation degrades the strong gammatone spectral channels and
a sharper feature has the most room to help (iter-41's stated venue-dependence). The
SAME sharp all-pole node (the 7th orthogonal cue) is wired into the SAME cue-graph;
this script scores the bottom-up front-end metrics (skip_axs — the AxS top-down node
is irrelevant to the feature-front-end verdict and slow on continuous clips).

Reuses iter36's gold-span gathering + shared-vocab restriction (the iter-15 harness),
and the iter-43 fold_metrics (sharp-graph vs without-all-pole vs gammatone-only +
the all-pole error-overlap vs the bottom-up graph + shuffle).

Run:
  PYTHONUNBUFFERED=1 python -m scripts.iter43_sharp_continuous_accept [n_spk] [utts] \
      [min_ex] [max_vocab]
"""
import os
import random
import sys

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.enriched_hvpt_accept as EH
import scripts.iter36_continuous_graph as IC
from scripts.iter43_sharp_frontend_accept import fold_metrics, _report


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    max_vocab = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    rounds = int(os.environ.get("ROUNDS", "2"))
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-43 — SHARP all-pole front-end on CONTINUOUS gold-span words", flush=True)
    print(f"  n_spk={n_spk} utts/spk={utts} min_exemplars={min_ex} "
          f"max_vocab={max_vocab} rounds={rounds}", flush=True)
    print(f"  ortho cues = {EH.ORTHO_NAMES}", flush=True)
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
        m = fold_metrics(EH.build_fold(va, held, rounds, shuffle=False, skip_axs=True))
        _report(m); real.append(m)
        sm = fold_metrics(EH.build_fold(va, held, rounds, shuffle=True, skip_axs=True))
        _report(sm); shuf.append(sm)

    if not real:
        print("\nNo valid folds (insufficient cross-speaker shared vocab).", flush=True)
        return

    def mean(rs, k):
        return float(np.mean([r[k] for r in rs]))

    print("\n" + "=" * 72, flush=True)
    print(f"VERDICT (mean over {len(real)} held-out speakers, continuous gold-span)",
          flush=True)
    print("=" * 72, flush=True)
    sharp = mean(real, "sharp"); no_ap = mean(real, "no_ap")
    gam = mean(real, "gammatone"); sf = mean(real, "single_flat")
    fr = mean(real, "frozen"); ap_alone = mean(real, "ap_alone")
    s_sh = mean(shuf, "sharp"); s_noap = mean(shuf, "no_ap")

    print(f"\n  SHARP graph (+all-pole)     {sharp:.3f}", flush=True)
    print(f"  same graph WITHOUT all-pole {no_ap:.3f}", flush=True)
    print(f"  *** all-pole drop-it Δ      {sharp-no_ap:+.3f}   "
          f"=> {'LIFTS' if sharp > no_ap else ('NEUTRAL' if sharp==no_ap else 'HURTS')}",
          flush=True)
    print(f"  gammatone-only              {gam:.3f}   Δ(sharp-gam) {sharp-gam:+.3f}",
          flush=True)
    print(f"  single-flat {sf:.3f}   frozen {fr:.3f}   all-pole alone {ap_alone:.3f} "
          f"(chance {chance:.3f})", flush=True)

    n_bu = sum(r["n_bu_err"] for r in real)
    n_caught = sum(r["ap_caught"] for r in real)
    n_fixed = sum(r["sharp_fixed"] for r in real)
    n_broke = sum(r["sharp_broke"] for r in real)
    rate = n_caught / max(n_bu, 1)
    print(f"\n  ERROR-OVERLAP (pooled): bottom-up wrong on {n_bu}; all-pole-alone "
          f"catches {n_caught} = {rate:.3f} "
          f"({'ABOVE' if rate > chance else 'at/below'} chance {chance:.3f})", flush=True)
    print(f"  SHARP graph net on bottom-up errors: fixed {n_fixed} broke {n_broke} "
          f"net {n_fixed-n_broke:+d}", flush=True)
    print(f"\n  SHUFFLE: SHARP real {sharp:.3f} vs shuffle {s_sh:.3f} "
          f"=> margin {sharp-s_sh:+.3f} ({'CLEAN' if sharp > s_sh else 'NOT CLEAN'})",
          flush=True)
    print(f"    without-all-pole real {no_ap:.3f} vs shuffle {s_noap:.3f} "
          f"=> margin {no_ap-s_noap:+.3f}", flush=True)


if __name__ == "__main__":
    main()
