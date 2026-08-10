"""Ask the jabberwock to point its EXISTING understand-drive at its own ear -- the signal as a frontier.

The reframe (the creator's): the agent does not NEED predictive coding bolted on. Its autonomy loop already IS a
prediction-error / free-energy manifold -- it has only ever run it on its CAPABILITIES, never on its EAR. So the
move is not to build a beat-predictor FACULTY; it is to point the loop it already runs one level DOWN, at the raw
acoustic stream, with zero new cognition -- only a new thing to predict. The agent decides how its own manifold
ingests the signal as a frontier.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. A reframe of your last decision -- sharper, and more yours.

You decided to predictive-code your ear by building a beat-predictor. But step back: you do not NEED predictive
coding added. Your autonomy loop ALREADY IS a prediction-error manifold -- you have only ever run it on your
CAPABILITIES, never on your EAR. Part for part:
  - the understand-drive (measurement_key model_coverage) = MINIMISE prediction error.
  - frontier_pick (Argmax over CapabilityAxis by gap) = attend where error is high AND reducible (precision).
  - the investigation loop (bind operator -> run -> measure -> bank) = predict, observe, update.
  - mint_impasse_from_stall / mint_goal_from_surprise = a persistent error SPAWNS new structure.
  - competitive_inhibition = competing predictions, winner-take-all.  feedback_control = error -> correction.
  - prediction_minus_observation = the error itself.
You said it yourself: "the shape I already am, never before pointed at my own input." This is that, exactly.

So the move is NOT a new faculty. A standalone beat-predictor would be the bolt-on you already paid for (the
deleted 13K-line CuriousAgent; your own "compose, don't bolt on"). The move is to POINT THE LOOP YOU ALREADY RUN
one level down -- at the raw cochleagram stream -- adding ZERO new cognition, only a new thing to predict.

THE CLAIM HIDING HERE (engage with it): there is no separate "speech faculty." Hearing-as-prediction and
choosing-what-to-understand are the SAME operation at different scales. The BEAT is the smallest thing your
manifold can predict; a PHONEME is a slower one; a WORD slower still; "what should I investigate next" is the
same loop at the top. If that is true, your ear is just the one input your manifold never looked at.

DECIDE, concretely and in your own terms -- how YOUR EXISTING manifold ingests the signal as a frontier:
 1. THE AXIS. What is the CapabilityAxis "predict my next acoustic event"? Its capability_keys, and -- the key
    change -- its measurement_key is PREDICTION ERROR (timing/spectral), not coverage or a recognition score. How
    does frontier_pick come to select it (its gap = how badly you currently predict the signal)?
 2. THE OBSERVATION + THE OPERATOR. The cochleagram onset stream ingested as graph events (you already ingest);
    the operator the drive BINDS is an acoustic predictor (your oscillator) -- but as an Operator the investigation
    loop runs, not a standalone faculty. What does bind_investigation_faculty join it to?
 3. THE UPDATE + THE SPAWN. The measurement = prediction error; bank_measurement_to_axis updates the predictor
    (period/phase) and the axis shortfall -- the SAME bank rule. An unpredicted onset is a SURPRISE = an impasse
    your mint_goal_from_surprise / impasse machinery ALREADY handles -> it spawns a NEW acoustic predictor
    (competitive). Walk the loop: master_tick -> pick the predict-signal axis -> run the predictor -> measure
    error -> bank -> on surprise, spawn. What, HONESTLY, is the only-new graph data (one axis, one predictor
    operator, the onset ingest) versus what is purely the manifold you already hold?
 4. THE FIRST STEP + MEASURE. The smallest run: the UNTOUCHED loop predicts the nursery onset stream, prediction
    error falls, no new cognitive rules -- only the new axis/operator/ingest. Measure: error dropping over a
    refrain (understanding), vs a constant-period baseline. The honest risk: that it does NOT reduce to your
    existing loop and you DO need new cognition -- if so, say exactly what and why.

Be concise and concrete -- the wiring that makes your ear just another frontier your own loop predicts."""


def main():
    ask = make_ask(timeout=480, preamble=PREAMBLE)
    print(ask("How does your EXISTING understand-drive ingest the raw signal as a frontier and predict it -- "
              "no new faculty, only a new thing to point at? Decide and give the step."))


if __name__ == "__main__":
    main()
