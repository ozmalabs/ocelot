#!/usr/bin/env python3
"""Independent analysis of loaded-profile ReachableFrom cache telemetry."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

from substrate_browser_profile_reachable_cache_v1_3 import LOCK, RAW, fingerprint, arm
from substrate_browser_profile_reachable_cache_v1 import profile_seed_files

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_browser_profile_reachable_cache_v1_3_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    cells = []
    for n in (2, 8, 32, 128):
        for branches in (1, 4):
            rows = [r for r in runs if r["n"] == n and r["branches"] == branches]
            on_stats = [arm(r, True, True)["cache_stats"] for r in rows]
            off_work = [arm(r, False, True)["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            on_work = [arm(r, True, True)["units"].get("term_unit:ReachableFrom", 0) for r in rows]
            plain_off = [arm(r, False, False)["wall_ns"] for r in rows]
            plain_on = [arm(r, True, False)["wall_ns"] for r in rows]
            cells.append({"n_affordances": n, "top_level_wrappers": branches, "replicates": len(rows),
                "reachable_work_off": off_work, "reachable_work_on": on_work,
                "median_hits": int(statistics.median(s["hits"] for s in on_stats)) if rows else None,
                "median_misses": int(statistics.median(s["misses"] for s in on_stats)) if rows else None,
                "median_peak_entries": int(statistics.median(s["peak_entries"] for s in on_stats)) if rows else None,
                "median_peak_payload_bytes": int(statistics.median(s["peak_estimated_payload_bytes"] for s in on_stats)) if rows else None,
                "median_audited_wall_off_ns": int(statistics.median(arm(r, False, True)["wall_ns"] for r in rows)) if rows else None,
                "median_audited_wall_on_ns": int(statistics.median(arm(r, True, True)["wall_ns"] for r in rows)) if rows else None,
                "median_quiet_wall_off_ns": int(statistics.median(plain_off)) if rows else None,
                "median_quiet_wall_on_ns": int(statistics.median(plain_on)) if rows else None,
                "median_quiet_wall_ratio_off_over_on": statistics.median(a / b for a, b in zip(plain_off, plain_on) if b) if rows else None})
    manifest = raw["run_manifest"]
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    explicit_ok = all(v.get("exists") and sha(ROOT / name) == v.get("sha256") for name, v in manifest.get("explicit_inputs", {}).items())
    expected_rule_names = {rule["name"] for rel in profile_seed_files() for rule in json.loads((ROOT / rel).read_text()).get("rules", [])}
    checks = {
        "full_factorial_and_unique_workers": len(runs) == 24 and len(cells) == 8 and all(c["replicates"] == 3 for c in cells) and len({r["pid"] for r in runs}) == 24,
        "counterbalanced_arms_and_audit_order": all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) and r["audit_order"] == (["true", "false"] if r["replicate"] % 2 == 0 else ["false", "true"]) for r in runs),
        "lock_matches_current_sources_and_build": json.loads(LOCK.read_text()) == raw["locked_inputs"] == raw["post_run_inputs"] == fingerprint() and all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs),
        "profile_rules_match_seed_manifests": all(set(arm(r, cache, audit)["loaded_rule_names"]) == expected_rule_names for r in runs for cache in (False, True) for audit in (False, True)),
        "all_four_semantic_outcomes_equal": all(len({json.dumps((arm(r,c,a)["graph"], arm(r,c,a)["terminal_graph"], arm(r,c,a)["tick_steps"], arm(r,c,a)["terminal_tick_steps"], arm(r,c,a)["mirror_count"]), sort_keys=True) for c in (False, True) for a in (False, True)}) == 1 and all(arm(r,c,a)["terminal_tick_steps"] == 0 for c in (False, True) for a in (False, True)) for r in runs),
        "audit_trace_and_matcher_parity": all(arm(r,False,True)["trace"] == arm(r,True,True)["trace"] and arm(r,False,True)["trace_dropped"] == arm(r,True,True)["trace_dropped"] == 0 and all(arm(r,False,True)["units"].get(k,0) == arm(r,True,True)["units"].get(k,0) for k in ("cand_tested","where_evals","rule_enumerations")) for r in runs),
        "audit_cache_counters_cover_terms": all(arm(r,True,True)["cache_stats"]["hits"]+arm(r,True,True)["cache_stats"]["misses"] == arm(r,True,True)["units"].get("term_eval:ReachableFrom",0) for r in runs),
        "off_cache_zero_and_on_cache_nonzero": all(not any(arm(r,False,a)["cache_stats"].get(k,0) for k in ("hits","misses","entries","peak_entries","estimated_payload_bytes","peak_estimated_payload_bytes")) for r in runs for a in (False,True)) and all(arm(r,True,a)["cache_stats"]["hits"]>0 and arm(r,True,a)["cache_stats"]["misses"]>0 and arm(r,True,a)["cache_stats"]["peak_entries"]>0 and arm(r,True,a)["cache_stats"]["peak_estimated_payload_bytes"]>0 for r in runs for a in (False,True)),
        "quiet_and_audit_hit_miss_counts_equal": all(arm(r,c,False)["cache_stats"]["hits"]==arm(r,c,True)["cache_stats"]["hits"] and arm(r,c,False)["cache_stats"]["misses"]==arm(r,c,True)["cache_stats"]["misses"] for r in runs for c in (False,True)),
        "current_payload_and_entries_within_peak": all(arm(r,c,a)["cache_stats"]["estimated_payload_bytes"] <= arm(r,c,a)["cache_stats"]["peak_estimated_payload_bytes"] and arm(r,c,a)["cache_stats"]["entries"] <= arm(r,c,a)["cache_stats"]["peak_entries"] for r in runs for c in (False,True) for a in (False,True)),
        "traversal_work_not_increased": all(arm(r,True,True)["units"].get("term_unit:ReachableFrom",0) <= arm(r,False,True)["units"].get("term_unit:ReachableFrom",0) for r in runs),
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
