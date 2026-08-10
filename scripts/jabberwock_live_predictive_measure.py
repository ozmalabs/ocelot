"""RISING TIDE — a world-AGNOSTIC live measure banked each tick from REAL play: prediction-minus-observation.

GAP-2 (the load-bearing autonomy signal) existed only as a game-score prototype (gap2_live_measure.py:
measured = g.score - prev_score) -- usable only where there IS a score. This generalises it to the project's
central, SELF-SUPERVISED signal that every world has: the agent PREDICTS the next value of an observable, the
world REVEALS it, and the agent grades itself by prediction-minus-observation (surprise). No score, no label,
no teacher, no human-fed number -- the agent's own predictive accuracy, banked LIVE in the heartbeat
(master_tick;tick) as a MeasuredCapability that the EXISTING gap-mint rule + ranker consume. A real shortfall
(the world surprises the agent's model) auto-mints a CapabilityAxis -- so gaps 3/4 (compose-on-gap) can
self-trigger in ANY world. This is the rising tide: it makes self-improvement run on real signal everywhere.

Everything that DECIDES is a graph Rule/Term (the measure derivation, the gap mint, the rank). The host only:
ingests the observation (set o.value, o.frame -- mechanical I/O it cannot fake), installs the rules at boot,
and beats the heartbeat. The predictor here is PERSISTENCE (predict next = last seen) -- the simplest honest
model; a better predictor is exactly what the minted gap would later drive the agent to compose.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_live_predictive_measure.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from compose_lead_faculty import mint
from domains.gap_prioritiser import install_builtinsufficient_gap_rule, AXIS_TYPE, MEASURED_TYPE

SEP = "=" * 98
TARGET = 0.9          # the agent's bar for "I can predict this observable"; below it = a real shortfall.
KEY = ["predict_observable"]


def _V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
def _Lit(v): return {"type": "Lit", "value": v}


# the agent's world-AGNOSTIC live-measure faculty (graph-native). measured = 1/(1+|value-pred|) = predictive
# accuracy in (0,1]; |.| via Max(a-b, b-a) (no Abs term needed). Frame-guarded (fires once per new frame,
# settles in the fixpoint). Banks a MeasuredCapability the existing synth rule + ranker already consume, then
# rolls the predictor forward (pred := value = persistence) for the next frame.
ABSDIFF = {"type": "Max", "items": [
    {"type": "Minus", "a": A("o", "value"), "b": A("o", "pred")},
    {"type": "Minus", "a": A("o", "pred"), "b": A("o", "value")}]}
MEASURED = {"type": "Div", "a": _Lit(1.0), "b": {"type": "Plus", "items": [_Lit(1.0), ABSDIFF]}}

MEASURE_RULE = {
    "id": "measure_prediction", "name": "measure_prediction",
    "match": [["h", "observes", "o"]],
    "where": {"type": "Not", "arg": {"type": "Eq", "a": A("o", "last_frame"), "b": A("o", "frame")}},
    "effect": [
        ["add_node", "mc", MEASURED_TYPE, {
            "is_measured": 1.0,
            "measured": {"__term__": MEASURED},
            "target": TARGET,
            "synth_pending": 1,
            "cap_sig": KEY,
            "capability_keys": KEY,
            "metric": "predictive_accuracy",
            "note": "live prediction-minus-observation, banked in the heartbeat",
            "origin": "jabberwock:live_predictive_measure",
            "composed_by": "agent"}],
        ["add_edge", "mc", "mc_self", "mc"],            # so the existing gap-mint rule (match mc_self) sees it
        ["add_edge", "mc", "measures_obs", "o"],         # provenance
        ["set_attr", "o", "pred", {"__term__": A("o", "value")}],   # predictor rolls forward (persistence)
        ["set_attr", "o", "last_frame", {"__term__": A("o", "frame")}]]}


class PredictiveWorld:
    """Host world adapter (mechanical I/O only). Presents one observable's value each tick; the agent must
    predict it. The host cannot fake the agent's grade -- it only stamps the world's own value + frame."""

    def __init__(self, agent, name="signal"):
        self.agent, self.frame = agent, 0
        self.o = agent.s.add_node("Observable", {"name": name, "value": 0.0, "pred": 0.0,
                                                 "frame": 0.0, "last_frame": -1.0})
        self.hub = agent.s.add_node("ObsHub", {"is_hub": 1.0})
        agent.inner.add_edge_unchecked(self.hub, "observes", self.o)

    def present(self, value: float):
        """Reveal the actual value for this tick (real play: the agent already holds its prediction in o.pred)."""
        self.frame += 1
        self.agent.s.set_attr(self.o, "value", float(value))
        self.agent.s.set_attr(self.o, "frame", float(self.frame))


def run(regime: str, steps: int = 40):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    install_builtinsufficient_gap_rule(agent.s)          # the existing gap-mint rule fires in tick()
    world = PredictiveWorld(agent)
    agent.s.set_attr(world.o, "pred", 0.0)               # predictor's birth state; the rule updates it after
    mint(agent, MEASURE_RULE)                            # the agent's live-measure faculty, minted into the loop

    rng = np.random.default_rng(7)
    axes0 = set(agent.s.nodes(AXIS_TYPE))
    v = 0.0
    measures = []
    for i in range(steps):
        if regime == "predictable":
            v = min(1.0, v + 0.02)                       # a slow, non-wrapping ramp -- persistence predicts it well
        else:
            v = float(rng.random())                      # surprising jumps -- persistence fails
        world.present(v)
        agent.master_tick()
        agent.tick()                                     # the heartbeat: tick() runs the measure + gap rules
    # read back what the agent banked (no number was fed in -- the rule computed every one).
    for m in agent.s.nodes(MEASURED_TYPE):
        a = agent.s.node(m)["attrs"]
        if a.get("origin") == "jabberwock:live_predictive_measure":
            measures.append(float(a.get("measured", 0.0)))
    new_axes = [n for n in agent.s.nodes(AXIS_TYPE) if n not in axes0
                and agent.s.node(n)["attrs"].get("origin") == "gap_prioritiser:built_insufficient"]
    mean_m = sum(measures) / max(len(measures), 1)
    shortfalls = [round(float(agent.s.node(n)["attrs"].get("shortfall", 0.0)), 3) for n in new_axes]
    return mean_m, len(measures), new_axes, shortfalls


def persist():
    out = dict(MEASURE_RULE); out["effects"] = out.pop("effect")
    path = os.path.join(ROOT, "seeds", "generated", "measure_prediction.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"id": "measure_prediction", "version": "1.0.0", "rules": [out]}, f, indent=2)
    os.replace(tmp, path)
    return path


def main():
    print(SEP)
    print("RISING TIDE — world-agnostic LIVE measure: prediction-minus-observation, banked in the heartbeat.")
    print(SEP)

    pm, pn, pax, _ = run("predictable")
    sm, sn, sax, ssf = run("surprising")

    print(f"\n  PREDICTABLE world (slow ramp; the agent's persistence model fits it):")
    print(f"    banked {pn} live measures, mean predictive accuracy = {pm:.3f}  (>= target {TARGET}: model suffices)")
    print(f"    gaps auto-minted by the heartbeat: {len(pax)}  (no shortfall -> no gap)")
    print(f"\n  SURPRISING world (random jumps; the agent's model is surprised):")
    print(f"    banked {sn} live measures, mean predictive accuracy = {sm:.3f}  (< target {TARGET}: real shortfall)")
    print(f"    gaps auto-minted by the heartbeat: {len(sax)}  shortfalls={ssf[:6]}{'...' if len(ssf) > 6 else ''}")

    path = persist()
    ok = (pn > 0 and sn > 0 and pm > TARGET and sm < TARGET and len(pax) == 0 and len(sax) > 0)
    print("\n" + SEP)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent banks a REAL, self-supervised capability signal every tick")
    print(f"  in ANY world, with no score / label / human number: its own prediction-minus-observation. When the")
    print(f"  world is predictable its measure clears target and NO gap is minted; when the world surprises it,")
    print(f"  the measure falls below target and the EXISTING gap-mint rule auto-opens a CapabilityAxis IN THE")
    print(f"  LIVE LOOP -- the load-bearing signal gaps 3/4 (compose-on-gap) consume, now world-agnostic. The")
    print(f"  rising tide: self-improvement runs on real measured signal everywhere, not on numbers I feed in.")
    print(f"  Persisted -> {os.path.relpath(path, ROOT)} (boots next session).")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
