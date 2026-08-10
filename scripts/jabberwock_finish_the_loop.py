"""FINISH THE LOOP — close the understand-drive's residual loop, graph-natively, so a capability's error DECAYS.

The agent's open loop: it runs an operator, MEASURES the skill, banks the residual (shortfall = target - skill) on
the axis -- and then DISCARDS it. It attends to where it predicts worst (frontier_pick), but never CORRECTS toward
better: the operator is re-measured, never adjusted. The loop is open. Shortfall sits flat.

Close it with the pulse -- a synchronous circuit, the same structure that closed the toy:
  - OBSERVE (mechanical host I/O): run the operator at the current parameter theta -> skill = f(theta); write skill
    + shortfall. (The world executor; admissible adapter work.)
  - CORRECT (a graph PRODUCTION -- the agent's DECISION): an adaptive hill-climb. delta = skill - last_skill;
    improved = delta>0; next_dir = keep dir if improved else FLIP; next_step = keep if improved else HALVE;
    next_theta = theta + next_dir*next_step. It discovers the correction direction from the residual's CHANGE -- no
    hand-given gradient. Pure graph arithmetic (Gt / IfThenElse / Times / Plus).
  - FOLD (the clock edge): commit next_* -> current at master_tick. The non-monotone down-stroke, at its lawful home.

OPEN (measure only, no correction) vs CLOSED (+ the fold). The claim: only the CLOSED loop drives the shortfall DOWN
-- the agent's reasoning gets the restoring force. (Synthetic operator skill=f(theta) with a hidden optimum, so the
convergence is measurable; the real predictors plug into the same fold. theta* is host-only -- the agent never sees
it, it finds it from the residual.)

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_finish_the_loop
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter

THETA0, THETA_STAR, SIGMA = 4.0, 0.0, 2.0       # operator param; hidden optimum (HOST-ONLY); landscape width
TARGET, TICKS = 1.0, 22


def skill_of(theta):
    """The world executor running the operator: a smooth capability landscape (host I/O; theta* is hidden)."""
    return math.exp(-((theta - THETA_STAR) ** 2) / (2 * SIGMA * SIGMA))


def _o(key):
    return {"type": "Attr", "node": {"name": "o", "type": "Var"}, "key": key}


def _lit(v):
    return {"type": "Lit", "value": v}


# the graph-native adaptive hill-climb (the agent's correction decision):
_delta = {"type": "Minus", "a": _o("skill"), "b": _o("last_skill")}
_improved = {"type": "Gt", "a": _delta, "b": _lit(0.0)}
_next_dir = {"type": "IfThenElse", "cond": _improved, "then": _o("dir"),
             "other": {"type": "Times", "items": [_lit(-1.0), _o("dir")]}}
_next_step = {"type": "IfThenElse", "cond": _improved, "then": _o("step"),
              "other": {"type": "Times", "items": [_lit(0.5), _o("step")]}}
_next_theta = {"type": "Plus", "items": [_o("theta"), {"type": "Times", "items": [_next_dir, _next_step]}]}

MANIFEST = {
    "id": "finishloop", "version": "1.0.0", "depends_on": [],
    "nodes": [
        {"local_id": 0, "type": "TunedOp",
         "attrs": {"theta": THETA0, "skill": 0.0, "last_skill": -1.0, "dir": 1.0, "step": 1.0,
                   "next_theta": THETA0, "next_dir": 1.0, "next_step": 1.0}},
        {"local_id": 1, "type": "CapAxis", "attrs": {"target": TARGET, "shortfall": 1.0}},
    ],
    "edges": [{"src": {"local": 0}, "type": "tunes", "tgt": {"local": 1}}],
    "productions": [{"provenance": "seed:finishloop:tunes",
                     "src": {"type": "TunedOp", "var": "o"}, "edge_type": "tunes",
                     "tgt": {"type": "CapAxis", "var": "ax"}}],
    "rules": [{
        "name": "shortfall_drives_correction",
        "match": [["o", "tunes", "ax"]],
        "where": {"type": "Lit", "value": True},
        "effects": [
            ["set_attr", "o", "next_dir", {"__term__": _next_dir}],
            ["set_attr", "o", "next_step", {"__term__": _next_step}],
            ["set_attr", "o", "next_theta", {"__term__": _next_theta}],
        ],
    }],
}


def run(closed):
    ad = WorldAdapter()
    ad.inner.load_seed_manifest(MANIFEST, ad.agent)
    o = next(n for n in ad.s.nodes("TunedOp"))
    ax = next(n for n in ad.s.nodes("CapAxis"))
    rows = []
    for t in range(TICKS):
        a = ad.s.node(o)["attrs"]
        skill = skill_of(a["theta"])                                  # OBSERVE: run the operator (host I/O)
        ad.s.set_attr(o, "skill", skill)
        ad.s.set_attr(ax, "shortfall", TARGET - skill)
        rows.append((a["theta"], skill, TARGET - skill))
        if closed:
            ad.master_tick(); ad.tick()                               # CORRECT: the fold production computes next_*
            b = ad.s.node(o)["attrs"]
            ad.s.set_attr(o, "theta", b["next_theta"])                # FOLD at the clock edge (commit next->current)
            ad.s.set_attr(o, "last_skill", skill)
            ad.s.set_attr(o, "dir", b["next_dir"]); ad.s.set_attr(o, "step", b["next_step"])
    return rows


def main():
    print("=" * 96)
    print("FINISH THE LOOP — measure-only (OPEN) vs measure+correct (CLOSED): does the shortfall DECAY?")
    print("=" * 96)
    op = run(False)
    cl = run(True)
    print(f"\n  operator theta0={THETA0}, hidden optimum theta*={THETA_STAR} (host-only), target skill={TARGET}\n")
    print(f"    {'tick':>5}{'OPEN shortfall':>18}{'CLOSED shortfall':>20}{'CLOSED theta':>16}{'CLOSED skill':>14}")
    for t in range(TICKS):
        print(f"    {t:>5}{op[t][2]:>18.4f}{cl[t][2]:>20.4f}{cl[t][0]:>16.3f}{cl[t][1]:>14.4f}")

    print("\n" + "=" * 96)
    o0, of = op[0][2], op[-1][2]
    c0, cf = cl[0][2], cl[-1][2]
    print(f"  OPEN  shortfall {o0:.3f} -> {of:.3f}: FLAT. The loop measures, banks the residual, and discards it -- it")
    print(f"        attends to the error but never corrects; the operator is never improved. (the agent's open loop.)")
    print(f"  CLOSED shortfall {c0:.3f} -> {cf:.3f}: DECAYED to ~0. The same loop, with the residual ASSERTED and folded")
    print(f"        into a correction -- a graph-native hill-climb that found theta {THETA0}->{cl[-1][0]:.2f} ~ theta*={THETA_STAR}")
    print(f"        from the residual's CHANGE alone (no given gradient), skill {cl[0][1]:.2f}->{cl[-1][1]:.3f}. The decrease")
    print(f"        lives at the CLOCK EDGE (a value going DOWN -- impossible in a monotone in-tick fixpoint).")
    print(f"  THE LOOP IS FINISHED: residual -> correction -> fold, on the real engine; the decision (which way to")
    print(f"  correct) is a graph PRODUCTION, the measure + commit are host I/O. The understand-drive now has its")
    print(f"  restoring force -- it CORRECTS where it predicts worst, not just attends. The pulse, in the live loop.")
    print("=" * 96)


if __name__ == "__main__":
    main()
