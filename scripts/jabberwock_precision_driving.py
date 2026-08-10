#!/usr/bin/env python3
"""Run graph-native precision driving against the deterministic skid pad.

Python performs simulator I/O, exact graph transduction, condition selection,
and receipt aggregation. It does not select phases, targets, trade-offs, or
actuator commands.
"""
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
from domains.precision_driving_world import (  # noqa: E402
    PRECISION_COURSES,
    PrecisionDrivingWorld,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


MANOEUVRE_ORDINALS = {
    name: float(index) for index, name in enumerate(PRECISION_COURSES)
}
ANGLE_HOLD_TOLERANCE_RAD = math.radians(5.0)
RADIAL_HOLD_TOLERANCE_M = 2.0
CLIP_COMMITMENT_MEASUREMENT_FLOOR = 0.75


def _sensed_attrs(observation: dict[str, Any]) -> dict[str, float]:
    """Mechanically rename plant and course telemetry for graph ingestion."""
    return {
        "state_time_s": float(observation["time_s"]),
        "state_speed_m_s": float(observation["speed_m_s"]),
        "state_body_vx_m_s": float(observation["body_vx_m_s"]),
        "state_body_vy_m_s": float(observation["body_vy_m_s"]),
        "state_yaw_rate_rad_s": float(observation["yaw_rate_rad_s"]),
        "state_slip_angle": float(observation["slip_angle_rad"]),
        "state_radial_error_m": float(
            observation["precision_radial_error_m"]
        ),
        "state_tangent_heading_error_rad": float(
            observation["precision_tangent_heading_error_rad"]
        ),
        "state_angular_travel_rad": float(
            observation["precision_angular_travel_rad"]
        ),
        "state_path_phase_rad": float(
            observation["precision_path_phase_rad"]
        ),
        "state_path_length_m": float(
            observation["precision_path_length_m"]
        ),
        "state_path_lateral_error_m": float(
            observation["precision_path_lateral_error_m"]
        ),
        "state_path_curvature_now_inv_m": float(
            observation["precision_path_curvature_now_inv_m"]
        ),
        "state_path_curvature_near_inv_m": float(
            observation["precision_path_curvature_near_inv_m"]
        ),
        "state_path_curvature_middle_inv_m": float(
            observation["precision_path_curvature_middle_inv_m"]
        ),
        "state_path_curvature_far_inv_m": float(
            observation["precision_path_curvature_far_inv_m"]
        ),
        "state_path_curvature_envelope_inv_m": float(
            observation["precision_path_curvature_envelope_inv_m"]
        ),
        "state_preview_near_bearing_rad": float(
            observation["precision_preview_near_bearing_rad"]
        ),
        "state_preview_middle_bearing_rad": float(
            observation["precision_preview_middle_bearing_rad"]
        ),
        "state_preview_far_bearing_rad": float(
            observation["precision_preview_far_bearing_rad"]
        ),
        "state_preview_far_heading_error_rad": float(
            observation["precision_preview_far_heading_error_rad"]
        ),
        "state_tyre_condition": float(
            observation["tyre_condition_mean"]
        ),
        "state_tyre_temperature_c": float(
            observation["tyre_temperature_mean_c"]
        ),
        "state_fuel_l": float(observation["fuel_l"]),
    }


def _graph_action(agent: WorldAdapter, episode: Any) -> dict[str, float | int]:
    attrs = agent.s.node(episode)["attrs"]
    if float(attrs.get("action_ready", 0.0)) != 1.0:
        raise RuntimeError("precision-driving graph did not publish an action")
    return {
        "steering": float(attrs["command_steering"]),
        "throttle": float(attrs["command_throttle"]),
        "brake": float(attrs["command_brake"]),
        "drive_front_left": float(attrs["command_drive_front_left"]),
        "drive_front_right": float(attrs["command_drive_front_right"]),
        "drive_rear_left": float(attrs["command_drive_rear_left"]),
        "drive_rear_right": float(attrs["command_drive_rear_right"]),
        "brake_front_left": float(attrs["command_brake_front_left"]),
        "brake_front_right": float(attrs["command_brake_front_right"]),
        "brake_rear_left": float(attrs["command_brake_rear_left"]),
        "brake_rear_right": float(attrs["command_brake_rear_right"]),
        "front_wing": float(attrs["command_front_wing"]),
        "rear_wing": float(attrs["command_rear_wing"]),
        "gear": int(round(float(attrs["command_gear"]))),
        "pit_request": int(round(float(attrs["command_pit"]))),
    }


def run_precision_manoeuvre(
    *,
    manoeuvre: str = "drift_left",
    duration_s: float = 35.0,
    seed: int = 0,
    trace_hz: float = 10.0,
    trajectory_architecture: str = "preview_clip",
) -> dict[str, Any]:
    if manoeuvre not in MANOEUVRE_ORDINALS:
        raise ValueError(
            f"unknown manoeuvre {manoeuvre!r}; "
            f"expected one of {sorted(MANOEUVRE_ORDINALS)}"
        )
    if duration_s <= 0.0:
        raise ValueError("duration_s must be positive")
    if trace_hz <= 0.0:
        raise ValueError("trace_hz must be positive")
    if trajectory_architecture not in {"radial_only", "preview_clip"}:
        raise ValueError(
            "trajectory_architecture must be 'radial_only' or 'preview_clip'"
        )

    world = PrecisionDrivingWorld(course=manoeuvre, seed=seed)
    observation = world.reset()
    agent = WorldAdapter(seeds=("precision_driving",))
    episode = agent.s.add_node("PrecisionDrivingEpisode", {
        "manoeuvre_ordinal": MANOEUVRE_ORDINALS[manoeuvre],
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

    control_hz = world.config.control_hz
    step_count = int(round(duration_s * control_hz))
    trace_interval = max(1, int(round(control_hz / trace_hz)))
    previous_slip = float(observation["slip_angle_rad"])
    previous_yaw_rate = float(observation["yaw_rate_rad_s"])
    previous_yaw_request = 0.0
    initial_fuel_l = float(observation["fuel_l"])
    initial_tyre_condition = float(observation["tyre_condition_mean"])
    trace: list[dict[str, Any]] = []
    graph_latencies_us: list[float] = []
    hold_samples = 0
    angle_hold_samples = 0
    path_hold_samples = 0
    combined_hold_samples = 0
    absolute_angle_error_sum = 0.0
    absolute_yaw_error_sum = 0.0
    absolute_radial_error_sum = 0.0
    maximum_abs_slip = 0.0
    clip_samples = 0
    clip_hit_samples = 0
    absolute_clip_error_sum = 0.0

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
        tick_start_ns = time.perf_counter_ns()
        agent.tick()
        graph_latencies_us.append(
            (time.perf_counter_ns() - tick_start_ns) / 1000.0
        )
        attrs = agent.s.node(episode)["attrs"]
        action = _graph_action(agent, episode)
        previous_slip = float(observation["slip_angle_rad"])
        previous_yaw_rate = float(observation["yaw_rate_rad_s"])
        previous_yaw_request = float(
            attrs["command_differential_yaw_request"]
        )
        observation = world.step(action)

        phase = int(round(float(attrs["manoeuvre_phase"])))
        slip = float(observation["slip_angle_rad"])
        target_slip = float(attrs["target_slip_rad"])
        yaw_rate = float(observation["yaw_rate_rad_s"])
        target_yaw_rate = float(attrs["target_yaw_rate_rad_s"])
        radial_error = float(observation["precision_radial_error_m"])
        maximum_abs_slip = max(maximum_abs_slip, abs(slip))
        if phase == 2:
            angle_error = abs(slip - target_slip)
            yaw_error = abs(yaw_rate - target_yaw_rate)
            hold_samples += 1
            absolute_angle_error_sum += angle_error
            absolute_yaw_error_sum += yaw_error
            absolute_radial_error_sum += abs(radial_error)
            angle_ok = angle_error <= ANGLE_HOLD_TOLERANCE_RAD
            path_ok = abs(radial_error) <= RADIAL_HOLD_TOLERANCE_M
            angle_hold_samples += int(angle_ok)
            path_hold_samples += int(path_ok)
            combined_hold_samples += int(angle_ok and path_ok)
            clip_commitment = float(attrs["clip_commitment"])
            if (
                clip_commitment
                >= CLIP_COMMITMENT_MEASUREMENT_FLOOR
            ):
                clip_error = abs(
                    radial_error
                    - float(attrs["clip_target_radial_offset_m"])
                )
                clip_samples += 1
                absolute_clip_error_sum += clip_error
                clip_hit_samples += int(
                    clip_error <= RADIAL_HOLD_TOLERANCE_M
                )

        if request_seq % trace_interval == 0 or request_seq == step_count:
            trace.append({
                "time_s": float(observation["time_s"]),
                "phase": phase,
                "phase_start_time_s": float(attrs["phase_start_time_s"]),
                "phase_start_angular_travel_rad": float(
                    attrs["phase_start_angular_travel_rad"]
                ),
                "speed_m_s": float(observation["speed_m_s"]),
                "target_speed_m_s": float(attrs["target_speed_m_s"]),
                "slip_angle_rad": slip,
                "target_slip_rad": target_slip,
                "yaw_rate_rad_s": yaw_rate,
                "target_yaw_rate_rad_s": target_yaw_rate,
                "radial_error_m": radial_error,
                "tangent_heading_error_rad": float(
                    observation["precision_tangent_heading_error_rad"]
                ),
                "angular_travel_rad": float(
                    observation["precision_angular_travel_rad"]
                ),
                "attitude_cost": float(attrs["attitude_cost"]),
                "yaw_cost": float(attrs["yaw_cost"]),
                "path_cost": float(attrs["path_cost"]),
                "path_tradeoff_weight": float(
                    attrs["path_tradeoff_weight"]
                ),
                "path_phase_rad": float(
                    observation["precision_path_phase_rad"]
                ),
                "preview_near_bearing_rad": float(
                    observation["precision_preview_near_bearing_rad"]
                ),
                "preview_middle_bearing_rad": float(
                    observation["precision_preview_middle_bearing_rad"]
                ),
                "preview_far_bearing_rad": float(
                    observation["precision_preview_far_bearing_rad"]
                ),
                "preview_path_command": float(
                    attrs["preview_path_command"]
                ),
                "selected_clip_ordinal": int(round(float(
                    attrs["selected_clip_ordinal"]
                ))),
                "clip_ahead_distance_m": float(
                    attrs["clip_ahead_distance_m"]
                ),
                "clip_commitment": float(attrs["clip_commitment"]),
                "clip_target_radial_offset_m": float(
                    attrs["clip_target_radial_offset_m"]
                ),
                "clip_path_command": float(attrs["clip_path_command"]),
                "energy_cost": float(attrs["energy_cost"]),
                "learned_yaw_response": float(
                    attrs["learned_yaw_response"]
                ),
                "learned_slip_response": float(
                    attrs["learned_slip_response"]
                ),
                "action": dict(action),
            })

    attrs = agent.s.node(episode)["attrs"]
    sorted_latency = sorted(graph_latencies_us)
    percentile_index = min(
        len(sorted_latency) - 1,
        int(0.99 * len(sorted_latency)),
    )
    divisor = max(hold_samples, 1)
    return {
        "protocol": "precision_driving_v1",
        "backend": world.backend,
        "manoeuvre": manoeuvre,
        "trajectory_architecture": trajectory_architecture,
        "seed": seed,
        "duration_s": duration_s,
        "control_hz": control_hz,
        "physics_hz": world.config.physics_hz,
        "completed": int(round(float(attrs["manoeuvre_phase"]))) == 4,
        "final_phase": int(round(float(attrs["manoeuvre_phase"]))),
        "phase_start_time_s": float(attrs["phase_start_time_s"]),
        "phase_start_angular_travel_rad": float(
            attrs["phase_start_angular_travel_rad"]
        ),
        "angular_travel_rad": float(
            observation["precision_angular_travel_rad"]
        ),
        "maximum_abs_slip_rad": maximum_abs_slip,
        "hold_duration_s": hold_samples / control_hz,
        "mean_abs_angle_error_rad": absolute_angle_error_sum / divisor,
        "mean_abs_yaw_rate_error_rad_s": (
            absolute_yaw_error_sum / divisor
        ),
        "mean_abs_radial_error_m": absolute_radial_error_sum / divisor,
        "angle_hold_fraction": angle_hold_samples / divisor,
        "path_hold_fraction": path_hold_samples / divisor,
        "combined_hold_fraction": combined_hold_samples / divisor,
        "clip_commitment_duration_s": clip_samples / control_hz,
        "mean_abs_clip_error_m": (
            absolute_clip_error_sum / max(clip_samples, 1)
        ),
        "clip_hit_fraction": clip_hit_samples / max(clip_samples, 1),
        "fuel_used_l": initial_fuel_l - float(observation["fuel_l"]),
        "tyre_condition_used": (
            initial_tyre_condition
            - float(observation["tyre_condition_mean"])
        ),
        "final_speed_m_s": float(observation["speed_m_s"]),
        "learned_yaw_response": float(attrs["learned_yaw_response"]),
        "learned_slip_response": float(attrs["learned_slip_response"]),
        "graph_tick_latency_us": {
            "median": sorted_latency[len(sorted_latency) // 2],
            "p99": sorted_latency[percentile_index],
            "maximum": max(sorted_latency),
        },
        "trace": trace,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manoeuvre",
        choices=sorted(MANOEUVRE_ORDINALS),
        default="drift_left",
    )
    parser.add_argument("--duration-s", type=float, default=35.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trace-hz", type=float, default=10.0)
    parser.add_argument(
        "--trajectory-architecture",
        choices=("radial_only", "preview_clip"),
        default="preview_clip",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_precision_manoeuvre(
        manoeuvre=args.manoeuvre,
        duration_s=args.duration_s,
        seed=args.seed,
        trace_hz=args.trace_hz,
        trajectory_architecture=args.trajectory_architecture,
    )
    payload = json.dumps(result, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
