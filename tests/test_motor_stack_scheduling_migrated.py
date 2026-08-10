"""Biological scheduling gates shared by ground, aerial, and helicopter stacks."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from substrate.world_adapter import WorldAdapter


def _seed(name: str) -> dict:
    return json.loads((ROOT / "seeds" / f"{name}.json").read_text())


def _rules(name: str) -> dict[str, dict]:
    return {rule["name"]: rule for rule in _seed(name)["rules"]}


def _edge(agent: WorldAdapter, source, edge_type: str, target) -> None:
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def test_motor_stacks_use_biologically_tiered_deadlines():
    expected = {
        "embodied_adaptation": {
            "soft_realtime": {"ea_learn_forward_model"},
            "background": {"ea_expose_motor_decision_option"},
        },
        "aerial_adaptation": {
            "soft_realtime": {"aa_learn_aerial_forward_model"},
            "background": {"aa_expose_motor_decision_option"},
        },
        "helicopter_autorotation": {
            "soft_realtime": {"ha_learn_local_energy_dynamics"},
            "background": {
                "ha_memorise_bounded_intervention",
                "ha_expose_motor_decision_option",
            },
        },
    }
    for seed_name, tiers in expected.items():
        seed = _seed(seed_name)
        rules = _rules(seed_name)
        assert seed["latency_class"] == "soft_realtime"
        assert {
            name
            for name, rule in rules.items()
            if rule["latency_class"] == "soft_realtime"
        } == tiers["soft_realtime"]
        assert {
            name
            for name, rule in rules.items()
            if rule["latency_class"] == "background"
        } == tiers["background"]
        assert all(
            rule["latency_class"]
            in {"hard_realtime", "soft_realtime", "background"}
            for rule in rules.values()
        )


def test_immediate_estimation_interruption_and_release_remain_hard():
    hard = {
        "embodied_adaptation": {
            "ea_measure_goal_state",
            "ea_choose_babble_action",
            "ea_choose_change_recalibration",
            "ea_choose_model_action",
            "ea_choose_adaptation_probe",
            "ea_choose_no_learning_control",
            "ea_choose_random_control",
            "ea_choose_shuffled_model_control",
            "ea_prepare_shared_motor_collapse_values",
            "ea_arm_shared_motor_collapse",
            "ea_release_shared_motor_collapse",
            "ea_open_motor_trial",
            "ea_close_no_learning_trial",
        },
        "aerial_adaptation": {
            "aa_measure_flight_state",
            "aa_choose_motor_babble",
            "aa_choose_learned_flight_action",
            "aa_prepare_shared_motor_collapse_values",
            "aa_arm_shared_motor_collapse",
            "aa_release_shared_motor_collapse",
            "aa_open_flight_trial",
            "aa_close_frozen_flight_trial",
            "aa_detect_direct_control_emergency",
            "aa_direct_three_rotor_reduced_attitude_control",
        },
        "helicopter_autorotation": {
            "ha_measure_viability",
            "ha_choose_unmodelled_intervention",
            "ha_choose_energy_viability_action",
            "ha_choose_compact_model_fallback",
            "ha_prepare_shared_memory_options",
            "ha_retire_shared_compact_options",
            "ha_arm_shared_memory_collapse",
            "ha_release_shared_memory_collapse",
            "ha_prepare_shared_compact_options",
            "ha_arm_shared_compact_collapse",
            "ha_release_shared_compact_collapse",
            "ha_open_energy_trial",
            "ha_request_motor_learning",
        },
    }
    for seed_name, expected in hard.items():
        rules = _rules(seed_name)
        assert {
            name
            for name, rule in rules.items()
            if rule["latency_class"] == "hard_realtime"
        } == expected


def test_ground_shared_collapse_release_is_executable_graph_data():
    """The selected model must be a Var term, not an unparseable host string."""
    release = _rules("embodied_adaptation")[
        "ea_release_shared_motor_collapse"
    ]
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(
        {"id": "ground_shared_collapse_release_gate", "rules": [release]},
        agent.agent,
    )
    assert any(
        rule.get("active")
        and rule.get("name") == "ea_release_shared_motor_collapse"
        for rule in agent.inner.export_rules()
    )


def test_all_three_stacks_migrate_learned_release_to_shared_collapse():
    cases = (
        (
            "embodied_adaptation",
            "ea",
            "ea_prepare_shared_motor_collapse_values",
            "ea_release_shared_motor_collapse",
        ),
        (
            "aerial_adaptation",
            "aa",
            "aa_prepare_shared_motor_collapse_values",
            "aa_release_shared_motor_collapse",
        ),
        (
            "helicopter_autorotation",
            "ha",
            "ha_prepare_shared_memory_options",
            "ha_release_shared_memory_collapse",
        ),
    )
    for seed_name, prefix, prepare_name, release_name in cases:
        seed = _seed(seed_name)
        assert "motor_decision_collapse" in seed["depends_on"]
        rules = _rules(seed_name)
        exposure = rules[f"{prefix}_expose_motor_decision_option"]
        serialized = json.dumps(exposure)
        for key in (
            "available",
            "default_value",
            "learned_value",
            "grounded_value",
            "ordinal",
        ):
            assert key in serialized
        assert not any(
            edge[1] in {"in_scene", "in_episode"}
            for edge in exposure["effects"]
            if edge[0] == "add_edge"
        )
        prepare = json.dumps(rules[prepare_name])
        release = json.dumps(rules[release_name])
        assert "has_motor_decision_option" in prepare
        assert "grounded_value" in prepare
        assert "selected_option_ref" in release


def test_verified_helicopter_receipt_recruits_soft_learning_and_background_memory():
    agent = WorldAdapter(seeds=("helicopter_autorotation",))
    episode = agent.s.add_node("HelicopterEnergyEpisode", {
        "authority_change_count": 0.0,
    })
    model = agent.s.add_node("HelicopterEnergyActionModel", {
        "token": "opaque_test",
        "ordinal": 0.0,
        "experience_count": 0.0,
        "mean_dvx": 0.0,
        "mean_dvy": 0.0,
        "mean_dvz": 0.0,
        "mean_droll_rate": 0.0,
        "mean_dpitch_rate": 0.0,
        "mean_dyaw_rate": 0.0,
        "mean_drotor_fraction": 0.0,
        "mean_supplied_energy_joules": 0.0,
        "mean_recovered_energy_joules": 0.0,
        "prediction_error_ema": 0.0,
        "surprise_count": 0.0,
    })
    trial = agent.s.add_node("HelicopterEnergyTrial", {
        "status": "issued",
    })
    outcome = agent.s.add_node("HelicopterEnergyOutcome", {
        "pre_vx": 0.0,
        "pre_vy": 0.0,
        "pre_vz": -2.0,
        "post_vx": 0.1,
        "post_vy": 0.0,
        "post_vz": -1.8,
        "pre_roll": 0.0,
        "pre_pitch": 0.0,
        "pre_yaw": 0.0,
        "pre_roll_rate": 0.0,
        "pre_pitch_rate": 0.0,
        "pre_yaw_rate": 0.0,
        "post_roll_rate": 0.0,
        "post_pitch_rate": 0.01,
        "post_yaw_rate": 0.0,
        "pre_rotor_fraction": 0.8,
        "post_rotor_fraction": 0.82,
        "supplied_energy_joules": 0.0,
        "recovered_energy_joules": 2.0,
        "receipt_verified": 1.0,
        "processed": 0.0,
        "bounded_intervention": 1.0,
        "memory_recorded": 0.0,
        "helicopter_learning_escalation_requested": 0.0,
    })
    _edge(agent, agent.agent, "has_helicopter_episode", episode)
    _edge(agent, episode, "has_energy_action_model", model)
    _edge(agent, episode, "has_helicopter_energy_trial", trial)
    _edge(agent, trial, "uses_energy_action_model", model)
    _edge(agent, trial, "has_helicopter_energy_outcome", outcome)

    agent.tick()

    assert agent.s.node(trial)["attrs"]["status"] == "learned"
    assert agent.s.node(model)["attrs"]["experience_count"] == 1.0
    assert agent.s.node(model)["attrs"]["motor_option_schema_ready"] == 1.0
    assert agent.s.node(outcome)["attrs"]["memory_recorded"] == 1.0
    assert len(list(agent.inner.neighbours(
        episode, "has_energy_transition_memory"
    ))) == 1
    escalations = list(agent.inner.neighbours(
        outcome, "has_system_two_escalation"
    ))
    own_escalations = [
        escalation
        for escalation in escalations
        if agent.s.node(escalation)["attrs"].get("reason")
        == "verified_helicopter_motor_receipt"
    ]
    assert len(own_escalations) == 1
    assert agent.s.node(own_escalations[0])["attrs"]["status"] == "serviced"
