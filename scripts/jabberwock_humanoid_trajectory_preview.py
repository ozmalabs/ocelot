#!/usr/bin/env python3
"""Matched humanoid test of support-geometry trajectory preview."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_humanoid_walk import _run_arm  # noqa: E402


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "humanoid_support_preview_v1.json"
)


def _summary(run: dict[str, Any]) -> dict[str, Any]:
    return {
        key: run[key]
        for key in (
            "trajectory_architecture",
            "target_directed_progress_m",
            "locomotion_residual_m_graph_assessment",
            "locomotion_drive_active_at_end",
            "active_gait_attractor",
            "active_gait_attractor_ordinal",
            "gait_attractors",
            "active_residual_regime_ordinal",
            "residual_regime_selection_count",
            "residual_control_regimes",
            "directed_progress",
            "gait_path_efficiency",
            "lateral_offset",
            "maximum_lateral_excursion",
            "minimum_height",
            "peak_tilt",
            "first_fall_action",
            "support_alternations",
            "aerial_samples_per_locomotor_cycle",
            "opaque_actuator_usage_counts",
            "motor_input_energy_joules_graph_assessment",
            "motor_cost_of_transport_graph_assessment",
            "mean_realized_motor_command_rate_hz",
        )
    }


def run_comparison(
    protocol_path: Path = DEFAULT_PROTOCOL,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    arm_paths = {
        "body_trajectory_only": (
            ROOT / "results" / "humanoid_support_preview_body_only_v1.json"
        ),
        "persistent_residual_support_preview": (
            ROOT / "results" / "humanoid_support_preview_enhanced_v1.json"
        ),
    }
    for architecture, output_path in arm_paths.items():
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--protocol",
                str(protocol_path),
                "--single-architecture",
                architecture,
                "--single-output",
                str(output_path),
            ],
            check=True,
        )
    baseline = json.loads(
        arm_paths["body_trajectory_only"].read_text(encoding="utf-8")
    )
    enhanced = json.loads(
        arm_paths["persistent_residual_support_preview"].read_text(
            encoding="utf-8"
        )
    )
    return {
        "protocol": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "policy_owner": "rust_graph",
        "matched_conditions": {
            "body_trajectory_only": baseline,
            "persistent_residual_support_preview": enhanced,
        },
        "paired_delta": {
            "directed_progress_m": (
                enhanced["directed_progress"]
                - baseline["directed_progress"]
            ),
            "gait_path_efficiency": (
                enhanced["gait_path_efficiency"]
                - baseline["gait_path_efficiency"]
            ),
            "absolute_lateral_offset_m": (
                abs(enhanced["lateral_offset"])
                - abs(baseline["lateral_offset"])
            ),
            "maximum_lateral_excursion_m": (
                enhanced["maximum_lateral_excursion"]
                - baseline["maximum_lateral_excursion"]
            ),
            "minimum_height_m": (
                enhanced["minimum_height"] - baseline["minimum_height"]
            ),
            "peak_tilt": enhanced["peak_tilt"] - baseline["peak_tilt"],
            "motor_input_energy_joules": (
                enhanced["motor_input_energy_joules_graph_assessment"]
                - baseline["motor_input_energy_joules_graph_assessment"]
            ),
        },
        "assessment": {
            "preview_helped_progress": (
                enhanced["directed_progress"] > baseline["directed_progress"]
            ),
            "preview_helped_path_efficiency": (
                enhanced["gait_path_efficiency"]
                > baseline["gait_path_efficiency"]
            ),
            "preview_reduced_absolute_lateral_offset": (
                abs(enhanced["lateral_offset"])
                < abs(baseline["lateral_offset"])
            ),
            "preview_avoided_new_fall": (
                enhanced["first_fall_action"] is None
                or baseline["first_fall_action"] is not None
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "humanoid_support_preview_v1.json",
    )
    parser.add_argument(
        "--single-architecture",
        choices=(
            "body_trajectory_only",
            "persistent_residual_support_preview",
        ),
    )
    parser.add_argument("--single-output", type=Path)
    args = parser.parse_args()
    if args.single_architecture is not None:
        if args.single_output is None:
            parser.error("--single-output is required for a single arm")
        protocol = json.loads(
            args.protocol.resolve().read_text(encoding="utf-8")
        )
        single_protocol = deepcopy(protocol)
        single_protocol["locomotion"][
            "support_geometry_preview_authority"
        ] = float(
            args.single_architecture
            == "persistent_residual_support_preview"
        )
        single_protocol["locomotion"][
            "persistent_task_residual_authority"
        ] = float(
            args.single_architecture
            == "persistent_residual_support_preview"
        )
        args.single_output.write_text(
            json.dumps(
                _summary(_run_arm(single_protocol, "directed_walk")),
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        return 0
    result = run_comparison(args.protocol)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "matched_conditions": result["matched_conditions"],
        "paired_delta": result["paired_delta"],
        "assessment": result["assessment"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
