"""P7.03 native graph-rule acceptance tests for qualia acquisition."""
import json
from pathlib import Path

from substrate_rs import _native

from scripts.gen_qualia_acquisition_seed import build_seed

ROOT = Path(__file__).resolve().parents[1]


def _boot(enabled=True, budget=16):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "qualia_space",
                 "cognition_signature", "experience_signature"):
        result = s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
        assert result["rules_skipped"] == [], (name, result)
    result = s.load_seed_manifest(build_seed(), ag)
    assert result["rules_skipped"] == [], result
    s.set_attr(s.nodes("ThinkingBudget")[0], "enabled", 1.0)
    s.set_attr(s.nodes("ThinkingBudget")[0], "remaining", float(budget))
    s.set_attr(s.nodes("ThinkingBudget")[0], "last_refill_epoch", 10.0)
    s.set_attr(s.nodes("QualiaAcquisitionPolicy")[0], "enabled", 1.0 if enabled else 0.0)
    s.set_attr(s.nodes("NetworkModeState")[0], "epoch", 10.0)
    return s, ag


def _tick(s, rounds=30):
    for _ in range(rounds):
        if not s.run_rules(2000):
            return
    raise AssertionError("qualia acquisition rules failed to reach a fixpoint")


def _episode(s, ag, i, value, consequence, *, owner="owner-a", context=None,
             source_epoch=3, model_epoch=2, frame_epoch=5, receipt_status="observed"):
    episode_id = f"episode-{i}"
    event_id = f"event-{i}"
    feature_id = f"feature-{i}"
    ep = s.add_node("ExperienceEpisode", {
        "owner_id": owner, "episode_id": episode_id,
        "context_id": context or f"context-{i}", "status": "observed"})
    ev = s.add_node("ExperienceEvent", {
        "owner_id": owner, "episode_id": episode_id, "event_id": event_id,
        "action_id": f"action-{i}", "status": "observed",
        "source_epoch": source_epoch, "model_epoch": model_epoch,
        "frame_epoch": frame_epoch, "frame_id": f"frame-{i}"})
    feature = s.add_node("ExperienceFeatureObservation", {
        "owner_id": owner, "episode_id": episode_id, "event_id": event_id,
        "feature_id": feature_id, "feature_key": "contact-pattern",
        "feature_family": "tool_contact", "feature_value": value,
        "value_kind": "symbol", "grain": 0.0, "is_missing": False,
        "source_epoch": source_epoch, "model_epoch": model_epoch,
        "frame_epoch": frame_epoch, "status": "observed"})
    receipt = s.add_node("ExperienceOutcomeReceipt", {
        "owner_id": owner, "episode_id": episode_id, "event_id": event_id,
        "feature_id": feature_id, "source_epoch": source_epoch,
        "model_epoch": model_epoch, "frame_epoch": frame_epoch,
        "status": receipt_status, "evidence_status": receipt_status,
        "consequence_kind": "measured_outcome", "consequence_value": consequence})
    s.add_edge(ag, "has_experience_episode", ep)
    s.add_edge(ep, "has_experience_event", ev)
    s.add_edge(ev, "has_episode_feature", feature)
    s.add_edge(feature, "has_outcome_receipt", receipt)
    return ep, ev, feature, receipt


def _candidate(s):
    return next((n for n in s.nodes("QualiaAxisCandidate")
                 if s.node(n)["attrs"].get("feature_key") == "contact-pattern"), None)


def _three_recurrence(s, ag):
    _episode(s, ag, 1, "rough", "repair")
    _episode(s, ag, 2, "smooth", "continue")
    _episode(s, ag, 3, "rough", "repair")
    _tick(s)
    return _candidate(s)


def test_no_target_axis_in_inputs():
    s, ag = _boot()
    _episode(s, ag, 1, "rough", "repair")
    _episode(s, ag, 2, "smooth", "continue")
    _episode(s, ag, 3, "rough", "repair")
    assert all("target_dimension" not in s.node(n)["attrs"] and
               "expected_class" not in s.node(n)["attrs"]
               for n in s.nodes("ExperienceEpisode") + s.nodes("ExperienceEvent") +
               s.nodes("ExperienceFeatureObservation"))
    _tick(s)
    candidate = _candidate(s)
    assert candidate is not None
    attrs = s.node(candidate)["attrs"]
    assert attrs["feature_key"] == "contact-pattern"
    assert not any(k in attrs for k in ("target_dimension", "expected_class", "answer"))
    assert len(s.neighbours(candidate, "has_acquisition_witness")) == 3


def test_finer_grain_cannot_fake_missing_dimension():
    s, ag = _boot()
    # Existing dimension coordinates remain equal; the observed feature is absent.
    for i, value in enumerate(("same", "same", "same"), 1):
        _episode(s, ag, i, value, "outcome", source_epoch=3)
    _tick(s)
    assert _candidate(s) is None
    # Equal source values cannot be split by a grain label or aperture.
    dim = s.add_node("QualiaDimension", {"name": "existing:contact", "family": "phenomenal",
                                        "grain_values": [0.0, 1.0]})
    assert s.node(dim)["attrs"]["name"] == "existing:contact"
    assert _candidate(s) is None


def test_new_axis_predicts_unseen_consequence():
    s, ag = _boot()
    candidate = _three_recurrence(s, ag)
    assert candidate is not None
    attrs = s.node(candidate)["attrs"]
    assert attrs["status"] == "proposed"
    assert len(s.neighbours(candidate, "has_acquisition_witness")) == 3
    assert not any(s.node(n)["attrs"].get("acquired") == 1.0 for n in s.nodes("QualiaDimension"))
    _episode(s, ag, 4, "smooth", "continue")
    _tick(s)
    assert s.node(candidate)["attrs"]["status"] == "proposed"
    _episode(s, ag, 5, "rough", "repair")
    _tick(s)
    assert s.node(candidate)["attrs"]["status"] == "validated"
    validations = s.neighbours(candidate, "has_acquisition_validation")
    assert len([v for v in validations if s.node(v)["attrs"]["result"] == "positive"]) >= 2
    dim_id = s.node(candidate)["attrs"]["dimension_id"]
    assert any(s.node(n)["attrs"].get("name") == dim_id for n in s.nodes("QualiaDimension"))
    assert len([n for n in s.nodes("CognitionSignatureSource")
                if s.node(n)["attrs"].get("source_id") == "qualia_acquisition"]) >= 3


def test_revision_preserves_old_witnesses():
    s, ag = _boot()
    candidate = _three_recurrence(s, ag)
    assert candidate is not None
    _episode(s, ag, 4, "smooth", "continue")
    _episode(s, ag, 5, "rough", "repair")
    _tick(s)
    assert s.node(candidate)["attrs"]["status"] == "validated"
    old_witnesses = set(s.neighbours(candidate, "has_acquisition_witness"))
    _episode(s, ag, 6, "rough", "unexpected", context="fresh-context-6")
    _tick(s)
    assert s.node(candidate)["attrs"]["status"] == "contested"
    assert s.node(candidate)["attrs"]["revision_count"] == 1.0
    assert old_witnesses.issubset(set(s.neighbours(candidate, "has_acquisition_witness")))
    assert any(s.node(v)["attrs"]["result"] == "negative"
               for v in s.neighbours(candidate, "has_acquisition_validation"))
    dim = next(n for n in s.nodes("QualiaDimension")
               if s.node(n)["attrs"].get("name") == s.node(candidate)["attrs"]["dimension_id"])
    assert s.node(dim)["attrs"]["acquisition_status"] == "contested"
    _episode(s, ag, 7, "rough", "repair", context="fresh-context-7")
    _episode(s, ag, 8, "smooth", "continue", context="fresh-context-8")
    _tick(s)
    assert s.node(candidate)["attrs"]["status"] == "validated"
    assert s.node(dim)["attrs"]["acquisition_status"] == "standing"
    assert s.node(candidate)["attrs"]["revision_count"] == 1.0


def test_residual_mints_once():
    s, ag = _boot()
    _three_recurrence(s, ag)
    _tick(s, rounds=5)
    assert len([n for n in s.nodes("QualiaAxisCandidate")
                if s.node(n)["attrs"].get("feature_key") == "contact-pattern"]) == 1


def test_redecode_uses_acquired_axis():
    s, ag = _boot()
    candidate = _three_recurrence(s, ag)
    _episode(s, ag, 4, "smooth", "continue")
    _episode(s, ag, 5, "rough", "repair")
    _tick(s)
    assert s.node(candidate)["attrs"]["status"] == "validated"
    sources = [n for n in s.nodes("CognitionSignatureSource")
               if s.node(n)["attrs"].get("source_id") == "qualia_acquisition"]
    assert sources
    axis = s.node(candidate)["attrs"]["dimension_id"]
    assert all(axis in s.node(n)["attrs"]["dimension_ids"] for n in sources)


def test_unrelated_episodes_not_merged():
    s, ag = _boot()
    _episode(s, ag, 1, "rough", "repair", owner="owner-a")
    _episode(s, ag, 2, "smooth", "continue", owner="owner-b")
    _episode(s, ag, 3, "rough", "repair", owner="owner-a")
    _episode(s, ag, 4, "smooth", "continue", owner="owner-b")
    _tick(s)
    assert _candidate(s) is None
    assert not s.nodes("QualiaAxisCandidate")


def test_disabled_policy_and_exhausted_budget_fail_closed():
    s, ag = _boot(enabled=False)
    _episode(s, ag, 1, "rough", "repair")
    _tick(s)
    assert not s.nodes("ThinkingBudgetRequest")
    assert not s.nodes("QualiaAcquisitionWitness")

    s, ag = _boot(budget=0)
    _episode(s, ag, 1, "rough", "repair")
    _tick(s)
    requests = s.nodes("ThinkingBudgetRequest")
    assert len(requests) == 1
    assert s.node(requests[0])["attrs"]["status"] == "denied"
    assert not s.nodes("QualiaAcquisitionWitness")


def test_stale_receipt_cannot_become_witness():
    s, ag = _boot()
    _episode(s, ag, 1, "rough", "repair", source_epoch=3)
    # Mismatch the source epoch after receipt creation, simulating a stale source.
    feature = s.nodes("ExperienceFeatureObservation")[0]
    s.set_attr(feature, "source_epoch", 4)
    _tick(s)
    assert not s.nodes("QualiaAcquisitionWitness")
