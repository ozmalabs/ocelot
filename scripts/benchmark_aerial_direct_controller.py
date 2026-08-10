"""Measure the graph-native three-rotor controller's compute latency."""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
import statistics
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_aerial_adaptation import (  # noqa: E402
    _one_node,
    _write_state,
)
from scripts.jabberwock_aerial_direct_recovery import (  # noqa: E402
    _recovery_episode,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _summary(samples_ns: list[int]) -> dict[str, float]:
    ordered = sorted(samples_ns)

    def percentile(fraction: float) -> float:
        index = round((len(ordered) - 1) * fraction)
        return ordered[index] / 1_000.0

    median_ns = statistics.median(ordered)
    return {
        "minimum_microseconds": ordered[0] / 1_000.0,
        "median_microseconds": median_ns / 1_000.0,
        "p95_microseconds": percentile(0.95),
        "p99_microseconds": percentile(0.99),
        "median_throughput_hz": 1_000_000_000.0 / median_ns,
    }


def run_benchmark(*, samples: int = 10_000, warmup: int = 300) -> dict[str, Any]:
    if samples < 1 or warmup < 0:
        raise ValueError("samples must be positive and warmup non-negative")
    agent = WorldAdapter(seeds=("aerial_adaptation",))
    policy = _one_node(agent, "AerialPolicy")
    episode = _recovery_episode(agent)
    for key, value in {
        "body_mass": 0.027,
        "body_arm_length": 0.0397,
        "motor_thrust_coefficient": 3.16e-10,
        "maximum_motor_rpm": 21_702.0,
        "gravity_acceleration": 9.81,
    }.items():
        agent.inner.set_attr(policy, key, value)
    for key, value in {
        "emergency_active": 1.0,
        "failed_motor_ordinal": 1.0,
        "emergency_target_x": 0.67,
        "emergency_target_y": 0.595,
        "emergency_target_z": 0.895,
    }.items():
        agent.inner.set_attr(episode, key, value)
    observation = {
        "base_position": (0.67, 0.595, 0.895),
        "base_orientation_xyzw": (0.0, 0.0, 0.0, 1.0),
        "base_linear_velocity": (0.0, 0.0, 0.0),
        "base_angular_velocity": (1.0, -5.0, -2.0),
        "goal_position": (0.75, 0.75, 1.0),
    }

    state_seq = 0

    def cycle(*, measure_whole_boundary: bool) -> int:
        nonlocal state_seq
        state_seq += 1
        started = time.perf_counter_ns() if measure_whole_boundary else 0
        _write_state(agent, episode, observation, state_seq=state_seq)
        agent.inner.set_attr(episode, "direct_motor_command_ready", 0.0)
        if not measure_whole_boundary:
            started = time.perf_counter_ns()
        agent.tick()
        if not measure_whole_boundary:
            return time.perf_counter_ns() - started
        attrs = dict(agent.s.node(episode)["attrs"])
        tuple(float(attrs[f"direct_rpm_{motor}"]) for motor in range(4))
        return time.perf_counter_ns() - started

    for _ in range(warmup):
        cycle(measure_whole_boundary=True)
    graph_cycles = []
    sensor_to_command = []
    for _ in range(samples):
        graph_cycles.append(cycle(measure_whole_boundary=False))
        sensor_to_command.append(cycle(measure_whole_boundary=True))

    return {
        "benchmark": "aerial_three_rotor_direct_controller",
        "policy_owner": "rust_graph",
        "samples": samples,
        "warmup": warmup,
        "host": platform.uname()._asdict(),
        "active_rust_graph_cycle": _summary(graph_cycles),
        "sensor_to_rpm_python_boundary": _summary(sensor_to_command),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=10_000)
    parser.add_argument("--warmup", type=int, default=300)
    args = parser.parse_args(argv)
    print(json.dumps(
        run_benchmark(samples=args.samples, warmup=args.warmup),
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
