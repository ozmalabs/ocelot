"""THE JABBERWOCK AUTHORS THE SILENCE CUE — order-4 self-authoring on the segmentation wall.

Self-training bottomed out at ~13.5% open-utterance WER with segs/word stuck at ~1.07: the
recogniser saturated but the segmenter keeps OVER-CUTTING (fricative/affricate sonority dips read
as word gaps). More training cannot fix it — the next gain needs a NEW segmentation CUE.

This is the agent authoring that cue ITSELF, effect-gated (the same shape as how it authored its
ear): a candidate cue lives in the segmenter's repertoire — an ABSOLUTE-SILENCE gate (a real word
gap drops to near-silence; a voiced dip does not). The agent GATES it in across a repertoire of
floors, RE-LEARNS its recogniser from the new cuts each time (consistency), measures held-out WER,
and KEEPS the floor that lowers WER — REVERTING to no-cue if none helps. A richer segmenter is not
automatically a better one; effect decides.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_authors_silence_cue
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

SEP = "=" * 88
THRESH = 0.35                       # the agent's self-tuned depth_threshold (from self-training)
TRAIN_PITCHES = (30, 42, 54, 66, 78, 90)
VAL_PITCHES = (48, 72)              # held-out from train AND test — the effect-gating yardstick
TEST_PITCHES = (36, 60, 84)        # held-out final report
CUE_REPERTOIRE = (0.03, 0.06, 0.10, 0.15)   # candidate silence floors (0.0 = cue off)


def build_and_eval(floor, eval_pitches):
    """Fresh agent: set the segmenter (threshold + this silence floor), LEARN the recogniser from
    its OWN cuts under that cue, return (WER, segs/word) on eval_pitches. The recogniser is always
    consistent with the cut framing the cue produces — so the measured effect is honest."""
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()
    s.add_node("Operation", {"kind": "sonority_valley", "smoothing_ms": 30.0,
                             "min_separation_ms": 80.0, "depth_threshold": THRESH,
                             "silence_floor": float(floor)})
    for pitch in TRAIN_PITCHES:
        for _rep in range(2):
            for lang, (voice, words) in LANGS.items():
                bank_from_own_cuts(s, sw, lex, voice, words, pitch)
    return evaluate(s, sw, lex, hat, pitches=eval_pitches)


def main():
    print(SEP)
    print("THE JABBERWOCK AUTHORS THE SILENCE CUE — effect-gated, on the segmentation wall.")
    print(SEP)
    # INTROSPECT the impasse (its own record of the plateau).
    print("  INTROSPECT: 'self-training bottomed at ~13.5% WER; segs/word stuck ~1.07 — I keep")
    print("              over-cutting. Retrying/hearing-more won't help; I need a new CUE.'\n")

    # BASELINE — the plateau: relative-prominence cue only (silence floor off).
    base_wer, base_spw = build_and_eval(0.0, VAL_PITCHES)
    print(f"  baseline (cue OFF): validation WER={base_wer*100:.1f}%  segs/word={base_spw:.2f}\n")

    # AUTHOR — gate the absolute-silence cue in across the repertoire; effect decides.
    print("  AUTHORING — gate in the absolute-silence cue, re-learn from the new cuts, measure:")
    trials = {0.0: base_wer}
    for floor in CUE_REPERTOIRE:
        wer, spw = build_and_eval(floor, VAL_PITCHES)
        trials[floor] = wer
        print(f"    silence_floor={floor:.2f}: validation WER={wer*100:.1f}%  segs/word={spw:.2f}  "
              f"{'(better)' if wer < base_wer - 0.005 else ''}")
    best = min(CUE_REPERTOIRE, key=lambda f: trials[f])
    adopt = best if trials[best] < base_wer - 0.005 else 0.0   # KEEP iff it meaningfully helps
    print(f"\n  -> the agent KEEPS silence_floor={adopt:.2f} "
          f"({'authored — it lowered WER' if adopt > 0 else 'reverted — no cue helped'}).\n")

    # CONFIRM on the held-out TEST set: before (cue off) vs after (authored cue).
    before_wer, before_spw = build_and_eval(0.0, TEST_PITCHES)
    after_wer, after_spw = build_and_eval(adopt, TEST_PITCHES)
    print(f"  HELD-OUT TEST:  before (cue off) WER={before_wer*100:.1f}% segs/word={before_spw:.2f}"
          f"   ->   after (authored) WER={after_wer*100:.1f}% segs/word={after_spw:.2f}")
    print(f"\n{SEP}")
    won = adopt > 0 and after_wer < before_wer
    if won:
        print(f"  PASS — the jabberwock AUTHORED the silence cue itself (silence_floor={adopt:.2f}), "
              f"effect-gated:")
        print(f"  open-utterance WER {before_wer*100:.1f}% -> {after_wer*100:.1f}%, segs/word "
              f"{before_spw:.2f} -> {after_spw:.2f}. It changed HOW IT CUTS, not just how it hears.")
    else:
        print(f"  The agent tried the silence cue and REVERTED it (effect-gating working as designed "
              f"— it adopts only what measurably helps). The over-segmentation needs a different cue.")
    print(SEP)
    return 0 if won else 1


if __name__ == "__main__":
    sys.exit(main())
