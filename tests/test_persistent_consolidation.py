"""Native persistent consolidation and resume tests for P25.03."""
from __future__ import annotations

from evaluation.process_mastery.learning_memory_budget import (
    apply_native_evictions,
    charge_persistent_summaries,
)
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import ThermalWorld, WorldReceipt
from substrate.seed_loader import manifest_for


def _learner(owner="p25-consolidation"):
    learner = NativeTargetLearner(owner_id=owner)
    learner.s._inner.load_seed_manifest(manifest_for("learning_memory_budget"), learner.ag)
    learner.s._inner.load_seed_manifest(manifest_for("persistent_consolidation"), learner.ag)
    consolidation = learner.s.nodes("PersistentConsolidationPolicy")[0]
    memory = learner.s.nodes("LearningMemoryBudgetPolicy")[0]
    learner.s.set_attr(consolidation, "enabled", 1.0)
    learner.s.set_attr(memory, "enabled", 1.0)
    return learner, consolidation, memory


def _learn_two(learner):
    world = ThermalWorld(object_ids=("train-a", "train-b"))
    learner.observe_world_receipt(world.apply("train-a", "warm"))
    learner.observe_world_receipt(world.apply("train-b", "warm"))
    learner.settle()
    assert len(learner.hypotheses()) == 1


def _work(learner, work_id="cycle-1", *, interrupted=False):
    work = learner.s.add_node("PersistentConsolidationWork", {
        "work_id": work_id, "status": "requested",
        "interrupted": bool(interrupted), "foreground_demand": False,
    })
    learner.s.add_edge(learner.ag, "has_persistent_consolidation_work", work, {})
    return work


def _run(learner):
    for _ in range(10):
        if learner.s.tick(2000) == 0:
            break


def test_consolidation_changes_persistent_learned_state():
    learner, _, memory = _learner()
    _learn_two(learner)
    work = _work(learner)
    _run(learner)
    measured = charge_persistent_summaries(learner.agent)
    _run(learner)

    summaries = learner.s.nodes("PersistentLearnedSummary")
    assert len(summaries) == 1
    summary = learner.s.node(summaries[0])["attrs"]
    assert summary["status"] == "verified"
    assert summary["witness_event_1"] != summary["witness_event_2"]
    assert summary["serialized_bytes"] == measured[0]["charged_bytes"]
    assert summary["serialized_bytes"] > measured[0]["payload_bytes"]
    assert learner.hypotheses()[0]["consolidation_verified"] is True
    assert learner.s.node(memory)["attrs"]["resident_bytes"] == summary["serialized_bytes"]
    assert learner.s.node(work)["attrs"]["status"] == "completed"

    _run(learner)
    assert len(learner.s.nodes("PersistentLearnedSummary")) == 1


def test_summary_used_after_source_eviction():
    learner, _, memory = _learner("p25-summary-after-eviction")
    _learn_two(learner)
    _run_work = _work(learner)
    _run(learner)
    charge = charge_persistent_summaries(learner.agent)[0]["charged_bytes"]
    _run(learner)
    source_nodes = (learner.s.nodes("TransitionObservation") +
                    learner.s.nodes("TransitionActionReceipt") +
                    learner.s.nodes("TransitionOutcomeReceipt") +
                    [node for node in learner.s.nodes("ProcessInductionHypothesis")
                     if learner.s.node(node)["attrs"].get("status") == "consolidated_source"])

    # The memory policy is the native victim selector; this adapter only
    # deletes the evidence nodes named by that decision.
    learner.s.set_attr(memory, "capacity_bytes", float(charge + 119))
    target = learner.s.add_node("LearningMemoryItem", {
        "item_id": "acquired-target-evidence", "content_class": "target_evidence",
        "availability": "pending_admission", "charged_bytes": 80.0,
        "admission_epoch": 1.0, "retention_priority": 1.0, "payload": "two source receipts",
        "protection_class": "ordinary",
    })
    learner.s.add_edge(learner.ag, "has_learning_memory_item", target, {})
    for node in source_nodes:
        wrapper = learner.s.add_node("LearningMemoryGraphNode", {
            "graph_node_id": int(node.value), "content_type": learner.s.node(node)["type"],
        })
        learner.s.add_edge(target, "has_learning_memory_graph_node", wrapper, {})
    other = learner.s.add_node("LearningMemoryItem", {
        "item_id": "interference-content", "content_class": "interference",
        "availability": "pending_admission", "charged_bytes": 40.0,
        "admission_epoch": 2.0, "retention_priority": 2.0, "payload": "unrelated",
        "protection_class": "ordinary",
    })
    learner.s.add_edge(learner.ag, "has_learning_memory_item", other, {})
    _run(learner)

    assert learner.s.node(target)["attrs"]["availability"] == "evicted"
    assert apply_native_evictions(learner.agent) == ["acquired-target-evidence"]
    assert learner.s.nodes("TransitionObservation") == []
    assert len(learner.hypotheses()) == 1
    assert learner.hypotheses()[0]["consolidation_verified"] is True
    result = learner.predict(query_id="after-source-eviction", action_kind="warm",
                             object_type="ThermalSample", feature_key="temperature",
                             before_value="cold", object_id="delayed-object")
    assert result is not None and result["expected_after_value"] == "warm"
    assert len(learner.s.nodes("PersistentLearnedSummary")) == 1


def test_summary_does_not_drop_counterexamples():
    learner, _, _ = _learner("p25-counterexample")
    _learn_two(learner)
    contrary = WorldReceipt("contrary:1", "counter-object", "ThermalSample", "warm",
                            "temperature", "cold", "cold", "observed", True, 1)
    learner.observe_world_receipt(contrary)
    learner.settle()
    assert learner.hypotheses()[0]["counterexample_count"] == 1.0
    assert learner.hypotheses()[0]["status"] == "disputed"

    _work(learner)
    _run(learner)
    assert learner.s.nodes("PersistentLearnedSummary") == []
    assert learner.hypotheses()[0]["counterexample_count"] == 1.0


def test_interrupt_resume_once():
    learner, _, memory = _learner("p25-resume")
    _learn_two(learner)
    work = _work(learner, interrupted=True)
    _run(learner)
    assert learner.s.nodes("PersistentLearnedSummary") == []
    assert learner.s.node(work)["attrs"]["status"] == "requested"
    assert learner.s.node(memory)["attrs"]["resident_bytes"] == 0.0

    learner.s.set_attr(work, "interrupted", False)
    _run(learner)
    charge = charge_persistent_summaries(learner.agent)[0]["charged_bytes"]
    _run(learner)
    assert len(learner.s.nodes("PersistentLearnedSummary")) == 1
    assert learner.s.node(work)["attrs"]["status"] == "completed"
    assert learner.s.nodes("LearningMemoryItem")[0]
    assert learner.s.node(memory)["attrs"]["resident_bytes"] == charge
    learner.s.set_attr(work, "interrupted", False)
    _run(learner)
    assert len(learner.s.nodes("PersistentLearnedSummary")) == 1
    assert learner.s.node(memory)["attrs"]["resident_bytes"] == charge
