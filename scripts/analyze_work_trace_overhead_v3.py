#!/usr/bin/env python3
"""Independent factorial analysis of live work-trace instrumentation overhead."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/work_trace_overhead_v3_20260928.json"
OUT = ROOT / "evaluation/reports/work_trace_overhead_v3_analysis_20260928.json"
EXPECTED = "I see the grey thing stays, the yellow counter, and the blue thing moves."
ARMS = {"baseline", "audit_only", "trace_only", "audit_and_trace"}
OBSERVABLES = ("reply", "route", "graph_node_count", "graph_edge_count", "goal_count", "outbound_texts")


def delta(on: int, off: int) -> dict:
    return {"delta_ns": on - off, "delta_percent": 100.0 * (on - off) / off}


def summary(values: list[float]) -> dict:
    return {"median": statistics.median(values), "min": min(values), "max": max(values)}


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    expected_orders = [
        ["baseline", "audit_only", "trace_only", "audit_and_trace"],
        ["audit_and_trace", "trace_only", "audit_only", "baseline"],
        ["audit_only", "baseline", "audit_and_trace", "trace_only"],
    ]
    checks = {
        "three_workers": len(runs) == 3,
        "three_fresh_processes": len({run["pid"] for run in runs}) == 3,
        "replicates_0_1_2": sorted(run["replicate"] for run in runs) == [0, 1, 2],
        "top_level_source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_source_lock_stable": all(run["before"] == raw["locked_inputs"] == run["after"] for run in runs),
        "registered_arm_orders": all(run["arm_order"] == expected_orders[run["replicate"]] for run in runs),
        "four_arms_each": all({arm["arm"] for arm in run["arms"]} == ARMS and len(run["arms"]) == 4 for run in runs),
    }
    pairs = []
    for run in runs:
        arms = {arm["arm"]: arm for arm in run["arms"]}
        observables = {name: {field: arms[name][field] for field in OBSERVABLES} for name in sorted(ARMS)}
        semantic_match = len({json.dumps(value, sort_keys=True) for value in observables.values()}) == 1
        counts = {name: arms[name]["scale_counters"] for name in ARMS}
        counter_keys = {key for row in counts.values() for key in row if not key.endswith("_ns")}
        audit_counter_match = all(counts["audit_only"].get(key, 0) == counts["audit_and_trace"].get(key, 0) for key in counter_keys)
        trace_only_work = {}
        for row in arms["trace_only"].get("all_scope_work_rows", []):
            if row[3] in {"scheduler_pass", "scheduler_external_poll_slots", "scheduler_fixedpoint_probe_slots", "scheduler_dirty_vector_slots", "scheduler_selected_rules"}:
                trace_only_work[row[3]] = trace_only_work.get(row[3], 0) + int(row[5])
        trace_scheduler_map = {
            "scheduler_pass": "scheduler_passes",
            "scheduler_external_poll_slots": "scheduler_external_poll_slots",
            "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
            "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
            "scheduler_selected_rules": "scheduler_selected_rules",
        }
        trace_only_scheduler_matches_audit = all(
            trace_only_work.get(kind, 0) == int(counts["audit_only"].get(metric, 0))
            for kind, metric in trace_scheduler_map.items()
        )
        gates = {
            "expected_reply_all_arms": all(arms[name]["reply"] == EXPECTED for name in ARMS),
            "task_observables_match_all_arms": semantic_match,
            "integer_audit_counters_match_between_audit_arms": audit_counter_match,
            "trace_only_scheduler_work_matches_audit_counter_control": trace_only_scheduler_matches_audit,
            "tracing_disabled_arms_have_no_rows": all(arms[name]["work_row_count"] == 0 and arms[name]["work_units"] == 0 for name in ("baseline", "audit_only")),
            "tracing_enabled_arms_have_rows": all(arms[name]["work_row_count"] > 0 and arms[name]["work_units"] > 0 for name in ("trace_only", "audit_and_trace")),
            "trace_drops_zero": all(arms[name]["work_dropped"] == 0 for name in ARMS),
            "all_request_timings_positive": all(arms[name]["request_wall_ns"] > 0 and arms[name]["request_process_cpu_ns"] > 0 for name in ARMS),
        }
        effects = {}
        for measure in ("request_wall_ns", "request_process_cpu_ns"):
            effects[f"trace_effect_audit_off_{measure}"] = delta(arms["trace_only"][measure], arms["baseline"][measure])
            effects[f"trace_effect_audit_on_{measure}"] = delta(arms["audit_and_trace"][measure], arms["audit_only"][measure])
            effects[f"audit_effect_trace_off_{measure}"] = delta(arms["audit_only"][measure], arms["baseline"][measure])
            effects[f"interaction_{measure}_ns"] = effects[f"trace_effect_audit_on_{measure}"]["delta_ns"] - effects[f"trace_effect_audit_off_{measure}"]["delta_ns"]
        pairs.append({
            "replicate": run["replicate"], "pid": run["pid"], "arm_order": run["arm_order"],
            "task_observables_by_arm": observables, "arms": arms, "effects": effects, "checks": gates,
        })
    checks["every_pair_semantic_and_counter_gate"] = all(all(pair["checks"].values()) for pair in pairs)
    timing_summary = {}
    effect_fields = [
        "trace_effect_audit_off_request_wall_ns", "trace_effect_audit_off_request_process_cpu_ns",
        "trace_effect_audit_on_request_wall_ns", "trace_effect_audit_on_request_process_cpu_ns",
        "audit_effect_trace_off_request_wall_ns", "audit_effect_trace_off_request_process_cpu_ns",
    ]
    for field in effect_fields:
        timing_summary[field] = {
            "delta_ns": summary([pair["effects"][field]["delta_ns"] for pair in pairs]),
            "delta_percent": summary([pair["effects"][field]["delta_percent"] for pair in pairs]),
        }
    for measure in ("request_wall_ns", "request_process_cpu_ns"):
        timing_summary[f"interaction_{measure}_ns"] = summary([pair["effects"][f"interaction_{measure}_ns"] for pair in pairs])
    result = {
        "schema_version": 1,
        "claim_boundary": "Three paired blocks on one authored dialogue route. Factorial timing isolates work-trace and scale-audit contrasts descriptively; it is not a general performance estimate.",
        "checks": checks, "paired_results": pairs, "timing_summary": timing_summary,
        "all_checks_pass": all(checks.values()),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "timing_summary": timing_summary, "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("factorial work-trace overhead analysis failed")


if __name__ == "__main__":
    main()
