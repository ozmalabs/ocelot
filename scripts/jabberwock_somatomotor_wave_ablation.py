#!/usr/bin/env python3
"""Run a controlled same-process somatomotor-wave paired ablation."""
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


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_developmental_smoke_v1.json"


def _canonical_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    canonical = deepcopy(protocol)
    canonical.setdefault("curriculum", {}).pop("somatomotor_waves", None)
    return canonical


def _digest(protocol: dict[str, Any]) -> str:
    encoded = json.dumps(
        protocol, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _arm_summary(result: dict[str, Any]) -> dict[str, Any]:
    waves = result.get("somatomotor_waves", {})
    return {
        "mastery_count": result["mastery_count"],
        "stage_transition_count": result["stage_transition_count"],
        "active_capability": result["active_capability"],
        "demonstrated_capabilities": result["demonstrated_capabilities"],
        "support_alternations": result["support_alternations"],
        "directed_progress": result["directed_progress"],
        "get_up_attempt_count": result["get_up_attempt_count"],
        "recovery_basin_transition_count": result[
            "recovery_basin_transition_count"
        ],
        "wave_program_count": waves.get("program_count", 0),
        "compound_wave_program_count": waves.get(
            "compound_program_count", 0
        ),
        "verified_wave_reafference_count": waves.get(
            "verified_reafference_count", 0
        ),
        "strengthened_coupling_count": waves.get(
            "strengthened_coupling_count", 0
        ),
        "fractionated_coupling_count": waves.get(
            "fractionated_coupling_count", 0
        ),
        "maximum_coupling_strength": waves.get(
            "maximum_coupling_strength", 0
        ),
        "productive_coupling_receipt_count": waves.get(
            "productive_coupling_receipt_count", 0
        ),
        "unproductive_coupling_receipt_count": waves.get(
            "unproductive_coupling_receipt_count", 0
        ),
        "warm_coupling_hint_count": waves.get(
            "warm_coupling_hint_count", 0
        ),
        "warm_coupling_reverification_count": waves.get(
            "warm_coupling_reverification_count", 0
        ),
        "warm_prior_pending_count": waves.get(
            "warm_prior_pending_count", 0
        ),
        "warm_prior_reverified_count": waves.get(
            "warm_prior_reverified_count", 0
        ),
        "loaded_somatomotor_coupling_count": result.get("run", {}).get(
            "motor_library_loaded_somatomotor_coupling_count", 0
        ),
        "passive_effector_scaffold_receipt_count": waves.get(
            "passive_scaffold_receipt_count", 0
        ),
        "passive_vestibular_scaffold_receipt_count": waves.get(
            "vestibular_scaffold_receipt_count", 0
        ),
        "caregiver_scaffold_handoff_ready": result.get("run", {}).get(
            "caregiver_scaffold_handoff_ready", 0
        ),
        "scaffolded_self_attempt_count": sum(
            row.get("collapse_kind") == "scaffolded_self_attempt"
            for row in result.get("run", {}).get("calibration_trace", ())
        ),
    }


def run_ablation(protocol_path: Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    source = json.loads(protocol_path.read_text(encoding="utf-8"))
    canonical = _canonical_protocol(source)
    wave_protocol = deepcopy(canonical)
    wave_protocol["curriculum"]["somatomotor_waves"] = True
    ablated_protocol = deepcopy(canonical)
    ablated_protocol["curriculum"]["somatomotor_waves"] = False

    wave_result = run_protocol(wave_protocol, protocol_path=protocol_path)
    ablated_result = run_protocol(
        ablated_protocol, protocol_path=protocol_path
    )
    wave = _arm_summary(wave_result)
    ablated = _arm_summary(ablated_result)
    return {
        "experiment": "somatomotor_wave_same_revision_paired_ablation_v1",
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "canonical_protocol_sha256": _digest(canonical),
        "design": {
            "same_process": True,
            "same_engine_revision": True,
            "same_body_and_fixture": True,
            "same_protocol_and_seed": True,
            "only_manipulated_variable": "curriculum.somatomotor_waves",
            "arm_execution_order": ["wave_enabled", "wave_ablated"],
        },
        "arms": {
            "wave_enabled": wave,
            "wave_ablated": ablated,
        },
        "paired_difference": {
            "mastery_count": (
                wave["mastery_count"] - ablated["mastery_count"]
            ),
            "stage_transition_count": (
                wave["stage_transition_count"]
                - ablated["stage_transition_count"]
            ),
            "support_alternations": (
                wave["support_alternations"]
                - ablated["support_alternations"]
            ),
            "directed_progress": (
                wave["directed_progress"] - ablated["directed_progress"]
            ),
            "get_up_attempt_count": (
                wave["get_up_attempt_count"]
                - ablated["get_up_attempt_count"]
            ),
        },
        "full_arms": {
            "wave_enabled": wave_result,
            "wave_ablated": ablated_result,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_ablation(args.protocol)
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
