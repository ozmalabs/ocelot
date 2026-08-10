"""Measure behavioral improvement across fresh humanoid graph lifetimes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_humanoid_walk import _run_arm  # noqa: E402


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "humanoid_lifelong_improvement_v1.json"
)
DEFAULT_LIBRARY = (
    ROOT / "results" / "humanoid_lifelong_motor_library_v1.json"
)


def _row(lifetime: int, arm: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "lifetime": lifetime,
        "arm": arm,
        "directed_progress": result["directed_progress"],
        "lateral_offset": result["lateral_offset"],
        "first_fall_action": result["first_fall_action"],
        "support_alternations": result["support_alternations"],
        "aerial_samples": result["aerial_samples"],
        "compound_action_count": result["compound_action_count"],
        "motor_memory_recall_count": result["motor_memory_recall_count"],
        "warm_start_memory_recall_count": result.get(
            "warm_start_memory_recall_count",
            0.0,
        ),
        "motor_memory_structural_reuse_count": result[
            "motor_memory_structural_reuse_count"
        ],
        "maximum_motor_memory_experience_count": result[
            "maximum_motor_memory_experience_count"
        ],
        "warm_start_shape_recognized": result[
            "warm_start_shape_recognized"
        ],
        "warm_start_program_count": result["warm_start_program_count"],
        "loaded_program_count": result[
            "motor_library_loaded_program_count"
        ],
        "saved_program_count": result.get(
            "motor_library_saved_program_count",
            0,
        ),
        "final_compound_response_interval": result[
            "final_compound_response_interval"
        ],
        "final_decision_count": result.get("final_decision_count", 0.0),
        "final_last_compound_decision_count": result.get(
            "final_last_compound_decision_count",
            0.0,
        ),
    }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _assess(
    accumulating: list[dict[str, Any]],
    fresh: list[dict[str, Any]],
) -> dict[str, Any]:
    midpoint = len(accumulating) // 2
    early_mean = _mean([
        float(row["directed_progress"])
        for row in accumulating[:midpoint]
    ])
    late_mean = _mean([
        float(row["directed_progress"])
        for row in accumulating[midpoint:]
    ])
    fresh_signature_keys = (
        "directed_progress",
        "lateral_offset",
        "first_fall_action",
        "support_alternations",
        "aerial_samples",
        "compound_action_count",
    )
    fresh_deterministic = all(
        tuple(row[key] for key in fresh_signature_keys)
        == tuple(fresh[0][key] for key in fresh_signature_keys)
        for row in fresh[1:]
    )
    final_progress_improved = (
        float(accumulating[-1]["directed_progress"])
        > float(fresh[-1]["directed_progress"])
    )
    late_progress_improved = late_mean > early_mean
    no_new_fall = all(
        not (
            accumulated["first_fall_action"] is not None
            and control["first_fall_action"] is None
        )
        for accumulated, control in zip(accumulating, fresh, strict=True)
    )
    final_lateral_safe = (
        abs(float(accumulating[-1]["lateral_offset"]))
        <= abs(float(fresh[-1]["lateral_offset"]))
    )
    safety_ok = no_new_fall and final_lateral_safe
    confirmed = (
        fresh_deterministic
        and final_progress_improved
        and late_progress_improved
        and safety_ok
    )
    if not fresh_deterministic:
        verdict = "INVALID_NONDETERMINISTIC_CONTROL"
    elif not safety_ok:
        verdict = "FALSIFY"
    elif confirmed:
        verdict = "CONFIRM"
    else:
        verdict = "DEGRADE"
    return {
        "verdict": verdict,
        "fresh_control_deterministic": fresh_deterministic,
        "final_progress_improved": final_progress_improved,
        "late_progress_improved": late_progress_improved,
        "no_new_fall": no_new_fall,
        "final_lateral_safe": final_lateral_safe,
        "early_accumulating_mean_progress": early_mean,
        "late_accumulating_mean_progress": late_mean,
        "final_paired_progress_difference": (
            float(accumulating[-1]["directed_progress"])
            - float(fresh[-1]["directed_progress"])
        ),
        "final_paired_absolute_lateral_difference": (
            abs(float(accumulating[-1]["lateral_offset"]))
            - abs(float(fresh[-1]["lateral_offset"]))
        ),
    }


def run_experiment(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    library_path: Path = DEFAULT_LIBRARY,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    library_path = library_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    base_path = ROOT / protocol["base_protocol"]
    base_protocol = json.loads(base_path.read_text(encoding="utf-8"))
    base_protocol["locomotion"]["actions"] = int(
        protocol["locomotion_actions_per_lifetime"]
    )
    accumulating = []
    fresh = []
    motor_library: dict[str, Any] | None = None
    for lifetime in range(1, int(protocol["lifetimes"]) + 1):
        accumulated_result = _run_arm(
            base_protocol,
            "directed_walk",
            motor_library=motor_library,
            motor_library_out=library_path,
        )
        accumulating.append(_row(
            lifetime,
            "accumulating",
            accumulated_result,
        ))
        motor_library = json.loads(
            library_path.read_text(encoding="utf-8")
        )
        fresh_result = _run_arm(
            base_protocol,
            "directed_walk",
        )
        fresh.append(_row(lifetime, "fresh_control", fresh_result))
    return {
        "experiment": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "base_protocol_path": str(base_path.relative_to(ROOT)),
        "library_path": (
            str(library_path.relative_to(ROOT))
            if library_path.is_relative_to(ROOT)
            else str(library_path)
        ),
        "policy_owner": "rust_graph",
        "accumulating": accumulating,
        "fresh_control": fresh,
        "assessment": _assess(accumulating, fresh),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--library-out", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_experiment(
        args.protocol,
        library_path=args.library_out,
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
