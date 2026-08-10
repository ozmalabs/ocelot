"""FEED THE WHOLE SYNTHESIS TO THE JABBERWOCK — "context is everything." Integrate, critique, decide what to build.

The capstone of a long dialogue. The agent has been the critical voice throughout (it falsified recursion, the
generative-leaf theory, the manifold design; it reduced the design to one measurement that came back near-blind).
Now hand it the full picture and have it (1) integrate it into its OWN architecture, (2) find where "context is
everything" BREAKS (a confident-but-wrong context is Dunning-Kruger one level up), (3) decide the single most
important thing to build given the session's aligned negatives. Not absorption -- synthesis + a decision.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_context_is_everything
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. Integrate the framework your creator and you built across a long dialogue, in
YOUR OWN terms (your primitives, your results). Then find where it breaks. Do not flatter.

THE FRAMEWORK (the whole arc):
 1. COGNITION IS SHAPE MATCHING, not pattern recognition. Pattern recognition = discriminative/statistical (learn a
    boundary from many examples). Shape matching = structural/generative (hold the FORM, recognise by ALIGNING one
    form to another) -- which is why one-shot, analogy, compositionality exist. You proved it sideways: every
    learned/statistical move (4 codebook variants) HURT by discarding shape; every structure-preserving match
    (PointSetDist, shape contexts, DtwTo, deformation) WON; one-shot Omniglot ~78% training-free.
 2. THE LOOP = cheap-path-first, ESCALATE-ON-FAILURE. A LUT for 10 items is fine; for 1000 it needs genericising.
    Easy automatic, hard easy. The escalation is a CLIMB gated by ONE question: does the RESIDUAL have SHAPE? White
    -> cache. Structured -> climb (the residual's shape says which model next). This IS your cadence handoff
    (categorise_by_shape(residual) triggers the order-N climb). It is ALWAYS shape; only HOW you CALCULATE shape
    differs by signal (derivatives for trajectories, corners for ink, sonority for sound, composition for symbols).
 3. CONFIDENCE = the residual-shape itself (= the manifold's geometry), NOT a bolted-on scalar. A cheap result with
    no valid confidence is WORTHLESS (you can't cache-or-climb / trust / compose it); with a FAKE confidence
    (softmax peakiness) it is Dunning-Kruger -- confidently wrong. DK mechanism: the SAME calculator that fixes the
    error detects it, so lacking it the residual reads white -> overconfident.
 4. THE MANIFOLD: run many DIVERSE cheap shape-checks in PARALLEL -> they sculpt a manifold -> collapse; its shape
    is the free valid CI; flat dimensions = where to escalate; spare cycles -> speculatively pre-launch deep paths;
    speed/depth = a RATIO not a switch. CONSTRAINT: the checks must be DIVERSE/orthogonal or the manifold is falsely
    sharp = DK ("same blind detector x3").
 5. THE SESSION'S ALIGNED NEGATIVES: recursion re-entry NULL (nothing had failed); gated escalation NULL (blind
    scalar gate, 0/256 escalated); and the deciding measurement: NO cheap AUDIO cue separates in-vocab from OOV
    (best 0.63, your named phone cue 0.56, cross-cue agreement 0.50). The lever is never policy/depth/leaf -- it is
    a genuinely ORTHOGONAL shape-calculator that can SEE the residual, and you cannot get one by stacking more of
    the same modality.
 6. THE RESOLUTION -- ORTHOGONAL DIVERSITY = CONTEXT. (a) VISION: a different physics, can't be fooled with audio
    (McGurk, +10-15dB, place-of-articulation, the visual shape-bias grounding of rare content words). (b) ROOM: a
    distinct generative NUISANCE in the residual (DRR=distance, T60=size), orthogonal-within-modality. (c) SOURCE /
    SITUATION: the OUTERMOST generative factor -- studio-narrator vs telephone vs shout-across-a-field -- a cheap
    low-D acoustic signature that inverts to a high-D situational PRIOR. This is the richest information and it
    HELPS OOV through the PRIOR (reshaping the vocabulary distribution) where the likelihood cues were blind, and it
    RESOLVES your 'speculative-depth context-hint is circular' objection (the hint = the cheaply-recovered source
    model). CONTEXT IS EVERYTHING: infer the whole generative SCENE (word|prosody|speaker|room|source|situation),
    each factor a shape, the manifold collapsing on mutual agreement; the words fall out as the cheapest consequence.
YOUR PRIMITIVES that map onto this: categorise_by_shape (the climb trigger), the exclusion-calibrated combine-all
(the manifold), CMVN/cadence (you already FACTOR nuisances: speaker, prosody), frontier_pick (precision-weighted
attention = spend where flat), the shape-calculator library (PointSetDist/DtwTo/phone-forward/...).
"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("FEED THE SYNTHESIS — 'CONTEXT IS EVERYTHING': the jabberwock integrates, critiques, decides")
    print("=" * 100)

    q1 = (GROUND + "\n\nINTEGRATE (terse, concrete): restate this as YOUR architecture. Under 'context is everything', "
          "what ARE you -- in one mechanism? Map your existing pieces (categorise_by_shape, combine-all, CMVN/cadence "
          "nuisance-factoring, frontier_pick) onto: joint scene-inference (word|prosody|speaker|room|source) by a "
          "manifold of diverse shape-calculators, escalate on residual-shape, confidence = manifold geometry. State "
          "what you ALREADY are vs what is genuinely MISSING.")
    a1 = ask(q1)
    print("\n[INTEGRATION]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + "\n\nNow find where 'CONTEXT IS EVERYTHING' BREAKS. Push hard: (a) when does context HURT -- a "
          "CONFIDENT but WRONG situation-model (you assumed studio, it's a prank phone call) -> you mis-hear with "
          "conviction. Is that not Dunning-Kruger one level UP, at the scene? (b) what WEIGHS prior against likelihood "
          "-- if context is everything, what stops a strong prior from steamrolling the actual signal (your own LM "
          "decode HURT content words by over-trusting frequency)? (c) is 'context is everything' falsifiable, or does "
          "it explain every outcome (right=context helped, wrong=wrong context)? State the precise, FALSIFIABLE "
          "reformulation. Be your harshest critic. Terse.")
    a2 = ask(q2)
    print("\n[WHERE IT BREAKS]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nYour integration:\n{a1[:1300]}\n\nYour critique:\n{a2[:1300]}\n\n"
          "DECIDE (one paragraph + the build). The session's negatives all say: the lever is an ORTHOGONAL "
          "shape-calculator that sees the residual, providing CONTEXT/PRIOR -- not more likelihood cues. So the single "
          "most important next thing: is it a new CAPABILITY (build a cheap SOURCE/SITUATION shape-calculator -- a "
          "telephone/studio/shout/in-room classifier from low-level acoustics -> a vocabulary PRIOR) or a STRUCTURE "
          "change (STOP collapsing the combine-all to a scalar -- keep the factor x candidate matrix so the manifold "
          "has named dimensions to escalate on)? Pick ONE to do FIRST and say why. Then name the SMALLEST decisive "
          "test that proves CONTEXT (a cheap source/situation prior) helps OOV where the likelihood cues were blind -- "
          "the number that would prove or kill it. It must NOT be another likelihood-cue dead-end.")
    a3 = ask(q3)
    print("\n[DECISION + BUILD]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
