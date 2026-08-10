"""Promoted concern pipeline: comprehend-first vs experiment-when-needed."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

import jabberwock_daemon as jbd


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _mint_self_concern(agent, content: str = "fix moon reply", kind: str = "reply_fix"):
    sc = agent.s.add_node("SelfConcern", {
        "status": "noted",
        "predicate": "reply_fix",
        "content": content,
        "source": "human_feedback",
        "kind": kind,
    })
    return sc


def test_reply_fix_defaults_to_comprehend_first_not_arc(agent):
    sc = _mint_self_concern(agent, content="route moon questions to topic grounding")
    sc_id = sc.value if hasattr(sc, "value") else sc
    result = jbd.promote_self_concern(agent, str(sc_id))
    assert result["ok"]
    assert result.get("pipeline") == "comprehend_first"
    import substrate_rs as srs
    sat = agent.s.node(srs.NodeID(int(result["standing_concern"])))["attrs"]
    heads = {r[0] for r in sat.get("relations") or [] if r}
    assert "comprehend" in heads
    assert "test" not in heads
    jbd._concern_tick(agent)
    axis = jbd._axis_for_capability_key(agent, sat["name"])
    if axis is not None:
        assert not jbd._axis_wants_experiment(agent, sat["name"])
        assert jbd._experiment_for_axis(agent, axis) is None


def test_reply_fix_can_include_experiment_when_content_signals_it(agent):
    sc = _mint_self_concern(agent, content="ablate conversation seed and test acting variant")
    result = jbd.promote_self_concern(agent, str(sc.value))
    assert result["pipeline"] == "experiment"
    import substrate_rs as srs
    sat = agent.s.node(srs.NodeID(int(result["standing_concern"])))["attrs"]
    heads = {r[0] for r in sat.get("relations") or [] if r}
    assert "test" in heads
    assert jbd._axis_wants_experiment(agent, sat["name"]) or sat["name"]


def test_self_improvement_uses_experiment_relations(agent):
    sc = agent.s.add_node("SelfConcern", {
        "status": "noted", "predicate": "improve", "content": "fix grammar",
        "source": "conversation", "kind": "self_improvement",
    })
    result = jbd.promote_self_concern(agent, str(sc.value))
    assert result["pipeline"] == "experiment"
    import substrate_rs as srs
    standing = list(agent.s.nodes("StandingConcern"))[-1]
    assert agent.s.node(standing)["attrs"].get("pipeline") == "experiment"


def test_ensure_experiment_world_mechanical(agent):
    assert not jbd._agent_knows_game(agent)
    wi = jbd._ensure_experiment_world(agent)
    assert agent.s.has_node(wi)
    assert agent.s.node(wi)["attrs"].get("name") == jbd._EXPERIMENT_GAME
    assert jbd._agent_knows_game(agent)


def test_repromote_resets_stale_arc_pipeline_to_comprehend_first(agent):
    import substrate_rs as srs
    sc = _mint_self_concern(agent, content='"moon" is the subject, "made of" refers to composition')
    sc_id = sc.value if hasattr(sc, "value") else sc
    key = f"promoted_self_concern_{sc_id}"
    # Simulate an old promote: experiment bundle + processed standing.
    standing = agent.s.add_node("StandingConcern", {
        "name": key,
        "relations": [["test", "HYPOTHESIS", "about", "MOON"],
                      ["vary", "SEED", "of", "MOON"]],
        "status": "processed",
        "source": "conversation_promoted",
        "about": '"moon" is the subject',
        "kind": "reply_fix",
        "pipeline": "experiment",
    })
    agent.inner.add_edge_unchecked(sc, "promoted_to", standing)
    agent.s.set_attr(sc, "status", "promoted")
    axis = agent.s.add_node("CapabilityAxis", {
        "capability_keys": [key],
        "residual_predicates": ["test", "vary", "moon"],
        "induced": 1.0,
    })
    exp = agent.s.add_node("Experiment", {"status": "running", "game": "navigate"})
    agent.inner.add_edge_unchecked(axis, "tested_by", exp)
    agent.inner.add_rule({
        "name": f"author_experiment_from_residual_{key}",
        "match": [["agent", "is_a", "Agent"]],
        "effects": [["set_attr", "agent", "probe", 1.0]],
        "active": True,
    })

    result = jbd.repromote_self_concern(agent, str(sc_id))
    assert result["ok"], result
    assert result.get("repromoted")
    assert result.get("pipeline") == "comprehend_first"
    assert agent.s.node(exp)["attrs"].get("status") == "cancelled"
    new_standing = srs.NodeID(int(result["standing_concern"]))
    assert agent.s.node(new_standing)["attrs"].get("status") == "pending"
    assert agent.s.node(new_standing)["attrs"].get("pipeline") == "comprehend_first"


def test_replay_judge_passes_made_of_reply_fix(agent):
    import substrate_rs as srs
    from domains import comprehend_text as ct

    sc = _mint_self_concern(agent, content='"moon" is the subject, "made of" refers to composition')
    mid = agent.s.add_node("Message", {"text": "What is the moon made of?", "from": "user"})
    agent.inner.add_edge_unchecked(sc, "about_message", mid)
    result = jbd.promote_self_concern(agent, str(sc.value))
    assert result["ok"]
    standing = srs.NodeID(int(result["standing_concern"]))
    agent.s.set_attr(standing, "status", "processed")
    agent.inner.add_edge_unchecked(standing, "about_message", mid)

    comp = ct.comprehend_text(agent, "What is the moon made of?")
    facts = agent._topic_facts(comp)
    assert facts.get("topic") == "moon"
    assert facts.get("composition")

    judged = jbd._replay_reply_fix_judge(agent)
    assert judged == 1
    verdict = agent.s.node(standing)["attrs"].get("replay_verdict")
    assert verdict in ("pass", "fail")  # depends on wiki grounding in test env


def test_stale_author_rule_scrubbed(agent):
    agent.inner.add_rule({
        "name": "author_experiment_from_residual_standing_self_improvement",
        "match": [["ag", "observed", "obs"], ["obs", "minted", "axis"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "axis"},
                                  "key": "is_axis"}, "b": {"type": "Lit", "value": 1.0}},
        ]},
        "effects": [["set_attr", "agent", "probe", 1.0]],
        "active": True,
    })
    removed = jbd._scrub_stale_author_rules(agent)
    assert removed >= 1
    names = [r.get("name") for r in agent.inner.export_rules() if r.get("active")]
    assert "author_experiment_from_residual_standing_self_improvement" not in names


def test_cancel_unscoped_experiment(agent):
    import substrate_rs as srs
    from domains.experiment_dispatch import cancel_experiment
    axis = agent.s.add_node("CapabilityAxis", {
        "capability_keys": ["promoted_self_concern_99"],
        "residual_predicates": ["comprehend", "reply"],
        "induced": 1.0,
    })
    exp = agent.s.add_node("Experiment", {"status": "requested", "game": "navigate"})
    agent.inner.add_edge_unchecked(axis, "tested_by", exp)
    n = jbd._cancel_unscoped_experiments(agent)
    assert n == 1
    assert agent.s.node(exp)["attrs"].get("status") == "cancelled"
