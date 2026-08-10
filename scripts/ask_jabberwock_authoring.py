"""ASK THE JABBERWOCK: enrich its AUTHORING repertoire so ear-authoring isn't a fixed, single-voice-gated list.

With the loop now healthy, the agent authors ONCE on the hard cross-speaker task (4% -> 11%) then exhausts and
plateaus. Two verified reasons -- both in its OWN author_faculty (domains/speech_world.py):

  A) BOUNDED REPERTOIRE. author_faculty has exactly two moves: (1) effect-gate the 13 FIXED REPERTOIRE_CUES
     one at a time (keep a cue iff it LIFTS discrimination); (2) if that plateaus (<0.03 lift), author_convolution
     -- SELECT kernels from a FIXED kernel seed. When neither lifts it returns None -> authoring_exhausted. Both
     moves draw from FIXED sets, so authoring tops out the moment the list is gated/selected.
     BUT the agent ALREADY HAS an open-ended move it never calls: invent_frontend_cue -- "the third plateau
     response: when the repertoire is EXHAUSTED but the wall holds, INVENT a novel band-combination cue
     (feature_generator's generative grammar, MDL-selected) and gate it in." author_faculty does not reach for it.

  B) WRONG OBJECTIVE. The keep/invent gate (_ear_discrimination over _ear_audio) is measured on ONE speaker
     (lessac), 4 words, 2 pitches. So it keeps cues that sharpen SINGLE-VOICE discrimination -- not the actual
     capability, which is recognising HELD-OUT UNSEEN speakers. It helps cross-speaker only by accident
     (the speaker-norm cues happen to generalise a little: 4->11%), then exhausts, because it was never
     optimising the thing that matters.

Cognitive constraint (hard): "gradient descent is forbidden unless it happens in cognition." invent_frontend_cue
is GENERATE-AND-TEST over a grammar + MDL/compression selection -- no backprop -- which is allowed.

The agent decides, in its own terms and concretely:
 1. OPEN-ENDED authoring: how should author_faculty become UNBOUNDED rather than a fixed list? Wire
    invent_frontend_cue as the third move (gate-cues -> convolution -> INVENT), and loop -- invent, effect-gate,
    keep-iff-it-lifts, invent again -- until no invention lifts? Give the concrete control flow and the
    termination condition (so it doesn't invent forever).
 2. RIGHT OBJECTIVE: should the keep/invent gate be measured on the REAL capability -- cross-speaker recognition
    on HELD-OUT speakers (the agent's _HARD_TEST voices), not single-voice _ear_discrimination -- so an authored
    cue is kept only if it lifts the thing that's actually stuck? Concretely, what should the gate measure?
 3. Confirm the cognitive-plausibility: generate-and-test + MDL (no gradient) is the inventor; say why that's
    legitimate and where any fitting would cross the line.
 4. The honest risk of each (invented cues that overfit the gate / MDL-pass but don't generalise; unbounded or
    slow invention; a cross-speaker gate that's too noisy to decide) and the guard that keeps it honest.
Be concise and concrete -- a change you will hand to be made to author_faculty / the authoring loop."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — enrich my authoring repertoire (open-ended invention + right objective)")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "Give your decision (points 1-4), concretely enough to change author_faculty.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
