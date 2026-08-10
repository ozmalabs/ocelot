#!/usr/bin/env python3
"""Run the matched precision-driving manoeuvre protocol."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.jabberwock_precision_driving import run_precision_manoeuvre


MANOEUVRES = (
    "drift_left",
    "drift_right",
    "donut_left",
    "donut_right",
)
ARCHITECTURES = ("radial_only", "preview_clip")
DEFAULT_DURATION_S = 35.0
RECEIPT_FIELDS = (
    "completed",
    "final_phase",
    "angular_travel_rad",
    "maximum_abs_slip_rad",
    "hold_duration_s",
    "mean_abs_angle_error_rad",
    "mean_abs_yaw_rate_error_rad_s",
    "mean_abs_radial_error_m",
    "angle_hold_fraction",
    "path_hold_fraction",
    "combined_hold_fraction",
    "clip_commitment_duration_s",
    "mean_abs_clip_error_m",
    "clip_hit_fraction",
    "fuel_used_l",
    "tyre_condition_used",
    "final_speed_m_s",
    "learned_yaw_response",
    "learned_slip_response",
    "graph_tick_latency_us",
)


def _receipt(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "manoeuvre": result["manoeuvre"],
        "trajectory_architecture": result["trajectory_architecture"],
        **{field: result[field] for field in RECEIPT_FIELDS},
    }


def run_benchmark(*, duration_s: float = DEFAULT_DURATION_S) -> dict[str, Any]:
    receipts = {
        architecture: {
            manoeuvre: _receipt(run_precision_manoeuvre(
                manoeuvre=manoeuvre,
                duration_s=duration_s,
                trace_hz=2.0,
                trajectory_architecture=architecture,
            ))
            for manoeuvre in MANOEUVRES
        }
        for architecture in ARCHITECTURES
    }
    preview = receipts["preview_clip"]
    radial = receipts["radial_only"]
    return {
        "protocol": "precision_driving_v1",
        "duration_s": duration_s,
        "manoeuvres": list(MANOEUVRES),
        "architectures": list(ARCHITECTURES),
        "receipts": receipts,
        "preview_minus_radial_only": {
            manoeuvre: {
                "mean_abs_angle_error_rad": (
                    preview[manoeuvre]["mean_abs_angle_error_rad"]
                    - radial[manoeuvre]["mean_abs_angle_error_rad"]
                ),
                "mean_abs_radial_error_m": (
                    preview[manoeuvre]["mean_abs_radial_error_m"]
                    - radial[manoeuvre]["mean_abs_radial_error_m"]
                ),
                "path_hold_fraction": (
                    preview[manoeuvre]["path_hold_fraction"]
                    - radial[manoeuvre]["path_hold_fraction"]
                ),
                "clip_hit_fraction": (
                    preview[manoeuvre]["clip_hit_fraction"]
                    - radial[manoeuvre]["clip_hit_fraction"]
                ),
            }
            for manoeuvre in MANOEUVRES
        },
        "symmetry": {
            "drift_angle_error_delta_rad": abs(
                preview["drift_left"]["mean_abs_angle_error_rad"]
                - preview["drift_right"]["mean_abs_angle_error_rad"]
            ),
            "donut_angle_error_delta_rad": abs(
                preview["donut_left"]["mean_abs_angle_error_rad"]
                - preview["donut_right"]["mean_abs_angle_error_rad"]
            ),
            "drift_radial_error_delta_m": abs(
                preview["drift_left"]["mean_abs_radial_error_m"]
                - preview["drift_right"]["mean_abs_radial_error_m"]
            ),
            "donut_radial_error_delta_m": abs(
                preview["donut_left"]["mean_abs_radial_error_m"]
                - preview["donut_right"]["mean_abs_radial_error_m"]
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-s", type=float, default=DEFAULT_DURATION_S)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_benchmark(duration_s=args.duration_s)
    payload = json.dumps(result, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
