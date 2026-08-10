from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "aerial_adaptation.json"
GENERATOR = ROOT / "scripts" / "gen_aerial_adaptation_seed.py"
RUNNER = ROOT / "scripts" / "jabberwock_aerial_adaptation.py"
ADAPTER = ROOT / "domains" / "gym_pybullet_drone_world.py"
REQUIREMENTS = ROOT / "requirements-drone.txt"
BROKEN_PROP_PROTOCOL = ROOT / "protocols" / "aerial_broken_prop_v1.json"
COMPLETE_PROP_FAILURE_PROTOCOL = (
    ROOT / "protocols" / "aerial_complete_prop_failure_v1.json"
)
DIRECT_RECOVERY_PROTOCOL = (
    ROOT / "protocols" / "aerial_three_rotor_direct_recovery_v1.json"
)


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def test_aerial_seed_owns_three_dimensional_learning_and_flight_judgment():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    chooser = json.dumps(_rule(seed, "aa_choose_learned_flight_action"))
    learner = json.dumps(_rule(seed, "aa_learn_aerial_forward_model"))
    measure = json.dumps(_rule(seed, "aa_measure_flight_state"))

    assert seed["id"] == "aerial_adaptation"
    assert seed["version"] == "1.4.0"
    assert '"type": "Argmin"' in chooser
    for axis in ("dx", "dy", "dz"):
        assert f"mean_{axis}" in chooser
        assert f"observed_{axis}" in learner
    assert "mean_post_vx" in chooser
    assert "surprise_adaptation_rate" in learner
    assert "error_ema" in learner
    assert "mean_dwz" in chooser
    assert "angular_stability_weight" in chooser
    assert _rule(seed, "aa_close_frozen_flight_trial")
    assert "flight_achieved" in measure
    assert "goal_reached" in measure
    assert "peak_altitude_gain" in measure
    detector = json.dumps(
        _rule(seed, "aa_detect_direct_control_emergency")
    )
    direct_control = json.dumps(
        _rule(seed, "aa_direct_three_rotor_reduced_attitude_control")
    )
    assert "failed_motor_ordinal" in detector
    assert "emergency_angular_speed_threshold" in detector
    for motor in range(4):
        assert f"direct_rpm_{motor}" in direct_control
    assert "motor_thrust_coefficient" in direct_control
    assert "maximum_motor_rpm" in direct_control


def test_aerial_runtime_is_transduction_not_python_policy():
    runner = RUNNER.read_text(encoding="utf-8")
    adapter = ADAPTER.read_text(encoding="utf-8")
    generator = GENERATOR.read_text(encoding="utf-8")

    assert 'WorldAdapter(seeds=("aerial_adaptation",))' in runner
    assert '"semantics": "unknown"' in runner
    assert "selected_token" in runner
    assert "world.step(token)" in runner
    assert "predicted_goal_distance" not in runner
    assert "goal_reached_graph_assessment" in runner
    assert "substrate" not in adapter
    assert '"type": "Argmin"' in generator


def test_drone_boundary_has_no_agent_policy_or_learning_api():
    if importlib.util.find_spec("gym_pybullet_drones") is None:
        pytest.skip("install requirements-drone.txt")
    import domains.gym_pybullet_drone_world as module

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
        "set_control_frequency",
        "set_goal",
        "step",
        "step_control_tick",
        "step_motor_rpm",
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


def test_official_simulator_is_pinned_and_opaque_drone_takes_off():
    pytest.importorskip("gym_pybullet_drones")
    pybullet = pytest.importorskip("pybullet")
    from domains.gym_pybullet_drone_world import (
        SIMULATOR_COMMIT,
        GymPyBulletDroneWorld,
    )

    requirement = REQUIREMENTS.read_text(encoding="utf-8")
    assert SIMULATOR_COMMIT in requirement
    with GymPyBulletDroneWorld() as world:
        initial = world.observe()
        options = world.actuator_options()
        assert (
            pybullet.getConnectionInfo(world._environment.CLIENT)[
                "connectionMethod"
            ]
            == pybullet.DIRECT
        )
        assert tuple(row["token"] for row in options) == tuple(
            f"flight_actuator_{index:03d}" for index in range(7)
        )
        assert all(len(row["vector"]) == 4 for row in options)
        assert not any(
            word in row["token"]
            for row in options
            for word in ("up", "down", "left", "right", "hover")
        )
        airborne = world.step("flight_actuator_005")
        assert initial["supplied_energy_joules"] == 0.0
        assert airborne["supplied_energy_joules"] > 0.0
        assert airborne["peak_actuator_power_watts"] > 0.0

    assert airborne["base_position"][2] > initial["base_position"][2]
    assert airborne["last_actuator_token"] == "flight_actuator_005"
    assert airborne["step_index"] > 0


def test_direct_motor_authority_is_explicit_and_runs_at_physics_rate():
    pytest.importorskip("gym_pybullet_drones")
    from domains.gym_pybullet_drone_world import (
        PHYSICS_FREQUENCY_HZ,
        GymPyBulletDroneWorld,
    )

    with GymPyBulletDroneWorld() as stabilized:
        with pytest.raises(RuntimeError, match="not enabled"):
            stabilized.step_motor_rpm((0.0,) * 4)

    with GymPyBulletDroneWorld(
        enable_direct_motor_actuators=True,
    ) as direct:
        parameters = direct.body_parameters()
        direct.set_control_frequency(PHYSICS_FREQUENCY_HZ)
        initial = direct.observe()
        rpm = parameters["maximum_motor_rpm"] * 0.5
        after = direct.step_motor_rpm((rpm,) * 4)
        after_stabilized_action = direct.step("flight_actuator_000")
        with pytest.raises(ValueError):
            direct.set_control_frequency(PHYSICS_FREQUENCY_HZ - 1)

    assert set(parameters) == {
        "body_mass",
        "body_arm_length",
        "motor_thrust_coefficient",
        "maximum_motor_rpm",
        "gravity_acceleration",
    }
    assert after["sim_time"] - initial["sim_time"] == pytest.approx(
        1.0 / PHYSICS_FREQUENCY_HZ
    )
    assert after["step_index"] == initial["step_index"] + 1
    assert after["last_actuator_token"] == "graph_direct_motor_command"
    assert (
        after_stabilized_action["sim_time"] - after["sim_time"]
    ) == pytest.approx(direct.action_duration_seconds)


def test_motor_damage_is_hidden_and_changes_only_post_onset_physics():
    pytest.importorskip("gym_pybullet_drones")
    from domains.gym_pybullet_drone_world import (
        AerialMechanicalCondition,
        GymPyBulletDroneWorld,
    )

    condition = AerialMechanicalCondition(
        onset_action=1,
        motor_rpm_retention=(1.0, 0.9, 1.0, 1.0),
    )
    with (
        GymPyBulletDroneWorld(action_duration_seconds=0.1) as healthy,
        GymPyBulletDroneWorld(
            action_duration_seconds=0.1,
            mechanical_condition=condition,
        ) as damaged,
    ):
        healthy_first = healthy.step("flight_actuator_005")
        damaged_first = damaged.step("flight_actuator_005")
        healthy_after_damage = healthy.step("flight_actuator_001")
        damaged_after_damage = damaged.step("flight_actuator_001")

    assert healthy_first["base_position"] == damaged_first["base_position"]
    assert (
        healthy_after_damage["base_position"]
        != damaged_after_damage["base_position"]
    )
    assert not any(
        "damage" in key or "retention" in key or "condition" in key
        for key in damaged_after_damage
    )


def test_broken_prop_is_hidden_aerodynamic_loss_not_motor_throttling():
    pytest.importorskip("gym_pybullet_drones")
    numpy = pytest.importorskip("numpy")
    from domains.gym_pybullet_drone_world import (
        AerialPropellerCondition,
        GymPyBulletDroneWorld,
    )

    condition = AerialPropellerCondition(
        onset_action=1,
        thrust_retention=(1.0, 0.87, 1.0, 1.0),
        torque_retention=(1.0, 0.74, 1.0, 1.0),
    )
    with (
        GymPyBulletDroneWorld(action_duration_seconds=0.1) as healthy,
        GymPyBulletDroneWorld(
            action_duration_seconds=0.1,
            propeller_condition=condition,
        ) as broken,
    ):
        healthy_first = healthy.step("flight_actuator_005")
        broken_first = broken.step("flight_actuator_005")
        broken._environment._set_propeller_retention(
            condition.thrust_retention,
            condition.torque_retention,
        )
        action = numpy.asarray(
            [[healthy.actuator_options()[1]["vector"]]],
            dtype=numpy.float32,
        ).reshape(1, 4)
        assert numpy.array_equal(
            healthy._environment._preprocessAction(action),
            broken._environment._preprocessAction(action),
        )
        healthy_after_break = healthy.step("flight_actuator_001")
        broken_after_break = broken.step("flight_actuator_001")

    assert healthy_first["base_position"] == broken_first["base_position"]
    assert healthy_after_break["base_position"] != broken_after_break[
        "base_position"
    ]
    assert not any(
        "prop" in key or "damage" in key or "retention" in key
        for key in broken_after_break
    )

    adapter = ADAPTER.read_text(encoding="utf-8")
    preprocessing = adapter.split("def _preprocessAction", 1)[1].split(
        "def _physics", 1
    )[0]
    physics = adapter.split("def _physics", 1)[1].split(
        "def _triple", 1
    )[0]
    assert "_prop_thrust_retention" not in preprocessing
    assert "_prop_thrust_retention" in physics
    assert "_prop_torque_retention" in physics


@pytest.mark.parametrize(
    "kwargs",
    [
        {"onset_action": -1, "motor_rpm_retention": (1.0,) * 4},
        {"onset_action": 1, "motor_rpm_retention": (1.0,) * 3},
        {
            "onset_action": 1,
            "motor_rpm_retention": (1.0, 1.1, 1.0, 1.0),
        },
    ],
)
def test_invalid_aerial_mechanical_damage_is_rejected(kwargs):
    from domains.gym_pybullet_drone_world import AerialMechanicalCondition

    with pytest.raises(ValueError):
        AerialMechanicalCondition(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "onset_action": -1,
            "thrust_retention": (1.0,) * 4,
            "torque_retention": (1.0,) * 4,
        },
        {
            "onset_action": 1,
            "thrust_retention": (1.0,) * 3,
            "torque_retention": (1.0,) * 4,
        },
        {
            "onset_action": 1,
            "thrust_retention": (1.0,) * 4,
            "torque_retention": (1.0, -0.1, 1.0, 1.0),
        },
    ],
)
def test_invalid_broken_prop_condition_is_rejected(kwargs):
    from domains.gym_pybullet_drone_world import AerialPropellerCondition

    with pytest.raises(ValueError):
        AerialPropellerCondition(**kwargs)


def test_fresh_graph_learns_and_flies_to_unseen_spatial_goal():
    pytest.importorskip("gym_pybullet_drones")
    from scripts.jabberwock_aerial_adaptation import run_flight

    result = run_flight(
        steps=80,
        goal=(-0.6, 0.6, 0.9),
        seed=11,
        babble_samples=2,
    )

    assert result["fresh_substrate"] is True
    assert result["policy_owner"] == "rust_graph"
    assert result["flight_achieved_graph_assessment"] == 1.0
    assert result["goal_reached_graph_assessment"] == 1.0
    assert result["final_goal_distance"] < result["initial_goal_distance"]
    assert all(model["experience_count"] >= 2 for model in result["models"])
    assert {row["decision_kind"] for row in result["trace"]} == {
        "motor_babble",
        "shared_flight_model",
    }
    assert all(row["trial_status"] == "learned" for row in result["trace"])


def test_hidden_in_flight_damage_recovery_beats_frozen_graph():
    pytest.importorskip("gym_pybullet_drones")
    from scripts.jabberwock_aerial_damage_trial import run_damage_trial

    result = run_damage_trial()

    assert result["damage_is_observable_to_graph"] is False
    assert result["pre_damage_trajectories_identical"] is True
    assert result["adaptive"]["surprise_events"] > 0
    assert result["adaptive"]["learning_actions"] > 0
    assert result["frozen"]["learning_actions"] == 0
    assert result["adaptive"]["contact_actions"] == 0
    assert result["frozen"]["contact_actions"] == 0
    assert result["adaptive"]["goal_reached_at_end"] == 1.0
    assert result["frozen"]["goal_reached_at_end"] == 0.0
    assert result["paired_effect"]["final_distance_reduction"] > 0.0


def test_hidden_broken_prop_recovery_beats_frozen_graph():
    pytest.importorskip("gym_pybullet_drones")
    from scripts.jabberwock_aerial_damage_trial import run_damage_trial

    result = run_damage_trial(BROKEN_PROP_PROTOCOL)

    assert result["damage_kind"] == "broken_propeller"
    assert result["damage_is_observable_to_graph"] is False
    assert result["pre_damage_trajectories_identical"] is True
    assert len(result["runs"]["adaptive"]["action_alphabet"]) == 9
    assert result["adaptive"]["surprise_events"] > 0
    assert result["adaptive"]["contact_actions"] == 0
    assert result["frozen"]["contact_actions"] == 0
    assert result["adaptive"]["goal_reached_at_end"] == 1.0
    assert result["frozen"]["goal_reached_at_end"] == 0.0
    assert result["paired_effect"]["final_distance_reduction"] > 0.8
    assert result["paired_effect"]["mean_angular_speed_reduction"] > 0.0


def test_complete_prop_loss_exposes_three_rotor_control_limit():
    pytest.importorskip("gym_pybullet_drones")
    from scripts.jabberwock_aerial_damage_trial import run_damage_trial

    result = run_damage_trial(COMPLETE_PROP_FAILURE_PROTOCOL)

    assert result["damage_kind"] == "broken_propeller"
    assert result["pre_damage_trajectories_identical"] is True
    assert result["state_before_damage"]["position"][2] > 0.8
    assert result["adaptive"]["surprise_events"] > 0
    assert result["adaptive"]["goal_reached_at_end"] == 0.0
    assert result["frozen"]["goal_reached_at_end"] == 0.0
    assert result["adaptive"]["first_contact_action"] == 72
    assert result["frozen"]["first_contact_action"] == 72
    assert result["adaptive"]["contact_latency_seconds"] == 0.75
    assert result["adaptive"]["peak_angular_speed"] > 30.0
    assert result["frozen"]["peak_angular_speed"] > 30.0
    assert {
        row["first_contact_latency_seconds"]
        for row in result["forced_action_controls"]
    } == {0.75}


def test_graph_direct_authority_recovers_complete_prop_loss():
    pytest.importorskip("gym_pybullet_drones")
    from domains.gym_pybullet_drone_world import PHYSICS_FREQUENCY_HZ
    from scripts.jabberwock_aerial_direct_recovery import run_direct_recovery

    result = run_direct_recovery(DIRECT_RECOVERY_PROTOCOL)

    assert result["policy_owner"] == "rust_graph"
    assert result["pre_failure_replay_identical"] is True
    assert result["state_before_failure"]["position"][2] > 0.8
    assert result["detection_ticks"] == 2
    assert result["detection_latency_seconds"] == pytest.approx(
        2.0 / PHYSICS_FREQUENCY_HZ
    )
    assert result["failed_motor_ordinal_graph"] == 1.0
    assert result["control_mode"] == "three_rotor_direct"
    assert result["recovery_control_hz"] == PHYSICS_FREQUENCY_HZ
    assert result["direct_command_count"] == result["recovery_ticks"]
    assert result["contact_ticks"] == 0
    assert result["minimum_altitude"] > 0.8
    assert result["hold_position_error"] < 0.01

    runner = (
        ROOT / "scripts" / "jabberwock_aerial_direct_recovery.py"
    ).read_text(encoding="utf-8")
    assert "step_motor_rpm" in runner
    assert "computeControl" not in runner
    assert "motor_thrust_coefficient" not in runner
