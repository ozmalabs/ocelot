"""AUTONOMY — the agent GENERATES its own search space graph-natively, then searches it. Closes the last
hand-holding in jabberwock_compose_search (where the HOST enumerated the candidate list).

The candidate predictors are the finite-difference extrapolator LADDER (order 0 = persistence, 1 = linear,
2 = quadratic, 3 = cubic, ...), the resource-rational model-complexity ladder. It has a clean graph recurrence
on the coefficients of pred = c0*value + c1*prev + c2*prev2 + c3*prev3:
    order k  from  order k-1 :   c0 += 1 ;  c1 -= old c0 ;  c2 -= old c1 ;  c3 -= old c2
(seed order 0 = [1,0,0,0]). A GENERATE rule unrolls the whole ladder from that single seed -- so the agent
builds its OWN candidate space, the host lists nothing. The SEARCH then escalates order on a sustained gap
until the agent's own measure clears target. Proven on three worlds where successively HIGHER orders win:

    ramp  v=0.3t    -> order 1 (linear  [2,-1,0,0])  wins
    quad  v=0.1t^2  -> order 1 fails -> order 2 (quadratic [3,-3,1,0]) wins
    cubic v=0.05t^3 -> orders 1,2 fail -> order 3 (cubic [4,-6,4,-1]) wins  <-- generated, never hand-listed

Every decision is a graph Rule (generate-ladder, measure, gap-mint, search-escalate, gate-keep). The host only
ingests the value and beats master_tick;tick; it does NOT enumerate the candidates -- the agent does.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_enumerate_and_search.py
"""
from __future__ import annotations

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
WINDOW = 5.0
MAX_ORDER = 5.0
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


# GENERATE-LADDER: from each candidate of order k (< MAX) with no successor yet, MINT order k+1 via the
# finite-difference recurrence on the coefficients -- the agent builds its own candidate space, graph-native.
GENERATE_LADDER = {
    "id": "__gen_ladder", "name": "__gen_ladder",
    "match": [["lib", "has_cand", "c"]],
    "where": _And(_Gt(_L(MAX_ORDER), A("c", "order")), _Eq(A("c", "has_next"), _L(0.0))),
    "effects": [
        ["add_node", "nc", "Candidate", {
            "order": {"__term__": _Plus(A("c", "order"), _L(1.0))},
            "c0": {"__term__": _Plus(A("c", "c0"), _L(1.0))},
            "c1": {"__term__": _Minus(A("c", "c1"), A("c", "c0"))},
            "c2": {"__term__": _Minus(A("c", "c2"), A("c", "c1"))},
            "c3": {"__term__": _Minus(A("c", "c3"), A("c", "c2"))},
            "has_next": 0.0}],
        ["add_edge", "lib", "has_cand", "nc"],
        ["set_attr", "c", "has_next", 1.0]]}

# MEASURE: predictive accuracy = 1/(1+|value-pred|); banks a MeasuredCapability + a sustained-shortfall streak.
ABSDIFF = _Max(_Minus(A("o", "value"), A("o", "pred")), _Minus(A("o", "pred"), A("o", "value")))
MEASURED = _Div(_L(1.0), _Plus(_L(1.0), ABSDIFF))
MEASURE_RULE = {
    "id": "measure_enum", "name": "measure_enum",
    "match": [["h", "es_pred", "o"]],
    "where": _Gt(A("o", "frame"), A("o", "mframe")),
    "effects": [
        ["add_node", "mc", MEASURED_TYPE, {
            "is_measured": 1.0, "measured": {"__term__": MEASURED}, "target": TARGET, "synth_pending": 1,
            "cap_sig": KEY, "capability_keys": KEY, "metric": "predictive_accuracy",
            "origin": "jabberwock:enumerate_search", "composed_by": "agent"}],
        ["add_edge", "mc", "mc_self", "mc"],
        ["set_attr", "o", "last_measured", {"__term__": MEASURED}],
        ["set_attr", "o", "miss_streak", {"__term__": _IfThenElse(
            _Gt(_L(TARGET), MEASURED), _Plus(A("o", "miss_streak"), _L(1.0)), _L(0.0))}],
        ["set_attr", "o", "mframe", {"__term__": A("o", "frame")}]]}

# PREDICT: parameterised by the active coefficients on o (set by the search). pred = c0*v + c1*prev + c2*prev2
# + c3*prev3, then roll history. The search installs a candidate by copying its coeffs onto o.
PREDICT_RULE = {
    "id": "predict_enum", "name": "predict_enum",
    "match": [["h", "es_pred", "o"]],
    "where": _And(_Eq(A("o", "mframe"), A("o", "frame")), _Gt(A("o", "frame"), A("o", "pframe"))),
    "effects": [
        ["set_attr", "o", "pred", {"__term__": _Plus(
            _Times(A("o", "c0"), A("o", "value")), _Times(A("o", "c1"), A("o", "prev")),
            _Times(A("o", "c2"), A("o", "prev2")), _Times(A("o", "c3"), A("o", "prev3")))}],
        ["set_attr", "o", "prev3", {"__term__": A("o", "prev2")}],
        ["set_attr", "o", "prev2", {"__term__": A("o", "prev")}],
        ["set_attr", "o", "prev", {"__term__": A("o", "value")}],
        ["set_attr", "o", "pframe", {"__term__": A("o", "frame")}]]}

# SEARCH-ESCALATE: on a sustained gap with no active test, install the next order (order == cur_order+1) by
# copying its generated coefficients onto o; open a measure window.
SEARCH = {
    "id": "__search_escalate", "name": "__search_escalate",
    "match": [["h", "es_pred", "o"], ["lib", "has_cand", "cand"]],
    "where": _And(_Gt(A("o", "miss_streak"), _L(2.5)), _Eq(A("o", "solved"), _L(0.0)),
                  _Gt(A("o", "frame"), A("o", "test_until")),
                  _Eq(A("cand", "order"), _Plus(A("o", "cur_order"), _L(1.0)))),
    "effects": [
        ["set_attr", "o", "c0", {"__term__": A("cand", "c0")}],
        ["set_attr", "o", "c1", {"__term__": A("cand", "c1")}],
        ["set_attr", "o", "c2", {"__term__": A("cand", "c2")}],
        ["set_attr", "o", "c3", {"__term__": A("cand", "c3")}],
        ["set_attr", "o", "cur_order", {"__term__": A("cand", "order")}],
        ["set_attr", "o", "trying", {"__term__": A("cand", "order")}],
        ["set_attr", "o", "test_until", {"__term__": _Plus(A("o", "frame"), _L(WINDOW))}]]}

# GATE: at the window end, KEEP if the agent's own measure cleared target; else leave unsolved -> escalate.
GATE = {
    "id": "__gate", "name": "__gate",
    "match": [["h", "es_pred", "o"]],
    "where": _And(_Eq(A("o", "solved"), _L(0.0)), _Eq(A("o", "frame"), A("o", "test_until")),
                  _Gt(A("o", "last_measured"), _L(TARGET))),
    "effects": [["set_attr", "o", "solved", 1.0], ["set_attr", "o", "kept_order", {"__term__": A("o", "trying")}]]}


def run(regime: str, steps=80):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    install_builtinsufficient_gap_rule(agent.s)

    o = agent.s.add_node("Observable", {"name": regime, "value": 0.0, "pred": 0.0, "prev": 0.0, "prev2": 0.0,
                                        "prev3": 0.0, "frame": 0.0, "mframe": -1.0, "pframe": -1.0,
                                        "miss_streak": 0.0, "cur_order": 0.0, "trying": 0.0, "test_until": 0.0,
                                        "solved": 0.0, "kept_order": -1.0, "c0": 1.0, "c1": 0.0, "c2": 0.0, "c3": 0.0})
    hub = agent.s.add_node("ObsHub", {"is_hub": 1.0})
    agent.inner.add_edge_unchecked(hub, "es_pred", o)
    # the SINGLE seed of the candidate ladder (order 0 = persistence); the agent generates the rest.
    seed = agent.s.add_node("Candidate", {"order": 0.0, "c0": 1.0, "c1": 0.0, "c2": 0.0, "c3": 0.0, "has_next": 0.0})
    lib = agent.s.add_node("CandLib", {"is_lib": 1.0})
    agent.inner.add_edge_unchecked(lib, "has_cand", seed)

    for r in (GENERATE_LADDER, MEASURE_RULE, PREDICT_RULE, SEARCH, GATE):
        agent.inner.add_rule(r)

    tried = []
    last_try = 0.0
    for i in range(1, steps + 1):
        v = {"ramp": 0.3 * i, "quad": 0.1 * i * i, "cubic": 0.05 * i ** 3}[regime]
        agent.s.set_attr(o, "value", float(round(v, 5)))
        agent.s.set_attr(o, "frame", float(i))
        agent.master_tick()
        agent.tick()
        oa = agent.s.node(o)["attrs"]
        if oa.get("trying") and oa.get("trying") != last_try:
            last_try = oa.get("trying")
            tried.append(int(last_try))
        if oa.get("solved") == 1.0:
            break
    oa = agent.s.node(o)["attrs"]
    ladder = sorted(int(agent.s.node(n)["attrs"]["order"]) for n in agent.s.nodes("Candidate"))
    coeffs_by_order = {int(agent.s.node(n)["attrs"]["order"]):
                       [agent.s.node(n)["attrs"][k] for k in ("c0", "c1", "c2", "c3")]
                       for n in agent.s.nodes("Candidate")}
    return int(oa.get("kept_order") or -1), oa.get("last_measured"), tried, ladder, coeffs_by_order


def main():
    print(SEP)
    print("AUTONOMY — the agent GENERATES its own predictor ladder graph-natively, then searches it (host lists nothing).")
    print(SEP)

    results = {}
    shown_ladder = False
    for regime in ("ramp", "quad", "cubic"):
        kept, lm, tried, ladder, coeffs = run(regime)
        if not shown_ladder:
            print(f"\n  the agent generated the candidate ladder from ONE seed (order 0): orders {ladder}")
            for k in sorted(coeffs):
                print(f"      order {k}: coeffs [{', '.join(f'{c:g}' for c in coeffs[k])}]")
            shown_ladder = True
        print(f"\n  world '{regime}': search escalated through orders {tried}  ->  KEPT order {kept} (measure {lm:.3f})")
        results[regime] = kept

    ok = (results["ramp"] == 1 and results["quad"] == 2 and results["cubic"] == 3)
    print("\n" + SEP)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent built its OWN search space (the finite-difference ladder, unrolled by a")
    print(f"  graph recurrence from a single seed -- the host enumerated nothing), then searched it: each world's")
    print(f"  surprise drove escalation up the order ladder until the agent's own measure cleared target -- order 1")
    print(f"  for the ramp, 2 for the quadratic, 3 for the cubic (coeffs [4,-6,4,-1] it GENERATED, never hand-listed).")
    print(f"  The compose step now generates-and-searches its own space: the agent finds the model, and the space.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
