"""adoption_safety v1.1.0: no adoption on a verdict the agent itself overrode.

Reproduces the race measured in tranche 23 in-graph, on the production
conversation profile: the generic judge writes 'supported', the authored
mark_adopt_ready rule marks adopt_ready, and the speed judge
(self_optimisation.judge_performance_experiment_outcome) overrides the outcome
to 'refuted' in the same fixpoint. Before v1.1.0 perform_adoptions then
adopted it. Both directions are pinned: a supported experiment is still
adopt-ready and not denied, and an experiment with no outcome is untouched.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "evaluation", "substrate_capability")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.reflective_faculty as rf   # noqa: E402
import endemic_rsi_daemon_v1 as E         # noqa: E402


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}


def _judge(tag):
    rate = {"type": "Div", "a": A("run", "score"), "b": A("run", "frames")}
    out = {"type": "IfThenElse", "cond": {"type": "Gt", "a": rate, "b": L(0.0)}, "then": L("supported"),
           "other": L("refuted")}
    return {"name": "judge_experiment_outcome_" + tag, "match": [["exp", "produced", "run"]],
            "where": {"type": "And", "items": [
                Eq(A("run", "status"), L("done")),
                Not({"type": "Exists", "source": {"type": "Neighbours", "node": V("exp"), "edge_type": "analysed"},
                     "var_name": "_j", "predicate": L(True)})]},
            "effects": [["set_attr", "exp", "outcome", {"__term__": out}], ["add_edge", "exp", "analysed", "run"],
                        ["set_attr", "exp", "conclusion_ready", True]]}


def _adopt(tag):
    # the byte-shape of the authored non-cue mark_adopt_ready_* rule
    return {"name": "mark_adopt_ready_" + tag, "match": [["exp", "has_delta", "delta"]],
            "where": {"type": "And", "items": [
                Eq(A("exp", "outcome"), L("supported")), Not(Eq(A("exp", "adopt_ready"), L(True))),
                Not(Eq(A("delta", "act_rule_varied"), L(""))), Not(Eq(A("delta", "act_rule_varied"), L(None)))]},
            "effects": [["set_attr", "exp", "adopt_ready", True]]}


@pytest.fixture(scope="module")
def agent():
    st = E.boot(True, promote=False)
    a = st.adapter
    tag = "ovr_probe"
    a.inner.add_rule(_judge(tag))
    a.inner.add_rule(_adopt(tag))
    return a


def _experiment(a, *, avg_turn_ms, baseline_ms, score=1, perf=True):
    exp = a.s.add_node("Experiment", {"status": "done", "game": "conversation", "axis_tag": "ovr_probe"})
    attrs = {"act_rule_varied": "reply_self_identity", "add_rules": "[]", "remove_rules": "[]"}
    if perf:
        attrs.update({"performance_objective": 1.0, "baseline_avg_turn_ms": baseline_ms})
    delta = a.s.add_node("SeedDelta", attrs)
    a.inner.add_edge_unchecked(exp, "has_delta", delta)
    # production order (P5c): the experiment is minted (its witness declared)
    # before its child runs; the child's report is ingested afterwards
    a.inner.run_rules()
    a.s.set_attr(exp, "regressions", 0)
    a.s.set_attr(exp, "avg_turn_ms", avg_turn_ms)
    run = a.s.add_node("Run", {"status": "done", "score": score, "frames": 1})
    a.inner.add_edge_unchecked(exp, "produced", run)
    a.inner.run_rules()
    return exp


def test_overridden_supported_verdict_is_denied_and_not_adopted(agent):
    a = agent
    live = {r["name"] for r in a.inner.export_rules() if r.get("active", True)}
    # self_optimisation v1.7.0 (plan P3b): the speed judge is the declared latency witness
    assert {"adopt_denied_on_overridden_verdict", "declare_witness_performance", "judge_declared_witness_outcome"} <= live
    exp = _experiment(a, avg_turn_ms=320.0, baseline_ms=70.0)   # slower than baseline: the speed judge refutes
    at = a.s.node(exp)["attrs"]
    assert at.get("adopt_ready") is True, "the generic verdict marked it adopt-ready (the race)"
    assert at.get("outcome") == "refuted", "the speed judge overrode it"
    assert at.get("adopt_denied") is True and "overrode" in at.get("adopt_denied_reason", "")
    rf.perform_adoptions(a)
    assert not a.s.node(exp)["attrs"].get("adopted")
    assert "reply_self_identity" in {r["name"] for r in a.inner.export_rules() if r.get("active", True)}


def test_supported_final_verdict_is_not_denied(agent):
    exp = _experiment(agent, avg_turn_ms=50.0, baseline_ms=70.0)    # faster: the speed judge supports
    at = agent.s.node(exp)["attrs"]
    assert at.get("outcome") == "supported" and at.get("adopt_ready") is True
    assert not at.get("adopt_denied")


def test_experiment_without_outcome_is_untouched(agent):
    a = agent
    exp = a.s.add_node("Experiment", {"status": "done", "adopt_ready": True})
    d = a.s.add_node("SeedDelta", {"act_rule_varied": "x"})
    a.inner.add_edge_unchecked(exp, "has_delta", d)
    a.inner.run_rules()
    assert not a.s.node(exp)["attrs"].get("adopt_denied")


def test_veto_rule_round_trips_through_the_engine(agent):
    import json
    import jabberwock_daemon as jd
    seed = json.load(open(os.path.join(ROOT, "seeds", "adoption_safety.json")))
    file_rule = next(r for r in seed["rules"] if r["name"] == "adopt_denied_on_overridden_verdict")
    live = [r for r in agent.inner.export_rules()
            if r.get("active", True) and r.get("name") == "adopt_denied_on_overridden_verdict"]
    assert len(live) == 1
    assert jd._canon_rule_body(file_rule) == jd._canon_rule_body(live[0])
