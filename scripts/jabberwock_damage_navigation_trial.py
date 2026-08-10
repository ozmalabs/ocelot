"""Execute the frozen randomized damage-navigation protocol.

The graph owns calibration, prediction, action choice, surprise, plasticity,
and goal assessment. This host script instantiates declared mechanical worlds,
runs matched arms, and mechanically aggregates preregistered measurements.
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


DEFAULT_PROTOCOL = ROOT / "protocols" / "embodied_damage_navigation_v1.json"
DEFAULT_RESULT = ROOT / "results" / "embodied_damage_navigation_v1.json"


def _condition(row: dict[str, Any], onset: int) -> MechanicalCondition:
    return MechanicalCondition(
        onset_action=onset,
        abrupt_retention=tuple(row["abrupt_retention"]),
        wear_per_use=tuple(row["wear_per_use"]),
        minimum_retention=float(row["minimum_retention"]),
    )


def _randomization(row: dict[str, Any]) -> MechanicalRandomization:
    return MechanicalRandomization(**row)


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
    normalized_progress = (start - final) / start if start > 0.0 else 0.0
    context_magnitudes = [
        max(
            abs(float(model[f"context_gain_{axis}"]))
            for axis in ("forward", "lateral", "turn")
        )
        for model in result["models"]
    ]
    promotion_rows = [
        row for row in post if float(row["candidate_promoted"]) == 1.0
    ]
    minimum_validation = float(
        result["candidate_min_validation_observations"]
    )
    promotion_margin = float(result["candidate_promotion_margin"])
    valid_promotion_rows = [
        row
        for row in promotion_rows
        if (
            float(row["model_candidate_validation_count_before"]) + 1.0
            >= minimum_validation
        )
        and (
            float(row["model_candidate_error_sum_before"])
            + float(row["candidate_squared_error"])
        )
        < (1.0 - promotion_margin)
        * (
            float(row["model_candidate_consolidated_error_sum_before"])
            + float(row["consolidated_squared_error"])
        )
    ]
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
        "normalized_progress_including_recalibration_cost": normalized_progress,
        "goal_reached_at_any_postchange_action": any(
            float(row["goal_reached"]) == 1.0 for row in post
        ),
        "postchange_model_updates": sum(
            float(row["model_experience_count_after"])
            > float(row["model_experience_count_before"])
            for row in post
        ),
        "recalibration_actions": sum(
            row["decision_kind"] == "change_recalibration" for row in post
        ),
        "recalibration_cycles_opened": sum(
            float(row["opened_recalibration"]) for row in post
        ),
        "postchange_surprises": sum(float(row["surprise"]) for row in post),
        "postchange_actions": len(post),
        "context_models_nonzero": sum(
            magnitude > 1.0e-8 for magnitude in context_magnitudes
        ),
        "max_abs_context_gain": max(context_magnitudes, default=0.0),
        "candidate_hypotheses_opened": sum(
            float(row["candidate_opened"]) for row in post
        ),
        "candidate_promotions": len(promotion_rows),
        "candidate_rollbacks": len(promotion_rows),
        "candidate_changes_validated": sum(
            float(row["candidate_change_validated"]) for row in post
        ),
        "candidate_promotion_receipts_valid": (
            len(valid_promotion_rows) == len(promotion_rows)
        ),
        "final_position": list(result["final_position"]),
        "enacted_goal": list(result["enacted_post_calibration_goal"]),
        "trace_sha256": hashlib.sha256(
            json.dumps(result["trace"], sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def _prechange_match(
    adaptive: dict[str, Any],
    frozen: dict[str, Any],
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
            adaptive["trace"][:onset],
            frozen["trace"][:onset],
            strict=True,
        )
    )


def _evaluate(
    protocol: dict[str, Any],
    rows: list[dict[str, Any]],
    pair_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    damaged = {
        (row["case_id"], row["morphology"], row["arm"]): row
        for row in rows
        if row["arm"] != "healthy_reference"
    }
    comparisons = []
    for case in protocol["cases"]:
        for morphology in protocol["morphologies"]:
            adaptive = damaged[
                (case["case_id"], morphology, "adaptive_damage_navigation")
            ]
            frozen = damaged[
                (case["case_id"], morphology, "frozen_damage_navigation")
            ]
            advantage = (
                adaptive["normalized_progress_including_recalibration_cost"]
                - frozen["normalized_progress_including_recalibration_cost"]
            )
            comparisons.append({
                "case_id": case["case_id"],
                "morphology": morphology,
                "adaptive_progress": adaptive[
                    "normalized_progress_including_recalibration_cost"
                ],
                "frozen_progress": frozen[
                    "normalized_progress_including_recalibration_cost"
                ],
                "paired_advantage": advantage,
                "adaptive_wins": advantage > 0.0,
            })

    gates = protocol["success_gates"]
    advantages = [row["paired_advantage"] for row in comparisons]
    adaptive_wins = sum(row["adaptive_wins"] for row in comparisons)
    by_morphology = {}
    positive_all = True
    for morphology in protocol["morphologies"]:
        body_rows = [
            row for row in comparisons if row["morphology"] == morphology
        ]
        median_progress = statistics.median(
            row["adaptive_progress"] for row in body_rows
        )
        positive_all = positive_all and median_progress > 0.0
        by_morphology[morphology] = {
            "adaptive_median_progress": median_progress,
            "frozen_median_progress": statistics.median(
                row["frozen_progress"] for row in body_rows
            ),
            "median_paired_advantage": statistics.median(
                row["paired_advantage"] for row in body_rows
            ),
            "adaptive_wins": sum(row["adaptive_wins"] for row in body_rows),
            "comparisons": len(body_rows),
        }

    gate_results = {
        "all_runs_complete": len(rows)
        == len(protocol["cases"]) * len(protocol["morphologies"]) * 3,
        "prechange_trajectories_exactly_matched": all(
            row["exact_match"] for row in pair_checks
        ),
        "adaptive_postchange_models_update": all(
            row["postchange_model_updates"] > 0
            for row in rows
            if row["arm"] == "adaptive_damage_navigation"
        ),
        "frozen_postchange_models_do_not_update": all(
            row["postchange_model_updates"] == 0
            for row in rows
            if row["arm"] == "frozen_damage_navigation"
        ),
        "adaptive_wins_required_of_18": adaptive_wins
        >= int(gates["adaptive_wins_required_of_18"]),
        "pooled_median_paired_advantage_minimum": statistics.median(advantages)
        >= float(gates["pooled_median_paired_advantage_minimum"]),
        "adaptive_median_progress_positive_in_every_morphology": positive_all,
    }
    if "context_models_nonvacuous" in gates:
        gate_results["context_models_nonvacuous"] = all(
            row["context_models_nonzero"] > 0
            for row in rows
            if row["arm"] in {
                "adaptive_damage_navigation",
                "frozen_damage_navigation",
            }
        )
    if "median_paired_advantage_positive_in_every_morphology" in gates:
        gate_results[
            "median_paired_advantage_positive_in_every_morphology"
        ] = all(
            row["median_paired_advantage"] > 0.0
            for row in by_morphology.values()
        )
    if "candidate_promotion_receipts_valid" in gates:
        gate_results["candidate_promotion_receipts_valid"] = all(
            row["candidate_promotion_receipts_valid"]
            for row in rows
            if row["arm"] == "adaptive_damage_navigation"
        )
    if "candidate_hypotheses_exercised" in gates:
        adaptive_rows = [
            row
            for row in rows
            if row["arm"] == "adaptive_damage_navigation"
        ]
        gate_results["candidate_hypotheses_exercised"] = (
            sum(row["candidate_hypotheses_opened"] for row in adaptive_rows)
            > 0.0
            and (
                sum(row["candidate_rollbacks"] for row in adaptive_rows)
                + sum(
                    row["candidate_changes_validated"]
                    for row in adaptive_rows
                )
            )
            > 0
        )
    return {
        "primary_claim_passed": all(gate_results.values()),
        "gate_results": gate_results,
        "bounded_recalibration_audit": {
            "adaptive_at_most_one_cycle": all(
                row["recalibration_cycles_opened"] <= 1.0
                for row in rows
                if row["arm"] == "adaptive_damage_navigation"
            ),
            "adaptive_at_most_nine_probe_actions": all(
                row["recalibration_actions"] <= 9
                for row in rows
                if row["arm"] == "adaptive_damage_navigation"
            ),
            "frozen_opens_no_cycles": all(
                row["recalibration_cycles_opened"] == 0.0
                for row in rows
                if row["arm"] == "frozen_damage_navigation"
            ),
        },
        "candidate_model_audit": {
            "hypotheses_opened": sum(
                row["candidate_hypotheses_opened"]
                for row in rows
                if row["arm"] == "adaptive_damage_navigation"
            ),
            "promotions": sum(
                row["candidate_promotions"]
                for row in rows
                if row["arm"] == "adaptive_damage_navigation"
            ),
            "rollbacks": sum(
                row["candidate_rollbacks"]
                for row in rows
                if row["arm"] == "adaptive_damage_navigation"
            ),
            "changed_models_validated": sum(
                row["candidate_changes_validated"]
                for row in rows
                if row["arm"] == "adaptive_damage_navigation"
            ),
            "all_promotion_receipts_valid": all(
                row["candidate_promotion_receipts_valid"]
                for row in rows
                if row["arm"] == "adaptive_damage_navigation"
            ),
        },
        "adaptive_wins": adaptive_wins,
        "comparisons": len(comparisons),
        "pooled_median_paired_advantage": statistics.median(advantages),
        "by_morphology": by_morphology,
        "paired_comparisons": comparisons,
    }


def execute(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    include_traces: bool = False,
) -> dict[str, Any]:
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes)
    started = time.perf_counter()
    onset = int(protocol["calibration_actions"])
    steps = int(protocol["total_actions"])
    rows = []
    pair_checks = []
    full_runs = [] if include_traces else None

    for case in protocol["cases"]:
        randomization = _randomization(case["dynamics"])
        condition = _condition(case["condition"], onset)
        for morphology in protocol["morphologies"]:
            pair = {}
            for mode in (
                "adaptive_damage_navigation",
                "frozen_damage_navigation",
            ):
                result = run_episode(
                    morphology,
                    mode,
                    steps=steps,
                    goal=protocol["initial_goal"],
                    seed=int(case["seed"]),
                    babble_samples=int(protocol["babble_samples"]),
                    mechanical_condition=condition,
                    mechanical_randomization=randomization,
                    post_calibration_goal_offset=case["goal_offset"],
                    goal_change_epoch=onset,
                )
                pair[mode] = result
                rows.append(
                    _summarize(
                        result,
                        case_id=case["case_id"],
                        arm=mode,
                        onset=onset,
                    )
                )
                if full_runs is not None:
                    full_runs.append(result)

            pair_checks.append({
                "case_id": case["case_id"],
                "morphology": morphology,
                "exact_match": _prechange_match(
                    pair["adaptive_damage_navigation"],
                    pair["frozen_damage_navigation"],
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
            )
            rows.append(
                _summarize(
                    healthy,
                    case_id=case["case_id"],
                    arm="healthy_reference",
                    onset=onset,
                )
            )
            if full_runs is not None:
                full_runs.append(healthy)

    payload = {
        "experiment": protocol["protocol_id"],
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "protocol_status_at_execution": protocol["status"],
        "runs": rows,
        "prechange_pair_checks": pair_checks,
        "evaluation": _evaluate(protocol, rows, pair_checks),
        "wall_time_seconds": time.perf_counter() - started,
    }
    if full_runs is not None:
        payload["full_runs"] = full_runs
    if not all(math.isfinite(value) for value in (
        row["normalized_progress_including_recalibration_cost"] for row in rows
    )):
        raise RuntimeError("non-finite primary metric")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--include-traces", action="store_true")
    args = parser.parse_args()
    payload = execute(args.protocol, include_traces=args.include_traces)
    args.json_out.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    evaluation = payload["evaluation"]
    print(json.dumps({
        "result": str(args.json_out),
        "protocol_sha256": payload["protocol_sha256"],
        "primary_claim_passed": evaluation["primary_claim_passed"],
        "adaptive_wins": evaluation["adaptive_wins"],
        "comparisons": evaluation["comparisons"],
        "pooled_median_paired_advantage": (
            evaluation["pooled_median_paired_advantage"]
        ),
        "gate_results": evaluation["gate_results"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
