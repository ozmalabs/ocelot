"""Gates for shared graph-native motor and energetic priors."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _receipt(
    agent, episode, model, *, step, contact, vz, energy, context=None
):
    trial_attrs = {}
    if context is not None:
        trial_attrs["motor_task_context"] = context
    trial = agent.s.add_node("MotorTrial", trial_attrs)
    outcome = agent.s.add_node("TransitionObservation", {
        "pre_x": 0.0,
        "pre_y": 0.0,
        "pre_z": 1.0,
        "post_x": 0.2,
        "post_y": 0.0,
        "post_z": 1.1,
        "pre_vz": float(vz),
        "pre_contact_count": float(contact),
        "contact_count": float(contact),
        "input_energy_joules": float(energy),
        "recovered_energy_joules": float(energy / 4.0),
        "peak_power_watts": float(energy * 2.0),
        "thermal_load_joules": float(energy / 4.0),
        "world_step_index": float(step),
        "motor_epoch": float(step),
        "energetic_window_seq": 0.0,
        "receipt_verified": 1.0,
    })
    _edge(agent, episode, "has_motor_trial", trial)
    _edge(agent, trial, "uses_action_model", model)
    _edge(agent, trial, "has_transition_outcome", outcome)


def test_domain_seeds_depend_on_shared_motor_priors():
    for name in (
        "humanoid_adaptation",
        "embodied_adaptation",
        "aerial_adaptation",
    ):
        manifest = json.loads((ROOT / "seeds" / f"{name}.json").read_text())
        assert "embodied_motor_priors" in manifest["depends_on"]


def test_priors_cover_hybrid_effectors_and_thermodynamic_economy():
    manifest = json.loads(
        (ROOT / "seeds" / "embodied_motor_priors.json").read_text()
    )
    kinds = {node["attrs"]["kind"] for node in manifest["nodes"]}
    assert {
        "momentum_exchange",
        "energetics",
        "viability",
        "composition",
        "temporal_continuity",
        "hybrid_manoeuvre",
    } <= kinds


def test_ideal_effort_starts_from_body_work_prior_then_adapts_quickly():
    agent = WorldAdapter(seeds=("embodied_motor_priors",))
    episode = agent.s.add_node("EmbodiedEpisode", {
        "phase": "locomotion",
        "body_mass": 2.0,
        "gravity_acceleration": 10.0,
        "characteristic_length_metres": 1.0,
        "motor_effector_group_count": 4.0,
    })
    model = agent.s.add_node("ActionModel", {"token": "opaque_effector"})
    _edge(agent, agent.agent, "has_embodied_episode", episode)
    agent.tick()

    # One of four independently controllable groups supplies a morphological
    # 1:4 prior. Its dimensional scale is one 20-joule body-work unit.
    assert agent.s.node(episode)["attrs"][
        "future_manifold_ideal_effort"
    ] == pytest.approx(0.25)
    assert agent.s.node(episode)["attrs"][
        "future_manifold_effort_scale_joules"
    ] == pytest.approx(20.0)

    _receipt(agent, episode, model, step=1, contact=1, vz=0.0, energy=4.0)
    agent.tick()
    assert agent.s.node(episode)["attrs"][
        "future_manifold_ideal_effort"
    ] == pytest.approx(0.2)

    _receipt(agent, episode, model, step=2, contact=1, vz=0.0, energy=2.0)
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["future_manifold_ideal_effort"] == pytest.approx(0.15)
    assert attrs["future_manifold_ideal_effort_evidence_count"] == 2.0


def test_ideal_effort_adapts_independently_by_motor_task_context():
    agent = WorldAdapter(seeds=("embodied_motor_priors",))
    episode = agent.s.add_node("EmbodiedEpisode", {
        "body_mass": 2.0,
        "gravity_acceleration": 10.0,
        "characteristic_length_metres": 1.0,
        "motor_effector_group_count": 4.0,
        "motor_task_context": "locomotion",
    })
    model = agent.s.add_node("ActionModel", {"token": "opaque_effector"})
    _edge(agent, agent.agent, "has_embodied_episode", episode)
    agent.tick()

    _receipt(
        agent, episode, model, step=1, contact=1, vz=0.0, energy=2.0,
        context="locomotion",
    )
    agent.tick()
    assert agent.s.node(episode)["attrs"][
        "future_manifold_ideal_effort"
    ] == pytest.approx(0.1)

    agent.inner.set_attr(episode, "motor_task_context", "self_takeoff")
    _receipt(
        agent, episode, model, step=2, contact=1, vz=0.0, energy=8.0,
        context="self_takeoff",
    )
    agent.tick()
    assert agent.s.node(episode)["attrs"][
        "future_manifold_ideal_effort"
    ] == pytest.approx(0.4)

    agent.inner.set_attr(episode, "motor_task_context", "locomotion")
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["future_manifold_ideal_effort"] == pytest.approx(0.1)
    assert attrs["future_manifold_ideal_effort_context"] == "locomotion"


def test_graph_learns_grounded_and_descending_effector_roles_separately():
    try:
        agent = WorldAdapter(seeds=("embodied_motor_priors",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")

    episode = agent.s.add_node("EmbodiedEpisode", {
        "phase": "locomotion",
        "body_mass": 2.0,
        "gravity_acceleration": 10.0,
        "locomotor_path_length": 0.4,
        "state_available_energy_joules": 10.0,
        "state_maximum_power_watts": 10.0,
        "state_thermal_capacity_joules": 5.0,
    })
    model = agent.s.add_node("ActionModel", {"token": "opaque_effector"})
    _edge(agent, agent.agent, "has_embodied_episode", episode)
    _receipt(
        agent,
        episode,
        model,
        step=1,
        contact=1,
        vz=0.5,
        energy=4.0,
    )
    agent.tick()

    energetic = agent.inner.neighbours(
        episode,
        "has_embodied_energetic_state",
    )
    assert len(energetic) == 1
    energetic_attrs = agent.s.node(energetic[0])["attrs"]
    assert energetic_attrs["input_energy_joules"] == pytest.approx(4.0)
    assert energetic_attrs["net_energy_joules"] == pytest.approx(3.0)
    assert energetic_attrs["cost_of_transport"] == pytest.approx(
        3.0 / (2.0 * 10.0 * math.sqrt(0.05))
    )
    assert energetic_attrs["remaining_energy_joules"] == pytest.approx(7.0)
    assert energetic_attrs["power_headroom_watts"] == pytest.approx(2.0)
    assert energetic_attrs["thermal_headroom_joules"] == pytest.approx(4.0)

    _receipt(
        agent,
        episode,
        model,
        step=2,
        contact=0,
        vz=-0.5,
        energy=2.0,
    )
    agent.tick()

    capabilities = [
        agent.s.node(node)["attrs"]
        for node in agent.inner.neighbours(
            model,
            "has_embodied_effector_capability",
        )
    ]
    assert {
        (row["coupling_regime"], row["vertical_regime"])
        for row in capabilities
    } == {(1.0, 1.0), (0.0, -1.0)}
    assert all(row["translation_per_joule"] > 0.0 for row in capabilities)
    assert all("flow_conditioned_authority_gain" in row for row in capabilities)

    energetic_attrs = agent.s.node(energetic[0])["attrs"]
    assert energetic_attrs["input_energy_joules"] == pytest.approx(6.0)
    assert energetic_attrs["net_energy_joules"] == pytest.approx(4.5)
    assert energetic_attrs["thermal_headroom_joules"] == pytest.approx(3.5)

    agent.inner.set_attr(episode, "locomotor_prior_reset_seq", 1.0)
    agent.tick()
    energetic_attrs = agent.s.node(energetic[0])["attrs"]
    assert energetic_attrs["input_energy_joules"] == 0.0
    assert energetic_attrs["transport_path_length_metres"] == 0.0
    assert energetic_attrs["remaining_energy_joules"] == 10.0
