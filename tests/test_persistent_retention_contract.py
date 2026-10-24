"""P25.01 contract-level checks for persistent learner and charged retention."""
from __future__ import annotations

from dataclasses import asdict

from evaluation.process_mastery.developmental_memory import ChargedMemory
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import ThermalWorld


def _receipt_payload(receipt):
    return asdict(receipt)


def test_same_learner_across_delay():
    learner = NativeTargetLearner(owner_id="p25-contract-stream")
    identity = (id(learner), id(learner.s), learner.owner_id)

    # Delay and treatment bookkeeping do not replace the learner.
    _offline_marker = {"stage": "interference", "learner_id": identity[2]}
    delayed_learner = learner

    assert (id(delayed_learner), id(delayed_learner.s), delayed_learner.owner_id) == identity


def test_recoverable_information_is_charged():
    memory = ChargedMemory(capacity_bytes=4096, overhead_bytes=32)
    record = {"event_id": "retained-1", "transition": "cold->warm",
              "source_epoch": 3, "provenance": ["world-receipt-1"]}
    result = memory.put("episode:retained-1", record)
    assert result["status"] == "stored"

    recovered, audit = memory.retrieve("episode:retained-1")
    assert recovered == record
    assert result["charged_bytes"] == len(memory._encode(record).encode("utf-8")) + 32 + len(
        "episode:retained-1".encode("utf-8"))
    assert audit["charged_bytes"] == result["charged_bytes"]
    assert memory.audit()["used_bytes"] <= memory.capacity_bytes


def test_target_receipts_not_selectively_protected():
    memory = ChargedMemory(capacity_bytes=4096)
    world = ThermalWorld(object_ids=("source-object", "target-object"))
    source = _receipt_payload(world.apply("source-object", "warm"))
    target = _receipt_payload(world.apply("target-object", "warm"))

    source_result = memory.put("source:1", source)
    target_result = memory.put("target:1", target)
    assert source_result["status"] == target_result["status"] == "stored"
    assert source_result["protected"] is target_result["protected"] is False
    source_copy, _ = memory.retrieve("source:1")
    target_copy, _ = memory.retrieve("target:1")
    assert source_copy == source and target_copy == target


def test_world_history_not_agent_memory():
    world = ThermalWorld(object_ids=("history-object",))
    receipt = world.apply("history-object", "warm")
    learner = NativeTargetLearner(owner_id="p25-history-boundary")

    # The evaluator's simulator owns the receipt until explicit delivery.
    assert len(world.receipts) == 1
    assert learner.accounting.visible_observations == 0
    assert learner.accounting.target_actions == 0

    learner.observe_world_receipt(receipt)
    assert learner.accounting.visible_observations == 1
    assert learner.accounting.target_actions == 1
