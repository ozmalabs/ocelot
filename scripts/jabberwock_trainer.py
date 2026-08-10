"""THE TRAINER PRIMITIVE — the agent's first graph-native gradient learner. Where compose-search picks a
closed-form model from a generated space, the trainer handles the case the two rules really need for the
handwriting climb: when the right model must be LEARNED from data, not derived.

The kernel is online gradient descent (the delta / Widrow-Hoff LMS rule), which IS gradient descent on the
squared error and the kernel of backprop:
    pred = w . x         (x = the recent history (value, prev, prev2, prev3))
    on the next observation:  err = target - pred ;  w_i += lr * err * x_i      (descend dE/dw_i)
It is graph-native (a Rule nudges the weights each tick), cheap and online (rule 1: a handful of weights, no
batch, no H100), and it LEARNS (rule 2). Per the two-rules clarification it is also what keeps a warm-start
LIVE -- nothing frozen, weights forever adapting.

Demonstrated on a signal whose recurrence cannot be guessed, only learned: v_t = sin(0.3 t), which obeys the
linear recurrence v_{t+1} = 2cos(0.3) v_t - v_{t-1} (true weights ~[1.911, -1, 0, 0]). The agent starts from
ZERO weights (pred 0, measure low) and its OWN live measure rises past target as the delta rule descends the
error -- the weights converge toward the true recurrence the agent never knew. Learning, in the heartbeat.

Every decision is a graph Rule (measure, learn=gradient step, predict, gate). The host only ingests the value
and beats master_tick;tick; it never tells the agent the recurrence.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_trainer.py
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.gap_prioritiser import install_builtinsufficient_gap_rule, MEASURED_TYPE

SEP = "=" * 100
TARGET = 0.9
LR = 0.4          # normalized-LMS step (step is divided by input power, so this is well-conditioned)
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


ABSDIFF = _Max(_Minus(A("o", "value"), A("o", "pred")), _Minus(A("o", "pred"), A("o", "value")))
MEASURED = _Div(_L(1.0), _Plus(_L(1.0), ABSDIFF))

MEASURE_RULE = {
    "id": "measure_train", "name": "measure_train",
    "match": [["h", "tr_pred", "o"]],
    "where": _Gt(A("o", "frame"), A("o", "mframe")),
    "effects": [
        ["add_node", "mc", MEASURED_TYPE, {
            "is_measured": 1.0, "measured": {"__term__": MEASURED}, "target": TARGET, "synth_pending": 1,
            "cap_sig": KEY, "capability_keys": KEY, "metric": "predictive_accuracy",
            "origin": "jabberwock:trainer", "composed_by": "agent"}],
        ["add_edge", "mc", "mc_self", "mc"],
        ["set_attr", "o", "last_measured", {"__term__": MEASURED}],
        ["set_attr", "o", "mframe", {"__term__": A("o", "frame")}]]}

# LEARN = one gradient step (delta rule). err = target(value) - pred(made last frame from stored inputs xi);
# w_i += lr * err * xi_i. Fires after measure (mframe==frame), once per frame (frame>lframe).
# err = target(value) - pred (made last frame). NORMALIZED delta step: scale by 1/(input power) so the update
# is well-conditioned on correlated inputs.  step = lr * err / (xi0^2 + xi1^2 + eps) ;  w_i += step * xi_i.
ERR = _Minus(A("o", "value"), A("o", "pred"))
POWER = _Plus(_Times(A("o", "xi0"), A("o", "xi0")), _Times(A("o", "xi1"), A("o", "xi1")), _L(0.05))
STEP = _Div(_Times(_L(LR), ERR), POWER)
LEARN_RULE = {
    "id": "learn_delta", "name": "learn_delta",
    "match": [["h", "tr_pred", "o"]],
    "where": _And(_Eq(A("o", "mframe"), A("o", "frame")), _Gt(A("o", "frame"), A("o", "lframe"))),
    "effects": [
        ["set_attr", "o", "w0", {"__term__": _Plus(A("o", "w0"), _Times(STEP, A("o", "xi0")))}],
        ["set_attr", "o", "w1", {"__term__": _Plus(A("o", "w1"), _Times(STEP, A("o", "xi1")))}],
        ["set_attr", "o", "lframe", {"__term__": A("o", "frame")}]]}

# PREDICT = the learned 2-tap linear model (the sine's true order); stores the inputs xi it used (for next
# frame's gradient step) and rolls history. Fires after learn (lframe==frame), once per frame.
PREDICT_RULE = {
    "id": "predict_train", "name": "predict_train",
    "match": [["h", "tr_pred", "o"]],
    "where": _And(_Eq(A("o", "lframe"), A("o", "frame")), _Gt(A("o", "frame"), A("o", "pframe"))),
    "effects": [
        ["set_attr", "o", "pred", {"__term__": _Plus(
            _Times(A("o", "w0"), A("o", "value")), _Times(A("o", "w1"), A("o", "prev")))}],
        ["set_attr", "o", "xi0", {"__term__": A("o", "value")}],
        ["set_attr", "o", "xi1", {"__term__": A("o", "prev")}],
        ["set_attr", "o", "prev", {"__term__": A("o", "value")}],
        ["set_attr", "o", "pframe", {"__term__": A("o", "frame")}]]}

GATE_RULE = {
    "id": "__trained", "name": "__trained",
    "match": [["h", "tr_pred", "o"]],
    "where": _And(_Gt(A("o", "last_measured"), _L(TARGET)), _Gt(_L(0.5), A("o", "trained"))),
    "effects": [["set_attr", "o", "trained", 1.0], ["set_attr", "o", "trained_at", {"__term__": A("o", "frame")}]]}


def main():
    print(SEP)
    print("THE TRAINER PRIMITIVE — graph-native online gradient descent (delta rule); the agent LEARNS a predictor.")
    print(SEP)

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    install_builtinsufficient_gap_rule(agent.s)

    o = agent.s.add_node("Observable", {"name": "sine", "value": 0.0, "pred": 0.0, "prev": 0.0,
                                        "frame": 0.0, "mframe": -1.0, "pframe": -1.0, "lframe": -1.0,
                                        "last_measured": 0.0, "trained": 0.0, "trained_at": -1.0,
                                        "w0": 0.0, "w1": 0.0, "xi0": 0.0, "xi1": 0.0})
    hub = agent.s.add_node("ObsHub", {"is_hub": 1.0})
    agent.inner.add_edge_unchecked(hub, "tr_pred", o)
    for r in (MEASURE_RULE, LEARN_RULE, PREDICT_RULE, GATE_RULE):
        agent.inner.add_rule(r)

    curve = []
    steps = 220
    for i in range(1, steps + 1):
        v = math.sin(0.3 * i)
        agent.s.set_attr(o, "value", float(v))
        agent.s.set_attr(o, "frame", float(i))
        agent.master_tick()
        agent.tick()
        oa = agent.s.node(o)["attrs"]
        curve.append((i, oa.get("last_measured"), [oa.get(f"w{k}") for k in range(2)]))

    oa = agent.s.node(o)["attrs"]
    w = [oa.get(f"w{k}") for k in range(2)]
    trained_at = int(oa.get("trained_at") or -1)
    true_w = [2 * math.cos(0.3), -1.0]
    start_m = sum(m for (_, m, _) in curve[:5]) / 5
    end_m = sum(m for (_, m, _) in curve[-20:]) / 20

    print(f"\n  signal v_t = sin(0.3 t); true recurrence weights ~ [{', '.join(f'{x:.3f}' for x in true_w)}] (agent is NOT told these).")
    print(f"  the agent starts from ZERO weights and learns online (delta rule) in the heartbeat:\n")
    print(f"    {'frame':>6}  {'measure':>8}  weights")
    for (i, m, ww) in curve:
        if i in (1, 5, 20, 50, 100, 150, 220):
            print(f"    {i:6d}  {m:8.3f}  [{', '.join(f'{x:6.3f}' for x in ww)}]")

    print(f"\n  measure: start (first 5) {start_m:.3f}  ->  end (last 20) {end_m:.3f}   (target {TARGET})")
    print(f"  learned weights [{', '.join(f'{x:.3f}' for x in w)}]  vs true [{', '.join(f'{x:.3f}' for x in true_w)}]")
    print(f"  crossed target ('trained') at frame {trained_at}")

    ok = (start_m < TARGET and end_m > TARGET and trained_at > 0
          and abs(w[0] - true_w[0]) < 0.25 and abs(w[1] - true_w[1]) < 0.25)
    print("\n" + SEP)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent's first graph-native gradient learner. Starting from zero weights, its")
    print(f"  online delta-rule updates descended the prediction error each tick until its OWN measure crossed")
    print(f"  target, the weights converging to the recurrence it was never told. This is the trainer primitive the")
    print(f"  two rules need for the handwriting climb: cheap + online (rule 1) and genuinely learned (rule 2) -- and")
    print(f"  the gradient kernel a warm-start would keep live (nothing frozen). Backprop is this rule, layered.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
