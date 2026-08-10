from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "helicopter_autorotation.json"
GENERATOR = ROOT / "scripts" / "gen_helicopter_autorotation_seed.py"
RUNNER = ROOT / "scripts" / "jabberwock_helicopter_autorotation.py"
WORLD = ROOT / "domains" / "traditional_helicopter_world.py"
PROTOCOL = ROOT / "protocols" / "helicopter_autorotation_v1.json"


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def test_world_has_rotor_energy_recovery_and_a_hidden_freewheel_failure():
    from domains.traditional_helicopter_world import (
        EngineFailureCondition,
        TraditionalHelicopterWorld,
    )

    world = TraditionalHelicopterWorld(
        failure=EngineFailureCondition(onset_seconds=0.0),
        initial_position=(0.0, 80.0),
        initial_velocity=(18.0, -6.0),
        action_duration_seconds=0.2,
    )
    options = world.actuator_options()
    low_collective = min(options, key=lambda row: row["vector"][0])["token"]
    before = world.observe()
    after = world.step(low_collective)

    assert "engine_failure" not in before
    assert "engine_failure" not in after
    assert after["supplied_energy_joules"] == 0.0
    assert after["recovered_energy_joules"] > 0.0
    assert after["rotor_kinetic_energy_joules"] > 0.0
    assert after["rotor_speed_fraction"] > 0.9


def test_helicopter_boundary_contains_mechanics_but_no_agent_policy():
    import domains.traditional_helicopter_world as module

    tree = ast.parse(inspect.getsource(module))
    public_methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert public_methods == {
        "actuator_options",
        "apply",
        "body_parameters",
        "close",
        "observe",
        "reset",
        "step",
    }
    assert not {
        "choose",
        "decide",
        "learn",
        "plan",
        "predict",
        "reward",
        "score",
    } & public_methods


def test_seed_uses_opaque_local_analysis_by_synthesis():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    chooser = json.dumps(_rule(seed, "ha_choose_energy_viability_action"))
    learner = json.dumps(_rule(seed, "ha_learn_local_energy_dynamics"))
    memory = json.dumps(_rule(seed, "ha_memorise_bounded_intervention"))
    measure = json.dumps(_rule(seed, "ha_measure_viability"))

    assert seed["id"] == "helicopter_autorotation"
    assert seed["depends_on"] == [
        "embodied_motor_priors",
        "motor_decision_collapse",
    ]
    assert '"type": "Argmin"' in chooser
    assert "has_energy_transition_memory" in chooser
    assert "prediction_error" in learner
    assert "surprise_adaptation_rate" in learner
    assert "verified_bounded_local_consequence" in memory
    assert "time_to_contact_seconds" in measure
    policy_text = json.dumps(seed["nodes"])
    for forbidden in (
        "lower_collective",
        "flare_now",
        "engine_failed",
        "autorotation_mode",
    ):
        assert forbidden not in policy_text


def test_runtime_is_a_mechanical_graph_boundary():
    runner = RUNNER.read_text(encoding="utf-8")
    generator = GENERATOR.read_text(encoding="utf-8")

    assert 'WorldAdapter(seeds=("helicopter_autorotation",))' in runner
    assert '"semantics": "unknown"' in runner
    assert "world.step(token)" in runner
    assert "selected_token" in runner
    assert '"type": "Argmin"' in generator
    assert "collective" not in runner
    assert "cyclic" not in runner


def test_graph_discovers_safe_hidden_failure_landing_and_transfers():
    from scripts.jabberwock_helicopter_autorotation import (
        run_autorotation_experiment,
    )

    result = run_autorotation_experiment(
        episodes=3,
        maximum_actions_per_episode=400,
        initial_altitudes=(80.0, 120.0, 160.0),
        initial_forward_speeds=(12.0, 18.0, 24.0),
    )

    assert result["policy_owner"] == "rust_graph"
    assert result["failure_observation_exposed"] is False
    assert result["action_semantics_exposed_to_graph"] is False
    assert result["calibration_interventions"] > 0
    assert result["safe_touchdowns"] == 3
    assert result["graph_assessed_safe_touchdowns"] == 3
    for row in result["episode_results"]:
        assert row["safe_touchdown_world_assessment"]
        assert row["viable_contact_graph_assessment"]
        assert abs(row["touchdown_vertical_speed"]) <= 2.5
        assert abs(row["touchdown_horizontal_speed"]) <= 8.0


def test_preflight_causal_memory_removes_cold_start_failure():
    from scripts.jabberwock_helicopter_autorotation import (
        run_autorotation_experiment,
    )

    learned = run_autorotation_experiment(
        episodes=2,
        maximum_actions_per_episode=300,
        calibration_repeats=1,
    )
    ablated = run_autorotation_experiment(
        episodes=2,
        maximum_actions_per_episode=300,
        calibration_repeats=0,
    )

    assert learned["safe_touchdowns"] == 2
    assert learned["success_rate"] > ablated["success_rate"]
    assert not ablated["episode_results"][0][
        "safe_touchdown_world_assessment"
    ]


def test_protocol_preregisters_physical_success_and_impossibility_bounds():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["id"] == "helicopter_autorotation_v1"
    assert protocol["failure"]["observable_to_agent"] is False
    assert protocol["controls"]["semantics_observable_to_agent"] is False
    assert protocol["success"]["maximum_vertical_speed_m_s"] == pytest.approx(
        2.5
    )
    assert "height_velocity_exclusion" in protocol["exclusions"]
