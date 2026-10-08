#!/usr/bin/env python3
"""Independent all-scope scheduler/deferred work reconciliation."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/live_scheduler_work_trace_v3_20260928.json"
OUT = ROOT / "evaluation/reports/live_scheduler_work_trace_v3_analysis_20260928.json"
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
        "expected_reply_each_worker": all(r["reply"] == "I see the grey thing stays, the yellow counter, and the blue thing moves." for r in runs),
    }
    profiles = []
    for run in runs:
        by_scope_trace: Counter[tuple[int, str]] = Counter()
        normalized_op: Counter[tuple[int, str, int | None]] = Counter()
        rows_valid = True
        scope_ids = set()
        for row in run["all_scope_work_rows"]:
            if len(row) != 6:
                rows_valid = False
                continue
            scope, operation, _uid, kind, subject, units = row
            scope, operation, units = int(scope), int(operation), int(units)
            subject = None if subject is None else int(subject)
            rows_valid &= scope > 0 and operation > 0 and units > 0
            scope_ids.add(scope)
            if kind in SCHEDULER:
                metric = SCHEDULER[kind]
            elif kind.startswith("deferred_queue_"):
                family = next((name for name, code in FAMILIES.items() if code == subject), None)
                suffix = {"deferred_queue_enqueue_items": "enqueued_items",
                          "deferred_queue_drain_batches": "drain_batches",
                          "deferred_queue_drained_items": "drained_items"}.get(kind)
                metric = f"deferred_queue:{family}:{suffix}" if family and suffix else None
            else:
                metric = None
            if metric is None:
                rows_valid = False
                continue
            by_scope_trace[(scope, metric)] += units
            normalized_op[(operation, kind, subject)] += units

        by_scope_counter: Counter[tuple[int, str]] = Counter()
        for scope, metric, units in run["all_scope_scale_counters"]:
            by_scope_counter[(int(scope), str(metric))] += int(units)
        relevant_counter_keys = {(scope, metric) for scope, metric in by_scope_counter
                                 if metric in set(SCHEDULER.values()) or metric.startswith("deferred_queue:")}
        all_scope_keys = set(by_scope_trace) | relevant_counter_keys
        scope_deltas = {f"{scope}:{metric}": by_scope_counter[(scope, metric)] - by_scope_trace[(scope, metric)]
                        for scope, metric in sorted(all_scope_keys)}

        global_counts = run["scale_counters"]
        global_deltas = {}
        metrics = list(SCHEDULER.values()) + [
            f"deferred_queue:{family}:{suffix}" for family in FAMILIES
            for suffix in ("enqueued_items", "drain_batches", "drained_items")
        ]
        for metric in metrics:
            scoped_sum = sum(value for (scope, name), value in by_scope_counter.items() if name == metric)
            global_deltas[metric] = {
                "global_units": int(global_counts.get(metric, 0)),
                "sum_scope_units": scoped_sum,
                "global_minus_scopes": int(global_counts.get(metric, 0)) - scoped_sum,
            }
        profile_checks = {
            "all_scope_rows_valid": rows_valid,
            "all_scope_trace_no_drops": run["all_scope_work_dropped"] == 0,
            "at_least_one_scope": bool(scope_ids),
            "every_scope_metric_reconciles": all(delta == 0 for delta in scope_deltas.values()),
            "all_process_global_totals_assigned_to_scopes": all(v["global_minus_scopes"] == 0 for v in global_deltas.values()),
        }
        profiles.append({
            "replicate": run["replicate"], "pid": run["pid"], "reply": run["reply"],
            "scope_count": len(scope_ids), "operation_count": len({row[1] for row in run["all_scope_work_rows"]}),
            "scoped_counter_deltas": scope_deltas, "process_global_minus_scope_deltas": global_deltas,
            "normalized_operation_work": {f"{op}:{kind}:{subject}": units for (op, kind, subject), units in sorted(normalized_op.items())},
            "checks": profile_checks,
        })
    for field in ("reply", "scope_count", "operation_count", "normalized_operation_work", "scoped_counter_deltas", "process_global_minus_scope_deltas"):
        checks[f"workers_match_{field}"] = all(p[field] == profiles[0][field] for p in profiles[1:])
    checks["per_worker_scope_reconciliation"] = all(p["checks"]["every_scope_metric_reconciles"] for p in profiles)
    checks["all_process_global_work_assigned"] = all(p["checks"]["all_process_global_totals_assigned_to_scopes"] for p in profiles)
    checks["per_worker_integrity"] = all(p["checks"]["all_scope_rows_valid"] and p["checks"]["all_scope_trace_no_drops"] and p["checks"]["at_least_one_scope"] for p in profiles)
    result = {
        "schema_version": 1,
        "claim_boundary": "One authored live route. All-scope operation work is attributed per graph; global residuals indicate scheduler/queue work outside captured run_rules scopes or missing instrumentation.",
        "checks": checks, "worker_profiles": profiles, "all_checks_pass": all(checks.values()),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("all-scope scheduler-work reconciliation failed")


if __name__ == "__main__":
    main()
