#!/usr/bin/env python3
"""Independent semantic and counter audit for trace-overhead panel v1."""
from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/live_scheduler_trace_overhead_v1_20260928.json"
OUT = ROOT / "evaluation/reports/live_scheduler_trace_overhead_v1_analysis_20260928.json"
EXPECTED = "I see the grey thing stays, the yellow counter, and the blue thing moves."
SCHEDULER = {
    "scheduler_pass": "scheduler_passes",
    "scheduler_external_poll_slots": "scheduler_external_poll_slots",
    "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
    "scheduler_selected_rules": "scheduler_selected_rules",
}
FAMILIES = {"rule_edits": 1, "rule_patches": 2, "fb_samples": 3, "track_identity": 4, "net_collapses": 5}


def work_metric(kind: str, subject: int | None) -> str | None:
    if kind in SCHEDULER:
        return SCHEDULER[kind]
    if not kind.startswith("deferred_queue_"):
        return None
    family = next((name for name, code in FAMILIES.items() if code == subject), None)
    suffix = {"deferred_queue_enqueue_items": "enqueued_items",
              "deferred_queue_drain_batches": "drain_batches",
              "deferred_queue_drained_items": "drained_items"}.get(kind)
    return f"deferred_queue:{family}:{suffix}" if family and suffix else None


def audit_trace(run: dict) -> tuple[bool, dict]:
    trace: Counter[tuple[int, str]] = Counter()
    kinds: dict[int, int] = {}
    scopes: set[int] = set()
    valid = True
    for row in run["all_scope_work_rows"]:
        if len(row) != 6:
            valid = False
            continue
        scope, operation, _uid, kind, subject, units = row
        scope, operation, units = int(scope), int(operation), int(units)
        subject = None if subject is None else int(subject)
        scopes.add(scope)
        valid &= scope > 0 and operation > 0 and units > 0
        if kind == "operation_kind":
            valid &= subject in (1, 2, 3) and units == 1 and operation not in kinds
            if subject is not None:
                kinds[operation] = subject
        else:
            metric = work_metric(kind, subject)
            valid &= metric is not None
            if metric:
                trace[(scope, metric)] += units
    counters: Counter[tuple[int, str]] = Counter()
    for scope, metric, units in run["all_scope_scale_counters"]:
        counters[(int(scope), str(metric))] += int(units)
    metrics = set(trace) | {(s, m) for s, m in counters
                            if m in set(SCHEDULER.values()) or m.startswith("deferred_queue:")}
    deltas = {f"{s}:{m}": counters[(s, m)] - trace[(s, m)] for s, m in sorted(metrics)}
    global_counts = run["scale_counters"]
    global_deltas = {}
    all_metrics = list(SCHEDULER.values()) + [
        f"deferred_queue:{family}:{suffix}" for family in FAMILIES
        for suffix in ("enqueued_items", "drain_batches", "drained_items")
    ]
    for metric in all_metrics:
        scoped = sum(v for (s, m), v in counters.items() if m == metric)
        global_deltas[metric] = int(global_counts.get(metric, 0)) - scoped
    op_ids = {int(row[1]) for row in run["all_scope_work_rows"]}
    passed = (valid and run["all_scope_work_dropped"] == 0 and set(kinds) == op_ids
              and all(v == 0 for v in deltas.values())
              and all(v == 0 for v in global_deltas.values()))
    return passed, {"scope_count": len(scopes), "operation_count": len(op_ids),
                    "work_row_count": len(run["all_scope_work_rows"]),
                    "scope_deltas": deltas, "process_global_deltas": global_deltas}


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    by = {(int(r["replicate"]), r["arm"]): r for r in runs}
    arms = ("baseline", "counters", "counters_work_trace")
    expected_order = [list(arms), ["counters", "counters_work_trace", "baseline"],
                      ["counters_work_trace", "baseline", "counters"]]
    checks = {
        "nine_fresh_processes": len(runs) == 9 and len({r["pid"] for r in runs}) == 9,
        "three_each_arm": all(sum(r["arm"] == arm for r in runs) == 3 for arm in arms),
        "rotated_preregistered_order": raw["arm_order"] == expected_order,
        "top_level_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "each_worker_lock_stable": all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs),
        "all_expected_replies": all(r["reply"] == EXPECTED for r in runs),
        "same_semantic_graph_and_size": len({(r["semantic_graph_sha256"], r["node_count"], r["edge_count"])
                                               for r in runs}) == 1,
        "baseline_has_no_counters_or_work": all(
            not any(int(v) for v in r["scale_counters"].values())
            and not r["all_scope_work_rows"] and r["all_scope_work_dropped"] == 0
            for r in runs if r["arm"] == "baseline"),
        "audit_arms_have_counters": all(any(int(v) for v in r["scale_counters"].values())
                                          for r in runs if r["arm"] != "baseline"),
        "work_trace_only_in_trace_arm": all(bool(r["all_scope_work_rows"])
                                            == (r["arm"] == "counters_work_trace") for r in runs),
    }
    trace_audits = {}
    for run in runs:
        if run["arm"] == "counters_work_trace":
            ok, detail = audit_trace(run)
            trace_audits[f"{run['replicate']}:{run['arm']}"] = {"pass": ok, **detail}
    checks["trace_arm_counter_reconciliation"] = len(trace_audits) == 3 and all(
        x["pass"] for x in trace_audits.values())
    counters = [by[(i, "counters")] for i in range(3)]
    traced = [by[(i, "counters_work_trace")] for i in range(3)]
    keys = set().union(*(set(r["scale_counters"]) for r in counters + traced))
    keys = {k for k in keys if not k.endswith("_ns")}
    checks["count_counters_match_trace_toggle"] = all(
        {k: int(a["scale_counters"].get(k, 0)) for k in keys}
        == {k: int(b["scale_counters"].get(k, 0)) for k in keys}
        for a, b in zip(counters, traced))
    ratios = []
    for i in range(3):
        base = by[(i, "baseline")]["converse_ns"]
        count = by[(i, "counters")]["converse_ns"]
        trace = by[(i, "counters_work_trace")]["converse_ns"]
        ratios.append({"replicate": i, "counters_over_baseline": count / base,
                       "counters_plus_trace_over_counters": trace / count,
                       "trace_over_baseline": trace / base,
                       "baseline_ns": base, "counters_ns": count, "trace_ns": trace})
    timing = {"replicates": ratios, "median_ratios": {
        key: statistics.median(row[key] for row in ratios) for key in (
            "counters_over_baseline", "counters_plus_trace_over_counters", "trace_over_baseline")}}
    result = {"schema_version": 1,
              "claim_boundary": "Three paired fresh-process measurements on one authored live route; timing ratios are descriptive, not general overhead estimates.",
              "checks": checks, "trace_reconciliation": trace_audits,
              "paired_timing": timing, "all_checks_pass": all(checks.values())}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "paired_timing": timing,
                      "all_checks_pass": result["all_checks_pass"], "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("trace overhead audit failed")


if __name__ == "__main__":
    main()
