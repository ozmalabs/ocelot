#!/usr/bin/env python3
"""Independent integrity and semantic analysis for grounded concern dispatch v1.2."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/grounded_concern_dispatch_v1_2_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/grounded_concern_dispatch_v1_2_lock_20260928.json"
OUT = ROOT / "evaluation/reports/grounded_concern_dispatch_v1_2_analysis_20260928.json"
RUNNER = ROOT / "scripts/substrate_grounded_concern_dispatch_v1_2.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_2_PREREG_20260928.md"
TEXTS = {
    "grounded_compare": "Compare where the two letters differ and judge the trial on that region.",
    "non_concern_walk": "Walk to the door.",
}
SCHEDULE = [[condition, rep] for rep in (0, 1) for condition in TEXTS]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    runs = raw.get("runs", [])
    checks = {
        "complete_capture_no_errors": raw.get("capture_status") == "complete" and not raw.get("errors"),
        "parent_lock_stable": raw.get("locked_inputs") == lock == raw.get("post_run_inputs"),
        "runner_hash_matches": lock.get("runner_sha256") == sha(RUNNER),
        "protocol_hash_matches": lock.get("protocol_sha256") == sha(PROTOCOL),
        "four_workers_exact_schedule": len(runs) == 4 and raw.get("schedule") == SCHEDULE,
        "unique_processes": len({r.get("pid") for r in runs}) == 4,
        "two_workers_per_condition": all(sum(r.get("condition") == k for r in runs) == 2 for k in TEXTS),
        "worker_locks_stable": all(r.get("inputs_stable") and r.get("inputs_before") == lock == r.get("inputs_after") for r in runs),
        "worker_boot_and_calls_complete": all(r.get("error") is None and r.get("boot_loaded", 0) > 0 and len(r.get("result", {})) > 0 for r in runs),
        "conditions_match_registered_text": all(r.get("text") == TEXTS.get(r.get("condition")) and r.get("predicate") == ("compare" if r.get("condition") == "grounded_compare" else "walk") for r in runs),
    }
    positives = [r for r in runs if r.get("condition") == "grounded_compare"]
    controls = [r for r in runs if r.get("condition") == "non_concern_walk"]
    pos_results = [r.get("result", {}) for r in positives]
    ctl_results = [r.get("result", {}) for r in controls]
    checks["positive_routes_to_grounded_concern"] = len(pos_results) == 2 and all(
        r.get("route") == "concern_authored" and r.get("goal_kind") == "author_concern"
        and isinstance(r.get("concern"), dict) and bool(r["concern"].get("signature"))
        and r["concern"].get("minted") is True and r["concern"].get("grounded") is True
        and r["concern"].get("path") == "experiment_rule" for r in pos_results)
    checks["control_stays_goal_only"] = len(ctl_results) == 2 and all(
        r.get("route") == "goal_only" and r.get("goal_kind") == "instruction" and r.get("concern") is None
        for r in ctl_results)
    checks["teacher_free_both_arms"] = all(r.get("teacher_calls") == 0 for r in runs)
    positive_concerns = [r.get("concern") for r in pos_results]
    checks["positive_concern_repeats_exactly"] = len(positive_concerns) == 2 and positive_concerns[0] == positive_concerns[1]
    summaries = {}
    for condition in TEXTS:
        group = [r for r in runs if r.get("condition") == condition]
        summaries[condition] = {
            "repeats": len(group),
            "route_counts": {route: sum(r.get("result", {}).get("route") == route for r in group) for route in sorted({r.get("result", {}).get("route") for r in group})},
            "text": TEXTS[condition],
            "median_task_wall_ms": statistics.median(r.get("task_wall_ns", 0) for r in group) / 1e6 if group else None,
            "median_task_cpu_ms": statistics.median(r.get("task_cpu_ns", 0) for r in group) / 1e6 if group else None,
            "rule_deltas": [r.get("rules_after", 0) - r.get("rules_before", 0) for r in group],
            "concern": [r.get("result", {}).get("concern") for r in group],
        }
    result = {
        "schema_version": 1,
        "analysis_id": "grounded-concern-dispatch-v1.2-independent-analysis",
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "analyzer_sha256": sha(Path(__file__)),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "outcomes_by_condition": summaries,
        "claim_boundary": "Four fresh workers show one teacher-free concern induction/grounding result for a preconstructed compare instruction and one goal-only walk control. Natural-language comprehension is bypassed; this is not a broad learning or task-generalization result.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "checks": checks, "all_checks_pass": result["all_checks_pass"]}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("independent analysis failed")


if __name__ == "__main__":
    main()
