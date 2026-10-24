"""P24 common target contract and graph-native receipt projection gates."""
from pathlib import Path

from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.target_learning_worlds import ThermalWorld
from scripts.gen_common_target_evidence_seed import build_seed


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/research/engine_substrate/COGNITION_ADDITIVE_TRANSFER_CONTRACT.md"
P20_RESULTS = ROOT / "docs/research/engine_substrate/COGNITION_LINEAR_P20_RESULTS.md"


def test_all_arms_assimilate_each_target_receipt():
    text = CONTRACT.read_text()
    assert "Every arm" in text and "ordinary `observe_world_receipt`" in text
    assert "The ordinary path owns target action and observation counts." in text
    for arm in ("fresh", "compatible_source", "wrong_source", "same_target_map_work"):
        assert f"`{arm}`" in text
    assert "All four arms receive the same target receipt IDs" in text


def test_pairing_does_not_duplicate_observation_credit():
    text = CONTRACT.read_text()
    assert "A map-pair view references that same target event ID" in text
    assert "it is not another target observation, action or support unit" in text
    assert "One event ID contributes at most one ordinary support item" in text
    assert "Replay of an event ID is idempotent" in text


def test_missing_map_cannot_block_fresh_learning():
    text = CONTRACT.read_text()
    assert "Ordinary target learning proceeds if the map is absent, pending" in text
    assert "stale, incompatible, wrong, or rejected" in text
    assert "No imported prior; cost-control arm only" in text


def test_source_exposure_cost_visible():
    text = CONTRACT.read_text()
    for field in ("source action count", "source-information units",
                  "map-pair count", "map verification queries",
                  "native rule/model work", "shared-budget debits"):
        assert field in text
    assert "no source cost is hidden inside target interaction count" in text
    p20 = P20_RESULTS.read_text()
    assert "primary transfer efficacy" in p20 and "`FAIL`" in p20
    assert "−0.3333" in p20


def _receipt(i, *, world=None):
    world = world or ThermalWorld(object_ids=[f"sample-{i}"])
    return world.apply(f"sample-{i}", "warm")


def _learned(learner):
    learner.settle()
    return learner.hypotheses()


def test_common_target_generator_is_deterministic_and_policy_is_opt_in():
    import json
    from scripts.gen_common_target_evidence_seed import OUT
    assert build_seed()["id"] == "common_target_evidence"
    assert json.loads(OUT.read_text()) == build_seed()
    learner = CommonTargetLearner(policy_enabled=False)
    learner.observe_world_receipt(_receipt(1))
    learner.observe_world_receipt(_receipt(2))
    learner.settle()
    assert not learner.s.nodes("TransitionObservation")
    assert not learner.hypotheses()


def test_two_target_events_teach_in_every_arm():
    for arm in ("fresh", "compatible_source", "wrong_source", "same_target_map_work"):
        learner = CommonTargetLearner()
        if arm == "compatible_source":
            learner.expose_source(source_id="source", relation="matched")
        elif arm == "wrong_source":
            learner.expose_source(source_id="source", relation="mismatched")
        for i in (1, 2):
            learner.observe_world_receipt(_receipt(i))
        hypotheses = _learned(learner)
        assert len(learner.s.nodes("TransitionObservation")) == 2, arm
        assert len(hypotheses) == 1, arm
        assert hypotheses[0]["support_count"] == 2.0, arm
        assert learner.accounting.target_actions == 2, arm


def test_duplicate_receipt_no_extra_support():
    learner = CommonTargetLearner()
    receipt = _receipt(1)
    first = learner.observe_world_receipt(receipt)
    replay = learner.observe_world_receipt(receipt)
    assert first == replay
    learner.observe_world_receipt(_receipt(2))
    hypotheses = _learned(learner)
    assert len(learner.s.nodes("TransitionObservation")) == 2
    assert [len(learner.s.neighbours(n, "has_action_receipt"))
            for n in learner.s.nodes("TransitionObservation")] == [1, 1]
    assert hypotheses[0]["support_count"] == 2.0
    assert learner.accounting.target_actions == 2


def test_map_pending_does_not_delay_prediction():
    learner = CommonTargetLearner()
    for i in (1, 2):
        learner.observe_world_receipt(_receipt(i), map_view={
            "pair_id": f"pending-pair-{i}", "source_event_id": f"src-{i}",
            "source_object_id": f"source-{i}", "source_action": "heat",
            "source_object_type": "HeatSample", "source_feature": "temperature",
            "source_before": "cool", "source_after": "hot"})
    learner.settle()
    assert len(learner.s.nodes("TargetMapObservation")) == 2
    assert all(learner.s.node(n)["attrs"]["status"] == "map_pending"
               for n in learner.s.nodes("TargetMapObservation"))
    assert len(learner.hypotheses()) == 1
    prediction = learner.predict(query_id="pending-map-query", action_kind="warm",
                                 object_type="ThermalSample", feature_key="temperature",
                                 before_value="cold", object_id="new-sample")
    assert prediction["expected_after_value"] == "warm"


def test_wrong_source_keeps_real_counterexample():
    learner = CommonTargetLearner()
    learner.expose_source(source_id="wrong-source", relation="mismatched")
    for i in (1, 2):
        learner.observe_world_receipt(_receipt(i))
    _learned(learner)
    learner.observe_world_receipt(_receipt(3, world=_ContraryThermalWorld()))
    learner.settle()
    hypothesis = learner.hypotheses()[0]
    assert hypothesis["status"] == "disputed"
    assert hypothesis["counterexample_count"] == 1.0


class _ContraryThermalWorld:
    def apply(self, object_id, action):
        from evaluation.process_mastery.target_learning_worlds import WorldReceipt
        return WorldReceipt("contrary:1", object_id, "ThermalSample", action,
                            "temperature", "cold", "cold", "observed", True, 1)

