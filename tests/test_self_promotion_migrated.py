"""SELF-PROMOTION and ROUTE CREDIT (tranche 20).

Pinned claims:
  * the agent requests promotion of its own oldest eligible noted concern,
    once per concern, within the policy budget, only when its own loop is idle;
  * a disabled policy promotes nothing (the pre-tranche-20 agent);
  * the self-promotion rule is itself protected loop machinery (tranche 19);
  * route credit is decision-equivalent with no history, and with history the
    route that worked for earlier verbs is tried first for a new verb.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.reflective_faculty as rf          # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate.boot_all import load_all_seeds     # noqa: E402


def _boot():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _policy(a):
    return next(iter(a.s.nodes("SelfPromotionPolicy")))


def _concerns(a, kind):
    return [n for n in a.s.nodes("SelfConcern") if a.s.node(n)["attrs"].get("kind") == kind]


@pytest.fixture(scope="module")
def agent():
    a = _boot()
    a.converse("Hello.", speech_act="greeting")
    a.converse("Bake the cake.", speech_act="request")
    a.converse("Decorate the house.", speech_act="request")
    a.inner.run_rules()
    return a


def test_the_agent_requests_its_own_promotion_once_when_idle(agent):
    a = agent
    req = [n for n in a.s.nodes("SelfConcern") if a.s.node(n)["attrs"].get("promote_requested") == 1.0]
    assert len(req) == 1, "exactly one self-promotion while idle"
    at = a.s.node(req[0])["attrs"]
    assert at["promoted_by"] == "self" and at["self_promote_attempted"] == 1
    assert at["kind"] in a.s.node(_policy(a))["attrs"]["eligible_kinds"]
    assert a.s.node(_policy(a))["attrs"]["promoted_count"] == 1
    # the oldest eligible noted concern is the one requested
    elig = sorted((n for n in a.s.nodes("SelfConcern")
                   if a.s.node(n)["attrs"].get("kind") in a.s.node(_policy(a))["attrs"]["eligible_kinds"]),
                  key=lambda n: int(n.value))
    assert req[0] == elig[0]
    # still requested-but-unexecuted: no second request (budget: one in flight)
    a.inner.run_rules()
    assert sum(1 for n in a.s.nodes("SelfConcern") if a.s.node(n)["attrs"].get("promote_requested") == 1.0) == 1


def test_the_steer_hook_executes_it_and_the_next_waits_for_idle(agent):
    import jabberwock_daemon as jd
    a = agent
    res = jd._steer_tick(a)
    assert res and res[0]["ok"]
    a.inner.run_rules()
    # a promoted StandingConcern is now pending: the loop is busy, nothing else is requested
    assert not [n for n in a.s.nodes("SelfConcern")
                if a.s.node(n)["attrs"].get("promote_requested") == 1.0
                and a.s.node(n)["attrs"].get("status") == "noted"]


def test_disabled_policy_promotes_nothing():
    a = _boot()
    a.s.set_attr(_policy(a), "enabled", 0)
    a.converse("Bake the cake.", speech_act="request")
    a.inner.run_rules()
    assert not [n for n in a.s.nodes("SelfConcern") if a.s.node(n)["attrs"].get("promote_requested") == 1.0]


def test_self_promotion_rule_is_protected_machinery(agent):
    rf._ensure_where_literal_rule_provenance(agent.s, agent.inner)
    rf._ensure_general_rule_provenance(agent.s, agent.inner)
    denied, why = rf._rule_denylisted(agent.s, "self_promote_noted_concern")
    assert denied and "machinery" in why


def test_route_credit_is_equivalent_without_history_and_learns_with_it():
    a = _boot()
    prog = rf._load_program(a.s, "cue_route_pick")
    op = next(n for n in a.s.nodes("VariationOp") if a.s.node(n)["attrs"].get("name") == "cue_set_edit")
    picks = {}
    for on in (0, 1):
        a.s.set_attr(op, "route_credit", on)
        picks[on] = [a.inner.evaluate(prog, {"verb": v, "chars": rf._char_bigrams(v)})
                     for v in ("bake", "decorate", "communicate", "spend")]
    assert picks[0] == picks[1], "no history: route credit must not change the pick"
    # history: three earlier verbs fixed by world_action, comprehend_text refuted for them
    for i, v in enumerate(("grow", "revolutionize", "admire")):
        for route, outcome in (("comprehend_text", "refuted"), ("world_action", "supported")):
            e = a.s.add_node("Experiment", {"game": "conversation", "status": "done", "outcome": outcome,
                                            "axis_tag": f"hist_{i}"})
            d = a.s.add_node("SeedDelta", {"cue_edit": 1.0, "cue_concept_added": v, "cue_route": route})
            a.inner.add_edge_unchecked(e, "has_delta", d)
    a.s.set_attr(op, "route_credit", 1)
    learned = [a.inner.evaluate(prog, {"verb": v, "chars": rf._char_bigrams(v)}) for v in ("bake", "spend")]
    assert learned == ["world_action", "world_action"], learned
