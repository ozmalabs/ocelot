#!/usr/bin/env python3
"""Independent paired analysis of live work-trace overhead pilot."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/work_trace_overhead_v1_20260928.json"
OUT = ROOT / "evaluation/reports/work_trace_overhead_v1_analysis_20260928.json"
EXPECTED = "I see the grey thing stays, the yellow counter, and the blue thing moves."


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    checks = {
        "three_workers": len(runs) == 3,
        "three_fresh_processes": len({run["pid"] for run in runs}) == 3,
        "replicates_0_1_2": sorted(run["replicate"] for run in runs) == [0, 1, 2],
        "top_level_source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_source_lock_stable": all(run["before"] == raw["locked_inputs"] == run["after"] for run in runs),
        "paired_order_balanced": sum(run["arm_order"] == ["trace_off", "trace_on"] for run in runs) == 2
            and sum(run["arm_order"] == ["trace_on", "trace_off"] for run in runs) == 1,
    }
    pairs = []
    for run in runs:
        by_arm = {row["arm"]: row for row in run["arms"]}
        off, on = by_arm["trace_off"], by_arm["trace_on"]
        obs_fields = ("reply", "route", "graph_node_count", "graph_edge_count", "goal_count", "outbound_texts")
        off_obs = {field: off[field] for field in obs_fields}
        on_obs = {field: on[field] for field in obs_fields}
        counter_fields = {k for k in set(off["scale_counters"]) | set(on["scale_counters"]) if not k.endswith("_ns")}
        counters_match = all(off["scale_counters"].get(k, 0) == on["scale_counters"].get(k, 0) for k in counter_fields)
        gates = {
            "expected_reply_both_arms": off["reply"] == EXPECTED and on["reply"] == EXPECTED,
            "task_observables_match": off_obs == on_obs,
            "integer_scale_counters_match": counters_match,
            "trace_off_has_no_work_rows": off["work_row_count"] == 0 and off["work_units"] == 0,
            "trace_on_has_work_rows": on["work_row_count"] > 0 and on["work_units"] > 0,
            "trace_drops_zero": off["work_dropped"] == on["work_dropped"] == 0,
            "positive_request_timings": min(off["request_wall_ns"], on["request_wall_ns"], off["request_process_cpu_ns"], on["request_process_cpu_ns"]) > 0,
        }
        delta_wall = on["request_wall_ns"] - off["request_wall_ns"]
        delta_cpu = on["request_process_cpu_ns"] - off["request_process_cpu_ns"]
        pairs.append({
            "replicate": run["replicate"], "pid": run["pid"], "arm_order": run["arm_order"],
            "trace_off": off, "trace_on": on,
            "task_observables_off": off_obs, "task_observables_on": on_obs,
            "paired_wall_delta_ns": delta_wall,
            "paired_wall_delta_percent": 100.0 * delta_wall / off["request_wall_ns"],
            "paired_process_cpu_delta_ns": delta_cpu,
            "paired_process_cpu_delta_percent": 100.0 * delta_cpu / off["request_process_cpu_ns"],
            "checks": gates,
        })
    checks["every_pair_semantic_and_counter_gate"] = all(all(pair["checks"].values()) for pair in pairs)
    wall_pct = [pair["paired_wall_delta_percent"] for pair in pairs]
    cpu_pct = [pair["paired_process_cpu_delta_percent"] for pair in pairs]
    summary = {
        "pair_count": len(pairs),
        "wall_delta_ns": {"median": statistics.median(p["paired_wall_delta_ns"] for p in pairs), "min": min(p["paired_wall_delta_ns"] for p in pairs), "max": max(p["paired_wall_delta_ns"] for p in pairs)},
        "wall_delta_percent": {"median": statistics.median(wall_pct), "min": min(wall_pct), "max": max(wall_pct)},
        "process_cpu_delta_ns": {"median": statistics.median(p["paired_process_cpu_delta_ns"] for p in pairs), "min": min(p["paired_process_cpu_delta_ns"] for p in pairs), "max": max(p["paired_process_cpu_delta_ns"] for p in pairs)},
        "process_cpu_delta_percent": {"median": statistics.median(cpu_pct), "min": min(cpu_pct), "max": max(cpu_pct)},
    }
    result = {
        "schema_version": 1,
        "claim_boundary": "Three paired blocks on one authored live route, scale auditing enabled in both arms; descriptive instrumentation overhead only.",
        "checks": checks, "paired_results": pairs, "timing_summary": summary,
        "all_checks_pass": all(checks.values()),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "timing_summary": summary, "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("work-trace overhead analysis failed")


if __name__ == "__main__":
    main()
