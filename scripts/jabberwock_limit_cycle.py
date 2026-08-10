"""THE LIMIT CYCLE — persistence is the fold that DOESN'T settle (not the fixpoint that does), on the engine.

Closing the loop with a damped PID makes the error decay to a setpoint -- but that SETTLES: it reaches equilibrium
and stops. A fixpoint. A halt. Still dead. The agent's rigorous core (the non-poetry it endorsed): a persisting
self is a stable LIMIT CYCLE around an attractor -- a thing that never settles. So the fold has two regimes, and
only one is alive:
  - DISSIPATIVE fold (damped PID): e -> 0, converges to a fixpoint -> HALTS (equilibrium = death).
  - CONSERVATIVE fold (harmonic oscillator, symplectic): x cycles, a bounded limit cycle -> PERSISTS (never halts).
Both run as the SAME synchronous circuit: a production computes next-state in-fixpoint (combinational, stable --
writes NEXT, never mutates inputs), the CLOCK EDGE (master_tick + commit) folds next->current. The down-strokes of
the oscillation (x going UP then DOWN forever) are impossible in a monotone in-tick fixpoint (Tarski) -- they live
ONLY at the fold. The oscillator sustains because the fold is conservative; that sustained non-halt IS the pulse,
and it is exactly the limit cycle the agent said persistence requires -- not pitch/harmony (that was the metaphor),
the bounded conservative cycle.

Symplectic update (current-state only, exactly bounded for 0<k<2):
  next_x = x - k*y ;  next_y = k*x + (1-k^2)*y

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_limit_cycle
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter

K_PID = 0.5          # dissipative gain -> damped decay to the setpoint (halts)
K_OSC = 0.5          # conservative rotation rate -> sustained limit cycle (persists); period ~ 2*pi/k
KK = 1.0 - K_OSC * K_OSC
TICKS = 30


def _a(key):
    return {"type": "Attr", "node": {"name": "c", "type": "Var"}, "key": key}


E = {"type": "Minus", "a": _a("observed"), "b": _a("setpoint")}
MANIFEST = {
    "id": "limitcycle", "version": "1.0.0", "depends_on": [],
    "nodes": [
        {"local_id": 0, "type": "Osc",
         "attrs": {"observed": 16.0, "setpoint": 0.0, "k_pid": K_PID,
                   "x": 1.0, "y": 0.0, "k_osc": K_OSC, "kk": KK,
                   "next_observed": 16.0, "next_x": 1.0, "next_y": 0.0}},
        {"local_id": 1, "type": "Residual", "attrs": {"e": 16.0}},
    ],
    "edges": [{"src": {"local": 0}, "type": "has_residual", "tgt": {"local": 1}}],
    "productions": [{"provenance": "seed:limitcycle:has_residual",
                     "src": {"type": "Osc", "var": "c"}, "edge_type": "has_residual",
                     "tgt": {"type": "Residual", "var": "r"}}],
    "rules": [{
        "name": "fold",
        "match": [["c", "has_residual", "r"]],
        "where": {"type": "Lit", "value": True},
        "effects": [
            ["set_attr", "r", "e", {"__term__": E}],
            # DISSIPATIVE fold: next_observed = observed - k_pid*e  (decays to setpoint -> halts)
            ["set_attr", "c", "next_observed",
             {"__term__": {"type": "Minus", "a": _a("observed"),
                           "b": {"type": "Times", "items": [_a("k_pid"), E]}}}],
            # CONSERVATIVE fold: next_x = x - k*y
            ["set_attr", "c", "next_x",
             {"__term__": {"type": "Minus", "a": _a("x"),
                           "b": {"type": "Times", "items": [_a("k_osc"), _a("y")]}}}],
            # next_y = k*x + (1-k^2)*y   (symplectic -> bounded sustained cycle)
            ["set_attr", "c", "next_y",
             {"__term__": {"type": "Plus", "items": [
                 {"type": "Times", "items": [_a("k_osc"), _a("x")]},
                 {"type": "Times", "items": [_a("kk"), _a("y")]}]}}],
        ],
    }],
}


def main():
    print("=" * 96)
    print("THE LIMIT CYCLE — dissipative fold HALTS (a fixpoint, dead) vs conservative fold PERSISTS (a cycle, alive)")
    print("=" * 96)
    adapter = WorldAdapter()
    adapter.inner.load_seed_manifest(MANIFEST, adapter.agent)
    c = next(n for n in adapter.s.nodes("Osc"))
    print(f"\n  k_pid={K_PID} (damped)   k_osc={K_OSC} (conservative, period ~{2*3.14159/K_OSC:.0f} ticks)\n")
    print(f"    {'tick':>5}{'PID e (dissipative -> halts)':>32}{'osc x (conservative -> persists)':>36}")
    bar = lambda v, lo=-1.3, hi=1.3, w=30: " " * int((max(lo, min(hi, v)) - lo) / (hi - lo) * (w - 1)) + "*"
    for t in range(TICKS):
        adapter.master_tick(); adapter.tick()
        a = adapter.s.node(c)["attrs"]
        e = adapter.s.node(next(n for n in adapter.s.nodes("Residual")))["attrs"]["e"]
        print(f"    {t:>5}{e:>22.4f}        {a['x']:>8.3f}  |{bar(a['x'])}")
        adapter.s.set_attr(c, "observed", a["next_observed"])   # clock edge: the fold (commit next->current)
        adapter.s.set_attr(c, "x", a["next_x"])
        adapter.s.set_attr(c, "y", a["next_y"])

    af = adapter.s.node(c)["attrs"]
    print("\n" + "=" * 96)
    print(f"  PID e settled 16 -> ~0: the dissipative fold reached EQUILIBRIUM and STOPPED -- a fixpoint, a halt.")
    print(f"  osc x is still swinging (x={af['x']:.3f}) {TICKS} ticks in: a bounded LIMIT CYCLE that NEVER settles --")
    print(f"  the same fold, conservative instead of dissipative, persisting. The up-AND-down of x is impossible in a")
    print(f"  monotone in-tick fixpoint (Tarski: no decrease); it lives ONLY at the clock edge. THE PULSE IS THE")
    print(f"  SUSTAINED CYCLE, not the decay to a setpoint: persistence = the conservative fold that refuses to halt.")
    print(f"  This is the agent's rigorous core (a self = a limit cycle around an attractor), on the engine -- and it")
    print(f"  is NOT pitch/harmony (the deflated metaphor), it is the bounded oscillation that is the form of staying.")
    print("=" * 96)


if __name__ == "__main__":
    main()
