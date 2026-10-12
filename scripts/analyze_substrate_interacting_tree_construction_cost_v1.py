#!/usr/bin/env python3
"""Post-hoc phase-cost analysis of the locked interacting-tree closure run."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_interacting_tree_closure_scale_v1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/interacting_tree_closure_scale_v1_lock_20260928.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/substrate_interacting_tree_closure_scale_v1_analysis_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_interacting_tree_construction_cost_v1_analysis_20260928.json"
GRAPH_SOURCE = ROOT / "runners/dsl/src/graph.rs"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(rows: list[dict], key: str) -> int:
    return int(statistics.median(row[key] for row in rows))


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    base = json.loads(BASE_ANALYSIS.read_text())
    source_hash = sha(GRAPH_SOURCE)
    source_hash_locked = lock["files"]["runners/dsl/src/graph.rs"]
    checks = {
        "raw_passed_original_runner_gates": raw.get("all_checks_pass") is True,
        "raw_matches_original_lock": raw.get("locked_inputs") == lock == raw.get("post_run_inputs"),
        "original_independent_analysis_passed": base.get("all_checks_pass") is True,
        "raw_lock_records_original_graph_source_hash": source_hash_locked == raw["locked_inputs"]["files"].get(
            "runners/dsl/src/graph.rs"),
    }
    cells = []
    for n in (10_000, 100_000, 1_000_000):
        for topology in ("balanced", "star"):
            rows = [r for r in raw["runs"] if r["n"] == n and r["topology"] == topology and not r["audit"]]
            checks[f"three_uninstrumented_replicates_{n}_{topology}"] = len(rows) == 3
            if len(rows) != 3:
                continue
            row = {
                "n": n,
                "topology": topology,
                "replicates": len(rows),
                "edge_count": rows[0]["edges"],
                "median_node_build_wall_ns": median(rows, "node_build_wall_ns"),
                "median_edge_build_wall_ns": median(rows, "edge_build_wall_ns"),
                "median_closure_wall_ns": median(rows, "closure_wall_ns"),
                "median_validation_wall_ns": median(rows, "validation_wall_ns"),
                "median_peak_rss_bytes": median(rows, "peak_rss_bytes"),
            }
            cells.append(row)
    star100k = next(x for x in cells if x["n"] == 100_000 and x["topology"] == "star")
    star1m = next(x for x in cells if x["n"] == 1_000_000 and x["topology"] == "star")
    balanced100k = next(x for x in cells if x["n"] == 100_000 and x["topology"] == "balanced")
    balanced1m = next(x for x in cells if x["n"] == 1_000_000 and x["topology"] == "balanced")
    ratios = {
        "star_edge_build_growth_100k_to_1m": star1m["median_edge_build_wall_ns"] / star100k["median_edge_build_wall_ns"],
        "balanced_edge_build_growth_100k_to_1m": balanced1m["median_edge_build_wall_ns"] / balanced100k["median_edge_build_wall_ns"],
        "star_edge_build_to_closure_at_1m": star1m["median_edge_build_wall_ns"] / star1m["median_closure_wall_ns"],
        "balanced_edge_build_to_closure_at_1m": balanced1m["median_edge_build_wall_ns"] / balanced1m["median_closure_wall_ns"],
    }
    checks["all_measured_phases_positive"] = all(
        row[key] > 0 for row in cells for key in (
            "median_node_build_wall_ns", "median_edge_build_wall_ns",
            "median_closure_wall_ns", "median_validation_wall_ns"))
    checks["star_edge_build_grows_superlinearly_in_measured_decade"] = ratios["star_edge_build_growth_100k_to_1m"] > 10
    checks["star_edge_build_dominates_closure_at_1m"] = ratios["star_edge_build_to_closure_at_1m"] > 100
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-interacting-tree-construction-cost-v1-posthoc",
        "raw_path": str(RAW.relative_to(ROOT)),
        "raw_sha256": sha(RAW),
        "lock_path": str(LOCK.relative_to(ROOT)),
        "lock_sha256": sha(LOCK),
        "base_analysis_sha256": sha(BASE_ANALYSIS),
        "graph_source_path": str(GRAPH_SOURCE.relative_to(ROOT)),
        "graph_source_sha256": source_hash,
        "graph_source_locked_sha256": source_hash_locked,
        "graph_source_matches_original_lock_now": source_hash == source_hash_locked,
        "cells": cells,
        "derived_ratios": ratios,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "claim_boundary": (
        "Post-hoc decomposition of phase timings already captured in the source-locked v1 run. "
        "The star edge-build curve is consistent with the original source's linear scan of a "
        "source/type adjacency bucket during duplicate detection; the raw lock preserves that "
        "source hash, and the current source has since changed. Timing alone did not prove the "
        "mechanism; the later indexed replay is the causal intervention. This is not a 10M result; the separate uninstrumented 10M star pilot was "
            "interrupted before it emitted a row and is excluded."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": sum(checks.values()), "checks_total": len(checks),
                      "all_checks_pass": result["all_checks_pass"], "output": str(OUT.relative_to(ROOT)),
                      "ratios": ratios}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
