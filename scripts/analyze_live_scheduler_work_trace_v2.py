#!/usr/bin/env python3
"""Independent live scheduler-work reconciliation using graph-scoped counters."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/live_scheduler_work_trace_v2_20260928.json"
OUT = ROOT / "evaluation/reports/live_scheduler_work_trace_v2_analysis_20260928.json"
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
        totals: Counter[tuple[str, int | None]] = Counter()
        operations: dict[int, Counter] = {}
        rows_valid = True
        for row in run["work_rows"]:
            if len(row) != 5:
                rows_valid = False
                continue
            operation, _uid, kind, subject, units = row
            operation, units = int(operation), int(units)
            rows_valid &= operation > 0 and units > 0
            key = (str(kind), None if subject is None else int(subject))
            totals[key] += units
            operations.setdefault(operation, Counter())[key] += units
        scale = run["scoped_scale_counters"]
        scheduler = {
            trace_kind: {
                "trace_scope_units": totals[(trace_kind, None)],
                "scoped_scale_units": int(scale.get(counter, 0)),
                "counter_minus_trace": int(scale.get(counter, 0)) - totals[(trace_kind, None)],
            }
            for trace_kind, counter in SCHEDULER.items()
        }
        queues = {}
        for family, subject in FAMILIES.items():
            prefix = f"deferred_queue:{family}:"
            queues[family] = {}
            for kind, metric in (("deferred_queue_enqueue_items", "enqueued_items"),
                                 ("deferred_queue_drain_batches", "drain_batches"),
                                 ("deferred_queue_drained_items", "drained_items")):
                queues[family][metric] = {
                    "trace_scope_units": totals[(kind, subject)],
                    "scoped_scale_units": int(scale.get(prefix + metric, 0)),
                    "counter_minus_trace": int(scale.get(prefix + metric, 0)) - totals[(kind, subject)],
                }
        profile_checks = {
            "work_rows_valid": rows_valid,
            "work_trace_no_drops": run["work_dropped"] == 0,
            "at_least_one_operation": bool(operations),
            "scheduler_scope_counters_match_trace": all(v["counter_minus_trace"] == 0 for v in scheduler.values()),
            "queue_scope_counters_match_trace": all(
                v["counter_minus_trace"] == 0
                for family in queues.values() for v in family.values()
            ),
        }
        profiles.append({
            "replicate": run["replicate"], "pid": run["pid"], "reply": run["reply"],
            "reported_graph_digest": run["semantic_graph_sha256"],
            "graph_digest_is_canonical": False,
            "process_global_scheduler_counters": {k: run["scale_counters"].get(v, 0) for k, v in SCHEDULER.items()},
            "process_global_fb_drain_batches": run["scale_counters"].get("deferred_queue:fb_samples:drain_batches", 0),
            "operation_count": len(operations),
            "operation_work": {str(op): {f"{k}:{s}": v for (k, s), v in sorted(values.items(), key=lambda x: (x[0][0], -1 if x[0][1] is None else x[0][1]))} for op, values in sorted(operations.items())},
            "aggregate_work": {f"{k}:{s}": v for (k, s), v in sorted(totals.items(), key=lambda x: (x[0][0], -1 if x[0][1] is None else x[0][1]))},
            "scheduler_scope_diagnostics": scheduler,
            "queue_scope_diagnostics": queues,
            "checks": profile_checks,
        })
    for field in ("reply", "aggregate_work", "operation_work", "scheduler_scope_diagnostics", "queue_scope_diagnostics"):
        checks[f"workers_match_{field}"] = all(p[field] == profiles[0][field] for p in profiles[1:])
    checks["per_worker_trace_integrity"] = all(all(p["checks"].values()) for p in profiles)
    checks["scoped_counter_parity_passed"] = all(
        p["checks"]["scheduler_scope_counters_match_trace"]
        and p["checks"]["queue_scope_counters_match_trace"] for p in profiles
    )
    result = {
        "schema_version": 1,
        "claim_boundary": "One authored live dialogue route and selected graph scope. Scoped scale counters reconcile with operation-work rows; this does not prove full-request attribution or locality.",
        "checks": checks,
        "worker_profiles": profiles,
        "all_checks_pass": all(checks.values()),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("amended live work trace integrity analysis failed")


if __name__ == "__main__":
    main()
