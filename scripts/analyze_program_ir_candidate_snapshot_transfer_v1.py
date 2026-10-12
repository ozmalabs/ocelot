#!/usr/bin/env python3
"""Independent integrity, oracle, branch, and cost analysis for Program IR panel."""
from __future__ import annotations

import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
import program_ir_candidate_snapshot_transfer_v1 as runner

RAW = ROOT / "evaluation/reports/program_ir_candidate_snapshot_transfer_v1_20260930_raw.json"
OUT = ROOT / "evaluation/reports/program_ir_candidate_snapshot_transfer_v1_analysis_20260930.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    expected_lock = json.loads(json.dumps(runner.lock_payload()))
    expected_schedule = [(task, rep) for rep in range(1, runner.REPS + 1) for task in runner.TASKS]
    random.Random(runner.SEED).shuffle(expected_schedule)
    workers = raw.get("workers", [])
    checks = {
        "protocol": raw.get("protocol") == "program_ir_candidate_snapshot_transfer_v1_20260930",
        "lock_matches_current_sources": raw.get("locked_inputs") == expected_lock,
        "lock_digest_matches": raw.get("lock_sha256") == sha(runner.LOCK),
        "schedule_exact": raw.get("schedule") == [list(x) for x in expected_schedule],
        "worker_count": len(workers) == len(expected_schedule),
        "no_worker_failures": not raw.get("worker_failures") and all(not w.get("worker_error") for w in workers),
        "unique_processes": len({w.get("pid") for w in workers}) == len(workers) and all(w.get("pid") for w in workers),
    }
    coverage = {(w.get("task"), w.get("replicate")) for w in workers}
    checks["cell_coverage_exact"] = coverage == set(expected_schedule) and len(coverage) == len(workers)
    checks["stable_task_definitions"] = expected_lock["design"]["tasks"] == runner.TASKS

    isolation_ok = True
    oracle_ok = True
    parity_ok = True
    controls_ok = True
    candidates = []
    transfer_rows = []
    false_accepts = 0
    all_worker_details = []
    for worker in workers:
        if worker.get("worker_error"):
            continue
        task = worker["task"]
        cand = worker["candidate"]
        eager = cand["eager"]
        shared = cand["shared_graph_pages"]
        frozen = worker["frozen"]
        exposure = worker["exposure_without_pump"]
        isolation_ok &= all(worker["isolation"].values())
        isolation_ok &= cand.get("snapshot_unchanged_after_eval") is True
        isolation_ok &= eager.get("source_unchanged") is True and shared.get("source_unchanged") is True
        isolation_ok &= eager.get("source_digest_before") == cand.get("snapshot_digest")
        isolation_ok &= shared.get("source_digest_before") == cand.get("snapshot_digest")
        isolation_ok &= frozen["evaluation"].get("source_unchanged") is True
        isolation_ok &= exposure["evaluation"].get("source_unchanged") is True
        isolation_ok &= worker["isolation"].get("baseline_unchanged") is True
        isolation_ok &= worker["baseline_digest"] == worker["isolation"].get("baseline_digest_after")

        expected_outputs = []
        for x in runner.TASKS[task]["heldout"]:
            expected_outputs.append({"input": x, "expected": runner.oracle(task, x)})
        for arm_name, arm in (("eager", eager), ("shared_graph_pages", shared)):
            outputs = arm.get("outputs", [])
            oracle_ok &= len(outputs) == len(expected_outputs)
            for expected, actual in zip(expected_outputs, outputs):
                oracle_ok &= actual.get("input") == expected["input"]
                oracle_ok &= actual.get("expected") == expected["expected"]
                oracle_ok &= actual.get("exact") is (actual.get("halted") is True and
                                                      actual.get("trap") is None and
                                                      actual.get("predicted") == expected["expected"])
                false_accepts += int(not actual.get("exact")) if arm_name == "eager" and cand.get("status") == "accepted" else 0
            oracle_ok &= arm.get("task_program_present") is True if cand.get("status") == "accepted" else True
            if arm_name == "eager":
                transfer_rows.append({"task": task, "replicate": worker["replicate"],
                                      "status": cand.get("status"),
                                      "exact_points": sum(bool(x.get("exact")) for x in outputs),
                                      "available_points": len(outputs)})

        parity_fields = ("program_node_count", "task_program_present", "ir_root_count", "outputs")
        parity_ok &= all(eager.get(k) == shared.get(k) for k in parity_fields)
        parity_ok &= eager.get("result_digest") == shared.get("result_digest")
        controls_ok &= frozen.get("task_program_count") == 0
        controls_ok &= exposure.get("task_program_count_before_eval") == 0
        controls_ok &= len(frozen["evaluation"].get("outputs", [])) == 0
        controls_ok &= len(exposure["evaluation"].get("outputs", [])) == 0
        controls_ok &= exposure.get("message_id") is not None
        controls_ok &= exposure.get("request") == runner.TASKS[task]["request"]
        controls_ok &= exposure.get("training_rows") == runner.TASKS[task]["training"]
        acquired = cand.get("status") == "accepted" and cand.get("program_id") is not None and cand.get("ir_root_count") == 1
        candidates.append(bool(acquired))
        all_worker_details.append({"task": task, "replicate": worker["replicate"], "status": cand.get("status"),
                                   "candidate_ir_root_count": cand.get("ir_root_count"),
                                   "eager_exact": sum(bool(x.get("exact")) for x in eager.get("outputs", [])),
                                   "shared_exact": sum(bool(x.get("exact")) for x in shared.get("outputs", [])),
                                   "eager_wall_ms": 1000 * eager.get("branch_wall_s", 0),
                                   "shared_wall_ms": 1000 * shared.get("branch_wall_s", 0),
                                   "train_wall_ms": 1000 * cand.get("train_wall_s", 0),
                                   "peak_rss_kib": worker.get("peak_rss_kib")})

    checks["branch_isolation_and_snapshot_immutability"] = bool(isolation_ok)
    checks["exact_oracle_reconstruction"] = bool(oracle_ok)
    checks["candidate_eager_shared_semantic_parity"] = bool(parity_ok)
    checks["frozen_and_exposure_control_states"] = bool(controls_ok)
    checks["accepted_candidate_has_one_ir_root"] = all(
        (w.get("candidate", {}).get("status") != "accepted" or
         (w["candidate"].get("ir_root_count") == 1 and w["candidate"].get("program_id") is not None))
        for w in workers if not w.get("worker_error"))
    checks["one_task_named_program_per_accepted_candidate"] = all(
        (w.get("candidate", {}).get("status") != "accepted" or
         (w["candidate"].get("program_count") == 1 and
          w["candidate"].get("eager", {}).get("task_program_present") is True and
          w["candidate"].get("shared_graph_pages", {}).get("task_program_present") is True))
        for w in workers if not w.get("worker_error"))

    valid_workers = [w for w in workers if not w.get("worker_error")]
    eager_walls = [w["candidate"]["eager"]["branch_wall_s"] * 1000 for w in valid_workers]
    shared_walls = [w["candidate"]["shared_graph_pages"]["branch_wall_s"] * 1000 for w in valid_workers]
    train_walls = [w["candidate"]["train_wall_s"] * 1000 for w in valid_workers]
    exact_total = sum(x["exact_points"] for x in transfer_rows)
    available_total = sum(x["available_points"] for x in transfer_rows)
    summary = {
        "workers": len(valid_workers),
        "candidate_acquisitions": sum(candidates),
        "candidate_acquisition_rate": sum(candidates) / len(candidates) if candidates else None,
        "heldout_points": available_total,
        "exact_heldout_points": exact_total,
        "exact_heldout_rate": exact_total / available_total if available_total else None,
        "accepted_false_predictions": false_accepts,
        "per_worker_transfer": transfer_rows,
        "median_training_pump_ms": statistics.median(train_walls) if train_walls else None,
        "median_eager_candidate_validation_ms": statistics.median(eager_walls) if eager_walls else None,
        "median_shared_page_candidate_validation_ms": statistics.median(shared_walls) if shared_walls else None,
        "median_peak_rss_kib": statistics.median(w["peak_rss_kib"] for w in valid_workers) if valid_workers else None,
        "claim_boundary": raw.get("claim_boundary"),
    }
    result = {"protocol": raw.get("protocol"), "checks": checks,
              "passed_checks": sum(bool(x) for x in checks.values()), "total_checks": len(checks),
              "all_checks_pass": all(checks.values()), "summary": summary,
              "worker_details": all_worker_details}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
