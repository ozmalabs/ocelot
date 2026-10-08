#!/usr/bin/env python3
"""Independent checks for the adaptive high-degree edge index replay."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/interacting_tree_edge_index_v1_2_lock_20260928.json"
BASE_RAW = ROOT / "evaluation/reports/substrate_interacting_tree_closure_scale_v1_20260928.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/substrate_interacting_tree_closure_scale_v1_analysis_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(rows: list[dict], key: str) -> int:
    return int(statistics.median(row[key] for row in rows))


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    base = json.loads(BASE_RAW.read_text())
    base_analysis = json.loads(BASE_ANALYSIS.read_text())
    checks = {
        "runner_gates_pass": raw.get("all_checks_pass") is True and all(raw["checks"].values()),
        "pre_post_lock_matches": raw.get("locked_inputs") == raw.get("post_run_inputs") == lock,
        "base_capture_passed_original_gates": base.get("all_checks_pass") is True,
        "base_independent_analysis_passed": base_analysis.get("all_checks_pass") is True,
        "semantic_transition_controls_all_pass": all(v is True for v in raw["semantic_probe"].values()
                                                       if isinstance(v, bool)),
        "final_semantic_probe_edge_count": raw["semantic_probe"].get("final_edge_count") == 17,
        "raw_and_analysis_source_locks_stable_in_workers": all(
            r.get("before") == r.get("after")
            and r["before"].get("commit") == lock.get("commit")
            and r["before"].get("native_sha256") == lock.get("native_sha256")
            and all(lock.get("files", {}).get(name) == digest
                    for name, digest in r["before"].get("files", {}).items())
            for r in raw["runs"]),
        "unique_worker_pids": len({r["pid"] for r in raw["runs"]}) == 12,
        "all_native_builds_fresh": all(not r["before"].get("native_build_stale") for r in raw["runs"]),
    }
    cells = []
    for n in (100_000, 1_000_000):
        for topology in ("balanced", "star"):
            new = [r for r in raw["runs"] if r["n"] == n and r["topology"] == topology]
            old = [r for r in base["runs"] if r["n"] == n and r["topology"] == topology and not r["audit"]]
            checks[f"three_new_replicates_{n}_{topology}"] = len(new) == 3
            checks[f"three_baseline_replicates_{n}_{topology}"] = len(old) == 3
            if len(new) != 3 or len(old) != 3:
                continue
            row = {
                "n": n,
                "topology": topology,
                "replicates_per_version": 3,
                "old_median_edge_build_wall_ns": median(old, "edge_build_wall_ns"),
                "new_median_edge_build_wall_ns": median(new, "edge_build_wall_ns"),
                "old_median_closure_wall_ns": median(old, "closure_wall_ns"),
                "new_median_closure_wall_ns": median(new, "closure_wall_ns"),
                "old_median_peak_rss_bytes": median(old, "peak_rss_bytes"),
                "new_median_peak_rss_bytes": median(new, "peak_rss_bytes"),
                "edge_build_speedup": median(old, "edge_build_wall_ns") / median(new, "edge_build_wall_ns"),
                "all_new_terminal_oracles_pass": all(
                    r["report"]["status"] == "fixed_point" and r["report"]["budget_overshoot"] == 0
                    and r["pending_count"] == r["ready_count"] == 0 and r["active_count"] == n for r in new),
                "all_new_graph_counts_pass": all(r["nodes"] == n and r["edges"] == 2 * (n - 1) for r in new),
                "all_new_sample_oracles_pass": all(
                    len(r["samples"]) == 3 and all(
                        s["status"] == "active" and s["ordinal"] == s["id"]
                        and s["bucket"] == s["expected_bucket"] and s["depth"] == s["expected_depth"]
                        and s["parents"] == s["expected_parents"] for s in r["samples"]) for r in new),
            }
            cells.append(row)
            checks[f"terminal_oracle_{n}_{topology}"] = row["all_new_terminal_oracles_pass"]
            checks[f"graph_count_oracle_{n}_{topology}"] = row["all_new_graph_counts_pass"]
            checks[f"sample_oracle_{n}_{topology}"] = row["all_new_sample_oracles_pass"]
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-interacting-tree-edge-index-v1-2-independent-analysis",
        "raw_path": str(RAW.relative_to(ROOT)),
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "baseline_raw_sha256": sha(BASE_RAW),
        "baseline_analysis_sha256": sha(BASE_ANALYSIS),
        "semantic_probe": raw["semantic_probe"],
        "cells": cells,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "claim_boundary": (
            "The current adaptive target index is compared with the prior locked implementation on two "
            "topologies and two sizes, three fresh workers per cell. Semantics and closure are gated. "
            "Timing and RSS ratios are descriptive and do not prove an asymptotic bound or broad workload benefit."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": sum(checks.values()), "checks_total": len(checks),
                      "all_checks_pass": result["all_checks_pass"], "output": str(OUT.relative_to(ROOT)),
                      "cells": cells}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
