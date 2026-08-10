#!/usr/bin/env python3
"""Run graph-native body-attitude/inertial-trajectory decomposition."""
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
from domains.vectoring_jet_world import VectoringJetWorld  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _sensed_attrs(observation: dict[str, Any]) -> dict[str, float]:
    return {
        "state_time_s": float(observation["time_s"]),
        "state_vx_m_s": float(observation["vx_m_s"]),
        "state_vy_m_s": float(observation["vy_m_s"]),
        "state_unwrapped_yaw_rad": float(observation["unwrapped_yaw_rad"]),
        "state_yaw_rate_rad_s": float(observation["yaw_rate_rad_s"]),
        "state_body_vx_m_s": float(observation["body_vx_m_s"]),
        "state_body_vy_m_s": float(observation["body_vy_m_s"]),
        "state_dynamic_pressure_pa": float(
            observation["dynamic_pressure_pa"]
        ),
    }


def run_attitude_trajectory(
    *, duration_s: float = 7.0, trace_hz: float = 20.0
) -> dict[str, Any]:
    world = VectoringJetWorld()
    observation = world.reset()
    agent = WorldAdapter(seeds=("attitude_trajectory",))
    episode = agent.s.add_node("AttitudeTrajectoryEpisode", {
        "request_seq": 0.0,
        "decision_seq": 0.0,
        "action_ready": 0.0,
        "manoeuvre_phase": 0.0,
        "target_unwrapped_yaw_rad": 0.0,
        "target_yaw_rate_rad_s": 0.0,
        "trajectory_error_vx_m_s": 0.0,
        "trajectory_error_vy_m_s": 0.0,
        "attitude_error_rad": 0.0,
        "command_throttle": 0.0,
        "command_lateral_vector": 0.0,
        "command_yaw_vector": 0.0,
        **_sensed_attrs(observation),
    })
    _edge(agent, agent.agent, "has_attitude_trajectory_episode", episode)

    control_hz = world.config.control_hz
    step_count = int(round(duration_s * control_hz))
    trace_interval = max(1, int(round(control_hz / trace_hz)))
    trace: list[dict[str, float]] = []
    graph_latency_us: list[float] = []
    maximum_velocity_heading_error = 0.0
    minimum_forward_velocity = float(observation["vx_m_s"])

    for request_seq in range(1, step_count + 1):
        stamp_attrs(agent, episode, {
            **_sensed_attrs(observation),
            "request_seq": float(request_seq),
            "action_ready": 0.0,
        })
        started_ns = time.perf_counter_ns()
        agent.tick()
        graph_latency_us.append((time.perf_counter_ns() - started_ns) / 1000.0)
        attrs = agent.s.node(episode)["attrs"]
        if float(attrs["action_ready"]) != 1.0:
            raise RuntimeError("attitude/trajectory graph did not act")
        observation = world.step({
            "throttle": float(attrs["command_throttle"]),
            "lateral_vector": float(attrs["command_lateral_vector"]),
            "yaw_vector": float(attrs["command_yaw_vector"]),
        })
        heading_error = abs(float(observation["velocity_heading_rad"]))
        maximum_velocity_heading_error = max(
            maximum_velocity_heading_error, heading_error
        )
        minimum_forward_velocity = min(
            minimum_forward_velocity, float(observation["vx_m_s"])
        )
        if request_seq % trace_interval == 0 or request_seq == step_count:
            trace.append({
                "time_s": float(observation["time_s"]),
                "phase": float(attrs["manoeuvre_phase"]),
                "x_m": float(observation["x_m"]),
                "y_m": float(observation["y_m"]),
                "vx_m_s": float(observation["vx_m_s"]),
                "vy_m_s": float(observation["vy_m_s"]),
                "velocity_heading_rad": float(
                    observation["velocity_heading_rad"]
                ),
                "unwrapped_yaw_rad": float(
                    observation["unwrapped_yaw_rad"]
                ),
                "target_unwrapped_yaw_rad": float(
                    attrs["target_unwrapped_yaw_rad"]
                ),
                "yaw_rate_rad_s": float(observation["yaw_rate_rad_s"]),
                "command_throttle": float(attrs["command_throttle"]),
                "command_lateral_vector": float(
                    attrs["command_lateral_vector"]
                ),
                "command_yaw_vector": float(attrs["command_yaw_vector"]),
            })

    ordered = sorted(graph_latency_us)
    percentile_index = min(
        len(ordered) - 1,
        math.ceil(0.99 * len(ordered)) - 1,
    )
    final_yaw_error = abs(
        2.0 * math.pi - float(observation["unwrapped_yaw_rad"])
    )
    return {
        "protocol": "attitude_trajectory_v1",
        "architecture": "graph_native_attitude_trajectory_decomposition",
        "plant": world.backend,
        "control_hz": control_hz,
        "physics_hz": world.config.physics_hz,
        "duration_s": duration_s,
        "metrics": {
            "completed_body_turns": (
                float(observation["unwrapped_yaw_rad"]) / (2.0 * math.pi)
            ),
            "final_yaw_error_deg": math.degrees(final_yaw_error),
            "minimum_forward_velocity_m_s": minimum_forward_velocity,
            "maximum_velocity_heading_error_deg": math.degrees(
                maximum_velocity_heading_error
            ),
            "final_speed_m_s": float(observation["speed_m_s"]),
            "forward_displacement_m": float(observation["x_m"]),
            "lateral_displacement_m": float(observation["y_m"]),
            "graph_latency_p99_us": ordered[percentile_index],
        },
        "trace": trace,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-s", type=float, default=7.0)
    parser.add_argument("--trace-hz", type=float, default=20.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_attitude_trajectory(
        duration_s=args.duration_s,
        trace_hz=args.trace_hz,
    )
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
