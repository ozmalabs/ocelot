#!/usr/bin/env python3
"""Independent analysis of the public high-degree remove_node replay."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_high_degree_remove_node_scale_v1_1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/high_degree_remove_node_scale_v1_1_lock_20260928.json"
CHURN_RAW = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_20260928.json"
BATCH_RAW = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_batch_v1_20260928.json"
BATCH_ANALYSIS = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_batch_v1_analysis_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_high_degree_remove_node_scale_v1_1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(rows: list[dict], key: str) -> int:
    return int(statistics.median(r[key] for r in rows))


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    churn = json.loads(CHURN_RAW.read_text())
    batch = json.loads(BATCH_RAW.read_text())
    batch_analysis = json.loads(BATCH_ANALYSIS.read_text())
    checks = {
        "runner_gates_pass": raw.get("all_checks_pass") is True and all(raw["checks"].values()),
        "stable_parent_lock": raw.get("locked_inputs") == raw.get("post_run_inputs") == lock,
        "worker_snapshots_stable": all(r.get("before") == lock == r.get("after") for r in raw["runs"]),
        "unique_worker_pids": len({r["pid"] for r in raw["runs"]}) == 9,
        "baseline_captures_pass": churn.get("all_checks_pass") is True and batch.get("all_checks_pass") is True,
        "batch_independent_analysis_passed": batch_analysis.get("all_checks_pass") is True,
        "run_manifest_success": raw["run_manifest"].get("exit_status") == 0,
    }
    cells = []
    for n in (5_000, 20_000, 80_000):
        rows = [r for r in raw["runs"] if r["n"] == n]
        churn_rows = [r for r in churn["runs"] if r["n"] == n]
        batch_rows = [r for r in batch["runs"] if r["n"] == n]
        checks[f"three_workers_{n}"] = len(rows) == len(churn_rows) == len(batch_rows) == 3
        checks[f"public_remove_node_semantics_{n}"] = len(rows) == 3 and all(
            r["removed"] is True and r["root_absent"] is True
            and r["node_count"] == r["node_rows"] == n and r["edge_count"] == 0
            and r["all_nodes_are_leaves"] is True and r["ordinal_values"] == list(range(n))
            and [x["attrs"].get("ordinal") for x in r["samples"]] == r["expected_sample_ordinals"]
            and r["hook_events"] == [[0, "Hub"]] for r in rows)
        if len(rows) == len(churn_rows) == len(batch_rows) == 3:
            remove_ns = median(rows, "remove_node_wall_ns")
            seq_ns = median(churn_rows, "delete_all_wall_ns")
            batch_ns = int(statistics.median(
                r["arms"]["batch"]["delete_wall_ns"] for r in batch_rows))
            cells.append({
                "n": n, "replicates": 3,
                "median_remove_node_wall_ns": remove_ns,
                "median_sequential_edge_delete_wall_ns": seq_ns,
                "median_batch_edge_delete_wall_ns": batch_ns,
                "remove_node_ns_per_incident_edge": remove_ns / n,
                "remove_node_to_sequential_edge_delete_ratio": remove_ns / seq_ns,
                "remove_node_to_batch_edge_delete_ratio": remove_ns / batch_ns,
                "median_setup_wall_ns": median(rows, "setup_wall_ns"),
            })
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-high-degree-remove-node-scale-v1-1-independent-analysis",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK), "churn_baseline_sha256": sha(CHURN_RAW),
        "batch_baseline_sha256": sha(BATCH_RAW), "batch_analysis_sha256": sha(BATCH_ANALYSIS),
        "cells": cells, "checks": checks, "all_checks_pass": all(checks.values()),
        "claim_boundary": "Public remove_node correctness and time for deleting one high-degree source with outgoing homogeneous edges; no rule-heavy, incoming-hub, or natural-workload claim.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": sum(checks.values()), "checks_total": len(checks),
                      "all_checks_pass": result["all_checks_pass"], "cells": cells,
                      "output": str(OUT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
