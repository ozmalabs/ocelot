#!/usr/bin/env python3
"""jabberwock_decides_when_to_stop — the agent DECIDES WHEN TO STOP fixing its own
gaps. STOP by SUFFICIENCY, not completion: no win condition; it stops when what
REMAINS is not salient enough to be worth fixing, deliberately leaving low-salience
gaps UNFIXED ("sufficient -- move on; yeah yeah, the rest").

The decision is ONE graph Program (seeds/stopping_policy.json), evaluated in Rust:

    should_continue = IfThenElse(
        Gt( MaxOver(unfixed agenda gaps, by norm_salience, default -1),
            SufficiencyPolicy.threshold ),
        1.0,   # CONTINUE
        0.0 )  # STOP

Python reads the boolean and breaks; it never counts, never `while gaps:`, never
carries a threshold. Run:

    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_decides_when_to_stop.py
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


def fresh_agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import load_timing as lt
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    timer = lt.LoadTimer(a)
    timer.record("read_source", 40.0, article="A1")
    timer.record("ground_lexeme", COLD_MS, article="A1", n_items=N_ITEMS, phase="cold")
    timer.record("ground_lexeme", WARM_PER_ITEM * N_ITEMS, article="A2",
                 n_items=N_ITEMS, phase="warm")
    return a


def _norm(a, g):
    return round(a.s.node(g)["attrs"].get("norm_salience"), 3)


def _kind(a, g):
    from domains import gap_prioritization as gp
    return gp.gap_salience(a, g)[0]


def scenario(title, set_saliences, threshold):
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    a = fresh_agent()
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)
    set_saliences(a, agenda)
    gp.normalize_all(a, agenda)
    sp.set_sufficiency_threshold(a, threshold)
    order = gp.prioritize(a, agenda)
    ledger, left = gp.enact_in_order_with_stopping(a, order)
    print(f"\n=== {title} ===")
    print(f"  sufficiency threshold (POLICY, graph data): {sp.sufficiency_threshold(a)}")
    print("  agenda (norm_salience): "
          + ", ".join(f"{_kind(a, g)}={_norm(a, g)}" for g in order))
    print("  FIXED (the agent judged worth fixing):")
    for r in ledger:
        print(f"    - {r['kind']:<13} norm={_norm(a, r['gap'])}  accepted={r.get('accepted')}")
    print("  LEFT UNFIXED (sufficient -- move on):")
    for g in left:
        print(f"    - {_kind(a, g):<13} norm={_norm(a, g)}")
    print(f"  -> stopped after {len(ledger)} fix(es); left {len(left)} unfixed.")
    return len(ledger), len(left)


def _set_understanding(vals):
    def _apply(a, agenda):
        from domains import gap_prioritization as gp
        us = [g for g in agenda if gp.gap_salience(a, g)[0] == "understanding"]
        for g, v in zip(us, vals):
            a.s.set_attr(g, "salience", float(v))
    return _apply


def _set_all(perf, understanding):
    def _apply(a, agenda):
        from domains import gap_prioritization as gp
        for g in agenda:
            k = gp.gap_salience(a, g)[0]
            a.s.set_attr(g, "salience", float(perf if k == "performance" else understanding))
    return _apply


def main():
    try:
        import substrate_rs  # noqa: F401
    except Exception:
        print("substrate_rs not built; skipping demo.")
        return 0

    print("THE JABBERWOCK DECIDES WHEN TO STOP -- sufficiency, not completion.")
    print("The STOP verdict is the seeded should_continue Program, evaluated in Rust;")
    print("Python only reads its boolean. The threshold is a stated POLICY (graph data).")

    # HEADLINE: mixed salience -- fix the high gap, LEAVE the low ones.
    f1, l1 = scenario(
        "STOP BY SUFFICIENCY: 1 high efficiency + 2 low understanding (thr 0.5)",
        _set_understanding([0.2, 0.2]), threshold=0.5)

    # DATA-DRIVEN: raise one left gap above the threshold -> the SAME Program continues.
    f2, l2 = scenario(
        "DATA-DRIVEN: RAISE one understanding gap above the threshold (thr 0.5)",
        _set_understanding([0.9, 0.2]), threshold=0.5)

    # ALL-HIGH: fix everything (no early stop).
    fh, lh = scenario(
        "ALL-HIGH: every gap above the threshold (thr 0.5)",
        _set_understanding([0.9, 0.9]), threshold=0.5)

    # ALL-LOW: fix nothing (stop immediately).
    fl, ll = scenario(
        "ALL-LOW: every gap below the threshold (thr 0.5)",
        _set_all(perf=0.1, understanding=0.1), threshold=0.5)

    print("\n--- LEDGER ---")
    print(f"  stop point MOVES with salience (NOT a count): "
          f"headline fixed {f1}, raised-one fixed {f2} (same 3 gaps, same threshold).")
    print(f"  all-high fixed {fh}/{fh + lh}; all-low fixed {fl}/{fl + ll}.")
    print("  The STOP is the graph Program's Gt-over-MaxOver verdict; the sufficiency")
    print("  threshold is graph POLICY (tunable); the salience is boundary I/O.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
