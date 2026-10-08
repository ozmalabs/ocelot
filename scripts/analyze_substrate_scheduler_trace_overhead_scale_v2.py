#!/usr/bin/env python3
"""Independent analysis of native scheduler trace overhead across rule sizes."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/scheduler_trace_overhead_scale_v2_20260928.json"
OUT = ROOT / "evaluation/reports/scheduler_trace_overhead_scale_v2_analysis_20260928.json"
SIZES = (8, 32, 128)
ARMS = {"baseline", "audit_only", "trace_only", "audit_and_trace"}
SCHEDULER_KIND_TO_COUNTER = {
    "scheduler_pass": "scheduler_passes",
    "scheduler_external_poll_slots": "scheduler_external_poll_slots",
    "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
    "scheduler_selected_rules": "scheduler_selected_rules",
}


def contrast(on: int, off: int) -> dict:
    return {"delta_ns": on - off, "delta_percent": 100.0 * (on - off) / off}


def summarize(rows: list[float]) -> dict:
    return {"median": statistics.median(rows), "min": min(rows), "max": max(rows)}


def main() -> None:
    raw = json.loads(RAW.read_text())
    workers = raw["runs"]
    checks = {
        "three_workers": len(workers) == 3,
        "three_fresh_processes": len({worker["pid"] for worker in workers}) == 3,
        "replicates_0_1_2": sorted(worker["replicate"] for worker in workers) == [0, 1, 2],
        "top_level_source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_source_locks_stable": all(worker["before"] == raw["locked_inputs"] == worker["after"] for worker in workers),
        "complete_size_arm_grid": all(len(worker["runs"]) == len(SIZES) * len(ARMS) for worker in workers),
    }
    cells = []
    for worker in workers:
        grouped = {}
        for row in worker["runs"]:
            grouped.setdefault(row["rule_count"], {})[row["arm"]] = row
        for n in SIZES:
            arms = grouped.get(n, {})
            if set(arms) != ARMS:
                checks[f"worker_{worker['replicate']}_size_{n}_has_all_arms"] = False
                continue
            baseline = arms["baseline"]
            audit = arms["audit_only"]
            trace = arms["trace_only"]
            both = arms["audit_and_trace"]
            expected_graph = None
            arm_checks = {}
            for name, row in arms.items():
                expected_graph = expected_graph or row["graph_sha256"]
                arm_checks[f"{name}_warmup_fixed_point"] = row["warmup_report"]["status"] == "fixed_point"
                arm_checks[f"{name}_warmup_expected_edges"] = (
                    row["warmup_trigger_edges"] == n and row["warmup_derived_edges"] == n
                )
                arm_checks[f"{name}_repeated_calls_fixed_point"] = row["repeated_status_counts"] == {"fixed_point": row["repeated_calls"]}
                arm_checks[f"{name}_passes_completed"] = row["repeated_passes_completed"] >= row["repeated_calls"]
                arm_checks[f"{name}_expected_edges"] = row["trigger_edges"] == n and row["derived_edges"] == n
                arm_checks[f"{name}_graph_digest_matches"] = row["graph_sha256"] == expected_graph
                arm_checks[f"{name}_positive_timing"] = row["request_wall_ns"] > 0 and row["request_process_cpu_ns"] > 0
                arm_checks[f"{name}_trace_drop_free"] = row["work_dropped"] == 0
            integer_keys = {key for row in (audit["scale_counters"], both["scale_counters"])
                             for key in row if not key.endswith("_ns")}
            arm_checks["audit_integer_counters_match_both"] = all(
                audit["scale_counters"].get(key, 0) == both["scale_counters"].get(key, 0)
                for key in integer_keys
            )
            arm_checks["trace_off_arms_empty"] = all(arms[name]["work_row_count"] == 0 and arms[name]["work_units"] == 0 for name in ("baseline", "audit_only"))
            arm_checks["trace_on_arms_nonempty"] = all(arms[name]["work_row_count"] > 0 and arms[name]["work_units"] > 0 for name in ("trace_only", "audit_and_trace"))
            trace_work = {kind: 0 for kind in SCHEDULER_KIND_TO_COUNTER}
            for work_row in trace["work_rows"]:
                if work_row[3] in trace_work:
                    trace_work[work_row[3]] += int(work_row[5])
            arm_checks["trace_only_scheduler_matches_audit_control"] = all(
                trace_work[kind] == int(audit["scale_counters"].get(counter, 0))
                for kind, counter in SCHEDULER_KIND_TO_COUNTER.items()
            )
            effect = {}
            for metric in ("request_wall_ns", "request_process_cpu_ns"):
                effect[f"trace_only_{metric}"] = contrast(trace[metric], baseline[metric])
                effect[f"trace_with_audit_{metric}"] = contrast(both[metric], audit[metric])
                effect[f"audit_only_{metric}"] = contrast(audit[metric], baseline[metric])
                effect[f"trace_audit_interaction_{metric}_ns"] = effect[f"trace_with_audit_{metric}"]["delta_ns"] - effect[f"trace_only_{metric}"]["delta_ns"]
                for contrast_name in (f"trace_only_{metric}", f"trace_with_audit_{metric}", f"audit_only_{metric}"):
                    effect[contrast_name]["delta_ns_per_call"] = effect[contrast_name]["delta_ns"] / trace["repeated_calls"]
            cells.append({
                "replicate": worker["replicate"], "pid": worker["pid"], "rule_count": n,
                "arms": arms, "trace_only_scheduler_work": trace_work,
                "effects": effect, "checks": arm_checks,
            })
    checks["every_cell_gate_passes"] = len(cells) == 3 * len(SIZES) and all(all(cell["checks"].values()) for cell in cells)
    summary = {}
    for n in SIZES:
        group = [cell for cell in cells if cell["rule_count"] == n]
        summary[str(n)] = {}
        for measure in ("request_wall_ns", "request_process_cpu_ns"):
            for effect_name in (f"trace_only_{measure}", f"trace_with_audit_{measure}", f"audit_only_{measure}"):
                summary[str(n)][effect_name] = {
                    "delta_ns": summarize([cell["effects"][effect_name]["delta_ns"] for cell in group]),
                    "delta_percent": summarize([cell["effects"][effect_name]["delta_percent"] for cell in group]),
                    "delta_ns_per_call": summarize([cell["effects"][effect_name]["delta_ns_per_call"] for cell in group]),
                }
            interaction = f"trace_audit_interaction_{measure}_ns"
            summary[str(n)][interaction] = summarize([cell["effects"][interaction] for cell in group])
    result = {
        "schema_version": 1,
        "claim_boundary": "Three paired blocks per controlled positive scheduler size, each timing 256 warmed fixed-point calls; descriptive factorial instrumentation contrasts only.",
        "checks": checks, "cells": cells, "timing_summary_by_rule_count": summary,
        "all_checks_pass": all(checks.values()),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "timing_summary_by_rule_count": summary, "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("native scheduler trace overhead analysis failed")


if __name__ == "__main__":
    main()
