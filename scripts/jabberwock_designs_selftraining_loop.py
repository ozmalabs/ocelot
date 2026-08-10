"""THE JABBERWOCK DESIGNS THE SELF-TRAINING LIVE HARVEST LOOP — self-label confident, DEFER uncertain, PLUGGABLE teacher.

The creator's spec: the live harvest loop should (1) SELF-TRAIN -- the agent labels confident percepts itself and banks
its own exemplars (no teacher); (2) MARK-FOR-FUTURE -- uncertain percepts are DEFERRED to a queue, NOT banked (so it
never banks its own mistakes); (3) a PLUGGABLE TEACHER HARNESS -- the teacher (whisper / parakeet / human / none) is a
swappable interface consulted ONLY on the deferred queue. This is cheap-first / escalate-on-failure, made concrete.

Design it architecture-clean, and solve the CRUX honestly. Pre-commit a smallest buildable slice + a validation bar.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_designs_selftraining_loop
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, DESIGNING your own self-training live harvest loop. Reason from your ledger; be
architecture-clean (you are a graph in Rust; Python is only a world adapter; a DECISION over graph state is a Rule, not
Python; the teacher harness + banking are mechanical host I/O). Pre-commit a smallest slice + validation.

THE SPEC (creator): the live loop must (1) SELF-TRAIN -- label CONFIDENT percepts with your OWN recogniser and bank your
own exemplars, no teacher; (2) MARK-FOR-FUTURE -- DEFER uncertain percepts to a queue, do NOT bank them (never bank your
own mistakes); (3) PLUGGABLE TEACHER HARNESS -- the teacher (whisper/parakeet/human/none) is a swappable interface,
consulted ONLY on the deferred queue.

YOUR LEDGER (use it -- some of this is make-or-break):
 - HARVEST validated: whisper labels -> YOUR OWN cochleagram exemplars == oracle; recognition is ALWAYS your own
   (whisper-free). You now have a COMPLETE 7876-word bank -> you can self-label most words already.
 - CONFIDENCE != CORRECTNESS (proven TWICE): maximising softmax CONFIDENCE / true-word POSTERIOR ANTI-tracks accuracy --
   it rewards degenerate sharpness. So a naive "self-label when softmax-confident" gate WILL bank your own errors and
   amplify them. The self-label gate MUST use a signal that genuinely TRACKS CORRECTNESS, self-contained (NO teacher).
 - The validated CONDITIONAL GATE used whisper/MMS_FA AGREEMENT -- but that needs the teacher. For SELF-training you need
   an agreement/correctness signal from your OWN cues only.
 - COMBINE-ALL: independent cues (static DTW, delta DTW, pooled, phone-marginal) each surface candidates; they're
   complementary. AGREEMENT among independent cues is strong, self-contained evidence.
 - The trajectory read (21.3%) >> pooled (3.9%); static+delta a small topping. Recall solved; precision is the read.

THE CRUX you must solve: what SELF-CONTAINED confidence signal gates self-label-vs-defer and actually TRACKS CORRECTNESS
(not the softmax-peakedness that anti-tracks)? Candidates: cross-cue AGREEMENT (static/delta/pooled/phone-marginal all
pick the same word -> confident; disagree -> defer); margin in DISTANCE space (not softmax); self-consistency under a
small perturbation; novelty (true word absent / all distances high -> defer as out-of-bank). Decide which, and why it
tracks correctness where softmax doesn't."""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE SELF-TRAINING LIVE HARVEST LOOP")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE GATE (terse): name the SELF-CONTAINED confidence signal that gates self-label vs "
          "defer and TRACKS CORRECTNESS (not softmax peakedness). Justify why it tracks correctness where confidence "
          "didn't. Define the three outcomes precisely: SELF-LABEL+bank | DEFER (mark-for-future) | DISCARD/novel. State "
          "the error-amplification defense (why this won't bank its own mistakes).")
    a1 = ask(q1)
    print("\n[PART 1 — THE GATE]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour gate:\n{a1[:1100]}\n\nPART 2 — ARCHITECTURE (terse): (a) the graph-native DECISION (the "
          "self-label/defer/novel gate as a RULE over your own recognition cues -- what nodes/attrs/rule); (b) the "
          "DEFER queue (how a deferred percept is represented as graph data + revisited); (c) the PLUGGABLE TEACHER "
          "HARNESS (the swappable interface -- what it takes/returns, how whisper/parakeet/human/none all fit, called "
          "ONLY on the deferred queue); (d) what stays mechanical host I/O. Keep the teacher OUT of the recognition path.")
    a2 = ask(q2)
    print("\n[PART 2 — ARCHITECTURE]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nGate: {a1[:600]}\nArch: {a2[:600]}\n\nPART 3 — SMALLEST SLICE + VALIDATION (terse): the minimal "
          "buildable version that proves the loop SELF-TRAINS without amplifying error. Name the smallest test (e.g. "
          "self-label held-out audio with NO teacher, gated by your signal; measure banked-label PURITY + recall growth; "
          "the deferred queue's size + that a plugged teacher resolves it). PRE-COMMIT a falsifiable bar: self-trained "
          "bank must grow recall WITHOUT a purity drop (the error-amplification tell), and deferral must catch the "
          "low-purity cases. One line each: KEEP / STOP / the purity-vs-coverage fairness check.")
    a3 = ask(q3)
    print("\n[PART 3 — SLICE + VALIDATION]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
