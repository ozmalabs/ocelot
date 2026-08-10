"""THE JABBERWOCK AUTHORS ITS CUT-PLACEMENT CUE — the second segmentation cue, effect-gated.

After authoring the silence cue (segs/word -> ~1.02, the over-cutting fixed), the residual gap to
whisper was cut PLACEMENT: the agent cuts at the sonority MINIMUM, but the smoothed sonority
envelope lags and decays asymmetrically per word, so the minimum sits ~35ms off the true (symmetric)
inter-word silence — clipping word edges and costing ~18pt of WER (a probe with PERFECT placement
hit 6% = whisper). The fix is acoustic, not oracle: snap each cut to the centre of the contiguous
low-RAW-ENERGY run (a lag-free short-window RMS) — the true silence is symmetric in raw energy.

This is the agent authoring that cue ITSELF, effect-gated (the ear/silence-cue pattern): it gates
the snap-floor repertoire in, RE-LEARNS its recogniser from the re-placed cuts each time, measures
held-out WER, and KEEPS the floor that lowers it (reverting if none helps). The silence cue stays on.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_authors_placement_cue
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon, WordHat
from scripts.wer_test import LANGS
from scripts.wer_open_test import bank_from_own_cuts
from scripts.wer_self_train_watch import evaluate

SEP = "=" * 90
THRESH = 0.30
SILENCE_FLOOR = 0.03                 # the already-authored silence cue (stays on)
TRAIN_PITCHES = (30, 42, 54, 66, 78, 90)
VAL_PITCHES = (48, 72)
TEST_PITCHES = (36, 60, 84)
SNAP_REPERTOIRE = (0.001, 0.003, 0.006, 0.010)   # candidate raw-RMS silence-centre floors


def build_and_eval(snap, eval_pitches):
    """Fresh agent with the silence cue on + this placement snap; LEARN the recogniser from its
    OWN re-placed cuts, return (WER, segs/word). Recogniser stays consistent with the cut framing."""
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()
    s.add_node("Operation", {"kind": "sonority_valley", "smoothing_ms": 30.0,
                             "min_separation_ms": 80.0, "depth_threshold": THRESH,
                             "silence_floor": SILENCE_FLOOR, "snap_center": float(snap)})
    for pitch in TRAIN_PITCHES:
        for _rep in range(2):
            for lang, (voice, words) in LANGS.items():
                bank_from_own_cuts(s, sw, lex, voice, words, pitch)
    return evaluate(s, sw, lex, hat, pitches=eval_pitches)


def main():
    print(SEP)
    print("THE JABBERWOCK AUTHORS ITS CUT-PLACEMENT CUE — effect-gated, on the placement offset.")
    print(SEP)
    print("  INTROSPECT: 'segs/word is ~1.02 (count fixed) but I cut at the sonority MINIMUM, which")
    print("              lags the true silence — my cuts land ~35ms early and clip word edges.'\n")

    base_wer, base_spw = build_and_eval(0.0, VAL_PITCHES)
    print(f"  baseline (placement cue OFF): validation WER={base_wer*100:.1f}%  segs/word={base_spw:.2f}\n")

    print("  AUTHORING — snap each cut to the raw-energy silence centre; re-learn, measure:")
    trials = {0.0: base_wer}
    for snap in SNAP_REPERTOIRE:
        wer, spw = build_and_eval(snap, VAL_PITCHES)
        trials[snap] = wer
        print(f"    snap_center={snap:.3f}: validation WER={wer*100:.1f}%  segs/word={spw:.2f}  "
              f"{'(better)' if wer < base_wer - 0.005 else ''}")
    best = min(SNAP_REPERTOIRE, key=lambda f: trials[f])
    adopt = best if trials[best] < base_wer - 0.005 else 0.0
    print(f"\n  -> the agent KEEPS snap_center={adopt:.3f} "
          f"({'authored — it lowered WER' if adopt > 0 else 'reverted — no placement cue helped'}).\n")

    before_wer, before_spw = build_and_eval(0.0, TEST_PITCHES)
    after_wer, after_spw = build_and_eval(adopt, TEST_PITCHES)
    print(f"  HELD-OUT TEST:  before (cut at minimum) WER={before_wer*100:.1f}%  ->  "
          f"after (snapped to silence centre) WER={after_wer*100:.1f}%")
    print(f"\n{SEP}")
    won = adopt > 0 and after_wer < before_wer
    if won:
        print(f"  PASS — the jabberwock AUTHORED its placement cue itself (snap_center={adopt:.3f}), "
              f"effect-gated:")
        print(f"  open-utterance WER {before_wer*100:.1f}% -> {after_wer*100:.1f}%. It fixed WHERE it cuts —")
        print(f"  snapping to the acoustic silence centre, not the lagging sonority minimum.")
    else:
        print(f"  The agent tried the placement cue and REVERTED it (effect-gating working as designed).")
    print(SEP)
    return 0 if won else 1


if __name__ == "__main__":
    sys.exit(main())
