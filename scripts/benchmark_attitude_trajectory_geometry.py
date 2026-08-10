#!/usr/bin/env python3
"""Matched benchmark for attitude/trajectory and gymkhana generalization."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_attitude_trajectory import (  # noqa: E402
    run_attitude_trajectory,
)
from scripts.jabberwock_gymkhana import run_gymkhana  # noqa: E402


def run_benchmark(*, gymkhana_duration_s: float = 55.0) -> dict:
    jet = run_attitude_trajectory()
    reactive = run_gymkhana(
        duration_s=gymkhana_duration_s,
        trajectory_architecture="reactive_tangent",
    )
    preview = run_gymkhana(
        duration_s=gymkhana_duration_s,
        trajectory_architecture="preview_clip",
    )
    reactive_metrics = reactive["metrics"]
    preview_metrics = preview["metrics"]
    return {
        "protocol": "attitude_trajectory_geometry_v1",
        "claim_boundary": (
            "deterministic research plants; not vehicle certification"
        ),
        "generalized_capability": {
            "separation": (
                "inertial trajectory, body attitude, and previewed geometry "
                "are independent graph terms"
            ),
            "jet": jet,
            "gymkhana": {
                "reactive_tangent": reactive,
                "preview_clip": preview,
                "matched_delta": {
                    "mean_path_error_reduction_m": (
                        reactive_metrics["mean_absolute_path_error_m"]
                        - preview_metrics["mean_absolute_path_error_m"]
                    ),
                    "offtrack_time_reduction_s": (
                        reactive_metrics["offtrack_time_s"]
                        - preview_metrics["offtrack_time_s"]
                    ),
                    "path_within_2m_fraction_gain": (
                        preview_metrics["path_within_2m_fraction"]
                        - reactive_metrics["path_within_2m_fraction"]
                    ),
                },
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gymkhana-duration-s", type=float, default=55.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/attitude_trajectory_geometry_v1.json"),
    )
    args = parser.parse_args()
    result = run_benchmark(gymkhana_duration_s=args.gymkhana_duration_s)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "jet": result["generalized_capability"]["jet"]["metrics"],
        "gymkhana_delta": result["generalized_capability"][
            "gymkhana"
        ]["matched_delta"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
