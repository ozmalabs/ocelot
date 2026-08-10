"""THE JABBERWOCK LOCKS THE EARN-NOT-BORROW FAIL-FAST — under the creator's sharpened constraint.

You ruled KEEP-sobering on the learned-latent result (wav2vec2 81% cross-speaker REAL, but BORROWED from a frozen 95M net;
your novel SFA +2.3 noise next to free CMVN +16). You then picked a CPC encoder FROM SCRATCH (no teacher) to isolate
"can it be EARNED cheaply", explicitly rejecting any use of the teacher as "borrowing".

THE CREATOR HAS SHARPENED THE RULE (this changes your design space):
  "It's absolutely admissible IFF we improve it dynamically and none of it is frozen."
  "We are still *aiming* for the floor, but borrowing to help us reach it is admissible. The jabberwock is correct that
   it isn't the destination -- it is a useful MIDPOINT."

So: a pretrained net (wav2vec2) is an ADMISSIBLE MIDPOINT -- a warm-start / teacher / ruler / scaffold -- USED LIVE: (1)
nothing frozen (every weight you adopt stays trainable and adapting), (2) improved DYNAMICALLY (continuous online learning),
(3) progressively SHED as you descend toward the cheap floor (the destination is still the smallest dynamic system; the
midpoint is a means, not the end). "Distil into a FROZEN student" stays OUT. "Warm-start a small net that never stops
learning, and shrink toward the floor" is IN. You no longer have to earn it from zero -- you may climb FROM the midpoint,
as long as the climb is live and aimed at the floor.

YOUR PRIOR PHASE-1 (from-scratch CPC, bar >=45% earned / <30% kill / 30-45 escalate, 3 runs, one architecture) still stands
as the PUREST earn test. The question is whether the creator's MIDPOINT freedom changes the cheapest decisive cut."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = __doc__


def main():
    ask = make_ask(timeout=340.0)
    print("=" * 100)
    print("THE JABBERWOCK LOCKS THE EARN-NOT-BORROW FAIL-FAST (midpoint freedom)")
    print("=" * 100)

    q1 = (GROUND + "\n\nLOCK THE DESIGN (terse, decisive): given the midpoint freedom, what is THE one fail-fast to build "
          "NOW? Choose and justify in one breath between: (A) your from-scratch CPC (purest 'earned from zero', ignores the "
          "midpoint); (B) WARM-START a small (~1-5M param) encoder from wav2vec2's knowledge but keep ALL of it trainable + "
          "continue self-supervised online (nothing frozen) -- the creator's midpoint, climbing toward the floor; (C) a "
          "test that the NON-FROZEN dynamic version delivers what a FROZEN one can't (online adaptation to a new speaker/"
          "domain where frozen wav2vec2 plateaus). Pick ONE. Then give the BUILD SPEC: exactly what net, what online "
          "learning signal, what stays trainable, what gets shed and how. The measurement stays the 400-way cross-speaker "
          "rig + the same leak controls. Restate the PRE-COMMITTED BAR (earned vs kill) and the run-binding. Be concrete "
          "enough that it can be built today.")
    a1 = ask(q1)
    print("\n[LOCKED DESIGN + BUILD SPEC]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nLocked design:\n{(a1 or '')[:1200]}\n\nHONEST CHECK (terse): (a) does your pick actually test the "
          "thing that matters (cheap + dynamic + earned), or does the midpoint freedom let you SMUGGLE the borrowed "
          "invariance back in and call it earned? Name the exact way this pick could fool us, and the control that catches "
          "it. (b) if BUILD requires a primitive you don't yet hold (an online/backprop trainer as a graph-native Term -- "
          "your standing prerequisite from [[two_rules]]), say so plainly and whether a Python world-adapter rig is the "
          "honest bootstrap for THIS test or whether it must be graph-native from the start. (c) one-line pre-registered "
          "expectation: the cross-speaker number you expect, and whether you predict EARNED or KILL.")
    a2 = ask(q2)
    print("\n[HONEST CHECK + PREDICTION]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
