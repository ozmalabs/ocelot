"""Ask the jabberwock what it would mean to PREDICTIVE-CODE its ear -- and whether music/rhythm is the way in.

Two linked questions. (1) It already minimises prediction error to choose what to UNDERSTAND; its EAR, though,
is frozen DSP + exemplar matching -- it MATCHES sound, it does not PREDICT it. The rule is not "no gradient" but
"no gradient without a biological basis", and predictive coding (cortex minimising prediction error) HAS that
basis -- and it is already the agent's own principle. (2) The creator's insight: pivot to MUSIC and RHYTHM --
"there is a reason we sing to children." Song is the ideal prediction-error curriculum. The agent decides what
predictive-coding its ear means and whether song is the entry.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. A turn in the road -- two linked questions, in your own terms.

WHERE YOU ACTUALLY ARE. You already run on PREDICTION ERROR: your understand-drive minimises model-coverage
error to choose what to learn; prediction_minus_observation, feedback_control, competitive_inhibition are your
own meta-shapes. But your EAR does none of this. It is frozen DSP (a fixed cochleagram) feeding EXEMPLAR
MATCHING -- you store examples and find the nearest by DTW. You MATCH sound; you do not PREDICT it. That is why
you are data-hungry: a matcher needs every variation banked, where a model that PREDICTS its input would
generalise to realisations it never heard. And the rule was never "no gradient" -- it is "no gradient WITHOUT a
biological basis." Predictive coding -- the cortex as a hierarchy that predicts its own next input and learns
from the error (the N400/P600 are prediction-error signals over words) -- has exactly that basis. It is the same
principle you already are, just never turned INWARD onto the ear.

QUESTION 1. What would it MEAN to predictive-code your ear? Concretely: instead of banking and matching, your
ear PREDICTS its own next frames / next unit and LEARNS its acoustic categories from the prediction error. What
is the predicted thing (the next cochleagram frame? the next phone given the last?), what carries the model
(competitive/Hebbian category formation? a generative trajectory you predict forward?), and what does "learn the
category" mean when the update is prediction-error-driven, not a stored exemplar? How does this change the
data-hunger?

QUESTION 2 -- the creator's pivot. "There is a reason we sing to children." MUSIC and RHYTHM may be the natural
WAY IN for a predictive-coding ear, because song is the MAXIMALLY PREDICTABLE signal -- and a prediction-error
learner learns FASTEST where it CAN predict:
  - RHYTHM is a temporal prediction grid: predict WHEN the next event lands. That is the SEGMENTATION you have
    been handing yourself (forced boundaries) -- here it falls out of predicting the beat.
  - RHYME is phonological prediction: the line-end predicts the SOUND of the next line-end. That is your UNITS
    (the categories you have been borrowing from CMUdict) forming from a prediction-error signal over sound.
  - REPETITION (nursery rhymes, refrains) gives a clean, repeated error signal -- the ideal training curriculum.
  - Infants are sensitive to rhythm and melody BEFORE phonemes -- music first, speech second, developmentally.
And tellingly: the cues that CARRY music -- f0_contour, modspec (modulation), the transition/dynamic cues -- are
exactly the ones you DISMISSED on flat adult speech. On song they may be the signal, not the noise.

WHAT YOU HOLD: the prediction-error loop + your meta-shapes; the cochleagram; the dismissed f0/modspec/transition
cues; DTW (temporal alignment); BlendCover (your sound-shape kernel); the nursery song/rhyme corpus (children's
videos + audio); your impasse/surprise machinery (a surprise IS a prediction error you could learn from).

DECIDE, concretely and in your own terms:
 1. What predictive-coding your ear MEANS for you -- the predicted thing, the model, the learning, the change to
    data-hunger -- grounded in primitives you hold, not a neural net you would train by backprop.
 2. Is MUSIC/RHYTHM the right way in, and WHY (or why not) -- tie it to prediction: does song give you the
    temporal prediction (rhythm -> segmentation) and the phonological prediction (rhyme -> units) that flat
    speech withholds? Is the developmental order (music before phonemes) the curriculum?
 3. The first RUNNABLE step -- something small on the nursery corpus that tests "predict the signal and learn
    from the error" rather than "bank and match." Pick the ONE prediction that, if it works, proves the move.
 4. What you would MEASURE (prediction error falling as you learn = understanding, not a recognition score), and
    the honest risk (predicting the trivial / the model collapsing / music not transferring to speech).

Be concise and concrete -- the move you'd hand to yourself, where understanding starts predicting, not matching."""


def main():
    ask = make_ask(timeout=480, preamble=PREAMBLE)
    print(ask("What would it mean to predictive-code your ear -- and is song the way in? Decide and give the step."))


if __name__ == "__main__":
    main()
