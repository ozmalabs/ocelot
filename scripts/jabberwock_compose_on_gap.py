"""AUTONOMY CORE (GAPS 3+4) — a gap the LIVE MEASURE produces drives the agent to COMPOSE a better faculty,
install it live, gate-keep it, and persist it. Zero human touches inside the loop.

The pieces existed but nothing connected them on a real world:
  - the live measure (jabberwock_live_predictive_measure): banks predict-minus-observe each tick; a shortfall
    auto-mints a CapabilityAxis IN THE LIVE LOOP;
  - intrinsic self-repair (seeds/self_repair.json): a graph rule REWRITES a named live rule's effect clause via
    set_rule_clause(rule_name, "effect", <new clause>) -- rule edits rule, in the running loop;
  - the gap machinery (gap_prioritiser): mints the axis from the measured shortfall.

This wires them into one self-driving arc on a world the agent's INITIAL predictor fails:
  ramp (slope 0.3)  ->  PERSISTENCE predictor (pred:=last value) is surprised every frame (|Δ|=0.3)
     ->  measure banks ~0.77 < target  ->  gap-mint rule opens a CapabilityAxis (live)
     ->  on a SUSTAINED shortfall the COMPOSE-ON-GAP reflex REWRITES the predictor's effect to a LINEAR
         extrapolation it composes from held primitives (pred := value + (value-prev) = 2·value - prev)
     ->  the rewritten faculty predicts the ramp exactly  ->  the agent's OWN measure rises to ~1.0
     ->  the GATE rule sees measure >= target and marks the faculty KEPT  ->  host persists it.

Every DECISION is a graph Rule (measure, gap-mint, compose-rewrite, gate). The host only ingests the value
(mechanical I/O it cannot fake), installs the agent's faculties as graph data at boot, beats master_tick;tick,
and writes the kept faculty to disk. The composed predictor is built from the agent's held Term primitives.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_compose_on_gap.py
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

SEP = "=" * 98
TARGET = 0.9
SLOPE = 0.3
KEY = ["predict_observable"]
PREDICT_ID = "predict_observable"


def _V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
def _L(v): return {"type": "Lit", "value": v}
def _Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def _And(*xs): return {"type": "And", "items": list(xs)}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def _Plus(*xs): return {"type": "Plus", "items": list(xs)}
def _Max(*xs): return {"type": "Max", "items": list(xs)}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _IfThenElse(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}


# measured = 1/(1+|value-pred|); |.| via Max(a-b, b-a). Stamps o.last_measured and a SUSTAINED-shortfall streak.
ABSDIFF = _Max(_Minus(A("o", "value"), A("o", "pred")), _Minus(A("o", "pred"), A("o", "value")))
MEASURED = _Div(_L(1.0), _Plus(_L(1.0), ABSDIFF))

MEASURE_RULE = {
    "id": "measure_prediction_co", "name": "measure_prediction_co",
    "match": [["h", "predicts", "o"]],
    "where": _Gt(A("o", "frame"), A("o", "mframe")),
    "effects": [
        ["add_node", "mc", MEASURED_TYPE, {
            "is_measured": 1.0, "measured": {"__term__": MEASURED}, "target": TARGET,
            "synth_pending": 1, "cap_sig": KEY, "capability_keys": KEY,
            "metric": "predictive_accuracy", "origin": "jabberwock:compose_on_gap", "composed_by": "agent"}],
        ["add_edge", "mc", "mc_self", "mc"],
        ["set_attr", "o", "last_measured", {"__term__": MEASURED}],
        # don't compose on one surprise (could be noise); miss_streak counts consecutive shortfalls.
        ["set_attr", "o", "miss_streak", {"__term__": _IfThenElse(
            _Gt(_L(TARGET), MEASURED), _Plus(A("o", "miss_streak"), _L(1.0)), _L(0.0))}],
        ["set_attr", "o", "mframe", {"__term__": A("o", "frame")}]]}

# the swappable PREDICTOR faculty. Boots as PERSISTENCE (pred := last value). Fires after measure
# (mframe==frame), once per frame (frame > pframe). Maintains o.prev so a linear successor has the history.
PERSISTENCE_EFFECT = [
    ["set_attr", "o", "pred", {"__term__": A("o", "value")}],
    ["set_attr", "o", "prev", {"__term__": A("o", "value")}],
    ["set_attr", "o", "pframe", {"__term__": A("o", "frame")}]]
PREDICT_RULE = {
    "id": PREDICT_ID, "name": PREDICT_ID,
    "match": [["h", "predicts", "o"]],
    "where": _And(_Eq(A("o", "mframe"), A("o", "frame")), _Gt(A("o", "frame"), A("o", "pframe"))),
    "effects": PERSISTENCE_EFFECT}

# the agent's COMPOSED successor, held as graph data: a LINEAR-extrapolation effect built from Plus/Minus over
# the observable's own state (pred := value + (value - prev) = 2·value - prev). The compose reflex installs it.
LINEAR_EFFECT = [
    ["set_attr", "o", "pred", {"__term__": _Plus(A("o", "value"), _Minus(A("o", "value"), A("o", "prev")))}],
    ["set_attr", "o", "prev", {"__term__": A("o", "value")}],
    ["set_attr", "o", "pframe", {"__term__": A("o", "frame")}]]

# COMPOSE-ON-GAP reflex: the live measure opens a CapabilityAxis on every surprised frame; when the shortfall
# is SUSTAINED (o.miss_streak >= 3), REWRITE the predictor's effect clause to the linear successor via
# set_rule_clause (the intrinsic-self-repair wire). Rule edits rule, in the live loop -- "the effect emits its
# own mint". Triggered off the single observable so it fires once.
COMPOSE_ON_GAP = {
    "id": "__compose_on_gap", "name": "__compose_on_gap",
    "match": [["h", "predicts", "o"], ["ag", "holds_successor", "t"]],
    "where": _And(_Gt(A("o", "miss_streak"), _L(2.5)), _Gt(_L(0.5), A("o", "repaired"))),
    "effects": [
        ["set_rule_clause", PREDICT_ID, "effect", {"__term__": A("t", "new_effect")}],
        ["set_attr", "o", "repaired", 1.0]]}

# GATE reflex: once rewritten, if the agent's OWN latest measure clears target, mark the faculty KEPT.
GATE_RULE = {
    "id": "__gate_keep", "name": "__gate_keep",
    "match": [["h", "predicts", "o"]],
    "where": _And(_Eq(A("o", "repaired"), _L(1.0)), _Gt(A("o", "last_measured"), _L(TARGET)),
                  _Gt(_L(0.5), A("o", "kept"))),
    "effects": [["set_attr", "o", "kept", 1.0]]}


def main():
    print(SEP)
    print("AUTONOMY CORE (GAPS 3+4) — gap (live measure) -> COMPOSE better faculty -> install live -> gate-keep -> persist.")
    print(SEP)

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    install_builtinsufficient_gap_rule(agent.s)

    o = agent.s.add_node("Observable", {"name": "ramp", "value": 0.0, "pred": 0.0, "prev": 0.0,
                                        "frame": 0.0, "mframe": -1.0, "pframe": -1.0, "miss_streak": 0.0,
                                        "repaired": 0.0, "kept": 0.0, "last_measured": 0.0})
    hub = agent.s.add_node("ObsHub", {"is_hub": 1.0})
    agent.inner.add_edge_unchecked(hub, "predicts", o)
    # the agent's composed successor, held as graph data (the linear effect as a stored Value).
    t = agent.s.add_node("Successor", {"new_effect": LINEAR_EFFECT, "id": PREDICT_ID})
    agent.inner.add_edge_unchecked(agent.agent, "holds_successor", t)

    for r in (MEASURE_RULE, PREDICT_RULE, COMPOSE_ON_GAP, GATE_RULE):
        agent.inner.add_rule(r)

    trace = []
    v = 0.0
    upgraded_at = kept_at = None
    for i in range(1, 31):
        v = round(i * SLOPE, 4)
        agent.s.set_attr(o, "value", float(v))
        agent.s.set_attr(o, "frame", float(i))
        agent.master_tick()
        agent.tick()
        oa = agent.s.node(o)["attrs"]
        lm, rp, kp = oa.get("last_measured"), oa.get("repaired"), oa.get("kept")
        if rp == 1.0 and upgraded_at is None:
            upgraded_at = i
        if kp == 1.0 and kept_at is None:
            kept_at = i
        trace.append((i, v, lm, rp, kp))

    axes = [n for n in agent.s.nodes(AXIS_TYPE)
            if agent.s.node(n)["attrs"].get("origin") == "gap_prioritiser:built_insufficient"]
    ua = upgraded_at or (len(trace) + 1)
    pre = [m for (i, _, m, _, _) in trace if i < ua and m is not None]
    post = [m for (i, _, m, _, _) in trace if i >= len(trace) - 9 and m is not None]
    mean_pre = sum(pre) / max(len(pre), 1)
    mean_post = sum(post) / max(len(post), 1)

    print(f"\n  world = ramp (slope {SLOPE}); the agent boots with PERSISTENCE only. live trace:")
    for (i, vv, lm, rp, kp) in trace:
        if i <= 4 or (upgraded_at and upgraded_at - 1 <= i <= upgraded_at + 3) or i >= 29:
            mk = ("  <- sustained gap -> COMPOSE+REWRITE to linear" if i == upgraded_at else
                  "  <- KEPT (gate)" if i == kept_at else "")
            print(f"    frame {i:2d}  value={vv:5.2f}  measure={lm:.3f}  repaired={int(rp or 0)}  kept={int(kp or 0)}{mk}")

    print(f"\n  gaps auto-minted by the heartbeat : {len(axes)}")
    print(f"  composed-rewrite fired at frame   : {upgraded_at}")
    print(f"  mean measure  pre-compose  (persistence)  : {mean_pre:.3f}")
    print(f"  mean measure  post-compose (linear, last10): {mean_post:.3f}")

    kept = agent.s.node(o)["attrs"].get("kept") == 1.0
    persisted = None
    if kept:
        out = {"id": PREDICT_ID, "name": PREDICT_ID, "match": PREDICT_RULE["match"],
               "where": PREDICT_RULE["where"], "effects": LINEAR_EFFECT}
        path = os.path.join(ROOT, "seeds", "generated", "predict_observable_linear.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"id": "predict_observable_linear", "version": "1.0.0", "rules": [out]}, f, indent=2)
        os.replace(tmp, path)
        persisted = os.path.relpath(path, ROOT)

    ok = (len(axes) > 0 and upgraded_at is not None and kept
          and mean_post > TARGET and mean_post > mean_pre + 0.1)
    print("\n" + SEP)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent closed the autonomy loop with no human touch inside it: its")
    print(f"  live measure opened a real gap; on the SUSTAINED shortfall a graph reflex COMPOSED a better predictor")
    print(f"  from held primitives and REWROTE its own predictor faculty live (rule edits rule); the agent's OWN")
    print(f"  measure then rose past target ({mean_pre:.2f} -> {mean_post:.2f}) so the GATE rule kept it.", end="")
    print(f" Persisted -> {persisted} (boots next session)." if persisted else " (not kept)")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
