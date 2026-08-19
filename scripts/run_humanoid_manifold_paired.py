"""Paired legacy/manifold humanoid run with identical protocol and seed."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_humanoid_walk import _run_arm


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_walking_v1.json"


def _metrics(run: dict) -> dict:
    return {
        "directed_progress": run["directed_progress"],
        "first_fall_action": run["first_fall_action"],
        "minimum_height": run["minimum_height"],
        "lateral_offset": run["lateral_offset"],
        "support_alternations": run["support_alternations"],
        "compound_action_count": run["compound_action_count"],
        "maximum_program_width": run["maximum_synthesized_motor_program_width"],
        "future_manifold": run["future_manifold"],
    }


def run(protocol_path: Path, actions: int | None = None) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if actions is not None:
        if actions < 1:
            raise ValueError("actions must be positive")
        protocol["locomotion"]["actions"] = actions
    protocol["locomotion"]["modes"] = ["directed_walk"]

    baseline_protocol = deepcopy(protocol)
    baseline_protocol["locomotion"]["future_manifold_enabled"] = 0.0
    baseline_protocol["locomotion"][
        "future_manifold_temporal_anchors_enabled"
    ] = 0.0

    treatment_protocol = deepcopy(protocol)
    treatment_protocol["locomotion"]["future_manifold_enabled"] = 1.0
    treatment_protocol["locomotion"][
        "future_manifold_temporal_anchors_enabled"
    ] = 1.0

    started = time.perf_counter()
    baseline = _run_arm(baseline_protocol, "directed_walk")
    baseline_seconds = time.perf_counter() - started
    started = time.perf_counter()
    treatment = _run_arm(treatment_protocol, "directed_walk")
    treatment_seconds = time.perf_counter() - started

    baseline_metrics = _metrics(baseline)
    treatment_metrics = _metrics(treatment)
    return {
        "experiment": "humanoid_future_manifold_paired",
        "protocol_path": str(protocol_path.resolve().relative_to(ROOT)),
        "seed": protocol["seed"],
        "actions": protocol["locomotion"]["actions"],
        "calibration_identical": (
            baseline["calibration_trace"] == treatment["calibration_trace"]
            and baseline["pre_locomotion_state"]
            == treatment["pre_locomotion_state"]
        ),
        "baseline_runtime_seconds": baseline_seconds,
        "treatment_runtime_seconds": treatment_seconds,
        "baseline": baseline_metrics,
        "treatment": treatment_metrics,
        "delta": {
            key: treatment_metrics[key] - baseline_metrics[key]
            for key in (
                "directed_progress",
                "minimum_height",
                "lateral_offset",
                "support_alternations",
                "compound_action_count",
                "maximum_program_width",
            )
        },
        "treatment_gate_active": bool(
            treatment_metrics["future_manifold"]["enabled"] > 0.5
            and treatment_metrics["future_manifold"][
                "temporal_anchors_enabled"
            ] > 0.5
            and treatment_metrics["future_manifold"]["bounds_ready"] > 0.5
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--actions", type=int)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = run(args.protocol, args.actions)
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
