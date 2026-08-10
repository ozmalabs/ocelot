#!/usr/bin/env python3
"""Ablate passive caregiver scaffolding on an unfamiliar articulated body."""
from __future__ import annotations

import argparse
from copy import deepcopy
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


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "humanoid_developmental_symmetric_transfer_v1.json"
)


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    run = result["run"]
    return {
        "completed": True,
        "mastery_count": result["mastery_count"],
        "demonstrated_capabilities": result["demonstrated_capabilities"],
        "caregiver_scaffold_event_count": len(
            run["caregiver_scaffold_trace"]
        ),
        "passive_effector_cycle_count": sum(
            row["kind"] == "passive_effector_cycle"
            for row in run["caregiver_scaffold_trace"]
        ),
        "passive_body_bounce_count": sum(
            row["kind"] == "passive_body_bounce"
            for row in run["caregiver_scaffold_trace"]
        ),
        "scaffolded_self_attempt_count": sum(
            row.get("collapse_kind") == "scaffolded_self_attempt"
            for row in run["calibration_trace"]
        ),
        "unscaffolded_self_attempt_count": sum(
            row.get("collapse_kind") == "unscaffolded_self_attempt"
            for row in run["calibration_trace"]
        ),
        "caregiver_protected_calibration_action_count": run[
            "caregiver_protected_calibration_action_count"
        ],
        "minimum_calibration_height": min(
            row["base_height"] for row in run["calibration_trace"]
        ),
        "maximum_calibration_peak_contact_force_newtons": max(
            row["peak_contact_force_newtons"]
            for row in run["calibration_trace"]
        ),
        "caregiver_support_impulse_newton_seconds": sum(
            row["caregiver_support_impulse_newton_seconds"]
            for row in run["calibration_trace"]
        ),
        "caregiver_scaffold_handoff_ready": run[
            "caregiver_scaffold_handoff_ready"
        ],
        "caregiver_scaffold_mismatch_count": run[
            "caregiver_scaffold_mismatch_count"
        ],
        "caregiver_scaffold_unresolved": run[
            "caregiver_scaffold_unresolved"
        ],
        "caregiver_passive_scaffold_withdrawn_before_active_attempt": run[
            "caregiver_passive_scaffold_withdrawn_before_active_attempt"
        ],
        "self_authored_action_count": (
            len(run["calibration_trace"])
            + len(run["synergy_calibration_trace"])
            + len(run["trace"])
        ),
        "passive_body_model_count": len(
            run["somatomotor_passive_body_models"]
        ),
        "passive_body_models_with_contingent_evidence": sum(
            int(row.get("contingent_count", 0)) > 0
            for row in run["somatomotor_passive_body_models"]
        ),
        "passive_models_actively_reverified": sum(
            int(row.get("active_reverification_count", 0)) > 0
            for row in run["somatomotor_passive_body_models"]
        ),
        "agency_disambiguation_receipt_count": sum(
            int(row.get("agency_disambiguated_count", 0))
            for row in run["somatomotor_passive_body_models"]
        ),
        "calibration_action_count": len(run["calibration_trace"]),
        "synergy_calibration_action_count": len(
            run["synergy_calibration_trace"]
        ),
        "locomotion_action_count": len(run["trace"]),
        "retained_experience_count": run["curriculum"][
            "retained_experience_count"
        ],
        "caregiver_buffered_experience_count": run["curriculum"][
            "caregiver_buffered_experience_count"
        ],
        "unbuffered_experience_count": run["curriculum"][
            "unbuffered_experience_count"
        ],
    }


def run_ablation(protocol_path: Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    canonical = json.loads(protocol_path.read_text(encoding="utf-8"))
    canonical["asset"] = "mjcf/walker2d.xml"
    canonical["protocol"] = "caregiver_scaffold_contingency_ablation_v2"
    arms = {}
    for name, enabled, mode in (
        ("caregiver_absent", False, "contingent"),
        ("caregiver_scrambled", True, "scrambled"),
        ("caregiver_contingent", True, "contingent"),
    ):
        protocol = deepcopy(canonical)
        protocol["curriculum"]["caregiver_scaffolding"] = enabled
        protocol["curriculum"]["caregiver_scaffolding_mode"] = mode
        try:
            arms[name] = _summary(run_protocol(
                protocol,
                protocol_path=protocol_path,
            ))
        except RuntimeError as exc:
            arms[name] = {
                "completed": False,
                "failure": str(exc),
            }
    return {
        "experiment": canonical["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "asset": canonical["asset"],
        "design": {
            "same_engine_revision": True,
            "same_body_fixture_seed_and_protocol": True,
            "independent_world_per_arm": True,
            "only_manipulated_variable": (
                "caregiver_scaffolding_presence_and_contingency"
            ),
            "passive_events_have_output_authority": 0,
            "passive_events_have_efference_copy": 0,
            "active_learning_requires_caregiver_handoff": False,
            "caregiver_protection_is_external_and_exafferent": True,
            "caregiver_protection_fades_from_graph_evidence": True,
        },
        "arms": arms,
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
