"""P20 bounded fresh target learner: receipt-bound native transition induction."""
import json
from pathlib import Path

from substrate_rs import _native
from scripts.gen_process_induction_seed import build_seed
from evaluation.process_mastery.target_learner import NativeTargetLearner

ROOT = Path(__file__).resolve().parents[1]


def _boot(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "cognition_signature",
                 "experience_signature"):
        s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
    result = s.load_seed_manifest(build_seed(), ag)
    assert result["rules_skipped"] == [], result
    for budget in s.nodes("ThinkingBudget"):
        s.set_attr(budget, "enabled", 1.0)
        s.set_attr(budget, "remaining", 100.0)
        s.set_attr(budget, "last_refill_epoch", 10.0)
    s.set_attr(s.nodes("NetworkModeState")[0], "epoch", 10.0)
    s.set_attr(s.nodes("ModelLearningPolicy")[0], "enabled", float(enabled))
    return s, ag


def _observe(s, ag, i, *, after="warm", owner="target", model=2, source=3,
             frame=5, receipt=True):
    episode, event = f"target-episode-{i}", f"target-event-{i}"
    obs = s.add_node("TransitionObservation", {
        "owner_id": owner, "episode_id": episode, "event_id": event,
        "object_id": f"object-{i}", "object_type": "Widget", "action_kind": "warm",
        "feature_key": "temperature", "before_value": "cold", "after_value": after,
        "source_epoch": source, "model_epoch": model, "frame_epoch": frame,
        "status": "observed"})
    action = s.add_node("TransitionActionReceipt", {
        "owner_id": owner, "episode_id": episode, "event_id": event,
        "source_epoch": source, "model_epoch": model, "frame_epoch": frame,
        "status": "observed"})
    s.add_edge(ag, "has_transition_observation", obs)
    s.add_edge(obs, "has_action_receipt", action)
    if receipt:
        outcome = s.add_node("TransitionOutcomeReceipt", {
            "owner_id": owner, "episode_id": episode, "event_id": event,
            "source_epoch": source, "model_epoch": model, "frame_epoch": frame,
            "status": "observed"})
        s.add_edge(obs, "has_outcome_receipt", outcome)
    return obs


def _run(s):
    for _ in range(40):
        if not s.run_rules(2000):
            return
    raise AssertionError("target learner did not reach fixpoint")


def test_fresh_has_real_learning_path():
    s, ag = _boot()
    _observe(s, ag, 1)
    _observe(s, ag, 2)
    _run(s)
    hypotheses = s.nodes("ProcessInductionHypothesis")
    assert len(hypotheses) == 1
    attrs = s.node(hypotheses[0])["attrs"]
    assert attrs["status"] == "candidate"
    assert attrs["after_value"] == "warm"
    assert attrs["support_count"] == 2.0
    assert len(s.neighbours(hypotheses[0], "supported_by_transition")) == 2


def test_same_target_affordances_and_empty_start_for_all_source_conditions():
    # Source availability is represented separately; it does not change the
    # target learner or its affordances before target evidence arrives.
    learners = [NativeTargetLearner() for _ in ("fresh", "matched", "mismatched")]
    learners[1].expose_source(source_id="source-a", relation="matched")
    learners[2].expose_source(source_id="source-b", relation="mismatched")
    for learner in learners:
        assert learner.s.node(learner.s.nodes("ModelLearningPolicy")[0])["attrs"]["enabled"] == 1.0
        assert len(learner.s.nodes("ThinkingBudget")) == 1
        assert not learner.s.nodes("TransitionObservation")
        assert not learner.s.nodes("ProcessInductionHypothesis")


def test_missing_outcome_receipt_cannot_teach_fresh_target():
    s, ag = _boot()
    _observe(s, ag, 1, receipt=False)
    _observe(s, ag, 2, receipt=False)
    _run(s)
    assert not s.nodes("ProcessInductionHypothesis")


def test_wrong_owner_or_epoch_receipt_does_not_create_hypothesis():
    s, ag = _boot()
    obs = _observe(s, ag, 1)
    outcome = s.neighbours(obs, "has_outcome_receipt")[0]
    s.set_attr(outcome, "model_epoch", 99.0)
    _run(s)
    assert not s.nodes("ProcessInductionHypothesis")


def test_disabled_policy_has_no_target_learning_path():
    s, ag = _boot(enabled=False)
    _observe(s, ag, 1)
    _observe(s, ag, 2)
    _run(s)
    assert not s.nodes("ProcessInductionHypothesis")


def test_counterevidence_disputes_target_effect():
    s, ag = _boot()
    _observe(s, ag, 1, after="warm")
    _observe(s, ag, 2, after="warm")
    _run(s)
    hypothesis = s.nodes("ProcessInductionHypothesis")[0]
    _observe(s, ag, 3, after="cold")
    _run(s)
    assert s.node(hypothesis)["attrs"]["status"] == "disputed"


def test_target_adapter_learns_from_two_world_observations_and_predicts_new_binding():
    learner = NativeTargetLearner()
    for i in (1, 2):
        learner.observe_opportunity(event_id=f"observed-{i}", action_kind="warm",
                                    object_id=f"obj-{i}", object_type="Widget",
                                    feature_key="temperature", before_value="cold",
                                    after_value="warm")
    learner.settle()
    assert len(learner.hypotheses()) == 1
    prediction = learner.predict(query_id="new-target", action_kind="warm",
                                 object_type="Widget", feature_key="temperature",
                                 before_value="cold", object_id="obj-new")
    assert prediction["expected_after_value"] == "warm"
    assert prediction["evidence_status"] == "predicted"
    assert learner.accounting.target_actions == 2


def test_source_exposure_is_charged_but_cannot_create_target_hypothesis():
    learner = NativeTargetLearner()
    learner.expose_source(source_id="matched-source-1", relation="matched", units=2.5)
    learner.settle()
    assert learner.accounting.source_information_units == 2.5
    assert learner.accounting.visible_observations == 0
    assert learner.hypotheses() == []


def test_missing_opportunity_is_counted_without_inventing_a_transition():
    learner = NativeTargetLearner()
    assert learner.observe_opportunity(event_id="occluded-1", visible=False) is None
    assert learner.accounting.evidence_opportunities == 1
    assert learner.accounting.missing_observations == 1
    assert learner.accounting.target_actions == 0
    assert learner.hypotheses() == []


def _source_prior(learner, *, map_status="verified", target_event="target-transfer-1",
                  exact=True):
    learner.import_source_prior(
        prior_id="source-prior-1", source_id="source-model-1",
        action_kind="warm", object_type="Widget", feature_key="temperature",
        before_value="cold", after_value="warm", source_epoch=3, model_epoch=2,
        frame_epoch=5,
        map_evidence={"map_id": "map-1", "status": map_status,
                      "mapping_kind": "exact_categorical_effect",
                      "target_frame_epoch": 5},
        target_receipt={"receipt_id": "target-verify-1", "source_prior_id": "source-prior-1",
                        "target_event_id": target_event, "status": "verified",
                        "exact_effect_match": exact})


def test_source_uses_same_target_verifier_and_new_binding_predictor():
    learner = NativeTargetLearner(transfer_enabled=True)
    _source_prior(learner)
    learner.expose_source(source_id="source-model-1", relation="matched", units=3.0)
    learner.observe_opportunity(event_id="target-transfer-1", action_kind="warm",
                                object_id="target-object-1", object_type="Widget",
                                feature_key="temperature", before_value="cold",
                                after_value="warm")
    learner.settle()
    assert len(learner.hypotheses()) == 1
    assert learner.hypotheses()[0]["effect_evaluation"] == "exact_source_map_and_target_receipt"
    prediction = learner.predict(query_id="transferred-binding", action_kind="warm",
                                 object_type="Widget", feature_key="temperature",
                                 before_value="cold", object_id="target-object-2")
    assert prediction["expected_after_value"] == "warm"


def test_wrong_map_or_wrong_target_receipt_is_rejected():
    for map_status, event_id in (("stale", "target-transfer-1"),
                                 ("verified", "different-target-event")):
        learner = NativeTargetLearner(transfer_enabled=True)
        _source_prior(learner, map_status=map_status, target_event=event_id)
        learner.observe_opportunity(event_id="target-transfer-1", action_kind="warm",
                                    object_id="target-object-1", object_type="Widget",
                                    feature_key="temperature", before_value="cold",
                                    after_value="warm")
        learner.settle()
        assert learner.hypotheses() == []
