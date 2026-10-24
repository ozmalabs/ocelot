"""P25.04 simulator, split-boundary, and capacity-assignment checks."""
from dataclasses import asdict

from evaluation.process_mastery.developmental_memory import ChargedMemory
from evaluation.process_mastery.persistent_retention_worlds import (
    CAPACITY_RATIOS,
    PersistentRetentionWorld,
    capacity_for_ratio,
    serialized_learning_content_bytes,
)
from evaluation.process_mastery.target_learner import NativeTargetLearner


def _world(family="thermal", stream="p25-world-test", seed=17):
    return PersistentRetentionWorld(stream, family, seed)


def test_pressure_affects_relevant_learned_content():
    world = _world()
    receipts = world.acquire()
    rows = [asdict(receipt) for receipt in receipts]
    capacity = capacity_for_ratio(rows, 0.5)
    assert capacity < serialized_learning_content_bytes(rows)

    memory = ChargedMemory(capacity_bytes=capacity)
    for index, row in enumerate(rows):
        memory.put(f"learning:{index}", row)
    audit = memory.audit()
    assert audit["used_bytes"] <= capacity
    assert audit["evictions"] or any(
        memory.retrieve(f"learning:{index}")[0] is None for index in range(len(rows)))


def test_delay_does_not_replace_learner():
    world = _world("latch")
    learner = NativeTargetLearner(owner_id="p25-world-lifecycle")
    for receipt in world.acquire():
        world.deliver(learner, receipt)
    learner.settle()
    before = (id(learner), id(learner.s), learner.owner_id)
    world.add_interference(5)
    world.record_pre_delay(learner, query_id="pre-delay", object_id="new-latch")
    after = (id(learner), id(learner.s), learner.owner_id)
    assert after == before


def test_external_archive_not_visible():
    world = _world()
    learner = NativeTargetLearner(owner_id="p25-archive-boundary")
    acquired = world.acquire()
    world.deliver(learner, acquired[0])
    world.deliver(learner, acquired[1])
    learner.settle()
    result = world.delayed_score(learner, query_id="delayed", object_id="sealed-target")
    archive = world.evaluator_archive()
    audit = world.learner_input_audit()
    assert any(row["event_id"] == result["delayed_event_id"] for row in archive)
    assert result["delayed_event_id"] not in audit["delivered_event_ids"]
    assert result["delayed_event_id"] not in {
        row.get("event_id") for row in learner.learning_records
    }
    assert audit["evaluator_archive_accessible"] is False


def test_capacity_assignment_independent_of_arm():
    world = _world()
    records = [asdict(receipt) for receipt in world.acquire()]
    assignment = {ratio: capacity_for_ratio(records, ratio)
                  for ratio in CAPACITY_RATIOS}
    # Arm is absent from the assignment interface and therefore cannot affect
    # the stream's pre-treatment capacity stratum.
    assert assignment == {ratio: capacity_for_ratio(records, ratio)
                          for ratio in CAPACITY_RATIOS}
    assert assignment[0.5] < assignment[1.0] < assignment[2.0]


def test_unsolved_pre_delay_not_hidden():
    world = _world("thermal", "p25-unsolved-pre-delay", 31)
    learner = NativeTargetLearner(owner_id="p25-unsolved-pre-delay")
    pre = world.record_pre_delay(learner, query_id="pre-unsolved", object_id="sealed")
    delayed = world.delayed_score(learner, query_id="delayed-unsolved", object_id="sealed")
    assert pre["prediction_status"] == "not_predicted"
    assert delayed["prediction_status"] == "not_predicted"
    assert delayed["correct"] is False
    assert world.pre_delay_records[0] == pre
    assert len(world.pre_delay_records) == 2
