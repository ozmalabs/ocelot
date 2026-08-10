from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "humanoid_adaptation.json"


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def _episode(agent):
    from domains.embodied_graph_transducer import add_unchecked_edge

    episode = agent.s.add_node("HumanoidEpisode", {
        "phase": "locomotion",
        "mode": "developmental",
        "evaluation_active": 1,
        "developmental_curriculum_active": 1,
        "locomotion_drive_active": 1,
        "developmental_goal": "supported_translation",
        "state_seq": 1,
        "measured_state_seq": 0,
        "state_z": 0.2,
        "standing_reference_z": 1.0,
        "state_qx": 0.70710678,
        "state_qy": 0.0,
        "state_qz": 0.0,
        "state_qw": 0.70710678,
        "learned_gait_tilt_envelope": 0.1,
        "learned_gait_mean_tilt": 0.05,
        "learned_gait_prediction_error_envelope": 1.0,
        "gait_surprise_streak": 0,
        "recovery_mode": 0,
        "action_ready": 1,
        "state_is_receipt": 0,
        "body_reset_seq": 0,
        "body_reset_processed_seq": 0,
    })
    add_unchecked_edge(
        agent,
        agent.agent,
        "has_humanoid_episode",
        episode,
    )
    return episode


def test_situated_context_owns_trajectory_without_minting_a_pose_target():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    opener = _rule(
        seed,
        "ha_open_intentional_situated_locomotion_context",
    )
    attrs = next(
        effect[3]
        for effect in opener["effects"]
        if effect[:3] == [
            "add_node",
            "context",
            "HumanoidSituatedLocomotionContext",
        ]
    )

    assert seed["version"] == "1.6.0"
    assert attrs["trajectory_ownership"] == 1
    assert attrs["pose_target_authority"] == 0
    assert attrs["material_limit_authority"] == 1
    assert all(
        isinstance(attrs[key], int)
        for key in (
            "trajectory_ownership",
            "pose_target_authority",
            "material_limit_authority",
        )
    )
    assert not {
        "reference_z_x",
        "reference_z_y",
        "reference_z",
        "minimum_viable_z",
        "maximum_axis_departure",
    } & attrs.keys()
    assert any(
        production["edge_type"]
        == "has_current_humanoid_situated_locomotion_context"
        for production in seed["productions"]
    )

    chooser = json.dumps(
        _rule(seed, "ha_choose_learned_walking_twitch")
    )
    selector = json.dumps(
        _rule(seed, "ha_select_pareto_persistent_residual_regime")
    )
    interrupt = json.dumps(
        _rule(seed, "ha_measure_gait_prediction_error_and_interrupt")
    )
    assert "has_current_humanoid_situated_locomotion_context" in chooser
    assert "has_current_humanoid_situated_locomotion_context" in selector
    assert "mean_tilt" in selector
    assert "mean_height_deficit" in selector
    assert "sensorimotor_interrupt_required" in interrupt
    assert "reset_requested" in interrupt


def test_owned_non_upright_trajectory_does_not_recruit_pose_recovery():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    episode = _episode(agent)
    agent.tick()

    contexts = agent.inner.neighbours(
        episode,
        "has_current_humanoid_situated_locomotion_context",
    )
    attrs = agent.s.node(episode)["attrs"]
    context_attrs = agent.s.node(contexts[0])["attrs"]
    assert len(contexts) == 1
    assert attrs["upright"] == 0.0
    assert attrs["recovery_mode"] == 0.0
    assert attrs["situated_locomotion_context_active"] == 1
    assert context_attrs["trajectory_ownership"] == 1
    assert context_attrs["pose_target_authority"] == 0


def test_owned_trajectory_cannot_waive_hard_sensorimotor_interrupt():
    from domains.embodied_graph_transducer import add_unchecked_edge
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    episode = _episode(agent)
    agent.tick()
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "decision_kind": "learned_walk",
        "motor_task_context": "locomotion",
        "predicted_dvx": 0.0,
        "predicted_dvy": 0.0,
        "predicted_dvz": 0.0,
    })
    outcome = agent.s.add_node("HumanoidMotorTransition", {
        "receipt_verified": 1,
        "prediction_error_measured": 0,
        "pre_vx": 0.0,
        "post_vx": 0.0,
        "pre_vy": 0.0,
        "post_vy": 0.0,
        "pre_vz": 0.0,
        "post_vz": 0.0,
        "sensorimotor_interrupt_required": 1,
    })
    add_unchecked_edge(
        agent,
        episode,
        "has_humanoid_motor_trial",
        trial,
    )
    add_unchecked_edge(
        agent,
        trial,
        "has_humanoid_transition",
        outcome,
    )

    agent.tick()

    assert agent.s.node(episode)["attrs"]["recovery_mode"] == 1.0
    assert agent.s.node(outcome)["attrs"]["prediction_error_measured"] == 1.0
