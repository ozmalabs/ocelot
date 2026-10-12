#!/usr/bin/env python3
"""Independent validation and cell summaries for the ReachableFrom cache panel."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_reachable_from_cache_v1_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_reachable_from_cache_v1_analysis_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/reachable_from_cache_v1_lock_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    cells = []
    for n in (32, 128, 512):
        for readers in (1, 16, 64):
            rows = [r for r in runs if r["n"] == n and r["readers"] == readers]
            off = [r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            on = [r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            ratios = [a / b if b else None for a, b in zip(off, on)]
            off_wall = [r["arms"]["false"]["wall_ns"] for r in rows]
            on_wall = [r["arms"]["true"]["wall_ns"] for r in rows]
            cells.append({"n": n, "readers": readers, "replicates": len(rows),
                "off_work": off, "on_work": on, "work_ratio": ratios,
                "median_wall_off_ns": int(statistics.median(off_wall)) if rows else None,
                "median_wall_on_ns": int(statistics.median(on_wall)) if rows else None})
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / p) == v.get("sha256") for p, v in manifest.get("explicit_inputs", {}).items())
    checks = {
        "expected_factorial_and_replicates": len(runs) == 27 and len(cells) == 9 and all(c["replicates"] == 3 for c in cells),
        "unique_fresh_processes": len({r["pid"] for r in runs}) == 27,
        "source_lock_pre_post_and_worker_stability": raw["locked_inputs"] == raw["post_run_inputs"] and all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs) and sha(LOCK) != "",
        "all_runner_gates_pass": raw["all_checks_pass"] and all(raw["checks"].values()),
        "exact_operation_count_formula": all(c["off_work"] == [c["n"] ** 2 * c["readers"]] * 3 and c["on_work"] == [c["n"]] * 3 and c["work_ratio"] == [c["n"] * c["readers"]] * 3 for c in cells),
        "mutation_control_reaches_changed_semantics": all(x["before_open"] == 0 and x["after_open"] == 8 and x["after"]["status"] == "fixed_point" and x["units"].get("term_unit:ReachableFrom", 0) > 0 for x in raw["mutation_control"].values()),
        "manifest_and_source_hashes_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok,
        "parent_log_hash_valid": log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "cell_summaries": cells,
        "mutation_work": {k: v["units"].get("term_unit:ReachableFrom", 0) for k, v in raw["mutation_control"].items()},
        "claim_boundary": raw["claim_boundary"], "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
