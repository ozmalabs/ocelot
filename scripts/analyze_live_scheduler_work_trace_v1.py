#!/usr/bin/env python3
"""Independent counter reconciliation for the live scheduler-work trace."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/live_scheduler_work_trace_v1_20260928.json"
OUT = ROOT / "evaluation/reports/live_scheduler_work_trace_v1_analysis_20260928.json"
SCHEDULER = {
    "scheduler_pass": "scheduler_passes",
    "scheduler_external_poll_slots": "scheduler_external_poll_slots",
    "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
    "scheduler_selected_rules": "scheduler_selected_rules",
}
FAMILIES = {"rule_edits": 1, "rule_patches": 2, "fb_samples": 3, "track_identity": 4, "net_collapses": 5}


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    checks = {
        "three_workers": len(runs) == 3,
        "three_fresh_processes": len({r["pid"] for r in runs}) == 3,
        "replicates_0_1_2": sorted(r["replicate"] for r in runs) == [0, 1, 2],
        "top_level_source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_source_lock_stable": all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs),
    }
    profiles = []
    for run in runs:
        totals: Counter[tuple[str, int | None]] = Counter()
        per_operation: dict[int, Counter] = {}
        valid_rows = True
        for row in run["work_rows"]:
            if len(row) != 5:
                valid_rows = False
                continue
            operation, uid, kind, subject, units = row
            operation, units = int(operation), int(units)
            valid_rows &= operation > 0 and units > 0
            key = (str(kind), None if subject is None else int(subject))
            totals[key] += units
            per_operation.setdefault(operation, Counter())[key] += units
        scale = run["scale_counters"]
        row_checks = {"work_rows_valid": valid_rows, "work_trace_no_drops": run["work_dropped"] == 0,
                      "at_least_one_run_rules_operation": bool(per_operation)}
        for kind, counter in SCHEDULER.items():
            row_checks[f"{counter}_reconciles"] = totals[(kind, None)] == int(scale.get(counter, 0))
        for family, subject in FAMILIES.items():
            prefix = f"deferred_queue:{family}:"
            for kind, metric in (("deferred_queue_enqueue_items", "enqueued_items"),
                                 ("deferred_queue_drain_batches", "drain_batches"),
                                 ("deferred_queue_drained_items", "drained_items")):
                row_checks[f"{family}_{metric}_reconciles"] = totals[(kind, subject)] == int(scale.get(prefix + metric, 0))
        profiles.append({
            "replicate": run["replicate"], "pid": run["pid"], "reply": run["reply"],
            "semantic_graph_sha256": run["semantic_graph_sha256"],
            "operation_count": len(per_operation),
            "operation_work": {str(op): {f"{k}:{s}": v for (k, s), v in sorted(vals.items(), key=lambda x: (x[0][0], -1 if x[0][1] is None else x[0][1]))} for op, vals in sorted(per_operation.items())},
            "aggregate_work": {f"{k}:{s}": v for (k, s), v in sorted(totals.items(), key=lambda x: (x[0][0], -1 if x[0][1] is None else x[0][1]))},
            "checks": row_checks,
        })
    for field in ("reply", "semantic_graph_sha256", "aggregate_work", "operation_work"):
        checks[f"workers_match_{field}"] = all(p[field] == profiles[0][field] for p in profiles[1:])
    checks["all_worker_reconciliations_pass"] = all(all(p["checks"].values()) for p in profiles)
    result = {"schema_version": 1, "claim_boundary": "One authored live dialogue route; operation-work counter parity is not complete trace recall, locality prevalence, or scaling evidence.", "worker_profiles": profiles, "checks": checks, "all_checks_pass": all(checks.values())}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("live scheduler-work trace analysis failed")


if __name__ == "__main__":
    main()
