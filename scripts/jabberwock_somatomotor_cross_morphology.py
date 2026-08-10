#!/usr/bin/env python3
"""Test output-null developmental transfer to a different morphology."""
from __future__ import annotations

import argparse
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
from scripts.jabberwock_somatomotor_wave_matrix import (  # noqa: E402
    mastery_receipts,
)


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "humanoid_developmental_symmetric_transfer_v1.json"
)


def transfer_comparison(
    cold_receipts: dict[str, int], warm_receipts: dict[str, int]
) -> dict[str, Any]:
    common = sorted(set(cold_receipts) & set(warm_receipts))
    rows = [{
        "capability": name,
        "cold_receipts_to_mastery": cold_receipts[name],
        "warm_receipts_to_mastery": warm_receipts[name],
        "receipts_saved": cold_receipts[name] - warm_receipts[name],
    } for name in common]
    return {
        "common_mastered_capabilities": rows,
        "common_mastered_count": len(common),
        "warm_only_mastered_capabilities": sorted(
            set(warm_receipts) - set(cold_receipts)
        ),
        "cold_only_mastered_capabilities": sorted(
            set(cold_receipts) - set(warm_receipts)
        ),
        "total_receipts_saved_on_common_capabilities": sum(
            row["receipts_saved"] for row in rows
        ),
    }


def _capability_signatures(library: dict[str, Any]) -> set[str]:
    return {
        json.dumps(
            row["attrs"]["signature"],
            sort_keys=True,
            separators=(",", ":"),
        )
        for row in library.get("developmental_capabilities", ())
    }


def warm_start_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(({
        "capability": str(stage["name"]),
        "shape_overlap": int(stage.get("warm_start_overlap", 0)),
        "status": str(stage["status"]),
        "attempt_count": int(stage["attempt_count"]),
        "last_receipt_seq": int(stage["last_receipt_seq"]),
    } for stage in result["stages"]
        if int(stage.get("warm_start_overlap", 0)) > 0
    ), key=lambda row: row["capability"])


def trajectory_comparison(
    cold: dict[str, Any], warm: dict[str, Any]
) -> dict[str, Any]:
    """Compare situated compound outcomes without collapsing their tradeoffs."""
    cold_trace = cold["run"]["trace"]
    warm_trace = warm["run"]["trace"]
    shared = min(len(cold_trace), len(warm_trace))
    program_differences = [
        index
        for index in range(shared)
        if (
            cold_trace[index]["motor_configuration_shape_after"],
            int(cold_trace[index]["motor_bundle_width"]),
        ) != (
            warm_trace[index]["motor_configuration_shape_after"],
            int(warm_trace[index]["motor_bundle_width"]),
        )
    ]
    physical_differences = [
        index
        for index in range(shared)
        if cold_trace[index]["position_after"] != warm_trace[index]["position_after"]
    ]
    return {
        "shared_action_count": shared,
        "compound_program_difference_count": len(program_differences),
        "first_compound_program_divergence_action": (
            program_differences[0] if program_differences else None
        ),
        "physical_trajectory_difference_count": len(physical_differences),
        "first_physical_divergence_action": (
            physical_differences[0] if physical_differences else None
        ),
        "cold_trace_length": len(cold_trace),
        "warm_trace_length": len(warm_trace),
    }


def run_transfer(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    source_library_path: Path,
    protocol_overrides: dict[str, Any] | None = None,
    arm_order: tuple[str, str] = ("cold", "warm"),
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    source_library_path = source_library_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol_overrides:
        for key, value in protocol_overrides.items():
            if isinstance(value, dict) and isinstance(protocol.get(key), dict):
                protocol[key].update(value)
            else:
                protocol[key] = value
    if set(arm_order) != {"cold", "warm"} or len(arm_order) != 2:
        raise ValueError("arm_order must contain cold and warm exactly once")
    source_library = json.loads(
        source_library_path.read_text(encoding="utf-8")
    )
    source_hash = hashlib.sha256(
        source_library_path.read_bytes()
    ).hexdigest()
    source_signatures = _capability_signatures(source_library)
    if len(source_signatures) != 1:
        raise ValueError("source capabilities must describe one source body")

    arms = {}
    for arm in arm_order:
        arms[arm] = run_protocol(
            protocol,
            protocol_path=protocol_path,
            motor_library_path=(
                source_library_path if arm == "warm" else None
            ),
            update_motor_library=False,
        )
    cold = arms["cold"]
    warm = arms["warm"]
    if hashlib.sha256(source_library_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("cross-morphology run mutated source library")
    cold_receipts = mastery_receipts(cold)
    warm_receipts = mastery_receipts(warm)
    target_signature = warm["run"]["curriculum"][
        "body_capability_signature"
    ]
    target_signature_json = json.dumps(
        target_signature, sort_keys=True, separators=(",", ":")
    )
    if target_signature_json in source_signatures:
        raise RuntimeError("target morphology unexpectedly matches source shape")
    source_signature = next(iter(source_signatures))
    source_relations = {
        tuple(row) for row in json.loads(source_signature)
    }
    target_relations = {tuple(row) for row in target_signature}
    return {
        "experiment": "somatomotor_cross_morphology_transfer_v2",
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "source_library": {
            "path": str(source_library_path),
            "sha256": source_hash,
            "capability_count": len(
                source_library.get("developmental_capabilities", ())
            ),
            "somatomotor_coupling_count": len(
                source_library.get("somatomotor_couplings", ())
            ),
            "output_authority": 0,
        },
        "design": {
            "same_engine_revision": True,
            "same_target_body_fixture_and_seed": True,
            "independent_target_world_per_arm": True,
            "arm_execution_order": list(arm_order),
            "only_manipulated_variable": (
                "source_output_null_shape_library_presence"
            ),
            "source_and_target_shape_differ": True,
            "source_library_immutable": True,
        },
        "target": {
            "asset": protocol["asset"],
            "actuator_channel_count": (
                int(warm["run"]["non_tonic_actuator_count"]) // 2
            ),
            "body_capability_signature": target_signature,
            "shape_overlap": {
                "source_relation_count": len(source_relations),
                "target_relation_count": len(target_relations),
                "shared_relation_count": len(
                    source_relations & target_relations
                ),
                "target_residual_relation_count": len(
                    target_relations - source_relations
                ),
            },
        },
        "cold": {
            **_arm_summary(cold),
            "mastery_receipts": cold_receipts,
            "cross_body_warm_start_count": cold[
                "cross_body_warm_start_count"
            ],
            "exact_body_recall_count": cold["exact_body_recall_count"],
        },
        "warm": {
            **_arm_summary(warm),
            "mastery_receipts": warm_receipts,
            "cross_body_warm_start_count": warm[
                "cross_body_warm_start_count"
            ],
            "exact_body_recall_count": warm["exact_body_recall_count"],
            "shape_warm_started_capabilities": warm_start_rows(warm),
        },
        "transfer": transfer_comparison(cold_receipts, warm_receipts),
        "trajectory_comparison": trajectory_comparison(cold, warm),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--source-library", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_transfer(
        args.protocol,
        source_library_path=args.source_library,
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
