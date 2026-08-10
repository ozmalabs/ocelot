import json
from pathlib import Path

import pytest

from domains.embodied_graph_transducer import enact_graph_force_request
from domains.pybullet_humanoid_world import (
    HumanoidBodyConfiguration,
    PyBulletHumanoidWorld,
)
from scripts.jabberwock_humanoid_walk import (
    _motor_library_snapshot,
    _restore_motor_library,
)
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target, {})


def _episode(agent):
    episode = agent.s.add_node("HumanoidEpisode", {
        "mode": "directed_walk",
        "phase": "locomotion",
        "curriculum_active": 1.0,
        "evaluation_active": 1.0,
        "recovery_mode": 0.0,
        "upright": 1.0,
        "state_is_receipt": 1.0,
        "request_seq": 20.0,
        "decision_seq": 20.0,
        "curriculum_last_request_seq": 0.0,
        "curriculum_last_challenge_cycle_count": 0.0,
        "curriculum_pending_baseline_directed_progress": 0.0,
        "curriculum_pending_baseline_cycle_count": 0.0,
        "curriculum_challenge_request_seq": 0.0,
        "curriculum_challenge_applied_seq": 0.0,
        "curriculum_recovery_pending": 0.0,
        "curriculum_pending_recovery_request_seq": 0.0,
        "curriculum_stage_ordinal": 0.0,
        "curriculum_external_impulse_authority": 1.0,
        "self_takeoff_drive_active": 0.0,
        "self_takeoff_target_velocity_scale": 0.0,
        "self_takeoff_compression_scale": 0.0,
        "response_frames": 18.0,
        "support_sensor_count": 2.0,
        "active_support_count": 1.0,
        "state_linear_momentum_z": 0.0,
        "locomotor_cycle_count": 1.0,
        "directed_progress": 0.1,
        "standing_reference_z": 1.2,
        "body_mass": 50.0,
        "physics_time_step": 1.0 / 240.0,
        "action_ready": 1.0,
        "state_seq": 1.0,
        "measured_state_seq": 1.0,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    return episode


def test_curriculum_is_graph_native_and_uses_core_curiosity():
    seed = json.loads(
        (ROOT / "seeds" / "humanoid_coordination_curriculum.json").read_text()
    )
    text = json.dumps(seed)
    assert seed["depends_on"] == ["humanoid_adaptation"]
    assert len(seed["nodes"]) == 14
    assert "EvalSubgraph" in text
    assert "action_score_term" in text
    assert "support_phase_prior_strength" in text
    assert "difficulty_scale" in text
    assert "unsafe_receipt_count" in text
    landing_nodes = [
        row for row in seed["nodes"]
        if row["attrs"]["family"] == "ballistic_landing"
    ]
    assert [row["attrs"]["name"] for row in landing_nodes] == [
        "vertical_landing",
        "forward_landing",
        "left_landing",
        "right_landing",
    ]
    assert [row["attrs"]["authorized"] for row in landing_nodes] == [
        0.0,
        0.0,
        0.0,
        0.0,
    ]
    assert [
        row["attrs"]["prerequisite_name"] for row in landing_nodes
    ] == [
        "unload",
        "vertical_landing",
        "vertical_landing",
        "vertical_landing",
    ]
    takeoff = next(
        row for row in seed["nodes"]
        if row["attrs"]["family"] == "self_takeoff"
    )
    assert takeoff["attrs"]["external_impulse_authority"] == 0.0
    assert takeoff["attrs"]["prerequisite_name"] == "vertical_landing"


def test_ballistic_stages_unlock_from_graph_learned_safe_envelopes():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    challenges = {
        agent.s.node(node)["attrs"]["name"]: node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
    }
    unload = challenges["unload"]
    vertical = challenges["vertical_landing"]
    forward = challenges["forward_landing"]
    left = challenges["left_landing"]
    right = challenges["right_landing"]
    takeoff = challenges["self_takeoff"]
    agent.inner.set_attr(unload, "largest_safe_scale", 0.75)
    agent.inner.set_attr(unload, "success_count", 2.0)
    agent.tick()

    vertical_attrs = agent.s.node(vertical)["attrs"]
    assert vertical_attrs["authorized"] == 1.0
    assert vertical_attrs["difficulty_scale"] == pytest.approx(0.75)
    assert agent.s.node(forward)["attrs"]["authorized"] == 0.0
    assert agent.s.node(episode)["attrs"]["curriculum_stage_ordinal"] == 1.0

    agent.inner.set_attr(vertical, "largest_safe_scale", 0.625)
    agent.inner.set_attr(vertical, "success_count", 2.0)
    agent.tick()
    forward_attrs = agent.s.node(forward)["attrs"]
    assert forward_attrs["authorized"] == 1.0
    assert forward_attrs["difficulty_scale"] == pytest.approx(0.625)
    assert agent.s.node(left)["attrs"]["authorized"] == 1.0
    assert agent.s.node(right)["attrs"]["authorized"] == 1.0

    takeoff_attrs = agent.s.node(takeoff)["attrs"]
    assert takeoff_attrs["authorized"] == 1.0
    assert takeoff_attrs["difficulty_scale"] == pytest.approx(0.625)
    assert agent.s.node(episode)["attrs"]["curriculum_stage_ordinal"] == 3.0


def test_ballistic_receipt_requires_airborne_before_touchdown():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    vertical = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["name"] == "vertical_landing"
    )
    agent.inner.set_attr(vertical, "pending_recovery", 1.0)
    agent.inner.set_attr(vertical, "active_request_seq", 20.0)
    agent.inner.set_attr(
        episode,
        "curriculum_pending_recovery_request_seq",
        20.0,
    )
    agent.inner.set_attr(episode, "curriculum_recovery_pending", 1.0)

    # Contact without a preceding aerial interval is not a landing.
    agent.tick()
    attrs = agent.s.node(vertical)["attrs"]
    assert attrs["airborne_observed"] == 0.0
    assert attrs["touchdown_observed"] == 0.0

    agent.inner.set_attr(episode, "active_support_count", 0.0)
    agent.tick()
    attrs = agent.s.node(vertical)["attrs"]
    assert attrs["airborne_observed"] == 1.0
    assert attrs["touchdown_observed"] == 0.0

    agent.inner.set_attr(episode, "active_support_count", 1.0)
    agent.tick()
    attrs = agent.s.node(vertical)["attrs"]
    assert attrs["airborne_observed"] == 1.0
    assert attrs["touchdown_observed"] == 1.0


def test_self_takeoff_opens_vertical_motor_residual_without_external_force():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    challenges = {
        agent.s.node(node)["attrs"]["name"]: node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
    }
    vertical = challenges["vertical_landing"]
    takeoff = challenges["self_takeoff"]
    agent.inner.set_attr(vertical, "largest_safe_scale", 0.5)
    agent.inner.set_attr(vertical, "success_count", 2.0)
    for name, challenge in challenges.items():
        if name != "self_takeoff":
            agent.inner.set_attr(challenge, "unsafe_receipt_count", 1.0)
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 21.0,
        "motor_task_context": "locomotion",
    })
    program = agent.s.add_node("HumanoidMotorProgram", {
        "motor_task_context": "locomotion",
    })
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "enacts_humanoid_motor_program", program)
    agent.tick()

    episode_attrs = agent.s.node(episode)["attrs"]
    assert agent.s.node(takeoff)["attrs"]["authorized"] == 1.0
    assert episode_attrs["curriculum_active_challenge_ordinal"] == 13.0
    assert episode_attrs["curriculum_external_impulse_authority"] == 0.0
    assert episode_attrs["self_takeoff_drive_active"] == 1.0
    assert episode_attrs["self_takeoff_target_velocity_scale"] == 0.5
    assert episode_attrs["curriculum_force_x_body_weights"] == 0.0
    assert episode_attrs["curriculum_force_y_body_weights"] == 0.0
    assert episode_attrs["curriculum_force_z_body_weights"] == 0.0
    assert agent.s.node(trial)["attrs"]["motor_task_context"] == "self_takeoff"
    assert agent.s.node(program)["attrs"]["motor_task_context"] == "self_takeoff"


def test_self_takeoff_requires_upward_whole_body_momentum_at_support_loss():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    takeoff = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["name"] == "self_takeoff"
    )
    agent.inner.set_attr(takeoff, "pending_recovery", 1.0)
    agent.inner.set_attr(takeoff, "active_request_seq", 20.0)
    agent.inner.set_attr(
        episode,
        "curriculum_pending_recovery_request_seq",
        20.0,
    )
    agent.inner.set_attr(episode, "curriculum_recovery_pending", 1.0)
    agent.inner.set_attr(episode, "active_support_count", 0.0)
    agent.inner.set_attr(episode, "state_linear_momentum_z", -1.0)
    agent.inner.set_attr(episode, "state_seq", 2.0)
    agent.tick()
    assert agent.s.node(takeoff)["attrs"]["airborne_observed"] == 0.0

    agent.inner.set_attr(episode, "state_linear_momentum_z", 1.0)
    agent.inner.set_attr(episode, "state_seq", 3.0)
    agent.tick()
    assert agent.s.node(takeoff)["attrs"]["airborne_observed"] == 1.0


def test_underpowered_takeoff_releases_actuators_before_recovery_verdict():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    policy = agent.s.nodes("HumanoidPolicy")[0]
    episode = _episode(agent)
    takeoff = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["name"] == "self_takeoff"
    )
    prior_strength = agent.s.node(policy)["attrs"][
        "support_phase_prior_strength"
    ]
    pending_seq = 20.0
    for key, value in {
        "pending_recovery": 1.0,
        "active_request_seq": pending_seq,
        "airborne_observed": 0.0,
    }.items():
        agent.inner.set_attr(takeoff, key, value)
    for key, value in {
        "curriculum_active": 1.0,
        "curriculum_recovery_pending": 1.0,
        "curriculum_pending_recovery_request_seq": pending_seq,
        "self_takeoff_drive_active": 1.0,
        "request_seq": pending_seq + prior_strength,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    # The challenge remains open for a graph-native recovery verdict, while
    # its expired ballistic residual no longer pre-empts balance control.
    assert agent.s.node(takeoff)["attrs"]["pending_recovery"] == 1.0
    assert agent.s.node(episode)["attrs"]["curriculum_recovery_pending"] == 1.0
    assert agent.s.node(episode)["attrs"]["self_takeoff_drive_active"] == 0.0


def test_self_takeoff_accumulates_height_and_duration_once_per_state():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    takeoff = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["name"] == "self_takeoff"
    )
    for key, value in (
        ("pending_recovery", 1.0),
        ("active_request_seq", 20.0),
        ("takeoff_baseline_z", 1.2),
        ("takeoff_target_height_gain", 0.01),
        ("takeoff_last_observed_state_seq", 1.0),
    ):
        agent.inner.set_attr(takeoff, key, value)
    agent.inner.set_attr(
        episode,
        "curriculum_pending_recovery_request_seq",
        20.0,
    )
    agent.inner.set_attr(episode, "curriculum_recovery_pending", 1.0)
    agent.inner.set_attr(episode, "active_support_count", 0.0)
    agent.inner.set_attr(episode, "state_linear_momentum_z", 1.0)
    agent.inner.set_attr(episode, "state_com_z", 1.21)
    agent.inner.set_attr(episode, "state_seq", 2.0)
    agent.tick()
    first = agent.s.node(takeoff)["attrs"]
    assert first["takeoff_aerial_receipt_count"] == 1.0
    assert first["takeoff_peak_height_gain"] == pytest.approx(0.01)

    # A graph fixpoint cannot manufacture another duration receipt.
    agent.tick()
    assert (
        agent.s.node(takeoff)["attrs"]["takeoff_aerial_receipt_count"]
        == 1.0
    )
    agent.inner.set_attr(episode, "state_com_z", 1.215)
    agent.inner.set_attr(episode, "state_seq", 3.0)
    agent.tick()
    final = agent.s.node(takeoff)["attrs"]
    assert final["takeoff_aerial_receipt_count"] == 2.0
    assert final["takeoff_peak_height_gain"] == pytest.approx(0.015)


def test_jump_schema_is_replayable_only_after_whole_trajectory_recovery():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    takeoff = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["name"] == "self_takeoff"
    )
    for key, value in {
        "pending_recovery": 1.0,
        "active_request_seq": 20.0,
        "airborne_observed": 1.0,
        "touchdown_observed": 1.0,
        "takeoff_peak_height_gain": 0.02,
        "takeoff_target_height_gain": 0.01,
        "takeoff_aerial_receipt_count": 2.0,
    }.items():
        agent.inner.set_attr(takeoff, key, value)
    for key, value in {
        "curriculum_pending_recovery_request_seq": 20.0,
        "curriculum_recovery_pending": 1.0,
        "request_seq": 40.0,
        "locomotor_cycle_count": 2.0,
        "directed_progress": 0.1,
    }.items():
        agent.inner.set_attr(episode, key, value)
    transition = agent.s.add_node("HumanoidMotorTransition", {
        "ordinal": 1.0,
        "motor_task_context": "self_takeoff",
        "from_program_ordinal": 1.0,
        "next_program_ordinal": 2.0,
        "task_request_seq": 20.0,
        "trajectory_verified": 0.0,
        "from_task_phase": "launch",
        "next_task_phase": "flight",
    })
    _edge(
        agent,
        episode,
        "has_humanoid_motor_transition",
        transition,
    )
    shape = agent.s.add_node("HumanoidBodyShapeSignature", {
        "name": "developmental_jump_shape",
    })
    previous = agent.s.add_node("HumanoidMotorProgram", {
        "ordinal": 1.0,
        "motor_task_context": "self_takeoff",
        "member_count": 2.0,
        "memory_eligible": 1.0,
        "mean_directed_advance": 1.0,
        "warm_start_requires_verification": 0.0,
    })
    memory = agent.s.add_node("HumanoidMotorProgram", {
        "ordinal": 2.0,
        "motor_task_context": "self_takeoff",
        "member_count": 2.0,
        "memory_eligible": 1.0,
        "mean_directed_advance": 1.0,
        "warm_start_requires_verification": 0.0,
    })
    _edge(agent, agent.agent, "has_humanoid_body_shape_library", shape)
    _edge(agent, episode, "recognizes_humanoid_body_shape", shape)
    _edge(agent, shape, "stores_humanoid_motor_program", previous)
    _edge(agent, shape, "stores_humanoid_motor_program", memory)
    _edge(agent, previous, "has_humanoid_motor_transition", transition)
    _edge(
        agent,
        transition,
        "continues_with_humanoid_motor_program",
        memory,
    )

    agent.tick()

    attrs = agent.s.node(transition)["attrs"]
    assert attrs["trajectory_verified"] == 1.0
    assert attrs["jump_schema_id"] == 20.0
    for endpoint in (previous, memory):
        endpoint_attrs = agent.s.node(endpoint)["attrs"]
        assert endpoint_attrs["trajectory_verified"] == 1.0
        assert endpoint_attrs["jump_schema_id"] == 20.0
    assert agent.s.node(takeoff)["attrs"]["pending_recovery"] == 0.0
    agent.tick()
    assert agent.inner.neighbours(
        shape,
        "stores_humanoid_motor_transition",
    ) == [transition]
    snapshot = _motor_library_snapshot(agent)
    stored = next(
        row
        for row in snapshot["body_shapes"]
        if row["attrs"]["name"] == "developmental_jump_shape"
    )
    assert stored["motor_transitions"][0]["attrs"][
        "trajectory_verified"
    ] == 1.0
    restored_agent = WorldAdapter(seeds=("humanoid_adaptation",))
    restored = _restore_motor_library(restored_agent, snapshot)
    assert restored["transition_count"] == 1


def test_stable_underpowered_ballistic_trial_expands_without_unsafe_label():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    vertical = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["name"] == "vertical_landing"
    )
    agent.inner.set_attr(vertical, "pending_recovery", 1.0)
    agent.inner.set_attr(vertical, "active_request_seq", 20.0)
    agent.inner.set_attr(vertical, "active_difficulty_scale", 0.75)
    agent.inner.set_attr(
        episode,
        "curriculum_pending_recovery_request_seq",
        20.0,
    )
    agent.inner.set_attr(episode, "curriculum_recovery_pending", 1.0)
    agent.inner.set_attr(episode, "request_seq", 40.0)
    agent.inner.set_attr(episode, "locomotor_cycle_count", 2.0)
    agent.inner.set_attr(episode, "directed_progress", 0.1)
    agent.tick()

    attrs = agent.s.node(vertical)["attrs"]
    assert attrs["pending_recovery"] == 0.0
    assert attrs["unsafe_receipt_count"] == 0.0
    assert attrs["insufficient_task_count"] == 1.0
    assert attrs["difficulty_scale"] > 0.75
    assert agent.s.node(episode)["attrs"]["curriculum_recovery_pending"] == 0.0


def test_contextual_failure_clears_an_inverted_scalar_safe_floor():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    vertical = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["name"] == "vertical_landing"
    )
    agent.inner.set_attr(vertical, "pending_recovery", 1.0)
    agent.inner.set_attr(vertical, "active_request_seq", 20.0)
    agent.inner.set_attr(vertical, "active_difficulty_scale", 0.7)
    agent.inner.set_attr(vertical, "largest_safe_scale", 0.8)
    agent.inner.set_attr(vertical, "airborne_observed", 1.0)
    agent.inner.set_attr(vertical, "touchdown_observed", 1.0)
    agent.inner.set_attr(
        episode,
        "curriculum_pending_recovery_request_seq",
        20.0,
    )
    agent.inner.set_attr(episode, "curriculum_recovery_pending", 1.0)
    agent.inner.set_attr(episode, "request_seq", 40.0)
    agent.inner.set_attr(episode, "recovery_mode", 1.0)
    agent.tick()

    attrs = agent.s.node(vertical)["attrs"]
    assert attrs["unsafe_receipt_count"] == 1.0
    assert attrs["smallest_unsafe_scale"] == pytest.approx(0.7)
    assert attrs["largest_safe_scale"] == 0.0
    assert attrs["difficulty_scale"] < 0.7


def test_graph_requests_and_learns_a_challenge_receipt():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    policy = agent.s.nodes("HumanoidPolicy")[0]
    agent.inner.set_attr(policy, "support_phase_prior_strength", 9.0)
    episode = _episode(agent)
    agent.tick()

    episode_attrs = agent.s.node(episode)["attrs"]
    assert episode_attrs["curriculum_challenge_request_seq"] == 21.0
    assert episode_attrs["curriculum_active_challenge_ordinal"] == 0.0
    challenge = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["ordinal"] == 0.0
    )
    assert agent.s.node(challenge)["attrs"]["asym_count"] == 9.0

    agent.inner.set_attr(episode, "request_seq", 21.0)
    agent.inner.set_attr(
        episode,
        "curriculum_pending_baseline_directed_progress",
        0.1,
    )
    agent.inner.set_attr(
        episode,
        "curriculum_challenge_applied_seq",
        21.0,
    )
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 21.0,
    })
    outcome = agent.s.add_node("HumanoidTransition", {
        "receipt_verified": 0.0,
        "external_event_receipt_verified": 1.0,
        "curriculum_challenge_learned": 0.0,
        "post_qx": 0.0,
        "post_qy": 0.0,
        "post_qz": 0.0,
        "post_qw": 1.0,
        "post_z": 1.2,
        "post_vx": 0.01,
        "post_vy": 0.0,
        "peak_contact_force_newtons": 500.0,
    })
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "has_humanoid_transition", outcome)
    agent.tick()

    observed = agent.s.node(challenge)["attrs"]
    assert observed["sample_count"] == 1.0
    assert observed["success_count"] == 0.0
    assert observed["pending_recovery"] == 1.0
    assert agent.s.node(outcome)["attrs"]["curriculum_challenge_learned"] == 1.0

    agent.inner.set_attr(episode, "request_seq", 30.0)
    agent.inner.set_attr(episode, "state_is_receipt", 1.0)
    agent.inner.set_attr(episode, "locomotor_cycle_count", 2.0)
    agent.inner.set_attr(episode, "directed_progress", 0.11)
    agent.tick()
    learned = agent.s.node(challenge)["attrs"]
    assert learned["success_count"] == 1.0
    assert learned["pending_recovery"] == 0.0
    assert learned["difficulty_scale"] > 1.0
    assert learned["mean_recovery_cycle_gain"] == 1.0
    assert learned["mean_recovery_progress_gain"] == pytest.approx(
        (0.11 - 0.1) / 1.2
    )

    shape = agent.s.add_node("HumanoidBodyShapeSignature", {
        "name": "test_shape",
        "signature": (("body", 1, 1, 1),),
    })
    _edge(agent, agent.agent, "has_humanoid_body_shape_library", shape)
    _edge(agent, episode, "recognizes_humanoid_body_shape", shape)
    agent.inner.set_attr(episode, "library_consolidation_seq", 1.0)
    agent.inner.set_attr(episode, "library_consolidation_requested", 1.0)
    agent.tick()
    memories = agent.inner.neighbours(
        shape,
        "stores_humanoid_challenge_memory",
    )
    assert len(memories) == 1

    snapshot = _motor_library_snapshot(agent)
    assert len(
        snapshot["body_shapes"][0]["coordination_challenges"]
    ) == 1
    restored_agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    restored = _restore_motor_library(restored_agent, snapshot)
    assert restored["challenge_memory_count"] == sum(
        len(row["coordination_challenges"])
        for row in snapshot["body_shapes"]
    )


def test_mastered_takeoff_remains_eligible_for_bounded_efficiency_probes():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    policy = agent.s.nodes("HumanoidPolicy")[0]
    agent.inner.set_attr(policy, "support_phase_prior_strength", 9.0)
    episode = _episode(agent)
    takeoff = None
    for challenge in agent.s.nodes("HumanoidCoordinationChallenge"):
        attrs = agent.s.node(challenge)["attrs"]
        agent.inner.set_attr(challenge, "initialized", 1.0)
        agent.inner.set_attr(challenge, "warm_start_restored", 1.0)
        agent.inner.set_attr(challenge, "authorized", 0.0)
        if attrs["family"] == "self_takeoff":
            takeoff = challenge
    assert takeoff is not None
    for key, value in {
        "authorized": 1.0,
        "largest_safe_scale": 0.5,
        "smallest_unsafe_scale": 0.6,
        "asym_count": 0.5,
        "unsafe_receipt_count": 0.0,
        "takeoff_efficiency_probe_count": 0.0,
    }.items():
        agent.inner.set_attr(takeoff, key, value)

    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["curriculum_active_challenge_ordinal"] == 13.0
    assert attrs["self_takeoff_drive_active"] == 1.0
    assert attrs["self_takeoff_compression_scale"] == 0.0


def test_verified_takeoff_starts_a_fresh_phase_refinement_frontier():
    agent = WorldAdapter(seeds=(
        "humanoid_adaptation",
        "humanoid_coordination_curriculum",
    ))
    episode = _episode(agent)
    takeoff = next(
        node
        for node in agent.s.nodes("HumanoidCoordinationChallenge")
        if agent.s.node(node)["attrs"]["family"] == "self_takeoff"
    )
    for key, value in {
        "takeoff_efficiency_probe_count": 7.0,
        "takeoff_compression_safe_scale": 0.25,
        "takeoff_compression_unsafe_scale": 0.5,
        "takeoff_schema_refinement_initialized": 0.0,
    }.items():
        agent.inner.set_attr(takeoff, key, value)
    schema_stage = agent.s.add_node("HumanoidMotorProgram", {
        "motor_task_context": "self_takeoff",
        "trajectory_verified": 1.0,
    })
    _edge(agent, episode, "has_humanoid_motor_program", schema_stage)

    agent.tick()

    attrs = agent.s.node(takeoff)["attrs"]
    assert attrs["takeoff_schema_refinement_initialized"] == 1.0
    assert attrs["takeoff_efficiency_probe_count"] == 0.0
    assert attrs["takeoff_compression_safe_scale"] == 0.0
    assert attrs["takeoff_compression_unsafe_scale"] == 0.0


class _FakeWorld:
    def __init__(self):
        self.calls = []

    def apply_force_pulse(self, force, *, frames):
        self.calls.append((tuple(force), frames))


def test_force_boundary_only_translates_graph_request():
    agent = WorldAdapter(seeds=())
    episode = agent.s.add_node("HumanoidEpisode", {
        "request_seq": 3.0,
        "curriculum_challenge_request_seq": 3.0,
        "curriculum_challenge_applied_seq": 2.0,
        "curriculum_active_challenge_ordinal": 4.0,
        "curriculum_force_x_body_weights": 0.5,
        "curriculum_force_y_body_weights": -0.25,
        "curriculum_force_z_body_weights": 0.0,
        "curriculum_force_frames": 2.0,
    })
    world = _FakeWorld()
    receipt = enact_graph_force_request(
        agent,
        episode,
        world,
        {"body_mass": 10.0, "gravity_acceleration": 10.0},
        prefix="curriculum",
    )
    assert world.calls == [((50.0, -25.0, 0.0), 2)]
    assert receipt["challenge_ordinal"] == 4.0
    assert (
        agent.s.node(episode)["attrs"]["curriculum_challenge_applied_seq"]
        == 3.0
    )


def test_force_boundary_acknowledges_self_generated_task_without_impulse():
    agent = WorldAdapter(seeds=())
    episode = agent.s.add_node("HumanoidEpisode", {
        "request_seq": 4.0,
        "curriculum_challenge_request_seq": 4.0,
        "curriculum_challenge_applied_seq": 3.0,
        "curriculum_active_challenge_ordinal": 13.0,
        "curriculum_external_impulse_authority": 0.0,
        "curriculum_force_frames": 2.0,
    })
    world = _FakeWorld()
    receipt = enact_graph_force_request(
        agent,
        episode,
        world,
        {"body_mass": 10.0, "gravity_acceleration": 10.0},
        prefix="curriculum",
    )
    assert world.calls == []
    assert receipt["frames"] == 0
    assert receipt["challenge_ordinal"] == 13.0


def test_humanoid_world_exposes_whole_body_physics():
    pytest.importorskip("pybullet")
    configuration = HumanoidBodyConfiguration(
        time_step=1.0 / 240.0,
        gravity_acceleration=9.81,
        action_frames=1,
        settling_frames=1,
        joint_twitch_radians=0.085,
        maximum_joint_force=50.0,
        position_gain=0.3,
        velocity_gain=1.0,
    )
    with PyBulletHumanoidWorld(configuration) as world:
        observation = world.observe()
    assert len(observation["whole_body_centre_of_mass"]) == 3
    assert len(observation["whole_body_linear_momentum"]) == 3
    assert len(observation["whole_body_angular_momentum"]) == 3
    assert observation["links"]
    assert {"lower_limit", "upper_limit", "maximum_force"} <= set(
        observation["joints"][0]
    )
    assert "peak_contact_force_newtons" in observation
    if observation["contacts"]:
        assert "normal_impulse" in observation["contacts"][0]
