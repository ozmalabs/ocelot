from __future__ import annotations

import json
from pathlib import Path

import pytest

from domains.full_racing_world import (
    FullRacingWorld,
    RacingDamage,
    RacingPlantConfig,
)
from domains.speed_dreams_racing_world import (
    COMMAND_MAGIC,
    COMMAND_STRUCT,
    PROTOCOL_VERSION,
    TELEMETRY_MAGIC,
    TELEMETRY_STRUCT,
    decode_telemetry,
    encode_command,
)
from scripts import gen_racing_cognition_seed
from scripts.jabberwock_full_racing import run_race
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "racing_cognition.json"
GENERATOR = ROOT / "scripts" / "gen_racing_cognition_seed.py"
RUNNER = ROOT / "scripts" / "jabberwock_full_racing.py"
WORLD = ROOT / "domains" / "full_racing_world.py"
PROTOCOL = ROOT / "protocols" / "full_racing_v1.json"
BASELINE = ROOT / "results" / "full_racing_baseline_v1.json"
DAMAGE = ROOT / "results" / "full_racing_damage_v1.json"
SPEED_DREAMS_BRIDGE = (
    ROOT / "simulators" / "speed_dreams_jabberwock" / "jabberwock.cpp"
)


def test_racing_seed_is_generated_and_shared_core_backed():
    payload = json.loads(SEED.read_text(encoding="utf-8"))
    assert payload == gen_racing_cognition_seed.manifest()
    assert payload["depends_on"] == [
        "embodied_pareto_profile",
        "motor_decision_collapse",
        "embodied_structural_limits",
    ]
    names = {rule["name"] for rule in payload["rules"]}
    assert {
        "race_system1_coupled_fast_control",
        "race_learn_dynamics_from_exact_receipt",
        "race_learn_resource_rates_from_exact_receipt",
        "race_close_unexcited_receipt",
        "race_system2_dynamic_pareto_envelope",
    } <= names
    serialized = json.dumps(payload)
    for output in (
        "command_steering",
        "command_throttle",
        "command_brake",
        "command_drive_front_left",
        "command_drive_front_right",
        "command_drive_rear_left",
        "command_drive_rear_right",
        "command_brake_front_left",
        "command_brake_front_right",
        "command_brake_rear_left",
        "command_brake_rear_right",
        "command_front_wing",
        "command_rear_wing",
        "command_gear",
        "command_pit",
    ):
        assert output in serialized
    assert "state_curvature_envelope_far" in serialized
    assert "state_opponent_gap_m" in serialized
    assert "learned_steering_response" in serialized
    assert "model_surprise" in serialized


def test_strategy_library_is_non_dominated_on_declared_objectives():
    payload = json.loads(SEED.read_text(encoding="utf-8"))
    candidates = [
        node["attrs"]
        for node in payload["nodes"]
        if node["type"] == "RacingStrategyCandidate"
    ]
    assert len(candidates) >= 6
    assert all(0.0 < candidate["pit_threshold"] < 2.0 for candidate in candidates)
    objectives = ("fuel_cost", "tyre_cost", "contact_risk")
    for candidate in candidates:
        dominators = []
        for other in candidates:
            if other is candidate:
                continue
            no_worse = (
                other["pace_fraction"] >= candidate["pace_fraction"]
                and all(other[key] <= candidate[key] for key in objectives)
            )
            strictly_better = (
                other["pace_fraction"] > candidate["pace_fraction"]
                or any(other[key] < candidate[key] for key in objectives)
            )
            if no_worse and strictly_better:
                dominators.append(other["ordinal"])
        assert dominators == []


def test_graph_seed_loads_without_malformed_rule_warning(capsys):
    WorldAdapter(seeds=("racing_cognition",))
    captured = capsys.readouterr()
    assert "malformed rule" not in captured.out
    assert "malformed rule" not in captured.err


def test_host_files_are_plant_and_transduction_not_driver_policy():
    runner = RUNNER.read_text(encoding="utf-8")
    world = WORLD.read_text(encoding="utf-8")
    generator = GENERATOR.read_text(encoding="utf-8")
    assert "_target_speed" not in runner
    assert "_desired_steering" not in runner
    assert "command_steering" in runner
    assert "agent.tick()" in runner
    assert "target_speed_m_s" not in world
    assert "overtake" not in world.lower()
    assert "def recovery" not in world.lower()
    assert "recovery_command" not in world.lower()
    assert "race_system1_coupled_fast_control" in generator
    assert "following_distance_gain" in generator


def test_speed_dreams_packets_match_the_bridge_abi():
    assert TELEMETRY_STRUCT.size == 328
    assert COMMAND_STRUCT.size == 136
    payload = TELEMETRY_STRUCT.pack(
        TELEMETRY_MAGIC,
        PROTOCOL_VERSION,
        TELEMETRY_STRUCT.size,
        17,
        *[float(index) for index in range(36)],
        *range(6),
    )
    telemetry = decode_telemetry(payload)
    assert telemetry["sequence"] == 17
    assert telemetry["simulation_time_s"] == 0.0
    assert telemetry["engine_rpm"] == 35.0
    assert telemetry["gear"] == 0
    assert telemetry["total_laps"] == 5

    command = encode_command(17, {
        "steering": -0.25,
        "throttle": 0.7,
        "brake": 0.0,
        "drive_front_left": 0.7,
        "drive_front_right": 0.7,
        "drive_rear_left": 0.7,
        "drive_rear_right": 0.7,
        "brake_front_left": 0.0,
        "brake_front_right": 0.0,
        "brake_rear_left": 0.0,
        "brake_rear_right": 0.0,
        "clutch": 0.1,
        "front_wing": 0.2,
        "rear_wing": 0.3,
        "gear": 3,
        "pit_request": 1,
    })
    unpacked = COMMAND_STRUCT.unpack(command)
    assert unpacked[:4] == (
        COMMAND_MAGIC,
        PROTOCOL_VERSION,
        COMMAND_STRUCT.size,
        17,
    )
    assert unpacked[4:] == pytest.approx(
        (
            -0.25,
            0.7,
            0.0,
            0.1,
            0.2,
            0.3,
            0.7,
            0.7,
            0.7,
            0.7,
            0.0,
            0.0,
            0.0,
            0.0,
            3,
            1,
        )
    )


def test_speed_dreams_bridge_is_modern_policy_free_transduction():
    source = SPEED_DREAMS_BRIDGE.read_text(encoding="utf-8")
    assert "moduleWelcome" in source
    assert "moduleInitialize" in source
    assert "moduleTerminate" in source
    assert "static_assert(sizeof(TelemetryPacket) == 328)" in source
    assert "static_assert(sizeof(CommandPacket) == 136)" in source
    for forbidden in (
        "target_speed",
        "racing_line",
        "overtake",
        "recovery_controller",
        "pareto",
    ):
        assert forbidden not in source.lower()


def test_world_is_deterministic_and_applies_physical_damage():
    action = {
        "steering": 0.28,
        "throttle": 0.7,
        "brake": 0.0,
        "drive_front_left": 0.7,
        "drive_front_right": 0.7,
        "drive_rear_left": 0.7,
        "drive_rear_right": 0.7,
        "brake_front_left": 0.0,
        "brake_front_right": 0.0,
        "brake_rear_left": 0.0,
        "brake_rear_right": 0.0,
        "front_wing": 0.5,
        "rear_wing": 0.6,
        "gear": 2,
        "pit_request": 0,
    }
    damage = RacingDamage(
        onset_s=0.0,
        steering_retention=0.35,
        power_retention=0.5,
        front_brake_retention=0.4,
        aero_retention=0.6,
        yaw_bias_nm=300.0,
    )
    first = FullRacingWorld(seed=7, damage=damage, opponent_count=0)
    second = FullRacingWorld(seed=7, damage=damage, opponent_count=0)
    first_observation = second_observation = None
    for _ in range(80):
        first_observation = first.step(action)
        second_observation = second.step(action)
    assert first_observation == second_observation
    assert first_observation is not None
    assert first_observation["damage_active"] == 1.0
    assert first_observation["receipt_steering_retention"] == 0.35
    assert first_observation["receipt_power_retention"] == 0.5
    assert first_observation["receipt_front_brake_retention"] == 0.4
    assert first_observation["receipt_aero_retention"] == 0.6


def test_world_rejects_incomplete_or_opposed_pedal_receipts():
    world = FullRacingWorld(opponent_count=0)
    with pytest.raises(ValueError, match="missing"):
        world.step({"steering": 0.0})
    with pytest.raises(ValueError, match="exclusive"):
        world.step({
            "steering": 0.0,
            "throttle": 0.5,
            "brake": 0.5,
            "drive_front_left": 0.0,
            "drive_front_right": 0.0,
            "drive_rear_left": 0.0,
            "drive_rear_right": 0.0,
            "brake_front_left": 0.0,
            "brake_front_right": 0.0,
            "brake_rear_left": 0.0,
            "brake_rear_right": 0.0,
            "front_wing": 0.0,
            "rear_wing": 0.0,
            "gear": 1,
            "pit_request": 0,
        })


def test_short_closed_loop_run_is_graph_authored_and_bounded():
    result = run_race(
        duration_s=4.0,
        seed=3,
        opponent_count=1,
        trace_hz=1.0,
    )
    assert result["control_hz"] == 50.0
    assert result["physics_hz"] == 250.0
    assert result["total_progress_m"] > 30.0
    assert result["graph_tick_latency_us"]["p99"] < 2000.0
    assert result["trace"]
    for row in result["trace"]:
        action = row["action"]
        assert -1.0 <= action["steering"] <= 1.0
        assert 0.0 <= action["throttle"] <= 1.0
        assert 0.0 <= action["brake"] <= 1.0
        assert not (action["throttle"] > 0.0 and action["brake"] > 0.0)
        assert action["drive_front_left"] == pytest.approx(
            action["drive_front_right"]
        )
        assert action["drive_rear_left"] == pytest.approx(
            action["drive_rear_right"]
        )


def test_differential_control_authors_individual_wheel_yaw_moment():
    result = run_race(
        duration_s=30.0,
        seed=3,
        opponent_count=0,
        trace_hz=5.0,
        control_architecture="differential",
    )
    assert result["control_architecture"] == "differential"
    assert any(
        abs(row["differential_yaw_request"]) > 0.01
        for row in result["trace"]
    )
    assert any(
        abs(row["differential_yaw_moment_nm"]) > 100.0
        for row in result["trace"]
    )
    assert any(
        abs(
            row["action"]["drive_front_left"]
            - row["action"]["drive_front_right"]
        ) > 0.001
        for row in result["trace"]
    )
    assert any(
        abs(
            row["action"]["brake_rear_left"]
            - row["action"]["brake_rear_right"]
        ) > 0.001
        for row in result["trace"]
    )


def test_system2_moves_on_pareto_front_and_commits_pit_for_shortfall():
    result = run_race(
        duration_s=2.0,
        seed=4,
        opponent_count=0,
        trace_hz=4.0,
        world_config=RacingPlantConfig(fuel_capacity_l=0.35),
    )
    trace = result["trace"]
    assert any(row["fuel_pressure"] > 1.0 for row in trace)
    assert any(row["pit_commit"] for row in trace)
    assert any(
        row["pit_pressure"] > row["strategy_pit_threshold"]
        for row in trace
    )
    assert any(row["strategy_fuel_cost"] <= 0.56 for row in trace)
    assert all(0 <= row["strategy_ordinal"] < 8 for row in trace)


def test_checked_runs_satisfy_preregistered_race_and_damage_gates():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    damage = json.loads(DAMAGE.read_text(encoding="utf-8"))
    gates = protocol["success_gates"]
    assert baseline["laps"] >= gates["baseline_completed_laps_minimum"]
    assert (
        baseline["offtrack_time_s"]
        <= gates["baseline_offtrack_time_s_maximum"]
    )
    assert baseline["collisions"] <= gates["baseline_collisions_maximum"]
    assert damage["laps"] >= gates["damage_completed_laps_minimum"]
    assert (
        damage["total_progress_m"] / baseline["total_progress_m"]
        >= gates["damage_progress_retention_minimum"]
    )
    assert (
        damage["offtrack_time_s"]
        <= gates["damage_offtrack_time_s_maximum"]
    )
    assert (
        baseline["graph_tick_latency_us"]["p99"]
        <= gates["graph_tick_p99_us_maximum"]
    )
    assert (
        damage["graph_tick_latency_us"]["p99"]
        <= gates["graph_tick_p99_us_maximum"]
    )
