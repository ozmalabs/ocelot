"""THE JABBERWOCK DESIGNS THE OOV NOVELTY GATE — the teacher-free "is this word KNOWN at all?" faculty.

The live audio adapter works for IN-VOCAB speech (ACT 96.2% @ 49% coverage, gate self-tuned online). But streaming ALL words
incl. OUT-OF-VOCABULARY ones (the bank knows ~400 words; LibriSpeech has thousands) drops base to 41% / ACT 66.7%: an OOV
word gets FORCED to its nearest exemplar (always wrong), and the RELATIVE top1/top2 margin does NOT catch it — an OOV can
have a spuriously high margin (its nearest bank word happens to be much closer than the 2nd, even though BOTH are wrong).

THE FIX you already named: OOV deferral needs an ABSOLUTE-distance NOVELTY gate — "is this close to ANYTHING I know?" — not
the relative margin. Design it as graph data, teacher-free, composing with the existing selective-action margin gate.

WHAT EXISTS: the strong ear emits, per word, the banked-exemplar DTW result — best-match distance d1 (absolute, how close the
nearest known word is) AND the top1/top2 margin (relative confidence). The selective-action faculty already gates on margin
vs a trained threshold. The graph-native delta-rule TRAINER can tune a second threshold online.

THE ARCHITECTURE RULE: the ear is perception (emits d1, margin). The NOVELTY DECISION (known vs novel) is a graph Rule; its
threshold is graph data, calibrated TEACHER-FREE (no OOV labels). The constraints: floor of efficiency; dynamic; nothing frozen."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = __doc__


def main():
    ask = make_ask(timeout=340.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE OOV NOVELTY GATE")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE NOVELTY SIGNAL + TEACHER-FREE CALIBRATION (terse, concrete): (a) what is the novelty "
          "signal read off the ear's output — absolute best-match distance d1, or a normalised form (d1 vs the bank's "
          "typical nearest distance), or something better that separates 'a known word heard from a new speaker' (in-vocab, "
          "should ACT) from 'a word I have no exemplar for' (OOV, should DEFER)? The hard case: a known word from a new "
          "speaker ALSO has a largish d1 (cross-speaker variation) — so raw d1 may not separate OOV from cross-speaker "
          "in-vocab. How do you tell them apart TEACHER-FREE? (b) how is the novelty threshold calibrated with NO OOV labels "
          "— e.g. off the bank's OWN leave-one-out nearest-exemplar distance distribution (a known word's d1 to OTHER "
          "speakers' exemplars), set at a percentile, then tuned online by your delta-rule trainer to a target novel-rate?")
    a1 = ask(q1)
    print("\n[PART 1 — NOVELTY SIGNAL + CALIBRATION]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour signal:\n{(a1 or '')[:1100]}\n\nPART 2 — FACULTY AS GRAPH DATA + COMPOSE + TEST/BAR (terse): "
          "(a) the novelty faculty as nodes+Rules in your trainer idiom (a NoveltyGate{threshold} node, the Rule that marks a "
          "Recognition NOVEL vs KNOWN from the signal-vs-threshold, and how it COMPOSES with the margin gate — ACT iff KNOWN "
          "AND confident; DEFER if novel OR unconfident). (b) the decisive test on the cached rig: stream IN-VOCAB + OOV "
          "words; the bar — (i) the novelty signal separates OOV from in-vocab with AUROC >= X, AND (ii) the combined gate "
          "RECOVERS accuracy on the OOV-containing stream — ACT-set accuracy back to >= Y% (vs margin-alone 66.7) by "
          "deferring OOV, at reasonable coverage. State X, Y, and the honest kill (if d1 can't separate OOV from cross-"
          "speaker in-vocab, novelty-by-distance is dead and OOV needs a different signal).")
    a2 = ask(q2)
    print("\n[PART 2 — FACULTY + COMPOSE + TEST/BAR]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
