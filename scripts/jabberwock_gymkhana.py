#!/usr/bin/env python3
"""Run the generalized precision graph on changing gymkhana geometry."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.embodied_graph_transducer import (  # noqa: E402
    add_unchecked_edge as _edge,
    stamp_attrs,
)
from domains.gymkhana_driving_world import GymkhanaDrivingWorld  # noqa: E402
from scripts.jabberwock_precision_driving import _graph_action  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


GYMKHANA_MANOEUVRE_ORDINAL = 4.0
PATH_HOLD_TOLERANCE_M = 2.0


def _sensed_attrs(observation: dict[str, Any]) -> dict[str, float]:
    lateral = float(observation["gymkhana_path_lateral_error_m"])
    return {
        "state_time_s": float(observation["time_s"]),
        "state_speed_m_s": float(observation["speed_m_s"]),
        "state_body_vx_m_s": float(observation["body_vx_m_s"]),
        "state_body_vy_m_s": float(observation["body_vy_m_s"]),
        "state_yaw_rate_rad_s": float(observation["yaw_rate_rad_s"]),
        "state_slip_angle": float(observation["slip_angle_rad"]),
        "state_radial_error_m": lateral,
        "state_path_lateral_error_m": lateral,
        "state_tangent_heading_error_rad": float(
            observation["gymkhana_tangent_heading_error_rad"]
        ),
        "state_angular_travel_rad": (
            2.0
            * math.pi
            * (
                float(observation["laps"])
                + float(observation["track_progress_m"])
                / float(observation["track_length_m"])
            )
        ),
        "state_path_phase_rad": float(
            observation["gymkhana_path_phase_rad"]
        ),
        "state_path_length_m": float(
            observation["gymkhana_path_length_m"]
        ),
        "state_path_curvature_now_inv_m": float(
            observation["gymkhana_path_curvature_now_inv_m"]
        ),
        "state_path_curvature_near_inv_m": float(
            observation["gymkhana_path_curvature_near_inv_m"]
        ),
        "state_path_curvature_middle_inv_m": float(
            observation["gymkhana_path_curvature_middle_inv_m"]
        ),
        "state_path_curvature_far_inv_m": float(
            observation["gymkhana_path_curvature_far_inv_m"]
        ),
        "state_path_curvature_envelope_inv_m": float(
            observation["gymkhana_path_curvature_envelope_inv_m"]
        ),
        "state_preview_near_bearing_rad": float(
            observation["gymkhana_preview_near_bearing_rad"]
        ),
        "state_preview_middle_bearing_rad": float(
            observation["gymkhana_preview_middle_bearing_rad"]
        ),
        "state_preview_far_bearing_rad": float(
            observation["gymkhana_preview_far_bearing_rad"]
        ),
        "state_preview_far_heading_error_rad": float(
            observation["gymkhana_preview_far_heading_error_rad"]
        ),
        "state_tyre_condition": float(observation["tyre_condition_mean"]),
        "state_tyre_temperature_c": float(
            observation["tyre_temperature_mean_c"]
        ),
        "state_fuel_l": float(observation["fuel_l"]),
    }


def run_gymkhana(
    *,
    duration_s: float = 35.0,
    seed: int = 0,
    trace_hz: float = 10.0,
    trajectory_architecture: str = "preview_clip",
) -> dict[str, Any]:
    if trajectory_architecture not in {"reactive_tangent", "preview_clip"}:
        raise ValueError(
            "trajectory_architecture must be reactive_tangent or preview_clip"
        )
    world = GymkhanaDrivingWorld(seed=seed)
    observation = world.reset()
    agent = WorldAdapter(seeds=("precision_driving",))
    episode = agent.s.add_node("PrecisionDrivingEpisode", {
        "manoeuvre_ordinal": GYMKHANA_MANOEUVRE_ORDINAL,
        "preview_authority": float(
            trajectory_architecture == "preview_clip"
        ),
        "manoeuvre_phase": 0.0,
        "phase_start_time_s": 0.0,
        "phase_start_angular_travel_rad": 0.0,
        "phase_decision_seq": 0.0,
        "request_seq": 0.0,
        "decision_seq": 0.0,
        "action_ready": 0.0,
        "receipt_pending": 0.0,
        "receipt_seq": 0.0,
        "learned_receipt_seq": 0.0,
        "receipt_yaw_request": 0.0,
        "receipt_yaw_rate_delta": 0.0,
        "receipt_slip_delta": 0.0,
        "learned_yaw_response": 0.02,
        "learned_slip_response": 0.01,
        "target_slip_rad": 0.0,
        "target_yaw_rate_rad_s": 0.0,
        "target_speed_m_s": 0.0,
        "attitude_cost": 0.0,
        "yaw_cost": 0.0,
        "path_cost": 0.0,
        "path_tradeoff_weight": 0.0,
        "energy_cost": 0.0,
        "selected_clip_ordinal": 0.0,
        "clip_ahead_distance_m": 0.0,
        "clip_commitment": 0.0,
        "clip_target_radial_offset_m": 0.0,
        "clip_path_command": 0.0,
        "preview_path_command": 0.0,
        "command_steering": 0.0,
        "command_throttle": 0.0,
        "command_brake": 0.0,
        "command_differential_yaw_request": 0.0,
        "command_drive_front_left": 0.0,
        "command_drive_front_right": 0.0,
        "command_drive_rear_left": 0.0,
        "command_drive_rear_right": 0.0,
        "command_brake_front_left": 0.0,
        "command_brake_front_right": 0.0,
        "command_brake_rear_left": 0.0,
        "command_brake_rear_right": 0.0,
        "command_front_wing": 0.0,
        "command_rear_wing": 0.0,
        "command_gear": 1.0,
        "command_pit": 0.0,
        **_sensed_attrs(observation),
    })
    _edge(agent, agent.agent, "has_precision_episode", episode)

    step_count = int(round(duration_s * world.config.control_hz))
    trace_interval = max(
        1, int(round(world.config.control_hz / trace_hz))
    )
    previous_slip = float(observation["slip_angle_rad"])
    previous_yaw_rate = float(observation["yaw_rate_rad_s"])
    previous_yaw_request = 0.0
    graph_latencies_us: list[float] = []
    trace: list[dict[str, float]] = []
    absolute_path_error_sum = 0.0
    path_hold_samples = 0
    maximum_path_error = 0.0
    maximum_abs_slip = 0.0
    clip_samples = 0
    clip_hit_samples = 0

    for request_seq in range(1, step_count + 1):
        stamp_attrs(agent, episode, {
            **_sensed_attrs(observation),
            "request_seq": float(request_seq),
            "action_ready": 0.0,
            "receipt_pending": float(request_seq > 1),
            "receipt_seq": float(request_seq - 1),
            "receipt_yaw_request": previous_yaw_request,
            "receipt_yaw_rate_delta": (
                float(observation["yaw_rate_rad_s"]) - previous_yaw_rate
            ),
            "receipt_slip_delta": (
                float(observation["slip_angle_rad"]) - previous_slip
            ),
        })
        started_ns = time.perf_counter_ns()
        agent.tick()
        graph_latencies_us.append((time.perf_counter_ns() - started_ns) / 1000.0)
        attrs = agent.s.node(episode)["attrs"]
        action = _graph_action(agent, episode)
        previous_slip = float(observation["slip_angle_rad"])
        previous_yaw_rate = float(observation["yaw_rate_rad_s"])
        previous_yaw_request = float(
            attrs["command_differential_yaw_request"]
        )
        observation = world.step(action)

        path_error = abs(
            float(observation["gymkhana_path_lateral_error_m"])
        )
        absolute_path_error_sum += path_error
        path_hold_samples += int(path_error <= PATH_HOLD_TOLERANCE_M)
        maximum_path_error = max(maximum_path_error, path_error)
        maximum_abs_slip = max(
            maximum_abs_slip,
            abs(float(observation["slip_angle_rad"])),
        )
        if float(attrs["clip_commitment"]) >= 0.75:
            clip_samples += 1
            clip_error = abs(
                float(observation["gymkhana_path_lateral_error_m"])
                - float(attrs["clip_target_radial_offset_m"])
            )
            clip_hit_samples += int(clip_error <= PATH_HOLD_TOLERANCE_M)

        if request_seq % trace_interval == 0 or request_seq == step_count:
            trace.append({
                "time_s": float(observation["time_s"]),
                "phase": float(attrs["manoeuvre_phase"]),
                "x_m": float(observation["x_m"]),
                "y_m": float(observation["y_m"]),
                "progress_m": float(observation["track_progress_m"]),
                "path_phase_rad": float(
                    observation["gymkhana_path_phase_rad"]
                ),
                "path_lateral_error_m": float(
                    observation["gymkhana_path_lateral_error_m"]
                ),
                "speed_m_s": float(observation["speed_m_s"]),
                "target_speed_m_s": float(attrs["target_speed_m_s"]),
                "slip_angle_rad": float(observation["slip_angle_rad"]),
                "target_slip_rad": float(attrs["target_slip_rad"]),
                "yaw_rate_rad_s": float(observation["yaw_rate_rad_s"]),
                "target_yaw_rate_rad_s": float(
                    attrs["target_yaw_rate_rad_s"]
                ),
                "path_curvature_inv_m": float(
                    observation["gymkhana_path_curvature_now_inv_m"]
                ),
                "clip_commitment": float(attrs["clip_commitment"]),
                "command_steering": float(attrs["command_steering"]),
                "command_differential_yaw_request": float(
                    attrs["command_differential_yaw_request"]
                ),
            })

    ordered = sorted(graph_latencies_us)
    percentile_index = min(
        len(ordered) - 1, math.ceil(0.99 * len(ordered)) - 1
    )
    return {
        "protocol": "gymkhana_geometry_v1",
        "architecture": trajectory_architecture,
        "plant": world.backend,
        "duration_s": duration_s,
        "control_hz": world.config.control_hz,
        "physics_hz": world.config.physics_hz,
        "metrics": {
            "mean_absolute_path_error_m": (
                absolute_path_error_sum / step_count
            ),
            "maximum_absolute_path_error_m": maximum_path_error,
            "path_within_2m_fraction": path_hold_samples / step_count,
            "maximum_abs_slip_deg": math.degrees(maximum_abs_slip),
            "completed_laps": int(observation["laps"]),
            "completed_course_fraction": (
                float(observation["track_progress_m"])
                / float(observation["track_length_m"])
            ),
            "offtrack_time_s": float(observation["offtrack_time_s"]),
            "clip_hit_fraction": (
                clip_hit_samples / clip_samples if clip_samples else 0.0
            ),
            "graph_latency_p99_us": ordered[percentile_index],
        },
        "trace": trace,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-s", type=float, default=35.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trace-hz", type=float, default=10.0)
    parser.add_argument(
        "--trajectory-architecture",
        choices=("reactive_tangent", "preview_clip"),
        default="preview_clip",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_gymkhana(
        duration_s=args.duration_s,
        seed=args.seed,
        trace_hz=args.trace_hz,
        trajectory_architecture=args.trajectory_architecture,
    )
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
