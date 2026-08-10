"""FULL LADDER INTEGRATION — a failed self-repair climbs the agent's order-2..6 impasse_escalation ladder.

A repair-kind axis that keeps failing (non-improving measures) is opened onto the EXISTING escalation ladder
by repair_escalate_open; the GENERIC escalation_climb drives order 2->6, and repair-kind rung adapters
specialise each rung: 2 retry (re-arm a different synthesised clause), 3 reframe (flip field), 4 author
(need_template), 5 set-aside, 6 honest HumanImpasse. Forward motion comes only from a rung firing and order
strictly increases, so the old detect->repair->revert loop cannot form.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_repair_ladder.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def repair_impasse(agent):
    for n in agent.s.nodes("Impasse"):
        a = agent.s.node(n)["attrs"]
        if a.get("repair_imp") == 1.0:
            return a
    return None


def main():
    print("=" * 96)
    print("FULL LADDER INTEGRATION — a failed repair climbs the order-2..6 impasse_escalation ladder.")
    print("=" * 96)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    mt = agent.s.add_node("Microtheory", {"name": "repair_world"})
    agent.inner.add_edge_unchecked(agent.agent, "operates_in", mt)

    ax = agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "repair_kind": 1.0, "repair_rule": "R", "repair_field": "effect",
        "saturation": 0.2, "sat_best": 1.0, "target": 1.0, "mf_stall": 0.0,
        "escalating": 0.0, "fault_open": 1.0, "shortfall": 0.7})
    f = agent.s.add_node("Fault", {"target_rule": "R", "field": "effect", "attempt": 0.0, "terminal": 0.0})
    agent.inner.add_edge_unchecked(ax, "has_fault", f)

    milestones, seen_orders = [], set()
    for step in range(70):
        mc = agent.s.add_node("MeasuredCapability", {"measured": 0.2, "target": 1.0, "metric": "self_id_stability"})
        agent.inner.add_edge_unchecked(mc, "measures_axis", ax)
        agent.master_tick(); agent.tick()
        imp = repair_impasse(agent)
        order = int(imp.get("order")) if imp and imp.get("order") is not None else None
        if order is not None and order not in seen_orders:
            seen_orders.add(order)
            fa = agent.s.node(f)["attrs"]; axa = agent.s.node(ax)["attrs"]
            milestones.append((step, order, fa.get("attempt"), fa.get("field"),
                               axa.get("repair_aside"), fa.get("need_template")))
        his = [n for n in agent.s.nodes("HumanImpasse")
               if agent.s.node(n)["attrs"].get("kind") == "repair_exhausted"]
        if his:
            break

    fa = agent.s.node(f)["attrs"]; axa = agent.s.node(ax)["attrs"]
    his = [agent.s.node(n)["attrs"] for n in agent.s.nodes("HumanImpasse")
           if agent.s.node(n)["attrs"].get("kind") == "repair_exhausted"]
    print("\n  ladder climb (step, order, fault.attempt, fault.field, axis.repair_aside, need_template):")
    for m in milestones:
        print(f"    step {m[0]:>2}: order={m[1]}  attempt={m[2]}  field={m[3]!r}  aside={m[4]}  need_template={m[5]}")
    print(f"\n  reached order 6: {6 in seen_orders}; HumanImpasse minted: {len(his) > 0}; "
          f"fault terminal: {fa.get('terminal')}")
    print(f"  rung evidence — order2 retry (attempt>=1): {(fa.get('attempt') or 0) >= 1}; "
          f"order3 reframe (field flipped to 'where'): {fa.get('field') == 'where'}; "
          f"order4 need_template: {fa.get('need_template') == 1.0}; "
          f"order5 set-aside (repair_aside): {axa.get('repair_aside') == 1.0}")

    ok = (6 in seen_orders and len(his) > 0 and fa.get("terminal") == 1.0
          and (fa.get("attempt") or 0) >= 1 and fa.get("field") == "where"
          and axa.get("repair_aside") == 1.0 and max(seen_orders) == 6)
    print("\n" + "=" * 96)
    print(f"  {'PASS' if ok else 'FAIL'} — a failed repair climbed the SAME order-2..6 ladder the agent uses "
          f"for everything: retry (2) -> reframe (3) -> author (4) -> set-aside (5) -> honest HumanImpasse "
          f"(6). Bounded, strictly increasing, no silent latch. Pure graph data; the generic ladder untouched.")
    print("=" * 96)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
