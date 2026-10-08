#!/usr/bin/env python3
"""Independent validator and summary for the loaded-profile cache panel."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

from substrate_browser_profile_reachable_cache_v1 import LOCK, RAW, fingerprint, profile_seed_files

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_browser_profile_reachable_cache_v1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    rows = raw["runs"]
    cells = []
    for n in (2, 8, 32, 128):
        for branches in (1, 4):
            cell = [r for r in rows if r["n"] == n and r["branches"] == branches]
            off = [r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) for r in cell]
            on = [r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) for r in cell]
            off_wall = [r["arms"]["false"]["wall_ns"] for r in cell]
            on_wall = [r["arms"]["true"]["wall_ns"] for r in cell]
            cells.append({"n_affordances": n, "top_level_wrappers": branches, "replicates": len(cell),
                "work_off": off, "work_on": on,
                "work_reduction": [a / b if b else None for a, b in zip(off, on)],
                "median_tick_wall_off_ns": int(statistics.median(off_wall)) if cell else None,
                "median_tick_wall_on_ns": int(statistics.median(on_wall)) if cell else None,
                "median_wall_ratio_off_over_on": statistics.median(a / b for a, b in zip(off_wall, on_wall) if b) if cell else None})
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / name) == v.get("sha256") for name, v in manifest.get("explicit_inputs", {}).items())
    expected_rule_names = {rule["name"] for rel in profile_seed_files() for rule in json.loads((ROOT / rel).read_text()).get("rules", [])}
    checks = {
        "complete_factorial_and_replicates": len(rows) == 24 and len(cells) == 8 and all(c["replicates"] == 3 for c in cells),
        "fresh_processes_and_arm_order": len({r["pid"] for r in rows}) == 24 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "source_and_native_lock_current": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in rows),
        "loaded_profile_rules_match_seed_manifests": all(set(r["arms"][mode]["loaded_rule_names"]) == expected_rule_names for r in rows for mode in ("false", "true")),
        "runner_gates_all_pass": raw["all_checks_pass"] and all(raw["checks"].values()),
        "exact_graph_and_progress_oracle": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["terminal_graph"] == r["arms"]["true"]["terminal_graph"] and r["arms"]["false"]["tick_steps"] == r["arms"]["true"]["tick_steps"] and r["arms"]["false"]["terminal_tick_steps"] == r["arms"]["true"]["terminal_tick_steps"] == 0 for r in rows),
        "mirror_edge_oracle": all(r["arms"][mode]["mirror_count"] == r["n"] for r in rows for mode in ("false", "true")),
        "access_trace_exact_and_complete": all(r["arms"]["false"]["trace"] == r["arms"]["true"]["trace"] and r["arms"]["false"]["trace_dropped"] == r["arms"]["true"]["trace_dropped"] == 0 for r in rows),
        "matcher_counters_equal": all(all(r["arms"]["false"]["units"].get(k, 0) == r["arms"]["true"]["units"].get(k, 0) for k in ("cand_tested", "where_evals", "rule_enumerations")) for r in rows),
        "work_positive_and_not_increased": all(c["work_off"] and c["work_on"] and all(on <= off for off, on in zip(c["work_off"], c["work_on"])) for c in cells),
        "manifest_build_and_explicit_hashes": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok,
        "parent_log_hash_valid": log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "cells": cells,
        "profile_rule_names": sorted(expected_rule_names), "claim_boundary": raw["claim_boundary"],
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
