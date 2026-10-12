#!/usr/bin/env python3
"""Independent checks for the fresh-process profile import observation."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/profile_runtime_import_observation_v1_20260928.json"
OUT = ROOT / "evaluation/reports/profile_runtime_import_observation_v1_analysis_20260928.json"


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    locked = raw["locked_inputs"]
    declared = runs[0]["profile_declared_modules"] if runs else []
    expected_call_names = [row["requested"] for row in runs[0]["import_calls"]] if runs else []
    signatures = []
    per_run = []
    for run in runs:
        calls = run["import_calls"]
        targets = [row["requested"] for row in calls]
        resolved = [row["resolved"] for row in calls]
        file_map_ok = all(path is not None and path.startswith("domains/")
                          for path in run["profile_module_files"].values())
        signatures.append({"loaded_seed_ids": run["loaded_seed_ids"], "node_count": run["node_count"],
                           "edge_count": run["edge_count"], "before": run["modules_loaded_before_profile"],
                           "new": run["new_domains_modules"], "calls": calls,
                           "profile_status": run["profile_status"], "file_map_ok": file_map_ok})
        per_run.append({"replicate": run["replicate"], "pid": run["pid"],
                        "selected_seed_count": len(run["loaded_seed_ids"]),
                        "import_call_count": len(calls),
                        "modules_loaded_before_count": len(run["modules_loaded_before_profile"]),
                        "new_domain_module_count": len(run["new_domains_modules"]),
                        "new_domain_modules": run["new_domains_modules"],
                        "wall_ms": run["profile_wall_ns"] / 1e6,
                        "peak_rss_bytes": run["peak_rss_bytes"],
                        "all_declared_modules_resolve_in_repo": file_map_ok})
    outcome_signatures = [{k: v for k, v in row.items() if k not in ("before", "new", "calls", "file_map_ok")}
                          for row in signatures]
    declared_per_worker = all(run["profile_declared_modules"] == declared for run in runs)
    checks = {
        "capture_status_complete": raw.get("capture_status") == "complete",
        "three_fresh_processes": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "replicates_0_1_2": sorted(r["replicate"] for r in runs) == [0, 1, 2],
        "top_level_source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_source_locks_stable": all(r["worker_started_inputs"] == locked == r["worker_finished_inputs"] for r in runs),
        "profile_selection_complete": all(r["profile_status"]["selection_complete"] is True for r in runs),
        "no_seed_load_failures": all(r["profile_status"]["failed_count"] == 0 for r in runs),
        "profile_declared_list_matches_across_workers": declared_per_worker,
        "profile_declares_65_unique_modules": len(declared) == 65 and len(set(declared)) == 65,
        "observed_import_calls_equal_declared_order": all(
            [c["requested"] for c in r["import_calls"]] == r["profile_declared_modules"]
            and [c["resolved"] for c in r["import_calls"]] == r["profile_declared_modules"] for r in runs),
        "all_declared_modules_have_repo_files": all(
            all(path is not None and path.startswith("domains/") for path in r["profile_module_files"].values())
            for r in runs),
        "profile_outcomes_repeat": bool(outcome_signatures) and all(s == outcome_signatures[0] for s in outcome_signatures[1:]),
        "new_module_sets_repeat": bool(runs) and all(r["new_domains_modules"] == runs[0]["new_domains_modules"] for r in runs[1:]),
        "observed_modules_include_profile_targets": all(
            set(r["profile_declared_modules"]).issubset(set(r["new_domains_modules"]) | set(r["modules_loaded_before_profile"]))
            for r in runs),
    }
    wall = [r["profile_wall_ns"] / 1e6 for r in runs]
    report = {
        "schema_version": 1,
        "run_id": raw.get("run_id"),
        "capture_status": raw.get("capture_status"),
        "all_checks_pass": all(checks.values()),
        "checks": checks,
        "declared_module_count": len(declared),
        "unique_new_domain_module_count": len(set(x for r in runs for x in r["new_domains_modules"])),
        "new_domain_modules": sorted(set(x for r in runs for x in r["new_domains_modules"])),
        "profile_wall_ms": {"median": statistics.median(wall) if wall else None,
                            "min": min(wall) if wall else None, "max": max(wall) if wall else None},
        "workers": per_run,
        "claim_boundary": "One explicit conversation profile on one source snapshot; import observation does not establish per-task module necessity, general capability, or full-runtime cost.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": report["all_checks_pass"], "checks": checks,
                      "new_domain_module_count": report["unique_new_domain_module_count"],
                      "profile_wall_ms": report["profile_wall_ms"], "output": str(OUT.relative_to(ROOT))}, indent=2))
    if not report["all_checks_pass"]:
        raise SystemExit("profile import observation gate failed")


if __name__ == "__main__":
    main()
