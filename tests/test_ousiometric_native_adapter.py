"""Native frame ingestion and common-consumer integration gates for P28."""
from __future__ import annotations

import math

import pytest

from evaluation.ousiometrics.native_adapter import (
    NativeOusiometricInvestigation,
    validate_coordinates,
)
from evaluation.ousiometrics.worlds import FactorProfile, ToolInterventionWorld


def _agent(frame="shared_basis_64bit_fixed_l1"):
    return NativeOusiometricInvestigation(frame)


def _world_receipt(event, *, position=0.2):
    world = ToolInterventionWorld(FactorProfile(0.4, 0.0, 0.0, 0.0, 0.0),
                                  seed=sum(map(ord, event)), episode_id=event,
                                  context_id=f"ctx-{event}")
    world.position, world.armed, world.turn = position, True, 1
    before = world.agent_view()
    receipt = world.apply_action("apply_small", source_epoch=3, model_epoch=2,
                                 frame_epoch=1)
    return world, before, receipt


def _ingest(agent, event):
    world, before, receipt = _world_receipt(event)
    return agent.ingest_verified_world_receipt(world=world, receipt=receipt,
                                                before_view=before, split="training")


def test_native_consumer_uses_selected_frame():
    agent = _agent("eq4_rotation_64bit_transported_l1")
    first = _ingest(agent, "train-1")
    second = _ingest(agent, "train-2")
    assert first.frame_id == second.frame_id
    assert first.projected != first.source_coordinates
    assert len(agent.s.nodes("OusiometricFrameProjection")) == 2
    agent.learner.settle()
    prediction = agent.predict(query_id="query", coordinate=0, value=first.projected[0],
                               action_kind="apply_small", object_id="unseen",
                               object_type="tool_intervention")
    assert prediction is not None
    assert prediction["expected_after_value"] == repr(-0.21999999999999997)
    hypothesis = next(agent.s.node(n)["attrs"] for n in agent.s.nodes("ProcessInductionHypothesis")
                      if agent.s.node(n)["attrs"].get("feature_key")
                      == f"{agent.frame_id}:coordinate:0")
    assert hypothesis["before_value"] == repr(first.projected[0])


def test_same_receipt_assimilation_every_arm():
    arms = [_agent(frame) for frame in (
        "shared_basis_64bit_fixed_l1", "eq4_rotation_64bit_fixed_l1",
        "random_rotation_dev_64bit_fixed_l1", "eq4_rotation_8bit_fixed_l1")]
    world, before, receipt = _world_receipt("paired-event")
    results = [agent.ingest_verified_world_receipt(world=world, receipt=receipt,
                                                   before_view=before, split="training")
               for agent in arms]
    for agent in arms:
        agent.learner.settle()
    assert len({result.event_id for result in results}) == 1
    assert results[0].event_id.startswith("tool_intervention:paired-event:")
    assert all(len(agent.s.nodes("CommonTargetEvidence")) == 3 for agent in arms)
    assert all(len(agent.s.nodes("TransitionObservation")) == 3 for agent in arms)
    assert all(agent.learner.accounting.target_actions == 3 for agent in arms)
    assert all(result.source_coordinates == results[0].source_coordinates for result in results)


def test_host_never_selects_action():
    agent = _agent()
    assert agent.profile_audit()["no_host_action"] is True
    assert not hasattr(agent, "choose_action")
    assert not hasattr(agent, "request_action")


def test_common_budget_and_capacity():
    agent = _agent()
    frames = [agent.s.node(n)["attrs"] for n in agent.s.nodes("OusiometricFrame")]
    full = [f for f in frames if f["precision_bits_per_coordinate"] == 64.0]
    low = [f for f in frames if f["precision_bits_per_coordinate"] == 8.0]
    assert {f["coordinate_count"] for f in frames} == {3.0}
    assert {f["total_representation_bits"] for f in full} == {1408.0}
    assert {f["total_representation_bits"] for f in low} == {1240.0}


def test_investigation_profile_default_isolation():
    agent = _agent()
    audit = agent.profile_audit()
    assert audit["profile"] == "p28-ousiometric-investigation"
    assert audit["frame_enabled"] == [1.0]
    assert audit["acquisition_enabled"] == [0.0]
    ordinary = NativeOusiometricInvestigation("shared_basis_64bit_fixed_l1", enabled=False)
    assert ordinary.profile_audit()["frame_enabled"] == [0.0]
    assert ordinary.profile_audit()["acquisition_enabled"] == [0.0]


def test_investigation_dependency_closure():
    agent = _agent()
    rules = {rule.get("name") for rule in agent.s._inner.export_rules()}
    assert f"ouf_project_shared_event_{agent.frame_id}" in rules
    assert "oua_request_funded_flex_frame_proposal" in rules
    assert "cte_project_one_event_to_ordinary_transition" in rules
    assert "pi_predict_from_lifted_effect" in rules
    assert "qbh_authorize_only_source_bound_legal_funded_action" in rules


def test_malformed_nonfinite_out_of_range_and_epoch_mismatch_rejected_at_boundary():
    for coordinates in ((1.0, 2.0), (0.1, float("nan"), 0.0),
                        (0.1, float("inf"), 0.0), (0.1, 0.2, 0.6),
                        (True, 0.0, 0.0), ("0.1", 0.0, 0.0)):
        with pytest.raises(ValueError):
            validate_coordinates(coordinates)
    agent = _agent()
    with pytest.raises(ValueError):
        agent._ingest_fixture(event_id="bad", episode_id="ep-bad", context_id="ctx",
                     coordinates=(0.1, math.nan, 0.0), consequence=(0.0, 0.0, 0.0),
                     action_kind="apply", object_id="tool", object_type="Tool")
    assert not agent.s.nodes("OusiometricRawEvidence")
    with pytest.raises(ValueError, match="scope"):
        agent._ingest_fixture(event_id="wrong-epoch", episode_id="ep", context_id="ctx",
                     coordinates=(0.1, 0.0, 0.0), consequence=(0.0, 0.0, 0.0),
                     action_kind="apply", object_id="tool", object_type="Tool",
                     source_epoch=99)
    assert not agent.s.nodes("OusiometricRawEvidence")


def test_raw_source_audit_does_not_feed_scored_consumer():
    agent = _agent()
    first = _ingest(agent, "train-1")
    _ingest(agent, "train-2")
    agent.learner.settle()
    raw_node = first.raw_node
    agent.s.set_attr(raw_node, "coordinates", [0.49, -0.49, 0.49])
    prediction = agent.predict(query_id="query", coordinate=0, value=first.projected[0],
                               action_kind="apply_small", object_id="unseen",
                               object_type="tool_intervention")
    assert prediction["expected_after_value"] == repr(-0.21999999999999997)


def test_native_action_authorization_uses_acquired_projected_axis():
    agent = _agent()
    profile = FactorProfile(0.4, 0.0, 0.0, 0.0, 0.0)
    for i, position in enumerate((0.2, 0.8, 0.2, 0.8, 0.2), 1):
        world = ToolInterventionWorld(profile, seed=2800 + i,
                                      episode_id=f"behavior-{i}",
                                      context_id=f"context-{i}")
        world.position, world.armed, world.turn = position, True, 1
        before = world.agent_view()
        receipt = world.apply_action("apply_small", source_epoch=3,
                                     model_epoch=2, frame_epoch=1)
        agent.ingest_verified_world_receipt(world=world, receipt=receipt,
                                            before_view=before, split="training")

    query_world = ToolInterventionWorld(profile, seed=9999,
                                        episode_id="native-action-world",
                                        context_id="fresh-context")
    query_world.position, query_world.armed, query_world.turn = 0.2, True, 1
    query_view = query_world.agent_view()
    authorization = agent.authorize_action(
        event_id="fresh-action", episode_id="fresh-episode", context_id="fresh-context",
        coordinates=query_view["coordinates"],
        available_actions=query_view["available_actions"])
    assert authorization is not None
    assert authorization["status"] == "authorized"
    assert authorization["action_id"] == "apply_small"
    assert authorization["action_id"] in query_view["available_actions"]
    world_receipt = query_world.apply_action(authorization["action_id"], source_epoch=3,
                                             model_epoch=2, frame_epoch=1)
    assert query_world.verify_receipt(world_receipt)
    assert world_receipt.action == authorization["action_id"]
    assert len([n for n in agent.s.nodes("QualiaActionAuthorization")
                if agent.s.node(n)["attrs"].get("event_id") == "fresh-action"]) == 1
    event = next(n for n in agent.s.nodes("ExperienceEvent")
                 if agent.s.node(n)["attrs"].get("event_id") == "fresh-action")
    projection = agent.s.neighbours(event, "uses_ousiometric_projection")
    assert len(projection) == 1
    assert all(agent.s.neighbours(feature, "derived_from_frame_projection") == projection
               for feature in agent.s.neighbours(event, "has_episode_feature"))


def test_world_receipt_must_verify_before_assimilation():
    agent = _agent()
    world = ToolInterventionWorld(FactorProfile(0.4, 0.0, 0.0, 0.0, 0.0),
                                  seed=2808, episode_id="verified-episode",
                                  context_id="verified-context")
    before = world.agent_view()
    receipt = world.apply_action("inspect", source_epoch=3, model_epoch=2, frame_epoch=1)
    result = agent.ingest_verified_world_receipt(world=world, receipt=receipt,
                                                  before_view=before, split="training")
    assert result.verified is True
    assert agent.s.neighbours(result.projection_node, "retains_source") == [result.raw_node]
    agent.learner.settle()
    assert len([node for node in agent.s.nodes("CommonTargetEvidence")
                if agent.s.node(node)["attrs"].get("event_id", "").startswith(receipt.event_id)]) == 3

    from dataclasses import replace
    forged = replace(receipt, action="apply_large")
    with pytest.raises(ValueError, match="verification"):
        agent.ingest_verified_world_receipt(world=world, receipt=forged,
                                            before_view=before, split="training")

