#!/usr/bin/env python3
"""Validate and summarize the generated Euler active-query capture."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_generated_euler_active_query_v1_2_20260930_raw.json"
LOCK = ROOT / "evaluation/substrate_capability/substrate_generated_euler_active_query_v1_2_20260930_lock.json"
OUT = ROOT / "evaluation/reports/substrate_generated_euler_active_query_v1_2_20260930_analysis.json"


def median(values):
    return statistics.median(values) if values else None


def main() -> int:
    raw = json.loads(RAW.read_text())
    saved_lock = json.loads(LOCK.read_text())
    checks = []

    def check(name, condition, detail=None):
        checks.append({"name": name, "ok": bool(condition), "detail": detail})

    anchors = raw.get("anchors", [])
    check("capture_matches_saved_source_lock", raw.get("lock") == saved_lock)
    check("expected_anchor_order", [row.get("anchor") for row in anchors] == ["point", "edge", "triangle"])
    check("no_worker_failures", not raw.get("worker_failures"))
    grouped = {}
    for anchor in anchors:
        gen = anchor["generation"]
        check(f"{anchor['anchor']}_bounded_pool_complete",
              gen["halt_reason"] == "max_size" and gen["bounded_pool_complete"],
              {"halt_reason": gen["halt_reason"], "pool_size": gen["pool_size"]})
        check(f"{anchor['anchor']}_pool_contains_heldout_correct", anchor["pool_contains_heldout_correct"])
        check(f"{anchor['anchor']}_run_count", len(anchor["runs"]) == 23)
        candidate_names = set(saved_lock["design"]["candidate_names"])
        for run in anchor["runs"]:
            grouped.setdefault(run["policy"], []).append(run)
            response_names = [row["query"] for row in run["oracle_responses"]]
            check(f"{anchor['anchor']}_{run['policy']}_{run['replicate']}_query_membership",
                  all(name in candidate_names for name in response_names))
            check(f"{anchor['anchor']}_{run['policy']}_{run['replicate']}_no_repeated_queries",
                  len(response_names) == len(set(response_names)))
            check(f"{anchor['anchor']}_{run['policy']}_{run['replicate']}_call_count",
                  run["oracle_calls"] == len(run["oracle_responses"]))
            check(f"{anchor['anchor']}_{run['policy']}_{run['replicate']}_timing_fields",
                  all(row.get("oracle_wall_s", -1) >= 0 and row.get("oracle_cpu_s", -1) >= 0
                      for row in run["oracle_responses"]) and
                  run["decision_compute_wall_s"] >= 0 and run["decision_compute_cpu_s"] >= 0)
            if run["policy"] == "entropy_cached":
                check(f"{anchor['anchor']}_cached_matrix_accounting",
                      run["cache_retained_heap_bytes"] > 0 and
                      run["cache_build_wall_s"] >= 0 and run["matrix_cells_read"] > 0)
            check(f"{anchor['anchor']}_{run['policy']}_{run['replicate']}_ends_at_singleton_or_exhaustion",
                  len(run["final_survivor_ids"]) <= 1 or run["oracle_calls"] == len(candidate_names))
            check(f"{anchor['anchor']}_{run['policy']}_{run['replicate']}_heldout_correct",
                  run["unique_heldout_correct"])

    summary = {}
    for policy, rows in sorted(grouped.items()):
        calls = [row["oracle_calls"] for row in rows]
        summary[policy] = {
            "n": len(rows),
            "unique_heldout_correct": sum(row["unique_heldout_correct"] for row in rows),
            "median_oracle_calls": median(calls),
            "mean_oracle_calls": statistics.mean(calls),
            "max_oracle_calls": max(calls),
            "median_prediction_evaluations": median([row["prediction_evaluations"] for row in rows]),
            "median_selection_wall_s": median([row["selection_wall_s"] for row in rows]),
            "median_selection_cpu_s": median([row["selection_cpu_s"] for row in rows]),
            "median_decision_compute_wall_s": median([row["decision_compute_wall_s"] for row in rows]),
            "median_decision_compute_cpu_s": median([row["decision_compute_cpu_s"] for row in rows]),
            "median_oracle_wall_s": median([row["oracle_wall_s"] for row in rows]),
            "median_oracle_cpu_s": median([row["oracle_cpu_s"] for row in rows]),
            "median_decision_plus_oracle_wall_s": median([
                row["decision_compute_wall_s"] + row["oracle_wall_s"] for row in rows]),
            "median_decision_plus_oracle_and_cache_wall_s": median([
                row["decision_plus_oracle_and_cache_wall_s"] for row in rows]),
            "median_cache_build_wall_s": median([
                row["cache_build_wall_s"] for row in rows if row["cache_build_wall_s"] is not None]),
            "median_cache_heap_bytes": median([
                row["cache_retained_heap_bytes"] for row in rows
                if row["cache_retained_heap_bytes"] is not None]),
            "median_matrix_cells_read": median([row["matrix_cells_read"] for row in rows]),
            "calls_by_anchor": {
                anchor["anchor"]: [run["oracle_calls"] for run in anchor["runs"] if run["policy"] == policy]
                for anchor in anchors
            },
        }
    check("all_registered_policies_present", set(grouped) == {
        "entropy_uncached", "entropy_cached", "fixed_first", "seeded_random"})
    check("each_policy_success_for_every_run", all(
        stats["unique_heldout_correct"] == stats["n"] for stats in summary.values()))
    report = {
        "protocol": raw.get("protocol"),
        "raw_sha256": "sha256:" + hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "analyzer_sha256": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "check_count": len(checks), "checks": checks,
        "failed_checks": [row for row in checks if not row["ok"]],
        "all_checks_pass": all(row["ok"] for row in checks),
        "generation": {
            "pool_sizes": [row["generation"]["pool_size"] for row in anchors],
            "explored": [row["generation"]["explored"] for row in anchors],
            "median_wall_s": median([row["generation"]["wall_s"] for row in anchors]),
            "halt_reasons": [row["generation"]["halt_reason"] for row in anchors],
        },
        "policies": summary,
        "interpretation": "Compare query counts only together with selector computation: entropy recomputes predictions over the remaining pool each round. Claims are limited to these three Euler anchors and generated synthetic complexes.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT), "checks": len(checks),
                      "failed": len(report["failed_checks"]),
                      "all_checks_pass": report["all_checks_pass"],
                      "generation": report["generation"], "policies": summary}, sort_keys=True))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
