"""Regression gates for humanoid receipt normalization into energetics."""
from __future__ import annotations

import pytest

from scripts.audit_humanoid_locomotor_results import _energy_observability
from substrate.world_adapter import WorldAdapter


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _episode(agent):
    episode = agent.s.add_node("HumanoidEpisode", {
        "phase": "evaluation",
        "body_mass": 2.0,
        "gravity_acceleration": 10.0,
        "locomotor_prior_reset_seq": 0.0,
        "state_available_energy_joules": 100.0,
        "state_maximum_power_watts": 100.0,
        "state_thermal_capacity_joules": 100.0,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    return episode


def _receipt(agent, episode, model, *, energy=5.0, epoch=1.0, step=1.0):
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "status": "issued",
        "support_phase": 0.0,
    })
    outcome = agent.s.add_node("HumanoidTransition", {
        "pre_x": 0.0,
        "pre_y": 0.0,
        "pre_z": 1.0,
        "post_x": 0.2,
        "post_y": 0.0,
        "post_z": 1.0,
        "pre_vz": 0.0,
        "pre_contact_count": 2.0,
        "contact_count": 2.0,
        "input_energy_joules": float(energy),
        "absorbed_energy_joules": 0.0,
        "recovered_energy_joules": 0.0,
        "peak_power_watts": 12.0,
        "thermal_load_joules": 0.0,
        "world_step_index": float(step),
        "motor_epoch": float(epoch),
        "energetic_window_seq": 0.0,
        "receipt_verified": 1.0,
    })
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "uses_humanoid_action_model", model)
    _edge(agent, trial, "has_humanoid_transition", outcome)
    return trial, outcome


def _agent():
    try:
        return WorldAdapter(seeds=("embodied_motor_priors",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")


def test_primitive_humanoid_receipt_updates_shared_energetics():
    agent = _agent()
    episode = _episode(agent)
    model = agent.s.add_node("HumanoidActionModel", {
        "token": "opaque_actuator",
    })
    trial, outcome = _receipt(agent, episode, model)

    agent.tick()

    assert agent.inner.neighbours(
        episode, "has_embodied_motor_receipt"
    ) == [outcome]
    assert agent.inner.neighbours(
        trial, "has_embodied_motor_receipt"
    ) == [outcome]
    assert agent.inner.neighbours(
        model, "has_embodied_motor_receipt"
    ) == [outcome]
    energetic = agent.inner.neighbours(
        episode, "has_embodied_energetic_state"
    )
    assert len(energetic) == 1
    assert agent.s.node(energetic[0])["attrs"][
        "input_energy_joules"
    ] == pytest.approx(5.0)
    assert agent.s.node(episode)["attrs"][
        "motor_input_energy_joules"
    ] == pytest.approx(5.0)


def test_phase_model_path_excludes_primitive_receipt_path():
    agent = _agent()
    episode = _episode(agent)
    primitive = agent.s.add_node("HumanoidActionModel", {
        "token": "opaque_actuator",
    })
    phase = agent.s.add_node("HumanoidPhaseActionModel", {
        "token": "opaque_actuator",
    })
    trial, outcome = _receipt(agent, episode, primitive, energy=7.0)
    _edge(agent, trial, "uses_humanoid_phase_action_model", phase)

    agent.tick()
    agent.tick()

    assert agent.inner.neighbours(
        phase, "has_embodied_motor_receipt"
    ) == [outcome]
    assert agent.inner.neighbours(
        primitive, "has_embodied_motor_receipt"
    ) == []
    energetic = agent.inner.neighbours(
        episode, "has_embodied_energetic_state"
    )
    assert agent.s.node(energetic[0])["attrs"][
        "input_energy_joules"
    ] == pytest.approx(7.0)


def test_energy_uses_monotonic_motor_epoch_across_world_reset():
    agent = _agent()
    episode = _episode(agent)
    model = agent.s.add_node("HumanoidActionModel", {
        "token": "opaque_actuator",
    })
    _receipt(agent, episode, model, energy=5.0, epoch=1.0, step=10.0)
    agent.tick()

    # A physical reset restarts the simulator-local step counter. The motor
    # epoch remains monotonic and therefore keeps the later receipt visible.
    _receipt(agent, episode, model, energy=7.0, epoch=2.0, step=1.0)
    agent.tick()

    energetic = agent.inner.neighbours(
        episode, "has_embodied_energetic_state"
    )
    attrs = agent.s.node(energetic[0])["attrs"]
    assert attrs["input_energy_joules"] == pytest.approx(12.0)
    assert attrs["measured_motor_epoch"] == pytest.approx(2.0)
    assert attrs["measured_world_step_index"] == pytest.approx(1.0)


def test_energy_audit_compares_the_graphs_current_window():
    trace = [
        {"motor_input_energy_joules": 3.0, "energetic_window_seq": 1.0},
        {"motor_input_energy_joules": 5.0, "energetic_window_seq": 2.0},
        {"motor_input_energy_joules": 7.0, "energetic_window_seq": 2.0},
    ]
    report = _energy_observability({
        "motor_input_energy_joules_graph_assessment": 12.0,
        "motor_energetic_window_seq_graph_assessment": 2.0,
    }, trace)

    assert report["trace_motor_input_energy_joules_evaluation_total"] == 15.0
    assert report[
        "trace_motor_input_energy_joules_current_graph_window"
    ] == 12.0
    assert report["energy_observable_comparison_scope"] == (
        "current_graph_energetic_window"
    )
    assert report["energy_observable_consistent"] is True


def test_energy_audit_does_not_compare_legacy_rung_two_scopes():
    report = _energy_observability({
        "motor_input_energy_joules_graph_assessment": 12.0,
        "control_regime": {"ordinal": 2.0},
    }, [{"motor_input_energy_joules": 15.0}])

    assert report["energy_observable_comparison_scope"] == (
        "window_metadata_unavailable"
    )
    assert report["energy_observable_comparable"] is False
    assert report["energy_observable_consistent"] is None
