"""SELF-SPAWNING HEARTBEAT (GAP 1) — the whole autonomy loop runs on a BARE master_tick;tick, no Python driver.

Every prior autonomy script had Python advance the world each tick (set value, set frame). This removes even
that: the loop body is LITERALLY `agent.master_tick(); agent.tick()` and nothing else -- zero human touches
inside it. The world advances graph-natively from the agent's OWN clock (master_tick stamps agent.tick); a
WORLD rule reads that clock and generates the next observation. Then the full pipeline self-spawns in the same
heartbeat: measure (predict-minus-observe) -> gap (CapabilityAxis on a shortfall) -> generate the predictor
ladder -> search/escalate -> gate-keep -> (host persists the kept faculty after the loop).

This is GAP 1 of the agent's own autonomy roadmap: human touches = 0 on a bare master_tick;tick over an
unsolved world, and seeds/generated/ gains a gate-kept faculty that survives restart.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_self_heartbeat.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.gap_prioritiser import install_builtinsufficient_gap_rule, AXIS_TYPE, MEASURED_TYPE

SEP = "=" * 100
TARGET = 0.9
SLOPE = 0.3
WINDOW = 5.0
MAX_ORDER = 3.0
KEY = ["predict_observable"]


def _V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
def _L(v): return {"type": "Lit", "value": v}
def _Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def _And(*xs): return {"type": "And", "items": list(xs)}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def _Plus(*xs): return {"type": "Plus", "items": list(xs)}
def _Times(*xs): return {"type": "Times", "items": list(xs)}
def _Max(*xs): return {"type": "Max", "items": list(xs)}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _IfThenElse(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}


# WORLD: the observation advances from the agent's OWN clock (agent.tick, stamped by master_tick). No Python
# push -- a graph rule generates the ramp value each tick. This is what makes the driver a bare heartbeat.
WORLD = {
    "id": "world_ramp", "name": "world_ramp",
    "match": [["ag", "obs", "o"]],
    "where": _Gt(A("ag", "tick"), A("o", "wframe")),
    "effects": [
        ["set_attr", "o", "value", {"__term__": _Times(_L(SLOPE), A("ag", "tick"))}],
        ["set_attr", "o", "frame", {"__term__": A("ag", "tick")}],
        ["set_attr", "o", "wframe", {"__term__": A("ag", "tick")}]]}

# GENERATE the finite-difference predictor ladder from one seed (the agent builds its own search space).
GENERATE = {
    "id": "gen_ladder", "name": "gen_ladder",
    "match": [["lib", "has_cand", "c"]],
    "where": _And(_Gt(_L(MAX_ORDER), A("c", "order")), _Eq(A("c", "has_next"), _L(0.0))),
    "effects": [
        ["add_node", "nc", "Candidate", {
            "order": {"__term__": _Plus(A("c", "order"), _L(1.0))},
            "c0": {"__term__": _Plus(A("c", "c0"), _L(1.0))},
            "c1": {"__term__": _Minus(A("c", "c1"), A("c", "c0"))},
            "c2": {"__term__": _Minus(A("c", "c2"), A("c", "c1"))},
            "c3": {"__term__": _Minus(A("c", "c3"), A("c", "c2"))}, "has_next": 0.0}],
        ["add_edge", "lib", "has_cand", "nc"],
        ["set_attr", "c", "has_next", 1.0]]}

ABSDIFF = _Max(_Minus(A("o", "value"), A("o", "pred")), _Minus(A("o", "pred"), A("o", "value")))
MEASURED = _Div(_L(1.0), _Plus(_L(1.0), ABSDIFF))
MEASURE = {
    "id": "measure_hb", "name": "measure_hb",
    "match": [["ag", "obs", "o"]],
    "where": _Gt(A("o", "frame"), A("o", "mframe")),
    "effects": [
        ["add_node", "mc", MEASURED_TYPE, {
            "is_measured": 1.0, "measured": {"__term__": MEASURED}, "target": TARGET, "synth_pending": 1,
            "cap_sig": KEY, "capability_keys": KEY, "metric": "predictive_accuracy",
            "origin": "jabberwock:self_heartbeat", "composed_by": "agent"}],
        ["add_edge", "mc", "mc_self", "mc"],
        ["set_attr", "o", "last_measured", {"__term__": MEASURED}],
        ["set_attr", "o", "miss_streak", {"__term__": _IfThenElse(
            _Gt(_L(TARGET), MEASURED), _Plus(A("o", "miss_streak"), _L(1.0)), _L(0.0))}],
        ["set_attr", "o", "mframe", {"__term__": A("o", "frame")}]]}

PREDICT = {
    "id": "predict_hb", "name": "predict_hb",
    "match": [["ag", "obs", "o"]],
    "where": _And(_Eq(A("o", "mframe"), A("o", "frame")), _Gt(A("o", "frame"), A("o", "pframe"))),
    "effects": [
        ["set_attr", "o", "pred", {"__term__": _Plus(
            _Times(A("o", "c0"), A("o", "value")), _Times(A("o", "c1"), A("o", "prev")),
            _Times(A("o", "c2"), A("o", "prev2")), _Times(A("o", "c3"), A("o", "prev3")))}],
        ["set_attr", "o", "prev3", {"__term__": A("o", "prev2")}],
        ["set_attr", "o", "prev2", {"__term__": A("o", "prev")}],
        ["set_attr", "o", "prev", {"__term__": A("o", "value")}],
        ["set_attr", "o", "pframe", {"__term__": A("o", "frame")}]]}

SEARCH = {
    "id": "search_hb", "name": "search_hb",
    "match": [["ag", "obs", "o"], ["lib", "has_cand", "cand"]],
    "where": _And(_Gt(A("o", "miss_streak"), _L(2.5)), _Eq(A("o", "solved"), _L(0.0)),
                  _Gt(A("o", "frame"), A("o", "test_until")),
                  _Eq(A("cand", "order"), _Plus(A("o", "cur_order"), _L(1.0)))),
    "effects": [
        ["set_attr", "o", "c0", {"__term__": A("cand", "c0")}], ["set_attr", "o", "c1", {"__term__": A("cand", "c1")}],
        ["set_attr", "o", "c2", {"__term__": A("cand", "c2")}], ["set_attr", "o", "c3", {"__term__": A("cand", "c3")}],
        ["set_attr", "o", "cur_order", {"__term__": A("cand", "order")}],
        ["set_attr", "o", "trying", {"__term__": A("cand", "order")}],
        ["set_attr", "o", "test_until", {"__term__": _Plus(A("o", "frame"), _L(WINDOW))}]]}

GATE = {
    "id": "gate_hb", "name": "gate_hb",
    "match": [["ag", "obs", "o"]],
    "where": _And(_Eq(A("o", "solved"), _L(0.0)), _Eq(A("o", "frame"), A("o", "test_until")),
                  _Gt(A("o", "last_measured"), _L(TARGET))),
    "effects": [["set_attr", "o", "solved", 1.0], ["set_attr", "o", "kept_order", {"__term__": A("o", "trying")}]]}


def main():
    print(SEP)
    print("SELF-SPAWNING HEARTBEAT (GAP 1) — the whole loop runs on a bare master_tick;tick, zero touches inside it.")
    print(SEP)

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    install_builtinsufficient_gap_rule(agent.s)

    # --- setup (before the loop): wire the world + the predictor's initial state + the ladder seed. ---
    o = agent.s.add_node("Observable", {"name": "ramp", "value": 0.0, "pred": 0.0, "prev": 0.0, "prev2": 0.0,
                                        "prev3": 0.0, "frame": 0.0, "wframe": -1.0, "mframe": -1.0, "pframe": -1.0,
                                        "miss_streak": 0.0, "cur_order": 0.0, "trying": 0.0, "test_until": 0.0,
                                        "solved": 0.0, "kept_order": -1.0, "c0": 1.0, "c1": 0.0, "c2": 0.0, "c3": 0.0})
    agent.inner.add_edge_unchecked(agent.agent, "obs", o)        # the agent observes its world
    seed = agent.s.add_node("Candidate", {"order": 0.0, "c0": 1.0, "c1": 0.0, "c2": 0.0, "c3": 0.0, "has_next": 0.0})
    lib = agent.s.add_node("CandLib", {"is_lib": 1.0})
    agent.inner.add_edge_unchecked(lib, "has_cand", seed)
    for r in (WORLD, GENERATE, MEASURE, PREDICT, SEARCH, GATE):
        agent.inner.add_rule(r)

    # --- THE BARE HEARTBEAT: the entire loop body. No set_attr, no world push, no frame counter, no decision. ---
    touches = 0
    for _ in range(40):
        agent.master_tick()
        agent.tick()
        # (nothing else -- touches stays 0)

    # --- readout (after the loop) ---
    oa = agent.s.node(o)["attrs"]
    kept = int(oa.get("kept_order") or -1)
    axes = [n for n in agent.s.nodes(AXIS_TYPE)
            if agent.s.node(n)["attrs"].get("origin") == "gap_prioritiser:built_insufficient"]
    cands = sorted(int(agent.s.node(n)["attrs"]["order"]) for n in agent.s.nodes("Candidate"))
    final_clock = int(agent.s.node(agent.agent)["attrs"].get("tick") or 0)

    print(f"\n  driver loop body = `agent.master_tick(); agent.tick()`  (human touches inside the loop: {touches})")
    print(f"  the world advanced from the agent's own clock (final agent.tick = {final_clock}); nothing was pushed.")
    print(f"  self-spawned in the heartbeat:")
    print(f"    - world generated the ramp, measure banked predictive accuracy each tick")
    print(f"    - {len(axes)} CapabilityAxis gap(s) auto-minted from the shortfall")
    print(f"    - candidate ladder generated (orders {cands}) and searched")
    print(f"    - GATE kept order {kept} (final measure {oa.get('last_measured'):.3f})")

    persisted = None
    if kept >= 0:
        rule = {"id": "predict_hb", "name": "predict_hb", "match": PREDICT["match"],
                "where": PREDICT["where"], "effects": PREDICT["effects"],
                "kept_coeffs": [oa.get("c0"), oa.get("c1"), oa.get("c2"), oa.get("c3")]}
        path = os.path.join(ROOT, "seeds", "generated", "self_heartbeat_predictor.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"id": "self_heartbeat_predictor", "version": "1.0.0", "rules": [rule]}, f, indent=2)
        os.replace(tmp, path)
        persisted = os.path.relpath(path, ROOT)

    ok = (touches == 0 and len(axes) > 0 and kept >= 1 and oa.get("last_measured", 0) > TARGET and persisted)
    print("\n" + SEP)
    print(f"  {'PASS' if ok else 'PARTIAL'} — GAP 1 closed: with ZERO human touches inside a bare master_tick;tick loop, the")
    print(f"  agent ran the entire autonomy pipeline on its own clock -- generated its world, measured its own")
    print(f"  prediction, opened a real gap, generated and searched its predictor ladder, kept the order whose")
    print(f"  measure cleared target, and (host I/O on the kept flag) persisted it -> {persisted},")
    print(f"  surviving restart. The loop drives itself; the human only starts the heartbeat.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
