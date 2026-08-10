"""Evaluate graph-native heading escape against the legacy distance controller.

The host instantiates declared mechanical worlds, runs matched controller
ablations, and aggregates graph-authored measurements. It does not choose an
action, infer morphology, or calculate either control policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domains.pybullet_robot_world import (
    MechanicalCondition,
    MechanicalRandomization,
)
from scripts.jabberwock_embodied_adaptation import run_episode


DEFAULT_PROTOCOL = ROOT / "protocols" / "embodied_nonholonomic_control_v1.json"
DEFAULT_RESULT = ROOT / "results" / "embodied_nonholonomic_control_v1.json"


def _condition(row: dict[str, Any], onset: int) -> MechanicalCondition:
    return MechanicalCondition(
        onset_action=onset,
        abrupt_retention=tuple(row["abrupt_retention"]),
        wear_per_use=tuple(row["wear_per_use"]),
        minimum_retention=float(row["minimum_retention"]),
    )


def _summarize(
    result: dict[str, Any],
    *,
    case_id: str,
    arm: str,
    onset: int,
) -> dict[str, Any]:
    post = result["trace"][onset:]
    start = float(post[0]["goal_distance_before"])
    final = float(result["final_goal_distance"])
    return {
        "case_id": case_id,
        "morphology": result["morphology"],
        "arm": arm,
        "seed": result["seed"],
        "postchange_start_distance": start,
        "final_distance": final,
        "minimum_postchange_distance": min(
            float(row["goal_distance_after"]) for row in post
        ),
        "normalized_progress_including_recalibration_cost": (
            (start - final) / start if start > 0.0 else 0.0
        ),
        "goal_reached_at_any_postchange_action": any(
            float(row["goal_reached"]) == 1.0 for row in post
        ),
        "postchange_model_updates": sum(
            float(row["model_experience_count_after"])
            > float(row["model_experience_count_before"])
            for row in post
        ),
        "heading_escape_actions": sum(
            row["decision_kind"] == "forward_model"
            and row["control_regime"] == "heading_escape"
            for row in post
        ),
        "two_step_distance_actions": sum(
            row["decision_kind"] == "forward_model"
            and row["control_regime"] == "two_step_distance"
            for row in post
        ),
        "recalibration_actions": sum(
            row["decision_kind"] == "change_recalibration" for row in post
        ),
        "trace_sha256": hashlib.sha256(
            json.dumps(result["trace"], sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def _prechange_match(
    enhanced: dict[str, Any],
    legacy: dict[str, Any],
    onset: int,
) -> bool:
    keys = (
        "selected_token",
        "trial_token",
        "decision_kind",
        "pre_base_position",
        "pre_base_orientation_xyzw",
        "post_base_position",
        "post_base_orientation_xyzw",
        "model_experience_count_after",
        "model_context_gain_forward_after",
        "model_context_gain_lateral_after",
        "model_context_gain_turn_after",
        "model_candidate_promotion_count_after",
        "model_candidate_validation_success_count_after",
    )
    return all(
        all(left[key] == right[key] for key in keys)
        for left, right in zip(
            enhanced["trace"][:onset],
            legacy["trace"][:onset],
            strict=True,
        )
    )


def _evaluate(
    protocol: dict[str, Any],
    rows: list[dict[str, Any]],
    pair_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    indexed = {
        (row["case_id"], row["morphology"], row["arm"]): row
        for row in rows
    }
    comparisons = []
    for case in protocol["cases"]:
        for morphology in protocol["morphologies"]:
            enhanced = indexed[
                (case["case_id"], morphology, "adaptive_heading_escape")
            ]
            legacy = indexed[
                (case["case_id"], morphology, "adaptive_legacy_control")
            ]
            advantage = (
                enhanced["normalized_progress_including_recalibration_cost"]
                - legacy["normalized_progress_including_recalibration_cost"]
            )
            comparisons.append({
                "case_id": case["case_id"],
                "morphology": morphology,
                "enhanced_progress": enhanced[
                    "normalized_progress_including_recalibration_cost"
                ],
                "legacy_progress": legacy[
                    "normalized_progress_including_recalibration_cost"
                ],
                "paired_advantage": advantage,
                "enhanced_wins": advantage > 0.0,
            })

    by_morphology = {}
    for morphology in protocol["morphologies"]:
        body = [
            row for row in comparisons if row["morphology"] == morphology
        ]
        by_morphology[morphology] = {
            "enhanced_median_progress": statistics.median(
                row["enhanced_progress"] for row in body
            ),
            "legacy_median_progress": statistics.median(
                row["legacy_progress"] for row in body
            ),
            "median_paired_advantage": statistics.median(
                row["paired_advantage"] for row in body
            ),
            "enhanced_wins": sum(row["enhanced_wins"] for row in body),
            "comparisons": len(body),
        }

    gates = protocol["success_gates"]
    racecar = by_morphology["racecar"]
    healthy_rows = [
        row for row in rows if row["arm"] == "healthy_heading_escape"
    ]
    gate_results = {
        "all_runs_complete": len(rows)
        == len(protocol["cases"]) * len(protocol["morphologies"]) * 3,
        "prechange_trajectories_exactly_matched": all(
            row["exact_match"] for row in pair_checks
        ),
        "both_damage_arms_adapt": all(
            row["postchange_model_updates"] > 0
            for row in rows
            if row["arm"] in {
                "adaptive_heading_escape",
                "adaptive_legacy_control",
            }
        ),
        "enhanced_heading_escape_exercised": sum(
            row["heading_escape_actions"]
            for row in rows
            if row["arm"] == "adaptive_heading_escape"
        ) > 0,
        "legacy_heading_escape_disabled": all(
            row["heading_escape_actions"] == 0
            for row in rows
            if row["arm"] == "adaptive_legacy_control"
        ),
        "racecar_wins_required": racecar["enhanced_wins"]
        >= int(gates["racecar_wins_required"]),
        "racecar_median_paired_advantage_minimum": (
            racecar["median_paired_advantage"]
            >= float(gates["racecar_median_paired_advantage_minimum"])
        ),
        "racecar_enhanced_median_progress_positive": (
            racecar["enhanced_median_progress"] > 0.0
        ),
        "other_morphology_median_regression_floor": all(
            row["median_paired_advantage"]
            >= float(gates["other_morphology_median_regression_floor"])
            for morphology, row in by_morphology.items()
            if morphology != "racecar"
        ),
        "healthy_median_progress_positive_every_morphology": all(
            statistics.median(
                row["normalized_progress_including_recalibration_cost"]
                for row in healthy_rows
                if row["morphology"] == morphology
            ) > 0.0
            for morphology in protocol["morphologies"]
        ),
    }
    return {
        "primary_claim_passed": all(gate_results.values()),
        "gate_results": gate_results,
        "by_morphology": by_morphology,
        "paired_comparisons": comparisons,
    }


def execute(protocol_path: Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes)
    onset = int(protocol["calibration_actions"])
    steps = int(protocol["total_actions"])
    started = time.perf_counter()
    rows = []
    pair_checks = []

    for case in protocol["cases"]:
        randomization = MechanicalRandomization(**case["dynamics"])
        condition = _condition(case["condition"], onset)
        for morphology in protocol["morphologies"]:
            pair = {}
            for arm, enabled in (
                ("adaptive_heading_escape", True),
                ("adaptive_legacy_control", False),
            ):
                result = run_episode(
                    morphology,
                    "adaptive_damage_navigation",
                    steps=steps,
                    goal=protocol["initial_goal"],
                    seed=int(case["seed"]),
                    babble_samples=int(protocol["babble_samples"]),
                    mechanical_condition=condition,
                    mechanical_randomization=randomization,
                    post_calibration_goal_offset=case["goal_offset"],
                    goal_change_epoch=onset,
                    heading_escape_enabled=enabled,
                )
                pair[arm] = result
                rows.append(
                    _summarize(
                        result,
                        case_id=case["case_id"],
                        arm=arm,
                        onset=onset,
                    )
                )
            pair_checks.append({
                "case_id": case["case_id"],
                "morphology": morphology,
                "exact_match": _prechange_match(
                    pair["adaptive_heading_escape"],
                    pair["adaptive_legacy_control"],
                    onset,
                ),
            })
            healthy = run_episode(
                morphology,
                "adaptive_damage_navigation",
                steps=steps,
                goal=protocol["initial_goal"],
                seed=int(case["seed"]),
                babble_samples=int(protocol["babble_samples"]),
                mechanical_randomization=randomization,
                post_calibration_goal_offset=case["goal_offset"],
                goal_change_epoch=onset,
                heading_escape_enabled=True,
            )
            rows.append(
                _summarize(
                    healthy,
                    case_id=case["case_id"],
                    arm="healthy_heading_escape",
                    onset=onset,
                )
            )

    payload = {
        "experiment": protocol["protocol_id"],
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "protocol_status_at_execution": protocol["status"],
        "runs": rows,
        "prechange_pair_checks": pair_checks,
        "evaluation": _evaluate(protocol, rows, pair_checks),
        "wall_time_seconds": time.perf_counter() - started,
    }
    if not all(
        math.isfinite(
            row["normalized_progress_including_recalibration_cost"]
        )
        for row in rows
    ):
        raise RuntimeError("non-finite primary metric")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args()
    payload = execute(args.protocol)
    args.json_out.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "result": str(args.json_out),
        "protocol_sha256": payload["protocol_sha256"],
        "primary_claim_passed": payload["evaluation"][
            "primary_claim_passed"
        ],
        "gate_results": payload["evaluation"]["gate_results"],
        "by_morphology": payload["evaluation"]["by_morphology"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
