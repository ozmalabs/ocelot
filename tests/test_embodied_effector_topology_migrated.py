"""Gates for name-free, receipt-grounded effector assembly discovery."""
from __future__ import annotations

import pytest

from domains.embodied_effector_topology import (
    bind_effector_models,
    install_name_free_effector_topology,
)
from substrate.world_adapter import WorldAdapter


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _body(agent, tokens):
    episode = agent.s.add_node("EmbodiedEpisode", {
        "phase": "adaptation",
        "body_mass": 1.0,
        "gravity_acceleration": 9.81,
        "locomotor_path_length": 0.0,
        "state_available_energy_joules": 100.0,
        "state_maximum_power_watts": 100.0,
        "state_thermal_capacity_joules": 100.0,
    })
    _edge(agent, agent.agent, "has_embodied_episode", episode)
    options = (
        {
            "token": tokens[0],
            "actuator_group": 0,
            "mount_ordinal": 0,
            "command_polarity": 1.0,
            "tonic_default": 0.0,
            "hard_coupling_id": "coupling:0",
        },
        {
            "token": tokens[1],
            "actuator_group": 1,
            "mount_ordinal": 1,
            "command_polarity": 1.0,
            "tonic_default": 0.0,
            "hard_coupling_id": "coupling:0",
        },
        {
            "token": tokens[2],
            "actuator_group": 0,
            "mount_ordinal": 0,
            "command_polarity": -1.0,
            "tonic_default": 0.0,
        },
    )
    signature = (
        ("link", 0, -1),
        ("link", 1, 0),
        ("actuator", 0, 0),
        ("actuator", 1, 1),
        ("actuator", 2, 0),
    )
    topology = install_name_free_effector_topology(
        agent, episode, options, signature
    )
    models = {}
    for ordinal, token in enumerate(tokens):
        model = agent.s.add_node("ActionModel", {
            "token": token,
            "ordinal": float(ordinal),
        })
        models[token] = model
    bind_effector_models(agent, topology, models)
    return episode, topology, models


def _assembly_rows(agent, episode):
    return [
        agent.s.node(node)["attrs"]
        for node in agent.inner.neighbours(
            episode, "has_embodied_effector_assembly"
        )
    ]


def _compound_receipt(agent, episode, models, pair, *, step, progress):
    trial = agent.s.add_node("MotorTrial", {
        "predicted_task_progress": 0.25,
        "support_phase": 0.0,
        "status": "issued",
    })
    outcome = agent.s.add_node("TransitionObservation", {
        "receipt_verified": 1.0,
        "world_step_index": float(step),
        "has_task_progress": 1.0,
        "task_progress": float(progress),
        "pre_x": 0.0,
        "post_x": float(progress),
        "input_energy_joules": 1.0,
        "stability_cost": 0.1,
    })
    _edge(agent, episode, "has_motor_trial", trial)
    for token in pair:
        _edge(agent, trial, "uses_embodied_effector_model", models[token])
    _edge(agent, trial, "has_embodied_motor_receipt", outcome)
    return trial


def test_topology_marks_physical_couplings_and_command_conflicts():
    try:
        agent = WorldAdapter(seeds=("embodied_motor_priors",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    episode, topology, _models = _body(
        agent, ("opaque:a", "opaque:b", "opaque:c")
    )
    agent.tick()
    agent.tick()

    assert topology["relation_count"] == 3
    statuses = [row["status"] for row in _assembly_rows(agent, episode)]
    assert statuses.count("hard_coupled") == 1
    assert statuses.count("hard_conflict") == 1
    assert statuses.count("candidate") == 1


@pytest.mark.parametrize(
    "tokens",
    [
        ("flexor-ish", "extensor-ish", "brace-ish"),
        ("rotor:nw", "rotor:se", "surface:elevon"),
    ],
)
def test_receipts_learn_the_same_assembly_relation_for_any_vocabulary(tokens):
    try:
        agent = WorldAdapter(seeds=("embodied_motor_priors",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    episode, _topology, models = _body(agent, tokens)
    agent.tick()

    _compound_receipt(
        agent,
        episode,
        models,
        (tokens[1], tokens[2]),
        step=1,
        progress=1.0,
    )
    agent.tick()
    agent.tick()
    learned = [
        row for row in _assembly_rows(agent, episode)
        if row["experience_count"] > 0.0
    ]
    assert len(learned) == 1
    assert learned[0]["status"] == "cooperative"
    assert learned[0]["cooperation_evidence"] == pytest.approx(0.75)

    _compound_receipt(
        agent,
        episode,
        models,
        (tokens[1], tokens[2]),
        step=2,
        progress=-2.0,
    )
    agent.tick()
    learned = [
        row for row in _assembly_rows(agent, episode)
        if row["experience_count"] > 0.0
    ]
    assert len(learned) == 1
    assert learned[0]["status"] == "fractionating"
    assert learned[0]["interference_evidence"] > (
        learned[0]["cooperation_evidence"]
    )


def test_combined_command_token_is_decomposed_into_physical_effectors():
    try:
        agent = WorldAdapter(seeds=("embodied_motor_priors",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    episode = agent.s.add_node("EmbodiedEpisode", {})
    _edge(agent, agent.agent, "has_embodied_episode", episode)
    options = ({
        "token": "opaque_combined_command",
        "vector": (0.8, -0.4, 0.0),
        "effector_commands": ((0, 0.8), (1, -0.4), (2, 0.0)),
    },)
    topology = install_name_free_effector_topology(agent, episode, options)
    model = agent.s.add_node("ActionModel", {"token": options[0]["token"]})
    bind_effector_models(
        agent, topology, {options[0]["token"]: model}
    )
    assert len(topology["effectors"]) == 3
    assert len(agent.inner.neighbours(model, "models_embodied_effector")) == 2

    agent.tick()
    trial = agent.s.add_node("MotorTrial", {
        "predicted_task_progress": 0.0,
        "support_phase": 0.0,
        "status": "issued",
    })
    outcome = agent.s.add_node("TransitionObservation", {
        "receipt_verified": 1.0,
        "world_step_index": 1.0,
        "task_progress": 0.5,
        "input_energy_joules": 1.0,
    })
    _edge(agent, trial, "uses_action_model", model)
    _edge(agent, trial, "has_embodied_motor_receipt", outcome)
    agent.tick()
    agent.tick()
    learned = [
        row for row in _assembly_rows(agent, episode)
        if row["experience_count"] > 0.0
    ]
    assert len(learned) == 1
    assert learned[0]["status"] == "cooperative"
