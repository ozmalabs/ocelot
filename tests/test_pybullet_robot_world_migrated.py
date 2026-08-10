from __future__ import annotations

import ast
import inspect
import json
import math

import pytest

pybullet = pytest.importorskip("pybullet")

from domains.pybullet_robot_world import (
    MORPHOLOGIES,
    MechanicalCondition,
    MechanicalRandomization,
    PyBulletRobotWorld,
)


@pytest.mark.parametrize("morphology", MORPHOLOGIES)
def test_each_body_resets_headlessly_with_raw_sensor_state(morphology):
    with PyBulletRobotWorld(morphology, goal=(2.0, -1.0, 0.0)) as world:
        initial = world.observe()

        assert pybullet.getConnectionInfo(world._client)["connectionMethod"] == pybullet.DIRECT
        assert initial["morphology"] == morphology
        assert initial["step_index"] == 0
        assert initial["sim_time"] == 0.0
        assert initial["goal_position"] == (2.0, -1.0, 0.0)
        assert len(initial["base_position"]) == 3
        assert len(initial["base_orientation_xyzw"]) == 4
        assert len(initial["base_linear_velocity"]) == 3
        assert len(initial["base_angular_velocity"]) == 3
        assert initial["joints"]
        assert initial["contacts"]
        assert initial["supplied_energy_joules"] == 0.0
        assert initial["absorbed_energy_joules"] == 0.0
        json.dumps(initial)


@pytest.mark.parametrize("morphology", MORPHOLOGIES)
def test_common_tokens_are_opaque_and_advance_fixed_step_physics(morphology):
    with PyBulletRobotWorld(morphology, control_steps=12) as world:
        initial_position = world.observe()["base_position"]
        options = world.actuator_options()
        assert tuple(option["token"] for option in options) == tuple(
            f"actuator_{index:03d}" for index in range(9)
        )
        assert all(
            set(option) == {"token", "vector", "effector_commands"}
            for option in options
        )
        assert all(len(option["vector"]) == 2 for option in options)
        assert all(
            tuple(value for _channel, value in option["effector_commands"])
            == option["vector"]
            for option in options
        )
        assert not any(
            directional_word in option["token"]
            for option in options
            for directional_word in ("forward", "back", "left", "right", "turn", "stop")
        )

        observation = world.step("actuator_005")

        assert observation["step_index"] == 12
        assert observation["sim_time"] == pytest.approx(0.1)
        assert observation["last_actuator_token"] == "actuator_005"
        assert observation["last_actuator_vector"] == (1.0, 1.0)
        assert observation["supplied_energy_joules"] >= 0.0
        assert observation["absorbed_energy_joules"] >= 0.0
        assert observation["peak_actuator_power_watts"] >= 0.0
        assert all(math.isfinite(value) for value in observation["base_position"])

        later = world.step("actuator_005", frames=48)
        displacement = math.dist(initial_position, later["base_position"])
        assert displacement > 0.01


@pytest.mark.parametrize("morphology", MORPHOLOGIES)
def test_reset_is_fresh_and_deterministic_for_each_morphology(morphology):
    with PyBulletRobotWorld(morphology, seed=17) as world:
        first = world.observe()
        world.apply("actuator_005", steps=48)
        reset = world.reset()

        for key in (
            "base_position",
            "base_orientation_xyzw",
            "base_linear_velocity",
            "base_angular_velocity",
        ):
            assert reset[key] == pytest.approx(first[key], abs=1.0e-12)
        assert reset["step_index"] == 0
        assert reset["last_actuator_token"] is None
        assert reset["last_actuator_vector"] is None


def test_boundary_contains_no_agent_policy_or_learning_api():
    import domains.pybullet_robot_world as module

    tree = ast.parse(inspect.getsource(module))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    public_methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }

    assert imported_roots.isdisjoint({"substrate", "substrate_rs"})
    assert public_methods == {
        "actuator_options",
        "apply",
        "close",
        "observe",
        "reset",
            "set_goal",
            "step",
            "step_program",
        }
    assert not {"choose", "decide", "learn", "plan", "predict", "reward", "score"} & public_methods


def test_invalid_tokens_and_closed_world_fail_explicitly():
    world = PyBulletRobotWorld("r2d2")
    with pytest.raises(ValueError, match="unknown actuator token"):
        world.apply("forward")
    world.close()
    world.close()
    with pytest.raises(RuntimeError, match="closed"):
        world.observe()


@pytest.mark.parametrize(
    "kwargs",
    (
        {"onset_action": -1},
        {"onset_action": 0, "abrupt_retention": (1.1, 1.0)},
        {"onset_action": 0, "wear_per_use": (-0.1, 0.0)},
        {"onset_action": 0, "minimum_retention": 2.0},
    ),
)
def test_invalid_mechanical_conditions_are_refused(kwargs):
    with pytest.raises(ValueError):
        MechanicalCondition(**kwargs)


def test_hidden_dynamics_randomization_and_goal_change_are_mechanical_only():
    randomized = MechanicalRandomization(
        base_mass_scale=1.2,
        lateral_friction=0.55,
        rolling_friction=0.01,
        motor_force_scale=0.8,
    )
    with PyBulletRobotWorld(
        "r2d2",
        mechanical_randomization=randomized,
    ) as world:
        changed = world.set_goal((1.0, -2.0, 0.0))
        observation = world.step("actuator_005")

    assert changed["goal_position"] == (1.0, -2.0, 0.0)
    assert observation["goal_position"] == (1.0, -2.0, 0.0)
    assert not any(
        forbidden in observation
        for forbidden in ("mass_scale", "friction", "motor_force_scale")
    )


def test_hidden_damage_preserves_pre_onset_dynamics_then_changes_consequences():
    condition = MechanicalCondition(
        onset_action=2,
        abrupt_retention=(0.0, 1.0),
    )
    with (
        PyBulletRobotWorld("r2d2") as healthy,
        PyBulletRobotWorld("r2d2", mechanical_condition=condition) as damaged,
    ):
        healthy_rows = [healthy.step("actuator_005") for _ in range(4)]
        damaged_rows = [damaged.step("actuator_005") for _ in range(4)]

    assert healthy_rows[0]["base_position"] == damaged_rows[0]["base_position"]
    assert healthy_rows[1]["base_position"] == damaged_rows[1]["base_position"]
    assert healthy_rows[2]["base_position"] != damaged_rows[2]["base_position"]
    for row in damaged_rows:
        assert row["last_actuator_token"] == "actuator_005"
        assert row["last_actuator_vector"] == (1.0, 1.0)
        assert not any(
            forbidden in row
            for forbidden in (
                "damage",
                "wear",
                "retention",
                "effective_vector",
                "condition",
            )
        )


def test_progressive_wear_state_is_reset_with_the_world():
    condition = MechanicalCondition(
        onset_action=0,
        wear_per_use=(0.1, 0.0),
        minimum_retention=0.2,
    )
    with PyBulletRobotWorld("racecar", mechanical_condition=condition) as world:
        first = [world.step("actuator_005")["base_position"] for _ in range(5)]
        world.reset()
        replay = [world.step("actuator_005")["base_position"] for _ in range(5)]
    assert replay == pytest.approx(first, abs=1.0e-12)
