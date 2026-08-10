"""Paired reporting benchmark for standard and differential race control.

This file selects experimental conditions and aggregates receipts. All wheel,
path, stability, resource, and actuator decisions remain in the graph.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.jabberwock_full_racing import run_race


DEFAULT_DURATION_S = 120.0
DEFAULT_SEED_COUNT = 5
DEFAULT_OPPONENT_COUNT = 3
ARCHITECTURES = ("standard", "differential")
METRICS = (
    "total_progress_m",
    "mean_speed_m_s",
    "offtrack_time_s",
    "collisions",
    "fuel_used_l",
    "final_tyre_condition",
    "plant_damage",
    "pit_stops",
)


def _receipt(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": result["seed"],
        "control_architecture": result["control_architecture"],
        **{metric: result[metric] for metric in METRICS},
        "graph_tick_latency_us": result["graph_tick_latency_us"],
    }


def run_benchmark(
    *,
    duration_s: float = DEFAULT_DURATION_S,
    seed_count: int = DEFAULT_SEED_COUNT,
    opponent_count: int = DEFAULT_OPPONENT_COUNT,
) -> dict[str, Any]:
    if seed_count <= 0:
        raise ValueError("seed_count must be positive")
    receipts: dict[str, list[dict[str, Any]]] = {
        architecture: [] for architecture in ARCHITECTURES
    }
    for seed in range(seed_count):
        for architecture in ARCHITECTURES:
            result = run_race(
                duration_s=duration_s,
                seed=seed,
                opponent_count=opponent_count,
                trace_hz=0.2,
                control_architecture=architecture,
            )
            receipts[architecture].append(_receipt(result))

    aggregates = {
        architecture: {
            metric: mean(
                float(receipt[metric]) for receipt in architecture_receipts
            )
            for metric in METRICS
        }
        for architecture, architecture_receipts in receipts.items()
    }
    paired_deltas = {
        metric: mean(
            float(differential[metric]) - float(standard[metric])
            for standard, differential in zip(
                receipts["standard"],
                receipts["differential"],
                strict=True,
            )
        )
        for metric in METRICS
    }
    return {
        "protocol": "racing_differential_control_v1",
        "duration_s": duration_s,
        "seed_count": seed_count,
        "opponent_count": opponent_count,
        "architectures": list(ARCHITECTURES),
        "receipts": receipts,
        "mean": aggregates,
        "mean_differential_minus_standard": paired_deltas,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-s", type=float, default=DEFAULT_DURATION_S)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument(
        "--opponents",
        type=int,
        default=DEFAULT_OPPONENT_COUNT,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_benchmark(
        duration_s=args.duration_s,
        seed_count=args.seed_count,
        opponent_count=args.opponents,
    )
    payload = json.dumps(result, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
