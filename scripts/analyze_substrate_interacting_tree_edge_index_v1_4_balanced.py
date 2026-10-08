#!/usr/bin/env python3
"""Independent analysis of the 10M balanced-tree closure control."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_4_1_balanced_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/interacting_tree_edge_index_v1_4_1_balanced_lock_20260928.json"
INDEX_RAW = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_20260928.json"
INDEX_ANALYSIS = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_analysis_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_4_1_balanced_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def med(rows: list[dict], key: str) -> int:
    return int(statistics.median(row[key] for row in rows))


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    index_raw = json.loads(INDEX_RAW.read_text())
    index_analysis = json.loads(INDEX_ANALYSIS.read_text())
    rows = raw["runs"]
    base = [r for r in index_raw["runs"] if r["n"] == 1_000_000 and r["topology"] == "balanced"]
    summary = {
        "n": 10_000_000,
        "topology": "balanced",
        "replicates": len(rows),
        "median_node_build_wall_ns": med(rows, "node_build_wall_ns"),
        "median_edge_build_wall_ns": med(rows, "edge_build_wall_ns"),
        "median_closure_cpu_ns": med(rows, "closure_cpu_ns"),
        "median_closure_wall_ns": med(rows, "closure_wall_ns"),
        "median_validation_wall_ns": med(rows, "validation_wall_ns"),
        "median_live_rss_after_closure_bytes": med(rows, "rss_after_closure_bytes"),
        "median_peak_rss_bytes": med(rows, "peak_rss_bytes"),
        "ratios_to_indexed_1m_balanced": {
            key: med(rows, key) / med(base, key)
            for key in ("node_build_wall_ns", "edge_build_wall_ns", "closure_wall_ns")
        },
    }
    checks = {
        "runner_gates_pass": raw.get("all_checks_pass") is True and all(raw["checks"].values()),
        "stable_source_lock": raw["locked_inputs"] == raw["post_run_inputs"] == lock,
        "index_replay_analysis_passed": index_analysis.get("all_checks_pass") is True,
        "three_workers_and_pids": len(rows) == 3 and len({r["pid"] for r in rows}) == 3,
        "worker_source_projections_match_parent": all(
            r["before"] == r["after"] and r["before"].get("commit") == lock.get("commit")
            and r["before"].get("native_sha256") == lock.get("native_sha256")
            and all(lock["files"].get(name) == digest for name, digest in r["before"].get("files", {}).items())
            for r in rows),
        "all_exact_graph_and_fixed_point_oracles": all(
            r["nodes"] == 10_000_000 and r["edges"] == 19_999_998
            and r["report"]["status"] == "fixed_point" and r["report"]["budget_overshoot"] == 0
            and r["active_count"] == 10_000_000 and r["pending_count"] == r["ready_count"] == 0
            and len(r["samples"]) == 3 and all(
                s["status"] == "active" and s["ordinal"] == s["id"]
                and s["bucket"] == s["expected_bucket"] and s["depth"] == s["expected_depth"]
                and s["parents"] == s["expected_parents"] for s in r["samples"])
            for r in rows),
        "baseline_has_three_workers": len(base) == 3,
        "all_phase_timings_positive": all(all(r[k] > 0 for k in (
            "node_build_wall_ns", "edge_build_wall_ns", "closure_wall_ns", "validation_wall_ns")) for r in rows),
        "raw_manifest_success": raw["run_manifest"].get("exit_status") == 0,
    }
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-interacting-tree-edge-index-v1-4-1-balanced-independent-analysis",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK), "indexed_1m_raw_sha256": sha(INDEX_RAW),
        "indexed_1m_analysis_sha256": sha(INDEX_ANALYSIS), "summary": summary,
        "checks": checks, "all_checks_pass": all(checks.values()),
        "claim_boundary": "Three-worker 10M balanced-tree construction and closure for one fixed monotone rule pair on one host; no general complexity or natural-task locality claim.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": sum(checks.values()), "checks_total": len(checks),
                      "all_checks_pass": result["all_checks_pass"], "summary": summary,
                      "output": str(OUT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
