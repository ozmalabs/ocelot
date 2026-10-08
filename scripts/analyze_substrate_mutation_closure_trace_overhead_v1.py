#!/usr/bin/env python3
"""Independent analysis for mutation-to-fixpoint trace overhead v1."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/mutation_closure_trace_overhead_v1_20260928.json"
OUT = ROOT / "evaluation/reports/mutation_closure_trace_overhead_v1_analysis_20260928.json"
SIZES = (8, 32, 128)
FAMILIES = ("sparse", "matcher_dense")
ARMS = {"baseline", "audit_only", "trace_only", "audit_and_trace"}
SCHEDULER_KIND_TO_COUNTER = {
    "scheduler_pass": "scheduler_passes",
    "scheduler_external_poll_slots": "scheduler_external_poll_slots",
    "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
    "scheduler_selected_rules": "scheduler_selected_rules",
}


def delta(on: int, off: int, calls: int) -> dict:
    return {"delta_ns": on - off, "delta_percent": 100.0 * (on - off) / off,
            "delta_ns_per_call": (on - off) / calls}


def summary(values: list[float]) -> dict:
    return {"median": statistics.median(values), "min": min(values), "max": max(values)}


def main() -> None:
    raw = json.loads(RAW.read_text())
    workers = raw["runs"]
    checks = {
        "three_workers": len(workers) == 3,
        "three_fresh_processes": len({worker["pid"] for worker in workers}) == 3,
        "replicates_0_1_2": sorted(worker["replicate"] for worker in workers) == [0, 1, 2],
        "top_level_source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_source_locks_stable": all(w["before"] == raw["locked_inputs"] == w["after"] for w in workers),
        "complete_size_family_arm_grid": all(len(w["runs"]) == len(SIZES) * len(FAMILIES) * len(ARMS) for w in workers),
    }
    cells = []
    for worker in workers:
        grouped = {}
        for row in worker["runs"]:
            grouped.setdefault((row["rule_count"], row["family"]), {})[row["arm"]] = row
        for n in SIZES:
            for family in FAMILIES:
                arms = grouped.get((n, family), {})
                key = f"worker_{worker['replicate']}_{family}_n{n}"
                checks[key + "_all_arms"] = set(arms) == ARMS
                if set(arms) != ARMS:
                    continue
                baseline, audit, trace, both = (arms[name] for name in ("baseline", "audit_only", "trace_only", "audit_and_trace"))
                target_edges = 1 if family == "sparse" else 8
                cell_checks = {}
                for name, row in arms.items():
                    cell_checks[name + "_all_calls_fixed_point"] = len(row["reports"]) == 32 and all(r["status"] == "fixed_point" for r in row["reports"])
                    cell_checks[name + "_one_progress_step"] = all(r["progress_steps"] == 1 for r in row["reports"])
                    cell_checks[name + "_derived_edge_oracle"] = row["derived_counts"] == [target_edges] * 32
                    cell_checks[name + "_positive_timing"] = row["request_wall_ns"] > 0 and row["request_process_cpu_ns"] > 0
                    cell_checks[name + "_trace_drop_free"] = row["work_dropped"] == 0
                cell_checks["graphs_match_all_arms"] = all(row["graph_digests"] == baseline["graph_digests"] for row in arms.values())
                cell_checks["reports_match_all_arms"] = all(row["reports"] == baseline["reports"] for row in arms.values())
                integer_keys = {key for row in (audit["scale_counters"], both["scale_counters"]) for key in row if not key.endswith("_ns")}
                cell_checks["audit_integer_counters_match_both"] = all(audit["scale_counters"].get(k, 0) == both["scale_counters"].get(k, 0) for k in integer_keys)
                cell_checks["trace_off_arms_empty"] = all(row["work_row_count"] == 0 for row in (baseline, audit))
                cell_checks["trace_on_arms_nonempty"] = all(row["work_row_count"] > 0 for row in (trace, both))
                trace_work = {kind: 0 for kind in SCHEDULER_KIND_TO_COUNTER}
                for work_row in trace["work_rows"]:
                    if work_row[3] in trace_work:
                        trace_work[work_row[3]] += int(work_row[5])
                cell_checks["trace_only_scheduler_matches_audit"] = all(
                    trace_work[kind] == int(audit["scale_counters"].get(counter, 0))
                    for kind, counter in SCHEDULER_KIND_TO_COUNTER.items()
                )
                expected_candidates = 32 if family == "sparse" else 32 * (8 * 8 + 8)
                cell_checks["authored_matcher_workload_counter"] = int(audit["scale_counters"].get("cand_tested", 0)) == expected_candidates
                effects = {}
                for metric in ("request_wall_ns", "request_process_cpu_ns"):
                    effects["trace_only_" + metric] = delta(trace[metric], baseline[metric], baseline["repeats"])
                    effects["trace_with_audit_" + metric] = delta(both[metric], audit[metric], baseline["repeats"])
                    effects["audit_only_" + metric] = delta(audit[metric], baseline[metric], baseline["repeats"])
                    effects["interaction_" + metric + "_ns"] = effects["trace_with_audit_" + metric]["delta_ns"] - effects["trace_only_" + metric]["delta_ns"]
                cells.append({"replicate": worker["replicate"], "pid": worker["pid"], "rule_count": n,
                              "family": family, "arms": arms, "trace_only_scheduler_work": trace_work,
                              "effects": effects, "checks": cell_checks})
    checks["every_cell_gate_passes"] = len(cells) == 18 and all(all(c["checks"].values()) for c in cells)
    summaries = {}
    for family in FAMILIES:
        summaries[family] = {}
        for n in SIZES:
            group = [c for c in cells if c["family"] == family and c["rule_count"] == n]
            summaries[family][str(n)] = {}
            for effect in ("trace_only", "trace_with_audit", "audit_only"):
                for metric in ("request_wall_ns", "request_process_cpu_ns"):
                    values = [c["effects"][effect + "_" + metric] for c in group]
                    summaries[family][str(n)][effect + "_" + metric] = {
                        key: summary([v[key] for v in values])
                        for key in ("delta_ns", "delta_percent", "delta_ns_per_call")
                    }
    result = {"schema_version": 1, "claim_boundary": "Three process blocks; controlled mutation plus closure in two synthetic rule families; descriptive factorial trace contrasts only.",
              "checks": checks, "cells": cells, "timing_summary": summaries, "all_checks_pass": all(checks.values())}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "timing_summary": summaries,
                      "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("mutation closure trace overhead analysis failed")


if __name__ == "__main__":
    main()
