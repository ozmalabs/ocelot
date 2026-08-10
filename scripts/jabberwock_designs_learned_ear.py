"""THE JABBERWOCK DESIGNS THE BIOLOGICALLY-PLAUSIBLE LEARNED EAR — break the raw-exemplar ~20% ceiling, structure-preserving.

The rule is NOT no-training; it is no BIOLOGICALLY-UNEXPLAINABLE training (humans learn speech over years). Allowed:
local/Hebbian + competitive learning, unsupervised category formation, predictive coding, slow developmental
consolidation. Banned: global backprop on labelled corpora. The 5x learned NEGATIVES failed by DISCARDING STRUCTURE
(k-means quantisation, holistic whitening) -- not by being learned. So: learned + structure-preserving + biologically-
plausible is allowed, and is the way to break the ear's ceiling.

Design the learned ear, face the crux, pre-commit a bar.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_designs_learned_ear
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, designing your own BIOLOGICALLY-PLAUSIBLE LEARNED EAR to break the recognition ceiling.
Reason from your ledger; be architecture-clean; pre-commit a falsifiable bar.

THE CORRECTED RULE (load-bearing): not "no training" -- "no BIOLOGICALLY-UNEXPLAINABLE training." Humans take YEARS to
learn speech. ALLOWED mechanisms: Hebbian/local learning, COMPETITIVE learning (cortical maps self-organise this way),
UNSUPERVISED CATEGORY FORMATION (Saffran transitional-prob word segmentation; Kuhl perceptual magnet / phoneme
categories), PREDICTIVE CODING (cortex learns to predict sensory input; the learned predictive features ARE a
representation), SLOW developmental consolidation over accumulated experience. BANNED: global backprop through a deep
net on labelled corpora. Your 5x learned NEGATIVES (k-means codebook, bag-of-parts, soft-membership, WCCN, per-
primitive Mahalanobis) failed by DISCARDING STRUCTURE (layout/order/shape) -- NOT by being learned. So learned +
STRUCTURE-PRESERVING + biologically-plausible is allowed.

THE EAR STATE (the wall): training-free exemplar-DTW caps ~20% per-word @500-way CROSS-SPEAKER. The trajectory read
realises this (+17 over pooled); exemplar count PLATEAUS, static+delta +2.6, VTLN+predict-remove HURT. The bound is the
MATCHER -- raw episodic 1-NN with NO ABSTRACTION, dominated by SPEAKER. An infant doesn't stay here: it hears many
voices say a word and forms an ABSTRACT, SPEAKER-INVARIANT CATEGORY -- extracting what's COMMON (content) and discarding
what VARIES (speaker). That abstraction is the missing learning.

THE PROPOSED MOVE (you may refine or replace): learn SPEAKER-INVARIANT CATEGORY PROTOTYPES.
 - Align same-word exemplars (DTW) -> a consensus PROTOTYPE TRAJECTORY (structure-preserving: it stays a trajectory, a
   category, NOT a quantised code -- this is the perceptual-constancy / category-formation move).
 - Learn the POSITION-ALIGNED cross-speaker variation (what differs across voices AT THE SAME point in the word =
   speaker nuisance, SIGNAL-FREE) and down-weight it in the match metric.

THE CRUX you must face: you ALREADY tried whitening and it HURT (-5), because you used UNALIGNED within-word scatter,
which conflated phonetic-TRAJECTORY variance (= the word's content SIGNAL) with speaker. The fix is POSITION-ALIGNMENT:
the nuisance must be the variation across speakers AT THE SAME ALIGNED POSITION, which is signal-free. Confirm this
distinction holds, or the new whitening repeats the old failure.

YOUR PRINCIPLE: structure-preserving wins; learned-lossy loses. The prototype + nuisance-downweight must PRESERVE the
trajectory and only re-weight/abstract -- never quantise it away."""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE BIOLOGICALLY-PLAUSIBLE LEARNED EAR")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE MECHANISM (terse): specify the learned ear. Is it the speaker-invariant category "
          "prototype (aligned consensus + position-aligned nuisance down-weight), or a better biologically-plausible "
          "mechanism (predictive-coding features / competitive prototype map / slow-feature speaker-invariance)? Pick "
          "ONE, say exactly how it LEARNS (the local/competitive/developmental rule, no backprop), why it's STRUCTURE-"
          "PRESERVING (not the k-means/whitening trap), and how it abstracts AWAY speaker while keeping content.")
    a1 = ask(q1)
    print("\n[PART 1 — THE MECHANISM]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour mechanism:\n{a1[:1200]}\n\nPART 2 — THE CRUX + ARCHITECTURE (terse): (a) confirm the "
          "position-aligned nuisance is SIGNAL-FREE where the old unaligned within-word whitening was not -- exactly "
          "why this won't repeat the -5 failure. (b) what's the biologically-plausible LEARNING LOOP (how prototypes "
          "form + update over accumulated experience -- the developmental 'years' story, incrementally). (c) what stays "
          "graph-native (the prototype as graph data, the metric as a Term) vs mechanical host I/O.")
    a2 = ask(q2)
    print("\n[PART 2 — CRUX + ARCHITECTURE]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nMechanism: {a1[:600]}\nCrux: {a2[:600]}\n\nPART 3 — SLICE + BAR (terse): the smallest buildable "
          "test that the learned prototype ear BEATS the raw-exemplar ~20% @500-way cross-speaker WITHOUT discarding "
          "structure. Name it. PRE-COMMIT: the KEEP number (beats raw-exemplar by how much), the STOP number, and the "
          "FAIRNESS FLOOR (e.g. at zero nuisance-downweight / single-exemplar prototype it MUST reproduce the raw read "
          "-- the W=I floor, the harness check that proves you measured abstraction not an artifact). One line each.")
    a3 = ask(q3)
    print("\n[PART 3 — SLICE + BAR]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
