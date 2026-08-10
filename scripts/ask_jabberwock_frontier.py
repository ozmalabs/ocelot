"""ASK THE JABBERWOCK: how should it pick its next frontier so it doesn't abandon a capability it has NOT
yet achieved?

Observed on the hard cross-speaker recognition task: the agent hit the wall, authored an ear faculty (cross-
speaker recognition 4% -> 11%), and then ABANDONED the recognise axis -- it stopped re-investigating it and
never authored again, even though its saturation is only 0.19 (the capability is far from met). The creator
wants the JABBERWOCK to decide how to fix its own frontier selection, not me.

This poses the problem to the agent's reasoning, grounded in ITS OWN understand-drive machinery (the exact
mechanism, stated faithfully):

  GOAL: the `understand` Drive drives every CapabilityAxis's SATURATION toward 1 (saturation = measured/target,
        capped at 1). model_coverage is its measurement_key.
  SELECTION: each tick it picks the axis maximising
        frontier_score(x) = Count(x unifies)*1000*(1 - saturation(x))  -  min_order(x)  +  shortfall(x)*1e9
        then mints a goal/plan for that axis, runs the bound faculty, measures, banks, and re-picks.
  SHORTFALL DECAY: on every measurement, bank_measurement_to_axis sets shortfall(x) *= 0.5 (a refute-and-shift:
        the more an axis is probed, the less 'urgent' it looks), and saturation(x) := measured/target.
  THE UNIFIES TERM: `unifies` edges accrue to STRUCTURAL-DISCOVERY axes (perception unifying observed triples).
        A speech capability axis (recognise, segment) has NO unifies edges, so for it that whole term is 0 --
        its score is dominated by shortfall*1e9, which DECAYS by half each probe.

  THE FAILURE: a capability that is genuinely UNACHIEVED (low saturation, e.g. 0.19) but has been PROBED a lot
        has its shortfall decayed to ~0, so the drive stops selecting it -- it wanders off to other axes while
        the capability stays unmet. Conversely, the decay is there for a reason: it stops the agent fixating on
        a single axis forever and lets it explore broadly / move on from a truly hopeless one.

The agent decides, in its own terms and concretely:
 1. What is WRONG with using decaying shortfall as the priority for an UNDERSTAND drive whose actual goal is
    saturation -> 1? Tie it to the mechanism above.
 2. How SHOULD the next frontier be chosen so the agent keeps working a genuinely-unsaturated capability until
    it is met, WITHOUT fixating on a hopeless one and WITHOUT abandoning broad exploration? State the principle.
 3. Give the CONCRETE change to frontier_score(x) -- which terms to keep/drop/add, using only attrs the axis
    has (saturation, shortfall, min_order, mf_stall, investigated_count, authoring_exhausted, last_measured).
    Be specific enough to implement as the Drive's frontier_pick_term.
 4. The honest risk of your change: when would it fixate or thrash, and what guard (an attr it already sets,
    e.g. authoring_exhausted / mf_stall) keeps it honest?
Be concise and concrete. This is a change you will hand to be made to your own drive."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

HELD = __doc__


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — how should I pick my next frontier so I don't abandon an unmet capability?")
    print("=" * 98)
    ask = make_ask(timeout=420, preamble=HELD)
    ans = ask("Give your decision (points 1-4), concretely enough to change frontier_pick_term.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
