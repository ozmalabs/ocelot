"""Audit humanoid locomotor forward-model and composition observables.

This is an offline result reader.  It does not choose actions, alter graph
state, or infer simulator policy.  The reported values are measurements of
graph-authored receipts already serialized by the experiment runner.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINES = (
    ROOT / "results" / "humanoid_locomotor_repertoire_v9.json",
    ROOT / "results" / "humanoid_locomotor_repertoire_v10.json",
)


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _phase_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("token"),
        row.get("support_phase"),
        row.get("context_id"),
    )


def _quarter_means(values: list[float]) -> list[float]:
    if not values:
        return [0.0] * 4
    return [
        _mean(values[index * len(values) // 4:(index + 1) * len(values) // 4])
        for index in range(4)
    ]


def _energy_observability(
    run: dict[str, Any],
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare receipt energy only within the graph's accounting window."""
    evaluation_total = sum(
        float(row.get("motor_input_energy_joules", 0.0))
        for row in trace
    )
    graph_energy = float(
        run["motor_input_energy_joules_graph_assessment"]
    )
    final_window = run.get(
        "motor_energetic_window_seq_graph_assessment"
    )
    trace_has_windows = bool(trace) and all(
        "energetic_window_seq" in row for row in trace
    )
    if final_window is not None and trace_has_windows:
        current_window = sum(
            float(row.get("motor_input_energy_joules", 0.0))
            for row in trace
            if float(row["energetic_window_seq"]) == float(final_window)
        )
        comparison_scope = "current_graph_energetic_window"
        comparable = True
    elif float((run.get("control_regime") or {}).get("ordinal", 0.0)) >= 2.0:
        # Older results did not serialize receipt window identity.  Rung two
        # opens a new graph accounting window, so comparing its aggregate to
        # the full evaluation trace would manufacture an inconsistency.
        current_window = None
        comparison_scope = "window_metadata_unavailable"
        comparable = False
    else:
        current_window = evaluation_total
        comparison_scope = "evaluation_total"
        comparable = True
    consistent = (
        math.isclose(
            float(current_window),
            graph_energy,
            rel_tol=1e-9,
            abs_tol=1e-9,
        )
        if comparable
        else None
    )
    return {
        "trace_motor_input_energy_joules": evaluation_total,
        "trace_motor_input_energy_joules_evaluation_total": evaluation_total,
        "trace_motor_input_energy_joules_current_graph_window": current_window,
        "graph_motor_input_energy_joules": graph_energy,
        "graph_energetic_window_seq": final_window,
        "energy_observable_comparison_scope": comparison_scope,
        "energy_observable_comparable": comparable,
        "energy_observable_consistent": consistent,
    }


def summarize(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    run = result["run"]
    trace = run["trace"]
    walking = [row for row in trace if row["decision_kind"] == "learned_walk"]
    programs = sorted(
        run["motor_programs"],
        key=lambda row: row.get("request_seq", row.get("ordinal", 0)),
    )

    before_rows = run["phase_models_before_walk"]
    after_rows = run["phase_models_after_walk"]
    before = {_phase_key(row): row for row in before_rows}
    after = {_phase_key(row): row for row in after_rows}
    shared_keys = before.keys() & after.keys()
    changed_phase_models = sum(before[key] != after[key] for key in shared_keys)
    phase_experience_delta = sum(
        after[key].get("experience_count", 0)
        - before[key].get("experience_count", 0)
        for key in shared_keys
    )

    authorities = [
        (row.get("primary_token"), row.get("primary_context_id"))
        for row in programs
    ]
    authority_counts = Counter(authorities)
    token_counts = Counter(token for token, _ in authorities)
    authority_turnovers = sum(
        left != right for left, right in zip(authorities, authorities[1:])
    )
    dominant_authority_fraction = (
        sum(count for _, count in authority_counts.most_common(2))
        / max(1, len(authorities))
    )

    # A selected expert has become operationally stale when the realized
    # horizontal consequence is under one tenth of the consequence it still
    # predicts. Count later selections after that graph-observable mismatch.
    stale_seen: set[tuple[Any, ...]] = set()
    ever_stale: set[tuple[Any, ...]] = set()
    stale_reselections = 0
    stale_by_authority: dict[tuple[Any, ...], int] = defaultdict(int)
    stale_streak: dict[tuple[Any, ...], int] = defaultdict(int)
    maximum_stale_streak = 0
    realized_prediction_ratios: list[float] = []
    for program, authority in zip(programs, authorities):
        predicted = abs(float(program.get("sum_dvx", 0)))
        observed = abs(float(program.get("observed_dvx", 0)))
        ratio = observed / max(predicted, 1e-12)
        realized_prediction_ratios.append(ratio)
        if authority in stale_seen:
            if predicted <= 1e-6 or ratio >= 0.5:
                stale_seen.remove(authority)
                stale_streak[authority] = 0
            else:
                stale_reselections += 1
                stale_by_authority[authority] += 1
                stale_streak[authority] += 1
                maximum_stale_streak = max(
                    maximum_stale_streak,
                    stale_streak[authority],
                )
        if predicted > 1e-9 and ratio < 0.1:
            stale_seen.add(authority)
            ever_stale.add(authority)

    errors = [float(row.get("gait_prediction_error", 0)) for row in walking]
    error_quarters = _quarter_means(errors)
    walk_widths = Counter(int(row["motor_bundle_width"]) for row in walking)
    compound_signatures = {
        tuple(sorted(row.get("motor_tokens", ())))
        for row in walking
        if row.get("motor_bundle_width", 0) > 1
    }
    eligible_width_one = [
        row for row in programs
        if row.get("allow_expansion") == 1 and row.get("member_count") == 1
    ]
    energy_observability = _energy_observability(run, trace)

    return {
        "path": str(path),
        "protocol_path": result.get("protocol_path"),
        "actions": len(trace),
        "walking_actions": len(walking),
        "phase_model_count": len(after_rows),
        "phase_models_snapshot_identical": before_rows == after_rows,
        "changed_phase_model_count": changed_phase_models,
        "phase_model_experience_delta": phase_experience_delta,
        "authority_unique_count": len(authority_counts),
        "authority_turnover_count": authority_turnovers,
        "dominant_two_authority_fraction": dominant_authority_fraction,
        "dominant_two_token_fraction": (
            sum(count for _, count in token_counts.most_common(2))
            / max(1, len(authorities))
        ),
        "stale_authority_count": len(ever_stale),
        "stale_authority_still_active_count": len(stale_seen),
        "stale_authority_reselection_count": stale_reselections,
        "maximum_stale_authority_reselections": max(
            stale_by_authority.values(), default=0
        ),
        "maximum_consecutive_stale_reselections": maximum_stale_streak,
        "mean_realized_to_predicted_dvx_ratio": _mean(
            realized_prediction_ratios
        ),
        "tail_realized_to_predicted_dvx_ratio": _mean(
            realized_prediction_ratios[-max(1, len(realized_prediction_ratios) // 4):]
        ),
        "gait_prediction_error_quarter_means": error_quarters,
        "gait_prediction_error_decay_ratio": (
            error_quarters[-1] / max(error_quarters[0], 1e-12)
        ),
        "latest_gait_prediction_error": run["latest_gait_prediction_error"],
        "walking_width_counts": dict(sorted(walk_widths.items())),
        "walking_compound_fraction": (
            sum(count for width, count in walk_widths.items() if width > 1)
            / max(1, len(walking))
        ),
        "walking_compound_signature_count": len(compound_signatures),
        "maximum_walking_bundle_width": max(walk_widths, default=0),
        "maximum_synthesized_motor_program_width": run[
            "maximum_synthesized_motor_program_width"
        ],
        "expansion_eligible_width_one_count": len(eligible_width_one),
        "expansion_eligible_width_one_fraction": (
            len(eligible_width_one) / max(1, len(programs))
        ),
        "native_composition_attached_count": sum(
            row.get("native_composition_attached") == 1 for row in programs
        ),
        "nonzero_predicted_program_cost_count": sum(
            abs(float(row.get("predicted_cost", 0))) > 1e-12
            for row in programs
        ),
        "single_open_residual_program_fraction": (
            sum(row.get("open_residual_count") == 1 for row in programs)
            / max(1, len(programs))
        ),
        "approved_synergy_count": run["approved_synergy_count"],
        "maximum_synergy_probe_bundle_width": run[
            "maximum_synergy_probe_bundle_width"
        ],
        "fresh_programs_per_walking_action": len(programs) / max(1, len(walking)),
        "memory_eligible_program_count": sum(
            row.get("memory_eligible") == 1 for row in programs
        ),
        "motor_memory_recall_count": run["motor_memory_recall_count"],
        "deployment_learning_events": run["deployment_learning_events"],
        "gait_surprise_confirmation_receipts": run[
            "gait_surprise_confirmation_receipts"
        ],
        "directed_progress": run["directed_progress"],
        "maximum_directed_progress": run[
            "maximum_directed_progress_graph_assessment"
        ],
        "path_length": run["locomotor_path_length_graph_assessment"],
        "path_efficiency": run["gait_path_efficiency"],
        "forward_reversal_fraction": run["forward_reversal_fraction"],
        "support_alternations": run["support_alternations"],
        "minimum_height": run["minimum_height"],
        "canonical_height_floor": run["height_floor"],
        "below_canonical_height_floor": (
            run["minimum_height"] < run["height_floor"]
        ),
        "peak_tilt": run["peak_tilt"],
        **energy_observability,
    }


def candidate_checks(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, bool]:
    first, *_, last = candidate["gait_prediction_error_quarter_means"]
    return {
        "same_action_budget": candidate["actions"] == baseline["actions"],
        "prediction_error_decays_with_exposure": last <= 0.8 * first,
        "prediction_error_beats_v10_tail": (
            last < baseline["gait_prediction_error_quarter_means"][-1]
        ),
        "phase_model_authority_is_updated": (
            candidate["changed_phase_model_count"] > 0
            and candidate["deployment_learning_events"] > 0
        ),
        "stale_authority_reselection_is_reduced": (
            candidate["stale_authority_reselection_count"]
            < baseline["stale_authority_reselection_count"]
        ),
        "stale_authority_turns_over_within_confirmation_horizon": (
            candidate["maximum_consecutive_stale_reselections"]
            <= candidate["gait_surprise_confirmation_receipts"]
        ),
        "walking_compound_is_expressed": (
            candidate["maximum_walking_bundle_width"] >= 2
            and candidate["walking_compound_fraction"] > 0
        ),
        "walking_compound_has_diversity": (
            candidate["walking_compound_signature_count"] >= 2
        ),
        "final_progress_improves": (
            candidate["directed_progress"] > baseline["directed_progress"]
        ),
        "best_progress_improves": (
            candidate["maximum_directed_progress"]
            > baseline["maximum_directed_progress"]
        ),
        "path_efficiency_does_not_regress": (
            candidate["path_efficiency"] >= baseline["path_efficiency"]
        ),
        "reversal_fraction_improves": (
            candidate["forward_reversal_fraction"]
            < baseline["forward_reversal_fraction"]
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="*", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--assert-candidate", action="store_true")
    args = parser.parse_args(argv)

    paths = tuple(args.results) or DEFAULT_BASELINES
    reports = [summarize(path.resolve()) for path in paths]
    output: dict[str, Any] = {"reports": reports}
    passed = True
    if args.candidate is not None:
        candidate = summarize(args.candidate.resolve())
        baseline = reports[-1]
        checks = candidate_checks(candidate, baseline)
        output["candidate"] = candidate
        output["candidate_checks_against_last_baseline"] = checks
        passed = all(checks.values())
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if passed or not args.assert_candidate else 1


if __name__ == "__main__":
    raise SystemExit(main())
