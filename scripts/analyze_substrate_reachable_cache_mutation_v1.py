#!/usr/bin/env python3
"""Independent mutation-case checks for the ReachableFrom cache panel."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

from substrate_reachable_cache_mutation_v1 import CASES, LOCK, RAW, fingerprint

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_reachable_cache_mutation_v1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    cells = []
    for case in CASES:
        rows = [r for r in runs if r["case"] == case]
        arms = [r["arms"]["true"] for r in rows]
        cells.append({"case": case, "replicates": len(rows),
            "expected_reachable": arms[0]["expected_reachable"] if arms else None,
            "post_mutation_misses": [a["after_stats"].get("misses", 0) for a in arms],
            "post_mutation_hits": [a["after_stats"].get("hits", 0) for a in arms],
            "result_values": [a["after_stats"].get("result_values", 0) for a in arms],
            "mirror_counts": [a["mirror_count"] for a in arms],
            "median_misses": int(statistics.median(a["after_stats"].get("misses", 0) for a in arms)) if arms else None})
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / name) == v.get("sha256")
                      for name, v in manifest.get("explicit_inputs", {}).items())
    expected_rules = {"browser_mirror_has_affordance_reachable", "browser_drop_has_affordance_stale"}
    checks = {
        "complete_case_matrix": len(runs) == 30 and len(cells) == 10 and all(c["replicates"] == 3 for c in cells),
        "unique_workers_and_counterbalancing": len({r["pid"] for r in runs}) == 30 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in runs),
        "source_lock_and_build_current": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs),
        "all_arms_load_expected_rules": all(set(a["loaded_rule_names"]) == expected_rules for r in runs for a in r["arms"].values()),
        "live_cache_primed": all(a["before_stats"]["entries"] == 1 and a["before_stats"]["result_values"] == 4 and a["prime_steps"] == 0 for r in runs for a in r["arms"].values() if a["cache"]),
        "fresh_miss_and_expected_result": all(a["after_stats"]["misses"] > 0 and a["after_stats"]["entries"] == 1 and a["after_stats"]["result_values"] == a["expected_reachable"] for r in runs for a in r["arms"].values() if a["cache"]),
        "cache_disabled_stats_remain_zero": all(not any(a["after_stats"].get(k, 0) for k in ("hits", "misses", "entries", "result_values", "footprint_nodes", "estimated_payload_bytes")) for r in runs for a in r["arms"].values() if not a["cache"]),
        "semantic_graph_and_progress_parity": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["steps"] == r["arms"]["true"]["steps"] and r["arms"]["false"]["mirror_count"] == r["arms"]["true"]["mirror_count"] for r in runs),
        "manifest_source_and_parent_capture_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok and log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "cells": cells,
        "claim_boundary": raw["claim_boundary"], "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
