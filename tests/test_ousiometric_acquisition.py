"""P28 adapter to the existing P17 observed-axis acquisition lifecycle."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from substrate_rs import _native

from evaluation.ousiometrics.geometry_reference import GPADS_FROM_GAS
from scripts.gen_ousiometric_acquisition_seed import build_seed as build_acquisition_seed
from scripts.gen_ousiometric_frames_seed import build_seed as build_frames_seed
from scripts.gen_qualia_acquisition_seed import build_seed as build_qualia_seed

ROOT = Path(__file__).resolve().parents[1]


def _boot(*, acquisition=True, budget=100.0):
    sub = _native.Substrate()
    agent = sub.add_node("Agent", {})
    for seed_id in ("default_mode_core", "thinking_budget", "qualia_space",
                    "cognition_signature", "experience_signature"):
        result = sub.load_seed_manifest(json.loads((ROOT / "seeds" / f"{seed_id}.json").read_text()), agent)
        assert result["rules_skipped"] == [], (seed_id, result)
    for manifest in (build_qualia_seed(), build_frames_seed(), build_acquisition_seed()):
        result = sub.load_seed_manifest(manifest, agent)
        assert result["rules_skipped"] == [], result
    sub.set_attr(sub.nodes("ThinkingBudget")[0], "enabled", 1.0)
    sub.set_attr(sub.nodes("ThinkingBudget")[0], "remaining", float(budget))
    sub.set_attr(sub.nodes("ThinkingBudget")[0], "last_refill_epoch", 10.0)
    sub.set_attr(sub.nodes("NetworkModeState")[0], "epoch", 10.0)
    sub.set_attr(sub.nodes("QualiaAcquisitionPolicy")[0], "enabled", 1.0)
    sub.set_attr(sub.nodes("OusiometricAcquisitionPolicy")[0], "enabled", 1.0 if acquisition else 0.0)
    return sub, agent


def _tick(sub, rounds=60):
    for _ in range(rounds):
        if not sub.run_rules(4000):
            return
    raise AssertionError("ousiometric acquisition rules failed to reach fixpoint")


def _episode(sub, agent, i, value, consequence, *, source_epoch=3.0):
    episode_id, event_id, feature_id = f"p28-episode-{i}", f"p28-event-{i}", f"p28-feature-{i}"
    episode = sub.add_node("ExperienceEpisode", {
        "owner_id": "p28-agent", "episode_id": episode_id,
        "context_id": f"p28-context-{i}", "status": "observed"})
    event = sub.add_node("ExperienceEvent", {
        "owner_id": "p28-agent", "episode_id": episode_id, "event_id": event_id,
        "action_id": f"p28-action-{i}", "status": "observed",
        "source_epoch": source_epoch, "model_epoch": 2.0,
        "frame_epoch": 5.0, "frame_id": "shared-source-frame"})
    feature = sub.add_node("ExperienceFeatureObservation", {
        "owner_id": "p28-agent", "episode_id": episode_id, "event_id": event_id,
        "feature_id": feature_id, "feature_key": "observed-contact-pattern",
        "feature_family": "tool_contact", "feature_value": value,
        "value_kind": "symbol", "grain": 0.0, "is_missing": False,
        "source_epoch": source_epoch, "model_epoch": 2.0, "frame_epoch": 5.0,
        "status": "observed"})
    receipt = sub.add_node("ExperienceOutcomeReceipt", {
        "owner_id": "p28-agent", "episode_id": episode_id, "event_id": event_id,
        "feature_id": feature_id, "source_epoch": source_epoch,
        "model_epoch": 2.0, "frame_epoch": 5.0, "status": "observed",
        "evidence_status": "observed", "consequence_kind": "measured_outcome",
        "consequence_value": consequence})
    sub.add_edge(agent, "has_experience_episode", episode)
    sub.add_edge(episode, "has_experience_event", event)
    sub.add_edge(event, "has_episode_feature", feature)
    sub.add_edge(feature, "has_outcome_receipt", receipt)
    return episode, event, feature, receipt


def _five_episode_candidate(sub, agent, *, same_feature=False):
    values = ("same", "same", "same") if same_feature else ("rough", "smooth", "rough")
    outcomes = ("repair", "continue", "repair")
    for i, (value, outcome) in enumerate(zip(values, outcomes), start=1):
        _episode(sub, agent, i, value, outcome)
    _tick(sub)
    candidate = next((n for n in sub.nodes("QualiaAxisCandidate")
                      if sub.node(n)["attrs"].get("feature_key") == "observed-contact-pattern"), None)
    if candidate is None:
        return None
    if same_feature:
        return candidate
    for i, value, outcome in ((4, "smooth", "continue"), (5, "rough", "repair")):
        _episode(sub, agent, i, value, outcome)
    _tick(sub)
    return candidate


def test_acquired_frame_has_episode_witnesses():
    sub, agent = _boot(acquisition=True)
    candidate = _five_episode_candidate(sub, agent)
    assert candidate is not None
    assert sub.node(candidate)["attrs"]["status"] == "validated"
    frame_candidate = sub.nodes("OusiometricFrameCandidate")[0]
    attrs = sub.node(frame_candidate)["attrs"]
    assert attrs["status"] == "proposed"
    assert attrs["observed_witness_count"] == 3.0
    assert attrs["fresh_validation_count"] >= 2.0
    assert attrs["adds_observed_coordinate"] is True
    assert attrs["rotation_only"] is False
    assert sub.neighbours(frame_candidate, "derived_from_axis_candidate") == [candidate]
    assert len(sub.neighbours(candidate, "has_acquisition_witness")) == 3
    assert len(sub.neighbours(candidate, "has_acquisition_validation")) >= 2


def test_rotation_not_new_dimension():
    frames = build_frames_seed()["nodes"]
    fixed = [node["attrs"] for node in frames if node["type"] == "OusiometricFrame"]
    assert all(frame["coordinate_count"] == 3.0 for frame in fixed)
    assert all(np.linalg.matrix_rank(frame["forward_matrix"]) == 3 for frame in fixed)
    assert np.linalg.matrix_rank(GPADS_FROM_GAS) == 3
    assert not any("adds_observed_coordinate" in frame for frame in fixed)
    # The P28 acquired-coordinate condition is a separately costed four-axis
    # learned-flex proposal; it is never relabeled as a rotation.
    sub, agent = _boot(acquisition=True)
    candidate = _five_episode_candidate(sub, agent)
    assert candidate is not None
    flex = sub.node(sub.nodes("OusiometricFrameCandidate")[0])["attrs"]
    assert (flex["source_coordinate_count"], flex["target_coordinate_count"]) == (3.0, 4.0)


def test_new_dimension_requires_observed_information():
    sub, agent = _boot(acquisition=True)
    candidate = _five_episode_candidate(sub, agent, same_feature=True)
    assert candidate is None
    assert sub.nodes("OusiometricFrameCandidate") == []
    _tick(sub)
    assert sub.nodes("OusiometricFrameCandidate") == []


def test_heldout_lexical_labels_unavailable():
    manifest = build_acquisition_seed()
    policy = manifest["nodes"][0]["attrs"]
    assert manifest["self_load_only"] is True
    assert policy["lexical_labels_available"] is False
    serialized = json.dumps(manifest, sort_keys=True).casefold()
    assert "gpads" not in serialized and "vad_label" not in serialized
    assert "heldout_used_for_selection" in json.dumps(manifest)


def test_candidate_proposal_cost_charged():
    sub, agent = _boot(acquisition=False)
    axis = _five_episode_candidate(sub, agent)
    assert axis is not None and sub.node(axis)["attrs"]["status"] == "validated"
    budget = sub.nodes("ThinkingBudget")[0]
    before = sub.node(budget)["attrs"]["remaining"]
    policy = sub.nodes("OusiometricAcquisitionPolicy")[0]
    sub.set_attr(policy, "enabled", 1.0)
    _tick(sub)
    requests = [n for n in sub.nodes("ThinkingBudgetRequest")
                if sub.node(n)["attrs"].get("requester_kind") == "ousiometric_frame_proposal"]
    assert len(requests) == 1
    assert sub.node(requests[0])["attrs"]["status"] == "approved"
    proposal = sub.nodes("OusiometricFrameCandidate")[0]
    attrs = sub.node(proposal)["attrs"]
    assert attrs["proposal_work_funded"] is True
    assert attrs["package_cost_complete"] is True
    assert attrs["exception_bits"] == 0.0
    assert attrs["total_description_bits"] == 640.0
    assert sub.node(budget)["attrs"]["remaining"] == before - attrs["proposal_work_cost"]


def test_contested_source_retires_frame_proposal():
    sub, agent = _boot(acquisition=True)
    axis = _five_episode_candidate(sub, agent)
    assert axis is not None
    frame_candidate = sub.nodes("OusiometricFrameCandidate")[0]
    sub.set_attr(axis, "status", "contested")
    _tick(sub)
    assert sub.node(frame_candidate)["attrs"]["status"] == "retired"
    assert sub.node(frame_candidate)["attrs"]["retirement_reason"] == "source_contested_or_stale"
