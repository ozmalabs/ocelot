#!/usr/bin/env python3
"""Independent checkpoint and provenance checks for the browser mirror replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from substrate_browser_affordance_truth_maintenance_v1 import CHECKPOINTS, EXPECTED, LOCK, RAW, fingerprint

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/browser_affordance_truth_maintenance_v1_analysis_20260928.json"


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
        "source_lock_and_native_provenance_reconstruct": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in rows),
        "all_cache_modes_follow_exact_expected_mirror_sequence": all([cp["mirror_count"] for cp in r["arms"][mode]["checkpoints"]] == [EXPECTED[k] for k in CHECKPOINTS] for r in rows for mode in ("false", "true")),
        "exact_graph_and_progress_parity_at_each_checkpoint": all(r["arms"]["false"]["checkpoints"][i]["graph"] == r["arms"]["true"]["checkpoints"][i]["graph"] and r["arms"]["false"]["checkpoints"][i]["steps"] == r["arms"]["true"]["checkpoints"][i]["steps"] for r in rows for i in range(len(CHECKPOINTS))),
        "only_expected_seed_rules_loaded": all(set(r["arms"][mode]["loaded_rule_names"]) == {"browser_mirror_has_affordance_reachable", "browser_drop_has_affordance_stale"} for r in rows for mode in ("false", "true")),
        "cache_enabled_and_disabled_controls": all(any(cp["cache_stats"].get("hits",0) or cp["cache_stats"].get("misses",0) for cp in r["arms"]["true"]["checkpoints"]) and not any(cp["cache_stats"].get(k,0) for cp in r["arms"]["false"]["checkpoints"] for k in ("hits","misses","entries","result_values")) for r in rows),
        "manifest_and_parent_log_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok and log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "checkpoints": list(CHECKPOINTS),
        "expected_mirror_counts": EXPECTED, "claim_boundary": raw["claim_boundary"],
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
