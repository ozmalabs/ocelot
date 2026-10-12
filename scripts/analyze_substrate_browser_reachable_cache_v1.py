#!/usr/bin/env python3
"""Independent checks and work summaries for the browser-seed cache panel."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from substrate_browser_reachable_cache_v1 import LOCK, RAW, fingerprint

OUT = ROOT / "evaluation/reports/substrate_browser_reachable_cache_v1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    cells = []
    for n in (2, 8, 32, 128):
        for branches in (1, 4):
            rows = [r for r in runs if r["n"] == n and r["branches"] == branches]
            off = [r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            on = [r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            off_wall = [r["arms"]["false"]["wall_ns"] for r in rows]
            on_wall = [r["arms"]["true"]["wall_ns"] for r in rows]
            cells.append({"n_affordances": n, "top_level_wrappers": branches, "replicates": len(rows),
                "reachable_work_off": off, "reachable_work_on": on,
                "work_reduction": [a / b if b else None for a, b in zip(off, on)],
                "median_wall_off_ns": int(statistics.median(off_wall)) if rows else None,
                "median_wall_on_ns": int(statistics.median(on_wall)) if rows else None,
                "median_wall_ratio_off_over_on": statistics.median(a / b for a, b in zip(off_wall, on_wall) if b) if rows else None})
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / p) == v.get("sha256") for p, v in manifest.get("explicit_inputs", {}).items())
    checks = {
        "full_factorial_three_replicates": len(runs) == 24 and len(cells) == 8 and all(c["replicates"] == 3 for c in cells),
        "unique_workers_and_arm_orders": len({r["pid"] for r in runs}) == 24 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in runs),
        "current_lock_matches_run": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs),
        "runner_gates_all_pass": raw["all_checks_pass"] and all(raw["checks"].values()),
        "mirror_edge_oracle_all_runs": all(r["arms"][k]["mirror_count"] == r["n"] for r in runs for k in ("false", "true")),
        "nonvacuous_work_and_effective_reuse": all(c["reachable_work_off"] and c["reachable_work_on"] and all(on <= off for off, on in zip(c["reachable_work_off"], c["reachable_work_on"])) for c in cells) and any(any(on < off for off, on in zip(c["reachable_work_off"], c["reachable_work_on"])) for c in cells),
        "manifest_build_and_source_hashes": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok,
        "parent_log_hash": log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "cells": cells,
        "claim_boundary": raw["claim_boundary"], "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
