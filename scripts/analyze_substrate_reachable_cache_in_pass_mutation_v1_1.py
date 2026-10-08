#!/usr/bin/env python3
"""Independent verifier for the in-pass cache mutation counterexample."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from substrate_reachable_cache_in_pass_mutation_v1_1 import LOCK, RAW, fingerprint

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_reachable_cache_in_pass_mutation_v1_1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    rows = raw["runs"]
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / name) == v.get("sha256")
                      for name, v in manifest.get("explicit_inputs", {}).items())
    checks = {
        "five_independent_counterbalanced_workers": len(rows) == 5 and len({r["pid"] for r in rows}) == 5 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "source_lock_and_provenance_reconstruct": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in rows),
        "read_write_dependency_declared": all("edge:path" in r["arms"]["true"]["rule_access_sets"][2][3] and "edge:path" in r["arms"]["true"]["rule_access_sets"][1][5] for r in rows),
        "both_modes_reach_expected_fixed_point": all(r["arms"]["false"]["detected"] and r["arms"]["true"]["detected"] and r["arms"]["false"]["steps"] == r["arms"]["true"]["steps"] == 2 for r in rows),
        "final_graphs_equal": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] for r in rows),
        "manifest_and_log_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok and log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "replicates": len(rows),
        "cache_off_progress_steps": [r["arms"]["false"]["steps"] for r in rows],
        "cache_on_progress_steps": [r["arms"]["true"]["steps"] for r in rows],
        "claim_boundary": raw["claim_boundary"], "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
