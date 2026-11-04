"""Native policy and charged-store gates for P25.02."""
from __future__ import annotations

import json
from pathlib import Path

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.learning_memory_budget import apply_native_evictions
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import ThermalWorld
from scripts.gen_learning_memory_budget_seed import OUT, build_seed
from substrate.seed_loader import manifest_for


ROOT = Path(__file__).resolve().parents[1]


def _agent(*, capacity=100.0):
    agent = Agent(extra_seeds=("learning_memory_budget",), track_i=False,
                  profile="p25-learning-memory-budget-test")
    policy = agent.s.nodes("LearningMemoryBudgetPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    agent.s.set_attr(policy, "capacity_bytes", float(capacity))
    return agent, policy


def _item(agent, *, item_id, size, priority, content_class="learned_effect",
          payload="answer-bearing-effect", protection_class="ordinary"):
    item = agent.s.add_node("LearningMemoryItem", {
        "item_id": item_id, "content_class": content_class,
        "availability": "pending_admission", "charged_bytes": float(size),
        "admission_epoch": float(priority), "retention_priority": float(priority), "payload": payload,
        "protection_class": protection_class,
    })
    agent.s.add_edge(agent.ag, "has_learning_memory_item", item, {})
    return item


def _run(agent):
    # Execute native graph rules, not Python admission/eviction decisions.
    for _ in range(8):
        if agent.s.tick(1000) == 0:
            break


def test_evicted_effect_cannot_be_read_via_hypothesis():
    learner = NativeTargetLearner(owner_id="p25-eviction-hypothesis")
    learner.s._inner.load_seed_manifest(manifest_for("learning_memory_budget"), learner.ag)
    policy = learner.s.nodes("LearningMemoryBudgetPolicy")[0]
    learner.s.set_attr(policy, "enabled", 1.0)
    learner.s.set_attr(policy, "capacity_bytes", 100.0)
    world = ThermalWorld(object_ids=("learn-a", "learn-b"))
    for object_id in ("learn-a", "learn-b"):
        learner.observe_world_receipt(world.apply(object_id, "warm"))
    learner.settle()
    assert len(learner.hypotheses()) == 1

    low = learner.s.add_node("LearningMemoryItem", {
        "item_id": "target-effect", "content_class": "target_effect",
        "availability": "pending_admission", "charged_bytes": 80.0,
        "admission_epoch": 1.0, "retention_priority": 1.0, "payload": "effect-evidence",
        "protection_class": "ordinary",
    })
    learner.s.add_edge(learner.ag, "has_learning_memory_item", low, {})
    source_nodes = (learner.s.nodes("TransitionObservation") +
                    learner.s.nodes("TransitionActionReceipt") +
                    learner.s.nodes("TransitionOutcomeReceipt") +
                    learner.s.nodes("ProcessInductionHypothesis"))
    for node in source_nodes:
        wrapper = learner.s.add_node("LearningMemoryGraphNode", {
            "graph_node_id": int(node.value),
            "content_type": learner.s.node(node)["type"],
        })
        learner.s.add_edge(low, "has_learning_memory_graph_node", wrapper, {})
    high = learner.s.add_node("LearningMemoryItem", {
        "item_id": "other-content", "content_class": "other_learned_content",
        "availability": "pending_admission", "charged_bytes": 40.0,
        "admission_epoch": 2.0, "retention_priority": 2.0, "payload": "other-content",
        "protection_class": "ordinary",
    })
    learner.s.add_edge(learner.ag, "has_learning_memory_item", high, {})
    _run(learner.agent)

    assert learner.s.node(low)["attrs"]["availability"] == "evicted"
    assert learner.s.node(low)["attrs"]["payload"] is None
    assert apply_native_evictions(learner.agent) == ["target-effect"]
    assert learner.hypotheses() == []
    for node_type in ("TransitionObservation", "TransitionActionReceipt",
                      "TransitionOutcomeReceipt", "ProcessInductionHypothesis"):
        assert learner.s.nodes(node_type) == []
    assert learner.s.node(high)["attrs"]["availability"] == "resident"


def test_all_arms_same_protection_policy():
    policy = json.loads(OUT.read_text())
    assert policy["nodes"][0]["attrs"]["protection_policy"] == \
        "uniform_content_no_target_exemption"
    agent, _ = _agent(capacity=200)
    source = _item(agent, item_id="source-receipt", size=40, priority=1,
                   content_class="source_receipt")
    target = _item(agent, item_id="target-receipt", size=40, priority=1,
                   content_class="target_receipt")
    _run(agent)
    for item in (source, target):
        attrs = agent.s.node(item)["attrs"]
        assert attrs["availability"] == "resident"
        assert attrs["protection_class"] == "ordinary"


def test_rebuild_cost_charged():
    agent, policy = _agent()
    agent.s.set_attr(policy, "durable_read_bytes", 0.0)
    read = agent.s.add_node("DurableLearningRead", {
        "read_id": "rebuild-1", "status": "requested", "rebuild_bytes": 73.0,
        "availability": "unavailable",
    })
    agent.s.add_edge(agent.ag, "has_durable_learning_read", read, {})
    _run(agent)
    assert agent.s.node(policy)["attrs"]["durable_read_bytes"] == 73.0
    assert agent.s.node(read)["attrs"]["status"] == "charged"
    assert agent.s.node(read)["attrs"]["availability"] == "pending_capacity_admission"


def test_stale_cached_prediction_invalidated():
    agent, _ = _agent(capacity=60)
    item = _item(agent, item_id="source-low", size=40, priority=1)
    cache = agent.s.add_node("LearningMemoryCache", {
        "availability": "resident", "prediction": "warm",
        "rebuild_from_source": True,
    })
    agent.s.add_edge(item, "has_learning_memory_cache", cache, {})
    _item(agent, item_id="other-high", size=40, priority=2)
    _run(agent)
    assert agent.s.node(item)["attrs"]["availability"] == "evicted"
    assert agent.s.node(cache)["attrs"]["availability"] == "stale"
    assert agent.s.node(cache)["attrs"]["prediction"] is None
    assert agent.s.node(cache)["attrs"]["rebuild_from_source"] is False


def test_checkpoint_retains_capacity_state():
    # Capacity and accounting state live on an ordinary graph node, so the
    # substrate graph checkpoint serializer preserves them.
    import pytest
    native = pytest.importorskip("substrate_rs._native")
    agent, policy = _agent(capacity=321)
    agent.s.set_attr(policy, "resident_bytes", 123.0)
    restored = native.Substrate()
    restored.graph_from_dict(agent.s.graph_to_dict())
    restored_policies = restored.nodes("LearningMemoryBudgetPolicy")
    assert len(restored_policies) == 1
    attrs = restored.node(restored_policies[0])["attrs"]
    assert attrs["capacity_bytes"] == 321.0
    assert attrs["resident_bytes"] == 123.0


def test_generator_output_is_current_and_disabled_by_default():
    assert build_seed()["id"] == "learning_memory_budget"
    assert json.loads(OUT.read_text()) == build_seed()
    assert build_seed()["nodes"][0]["attrs"]["enabled"] == 0.0
