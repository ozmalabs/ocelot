#!/usr/bin/env python3
"""Counterbalanced somatomotor-wave family and retention assay."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_humanoid_developmental_curriculum import (  # noqa: E402
    run_protocol,
)
from scripts.jabberwock_somatomotor_wave_ablation import (  # noqa: E402
    _arm_summary,
)


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "somatomotor_wave_fixture_body_matrix_v1.json"
)
ARM_VALUES = {
    "wave_enabled": True,
    "wave_ablated": False,
}


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def condition_protocol(
    base: dict[str, Any], condition: dict[str, Any], arm: str
) -> dict[str, Any]:
    """Mechanically apply declared experimental boundary conditions."""
    if arm not in ARM_VALUES:
        raise ValueError(f"unknown ablation arm: {arm!r}")
    protocol = deepcopy(base)
    turns = condition["fixture_quarter_turns"]
    if (
        not isinstance(turns, list)
        or len(turns) != 3
        or any(isinstance(value, bool) or not isinstance(value, int) for value in turns)
    ):
        raise ValueError("fixture_quarter_turns must contain three integers")
    scale = condition["maximum_joint_force_scale"]
    numerator = _positive_integer(scale["numerator"], "force numerator")
    denominator = _positive_integer(scale["denominator"], "force denominator")
    protocol["body"]["initial_base_quarter_turns"] = list(turns)
    protocol["body"]["maximum_joint_force"] = (
        float(protocol["body"]["maximum_joint_force"])
        * numerator
        / denominator
    )
    protocol["curriculum"]["somatomotor_waves"] = ARM_VALUES[arm]
    return protocol


def mastery_receipts(result: dict[str, Any]) -> dict[str, int]:
    return {
        str(stage["name"]): int(stage["last_receipt_seq"])
        for stage in result["stages"]
        if stage["status"] == "mastered"
    }


def library_mastery_receipts(library_path: Path) -> dict[str, int]:
    library = json.loads(library_path.read_text(encoding="utf-8"))
    receipts: dict[str, int] = {}
    for row in library.get("developmental_capabilities", ()):
        attrs = row["attrs"]
        name = str(attrs["capability_name"])
        receipt_seq = attrs.get("mastery_receipt_seq")
        if (
            isinstance(receipt_seq, bool)
            or not isinstance(receipt_seq, (int, float))
            or int(receipt_seq) != receipt_seq
            or receipt_seq < 1
        ):
            raise ValueError(
                f"capability memory lacks causal mastery receipt: {name}"
            )
        receipts[name] = int(receipt_seq)
    return receipts


def rediscovery_summary(
    cold_receipts: dict[str, int], retained_receipts: dict[str, int]
) -> dict[str, Any]:
    capabilities = []
    for name, cold_count in sorted(cold_receipts.items()):
        retained_count = retained_receipts.get(name)
        capabilities.append({
            "capability": name,
            "cold_receipts_to_mastery": cold_count,
            "retained_receipts_to_remastery": retained_count,
            "receipts_saved": (
                cold_count - retained_count
                if retained_count is not None
                else None
            ),
            "retained_within_assay": int(retained_count is not None),
        })
    comparable = [
        row for row in capabilities if row["receipts_saved"] is not None
    ]
    return {
        "capabilities": capabilities,
        "cold_mastered_count": len(cold_receipts),
        "retained_remastered_count": len(retained_receipts),
        "comparable_capability_count": len(comparable),
        "total_receipts_saved": sum(
            int(row["receipts_saved"]) for row in comparable
        ),
        "all_cold_capabilities_retained_within_assay": (
            len(comparable) == len(cold_receipts)
        ),
    }


def _write_checkpoint(path: Path | None, result: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def run_matrix(
    matrix_path: Path = DEFAULT_PROTOCOL,
    *,
    library_path: Path,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    matrix_path = matrix_path.resolve()
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    base_path = ROOT / matrix["base_protocol"]
    base = json.loads(base_path.read_text(encoding="utf-8"))
    if library_path.exists():
        raise FileExistsError(
            f"refusing to contaminate a cold assay with existing library: {library_path}"
        )
    conditions = matrix["conditions"]
    if sum(bool(row.get("retention_source")) for row in conditions) != 1:
        raise ValueError("matrix must declare exactly one retention source")
    result: dict[str, Any] = {
        "experiment": matrix["protocol"],
        "matrix_protocol_path": str(matrix_path.relative_to(ROOT)),
        "base_protocol_path": str(base_path.relative_to(ROOT)),
        "matrix_sha256": _digest(matrix),
        "base_protocol_sha256": _digest(base),
        "design": {
            "same_engine_revision": True,
            "independent_world_per_arm": True,
            "counterbalanced_arm_order": True,
            "factorial_fixture_count": len({
                tuple(row["fixture_quarter_turns"]) for row in conditions
            }),
            "factorial_mechanical_body_count": len({
                (
                    row["maximum_joint_force_scale"]["numerator"],
                    row["maximum_joint_force_scale"]["denominator"],
                )
                for row in conditions
            }),
            "only_cognitive_manipulation": matrix[
                "only_cognitive_manipulation"
            ],
        },
        "conditions": [],
        "retention": {"status": "pending"},
    }
    retention_source: tuple[dict[str, Any], dict[str, int]] | None = None
    for condition in conditions:
        order = condition["arm_order"]
        if sorted(order) != sorted(ARM_VALUES):
            raise ValueError("each condition must execute both ablation arms")
        condition_row: dict[str, Any] = {
            "name": condition["name"],
            "fixture_quarter_turns": condition["fixture_quarter_turns"],
            "maximum_joint_force_scale": condition[
                "maximum_joint_force_scale"
            ],
            "arm_order": order,
            "arms": {},
        }
        result["conditions"].append(condition_row)
        for arm in order:
            protocol = condition_protocol(base, condition, arm)
            saves_retention = bool(
                condition.get("retention_source")
                and arm == "wave_enabled"
            )
            arm_result = run_protocol(
                protocol,
                protocol_path=base_path,
                motor_library_path=(library_path if saves_retention else None),
            )
            condition_row["arms"][arm] = {
                **_arm_summary(arm_result),
                "mastery_receipts": mastery_receipts(arm_result),
            }
            if saves_retention:
                retention_source = (
                    condition,
                    library_mastery_receipts(library_path),
                )
            _write_checkpoint(checkpoint_path, result)
        enabled = condition_row["arms"]["wave_enabled"]
        ablated = condition_row["arms"]["wave_ablated"]
        condition_row["paired_difference"] = {
            "mastery_count": (
                enabled["mastery_count"] - ablated["mastery_count"]
            ),
            "stage_transition_count": (
                enabled["stage_transition_count"]
                - ablated["stage_transition_count"]
            ),
            "support_alternations": (
                enabled["support_alternations"]
                - ablated["support_alternations"]
            ),
            "directed_progress": (
                enabled["directed_progress"]
                - ablated["directed_progress"]
            ),
        }
        _write_checkpoint(checkpoint_path, result)

    if retention_source is None:
        raise RuntimeError("retention source arm did not execute")
    source_condition, cold_receipts = retention_source
    retained_protocol = condition_protocol(
        base, source_condition, "wave_enabled"
    )
    retained_result = run_protocol(
        retained_protocol,
        protocol_path=base_path,
        motor_library_path=library_path,
        update_motor_library=False,
    )
    result["retention"] = {
        "status": "complete",
        "source_condition": source_condition["name"],
        "library_path": str(library_path),
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "exact_body_recall_count": retained_result[
            "exact_body_recall_count"
        ],
        "cross_body_warm_start_count": retained_result[
            "cross_body_warm_start_count"
        ],
        "retained_arm": _arm_summary(retained_result),
        "rediscovery": rediscovery_summary(
            cold_receipts,
            mastery_receipts(retained_result),
        ),
    }
    paired = [row["paired_difference"] for row in result["conditions"]]
    result["family_effect"] = {
        "condition_count": len(paired),
        "wave_mastery_advantage_condition_count": sum(
            row["mastery_count"] > 0 for row in paired
        ),
        "wave_mastery_disadvantage_condition_count": sum(
            row["mastery_count"] < 0 for row in paired
        ),
        "total_mastery_difference": sum(
            row["mastery_count"] for row in paired
        ),
        "total_support_alternation_difference": sum(
            row["support_alternations"] for row in paired
        ),
        "total_directed_progress_difference": sum(
            row["directed_progress"] for row in paired
        ),
    }
    _write_checkpoint(checkpoint_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--library-out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_matrix(
        args.protocol,
        library_path=args.library_out.resolve(),
        checkpoint_path=(args.json_out.resolve() if args.json_out else None),
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
