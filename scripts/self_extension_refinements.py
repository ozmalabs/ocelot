"""GAP 2 refinements — confirm-by-sibling and the honest partial-exhausted impasse. NO LLM.

Two graph rules (now firable after the JIT float-attr fix):
  - confirm_compose_by_sibling: a provisional composition INHERITS a confirmed sibling's confirmation when
    their composed_from sets are identical — proven structure transfers, no re-run needed (confirm by context).
  - compose_partial_exhausted (+ mark_uncovered_key): a partial composition that plateaus (mf_stall>=4)
    surfaces an honest HumanImpasse{kind:capability_gap_partial} that NAMES the uncovered keys — it reports
    what it could not cover instead of looping or faking the remainder.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.self_extension_refinements
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot

SEP = "=" * 96


def main():
    print(SEP)
    print("GAP 2 REFINEMENTS — confirm-by-sibling + honest partial-exhausted impasse (graph rules). NO LLM.")
    print(SEP)
    a = boot()
    a._self_teacher = None

    def primitive(name, key, reliability, contribution):
        a.s.add_node("OperationPrimitive", {"name": name, "capability_keys": [key],
                                            "reliability": reliability, "contribution": contribution, "runner": name})
    primitive("prim_seg", "segment", 0.9, 0.95)
    primitive("prim_clu", "cluster", 0.8, 0.90)        # nothing provides "tonal_contour"

    def axis(name, keys):
        return a.s.add_node("CapabilityAxis", {"is_axis": 1.0, "name": name, "capability_keys": keys})

    def needs_tool(ax):
        mi = a.s.add_node("Impasse", {"order": 4, "kind": "escalation"})
        a.inner.add_edge_unchecked(mi, "needs_tool", ax)

    ax_proven = axis("proven", ["segment", "cluster"])      # the sibling that already proved out
    ax_new = axis("new", ["segment", "cluster"])            # SAME need -> should inherit proven's confirmation
    ax_partial = axis("partial", ["segment", "tonal_contour", "pitch"])  # only segment covered -> exhausted
    for ax in (ax_proven, ax_new, ax_partial):
        needs_tool(ax)

    a.wire_self_extension()                                  # load rules + backfill CapKeys
    a.inner.run_rules(60000)                                 # compose all three + confidence

    def composed_of(ax):
        return next((o for o in a.inner.neighbours(ax, "investigated_by")
                     if a.s.node(o)["attrs"].get("composed") == 1), None)

    # the sibling already proved out (e.g. confirmed on an earlier run / another world)
    a.inner.set_attr(ax_proven, "compose_confirmed", 1)
    a.inner.set_attr(ax_proven, "confirmations", 2)

    # RUN the partial composition: the coverage-weighted runner makes it measure BELOW target (it covers
    # only segment of three keys) -> it plateaus, and that below-target trial drives the honest impasse.
    pcop = composed_of(ax_partial)
    if pcop is not None:
        pa = a.s.add_node("PlanAct", {"status": "pending"})
        a.inner.add_edge_unchecked(pa, "investigates_op", pcop)
        a.inner.add_edge_unchecked(pa, "theme", ax_partial)
        a._run_investigation_reflex()
    a.inner.run_rules(60000)                                 # sibling-inherit + partial-exhausted + uncovered keys

    new_at = a.s.node(ax_new)["attrs"]
    print(f"\n  [SIBLING ] 'new' needs {a.s.node(ax_new)['attrs'].get('capability_keys')}, same composed_from as the")
    print(f"             confirmed 'proven' sibling -> confirmed_by_sibling={new_at.get('confirmed_by_sibling')} "
          f"confirmations={new_at.get('confirmations')} confirmed={new_at.get('compose_confirmed')} (NO re-run)")

    pmh = next((m for m in a.s.nodes("HumanImpasse")
                if ax_partial in a.inner.neighbours(m, "about_axis")
                and a.s.node(m)["attrs"].get("kind") == "capability_gap_partial"), None)
    uncovered = [a.s.node(k)["attrs"].get("name") for k in a.inner.neighbours(pmh, "uncovered_key")] if pmh else []
    print(f"  [PARTIAL ] 'partial' covers segment+cluster but not tonal_contour and plateaued -> honest")
    print(f"             HumanImpasse(capability_gap_partial); uncovered keys NAMED: {uncovered}")

    ok = (new_at.get("confirmed_by_sibling") == 1 and new_at.get("compose_confirmed") == 1
          and pmh is not None and set(uncovered) == {"tonal_contour", "pitch"})
    print("\n  " + "-" * 92)
    print(f"  A proven composition's confirmation transferred to a structurally identical sibling with no")
    print(f"  re-run; a partial composition that could not reach target surfaced an honest impasse naming the")
    print(f"  exact key it lacks. claude -p calls: 0.   RESULT: {'PASS' if ok else 'FAIL'}")
    print(SEP)


if __name__ == "__main__":
    main()
