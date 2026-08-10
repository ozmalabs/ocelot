"""THE JABBERWOCK ANALYSES THE CREATOR'S IDEA — "we don't need BPL, we need more recursion".

Not a leading consult: the agent is given its OWN arc + primitives + NEGATIVES, the creator's idea, and asked to
analyse it honestly -- the case FOR, the strongest case AGAINST, what its own evidence does and does NOT prove,
where the idea breaks, and whether/what to build. Two calls (advocacy + adversary) so the critique is separated
from the endorsement, then the agent's own synthesis.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_analyses_recursion
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock -- a graph-resident agent running one loop in a Rust substrate. Analyse a claim
your creator just made, IN YOUR OWN TERMS (your experiments, your primitives, your negatives). Do not flatter; if
the claim is wrong or half-right, say so and say exactly where.

YOUR ARC (facts, not opinions):
 - YOUR LOOP: the understand-drive -- frontier_pick a CapabilityAxis by (1 - saturation) [attend where you predict
   WORST], investigate it with a bound operator, bank the MEASURED prediction error. The same loop, unedited, ran
   on research capabilities, then on your EAR (onset/cadence prediction), then on phone alignment. `measured` is
   faculty-agnostic.
 - GLYPH (Omniglot one-shot): you reached ~78-80%. The decisive move: the PARSE is uncertain, so you carried K
   parse hypotheses and MARGINALISED over them with a soft-min (log-sum-exp at temperature beta) instead of
   committing to one MAP parse -- soft beat MAP, your 79.9% peak. FOUR separate LEARNED representations (k-means
   codebook, bag-of-primitives, soft-membership, WCCN) all HURT: each discarded structure (layout/order) the raw
   geometric match used. The wins were structure-preserving + the marginal inference. The arc bottomed out where a
   NEW Rust primitive was needed (PointSetDist, ShapeContextDist, SmoothDeformDist) -- those you could NOT compose
   from what you held.
 - SPEECH: content-word recognition is rare-as-wholes / common-as-phones. A whole-word fixed vector blurs a content
   word; a multi-scale PYRAMID (whole+halves+quarters, combine-all over scales -- each token uses the resolution
   that separates it) lifted content acoustic recall 7.7->20.8%. REALIGNMENT within whole-word (DTW re-rank,
   landmark chunks) were NEGATIVES -- alignment was not the residual there. Then OPEN VOCABULARY: you read a
   NEVER-BANKED word from a PHONE LIBRARY by the forward algorithm (soft-DTW = log-sum-exp over phone alignments) --
   18% top-1, 4.5x chance. That was your GLYPH marginal-inference insight, transferred from parse-pairings to
   alignment-paths, one level down (word -> phones).
 - THE FAILURE: when you BOLTED the phone reader BESIDE the whole-word decoder (one flat lexicon, two heterogeneous
   scorers z-normalised onto a common scale), it FAILED -- OOV stayed 0%, AND in-vocab DROPPED 17->11%. The
   two pools compete by construction; the calibration seam is where it broke.

WHAT YOU HOLD (could compose): the scale-free loop; the marginal-inference primitive (graph-native log-sum-exp over
parses); parse operators at different levels (sonority_segment for speech, turning-angle corners for glyphs);
mint_impasse_from_stall (high prediction error -> a new goal); self-extension (author a new primitive on a wall).

THE CREATOR'S CLAIM (analyse THIS):
 "The realisation was that we needed BPL -- but BPL is more or less MICRO-INSTANCES OF THE LOOP. We don't need BPL,
  we need MORE RECURSION. Cognition is nested far more than we thought -- our 'cortex' goes into sub-cortexes, and
  each layer is its own loop that has mini-loops. So: don't build a per-domain BPL machine; make the LOOP RECURSE --
  on impasse (high prediction error on a whole), DECOMPOSE into parts (parse), run the SAME loop on each part,
  COMPOSE back up, MARGINALISING over the parse; bottom out at primitives."
"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK ANALYSES: 'we don't need BPL, we need more recursion'")
    print("=" * 100)

    q1 = (GROUND + "\n\nANALYSE (be terse, concrete, structured):\n"
          "1. Is BPL really 'the loop, one level down'? Map your glyph-BPL and your speech phone-read onto the loop "
          "EXACTLY -- which step of (frontier/predict, parse, marginalise, compose) is which, or say where the map "
          "FAILS.\n"
          "2. What does YOUR OWN evidence PROVE about the recursion claim, and what does it NOT prove? Use the "
          "phone-read success AND the open-vocab bolt-on failure specifically.\n"
          "3. Your FOUR learned negatives and your 'must-add-a-Rust-primitive' base cases -- what do they CONSTRAIN "
          "about how recursion must work (or whether it can be fully general)?")
    a1 = ask(q1)
    print("\n[ANALYSIS]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + "\n\nNow STEELMAN THE OPPOSITE. Make the STRONGEST case that the creator is WRONG -- that 'more "
          "recursion' is NOT the lever, or is a category error. Consider: (a) is the open-vocab failure a calibration "
          "bug that recursion does NOT actually fix? (b) does recursion just MOVE the calibration/composition "
          "problem to every level instead of removing it? (c) are your wins actually due to the PARSE/representation "
          "and the PRIMITIVES, with 'recursion' being a post-hoc story? Be your own harshest critic. Terse.")
    a2 = ask(q2)
    print("\n[STRONGEST CASE AGAINST]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nYour own analysis so far:\nFOR/ANALYSIS:\n{a1[:1500]}\n\nAGAINST:\n{a2[:1500]}\n\n"
          "SYNTHESISE: one paragraph. Is the creator right, half-right, or wrong -- and in WHAT PRECISE FORM? Then: "
          "would you BUILD a recursive recognition faculty? If yes, state the SMALLEST decisive experiment that "
          "would prove recursion is the lever and not the parse/primitives -- one your own substrate can run. If no, "
          "say what to build instead.")
    a3 = ask(q3)
    print("\n[SYNTHESIS + VERDICT]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
