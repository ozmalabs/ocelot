"""Graph-native generic temporal command encoding.

The host may transduce the emitted command node, but all quantisation and
residual state transitions must be authored graph terms.
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate.world_adapter import WorldAdapter
from scripts.gen_embodied_motor_program_seed import (
    close_temporal_command_trial_rule,
    copy_trial_members_rule,
    temporal_command_reset_rule,
    temporal_command_state_rule,
    temporal_encode_trial_member_rule,
    temporal_emit_neutral_for_empty_trial_rule,
    manifest,
)


def _agent(enabled: bool) -> tuple[WorldAdapter, object, list[object]]:
    manifest = {
        "id": "graph_temporal_probe",
        "version": "1.0.0",
        "rules": [
            temporal_command_state_rule(),
            temporal_command_reset_rule(),
            copy_trial_members_rule(),
            temporal_encode_trial_member_rule(),
            temporal_emit_neutral_for_empty_trial_rule(),
            close_temporal_command_trial_rule(),
        ],
    }
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest, agent.agent)
    policy = agent.s.add_node(
        "EmbodiedMotorProgramPolicy",
        {"temporal_command_encoding_enabled": 0.0},
    )
    agent.inner.add_edge_unchecked(
        agent.agent, "has_embodied_motor_program_policy", policy
    )
    episode = agent.s.add_node(
        "EmbodiedMotorProgramEpisode",
        {
            "temporal_command_encoding_enabled": float(enabled),
            "action_ready": 0.0,
        },
    )
    agent.inner.add_edge_unchecked(
        agent.agent, "has_embodied_motor_program_episode", episode
    )
    models = []
    for ordinal, level in enumerate((-1.0, 0.0, 1.0)):
        attrs = {
            "ordinal": float(ordinal),
            "actuator_group": 0.0,
            "specified_command_level": level,
            "token": f"opaque/{ordinal}",
            "never_commanded": 0.0,
        }
        if ordinal == 1:
            # The selected model supplies a continuous request while the
            # group's declared alphabet remains {-1, 0, +1}.
            attrs.update(
                temporal_request_declared=1.0,
                temporal_request_level=0.2,
            )
        model = agent.s.add_node("EmbodiedEffectorModel", attrs)
        models.append(model)
        agent.inner.add_edge_unchecked(
            episode, "has_embodied_effector_model", model
        )
    return agent, episode, models


def _trial(agent, episode, requested):
    program = agent.s.add_node("EmbodiedMotorProgram", {"member_count": 1.0})
    trial = agent.s.add_node(
        "EmbodiedMotorProgramTrial",
        {"status": "assembling", "request_seq": 1.0},
    )
    agent.inner.add_edge_unchecked(
        episode, "has_embodied_motor_program_trial", trial
    )
    agent.inner.add_edge_unchecked(
        trial, "enacts_embodied_motor_program", program
    )
    agent.inner.add_edge_unchecked(
        program, "includes_embodied_effector_model", requested
    )
    return trial


def test_temporal_encoder_is_graph_native_and_deterministic():
    agent, episode, models = _agent(True)
    emitted = []
    for _ in range(5):
        trial = _trial(agent, episode, models[1])
        agent.tick(max_steps=100)
        commands = agent.inner.neighbours(trial, "has_temporal_command")
        assert len(commands) == 1
        emitted.append(agent.s.node(commands[0])["attrs"]["command_level"])
    assert emitted == [0.0, 0.0, 1.0, 0.0, 0.0]
    state = agent.inner.neighbours(
        episode, "has_temporal_command_state"
    )
    assert len(state) == 1
    assert agent.s.node(state[0])["attrs"]["step"] == 5.0
    assert abs(agent.s.node(state[0])["attrs"]["residual"]) < 1e-12


def test_temporal_encoder_is_absent_inert_when_not_enabled():
    agent, episode, models = _agent(False)
    trial = _trial(agent, episode, models[1])
    agent.tick(max_steps=100)
    assert not agent.inner.neighbours(episode, "has_temporal_command_state")
    assert not agent.inner.neighbours(trial, "has_temporal_command")
    assert agent.s.node(trial)["attrs"]["status"] == "issued"


def test_temporal_encoder_reset_is_graph_state_reset():
    agent, episode, models = _agent(True)
    trial = _trial(agent, episode, models[1])
    agent.tick(max_steps=100)
    state = agent.inner.neighbours(
        episode, "has_temporal_command_state"
    )[0]
    assert agent.s.node(state)["attrs"]["step"] == 1.0
    agent.inner.set_attr(episode, "temporal_command_reset", 1.0)
    agent.tick(max_steps=100)
    assert agent.s.node(state)["attrs"]["step"] == 0.0
    assert agent.s.node(state)["attrs"]["residual"] == 0.0


def test_temporal_encoder_body_only_program_gets_graph_neutral_command():
    agent, episode, models = _agent(True)
    body = agent.s.add_node(
        "EmbodiedEffectorModel",
        {
            "ordinal": 9.0,
            "actuator_group": 9.0,
            "specified_command_level": 1.0,
            "token": "opaque/body",
            "never_commanded": 1.0,
        },
    )
    agent.inner.add_edge_unchecked(
        episode, "has_embodied_effector_model", body
    )
    trial = _trial(agent, episode, body)
    agent.tick(max_steps=100)
    commands = agent.inner.neighbours(trial, "has_temporal_command")
    assert len(commands) == 1
    assert agent.s.node(commands[0])["attrs"]["token"] == "opaque/1"


def test_generic_seed_snapshot_and_adaptation_contract_are_deterministic():
    """The generic graph owns receipt learning, publication, and reselection."""
    root = Path(__file__).resolve().parents[1]
    checked = json.loads(
        (root / "seeds" / "embodied_motor_program.json").read_text()
    )
    generated = manifest()
    assert checked == generated == manifest()
    assert checked["version"] == "1.25.0"
    names = {rule["name"] for rule in checked["rules"]}
    assert {
        "emp_learn_factorized_effector_from_exact_receipt",
        "emp_internalize_receipt_grounded_program_default",
        "emp_mark_factorized_models_for_recalibration",
        "emp_emit_neutral_for_empty_motor_trial",
    } <= names
    productions = {
        production["edge_type"] for production in checked["productions"]
    }
    assert "has_embodied_motor_command" in productions
