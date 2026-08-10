from __future__ import annotations

import json
import math
from pathlib import Path

from domains.gymkhana_driving_world import GymkhanaDrivingWorld
from domains.trajectory_geometry import preview_receipt
from domains.vectoring_jet_world import VectoringJetWorld
from scripts import gen_attitude_trajectory_seed
from scripts import gen_precision_driving_seed
from scripts.jabberwock_attitude_trajectory import run_attitude_trajectory
from scripts.jabberwock_gymkhana import run_gymkhana


ROOT = Path(__file__).resolve().parents[1]


def test_generated_manifests_match_checked_in_seeds() -> None:
    assert json.loads(
        (ROOT / "seeds" / "attitude_trajectory.json").read_text()
    ) == gen_attitude_trajectory_seed.manifest()
    assert json.loads(
        (ROOT / "seeds" / "precision_driving.json").read_text()
    ) == gen_precision_driving_seed.manifest()


def test_preview_receipt_is_body_relative_and_vehicle_independent() -> None:
    receipt = preview_receipt(
        observer_x_m=1.0,
        observer_y_m=2.0,
        observer_yaw_rad=math.pi * 0.5,
        target_x_m=1.0,
        target_y_m=12.0,
        target_heading_rad=math.pi * 0.5,
    )
    assert math.isclose(receipt.forward_m, 10.0, abs_tol=1e-9)
    assert math.isclose(receipt.lateral_m, 0.0, abs_tol=1e-9)
    assert math.isclose(receipt.heading_error_rad, 0.0, abs_tol=1e-9)


def test_vectoring_jet_plant_has_no_target_or_controller() -> None:
    source = (ROOT / "domains" / "vectoring_jet_world.py").read_text()
    assert "target_" not in source
    assert "reward" not in source
    world = VectoringJetWorld()
    before = world.reset()
    after = world.step({
        "throttle": 0.5,
        "lateral_vector": 0.2,
        "yaw_vector": 0.3,
    })
    assert after["time_s"] > before["time_s"]
    assert after["yaw_rate_rad_s"] > 0.0


def test_jet_graph_separates_body_turn_from_forward_trajectory() -> None:
    result = run_attitude_trajectory()
    metrics = result["metrics"]
    assert metrics["completed_body_turns"] >= 0.98
    assert metrics["minimum_forward_velocity_m_s"] >= 70.0
    assert metrics["maximum_velocity_heading_error_deg"] <= 3.0
    assert metrics["final_yaw_error_deg"] <= 2.0


def test_gymkhana_geometry_changes_curvature_sign() -> None:
    world = GymkhanaDrivingWorld()
    assert min(world._curvatures) < -0.05
    assert max(world._curvatures) > 0.05
    assert world.track_length_m > 250.0


def test_preview_graph_completes_gymkhana_and_beats_reactive() -> None:
    reactive = run_gymkhana(
        duration_s=55.0,
        trajectory_architecture="reactive_tangent",
    )
    preview = run_gymkhana(
        duration_s=55.0,
        trajectory_architecture="preview_clip",
    )
    reactive_metrics = reactive["metrics"]
    preview_metrics = preview["metrics"]
    assert preview_metrics["completed_laps"] >= 1
    assert preview_metrics["mean_absolute_path_error_m"] <= 4.0
    assert preview_metrics["offtrack_time_s"] <= 6.0
    assert (
        preview_metrics["mean_absolute_path_error_m"]
        < reactive_metrics["mean_absolute_path_error_m"]
    )
