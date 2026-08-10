from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "helicopter_autorotation.json"
RUNNER = ROOT / "scripts" / "jabberwock_helicopter_autorotation_3d.py"
WORLD = ROOT / "domains" / "pybullet_helicopter_world.py"
PROTOCOL = ROOT / "protocols" / "helicopter_autorotation_3d_v1.json"


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def test_six_dof_world_exposes_combined_opaque_authority_and_hidden_failure():
    from domains.pybullet_helicopter_world import PyBulletHelicopterWorld
    from domains.traditional_helicopter_world import EngineFailureCondition

    with PyBulletHelicopterWorld(
        failure=EngineFailureCondition(onset_seconds=0.0),
        initial_position=(0.0, 0.0, 80.0),
        initial_velocity=(18.0, 0.0, -3.0),
    ) as world:
        options = world.actuator_options()
        low_energy = min(
            options,
            key=lambda row: (row["vector"][0], sum(abs(x) for x in row["vector"][1:])),
        )
        before = world.observe()
        after = world.step(low_energy["token"])

    expected_actions = (
        len(PyBulletHelicopterWorld.COLLECTIVE_LEVELS)
        * len(PyBulletHelicopterWorld.CYCLIC_LONGITUDINAL_LEVELS)
        * len(PyBulletHelicopterWorld.CYCLIC_LATERAL_LEVELS)
        * len(PyBulletHelicopterWorld.PEDAL_LEVELS)
    )
    assert len(options) == expected_actions
    assert all(len(row["vector"]) == 4 for row in options)
    assert "engine_failure" not in before
    assert "engine_failure" not in after
    assert after["supplied_energy_joules"] == 0.0
    assert after["recovered_energy_joules"] > 0.0
    assert len(after["base_orientation_xyzw"]) == 4
    assert len(after["base_angular_velocity"]) == 3


def test_six_dof_world_boundary_contains_no_agent_policy():
    import domains.pybullet_helicopter_world as module

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


def test_same_graph_seed_models_three_dimensional_attitude_consequences():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    chooser = json.dumps(_rule(seed, "ha_choose_energy_viability_action"))
    learner = json.dumps(_rule(seed, "ha_learn_local_energy_dynamics"))
    policy = seed["nodes"][0]["attrs"]

    for field in (
        "mean_dvy",
        "mean_droll_rate",
        "mean_dpitch_rate",
        "mean_dyaw_rate",
    ):
        assert field in chooser
        assert field in learner
    assert policy["attitude_projection_seconds"] > (
        policy["action_duration_seconds"]
    )
    assert policy["pitch_attitude_projection_seconds"] == (
        policy["action_duration_seconds"]
    )
    assert policy["flight_roll_attitude_weight"] > 0.0
    assert policy["flight_pitch_attitude_weight"] > 0.0
    assert policy["flight_yaw_attitude_weight"] > 0.0
    assert policy["lateral_kinetic_weight"] > 0.0
    assert policy["transverse_angular_rate_weight"] > (
        policy["pitch_rate_weight"]
    )


def test_3d_runtime_is_transduction_not_python_flight_policy():
    source = RUNNER.read_text(encoding="utf-8")

    assert 'WorldAdapter(seeds=("helicopter_autorotation",))' in source
    assert '"semantics": "unknown"' in source
    assert "world.step(token)" in source
    assert "selected_token" in source
    for forbidden in ("lower_collective", "flare_now", "autorotation_mode"):
        assert forbidden not in source


def test_graph_autorotates_in_six_dof_across_crosswind_transfer():
    from scripts.jabberwock_helicopter_autorotation_3d import (
        run_autorotation_3d_experiment,
    )

    result = run_autorotation_3d_experiment(
        episodes=2,
        maximum_actions_per_episode=500,
        initial_altitudes=(80.0, 120.0),
        initial_forward_speeds=(12.0, 18.0),
        wind_velocities=((0.0, 1.0, 0.0), (-3.0, 4.0, 0.0)),
    )

    assert result["policy_owner"] == "rust_graph"
    assert result["failure_observation_exposed"] is False
    assert result["action_semantics_exposed_to_graph"] is False
    assert result["safe_touchdowns"] == 2
    assert result["graph_assessed_safe_touchdowns"] == 2
    for row in result["episode_results"]:
        velocity = row["touchdown_velocity"]
        attitude = row["touchdown_rpy"]
        assert row["safe_touchdown_world_assessment"]
        assert row["viable_contact_graph_assessment"]
        assert abs(velocity[2]) <= 2.5
        assert abs(velocity[1]) <= 8.0
        assert abs(attitude[0]) <= 0.3141592653589793
        assert abs(attitude[1]) <= 0.3141592653589793


def test_3d_protocol_keeps_failure_and_control_meanings_hidden():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    assert protocol["id"] == "helicopter_autorotation_3d_v1"
    assert protocol["failure"]["observable_to_agent"] is False
    assert protocol["controls"]["semantics_observable_to_agent"] is False
    assert protocol["plant"]["degrees_of_freedom"] == 6
    assert "crosswind" in protocol["transfer_axes"]
