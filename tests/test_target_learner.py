"""P20 bounded fresh target learner: receipt-bound native transition induction."""
import json
from pathlib import Path

from substrate_rs import _native
from scripts.gen_process_induction_seed import build_seed

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
    starts = []
    for source_condition in ("fresh", "matched", "mismatched"):
        s, ag = _boot()
        s.add_node("SourceExposure", {"condition": source_condition,
                                       "charged_units": 1.0, "status": "observed"})
        starts.append((s.node(s.nodes("ModelLearningPolicy")[0])["attrs"],
                       len(s.nodes("ProcessInductionHypothesis")),
                       s.node(ag)["attrs"]))
    assert all(not hyps for _, hyps, _ in starts)
    assert all(attrs["enabled"] == 1.0 for attrs, _, _ in starts)


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
