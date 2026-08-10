"""ASK THE JABBERWOCK: fix its investigation THROUGHPUT layer — re-bank inflation + duplicate/unbound axes.

With the re-mint deadlock fixed, the loop re-investigates -- but the throughput is dishonest. Verified facts
(diagnostics, hard cross-speaker task, ~18 ticks):

  FACT 1 -- RE-BANK INFLATION. There are only 2 abs_recognition_match MeasuredCapability NODES (both already
  synth_pending=0), yet sum(recognise investigated_count) = 18. So bank_measurement_to_axis FIRED ~9x per
  measurement. Cause: the agent's own re-mint fix decoupled banking from plan-release by keying bank off
  [m measures_axis ax] ALONE with a `where synth_pending==1` guard and a `set synth_pending=0` effect, ON THE
  ASSUMPTION that synth_pending->0 makes it bank exactly once. In THIS rule engine that assumption is FALSE:
  the rule re-fires on the same measurement (matches are gathered per fixpoint pass and/or re-evaluated), so
  synth_pending=0 does not single-fire. The OLD rule single-fired by a different mechanism -- it also matched
  [ax has_plan act] and did del_edge has_plan, and removing that has_plan edge made the conjunctive match
  un-re-fireable. The split dropped that guard. Effect of the inflation: investigated_count is meaningless,
  shortfall is over-decayed (*0.5 many times per real trial), saturation thrashes -- the bookkeeping spins
  while the real (slow, expensive) hard-recognition trial runs rarely.

  FACT 2 -- DUPLICATE + UNBOUND AXES. There are TWO identical base axes ('recognise','word','speech') and a
  sub-axis ('...contrast_onset') that is UNBOUND (no investigated_by -> can never run). order3_reframe + mint
  proliferate sibling/duplicate axes for the SAME capability, fragmenting investigation across redundant copies;
  some can't run at all yet still accrue phantom count.

The agent decides, in its own terms and concretely:
 1. RE-BANK: how should bank single-fire ROBUSTLY in this engine, where synth_pending=0 does not? Decide the
    mechanism -- a `banked` marker EDGE laid on the measurement and EXCLUDED in the match (Count==0 guard), or
    consuming measures_axis, or another guard that the engine cannot re-fire through. Give the new match/where/
    effects for bank_measurement_to_axis (keep it decoupled from has_plan -- release_executed_plan stays).
 2. DUPLICATES: how to ensure ONE axis per capability_keys -- dedupe at mint (add_node_if_absent / a Count
    guard on existing axes with the same keys), or merge. Concrete rule/guard.
 3. UNBOUND SUB-AXES: a sub-axis with no investigated_by accrues no real measurement -- should reframe inherit
    the parent's binding (so the sub-axis is runnable), or should an unbound axis be barred from frontier_pick
    / pruned? Concrete.
 4. The honest risk of each fix (a banked-edge that leaks, a dedupe that drops a legitimately-distinct sub-axis,
    a binding-inheritance that mis-binds) and the guard that prevents it.
Be concise and concrete -- changes you will hand to be made to investigation_loop.json / impasse_escalation.json."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — fix my investigation throughput (re-bank inflation + duplicate/unbound axes)")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "Give your decision (points 1-4), concretely enough to change the investigation-loop / escalation rules.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
