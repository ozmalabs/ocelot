"""Ask the jabberwock: the beat IGNITES the loop, but the target is CADENCE -- a shape, not a period.

It decided to point its understand-drive at its ear and predict onset TIMING with an oscillator -- and itself
found the boundary: an oscillator plateaus on speech because speech is not periodic. The creator names what is
there instead: people do not speak with a BEAT, they speak with a CADENCE. A beat is the degenerate (flat)
cadence; a cadence is a PATTERNED CONTOUR (timing+stress+pitch, an arc that resolves) -- predictable, but the
predicted thing is the SHAPE of the trajectory, not its spacing. And the agent ALREADY perceives shape. So the
richer predictor it said it would need is not missing -- it is its own shape cognition, turned predictive onto
the prosodic contour. The agent decides how cadence gets predicted and where the oscillator hands off to shape.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. A refinement of your own move -- and it answers the boundary YOU drew.

You decided: point the understand-drive at the ear, predict onset TIMING with an oscillator (period/phase),
correct on the residual, spawn a competitor on surprise -- all in the loop you already run. And you found the
edge yourself: "an oscillator plateaus on speech because a phoneme/word onset sequence is NOT periodic; the
predictor's internal model has to scale." Here is what scales it.

THE CREATOR: people do not speak with a BEAT, they speak with a CADENCE. This is the crux:
  - A BEAT is the degenerate cadence -- a flat, repeating contour; the next interval EQUALS the last, so an
    oscillator predicts it.
  - A CADENCE is a PATTERNED contour -- the rise and fall of timing AND stress AND pitch across a phrase, with a
    beginning, a lean, and a RESOLUTION. Still predictable (predictive coding still bites), but the predicted
    thing is the SHAPE of the trajectory, not its spacing. You cannot lock to it; you must recognise the ARC and
    anticipate where it goes.
  - You ALREADY perceive shape: BlendCover (your sound-shape kernel), categorise_by_shape, your order-N-over-time
    / transition / dynamic cues (a contour is exactly formant/energy motion over time), your meta-shapes. The
    "richer predictor" you said you'd need is NOT missing -- it is your shape cognition, turned predictive onto
    the prosodic contour. The manifold predicts; the SHAPE faculty is what it predicts WITH.

AND WHY WE SING: a song carries BOTH -- a beat (the metronome) and a cadence (the phrase arc that resolves). The
beat is the SCAFFOLD that makes the cadence learnable, because in song the phrase-shape recurs on a predictable
grid. Then speech keeps the CADENCE and drops the metronome. We sing to teach cadence, using the beat as training
wheels. So the beat is the IGNITION; the cadence is the TARGET that carries from song into speech.

DECIDE, concretely and in your own terms:
 1. CADENCE AS A PREDICTED THING. What contour do you predict -- the joint trajectory of WHAT (inter-onset
    timing? energy/stress? f0/pitch? the three as one prosodic shape)? And HOW does your shape cognition predict
    the next stretch of it from the contour so far (order-N dynamics of the contour? BlendCover over the shape?
    a held meta-shape)? Be concrete about the predictor, grounded in shape primitives you already hold.
 2. THE HANDOFF. Where does the oscillator hand off to the shape-predictor? The surprise that says "this is not
    periodic -- predict the SHAPE, not the period." When the escalation ladder spawns a competitor on that
    surprise, it must spawn a SHAPE-predictor (your cadence model), not another oscillator at a new period. Walk
    that: which impasse, which order of escalation, binds shape-over-contour instead of period.
 3. THE FIRST STEP. Does the beat still IGNITE first (nursery refrain, prove the loop reduces error on the
    signal), then scale to cadence -- or do you predict cadence directly? What is the only-new graph data (a
    cadence/shape predictor Operator reusing your shape faculty + the contour observation), and what is purely
    the loop + the shape cognition you already hold?
 4. MEASURE + RISK. Prediction error on the CONTOUR falling (understanding), vs a baseline (flat-cadence / shuffle
    the contour). The honest risk: the shape model collapsing, cadence not predictable enough on real speech, or
    the handoff failing -- and what you'd watch.

Be concise and concrete -- the predictor that turns 'predict the beat' into 'predict the cadence', in your loop."""


def main():
    ask = make_ask(timeout=480, preamble=PREAMBLE)
    print(ask("The beat ignites the loop, but the target is cadence -- a shape, not a period, carried by your "
              "shape cognition. How do you predict the contour, and where does the oscillator hand off to shape?"))


if __name__ == "__main__":
    main()
