from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from domains.precision_driving_world import (
    PrecisionDrivingWorld,
    PrecisionDrivingPlantConfig,
)
from scripts import gen_precision_driving_seed
from scripts.benchmark_precision_driving import run_benchmark
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "precision_driving.json"
RUNNER = ROOT / "scripts" / "jabberwock_precision_driving.py"
WORLD = ROOT / "domains" / "precision_driving_world.py"
PROTOCOL = ROOT / "protocols" / "precision_driving_v1.json"


def test_precision_seed_is_generated_and_graph_native():
    payload = json.loads(SEED.read_text(encoding="utf-8"))
    assert payload == gen_precision_driving_seed.manifest()
    assert payload["depends_on"] == [
        "motor_decision_collapse",
        "embodied_structural_limits",
    ]
    names = {rule["name"] for rule in payload["rules"]}
    assert {
        "precision_launch_to_attitude_acquisition",
        "precision_attitude_acquisition_to_hold",
        "precision_hold_to_exit",
        "precision_exit_to_complete",
        "precision_system1_attitude_path_energy_tradeoff",
        "precision_learn_combined_attitude_response",
    } <= names
    serialized = json.dumps(payload)
    for command in (
        "command_steering",
        "command_drive_front_left",
        "command_drive_front_right",
        "command_drive_rear_left",
        "command_drive_rear_right",
        "command_brake_front_left",
        "command_brake_front_right",
        "command_brake_rear_left",
        "command_brake_rear_right",
    ):
        assert command in serialized
    assert "path_tradeoff_weight" in serialized
    assert "PrecisionClipZone" in serialized
    assert "state_preview_far_bearing_rad" in serialized
    assert "clip_commitment" in serialized
    assert "state_slip_angle" in serialized


def test_precision_seed_loads_without_malformed_rule_warning(capsys):
    WorldAdapter(seeds=("precision_driving",))
    captured = capsys.readouterr()
    assert "malformed rule" not in captured.out
    assert "malformed rule" not in captured.err


def test_host_is_transduction_and_reporting_not_driver_policy():
    runner = RUNNER.read_text(encoding="utf-8")
    world = WORLD.read_text(encoding="utf-8")
    assert "agent.tick()" in runner
    assert "def _target_yaw_rate" not in runner
    assert "def _target_slip" not in runner
    assert "command_steering" in runner
    assert "manoeuvre_phase" not in world
    assert "command_steering" not in world
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["guardrails"]


def test_precision_world_has_symmetric_course_geometry_and_smooth_tyres():
    config = PrecisionDrivingPlantConfig()
    assert config.smooth_tyre_saturation is True
    assert config.combined_slip_coupling == 1.0
    assert config.rear_tyre_grip_scale < config.front_tyre_grip_scale
    left = PrecisionDrivingWorld(course="drift_left")
    right = PrecisionDrivingWorld(course="drift_right")
    left_observation = left.reset()
    right_observation = right.reset()
    assert left_observation["precision_course_radius_m"] == pytest.approx(
        right_observation["precision_course_radius_m"]
    )
    assert left_observation["precision_course_direction"] == 1.0
    assert right_observation["precision_course_direction"] == -1.0
    assert left_observation["precision_radial_error_m"] == pytest.approx(0.0)
    assert right_observation["precision_radial_error_m"] == pytest.approx(0.0)
    for horizon in ("near", "middle", "far"):
        assert math.isfinite(
            left_observation[
                f"precision_preview_{horizon}_bearing_rad"
            ]
        )


def test_precision_benchmark_completes_and_holds_declared_angles():
    result = run_benchmark()
    receipts = result["receipts"]["preview_clip"]
    radial_only = result["receipts"]["radial_only"]
    assert all(receipt["completed"] for receipt in receipts.values())
    for side in ("left", "right"):
        drift = receipts[f"drift_{side}"]
        donut = receipts[f"donut_{side}"]
        assert drift["mean_abs_angle_error_rad"] <= 0.06
        assert drift["angle_hold_fraction"] >= 0.9
        assert drift["mean_abs_radial_error_m"] <= 1.0
        assert drift["path_hold_fraction"] >= 0.9
        assert drift["clip_hit_fraction"] >= 0.7
        assert donut["mean_abs_angle_error_rad"] <= 0.025
        assert donut["angle_hold_fraction"] >= 0.98
        assert donut["mean_abs_radial_error_m"] <= 2.0
        assert donut["clip_hit_fraction"] >= 0.3
        assert drift["graph_tick_latency_us"]["p99"] < 1000.0
        assert donut["graph_tick_latency_us"]["p99"] < 1000.0
        assert drift["hold_duration_s"] >= 5.0
        assert donut["hold_duration_s"] >= 5.0
        assert (
            drift["mean_abs_radial_error_m"]
            < radial_only[f"drift_{side}"]["mean_abs_radial_error_m"]
        )
        assert (
            donut["mean_abs_radial_error_m"]
            < radial_only[f"donut_{side}"]["mean_abs_radial_error_m"]
        )
    assert all(
        math.isclose(delta, 0.0, rel_tol=0.0, abs_tol=1e-9)
        for delta in result["symmetry"].values()
    )
