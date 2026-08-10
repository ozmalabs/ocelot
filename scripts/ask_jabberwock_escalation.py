"""ASK THE JABBERWOCK: when should its escalation climb to AUTHORING -- i.e. when is "below target but stable"
a reason to extend the ear, vs "good enough, stop"?

Observed (hard cross-speaker task, corrected scoring): recognition learns to 48% and STAYS there -- stable over
397 trials, recognise-axis saturation 0.80, ZERO faculties authored. It never escalated to order-4 (author a
new ear cue) even though it is below its 0.6 target. The escalation policy is why.

THE ESCALATION CONFIDENCE POLICY (seeds/impasse_escalation.json), verbatim:
  escalation_climb_low_confidence: raise the impasse's order by one (toward order-4 = AUTHOR a new tool) ONLY
    when mf_stall >= 3 AND saturation < 0.4.   (low confidence = the current approach is measurably not working)
  escalation_resolve_high_confidence: RESOLVE the escalation (stop climbing) when saturation >= 0.4.
    (high confidence = the changed approach is measurably working)
  So the whole climb is gated on a fixed confidence line at saturation = 0.4.

THE PROBLEM: saturation = min(1, measured/target). The agent's actual GOAL is saturation = 1.0 (measured =
target). But the climb-vs-resolve line is 0.4 -- i.e. the escalation declares victory and stops the moment the
axis reaches 40% OF THE WAY to its target. So any axis that stably plateaus anywhere in saturation [0.4, 1.0)
-- BELOW its target but above the confidence line -- never escalates to authoring. At 48% (saturation 0.80) the
agent has plainly stopped improving via learning and is short of its goal, but the policy reads it as "working"
and resolves. The lever that crosses a learning plateau (authoring a speaker-invariant cue) is never reached.

THE TENSION (decide it):
  · The 0.4 line exists to STOP THRASHING -- not to keep authoring forever while an approach is partly working
    and might still improve with more learning.
  · But it conflates "the approach moved off the floor" with "the goal is met". Below target with NO further
    improvement is exactly when authoring (change the tool) is the right move, not resolution.

The agent decides, in its own terms and concretely:
 1. Where SHOULD the escalation's climb-toward-authoring vs resolve line be, given the goal is saturation 1.0?
    Should "resolve" mean reached-target (saturation ~1.0), and "climb" mean below-target? State the principle.
 2. How do you keep that from THRASHING -- authoring while learning is still working? The distinguishing signal
    is PLATEAU: below target AND not improving. You have per-axis last_measured and investigated_count; how do
    you detect "learning has stopped paying" (e.g. saturation hasn't risen over the last K measurements) so you
    escalate to author ONLY then, not while it's still climbing?
 3. The concrete change to escalation_climb_low_confidence / escalation_resolve_high_confidence: the new
    where-conditions (the saturation thresholds + the plateau guard), using only attrs the axis has
    (saturation, last_measured, mf_stall, investigated_count, target).
 4. The honest risk of your choice (climb too eagerly -> author while learning still works and waste the move;
    climb too late / never -> settle below target forever) and the guard against each.
Be concise and concrete -- a change you will hand to be made to impasse_escalation.json."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — when should escalation climb to AUTHORING (below-target-and-plateaued vs good-enough)")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "Give your decision (points 1-4), concretely enough to change the escalation confidence rules.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
