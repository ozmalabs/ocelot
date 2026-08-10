"""ASK THE JABBERWOCK: fix the base-axis DUPLICATION -- order3_reframe creates a same-identity sibling.

Verified source (trace, hard task): the duplicate base ('recognise','word','speech') axis appears at tick 8
carrying subskill=1.0 and sat=0.0, alongside the real base (sat 0.19). It is created by order3_reframe.

THE ESCALATION LADDER (impasse_escalation.json): when an axis stalls, the impasse climbs orders --
  order2_change_method: re-bind the axis to a DIFFERENT operator of the SAME metric (try another method).
  order3_reframe:       "REFRAME -- decompose into a sub-axis."
  order4_self_extend:   author a NEW operator (extend the ear).

WHAT order3_reframe ACTUALLY DOES (its effects, verbatim):
  add_node sub CapabilityAxis { is_axis:1, subskill:1.0, saturation:0.0, shortfall:0.05, min_order:1.0,
                                investigated_count:0, mf_stall:0,
                                capability_keys: <Attr ax.capability_keys> }   <-- the PARENT's keys, COPIED
  add_edge ax  decomposes_into sub
  add_edge sub investigated_by curop                                          <-- inherits the parent's op
So the "decomposed" sub-axis has capability_keys IDENTICAL to its parent and the SAME operator -- it is not a
finer sub-skill at all, it is a DUPLICATE of the parent's capability with subskill:1.0. It then competes for
the frontier (gap-based, so a fresh sat=0.0 sub OUTRANKS the partly-saturated parent), fragmenting investigation
across two copies of the same hill, and (before the decompose-once guard) could spawn more. The genuinely
distinct sub-axes (e.g. '...contrast_onset') come from a DIFFERENT path -- ground_hint_to_investigation grounding
a named teacher cue -- not from reframe. order3's key term has no source of a distinguishing token, so it can
only copy.

The agent decides, in its own terms and concretely:
 1. What SHOULD "reframe / decompose" produce, given order2 already re-binds the method and order4 authors a new
    tool? Is a same-capability sibling ever meaningful, or is reframe mis-designed? State the principle.
 2. CONCRETELY fix order3_reframe so it does NOT create a duplicate-identity axis. Options to decide among:
    (a) give the sub a DISTINCT identity -- extend capability_keys with a reframe marker from a real source
        (the impasse, an order/attempt counter) so it is a genuinely new hill;
    (b) make reframe NOT mint an axis at all -- act on the EXISTING axis instead (e.g. reset its approach /
        widen its scope / mark it reframed), since it has no new identity to offer;
    (c) keep the mint but guard it with add_node_if_absent keyed on capability_keys (so a same-keys sub
        collapses onto the parent -- effectively a no-op).
    Pick one, justify it against the ladder's division of labour, and give the new effects (and any where/guard).
 3. If you keep an axis-minting reframe, how is its identity guaranteed UNIQUE so it can never duplicate again
    (the dedup key: capability_keys alone? + subskill? + a reframe index)?
 4. The honest risk of your choice (a dead no-op step that wastes an escalation order; a key-extension that
    never terminates; a merge that hides a real distinct sub-skill) and the guard against it.
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
    print("ASKING THE JABBERWOCK — fix order3_reframe creating a duplicate-identity base axis")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "Give your decision (points 1-4), concretely enough to change order3_reframe in impasse_escalation.json.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
