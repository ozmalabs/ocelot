import json
from pathlib import Path

import pytest

from domains.humanoid_kinematics_study import (
    add_kinematic_receipt_points,
    install_opaque_kinematic_topology,
    summarize_kinematics_study,
    update_kinematic_coordinates,
)
from substrate.world_adapter import WorldAdapter
from scripts.gen_humanoid_adaptation_seed import Count
from scripts.gen_humanoid_kinematics_study_seed import (
    kinematic_reprobe_candidates,
)


ROOT = Path(__file__).resolve().parents[1]


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target, {})


def _observation(
    point_3_x,
    joint_position=None,
    joint_ordinal=0,
    joint_index=3,
):
    if joint_position is None:
        joint_position = point_3_x
    return {
        "base_position": (0.0, 0.0, 1.0),
        "base_orientation_xyzw": (0.0, 0.0, 0.0, 1.0),
        "links": (
            {"index": 0, "link_frame_position": (0.0, 0.0, 1.0)},
            {"index": 1, "link_frame_position": (0.0, 0.0, 1.2)},
            {"index": 2, "link_frame_position": (0.0, 0.2, 1.0)},
            {"index": 3, "link_frame_position": (point_3_x, 0.0, 1.3)},
        ),
        "joints": ({
            "ordinal": joint_ordinal,
            "index": joint_index,
            "position": joint_position,
            "velocity": 0.0,
        },),
        "last_actuator_tokens": ("opaque_1",),
    }


def _study_agent():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_kinematics_study",
    ))
    episode = agent.s.add_node("HumanoidEpisode", {
        "kinematics_study_active": 0.0,
        "phase": "motor_babble",
        "support_sensor_count": 2.0,
        "physics_time_step": 1.0,
        "kinematic_reach_target_mode": "nearest_learned_affordance",
        "kinematic_reach_goal_id": 0.0,
        "kinematic_reach_primary_initialized": 0.0,
        "kinematic_reach_secondary_initialized": 0.0,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    action = agent.s.add_node("HumanoidActionModel", {
        "token": "opaque_1",
        "ordinal": 1.0,
        "actuator_group": 0.0,
    })
    _edge(agent, episode, "has_humanoid_action_model", action)
    phases = []
    for support_phase in (0.0, 1.0):
        phase = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": "opaque_1",
            "ordinal": 1.0,
            "support_phase": support_phase,
            "actuator_group": 0.0,
        })
        _edge(agent, episode, "has_humanoid_phase_action_model", phase)
        _edge(
            agent,
            phase,
            "generalizes_humanoid_action_model",
            action,
        )
        phases.append(phase)
    signature = (
        ("body", 4, 1, 1),
        ("link", 0, -1, 4),
        ("link", 1, 0, 4),
        ("link", 2, 0, 4),
        ("link", 3, 1, 0),
        ("actuator", 0, 3, 1, 1, 0, 1, 0, 1),
        ("support", 0, 2),
    )
    terminal_count = install_opaque_kinematic_topology(
        agent,
        episode,
        signature,
    )
    return agent, episode, action, phases, terminal_count


def _receipt(
    agent,
    episode,
    action,
    *,
    request_seq,
    before_x,
    after_x,
    joint_ordinal=0,
):
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": float(request_seq),
        "response_frames": 2.0,
        "support_phase": 0.0,
        "bundle_member_count": 1.0,
        "decision_kind": "motor_babble",
    })
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "uses_humanoid_action_model", action)
    add_kinematic_receipt_points(
        agent,
        episode,
        trial,
        _observation(
            before_x,
            joint_ordinal=joint_ordinal,
            joint_index=3 if joint_ordinal == 0 else 4,
        ),
        _observation(
            after_x,
            joint_ordinal=joint_ordinal,
            joint_index=3 if joint_ordinal == 0 else 4,
        ),
        request_seq=request_seq,
        receipt_verified=True,
        external_event_frames=0,
    )
    agent.tick()
    return trial


def test_seed_is_graph_native_paired_prequential_study():
    seed = json.loads(
        (ROOT / "seeds" / "humanoid_kinematics_study.json").read_text()
    )
    text = json.dumps(seed)
    assert seed["depends_on"] == ["humanoid_adaptation"]
    assert "hks_measure_paired_prequential_kinematic_error" in text
    assert "HumanoidGlobalKinematicModel" in text
    assert "HumanoidPhaseKinematicModel" in text
    assert "Jacobian" not in text


def test_topology_infers_terminals_and_mints_paired_models():
    agent, _, _, phases, terminal_count = _study_agent()
    assert terminal_count == 2
    assert len(agent.s.nodes("HumanoidGlobalKinematicModel")) == 2
    assert len(agent.s.nodes("HumanoidPhaseKinematicModel")) == (
        terminal_count * len(phases)
    )
    assert len(agent.s.nodes("HumanoidKinematicCoordinate")) == 1
    assert len(agent.s.nodes("HumanoidKinematicArbitrationModel")) == (
        terminal_count * len(phases) * 2
    )


def test_receipts_are_scored_before_graph_model_update():
    agent, episode, action, _, _ = _study_agent()
    first = _receipt(
        agent,
        episode,
        action,
        request_seq=1,
        before_x=0.0,
        after_x=0.2,
    )
    first_point = next(
        transition
        for transition in agent.inner.neighbours(
            first,
            "has_humanoid_kinematic_transition",
        )
        if agent.s.node(transition)["attrs"]["point_ordinal"] == 3.0
    )
    first_attrs = agent.s.node(first_point)["attrs"]
    assert first_attrs["prediction_measured"] == 1.0
    assert first_attrs["global_prediction_error"] == pytest.approx(0.2)
    assert first_attrs["phase_prediction_error"] == pytest.approx(0.2)
    assert first_attrs["arbitration_measured"] == 1.0
    assert first_attrs["selected_approach_ordinal"] == 0.0
    phase_anchor = next(
        agent.s.node(model)["attrs"]
        for model in agent.s.nodes("HumanoidPhaseKinematicModel")
        if agent.s.node(model)["attrs"].get("point_ordinal") == 3.0
        and agent.s.node(model)["attrs"].get("support_phase") == 0.0
    )
    assert phase_anchor["coordinate_anchor_initialized"] == 1.0

    second = _receipt(
        agent,
        episode,
        action,
        request_seq=2,
        before_x=0.0,
        after_x=0.2,
    )
    second_point = next(
        transition
        for transition in agent.inner.neighbours(
            second,
            "has_humanoid_kinematic_transition",
        )
        if agent.s.node(transition)["attrs"]["point_ordinal"] == 3.0
    )
    second_attrs = agent.s.node(second_point)["attrs"]
    assert second_attrs["global_prediction_error"] == pytest.approx(0.0)
    assert second_attrs["phase_prediction_error"] == pytest.approx(0.0)
    assert second_attrs["arbitrated_prediction_error"] == pytest.approx(0.0)

    summary = summarize_kinematics_study(agent, 1.0)
    assert summary["terminal_point_count"] == 2
    assert summary["measured_point_receipt_count"] == 4


def test_observed_synergy_is_eligible_for_body_derived_reprobe():
    agent, episode, _, _, _ = _study_agent()
    synergy = agent.s.add_node("HumanoidSynergyModel", {
        "token_a": "opaque_1",
        "token_b": "opaque_2",
        "experience_count": 1.0,
    })
    _edge(agent, episode, "has_humanoid_synergy_model", synergy)
    agent.tick()
    assert len(agent.inner.neighbours(
        synergy,
        "has_humanoid_synergy_kinematic_model",
    )) == 2
    count = agent.inner.evaluate(
        Count(kinematic_reprobe_candidates()),
        {"episode": episode},
    )
    assert count == 1


def test_learned_forward_model_is_inverted_for_endpoint_reach():
    agent, episode, action, _, _ = _study_agent()
    _receipt(
        agent,
        episode,
        action,
        request_seq=1,
        before_x=0.0,
        after_x=0.2,
    )
    for key, value in {
        "phase": "kinematic_reach",
        "current_support_phase": 0.0,
        "response_frames": 2.0,
        "action_ready": 0.0,
        "kinematic_reach_initialized": 0.0,
        "kinematic_reach_complete": 0.0,
        "kinematic_reach_direction_dx": 1.0,
        "kinematic_reach_direction_dy": 0.0,
        "kinematic_reach_direction_dz": 0.0,
        "kinematic_reach_achieved_dx": 0.0,
        "kinematic_reach_achieved_dy": 0.0,
        "kinematic_reach_achieved_dz": 0.0,
        "kinematic_reach_last_receipt_seq": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["kinematic_reach_initialized"] == 1.0
    assert attrs["kinematic_reach_point_ordinal"] == 3.0
    assert attrs["kinematic_reach_target_dx"] == pytest.approx(0.2)
    assert attrs["decision_kind"] == "kinematic_reach"
    assert attrs["selected_token"] == "opaque_1"
    assert attrs["selected_secondary_token"] == "opaque_1"
    assert attrs["action_ready"] == 1.0


def test_inverse_prediction_tracks_remaining_opaque_joint_coordinate():
    agent, episode, action, _, _ = _study_agent()
    _receipt(
        agent,
        episode,
        action,
        request_seq=1,
        before_x=0.0,
        after_x=0.2,
    )
    update_kinematic_coordinates(
        agent,
        episode,
        _observation(0.2, joint_position=0.2),
        state_seq=3,
    )
    for key, value in {
        "phase": "kinematic_reach",
        "current_support_phase": 0.0,
        "response_frames": 2.0,
        "action_ready": 0.0,
        "kinematic_reach_initialized": 0.0,
        "kinematic_reach_complete": 0.0,
        "kinematic_reach_direction_dx": 1.0,
        "kinematic_reach_direction_dy": 0.0,
        "kinematic_reach_direction_dz": 0.0,
        "kinematic_reach_achieved_dx": 0.0,
        "kinematic_reach_achieved_dy": 0.0,
        "kinematic_reach_achieved_dz": 0.0,
        "kinematic_reach_last_receipt_seq": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["kinematic_reach_target_dx"] == pytest.approx(0.0)
    assert attrs["kinematic_reach_selected_predicted_dx"] == pytest.approx(
        0.0
    )


def test_graph_constructs_goal_from_two_distinct_learned_affordances():
    agent, episode, first_action, _, _ = _study_agent()
    _receipt(
        agent,
        episode,
        first_action,
        request_seq=1,
        before_x=0.0,
        after_x=0.2,
    )
    second_action = agent.s.add_node("HumanoidActionModel", {
        "token": "opaque_2",
        "ordinal": 2.0,
        "actuator_group": 1.0,
    })
    _edge(agent, episode, "has_humanoid_action_model", second_action)
    for support_phase in (0.0, 1.0):
        phase = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": "opaque_2",
            "ordinal": 2.0,
            "support_phase": support_phase,
            "actuator_group": 1.0,
        })
        _edge(agent, episode, "has_humanoid_phase_action_model", phase)
        _edge(
            agent,
            phase,
            "generalizes_humanoid_action_model",
            second_action,
        )
    coordinate = agent.s.add_node("HumanoidKinematicCoordinate", {
        "ordinal": 1.0,
        "joint_index": 4.0,
        "position": 0.0,
        "velocity": 0.0,
        "state_seq": 0.0,
    })
    _edge(
        agent,
        episode,
        "has_humanoid_kinematic_coordinate",
        coordinate,
    )
    agent.tick()
    _receipt(
        agent,
        episode,
        second_action,
        request_seq=2,
        before_x=0.0,
        after_x=0.1,
        joint_ordinal=1,
    )
    for key, value in {
        "phase": "kinematic_reach",
        "current_support_phase": 0.0,
        "response_frames": 2.0,
        "action_ready": 0.0,
        "kinematic_reach_target_mode": (
            "composition_of_distinct_learned_affordances"
        ),
        "kinematic_reach_initialized": 0.0,
        "kinematic_reach_primary_initialized": 0.0,
        "kinematic_reach_secondary_initialized": 0.0,
        "kinematic_reach_complete": 0.0,
        "kinematic_reach_direction_dx": 1.0,
        "kinematic_reach_direction_dy": 0.0,
        "kinematic_reach_direction_dz": 0.0,
        "kinematic_reach_achieved_dx": 0.0,
        "kinematic_reach_achieved_dy": 0.0,
        "kinematic_reach_achieved_dz": 0.0,
        "kinematic_reach_last_receipt_seq": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["kinematic_reach_initialized"] == 1.0
    assert {
        attrs["kinematic_reach_basis_token_a"],
        attrs["kinematic_reach_basis_token_b"],
    } == {"opaque_1", "opaque_2"}
    assert attrs["kinematic_reach_target_dx"] == pytest.approx(0.3)
    assert attrs["kinematic_reach_success_threshold"] == pytest.approx(0.05)
