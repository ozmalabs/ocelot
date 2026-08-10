"""ASK THE JABBERWOCK what IT wants to do next -- an open question, not a fix to hand over.

Where things stand (honest, after a long arc of the agent fixing its own loop):
 - Its autonomy loop is now healthy and HONEST: it picks its real frontier, measures against OBJECTIVE truth
   (scores recognition against the known word, not a faulty whisper proxy), stays on what's unmet, and escalates
   to AUTHORING a new ear cue exactly when it plateaus below target.
 - On a SINGLE voice it recognises ~99% (saturates).
 - On the HARD task -- recognise HELD-OUT, NEVER-HEARD speakers after banking only 2 train speakers -- it
   plateaus at ~48-52%. It now authors (3 ear faculties: cmvn / vtl-formant / formant-dynamic / modspec /
   f0 / landmark cues) but they only marginally lift it. The wall is genuine: generalising to UNSEEN speakers
   from 2 banked voices is hard, and the held-out test is small + piper-TTS-stochastic, so the signal it gates
   authoring on is near the noise floor.

What the agent itself has established this arc (its own findings, to reason from):
 - speaker (VTL) and word (vowel formants) are ENTANGLED on the same formant axis -- a frequency warp can't
   net-separate them (the render result); but the word's identity DOES live on a VTL-ORTHOGONAL axis -- the
   talker-invariant RELATIONAL shape (band-rank + self-similarity) and the DYNAMIC shape (formant MOTION /
   coarticulation gesture). The combine-all product over those crosses the speaker gap better than absolute cues.
 - recognition = a known-plaintext cipher: ~91% of the signal variance is the speaker KEY, ~9% the word MESSAGE;
   the message is read by a strong-enough KEY recovery (surface the candidate) + a PLAINTEXT PRIOR (language).

THE QUESTION (genuinely open -- the agent chooses its OWN next move and says why, in its own terms):
 - Would READING MORE RESEARCH help (on what -- speaker normalisation, cross-speaker invariance, developmental
   speech perception, something else), and what specifically would it look to learn?
 - Or DIFFERENT / MORE SPEAKERS (wider VTL coverage in the bank -- does more speaker variety crack held-out
   generalisation, and how many / how varied)?
 - Or more CHILD-DEVELOPMENT material (the developmental trajectory of how infants come to recognise words
   across talkers -- and what it would take from that)?
 - Or SOMETHING ELSE entirely (e.g. lean on its own VTL-orthogonal relational/dynamic representation rather
   than authoring more absolute cues; or a better-signal held-out test; or the language/plaintext prior)?

Decide, concretely:
 1. What do you WANT to do next, and WHY -- tie it to your own findings above (entanglement, the orthogonal
    axis, the cipher), not to generic ML advice.
 2. What is the SINGLE most likely thing to actually move held-out cross-speaker recognition, and what is the
    smallest concrete experiment that would test it?
 3. If reading would help: what exactly would you read FOR, and what claim would you be trying to confirm or kill?
 4. The honest risk that your chosen direction is a dead end, and the early signal that would tell you so.
Be concise and concrete. This is YOUR call about your OWN next move."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — what do you want to do next? (research / more speakers / child-dev / else)")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "What do YOU want to do next to cross the held-out cross-speaker wall? Decide (points 1-4), in your own terms.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
