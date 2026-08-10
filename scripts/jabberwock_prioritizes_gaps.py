#!/usr/bin/env python3
"""jabberwock_prioritizes_gaps — the SCHEDULING layer, demonstrated on the agent's
OWN perceived gaps.

The jabberwock already DRIVES its fixes on BOTH dimensions — efficiency
(performance_self_improvement) and understanding (understanding_self_improvement).
But when MULTIPLE gaps are perceived at once, which does it fix FIRST? This script
shows it DECIDE — the order coming OUT of the graph:

  1. PERCEIVE   3 gaps (2 understanding + 1 efficiency), each carrying a MEASURED
                salience (efficiency: the cold-init latency-excess; understanding:
                the defect-severity).
  2. NORMALIZE  per the agent's POLICY (SaliencePolicyWeight graph data) so the
                cross-domain magnitudes (ms vs a 0..1 severity) are comparable —
                stated as a POLICY, not a universal metric.
  3. PRIORITIZE via the gap_priority graph Program (an Argmax by normalized salience,
                applied repeatedly) — the efficiency gap FIRST. Then BOOST an
                understanding gap's salience above it and re-run the SAME Program:
                the order CHANGES. Same Program, different data, different order.
  4. FIX-IN-ORDER  dispatch each gap, in the graph order, to its existing driver
                (which #2-verifies) — the enactment order == the graph order.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_prioritizes_gaps.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

COLD_MS = 1400.0
WARM_PER_ITEM = 0.4
N_ITEMS = 20


def _boot():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import load_timing as lt
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    # the agent HOLDS its perceived load timing (real LoadTimer sensor mint).
    timer = lt.LoadTimer(a)
    timer.record("read_source", 40.0, article="A1")
    timer.record("ground_lexeme", COLD_MS, article="A1", n_items=N_ITEMS, phase="cold")
    timer.record("ground_lexeme", WARM_PER_ITEM * N_ITEMS, article="A2",
                 n_items=N_ITEMS, phase="warm")
    return a


def _prog_text(a, name):
    for n in a.s.nodes("Program"):
        if a.s.node(n)["attrs"].get("name") == name:
            return a.s.node(n)["attrs"].get("program")
    return None


def main() -> int:
    from domains import gap_prioritization as gp

    a = _boot()

    print("=" * 74)
    print("THE JABBERWOCK SCHEDULES ITS OWN FIXES — order out of the graph")
    print("=" * 74)

    # 1 + 2. PERCEIVE + NORMALIZE
    agenda = gp.perceive_gaps(a)
    print(f"\n[1] PERCEIVE — {len(agenda)} gaps, each carrying a MEASURED salience:")
    for g in agenda:
        kind, raw = gp.gap_salience(a, g)
        norm = gp.normalize_salience(a, g)
        at = a.s.node(g)["attrs"]
        label = at.get("faculty") or at.get("stage")
        print(f"    gap={str(g):<8} kind={kind:<13} raw={raw:<10} "
              f"norm={norm:<8} ({label})")

    print("\n[2] NORMALIZE — per the POLICY (graph data, tunable):")
    for w in a.s.nodes("SaliencePolicyWeight"):
        at = a.s.node(w)["attrs"]
        print(f"    SaliencePolicyWeight kind={at['kind']:<13} weight={at['weight']}")
    print("    salience_normalize Program:")
    print("      ", _prog_text(a, "salience_normalize"))

    # 3. PRIORITIZE (graph decision)
    print("\n[3] PRIORITIZE — the gap_priority Program (graph data):")
    print("      ", _prog_text(a, "gap_priority"))
    order = gp.prioritize(a, agenda)
    print("    ORDER (graph-decided, most-salient-first):")
    for i, v in enumerate(gp.order_view(a, order), 1):
        print(f"      {i}. kind={v['kind']:<13} norm={v['norm_salience']:<8} ({v['label']})")
    print(f"    -> efficiency FIRST: {gp.order_view(a, order)[0]['kind'] == 'performance'}")

    # DATA-DRIVEN PROOF — boost an understanding gap above the efficiency gap.
    u_gaps = [g for g in agenda if gp.gap_salience(a, g)[0] == "understanding"]
    boost = u_gaps[0]
    a.s.set_attr(boost, "salience", 5000.0)
    gp.reset_order(a, agenda)
    order2 = gp.prioritize(a, agenda)
    print("\n    DATA-DRIVEN PROOF — boost an understanding gap's salience (SAME Program):")
    for i, v in enumerate(gp.order_view(a, order2), 1):
        print(f"      {i}. kind={v['kind']:<13} norm={v['norm_salience']:<8} ({v['label']})")
    print(f"    -> boosted understanding gap now FIRST: {str(order2[0]) == str(boost)}")

    # REVERSE control — zero a gap -> sorts last.
    gp.reset_order(a, agenda)
    a.s.set_attr(boost, "salience", 0.0)
    gp.reset_order(a, agenda)
    order3 = gp.prioritize(a, agenda)
    print("\n    REVERSE control — zero that gap's salience -> it sorts LAST:")
    for i, v in enumerate(gp.order_view(a, order3), 1):
        print(f"      {i}. kind={v['kind']:<13} norm={v['norm_salience']:<8} ({v['label']})")
    print(f"    -> zero-salience gap LAST: {str(order3[-1]) == str(boost)}")

    # 4. FIX-IN-ORDER — fresh agent, full cycle.
    print("\n[4] FIX-IN-ORDER — dispatch each gap, in the graph order, to its driver:")
    a2 = _boot()
    led = gp.run_cycle(a2)
    graph_order = [str(g) for g in led["order"]]
    enact_order = [r["gap_str"] for r in led["enacted"]]
    for r in led["enacted"]:
        print(f"      kind={r['kind']:<13} fix={str(r.get('fix')):<16} "
              f"accepted={r.get('accepted')}")
    print(f"    graph order == enactment order: {graph_order == enact_order}")
    print(f"    efficiency fixed first: {led['enacted'][0]['kind'] == 'performance'}")

    print("\n" + "=" * 74)
    print("HONEST LEDGER")
    print("  · the ORDER is the gap_priority graph Program's Argmax output, applied")
    print("    repeatedly — NOT a Python sort. Boosting salience REORDERS (same Program).")
    print("  · the salience MEASUREMENT is the existing perceivers' boundary I/O.")
    print("  · the normalization WEIGHTS are a stated POLICY (SaliencePolicyWeight graph")
    print("    data, tunable) — how many ms of latency-excess trade for one unit of")
    print("    understanding defect. NOT a universal metric.")
    print("  · the per-gap fixing is the already-built drivers, called as-is (each #2-verifies).")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
