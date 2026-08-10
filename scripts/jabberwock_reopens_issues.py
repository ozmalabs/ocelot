#!/usr/bin/env python3
"""jabberwock_reopens_issues — the jabberwock DECIDES WHEN TO REOPEN a DEFERRED
issue and PASSES IT THROUGH into the running session.

The self-improvement loop STOPS by sufficiency (stopping_policy) and deliberately
leaves the low-salience gaps UNFIXED -- the DEFERRED `left` set. This driver shows
the twin decision run the other way: when re-measurement lifts a deferred gap's
salience above a strictly HIGHER reopen bar, the seeded should_reopen graph Program
says REOPEN, and the gap is PROMOTED to a live ReopenedConcern the RUNNING loop
consumes (the seeded reflex trips in fire_reflexes, and its response acts).

Everything decided here is the graph's: the sufficiency STOP (should_continue), the
per-gap REOPEN (should_reopen), both evaluated in Rust. Python re-measures salience
(boundary I/O via the salience_normalize Program), mints the pass-through node
(add_node/add_edge), and reads the verdicts. donkey=0.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reopens_issues.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import load_timing as lt
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    t = lt.LoadTimer(a)
    t.record("read_source", 40.0, article="A1")
    t.record("ground_lexeme", 1400.0, article="A1", n_items=20, phase="cold")
    t.record("ground_lexeme", 0.4 * 20, article="A2", n_items=20, phase="warm")
    return a


def main() -> int:
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    from domains import issue_reopen as ir

    a = _agent()

    # --- 1. run the cycle so it STOPS by sufficiency, leaving low gaps DEFERRED -----
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)
    us = [g for g in agenda if gp.gap_salience(a, g)[0] == "understanding"]
    for g in us:
        a.s.set_attr(g, "salience", 0.2)          # simulate two LOW-salience gaps
    gp.normalize_all(a, agenda)
    sp.set_sufficiency_threshold(a, 0.5)          # POLICY: good enough to leave <= 0.5
    ir.set_reopen_threshold(a, 0.7)               # POLICY: reopen bar (HIGHER -> hysteresis)

    led, left = gp.enact_in_order_with_stopping(a, gp.prioritize(a, agenda))
    print("SUFFICIENCY STOP")
    print("  sufficiency_threshold:", sp.sufficiency_threshold(a),
          " reopen_threshold:", ir.reopen_threshold(a),
          " (hysteresis dead-band between them)")
    print("  fixed  :", [r["kind"] for r in led])
    print("  DEFERRED (left unfixed):",
          [(gp.gap_salience(a, g)[0], a.s.node(g)["attrs"].get("norm_salience")) for g in left])

    # --- 2. HYSTERESIS: a deferred gap does not reopen just because it clears the ----
    #        sufficiency floor -- it must clear the HIGHER reopen bar.
    g = left[0]
    print("\nHYSTERESIS (same gap, rising salience):")
    for raw in (0.2, 0.6, 0.8):
        a.s.set_attr(g, "salience", raw)
        norm = ir.remeasure_salience(a, g)
        verdict = "REOPEN" if ir.should_reopen(a, g) else "stay deferred"
        band = ("below sufficiency" if raw < 0.5 else
                "DEAD-BAND (>suff, <reopen)" if raw < 0.7 else "above reopen bar")
        print(f"  norm={norm:.2f}  {band:<28} -> {verdict}")

    # --- 3. PASS-THROUGH: reopen the deferred set; the running loop consumes it ------
    print("\nPASS-THROUGH to the RUNNING session:")
    res = ir.reopen_deferred(a, left)             # g is at 0.8 (reopens); the other at 0.2 (stays)
    print("  reopened:", [str(x) for x in res["reopened"]])
    print("  still deferred:", [str(x) for x in res["still_deferred"]])
    print("  live concerns:", ir.concern_view(a, res["concerns"]))

    # the RUNNING loop SEES it: fire_reflexes on the real adapter trips the seeded reflex.
    fired = a.fire_reflexes()
    print("  running-loop fire_reflexes():", fired)
    for c in res["concerns"]:
        print("    concern", c, "pursued-by-live-loop:",
              a.s.node(c)["attrs"].get("pursued"))

    ok = (res["reopened"] == [g]
          and ir.REOPEN_REFLEX in fired
          and all(a.s.node(c)["attrs"].get("pursued") == 1.0 for c in res["concerns"]))
    print("\nHEADLINE:", "the jabberwock reopened a deferred issue and the running "
          "session picked it up." if ok else "UNEXPECTED -- inspect above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
