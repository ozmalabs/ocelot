"""ASK THE JABBERWOCK: how to fix its own re-investigation re-mint cycle, which stalls after a few trials.

The frontier now correctly keeps the unmet recognise axis selected (the agent's own gap-based fix). But the
INVESTIGATION CYCLE that turns 'selected' into 'measured + banked + re-selected' stalls after ~3 trials. The
creator wants the JABBERWOCK to decide the fix.

THE CYCLE (graph-native, one capability axis `ax`):
  1. mint_investigation_plan: match [ag frontier_pick ax]; where ax.is_axis==1 AND Count(ax has_plan)==0
       -> add PlanAct(pending), edge [act theme ax], edge [ax has_plan act].
  2. bind_investigation_faculty: bind the act to the operator the axis names (investigates_op).
  3. _run_investigation_reflex (mechanical, ONE act/tick): run the bound faculty -> lay a MeasuredCapability m
       with m.synth_pending=1 and edge [m measures_axis ax]; set the PlanAct status=executed.
  4. bank_measurement_to_axis: match [m measures_axis ax] AND [ax has_plan act]; where m.synth_pending==1
       -> set ax.saturation = min(1, measured/target); ax.shortfall *= 0.5; ax.investigated_count += 1;
          DEL [ax has_plan act]; set m.synth_pending=0.
  Then has_plan(ax)==0 again, so step 1 re-mints -> the axis is re-investigated. That is the loop.

THE STALL (observed, diagnosed): the escalation ladder proliferates SIBLING recognise axes -- the base
('recognise','word','speech') plus sub-axes ('...contrast_onset'), ('...since_stall') from order3_reframe. The
frontier picks one, mints a plan on it, but the measurement and the has_plan edge end up on DIFFERENT axes
(a measurement laid for axis A while the live has_plan sits on sibling axis B). bank_measurement_to_axis binds
ONE `ax` that must satisfy BOTH [m measures_axis ax] AND [ax has_plan act] -- no single axis satisfies both, so
bank fires for NEITHER. Result at the stall: a VALID unbanked measurement (abs_recognition_match=0.22,
synth_pending=1) sits next to a pending has_plan; ax.saturation/shortfall are never updated; investigated_count
FREEZES; re-mint never re-fires (the old has_plan never cleared). The capability is still unmet and selected,
but the loop has deadlocked on its own bookkeeping.

The agent decides, in its own terms and concretely:
 1. What is the STRUCTURAL flaw? Tie it to the bank rule binding a single `ax` across two edges
    (measures_axis and has_plan) that escalation can split across sibling axes.
 2. How should banking + has_plan release be re-designed so a measurement ALWAYS banks to the axis it
    measured, and that axis is ALWAYS freed for re-mint, even with sibling sub-axes -- WITHOUT double-banking
    a measurement or freeing a plan that never ran? State the principle.
 3. The CONCRETE graph change: which rule(s) to split/relax/add, with the new match/where/effects (use only
    edges/attrs already in play: measures_axis, has_plan, theme, investigates_op, synth_pending, status,
    saturation, shortfall, investigated_count). Specifically: should banking key off measures_axis ALONE
    (decoupled from has_plan), and has_plan be cleared by the PlanAct's executed STATUS instead? Decide.
 4. The honest risk: where could your redesign double-count, leak plans, or let a stale measurement re-bank,
    and what guard (synth_pending, status, an edge) prevents it?
Be concise and concrete. This is a change you will hand to be made to your own investigation loop."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — how do I fix my re-investigation cycle that deadlocks on its bookkeeping?")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "Give your decision (points 1-4), concretely enough to change the investigation-loop rules.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
