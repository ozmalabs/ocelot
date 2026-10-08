#!/usr/bin/env python3
"""Independent checks and paired summaries for candidate-snapshot efficacy v1."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
import genmint_candidate_snapshot_efficacy_v1_1 as runner
import genmint_matrix_family_reuse_probe_v3 as fixtures

RAW = ROOT / "evaluation/reports/genmint_candidate_snapshot_efficacy_v1_1_20261001.json"
ANALYSIS = ROOT / "evaluation/reports/genmint_candidate_snapshot_efficacy_v1_1_analysis_20261001.json"
SEMANTIC_FIELDS = (
    "status", "residual", "transforms", "selected_generator", "selected_matrix",
    "route", "independent_predictions", "exact_target_match",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive_inputs(matrix_name: str, layout_name: str, task_index: int):
    matrix = fixtures.MAPS[matrix_name]
    coords = fixtures.HELDOUT[task_index]
    base, target = [], []
    for j, (r, c) in enumerate(coords):
        b, y = fixtures.make_row("p0" if j % 2 == 0 else "p1", r, c, matrix)
        base.append(b)
        target.append(y)
    return base, target


def negative_inputs(task_index: int):
    coords = runner.NEGATIVE_POINTS[task_index]
    base = [[f"neg{task_index}_{j}", r, c, "red"] for j, (r, c) in enumerate(coords)]
    target = [[row[0], row[1] * row[1] + row[2], row[1] - row[2] * row[2], row[3]] for row in base]
    return base, target


def semantic(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
    return [{key: row.get(key) for key in fields} for row in rows]


def main() -> int:
    raw = json.loads(RAW.read_text())
    expected_lock = json.loads(json.dumps(runner.lock_payload()))
    workers = raw.get("workers", [])
    expected_cells = [(m, l, rep) for rep in range(1, runner.REPS + 1)
                      for m in runner.MATRICES for l in runner.LAYOUTS]
    import random
    rng = random.Random(runner.SEED)
    rng.shuffle(expected_cells)
    checks: dict[str, bool] = {}
    checks["protocol_id"] = raw.get("protocol") == "SUBSTRATE_OFFLINE_CANDIDATE_SNAPSHOT_EFFICACY_V1_1"
    checks["locked_inputs_current"] = raw.get("locked_inputs") == expected_lock
    checks["lock_digest_matches"] = raw.get("lock_sha256") == sha(runner.LOCK)
    checks["schedule_exact"] = raw.get("schedule") == [list(x) for x in expected_cells]
    checks["worker_count"] = len(workers) == runner.REPS * len(runner.MATRICES) * len(runner.LAYOUTS)
    checks["no_worker_failures"] = not raw.get("worker_failures") and all(not w.get("worker_error") for w in workers)
    all_cell_keys = {(w.get("matrix_name"), w.get("layout"), w.get("replicate")) for w in workers}
    checks["cell_coverage_unique"] = len(all_cell_keys) == len(workers) and all_cell_keys == set(expected_cells)

    input_reconstruction = True
    isolation = True
    positive_reconstruction = True
    negative_reconstruction = True
    backend_parity = True
    candidate_scores = []
    frozen_scores = []
    exposure_scores = []
    acquired_rows = 0
    acquired_routes = 0
    false_accepts = 0
    candidate_generator_mints = 0
    novelty_unadjudicated = 0
    all_rows_complete = True
    for worker in workers:
        if worker.get("worker_error"):
            continue
        matrix_name, layout_name = worker["matrix_name"], worker["layout"]
        cand_train = worker["candidate_train"]
        expected_matrix, _, train_base, train_target = runner.row_data(matrix_name, layout_name)
        input_reconstruction &= cand_train.get("matrix") == expected_matrix
        input_reconstruction &= cand_train.get("base") == train_base and cand_train.get("target") == train_target
        expected_acquired = cand_train.get("acquired_expected_generator")
        acquired_rows += int(expected_acquired is not None)
        isolation &= all(worker["isolation"].get(k) is True for k in (
            "primary_unchanged", "candidate_snapshot_unchanged_after_evaluation",
            "candidate_branch_isolated_from_primary", "frozen_source_unchanged", "exposure_source_unchanged", "reusable_source_unchanged", "reusable_snapshot_contract",
        ))
        isolation &= worker["isolation"].get("primary_digest_after") == worker.get("baseline_digest")
        isolation &= worker["isolation"].get("candidate_snapshot_digest_after") == worker.get("candidate_snapshot_digest")

        arm_rows = {arm: worker[arm]["positive"] for arm in
                    ("candidate_eager", "candidate_shared", "candidate_reusable", "frozen", "exposure")}
        for arm, rows in arm_rows.items():
            if len(rows) != len(fixtures.HELDOUT):
                all_rows_complete = False
            exact = 0
            for i, row in enumerate(rows):
                expected_base, expected_target = positive_inputs(matrix_name, layout_name, i)
                positive_reconstruction &= row.get("base") == expected_base and row.get("target") == expected_target
                if row.get("independent_predictions"):
                    independent_match = row["independent_predictions"] == expected_target
                    positive_reconstruction &= bool(row.get("exact_target_match")) == independent_match
                exact += int(bool(row.get("exact_target_match")))
                if arm == "candidate_eager" and expected_acquired:
                    acquired_routes += int(row.get("route") == "training_acquired" and
                                            row.get("selected_generator") == expected_acquired.get("name"))
            if arm == "candidate_eager":
                candidate_scores.append(exact / max(1, len(rows)))
            elif arm == "frozen":
                frozen_scores.append(exact / max(1, len(rows)))
            elif arm == "exposure":
                exposure_scores.append(exact / max(1, len(rows)))

        backend_parity &= semantic(worker["candidate_eager"]["positive"], SEMANTIC_FIELDS) == semantic(
            worker["candidate_shared"]["positive"], SEMANTIC_FIELDS)
        backend_parity &= semantic(worker["candidate_eager"]["negative"], (
            "status", "residual", "transforms", "selected_generator", "independent_predictions",
            "accepted", "false_accept", "minted_axes", "novelty_status_unadjudicated",
        )) == semantic(worker["candidate_shared"]["negative"], (
            "status", "residual", "transforms", "selected_generator", "independent_predictions",
            "accepted", "false_accept", "minted_axes", "novelty_status_unadjudicated",
        ))
        backend_parity &= semantic(worker["candidate_eager"]["positive"], SEMANTIC_FIELDS) == semantic(
            worker["candidate_reusable"]["positive"], SEMANTIC_FIELDS)
        backend_parity &= semantic(worker["candidate_eager"]["negative"], (
            "status", "residual", "transforms", "selected_generator", "independent_predictions",
            "accepted", "false_accept", "minted_axes", "novelty_status_unadjudicated",
        )) == semantic(worker["candidate_reusable"]["negative"], (
            "status", "residual", "transforms", "selected_generator", "independent_predictions",
            "accepted", "false_accept", "minted_axes", "novelty_status_unadjudicated",
        ))
        backend_parity &= worker["candidate_eager"]["new_generators_during_evaluation"] == \
            worker["candidate_shared"]["new_generators_during_evaluation"] == \
            worker["candidate_reusable"]["new_generators_during_evaluation"]

        for backend in ("candidate_eager", "candidate_shared", "candidate_reusable"):
            branch = worker[backend]
            candidate_generator_mints += len(branch.get("new_generators_during_evaluation", []))
            for i, row in enumerate(branch.get("negative", [])):
                expected_base, expected_target = negative_inputs(i)
                negative_reconstruction &= row.get("base") == expected_base and row.get("target") == expected_target
                false_accepts += int(bool(row.get("false_accept"))) if backend == "candidate_eager" else 0
                novelty_unadjudicated += int(bool(row.get("novelty_status_unadjudicated"))) if backend == "candidate_eager" else 0

    paired = []
    for c, f, e in zip(candidate_scores, frozen_scores, exposure_scores):
        paired.append({"candidate_minus_frozen_pp": 100 * (c - f),
                       "candidate_minus_exposure_pp": 100 * (c - e)})
    checks["training_input_reconstruction"] = bool(input_reconstruction)
    checks["positive_input_and_oracle_reconstruction"] = bool(positive_reconstruction)
    checks["negative_input_reconstruction"] = bool(negative_reconstruction)
    checks["branch_isolation"] = bool(isolation)
    checks["candidate_backend_semantic_parity"] = bool(backend_parity)
    checks["complete_positive_rows"] = bool(all_rows_complete)
    checks["no_candidate_generator_mint_during_evaluation"] = candidate_generator_mints == 0
    checks["all_acquired_positive_calls_route_to_acquired_generator"] = acquired_routes == acquired_rows * len(fixtures.HELDOUT)

    summary = {
        "worker_count": len(workers),
        "acquired_workers": acquired_rows,
        "total_heldout_calls_per_arm": len(workers) * len(fixtures.HELDOUT),
        "candidate_exact_positive_calls": round(sum(candidate_scores) * len(fixtures.HELDOUT)),
        "frozen_exact_positive_calls": round(sum(frozen_scores) * len(fixtures.HELDOUT)),
        "exposure_exact_positive_calls": round(sum(exposure_scores) * len(fixtures.HELDOUT)),
        "paired_cell_differences": paired,
        "median_candidate_minus_frozen_pp": statistics.median(x["candidate_minus_frozen_pp"] for x in paired) if paired else None,
        "median_candidate_minus_exposure_pp": statistics.median(x["candidate_minus_exposure_pp"] for x in paired) if paired else None,
        "mean_candidate_exact_positive_rate_pct": 100 * statistics.mean(candidate_scores) if candidate_scores else None,
        "mean_frozen_exact_positive_rate_pct": 100 * statistics.mean(frozen_scores) if frozen_scores else None,
        "mean_exposure_exact_positive_rate_pct": 100 * statistics.mean(exposure_scores) if exposure_scores else None,
        "mean_candidate_minus_frozen_pp": statistics.mean(x["candidate_minus_frozen_pp"] for x in paired) if paired else None,
        "mean_candidate_minus_exposure_pp": statistics.mean(x["candidate_minus_exposure_pp"] for x in paired) if paired else None,
        "acquired_training_generator_routes": acquired_routes,
        "false_accepts_on_negative_tasks": false_accepts,
        "new_candidate_generators_during_evaluation": candidate_generator_mints,
        "negative_novelty_signals_unadjudicated": novelty_unadjudicated,
        "median_candidate_training_closure_wall_ms": 1000 * statistics.median(
            w["candidate_train"]["closure_wall_s"] for w in workers if not w.get("worker_error")),
        "median_candidate_snapshot_fork_wall_ms": 1000 * statistics.median(
            w["candidate_fork_wall_s"] for w in workers if not w.get("worker_error")),
        "median_branch_validation_wall_ms": {
            arm: 1000 * statistics.median(w[arm]["branch_evaluation_wall_s"] for w in workers if not w.get("worker_error"))
            for arm in ("candidate_eager", "candidate_shared", "candidate_reusable", "frozen", "exposure")
        },
        "median_branch_fork_wall_ms": {
            arm: 1000 * statistics.median(w[arm]["fork_wall_s"] for w in workers if not w.get("worker_error"))
            for arm in ("candidate_eager", "candidate_shared", "candidate_reusable", "frozen", "exposure")
        },
        "median_validation_rule_closure_wall_ms": {
            arm: {"positive": 1000 * statistics.median(w[arm]["positive_closure_wall_s"] for w in workers if not w.get("worker_error")),
                  "negative": 1000 * statistics.median(w[arm]["negative_closure_wall_s"] for w in workers if not w.get("worker_error"))}
            for arm in ("candidate_eager", "candidate_shared", "candidate_reusable", "frozen", "exposure")
        },
        "median_worker_wall_s": statistics.median(w["elapsed_wall_s"] for w in workers if not w.get("worker_error")),
        "median_peak_rss_kib": statistics.median(w["peak_rss_kib"] for w in workers if not w.get("worker_error")),
        "performance_claim": "no general CoW performance claim; this panel's backend gate is semantic parity only",
    }
    result = {"protocol": raw.get("protocol"), "checks": checks,
              "passed_checks": sum(checks.values()), "total_checks": len(checks),
              "all_checks_pass": all(checks.values()), "summary": summary}
    ANALYSIS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
