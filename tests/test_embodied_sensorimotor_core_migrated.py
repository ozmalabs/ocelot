"""Executable gates for the shared biological sensorimotor stack."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from domains.sensorimotor_transducer import (
    SensorimotorSensorConfiguration,
    SensorimotorTransducer,
)
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _nodes(agent, node_type):
    return [
        node
        for node in agent.s.nodes()
        if agent.s.node(node)["type"] == node_type
    ]


def _fresh():
    return WorldAdapter(seeds=("embodied_motor_priors",))


def _fixture():
    agent = _fresh()
    episode = agent.s.add_node("EmbodiedEpisode", {
        "phase": "locomotion",
        "body_mass": 2.0,
        "gravity_acceleration": 9.81,
        "state_available_energy_joules": 100.0,
        "state_maximum_power_watts": 20.0,
        "state_thermal_capacity_joules": 20.0,
        "locomotor_prior_reset_seq": 0.0,
        "recovery_mode": 0.0,
        "has_sensor_state": 1.0,
        "sensor_requires_inference": 1.0,
        "state_seq": 1.0,
    })
    model = agent.s.add_node("ActionModel", {
        "token": "opaque_effector",
    })
    _edge(agent, agent.agent, "has_embodied_episode", episode)
    _edge(agent, episode, "has_action_model", model)
    agent.tick()
    return agent, episode, model


def _motor_receipt(
    agent,
    episode,
    model,
    *,
    epoch,
    pre_x,
    post_x,
    sensed_post_x,
    task_progress=0.25,
    contact=1.0,
    angular_velocity=0.0,
):
    trial = agent.s.add_node("MotorTrial", {
        "epoch": float(epoch),
        "token": "opaque_effector",
        "response_frames": 1.0,
        "status": "issued",
    })
    _edge(agent, episode, "has_motor_trial", trial)
    _edge(agent, trial, "uses_action_model", model)
    # The decision, efference copy, prediction and eligibility trace must exist
    # before the world receipt is attached.
    agent.tick()

    decision = list(
        agent.inner.neighbours(trial, "has_adaptive_decision")
    )
    assert len(decision) == 1
    assert agent.s.node(decision[0])["attrs"]["status"] == "committed"

    outcome = agent.s.add_node("TransitionObservation", {
        "pre_x": float(pre_x),
        "pre_y": 0.0,
        "pre_z": 0.5,
        "post_x": float(post_x),
        "post_y": 0.0,
        "post_z": 0.5,
        "pre_vx": 0.0,
        "pre_vy": 0.0,
        "pre_vz": 0.0,
        "post_vx": 0.2,
        "post_vy": 0.0,
        "post_vz": 0.0,
        "pre_wx": float(angular_velocity),
        "pre_wy": 0.0,
        "pre_wz": 0.0,
        "post_wx": float(angular_velocity),
        "post_wy": 0.0,
        "post_wz": 0.0,
        "has_sensor_sample": 1.0,
        "sensed_post_x": float(sensed_post_x),
        "sensed_post_y": 0.0,
        "sensed_post_z": 0.5,
        "sensed_post_vx": 0.2,
        "sensed_post_vy": 0.0,
        "sensed_post_vz": 0.0,
        "sensed_post_wx": float(angular_velocity),
        "sensed_post_wy": 0.0,
        "sensed_post_wz": 0.0,
        "sensed_pre_contact_count": float(contact),
        "sensed_contact_count": float(contact),
        "sensor_position_variance": 0.04,
        "sensor_velocity_variance": 0.02,
        "sensor_angular_variance": 0.01,
        "sensor_contact_variance": 0.01,
        "sensor_sample_period_seconds": 0.01,
        "sensor_latency_seconds": 0.02,
        "actuator_activation_seconds": 0.01,
        "pre_contact_count": float(contact),
        "contact_count": float(contact),
        "input_energy_joules": 1.0,
        "absorbed_energy_joules": 0.1,
        "recovered_energy_joules": 0.05,
        "peak_power_watts": 4.0,
        "thermal_load_joules": 0.1,
        "action_duration_seconds": 0.1,
        "world_step_index": float(epoch * 10),
        "has_motor_epoch": 1.0,
        "motor_epoch": float(epoch),
        "energetic_window_seq": 0.0,
        "task_progress": float(task_progress),
        "receipt_verified": 1.0,
        "processed": 0.0,
    })
    _edge(agent, trial, "has_transition_outcome", outcome)
    agent.tick()
    return trial, outcome, decision[0]


def test_manifest_reuses_existing_adaptive_and_default_mode_cores():
    manifest = json.loads(
        (ROOT / "seeds" / "embodied_sensorimotor_core.json").read_text()
    )
    assert manifest["depends_on"] == [
        "adaptive_control_core",
        "default_mode_core",
    ]
    names = {rule["name"] for rule in manifest["rules"]}
    assert {
        "esm_integrate_delayed_multimodal_receipt",
        "esm_bridge_motor_trial_to_adaptive_decision",
        "esm_learn_actuator_plant_envelope",
        "esm_forecast_motor_allostatic_reserve",
        "esm_publish_body_belief_to_generative_world_model",
        "esm_integrate_default_mode_motor_replay",
        "esm_advance_adaptive_clock_from_motor_receipt",
        "esm_archive_expired_eligibility_trace",
        "esm_archive_fully_credited_adaptive_outcome",
    } <= names
    assert not any("python" in rule.get("comment", "").lower() for rule in manifest["rules"])


def test_verified_recoverability_relaxes_local_exploration_interrupt():
    unsafe_agent, unsafe_episode, unsafe_model = _fixture()
    _motor_receipt(
        unsafe_agent,
        unsafe_episode,
        unsafe_model,
        epoch=2,
        pre_x=0.0,
        post_x=0.0,
        sensed_post_x=0.0,
        angular_velocity=10.0,
    )
    unsafe_attrs = unsafe_agent.s.node(unsafe_episode)["attrs"]
    assert unsafe_attrs["sensorimotor_interrupt_required"] == 1.0

    safe_agent, safe_episode, safe_model = _fixture()
    safety = safe_agent.s.add_node("LearningSafetyContext", {
        "verified": 1.0,
        "protective_support_available": 1.0,
        "protective_support_effectiveness": 1.0,
        "reset_reachable": 1.0,
        "recovery_path_count": 2.0,
    })
    _edge(safe_agent, safe_episode, "has_learning_safety_context", safety)
    _motor_receipt(
        safe_agent,
        safe_episode,
        safe_model,
        epoch=2,
        pre_x=0.0,
        post_x=0.0,
        sensed_post_x=0.0,
        angular_velocity=10.0,
    )
    safe_attrs = safe_agent.s.node(safe_episode)["attrs"]
    assert safe_attrs["sensorimotor_local_urgency"] < unsafe_attrs[
        "sensorimotor_local_urgency"
    ]
    assert safe_attrs["sensorimotor_interrupt_required"] == 0.0


def test_pruned_network_sample_is_not_republished_from_old_receipt():
    agent, episode, model = _fixture()
    _, outcome, _ = _motor_receipt(
        agent,
        episode,
        model,
        epoch=2,
        pre_x=0.0,
        post_x=0.1,
        sensed_post_x=0.1,
    )
    samples = agent.inner.neighbours(
        outcome, "has_embodied_network_mode_sample"
    )
    assert len(samples) == 1
    assert agent.s.node(outcome)["attrs"][
        "network_mode_sample_published"
    ] == 1.0

    # Default-mode retention may delete the transient sample. The receipt's
    # durable publication fact must prevent a delete/recreate fixed-point loop.
    agent.inner.remove_node(samples[0])
    agent.tick()
    assert agent.inner.neighbours(
        outcome, "has_embodied_network_mode_sample"
    ) == []


def test_mechanical_transducer_has_explicit_noise_and_sample_latency():
    config = SensorimotorSensorConfiguration(
        position_noise_std=0.1,
        orientation_noise_std=0.05,
        velocity_noise_std=0.2,
        latency_samples=1,
    )
    first_sensor = SensorimotorTransducer(
        sample_period_seconds=0.01,
        configuration=config,
        seed=7,
    )
    second_sensor = SensorimotorTransducer(
        sample_period_seconds=0.01,
        configuration=config,
        seed=7,
    )
    first = first_sensor.sample(
        position=(0, 0, 0),
        orientation_xyzw=(0, 0, 0, 1),
        linear_velocity=(0, 0, 0),
        angular_velocity=(0, 0, 0),
        contact_count=1,
        sample_id=0,
    )
    repeated = first_sensor.sample(
        position=(9, 9, 9),
        orientation_xyzw=(0, 0, 1, 0),
        linear_velocity=(9, 9, 9),
        angular_velocity=(9, 9, 9),
        contact_count=0,
        sample_id=0,
    )
    delayed = first_sensor.sample(
        position=(1, 0, 0),
        orientation_xyzw=(0, 0, 1, 0),
        linear_velocity=(1, 0, 0),
        angular_velocity=(0, 0, 0),
        contact_count=0,
        sample_id=1,
    )
    control = second_sensor.sample(
        position=(0, 0, 0),
        orientation_xyzw=(0, 0, 0, 1),
        linear_velocity=(0, 0, 0),
        angular_velocity=(0, 0, 0),
        contact_count=1,
        sample_id=0,
    )

    assert repeated == first
    assert delayed["sensed_base_position"] == first["sensed_base_position"]
    assert (
        delayed["sensed_base_orientation_xyzw"]
        == first["sensed_base_orientation_xyzw"]
    )
    assert first["sensed_base_position"] == control["sensed_base_position"]
    assert delayed["sensor_latency_seconds"] == pytest.approx(0.01)
    assert delayed["sensor_position_variance"] == pytest.approx(0.01)
    assert delayed["sensor_orientation_variance"] == pytest.approx(0.0025)
    assert delayed["sensor_velocity_variance"] == pytest.approx(0.04)


def test_receipt_fuses_body_belief_and_drives_existing_adaptive_cores():
    agent, episode, model = _fixture()
    _trial, outcome, decision = _motor_receipt(
        agent,
        episode,
        model,
        epoch=1,
        pre_x=0.0,
        post_x=0.5,
        sensed_post_x=0.4,
    )

    beliefs = list(agent.inner.neighbours(
        episode, "has_embodied_body_belief"
    ))
    assert len(beliefs) == 1
    belief = agent.s.node(beliefs[0])["attrs"]
    assert belief["estimate_x"] == pytest.approx(0.404)
    assert belief["uncertainty"] > 0.0
    assert agent.s.node(episode)["attrs"]["state_x"] == pytest.approx(
        belief["estimate_x"]
    )
    agent.inner.set_attr(episode, "state_x", 99.0)
    agent.inner.set_attr(episode, "state_seq", 2.0)
    agent.tick()
    assert agent.s.node(episode)["attrs"]["state_x"] == pytest.approx(
        belief["estimate_x"]
    )
    assert agent.s.node(outcome)["attrs"]["sensorimotor_integrated"] == 1.0

    assert len(_nodes(agent, "EfferenceCopy")) == 1
    assert len(_nodes(agent, "EligibilityTrace")) == 1
    assert len(_nodes(agent, "AdaptiveOutcome")) == 1
    assert len(_nodes(agent, "CreditAssignment")) == 1
    assert agent.s.node(decision)["attrs"]["status"] == "observed"

    envelopes = list(agent.inner.neighbours(
        model, "has_embodied_actuator_envelope"
    ))
    assert len(envelopes) == 1
    envelope = agent.s.node(envelopes[0])["attrs"]
    assert envelope["experience_count"] == 1.0
    assert envelope["sensorimotor_latency_seconds"] == pytest.approx(0.03)
    assert envelope["confidence"] > 0.0

    loops = list(agent.inner.neighbours(
        episode, "has_embodied_local_loop"
    ))
    loop = agent.s.node(loops[0])["attrs"]
    assert loop["control_period_seconds"] == pytest.approx(0.03)
    assert len(_nodes(agent, "AllostaticError")) == 1
    assert len(_nodes(agent, "WorldModelObservation")) == 1
    assert len(_nodes(agent, "NetworkModeSample")) == 1


def test_receipt_clock_bounds_active_temporal_credit_indexes():
    agent, episode, model = _fixture()
    for epoch in range(1, 8):
        _motor_receipt(
            agent,
            episode,
            model,
            epoch=epoch,
            pre_x=float(epoch - 1),
            post_x=float(epoch),
            sensed_post_x=float(epoch),
        )

    clocks = list(agent.inner.neighbours(
        agent.agent, "has_adaptive_clock"
    ))
    assert len(clocks) == 1
    assert agent.s.node(clocks[0])["attrs"]["epoch"] == 7.0

    # Outcome and trace nodes remain available through their receipt/decision
    # provenance. Only their hot agent-root indexes are kept horizon-bounded.
    assert not agent.inner.neighbours(
        agent.agent, "has_adaptive_outcome"
    )
    assert len(agent.inner.neighbours(
        agent.agent, "has_archived_adaptive_outcome"
    )) == 7
    assert len(agent.inner.neighbours(
        agent.agent, "has_eligibility_trace"
    )) <= 5
    assert agent.inner.neighbours(
        agent.agent, "has_archived_eligibility_trace"
    )
    assert len(_nodes(agent, "AdaptiveOutcome")) == 7
    assert len(_nodes(agent, "EligibilityTrace")) == 7


def test_belief_resists_noisy_sample_and_controller_consolidates_for_replay():
    agent, episode, model = _fixture()
    policy = _nodes(agent, "EmbodiedSensorimotorPolicy")[0]
    agent.inner.set_attr(policy, "procedural_consolidation_confidence", 0.0)

    _motor_receipt(
        agent, episode, model,
        epoch=1, pre_x=0.0, post_x=0.5, sensed_post_x=0.5,
    )
    belief_node = list(agent.inner.neighbours(
        episode, "has_embodied_body_belief"
    ))[0]
    first = agent.s.node(belief_node)["attrs"]["estimate_x"]
    _motor_receipt(
        agent, episode, model,
        epoch=2, pre_x=0.5, post_x=1.0, sensed_post_x=2.0,
    )
    second = agent.s.node(belief_node)["attrs"]["estimate_x"]
    assert first < second < 2.0
    _motor_receipt(
        agent, episode, model,
        epoch=3, pre_x=1.0, post_x=1.5, sensed_post_x=1.5,
    )

    memories = list(agent.inner.neighbours(
        model, "has_procedural_motor_episode"
    ))
    assert len(memories) == 1
    memory = memories[0]
    assert agent.s.node(memory)["attrs"]["consolidated"] is True

    forward = list(agent.inner.neighbours(
        model, "has_embodied_forward_model"
    ))[0]
    confidence_before = agent.s.node(forward)["attrs"]["confidence"]
    sample = agent.s.add_node("NetworkModeSample", {
        "epoch": 10.0,
        "exteroceptive_load": 0.0,
        "task_demand": 0.0,
        "interoceptive_urgency": 0.0,
        "uncertainty": 0.0,
        "idle_duration": 10.0,
        "status": "raw",
    })
    _edge(agent, agent.agent, "has_network_mode_sample", sample)
    agent.tick()
    contexts = [
        context
        for context in _nodes(agent, "InternallyGeneratedContext")
        if memory in agent.inner.neighbours(context, "replays_episode")
    ]
    assert len(contexts) == 1
    assert agent.s.node(forward)["attrs"]["confidence"] > confidence_before
    assert agent.s.node(memory)["attrs"]["replay_count"] == 1.0
