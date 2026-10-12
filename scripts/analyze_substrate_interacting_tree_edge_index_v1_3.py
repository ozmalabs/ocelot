#!/usr/bin/env python3
"""Independent analysis of the locked 10M adaptive-edge-index panel."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_3_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/interacting_tree_edge_index_v1_3_lock_20260928.json"
BASE_RAW = ROOT / "evaluation/reports/substrate_interacting_tree_closure_scale_v1_20260928.json"
INDEX_RAW = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_20260928.json"
INDEX_ANALYSIS = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_analysis_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_3_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def med(rows: list[dict], key: str) -> int:
    return int(statistics.median(row[key] for row in rows))


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    base = json.loads(BASE_RAW.read_text())
    index_raw = json.loads(INDEX_RAW.read_text())
    index_analysis = json.loads(INDEX_ANALYSIS.read_text())
    rows = raw["runs"]
    old_star_1m = [r for r in base["runs"] if r["n"] == 1_000_000 and r["topology"] == "star" and not r["audit"]]
    new_star_1m = [r for r in index_raw["runs"] if r["n"] == 1_000_000 and r["topology"] == "star"]
    cells = {
        "n": 10_000_000,
        "topology": "star",
        "replicates": len(rows),
        "median_node_build_wall_ns": med(rows, "node_build_wall_ns"),
        "median_edge_build_wall_ns": med(rows, "edge_build_wall_ns"),
        "median_closure_cpu_ns": med(rows, "closure_cpu_ns"),
        "median_closure_wall_ns": med(rows, "closure_wall_ns"),
        "median_validation_wall_ns": med(rows, "validation_wall_ns"),
        "median_live_rss_after_closure_bytes": med(rows, "rss_after_closure_bytes"),
        "median_peak_rss_bytes": med(rows, "peak_rss_bytes"),
        "samples": [r["samples"] for r in rows],
        "ratios_to_indexed_1m_star": {
            key: med(rows, key) / med(new_star_1m, key)
            for key in ("node_build_wall_ns", "edge_build_wall_ns", "closure_wall_ns")
        },
        "indexed_edge_build_speedup_over_preindex_1m_star":
            med(old_star_1m, "edge_build_wall_ns") / med(rows, "edge_build_wall_ns"),
    }
    checks = {
        "runner_gates_pass": raw.get("all_checks_pass") is True and all(raw["checks"].values()),
        "stable_pre_post_parent_lock": raw["locked_inputs"] == raw["post_run_inputs"] == lock,
        "v1_2_index_replay_analysis_passed": index_analysis.get("all_checks_pass") is True,
        "three_workers": len(rows) == 3,
        "unique_worker_pids": len({r["pid"] for r in rows}) == 3,
        "each_worker_source_snapshot_stable": all(r["before"] == r["after"] for r in rows),
        "all_worker_source_paths_match_parent": all(
            r["before"].get("commit") == lock.get("commit")
            and r["before"].get("native_sha256") == lock.get("native_sha256")
            and all(lock["files"].get(name) == digest for name, digest in r["before"].get("files", {}).items())
            for r in rows),
        "prior_indexed_and_preindex_baselines_have_three_workers": len(new_star_1m) == 3 and len(old_star_1m) == 3,
        "exact_terminal_graph_and_attributes": all(
            r["nodes"] == 10_000_000 and r["edges"] == 19_999_998
            and r["report"]["status"] == "fixed_point" and r["report"]["budget_overshoot"] == 0
            and r["pending_count"] == r["ready_count"] == 0 and r["active_count"] == 10_000_000
            and len(r["samples"]) == 3 and all(
                s["status"] == "active" and s["ordinal"] == s["id"]
                and s["bucket"] == s["expected_bucket"] and s["depth"] == s["expected_depth"]
                and s["parents"] == s["expected_parents"] for s in r["samples"])
            for r in rows),
        "all_phase_timings_positive": all(all(r[k] > 0 for k in (
            "node_build_wall_ns", "edge_build_wall_ns", "closure_wall_ns", "validation_wall_ns")) for r in rows),
        "raw_run_manifest_success": raw["run_manifest"].get("exit_status") == 0,
    }
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-interacting-tree-edge-index-v1-3-independent-analysis",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK), "preindex_baseline_sha256": sha(BASE_RAW),
        "indexed_1m_baseline_sha256": sha(INDEX_RAW), "indexed_1m_analysis_sha256": sha(INDEX_ANALYSIS),
        "summary": cells, "checks": checks, "all_checks_pass": all(checks.values()),
        "claim_boundary": "This verifies one 10M attributed high-fanout star and fixed two-rule propagation workload on one host. It does not establish arbitrary topology/rule-family complexity or natural task prevalence.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": sum(checks.values()), "checks_total": len(checks),
                      "all_checks_pass": result["all_checks_pass"], "summary": cells,
                      "output": str(OUT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
