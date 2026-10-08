#!/usr/bin/env python3
"""Independent analysis of high-degree edge deletion and reinsertion cost."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/high_degree_edge_delete_churn_v1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(rows: list[dict], key: str) -> int:
    return int(statistics.median(row[key] for row in rows))


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    checks = {
        "runner_gates_pass": raw.get("all_checks_pass") is True and all(raw["checks"].values()),
        "parent_lock_stable": raw.get("locked_inputs") == raw.get("post_run_inputs") == lock,
        "worker_snapshots_stable": all(r.get("before") == lock == r.get("after") for r in raw["runs"]),
        "worker_pids_unique": len({r["pid"] for r in raw["runs"]}) == 9,
        "manifest_success": raw["run_manifest"].get("exit_status") == 0,
    }
    cells = []
    for n in (5_000, 20_000, 80_000):
        rows = [r for r in raw["runs"] if r["n"] == n]
        checks[f"three_workers_{n}"] = len(rows) == 3
        checks[f"exact_mutation_oracles_{n}"] = len(rows) == 3 and all(
            r["removed_count"] == n and r["edge_count_after_delete"] == 0
            and r["sample_before"] == [True] * len(r["sample_ids"])
            and r["sample_absent_after_delete"] == [True] * len(r["sample_ids"])
            and r["sample_after_reinsert"] == [True] * len(r["sample_ids"])
            and r["counts_after_reinsert"] == {"nodes": n + 1, "edges": n} for r in rows)
        if len(rows) == 3:
            cells.append({
                "n": n, "replicates": len(rows),
                "median_node_build_wall_ns": median(rows, "node_build_wall_ns"),
                "median_edge_build_wall_ns": median(rows, "edge_build_wall_ns"),
                "median_delete_all_wall_ns": median(rows, "delete_all_wall_ns"),
                "median_reinsert_all_wall_ns": median(rows, "reinsert_all_wall_ns"),
                "median_delete_ns_per_edge": median(rows, "delete_all_wall_ns") / n,
                "median_reinsert_ns_per_edge": median(rows, "reinsert_all_wall_ns") / n,
            })
    growth = {
        "delete_5k_to_20k": cells[1]["median_delete_all_wall_ns"] / cells[0]["median_delete_all_wall_ns"],
        "delete_20k_to_80k": cells[2]["median_delete_all_wall_ns"] / cells[1]["median_delete_all_wall_ns"],
        "reinsert_5k_to_20k": cells[1]["median_reinsert_all_wall_ns"] / cells[0]["median_reinsert_all_wall_ns"],
        "reinsert_20k_to_80k": cells[2]["median_reinsert_all_wall_ns"] / cells[1]["median_reinsert_all_wall_ns"],
    }
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-high-degree-edge-delete-churn-v1-independent-analysis",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK), "cells": cells, "growth_ratios": growth,
        "checks": checks, "all_checks_pass": all(checks.values()),
        "claim_boundary": "Exact deletion/reinsertion semantics and descriptive cost curve for one homogeneous hub bucket over three sizes; no general asymptotic or mixed-graph claim.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": sum(checks.values()), "checks_total": len(checks),
                      "all_checks_pass": result["all_checks_pass"], "cells": cells,
                      "growth_ratios": growth, "output": str(OUT.relative_to(ROOT))},
                     indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
