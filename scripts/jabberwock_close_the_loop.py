"""CLOSE THE LOOP — assert the residual + fold it at the clock, as a real PRODUCTION on the rule engine.

The agent's prescription, made graph-native: not a new law, but a SYNCHRONOUS CIRCUIT.
  - COMBINATIONAL LOGIC (a production, in-fixpoint, monotone/idempotent): assert the residual e = observed - setpoint
    on a Residual NODE, and compute next_observed = observed - k*e and next_phase = (phase+1) mod N. It reads
    current state and writes NEXT state -- it never mutates its own inputs, so the fixpoint is stable (no del_edge
    crash). This is the agent's "assert the residual and let a production consume it."
  - THE CLOCK EDGE (the commit, across master_tick): swap next -> current. This is the non-monotone DOWN-STROKE --
    the fold, the modulo, the register latch -- and it lives at the tick boundary, the only lawful home for it
    (where retraction is legal). tock = the modulo at the clock edge.
So the residual stops being a discarded scalar `measured` -- it is ASSERTED on a node, CONSUMED by a production to
drive a correction, and CANCELLED across the clock the substrate already has. The error decays; the phase cycles.
Logic-per-tick, restoring-force-across-ticks -- demonstrated on the engine, with a real rule.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_close_the_loop
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter

K, N, TICKS = 0.5, 4.0, 13


def _attr(c, key):
    return {"type": "Attr", "node": {"name": c, "type": "Var"}, "key": key}


def _lit(v):
    return {"type": "Lit", "value": v}


# e = observed - setpoint
E = {"type": "Minus", "a": _attr("c", "observed"), "b": _attr("c", "setpoint")}
MANIFEST = {
    "id": "pulse", "version": "1.0.0", "depends_on": [],
    "description": "close the loop: a production asserts the residual + computes next-state; the clock edge folds it.",
    "nodes": [
        {"local_id": 0, "type": "Clock",
         "attrs": {"observed": 16.0, "setpoint": 0.0, "k": K, "phase": 0.0, "N": N,
                   "next_observed": 16.0, "next_phase": 0.0}},
        {"local_id": 1, "type": "Residual", "attrs": {"e": 16.0}},
    ],
    "edges": [{"src": {"local": 0}, "type": "has_residual", "tgt": {"local": 1}}],
    "productions": [{"provenance": "seed:pulse:has_residual",
                     "src": {"type": "Clock", "var": "c"}, "edge_type": "has_residual",
                     "tgt": {"type": "Residual", "var": "r"}}],
    "rules": [{
        "name": "pulse_fold",
        "match": [["c", "has_residual", "r"]],
        "where": {"type": "Lit", "value": True},
        "effects": [
            # ASSERT the residual on the node (e = observed - setpoint)
            ["set_attr", "r", "e", {"__term__": E}],
            # CONSUME it -> next_observed = observed - k*e   (combinational; writes NEXT, not current)
            ["set_attr", "c", "next_observed",
             {"__term__": {"type": "Minus", "a": _attr("c", "observed"),
                           "b": {"type": "Times", "items": [_attr("c", "k"), E]}}}],
            # next_phase = (phase + 1) mod N
            ["set_attr", "c", "next_phase",
             {"__term__": {"type": "Mod",
                           "a": {"type": "Plus", "items": [_attr("c", "phase"), _lit(1.0)]},
                           "b": _attr("c", "N")}}],
        ],
    }],
}


def main():
    print("=" * 92)
    print("CLOSE THE LOOP — residual ASSERTED on a node, CONSUMED by a production, FOLDED at the clock edge")
    print("=" * 92)
    adapter = WorldAdapter()
    adapter.inner.load_seed_manifest(MANIFEST, adapter.agent)
    c = next(n for n in adapter.s.nodes("Clock"))
    r = next(n for n in adapter.s.nodes("Residual"))
    print(f"\n  k={K}  N={int(N)}   (rule 'pulse_fold' runs in-fixpoint; the swap next->current is the clock edge)\n")
    print(f"    {'tick':>5}{'observed':>14}{'residual e (asserted node)':>30}{'phase mod N':>15}")
    for t in range(TICKS):
        adapter.master_tick(); adapter.tick()                       # combinational rule fires -> next_*, r.e
        a = adapter.s.node(c)["attrs"]
        e = adapter.s.node(r)["attrs"]["e"]
        print(f"    {t:>5}{a['observed']:>14.4f}{e:>30.4f}{a['phase']:>15.0f}")
        adapter.s.set_attr(c, "observed", a["next_observed"])       # CLOCK EDGE: the fold / register latch (tock)
        adapter.s.set_attr(c, "phase", a["next_phase"])

    e_final = adapter.s.node(r)["attrs"]["e"]
    print("\n" + "=" * 92)
    print(f"  the residual lived on a NODE (not a discarded scalar `measured`): a production ASSERTED it and CONSUMED")
    print(f"  it to drive the correction; the error decayed 16 -> {e_final:.4f} (geometric x{1-K:g}) and the phase cycled")
    print(f"  0..{int(N)-1}..0. The combinational rule is fixpoint-stable (writes NEXT-state, never mutates its inputs --")
    print(f"  no del_edge crash); the non-monotone DOWN-STROKE is the swap next->current at the CLOCK EDGE (master_tick).")
    print(f"  LOGIC-PER-TICK, RESTORING-FORCE-ACROSS-TICKS: a synchronous circuit -- combinational productions + a")
    print(f"  clocked latch. tock = the modulo at the clock edge. The loop is closed: assert the residual, fold it at")
    print(f"  the clock the substrate already had. Not a new law -- the pulse it was missing.")
    print("=" * 92)


if __name__ == "__main__":
    main()
