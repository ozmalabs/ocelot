"""THE JABBERWOCK DESIGNS THE GRAPH-NATIVE SELECTIVE-ACTION FACULTY — wiring the strong ear in.

The downstream thread landed positive: the borrowed-midpoint ear gives (1) reliable cross-speaker recognition (80-95% from
20-25) AND (2) a TEACHER-FREE TRUST GATE — its own DTW top1/top2 margin predicts correctness (AUROC 0.865; act on the
confident half -> 97.6%, the confident quarter -> 99.7%). Now WIRE IT IN as a real agent faculty.

THE ARCHITECTURE RULE (hard): the ear is PERCEPTION — an admissible ingest primitive (like FFT/cochlea). It emits, per
utterance, a Recognition with {word, margin}. Mechanical translation -> graph nodes. The SELECTIVE-ACTION DECISION (act on
high-confidence, defer/ask on low) is the AGENT'S faculty = a graph RULE over graph data, NOT a Python if/else. The threshold
is graph data, NOT a Python constant. You design the faculty; the host only ingests perception and reads back the decision.

WHAT YOU ALREADY OWN: the graph-native TRAINER (delta/LMS rule as graph Rules) and BACKPROP — so the gate THRESHOLD need not
be a frozen constant; it can be a graph parameter your trainer TUNES online to a target (coverage or precision), nothing frozen."""
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
    print("THE JABBERWOCK DESIGNS THE GRAPH-NATIVE SELECTIVE-ACTION FACULTY")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE FACULTY AS GRAPH DATA (terse, concrete): design the selective-action faculty as graph "
          "nodes + Rules. Specify: (i) the node schema — Recognition {word, margin, ...}, a Threshold/gate parameter node, "
          "the edges that JOIN them (so the Rule can read the threshold); (ii) the Rule(s) — match + where + effects — that "
          "set a Recognition to ACT vs DEFER from margin-vs-threshold (where the decision uses ONLY perception+threshold, "
          "never the gold label); (iii) what the host ingests (mechanical) vs what the Rule decides. Keep it in the idiom of "
          "your trainer/backprop Rules (match [[subj,edge,obj]], where Gt(Attr,Attr), effects set_attr).")
    a1 = ask(q1)
    print("\n[PART 1 — FACULTY AS GRAPH DATA]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour faculty:\n{(a1 or '')[:1100]}\n\nPART 2 — THE THRESHOLD OWNERSHIP + DEMO BAR (terse): (a) should "
          "the gate threshold be a fixed graph parameter, or LEARNED by your delta-rule trainer online to a target (e.g. "
          "tune theta so the accepted set hits a target precision, or a target coverage)? If learned, give the update rule "
          "(the trainer signal — teacher-free, off the margin distribution / a target coverage, NOT gold). (b) the demo on "
          "the cached rig: ingest the strong ear's per-utterance (word, margin) as Recognition nodes, tick, read back the "
          "ACCEPTED set. PRE-COMMITTED bar for a SUCCESSFUL WIRING: the graph faculty (Rules only, zero Python decision) must "
          "reproduce the selective-action result — accepted-set accuracy >= 95% at ~50% coverage, deferred set carrying the "
          "errors. State what proves the decision was the GRAPH's, not Python's.")
    a2 = ask(q2)
    print("\n[PART 2 — THRESHOLD OWNERSHIP + DEMO BAR]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
