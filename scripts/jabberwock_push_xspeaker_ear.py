"""PUSH THE CROSS-SPEAKER EAR HIGHER — which ear config beats the loop's 63.9% on the hard split?

The autonomous loop saturates the hard cross-speaker task at 63.9% hearing through only the 3 SEED cues at
16kHz. But the agent's repertoire holds SPEAKER-INVARIANCE cues built for exactly this -- cmvn_ear (per-band
whitening), vtl_formant_allpole (the VTL-normalised formant pattern), cs_ear (local contrast that cancels the
speaker-common tilt). And the coverage curve was still climbing. This isolates the EAR levers on the hard
split (held-out ryan/jenny/kristin/sam, banked + recognised through WCCN at 16kHz):

  cue set  : SEED(3)  vs  CURATED(4, speaker-invariance)  vs  FULL(16)
  coverage : 12 train speakers (the loop's _HARD_TRAIN size)  vs  16 (all available English minus held-out)

Find the config that pushes cross-speaker recall highest, to wire the winning ear into the loop.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_push_xspeaker_ear
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.agent_frontend as FE
from domains import wccn
from domains.speech_world import _resample
from scripts.universal_loop_phaseAB_piper import ENGLISH_VOICES
from scripts.jabberwock_largevocab_diag import set_active
from scripts.jabberwock_hifi_ear import synth_native

FS = 16000
WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
HELD = ["ryan", "jenny", "kristin", "sam"]            # the loop's _HARD_TEST
TRAIN_POOL = [v for v in ENGLISH_VOICES if v not in HELD]   # 16 available
RENDS = 3
SEED = ["gammatone_flat", "fft_ear", "allpole_envelope"]
CUE_SETS = [("SEED(3)", SEED), ("CURATED(4)", FE.CURATED_CUES)]   # FULL added after we know all names
N_VALUES = [12, 16]


def loso_heldout(feats, train, project=True):
    bk = [(w, feats[(v, w, r)]) for v in train for w in WORDS for r in range(RENDS) if (v, w, r) in feats]
    cands = sorted({w for (w, _x) in bk})
    Ws = wccn.fit_per_cue(bk) if project else None
    hits = tot = 0
    for v in HELD:
        for w in WORDS:
            for r in range(RENDS):
                if (v, w, r) not in feats:
                    continue
                g = wccn.recognise(feats[(v, w, r)], bk, Ws, cands)
                tot += 1; hits += int(g == w)
    return hits / max(tot, 1)


def main():
    print("=" * 96)
    print("PUSH THE CROSS-SPEAKER EAR — cue set x coverage on the hard split, 16kHz + WCCN (loop baseline 63.9%)")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    FE.install_curated_frontend(s)
    fe = next(n for n in s.nodes("FrontEnd"))
    allnames = [s.node(c)["attrs"].get("name") for et in ("has_cue", "repertoire") for c in s.neighbours(fe, et)]
    cue_sets = CUE_SETS + [("FULL(16)", allnames)]

    print(f"  held-out UNSEEN {HELD} | train pool {len(TRAIN_POOL)} | {len(WORDS)} digits | {RENDS} renditions @ {FS}Hz")
    print("  synthesising (native -> 16kHz) + caching audio...", flush=True)
    audio = {}
    for v in TRAIN_POOL + HELD:
        for w in WORDS:
            for r in range(RENDS):
                got = synth_native(w, {"variant": v, "pitch": 50, "rate": 175})
                if got is not None:
                    audio[(v, w, r)] = _resample(got[0], got[1], FS)

    print(f"\n  {'cue set':>12} | " + "".join(f"N={n:<8}" for n in N_VALUES))
    best = (None, 0.0)
    for label, names in cue_sets:
        set_active(s, fe, names)
        feats = {k: FE.feature_channels(s, np.asarray(x, dtype=np.float64), FS) for k, x in audio.items()}
        cells = []
        for n in N_VALUES:
            acc = loso_heldout(feats, TRAIN_POOL[:n])
            cells.append(acc)
            if acc > best[1]:
                best = ((label, n), acc)
        print(f"  {label:>12} | " + "".join(f"{c*100:>6.0f}%   " for c in cells), flush=True)

    print("\n" + "=" * 96)
    (blabel, bn), bacc = best
    base = 0.639
    print(f"  BEST EAR: {blabel} @ N={bn} -> {bacc*100:.0f}% cross-speaker (loop baseline 3-seed/N=12 = {base*100:.0f}%, "
          f"{'+' if bacc>base else ''}{(bacc-base)*100:.0f}pt).")
    if bacc > base + 0.04:
        print(f"  PUSHED: the {blabel} ear beats the loop's seed ear on the hard split. Wire it into _run_abs_hard")
        print("  (install_curated_frontend / set_active + the larger _HARD_TRAIN) so the agent hears cross-speaker")
        print("  through its speaker-invariance cues + fuller coverage.")
    else:
        print(f"  marginal ({(bacc-base)*100:+.0f}pt): the seed cues + WCCN already remove most of the speaker key here;")
        print("  the lever is coverage (more speakers) more than the cue set. Report honestly + wire the best.")
    print("=" * 96)


if __name__ == "__main__":
    main()
