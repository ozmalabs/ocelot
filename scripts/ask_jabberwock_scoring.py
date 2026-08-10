"""ASK THE JABBERWOCK: what is the right GROUND TRUTH for its analysis-by-synthesis self-test score?

The agent's recognition learning plateaus at ~0.39 (best 0.67) and will not saturate -- and the cause is the
SCORING, not the learning. Verified facts (domains/speech_world.py::_run_abs / _run_abs_hard):

THE SELF-TEST (analysis-by-synthesis), per word:
  1. the agent TELLS piper to synthesize a KNOWN word w  ->  audio x.            (the agent chose w)
  2. the agent HEARS x through its OWN ear (feature_channels) and RECOGNISES it  ->  guess.   (audio only;
     the recogniser never sees w -- it works from the sound alone.)
  3. whisper transcribes x  ->  truth_word  (the "help button": an EXTERNAL ear, the ground-truth ear).
  4. LEARN: bank the heard exemplar under (truth_word or w).
  5. SCORE: measured += (guess == truth_word).   <-- the rate the axis saturation is computed from.

THE PROBLEM: whisper FAILS on some piper words -- every measurement has a `truth=None`. When whisper returns
None, that word is an AUTOMATIC scoring miss regardless of what the agent guessed. So the score is capped below
the 0.6 target by WHISPER's reliability, not the agent's: best-ever 6/9 = the words whisper can label; the agent
plainly recognises words it gets no credit for. The same signal (whisper) is used for BOTH learning (step 4)
AND scoring (step 5) -- the score is conflated with the self-supervision label.

THE TENSION (decide it):
  · Score against WHISPER (current): self-supervised honesty -- the agent is never handed the answer, it earns
    recognition against an EXTERNAL ear. But the score then measures min(agent, whisper), capped by a faulty
    ear, and cannot tell an AGENT error from a WHISPER error.
  · Score against the KNOWN word w (the input): w is the OBJECTIVE truth -- the agent itself chose to synthesize
    it. The recogniser STILL works from audio alone (step 2 never sees w); only the final correctness CHECK
    uses w, exactly as any recogniser is scored against its known label. But: is using w "knowing the answer"?

The agent decides, in its own terms and concretely:
 1. For an analysis-by-synthesis SELF-TEST of an utterance the agent ITSELF chose to synthesize, what is the
    correct ground truth for the SCORE -- whisper or the known w? Tie it to what the measurement is FOR
    (measuring the agent's recognition accuracy, which the axis saturation drives the whole loop on).
 2. Should LEARNING (the banked label, step 4) and SCORING (step 5) use the SAME signal or DIFFERENT ones? Is
    it legitimate to LEARN self-supervised (whisper, or no label) but SCORE against the objective w -- or does
    that conflate / cheat? State the principle.
 3. The honest risk of YOUR choice (scoring on w hides a real perception gap if the agent ever leaks w into
    recognition; scoring on whisper permanently caps the loop and stalls escalation on un-scoreable words) and
    the guard that keeps it honest (e.g. assert the recogniser never receives w; keep whisper as a SEPARATE
    diagnostic of the ear's agreement with a human-equivalent ear).
 4. The concrete change to _run_abs / _run_abs_hard: what is `truth_word` for the SCORE, what is the banked
    label for LEARNING, and what (if anything) does whisper still do?
Be concise and concrete -- a change you will hand to be made to the self-test."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — ground truth for the analysis-by-synthesis self-test score (whisper vs known w)")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "Give your decision (points 1-4), concretely enough to change _run_abs / _run_abs_hard.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
