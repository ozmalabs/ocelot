#!/usr/bin/env python3
"""Independent analysis of stable-order batch edge deletion."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_batch_v1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/high_degree_edge_delete_batch_v1_lock_20260928.json"
BASE_RAW = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_20260928.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_analysis_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_batch_v1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[int]) -> int:
    return int(statistics.median(values))


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    baseline = json.loads(BASE_RAW.read_text())
    base_analysis = json.loads(BASE_ANALYSIS.read_text())
    checks = {
        "runner_gates_pass": raw.get("all_checks_pass") is True and all(raw["checks"].values()),
        "stable_parent_lock": raw.get("locked_inputs") == raw.get("post_run_inputs") == lock,
        "stable_worker_locks": all(r.get("before") == lock == r.get("after") for r in raw["runs"]),
        "unique_worker_pids": len({r["pid"] for r in raw["runs"]}) == 9,
        "baseline_capture_gates_pass": baseline.get("all_checks_pass") is True,
        "baseline_independent_analysis_pass": base_analysis.get("all_checks_pass") is True,
        "mixed_input_outcomes_exact": raw["semantic_probe"]["sequential_outcomes"]
            == raw["semantic_probe"]["batch_outcomes"] == [True, True, False, False, True],
        "hook_sequence_exact": raw["semantic_probe"]["sequential_events"]
            == raw["semantic_probe"]["batch_events"]
            and len(raw["semantic_probe"]["batch_events"]) == 3,
        "remaining_adjacency_order_exact": raw["checks"].get("stable_remaining_adjacency_order") is True,
        "mixed_graph_snapshot_exact": raw["semantic_probe"]["sequential_graph"]
            == raw["semantic_probe"]["batch_graph"]
            and raw["semantic_probe"]["sequential_digest"] == raw["semantic_probe"]["batch_digest"],
    }
    cells = []
    for n in (5_000, 20_000, 80_000):
        rows = [r for r in raw["runs"] if r["n"] == n]
        old_rows = [r for r in baseline["runs"] if r["n"] == n]
        checks[f"three_pairs_{n}"] = len(rows) == len(old_rows) == 3
        checks[f"paired_exact_state_{n}"] = len(rows) == 3 and all(
            r["arms"]["sequential"]["before_digest"] == r["arms"]["batch"]["before_digest"]
            and r["arms"]["sequential"]["deleted_digest"] == r["arms"]["batch"]["deleted_digest"]
            and r["arms"]["sequential"]["node_count"] == r["arms"]["batch"]["node_count"] == n + 1
            and r["arms"]["sequential"]["edge_count"] == r["arms"]["batch"]["edge_count"] == 0
            and r["arms"]["sequential"]["outcome_true_count"]
                == r["arms"]["batch"]["outcome_true_count"] == n
            for r in rows)
        if len(rows) != 3 or len(old_rows) != 3:
            continue
        seq_times = [r["arms"]["sequential"]["delete_wall_ns"] for r in rows]
        batch_times = [r["arms"]["batch"]["delete_wall_ns"] for r in rows]
        old_times = [r["delete_all_wall_ns"] for r in old_rows]
        cells.append({
            "n": n, "replicates": 3,
            "sequential_median_delete_wall_ns": median(seq_times),
            "batch_median_delete_wall_ns": median(batch_times),
            "baseline_sequential_median_delete_wall_ns": median(old_times),
            "sequential_to_batch_speedup": median(seq_times) / median(batch_times),
            "batch_time_per_edge_ns": median(batch_times) / n,
            "sequential_to_prior_baseline_ratio": median(seq_times) / median(old_times),
            "paired_speedups": [s / b for s, b in zip(seq_times, batch_times)],
        })
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-high-degree-edge-delete-batch-v1-independent-analysis",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK), "baseline_raw_sha256": sha(BASE_RAW),
        "baseline_analysis_sha256": sha(BASE_ANALYSIS), "cells": cells,
        "checks": checks, "all_checks_pass": all(checks.values()),
        "claim_boundary": "Paired sequential-versus-batch deletion cost and exact semantics for one high-degree outgoing bucket; three sizes and replicates; no general complexity claim.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": sum(checks.values()), "checks_total": len(checks),
                      "all_checks_pass": result["all_checks_pass"], "cells": cells,
                      "output": str(OUT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
