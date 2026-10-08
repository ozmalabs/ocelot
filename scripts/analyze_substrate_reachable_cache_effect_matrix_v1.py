#!/usr/bin/env python3
"""Independent analysis of internal ReachableFrom mutation effects."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from substrate_reachable_cache_effect_matrix_v1 import CASES, LOCK, RAW, fingerprint

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_reachable_cache_effect_matrix_v1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    rows = raw["runs"]
    summaries = []
    for case in CASES:
        group = [r for r in rows if r["case"] == case]
        summaries.append({"case": case, "replicates": len(group),
            "cache_on_detected": [r["arms"]["true"]["detected"] for r in group],
            "cache_off_detected": [r["arms"]["false"]["detected"] for r in group],
            "cache_on_steps": [r["arms"]["true"]["steps"] for r in group],
            "cache_off_steps": [r["arms"]["false"]["steps"] for r in group],
            "post_effect_cache_misses": [r["arms"]["true"]["cache_stats"].get("misses", 0) for r in group],
            "primed_result_values": [r["arms"]["true"]["primed_stats"].get("result_values", 0) for r in group]})
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / name) == v.get("sha256")
                      for name, v in manifest.get("explicit_inputs", {}).items())
    checks = {
        "complete_40_worker_matrix": len(rows) == 40 and len(summaries) == 8 and all(s["replicates"] == 5 for s in summaries),
        "unique_workers_counterbalanced": len({r["pid"] for r in rows}) == 40 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "source_lock_and_native_build_current": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in rows),
        "all_cache_arms_reach_expected_result": all(a["detected"] and a["expected_detected"] for r in rows for a in r["arms"].values()),
        "paired_graph_and_progress_parity": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["steps"] == r["arms"]["true"]["steps"] for r in rows),
        "live_memo_precedes_mutator": all(a["prime_steps"] == 0 and a["primed_stats"]["entries"] == 1 and a["primed_stats"]["result_values"] == (2 if r["case"] in ("del_node", "replace_value") else 1) for r in rows for a in r["arms"].values() if a["cache"]),
        "post_effect_cache_recomputed": all(a["cache_stats"]["misses"] >= 1 for r in rows for a in r["arms"].values() if a["cache"]),
        "off_cache_remains_empty": all(not any(a["cache_stats"].get(k, 0) for k in ("hits", "misses", "entries", "result_values", "footprint_nodes")) for r in rows for a in r["arms"].values() if not a["cache"]),
        "expected_read_dependency_exposed": all(len(a["rule_access_sets"]) == 3 and "edge:path" in a["rule_access_sets"][2][3] for r in rows for a in r["arms"].values()),
        "manifest_and_parent_log_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok and log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "cases": summaries,
        "claim_boundary": raw["claim_boundary"], "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
