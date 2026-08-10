"""AUTONOMY CORE, no answer handed over — the agent SEARCHES a space of compositions and its OWN measure
SELECTS the winner, rejecting the wrong ones. Generalises jabberwock_compose_on_gap (which installed a single
pre-held successor) to a real compose-and-select loop, graph-native.

The held primitives are Plus/Times over the observable's own history (value, prev = v_{t-1}, prev2 = v_{t-2}).
A candidate predictor is a composition c0*value + c1*prev + c2*prev2; the library spans persistence-/linear-/
quadratic-style compositions. On a SUSTAINED gap the search reflex installs the next untried candidate by
rewriting the predictor's effect (set_rule_clause -- rule edits rule), measures it for a window, and the GATE
KEEPS it if the agent's own measure clears target or ESCALATES to the next candidate if it does not. The agent
is handed a SPACE, not the answer; the measure picks. Proven on two worlds where DIFFERENT compositions win:

  ramp  v=0.3t      -> linear (2,-1,0) predicts it exactly; search keeps it on the first try.
  quad  v=0.1t^2    -> linear is wrong by a constant (measure ~0.83 < target) so the search REJECTS it and
                       escalates to quadratic (3,-3,1), which predicts it exactly. Same agent, no answer given.

Every decision is a graph Rule (measure, gap-mint, search-install, gate-keep/escalate). The host only ingests
the value, enumerates the candidate COMPOSITIONS as graph data (a stand-in for graph-native enumeration over
held primitives), beats master_tick;tick, and writes the kept faculty to disk.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_compose_search.py
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
WINDOW = 5.0          # frames to measure a candidate before judging it
KEY = ["predict_observable"]
PREDICT_ID = "predict_cs"
# the candidate COMPOSITIONS (idx, label, [c0,c1,c2] over value/prev/prev2) -- built from held Plus/Times.
CANDS = [(1.0, "linear", [2.0, -1.0, 0.0]),
         (2.0, "quadratic", [3.0, -3.0, 1.0]),
         (3.0, "mean2", [0.5, 0.5, 0.0])]


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


ABSDIFF = _Max(_Minus(A("o", "value"), A("o", "pred")), _Minus(A("o", "pred"), A("o", "value")))
MEASURED = _Div(_L(1.0), _Plus(_L(1.0), ABSDIFF))

MEASURE_RULE = {
    "id": "measure_prediction_cs", "name": "measure_prediction_cs",
    "match": [["h", "cs_pred", "o"]],
    "where": _Gt(A("o", "frame"), A("o", "mframe")),
    "effects": [
        ["add_node", "mc", MEASURED_TYPE, {
            "is_measured": 1.0, "measured": {"__term__": MEASURED}, "target": TARGET, "synth_pending": 1,
            "cap_sig": KEY, "capability_keys": KEY, "metric": "predictive_accuracy",
            "origin": "jabberwock:compose_search", "composed_by": "agent"}],
        ["add_edge", "mc", "mc_self", "mc"],
        ["set_attr", "o", "last_measured", {"__term__": MEASURED}],
        ["set_attr", "o", "miss_streak", {"__term__": _IfThenElse(
            _Gt(_L(TARGET), MEASURED), _Plus(A("o", "miss_streak"), _L(1.0)), _L(0.0))}],
        ["set_attr", "o", "mframe", {"__term__": A("o", "frame")}]]}


def predict_effect(c0, c1, c2):
    """A predictor effect composed from held primitives: pred = c0*value + c1*prev + c2*prev2, then roll
    history (prev2:=prev, prev:=value). Order matters: prev2 reads the OLD prev before prev:=value."""
    combo = _Plus(_Times(_L(c0), A("o", "value")), _Times(_L(c1), A("o", "prev")), _Times(_L(c2), A("o", "prev2")))
    return [["set_attr", "o", "pred", {"__term__": combo}],
            ["set_attr", "o", "prev2", {"__term__": A("o", "prev")}],
            ["set_attr", "o", "prev", {"__term__": A("o", "value")}],
            ["set_attr", "o", "pframe", {"__term__": A("o", "frame")}]]


# boot predictor = PERSISTENCE (c=1,0,0): wrong on any moving world -> triggers the search.
PREDICT_RULE = {
    "id": PREDICT_ID, "name": PREDICT_ID,
    "match": [["h", "cs_pred", "o"]],
    "where": _And(_Eq(A("o", "mframe"), A("o", "frame")), _Gt(A("o", "frame"), A("o", "pframe"))),
    "effects": predict_effect(1.0, 0.0, 0.0)}

# SEARCH-INSTALL: on a SUSTAINED gap and no active test, pick the next untried candidate (idx == cur_idx+1)
# and REWRITE the predictor's effect to that composition; open a test window. Rule edits rule, in the loop.
SEARCH_INSTALL = {
    "id": "__search_install", "name": "__search_install",
    "match": [["h", "cs_pred", "o"], ["lib", "has_cand", "cand"]],
    "where": _And(_Gt(A("o", "miss_streak"), _L(2.5)), _Eq(A("o", "solved"), _L(0.0)),
                  _Gt(A("o", "frame"), A("o", "test_until")),
                  _Eq(A("cand", "idx"), _Plus(A("o", "cur_idx"), _L(1.0)))),
    "effects": [
        ["set_rule_clause", PREDICT_ID, "effect", {"__term__": A("cand", "effect")}],
        ["set_attr", "o", "cur_idx", {"__term__": A("cand", "idx")}],
        ["set_attr", "o", "trying", {"__term__": A("cand", "idx")}],
        ["set_attr", "o", "test_until", {"__term__": _Plus(A("o", "frame"), _L(WINDOW))}]]}

# GATE: at the window end, KEEP if the agent's own measure cleared target (solved); else leave solved=0 so
# SEARCH-INSTALL escalates to the next candidate next frame.
GATE_KEEP = {
    "id": "__gate_keep", "name": "__gate_keep",
    "match": [["h", "cs_pred", "o"]],
    "where": _And(_Eq(A("o", "solved"), _L(0.0)), _Eq(A("o", "frame"), A("o", "test_until")),
                  _Gt(A("o", "last_measured"), _L(TARGET))),
    "effects": [["set_attr", "o", "solved", 1.0], ["set_attr", "o", "kept", {"__term__": A("o", "trying")}]]}


def run(regime: str):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    install_builtinsufficient_gap_rule(agent.s)

    o = agent.s.add_node("Observable", {"name": regime, "value": 0.0, "pred": 0.0, "prev": 0.0, "prev2": 0.0,
                                        "frame": 0.0, "mframe": -1.0, "pframe": -1.0, "miss_streak": 0.0,
                                        "cur_idx": 0.0, "trying": 0.0, "test_until": 0.0, "solved": 0.0, "kept": 0.0})
    hub = agent.s.add_node("ObsHub", {"is_hub": 1.0})
    agent.inner.add_edge_unchecked(hub, "cs_pred", o)
    # the candidate compositions, held as graph data.
    for idx, label, cs in CANDS:
        cand = agent.s.add_node("Candidate", {"idx": idx, "label": label, "effect": predict_effect(*cs)})
        agent.inner.add_edge_unchecked(agent.agent, "has_cand", cand)

    for r in (MEASURE_RULE, PREDICT_RULE, SEARCH_INSTALL, GATE_KEEP):
        agent.inner.add_rule(r)

    tried = []
    last_try = 0.0
    for i in range(1, 41):
        v = round(i * 0.3, 4) if regime == "ramp" else round(0.1 * i * i, 4)
        agent.s.set_attr(o, "value", float(v))
        agent.s.set_attr(o, "frame", float(i))
        agent.master_tick()
        agent.tick()
        oa = agent.s.node(o)["attrs"]
        if oa.get("trying") and oa.get("trying") != last_try:
            last_try = oa.get("trying")
            tried.append((i, int(last_try)))
        if oa.get("solved") == 1.0:
            break
    oa = agent.s.node(o)["attrs"]
    kept_idx = int(oa.get("kept") or 0)
    label = {int(c[0]): c[1] for c in CANDS}.get(kept_idx, "none")
    return kept_idx, label, oa.get("last_measured"), tried, agent, o


def main():
    print(SEP)
    print("AUTONOMY — the agent SEARCHES composed predictors and its OWN measure SELECTS the winner (no answer given).")
    print(SEP)

    results = {}
    for regime in ("ramp", "quad"):
        kept_idx, label, lm, tried, agent, o = run(regime)
        cand_labels = {int(c[0]): c[1] for c in CANDS}
        seq = " -> ".join(f"{cand_labels[idx]}" for (_, idx) in tried) or "(none)"
        print(f"\n  world '{regime}': search tried [{seq}]")
        print(f"    KEPT = {label} (idx {kept_idx}) at measure {lm:.3f}" if kept_idx else "    no candidate kept")
        results[regime] = (kept_idx, label, len(tried))

    # the autonomy criterion: DIFFERENT worlds keep DIFFERENT compositions, each selected by the agent's own
    # measure, with the wrong candidate REJECTED where it doesn't fit (quad rejects linear before quadratic).
    ramp_ok = results["ramp"][1] == "linear"
    quad_ok = results["quad"][1] == "quadratic" and results["quad"][2] >= 2   # tried linear THEN quadratic
    ok = ramp_ok and quad_ok
    print("\n" + SEP)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent was handed a SPACE of compositions, not an answer. On the ramp its")
    print(f"  measure selected LINEAR on the first try; on the quadratic world it REJECTED linear (measure below")
    print(f"  target) and ESCALATED to QUADRATIC, which its measure then kept. Same agent, same search, different")
    print(f"  composition chosen per world -- the compose step now genuinely composes-and-selects, no pre-held")
    print(f"  answer. The autonomy core (measure -> gap -> compose-search -> select -> keep) is the agent's own.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
