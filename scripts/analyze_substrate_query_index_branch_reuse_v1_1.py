#!/usr/bin/env python3
"""Validate and summarize cached versus uncached hypothesis branch batches."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_query_index_branch_reuse_v1_20260930_raw.json"
LOCK = ROOT / "evaluation/substrate_capability/substrate_query_index_branch_reuse_v1_20260930_lock.json"
OUT = ROOT / "evaluation/reports/substrate_query_index_branch_reuse_v1_1_20260930_analysis.json"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_QUERY_INDEX_BRANCH_REUSE_V1_1_AMENDMENT_20260930.md"


def median(xs):
    return statistics.median(xs) if xs else None


def main():
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    checks = []

    def check(name, condition, detail=None):
        checks.append({"name": name, "ok": bool(condition), "detail": detail})

    anchors = raw.get("anchors", [])
    check("raw_matches_source_lock", raw.get("lock") == lock)
    check("captured_runner_source_still_matches",
          lock["sources"]["scripts/substrate_query_index_branch_reuse_v1.py"] ==
          "sha256:" + hashlib.sha256(
              (ROOT / "scripts/substrate_query_index_branch_reuse_v1.py").read_bytes()).hexdigest())
    check("captured_original_analyzer_source_still_matches",
          lock["sources"]["scripts/analyze_substrate_query_index_branch_reuse_v1.py"] ==
          "sha256:" + hashlib.sha256(
              (ROOT / "scripts/analyze_substrate_query_index_branch_reuse_v1.py").read_bytes()).hexdigest())
    check("three_expected_anchors", [x["anchor"] for x in anchors] == ["point", "edge", "triangle"])
    check("no_worker_failures", not raw.get("worker_failures"))
    batches = {1: {"cached": [], "uncached": []},
               5: {"cached": [], "uncached": []},
               20: {"cached": [], "uncached": []}}
    paired_speedups = {1: [], 5: [], 20: []}
    for anchor in anchors:
        check(f"{anchor['anchor']}_pool_complete", anchor["pool"]["complete"] and
              anchor["pool"]["halt_reason"] == "max_size")
        check(f"{anchor['anchor']}_five_repetitions", len(anchor["repetitions"]) == 5)
        for rep in anchor["repetitions"]:
            check(f"{anchor['anchor']}_rep_{rep['replicate']}_three_batch_sizes", len(rep["batches"]) == 3)
            for batch in rep["batches"]:
                size = batch["branch_count"]
                check(f"{anchor['anchor']}_rep_{rep['replicate']}_b{size}_parity",
                      batch["exact_branch_parity"])
                check(f"{anchor['anchor']}_rep_{rep['replicate']}_b{size}_target_ids",
                      len(batch["target_ids"]) == size and len(set(batch["target_ids"])) == size)
                check(f"{anchor['anchor']}_rep_{rep['replicate']}_b{size}_arms",
                      set(batch["arms"]) == {"cached", "uncached"})
                for mode, arm in batch["arms"].items():
                    check(f"{anchor['anchor']}_rep_{rep['replicate']}_b{size}_{mode}_targets_preserved",
                          all(branch["target_id"] in branch["final_survivors"]
                              for branch in arm["branches"]))
                    check(f"{anchor['anchor']}_rep_{rep['replicate']}_b{size}_{mode}_branch_count",
                          arm["branch_count"] == size and len(arm["branches"]) == size)
                    check(f"{anchor['anchor']}_rep_{rep['replicate']}_b{size}_{mode}_timing_nonnegative",
                          arm["batch_wall_s"] >= 0 and arm["batch_cpu_s"] >= 0 and
                          arm["index_build_wall_s"] >= 0)
                    batches[size][mode].append(arm)
                uncached_wall = batch["arms"]["uncached"]["batch_wall_s"]
                cached_wall = batch["arms"]["cached"]["batch_wall_s"]
                paired_speedups[size].append(uncached_wall / cached_wall if cached_wall else None)
    summaries = {}
    for size, modes in batches.items():
        summaries[str(size)] = {}
        for mode, rows in modes.items():
            summaries[str(size)][mode] = {
                "n_paired_batches": len(rows),
                "median_batch_wall_s": median([row["batch_wall_s"] for row in rows]),
                "median_batch_cpu_s": median([row["batch_cpu_s"] for row in rows]),
                "median_total_queries": median([row["total_queries"] for row in rows]),
                "median_queries_per_branch": median([row["total_queries"] / size for row in rows]),
                "target_preserved_branches": sum(
                    branch["target_id"] in branch["final_survivors"]
                    for row in rows for branch in row["branches"]),
                "total_branches": sum(row["branch_count"] for row in rows),
                "unique_target_recovery_branches": sum(
                    branch["target_recovered"]
                    for row in rows for branch in row["branches"]),
                "median_native_selector_prediction_evaluations": median([
                    row["native_selector_prediction_evaluations"] for row in rows]),
                "median_target_response_evaluations": median([
                    row["target_response_evaluations"] for row in rows]),
                "median_index_build_wall_s": median([row["index_build_wall_s"] for row in rows]),
                "median_index_heap_bytes": median([row["index_retained_heap_bytes"]
                                                    for row in rows if row["index_retained_heap_bytes"]]),
                "median_paired_speedup_uncached_over_cached": median(paired_speedups[size]),
            }
    check("all_registered_batch_sizes_measured", all(
        len(batches[size]["cached"]) == len(batches[size]["uncached"]) == 15
        for size in batches))
    report = {
        "protocol": raw.get("protocol"),
        "raw_sha256": "sha256:" + hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "amendment_sha256": "sha256:" + hashlib.sha256(AMENDMENT.read_bytes()).hexdigest(),
        "runner_source_sha256": "sha256:" + hashlib.sha256(
            (ROOT / "scripts/substrate_query_index_branch_reuse_v1.py").read_bytes()).hexdigest(),
        "analyzer_sha256": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": checks, "check_count": len(checks),
        "failed_checks": [x for x in checks if not x["ok"]],
        "all_checks_pass": all(x["ok"] for x in checks),
        "generation": {row["anchor"]: row["pool"] for row in anchors},
        "batches": summaries,
        "interpretation": "Evidence covers serial in-process branches over alternate generated hypotheses. It measures cached query computation reuse, not graph or Rust Substrate CoW.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT), "checks": len(checks),
                      "failed": len(report["failed_checks"]),
                      "all_checks_pass": report["all_checks_pass"],
                      "batches": summaries}, sort_keys=True))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
