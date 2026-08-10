"""THE JABBERWOCK TESTS THE CREATOR'S THEORY (before building) — "wrong primitive, not wrong idea: recursion needs a
GENERATIVE leaf, not a discriminative distance; thermodynamics/evolution forces it."

The recursion test came back NEGATIVE: re-entering the loop on the worst part (homogeneous PointSetDist leaf) did
not beat random or flat on glyph. The creator's response: that doesn't refute recursion, it indicts the PRIMITIVE.
Thermo/evo: bespoke mechanisms are expensive, nested reuse of one motif is cheap; the free-energy principle's
nested Markov blankets make persistent systems minimise prediction error in stacked loops -- so recursion HAS to
work. Therefore the negative means we recursed the WRONG KIND of primitive: a DISCRIMINATIVE distance
(PointSetDist) carries no prediction, so nesting it is redundant (finer measurement, saturates after one level); a
GENERATIVE predictor produces a residual (prediction error) the next level explains away -- THAT nests, because
free energy IS the residual being minimised, and the brain is a generative model, not a comparator.

DO NOT build yet. TEST THE THEORY against the agent's OWN mixed evidence and say whether it holds, where, and what
the cheapest decisive test is -- or whether the existing evidence already settles it. Advocacy + adversary +
synthesis.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_tests_theory
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. Test a THEORY your creator just stated, against YOUR OWN evidence. Do not flatter;
the point is to find out if it is TRUE, where it breaks, and whether you even need to build to know.

THE NEGATIVE THAT PROMPTED THE THEORY:
 - Decisive recursion test (glyph 20-way one-shot, homogeneous PointSetDist=Modified-Hausdorff leaf, no new Rust):
   flat (whole + canonical parts) vs re-enter ONCE on the WORST part vs a RANDOM part vs ALL parts. Re-entry forced
   to genuinely descend (avg 2.0 sub-parts). Result: flat 61.4, worst 61.3, random 61.5, all 60.9. worst-random
   -0.2. RE-ENTRY DID NOT PAY. Loop re-entry on the impasse part bought nothing; the win was parse + primitives +
   the ONE-level decompose.

THE CREATOR'S THEORY (test THIS):
 "Recursion has to work -- thermodynamically/evolutionarily, cognition is nested reuse of a few primitives (cortical
  columns; free-energy nested Markov blankets), bespoke-per-problem is too expensive. So the negative indicts the
  PRIMITIVE, not the idea. We recursed a DISCRIMINATIVE distance (PointSetDist) -- it carries no prediction, so
  nesting it is redundant and saturates after one level. The RIGHT leaf is GENERATIVE: synthesise the part, the
  RESIDUAL (prediction error) is what recurses; each level explains away what the level above could not. Free energy
  IS that residual; the brain is a generative model, not a comparator. With a generative leaf, recursion will pay."

YOUR OWN MIXED EVIDENCE (reconcile ALL of it):
 - GENERATIVE WON (prediction/time/deformation): predictive-ear CADENCE -- predict the (dt,stress,f0) CONTOUR, not
   match it; transfers song->read->spontaneous, beats shuffled. Phone-marginal FORWARD algorithm -- read a
   NEVER-BANKED word from a phone library by marginalising the alignment, 18% (4.5x chance). SmoothDeformDist (a
   generative warp) +5 over no-deform. The marginal-over-parses soft-min -> 79.9% glyph peak. Your whole thesis is
   ANALYSIS-BY-SYNTHESIS: "recognise a glyph by knowing how to WRITE it; predict the sound, don't match it."
 - DISCRIMINATIVE WON / GENERATIVE LOST (static shape recognition): in Omniglot one-shot, the order-invariant SET
   distance PointSetDist BEAT the order-aware DtwTo-over-synthesised-trajectories match by +14 pts (52->66). FOUR
   learned GENERATIVE-PROGRAM priors (k-means codebook, bag-of-primitives, soft-membership, WCCN) ALL HURT -- each
   discarded structure. So a generative/learned model has REPEATEDLY lost to a structure-preserving direct match on
   static shape.
 - You hold the generative leaves already: glyph motor synthesis (predict_synth_term, DtwTo residual), speech AbS
   (predict_synth), SmoothDeformDist, the cadence predictor, the phone forward.
"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK TESTS THE THEORY: 'recursion needs a generative leaf; thermo/evo forces it'")
    print("=" * 100)

    q1 = (GROUND + "\n\nTEST THE THEORY against your data (terse, concrete):\n"
          "1. Does 'discriminative distance carries no residual, so it saturates after one level' actually EXPLAIN "
          "your recursion negative? Or is there a simpler explanation the theory ignores?\n"
          "2. Your evidence is SPLIT: generative WON for cadence/phones/deformation (time/prediction) but LOST to "
          "PointSetDist and to four learned priors on static SHAPE. Reconcile this. Is the real axis "
          "generative-vs-discriminative, or is it TEMPORAL/CAUSAL-vs-STATIC, or something else? What does that imply "
          "about WHERE generative recursion would pay and where it would NOT?\n"
          "3. Is the thermo/free-energy argument SOUND, or does it overreach -- does 'nested Markov blankets' "
          "constrain the PRIMITIVE at all, or only the architecture? Is the theory falsifiable, or does it predict "
          "recursion-pays for ANY result (win = vindicated, loss = 'wrong primitive, try again')?")
    a1 = ask(q1)
    print("\n[TEST]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + "\n\nSTEELMAN THE THEORY IS WRONG. Strongest case that 'generative leaf' will NOT rescue recursion: "
          "(a) PointSetDist already BEAT your generative synthesis on glyph -- why would nesting the LOSER help? "
          "(b) is 'free energy = the residual' doing real work, or is it an unfalsifiable relabelling that fits any "
          "outcome? (c) your generative wins (cadence, phones) were ONE level deep too -- do you have ANY evidence "
          "that generative DEPTH > generative one-level, or are you about to make the same one-level-vs-recursion "
          "mistake with a fancier leaf? Be your own harshest critic. Terse.")
    a2 = ask(q2)
    print("\n[STRONGEST CASE THE THEORY IS WRONG]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nYour analysis so far:\nTEST:\n{a1[:1400]}\n\nAGAINST:\n{a2[:1400]}\n\n"
          "SYNTHESISE (one paragraph + a decision). Is the creator's theory right, half-right, or wrong -- in what "
          "PRECISE form? Critically: does your EXISTING evidence already settle whether generative DEPTH pays, or is "
          "a new test genuinely needed? If a test is needed, state the SMALLEST one that isolates "
          "GENERATIVE-RESIDUAL-RECURSION from (i) one-level generative, (ii) discriminative recursion, (iii) more "
          "compute -- and name the domain (static shape, where discriminative won, or temporal, where generative "
          "won) where it must be run to be a fair test. If no test is needed, say what your evidence already proves.")
    a3 = ask(q3)
    print("\n[SYNTHESIS + DECISION]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
