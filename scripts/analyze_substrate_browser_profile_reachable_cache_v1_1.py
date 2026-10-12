#!/usr/bin/env python3
"""Independent analysis of loaded-profile ReachableFrom cache telemetry."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

from substrate_browser_profile_reachable_cache_v1_1 import LOCK, RAW, fingerprint
from substrate_browser_profile_reachable_cache_v1 import profile_seed_files

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_browser_profile_reachable_cache_v1_1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    cells = []
    for n in (2, 8, 32, 128):
        for branches in (1, 4):
            rows = [r for r in runs if r["n"] == n and r["branches"] == branches]
            on_stats = [r["arms"]["true"]["cache_stats"] for r in rows]
            off_work = [r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            on_work = [r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            cells.append({"n_affordances": n, "top_level_wrappers": branches, "replicates": len(rows),
                "reachable_work_off": off_work, "reachable_work_on": on_work,
                "median_hits": int(statistics.median(s["hits"] for s in on_stats)) if rows else None,
                "median_misses": int(statistics.median(s["misses"] for s in on_stats)) if rows else None,
                "median_peak_entries": int(statistics.median(s["peak_entries"] for s in on_stats)) if rows else None,
                "median_peak_payload_bytes": int(statistics.median(s["peak_estimated_payload_bytes"] for s in on_stats)) if rows else None,
                "median_wall_ns_off": int(statistics.median(r["arms"]["false"]["wall_ns"] for r in rows)) if rows else None,
                "median_wall_ns_on": int(statistics.median(r["arms"]["true"]["wall_ns"] for r in rows)) if rows else None})
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / name) == v.get("sha256") for name, v in manifest.get("explicit_inputs", {}).items())
    expected_rule_names = {rule["name"] for rel in profile_seed_files() for rule in json.loads((ROOT / rel).read_text()).get("rules", [])}
    checks = {
        "full_factorial_and_unique_workers": len(runs) == 24 and len(cells) == 8 and all(c["replicates"] == 3 for c in cells) and len({r["pid"] for r in runs}) == 24,
        "counterbalanced_arms": all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in runs),
        "lock_matches_current_sources_and_build": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs),
        "profile_rules_match_seed_manifests": all(set(r["arms"][m]["loaded_rule_names"]) == expected_rule_names for r in runs for m in ("false", "true")),
        "semantic_and_trace_parity": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["terminal_graph"] == r["arms"]["true"]["terminal_graph"] and r["arms"]["false"]["trace"] == r["arms"]["true"]["trace"] and r["arms"]["false"]["trace_dropped"] == r["arms"]["true"]["trace_dropped"] == 0 and r["arms"]["false"]["tick_steps"] == r["arms"]["true"]["tick_steps"] and r["arms"]["false"]["terminal_tick_steps"] == r["arms"]["true"]["terminal_tick_steps"] == 0 for r in runs),
        "expected_mirror_oracle": all(r["arms"][m]["mirror_count"] == r["n"] for r in runs for m in ("false", "true")),
        "matcher_counters_equal": all(all(r["arms"]["false"]["units"].get(k, 0) == r["arms"]["true"]["units"].get(k, 0) for k in ("cand_tested", "where_evals", "rule_enumerations")) for r in runs),
        "cache_counters_cover_reach_terms": all(r["arms"]["true"]["cache_stats"]["hits"] + r["arms"]["true"]["cache_stats"]["misses"] == r["arms"]["true"]["units"].get("term_eval:ReachableFrom", 0) for r in runs),
        "off_stats_zero_and_on_payload_nonzero": all(not any(r["arms"]["false"]["cache_stats"].get(k, 0) for k in ("hits", "misses", "entries", "peak_entries", "estimated_payload_bytes", "peak_estimated_payload_bytes")) for r in runs) and all(r["arms"]["true"]["cache_stats"]["hits"] > 0 and r["arms"]["true"]["cache_stats"]["misses"] > 0 and r["arms"]["true"]["cache_stats"]["peak_entries"] > 0 and r["arms"]["true"]["cache_stats"]["peak_estimated_payload_bytes"] > 0 for r in runs),
        "current_payload_and_entries_within_peak": all(r["arms"]["true"]["cache_stats"]["estimated_payload_bytes"] <= r["arms"]["true"]["cache_stats"]["peak_estimated_payload_bytes"] and r["arms"]["true"]["cache_stats"]["entries"] <= r["arms"]["true"]["cache_stats"]["peak_entries"] for r in runs),
        "traversal_work_not_increased": all(r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) <= r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) for r in runs),
        "manifest_and_parent_log_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and manifest.get("engine", {}).get("build_is_stale") is False and explicit_ok and log_path.is_file() and sha(log_path) == log.get("sha256") and log_path.stat().st_size == log.get("bytes", -1),
    }
    result = {"schema_version": 1, "run_id": raw["run_id"], "checks": checks,
        "all_checks_pass": all(checks.values()), "cells": cells, "claim_boundary": raw["claim_boundary"],
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
