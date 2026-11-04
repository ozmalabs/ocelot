"""P21 charged-memory storage and real native-learner delivery checks."""
from __future__ import annotations

from dataclasses import asdict

from evaluation.process_mastery.developmental_memory import ChargedMemory
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import ThermalWorld, WorldReceipt


def _receipt_dict(receipt: WorldReceipt) -> dict:
    return asdict(receipt)


def test_no_uncharged_hidden_originals_after_eviction():
    memory = ChargedMemory(capacity_bytes=260, overhead_bytes=16)
    first = {"event_id": "a", "payload": "x" * 90}
    second = {"event_id": "b", "payload": "y" * 90}
    assert memory.put("a", first)["status"] == "stored"
    assert memory.put("b", second)["status"] == "stored"
    assert not memory.contains("a")
    recovered, receipt = memory.retrieve("a")
    assert recovered is None and receipt["status"] == "unavailable"
    assert memory.used_bytes() <= memory.capacity_bytes
    assert memory.audit()["evictions"] == [{"key": "a", "reason": "capacity"}]


def test_all_arms_receive_the_same_memory_policy():
    capacities = {arm: ChargedMemory(capacity_bytes=4096).capacity_bytes
                  for arm in ("sleep", "replay_only", "awake", "no_offline")}
    assert set(capacities.values()) == {4096}


def test_curriculum_task_reaches_native_learner_from_retrieved_receipts():
    memory = ChargedMemory(capacity_bytes=4096)
    world = ThermalWorld(object_ids=("train-a", "train-b"))
    receipts = [world.apply("train-a", "warm"), world.apply("train-b", "warm")]
    for index, receipt in enumerate(receipts):
        assert memory.put(f"task-1:event-{index}", _receipt_dict(receipt))["status"] == "stored"

    learner = NativeTargetLearner(owner_id="curriculum-delivery")
    for index in range(2):
        saved, audit = memory.retrieve(f"task-1:event-{index}")
        assert saved is not None and audit["status"] == "retrieved"
        learner.observe_world_receipt(WorldReceipt(**saved))
    learner.settle()
    assert len(learner.hypotheses()) == 1
    assert learner.accounting.target_actions == 2
    assert memory.audit()["retrieval_bytes"] > 0


def test_sleep_chunk_is_used_on_delayed_task():
    memory = ChargedMemory(capacity_bytes=4096)
    world = ThermalWorld(object_ids=("sleep-a", "sleep-b"))
    receipts = [world.apply("sleep-a", "warm"), world.apply("sleep-b", "warm")]
    keys = []
    for index, receipt in enumerate(receipts):
        key = f"source:{index}"
        keys.append(key)
        assert memory.put(key, _receipt_dict(receipt))["status"] == "stored"
    chunk = memory.put_verified_chunk("sleep-chunk", keys)
    assert chunk["status"] == "stored"
    assert all(not memory.contains(key) for key in keys)
    restored, retrieval = memory.retrieve("sleep-chunk")
    assert retrieval["encoding"] == "zlib-json" and restored["lossless"] is True
    learner = NativeTargetLearner(owner_id="delayed-memory-test")
    for saved in restored["records"]:
        learner.observe_world_receipt(WorldReceipt(**saved))
    learner.settle()
    prediction = learner.predict(
        query_id="delayed-memory-query", action_kind="warm",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", object_id="sleep-unseen")
    assert prediction["status"] == "predicted"
    assert memory.audit()["decode_work_bytes"] > 0


def test_counterevidence_survives_lossless_compression():
    memory = ChargedMemory(capacity_bytes=4096)
    records = [
        {"event_id": f"event-{i}", "kind": "support", "transition": "cold->warm"}
        for i in range(3)
    ]
    records.append({"event_id": "counterexample-1", "kind": "counterexample",
                    "transition": "cold->unchanged", "evidence_status": "observed"})
    keys = []
    for index, record in enumerate(records):
        key = f"episode:{index}"
        keys.append(key)
        assert memory.put(key, record, protected=record["kind"] == "counterexample")["status"] == "stored"
    chunk = memory.put_verified_chunk("verified-chunk", keys)
    assert chunk["status"] == "stored" and chunk["protected"] is True
    restored, _ = memory.retrieve("verified-chunk")
    counterevidence = [row for row in restored["records"] if row["kind"] == "counterexample"]
    assert counterevidence == [records[-1]]


def test_later_test_identity_is_absent_from_curriculum_input():
    task = {"task_id": "train:17", "split": "training", "status": "awaiting_experience",
            "expected_outcome": "unknown", "answer_fields_absent": True,
            "action_kind": "warm", "object_type": "ThermalSample",
            "feature_key": "temperature", "before_value": "cold"}
    memory = ChargedMemory(capacity_bytes=4096)
    memory.put("training-task", task)
    stored, _ = memory.retrieve("training-task")
    assert stored == task
    assert "sealed_eval_id" not in stored and "expected_after_value" not in stored
    assert stored["split"] == "training" and stored["answer_fields_absent"] is True
