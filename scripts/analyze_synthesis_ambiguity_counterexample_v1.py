#!/usr/bin/env python3
"""Independent integrity, oracle, and paired analysis for hinge ambiguity panel."""
from __future__ import annotations

import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
import synthesis_ambiguity_counterexample_v1 as runner

RAW = ROOT / "evaluation/reports/synthesis_ambiguity_counterexample_v1_20260930_raw.json"
OUT = ROOT / "evaluation/reports/synthesis_ambiguity_counterexample_v1_analysis_20260930.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_arm(rows: list[dict], arm: str) -> dict:
    valid = [r for r in rows if r.get("arm") == arm and not r.get("worker_error")]
    statuses = [r["candidate"].get("status") for r in valid]
    accepted = [r for r in valid if r["candidate"].get("status") == "accepted"]
    exact_training = 0
    exact_holdout = 0
    holdout_points = 0
    false_accept_workers = 0
    false_accept_points = 0
    tested = []
    wall = []
    cpu = []
    for worker in valid:
        cand = worker["candidate"]
        enum = cand.get("enumerate") or {}
        if enum.get("tested") is not None:
            tested.append(enum["tested"])
        wall.append(worker.get("pump_wall_s", 0) * 1000)
        cpu.append(worker.get("pump_cpu_s", 0) * 1000)
        eager = cand["eager"].get("evaluations", [])
        train_rows = [x for x in eager if x.get("split") == "training"]
        heldout = [x for x in eager if x.get("split") == "heldout"]
        exact_training += sum(bool(x.get("exact")) for x in train_rows)
        exact_holdout += sum(bool(x.get("exact")) for x in heldout)
        holdout_points += len(heldout)
        wrong = sum(not bool(x.get("exact")) for x in heldout)
        false_accept_points += wrong if cand.get("status") == "accepted" else 0
        false_accept_workers += int(cand.get("status") == "accepted" and wrong > 0)
    return {
        "workers": len(valid), "accepted": len(accepted), "gapped": statuses.count("gapped"),
        "exact_training_points": exact_training,
        "exact_heldout_points": exact_holdout, "heldout_points_with_program": holdout_points,
        "false_accept_workers": false_accept_workers,
        "false_accept_heldout_points": false_accept_points,
        "candidate_tests": tested,
        "median_candidate_tests": statistics.median(tested) if tested else None,
        "median_pump_wall_ms": statistics.median(wall) if wall else None,
        "median_pump_cpu_ms": statistics.median(cpu) if cpu else None,
        "median_peak_rss_kib": statistics.median(r.get("peak_rss_kib", 0) for r in valid) if valid else None,
    }


def main() -> int:
    raw = json.loads(RAW.read_text())
    expected_lock = json.loads(json.dumps(runner.lock_payload()))
    expected_schedule = [(arm, rep) for rep in range(1, runner.REPS + 1) for arm in runner.ARMS]
    random.Random(runner.SEED).shuffle(expected_schedule)
    workers = raw.get("workers", [])
    checks = {
        "protocol_id": raw.get("protocol") == runner.STEM,
        "lock_matches_current_sources": raw.get("locked_inputs") == expected_lock,
        "lock_digest_matches": raw.get("lock_sha256") == sha(runner.LOCK),
        "schedule_exact": raw.get("schedule") == [list(x) for x in expected_schedule],
        "worker_count": len(workers) == len(expected_schedule),
        "no_worker_failures": not raw.get("worker_failures") and all(not w.get("worker_error") for w in workers),
        "unique_worker_pids": len({w.get("pid") for w in workers}) == len(workers) and all(w.get("pid") for w in workers),
    }
    cells = {(w.get("arm"), w.get("replicate")) for w in workers}
    expected_cells = {(arm, rep) for arm in runner.ARMS for rep in range(1, runner.REPS + 1)}
    checks["unique_complete_cells"] = len(cells) == len(workers) and cells == expected_cells

    label_reconstruction = True
    isolation = True
    parity = True
    accepted_program_integrity = True
    for worker in workers:
        if worker.get("worker_error"):
            continue
        arm = worker["arm"]
        expected_train = [{"inputs": {"r": r, "c": c}, "output": runner.target(r, c)}
                          for r, c in runner.train_rows(arm)]
        expected_holdout = [{"inputs": {"r": r, "c": c}, "output": runner.target(r, c)}
                            for r, c in runner.HOLDOUT]
        label_reconstruction &= worker.get("training") == expected_train
        label_reconstruction &= worker.get("holdout") == expected_holdout
        cand = worker["candidate"]
        eager, shared = cand["eager"], cand["shared_graph_pages"]
        isolation &= worker.get("primary", {}).get("unchanged") is True
        isolation &= worker.get("primary", {}).get("digest_before") == worker.get("primary", {}).get("digest_after")
        isolation &= cand.get("snapshot_unchanged") is True
        isolation &= eager.get("source_unchanged") is True and shared.get("source_unchanged") is True
        isolation &= eager.get("source_equals_candidate_snapshot") is True
        isolation &= shared.get("source_equals_candidate_snapshot") is True
        is_accepted = cand.get("status") == "accepted"
        if is_accepted:
            accepted_program_integrity &= cand.get("program_id") is not None and cand.get("ir") is not None
            accepted_program_integrity &= eager.get("ir_root_count") == shared.get("ir_root_count") == 1
            for backend in (eager, shared):
                values = backend.get("evaluations", [])
                train_values = [x for x in values if x.get("split") == "training"]
                holdout_values = [x for x in values if x.get("split") == "heldout"]
                expected_training = expected_train
                label_reconstruction &= len(train_values) == len(expected_training)
                label_reconstruction &= len(holdout_values) == len(expected_holdout)
                for expected, actual in zip(expected_training, train_values):
                    label_reconstruction &= actual.get("inputs") == expected["inputs"]
                    label_reconstruction &= actual.get("expected") == expected["output"]
                    label_reconstruction &= actual.get("exact") is (actual.get("halted") is True and
                                                                      actual.get("trap") is None and
                                                                      actual.get("predicted") == expected["output"])
                for expected, actual in zip(expected_holdout, holdout_values):
                    label_reconstruction &= actual.get("inputs") == expected["inputs"]
                    label_reconstruction &= actual.get("expected") == expected["output"]
                    label_reconstruction &= actual.get("exact") is (actual.get("halted") is True and
                                                                      actual.get("trap") is None and
                                                                      actual.get("predicted") == expected["output"])
        else:
            accepted_program_integrity &= cand.get("program_id") is None
            accepted_program_integrity &= eager.get("ir_root_count") == shared.get("ir_root_count") == 0
            accepted_program_integrity &= eager.get("evaluations") == shared.get("evaluations") == []
        parity &= eager.get("evaluations") == shared.get("evaluations")
        parity &= eager.get("ir_root_count") == shared.get("ir_root_count")
        parity &= eager.get("result_digest") == shared.get("result_digest")

    summaries = {arm: analyze_arm(workers, arm) for arm in runner.ARMS}
    sparse = summaries["ambiguous_default"]
    corrected = summaries["counterexample_default"]
    oracle = summaries["counterexample_oracle_grammar"]
    ambiguity_observed = sparse["false_accept_workers"] > 0
    corrected_safe = corrected["false_accept_workers"] == 0
    oracle_safe = oracle["false_accept_workers"] == 0
    checks["independent_label_and_output_reconstruction"] = bool(label_reconstruction)
    checks["candidate_and_primary_isolation"] = bool(isolation)
    checks["eager_shared_semantic_and_state_parity"] = bool(parity)
    checks["accepted_ir_and_gap_integrity"] = bool(accepted_program_integrity)
    checks["sparse_ambiguity_false_acceptance_observed"] = bool(ambiguity_observed)
    checks["counterexample_default_has_no_false_acceptance"] = bool(corrected_safe)
    checks["oracle_grammar_has_no_false_acceptance"] = bool(oracle_safe)

    result = {
        "protocol": raw.get("protocol"), "checks": checks,
        "passed_checks": sum(bool(v) for v in checks.values()), "total_checks": len(checks),
        "all_checks_pass": all(checks.values()),
        "summary": {
            "arm_summaries": summaries,
            "one_counterexample_changes_default_outcome": {
                "sparse_default": {"accepted": sparse["accepted"], "false_accept_workers": sparse["false_accept_workers"]},
                "corrected_default": {"accepted": corrected["accepted"], "gapped": corrected["gapped"],
                                      "false_accept_workers": corrected["false_accept_workers"]},
            },
            "oracle_grammar_supplied": runner.OPS,
            "interpretation": "A query can remove the sparse false-fit while leaving broad search unable to finish; the compact grammar arm supplies external task knowledge.",
            "claim_boundary": raw.get("claim_boundary"),
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
