"""Causal perturbation checks for the native projection-to-consumer path."""
from __future__ import annotations

import pytest

from evaluation.ousiometrics.native_adapter import NativeOusiometricInvestigation


def test_frame_knockout_affects_scored_path():
    agent = NativeOusiometricInvestigation("eq4_rotation_64bit_fixed_l1")
    for event in ("train-1", "train-2"):
        agent._ingest_fixture(event_id=event, episode_id=event, context_id="ctx",
                     coordinates=(0.2, 0.1, -0.1), consequence=(0.1, 0.2, 0.3),
                     action_kind="apply", object_id="tool", object_type="Tool")
    agent.learner.settle()
    # Disabled/mismatched policy cannot mint a current projection, so no
    # projected receipt reaches the common consumer and the query abstains.
    policy = agent.s.nodes("OusiometricFramePolicy")[0]
    agent.s.set_attr(policy, "enabled", 0.0)
    with pytest.raises(RuntimeError, match="did not produce"):
        agent._ingest_fixture(event_id="knocked-out", episode_id="ko", context_id="ctx",
                     coordinates=(0.2, 0.1, -0.1), consequence=(0.1, 0.2, 0.3),
                     action_kind="apply", object_id="tool", object_type="Tool")
    assert len(agent.s.nodes("OusiometricFrameProjection")) == 2
    assert len(agent.s.nodes("CommonTargetEvidence")) == 6
    assert agent.predict(query_id="unseen-after-knockout", coordinate=0, value=0.2,
                         action_kind="apply", object_id="unseen", object_type="Tool") is None


def test_inverse_tamper_is_detectable_before_transported_consumer_use():
    agent = NativeOusiometricInvestigation("eq4_rotation_64bit_transported_l1")
    agent.s.set_attr(agent._frame_node, "inverse_matrix", [[1.0, 0.0, 0.0]] * 3)
    with pytest.raises(RuntimeError, match="stale or owner-mismatched"):
        agent._ingest_fixture(event_id="e", episode_id="ep", context_id="ctx",
                     coordinates=(0.2, 0.1, -0.1), consequence=(0.1, 0.2, 0.3),
                     action_kind="apply", object_id="tool", object_type="Tool")
    result = agent.s.nodes("OusiometricFrameProjection")[0]
    projection = agent.s.node(result)["attrs"]
    assert projection["status"] == "current"
    assert projection["status"] != "verified_current"
    assert len(agent.s.nodes("OusiometricMetricMemory")) == 0
    assert len(agent.s.nodes("CommonTargetEvidence")) == 0


def _load_metric_neighbors(frame_id):
    agent = NativeOusiometricInvestigation(frame_id)
    points = (((0.45, 0.0, 0.0), "axis"), ((0.225, 0.315, 0.0), "diagonal"))
    for index, (coordinates, action) in enumerate(points):
        agent._ingest_fixture(event_id=f"memory-{index}", episode_id=f"memory-ep-{index}",
                     context_id=f"memory-context-{index}", coordinates=coordinates,
                     consequence=(float(index),) * 3, action_kind=action,
                     object_id=f"object-{index}", object_type="Tool")
    return agent


def test_native_transported_metric_has_full_rank_frame_parity():
    frames = ("shared_basis_64bit_transported_l1",
              "eq4_rotation_64bit_transported_l1",
              "random_rotation_dev_64bit_transported_l1")
    recalls = [_load_metric_neighbors(frame).metric_retrieve(
        query_id="same-query", coordinates=(0.0, 0.0, 0.0),
        legal_actions=("axis", "diagonal")) for frame in frames]
    assert all(recall is not None for recall in recalls)
    assert {recall["action_id"] for recall in recalls} == {"axis"}
    assert max(recall["distance"] for recall in recalls) - min(
        recall["distance"] for recall in recalls) < 1e-8


def test_native_fixed_metric_and_transported_metric_causally_change_retrieval():
    fixed = _load_metric_neighbors("eq4_rotation_64bit_fixed_l1")
    transported = _load_metric_neighbors("eq4_rotation_64bit_transported_l1")
    fixed_recall = fixed.metric_retrieve(query_id="fixed", coordinates=(0.0, 0.0, 0.0),
                                         legal_actions=("axis", "diagonal"))
    transported_recall = transported.metric_retrieve(
        query_id="transported", coordinates=(0.0, 0.0, 0.0),
        legal_actions=("axis", "diagonal"))
    assert fixed_recall["action_id"] == "diagonal"
    assert transported_recall["action_id"] == "axis"

