#!/usr/bin/env python3
"""Analyze v2.6 scheduler/deferred operation-work rows and parity gates."""
from __future__ import annotations
import collections, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_operation_work_v2_6_workers_raw_20260929.json"
CAPTURE = ROOT / "evaluation/reports/substrate_live_describe_scene_operation_work_v2_6_20260929.json"
BASELINE = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_5_workers_raw_20260929.json"
OUT = ROOT / "evaluation/reports/substrate_live_describe_scene_operation_work_v2_6_analysis_20260929.json"
LOCK = ROOT / "evaluation/substrate_capability/live_describe_scene_operation_work_v2_6_lock_20260929.json"
TRACE_SOURCE = ROOT / "runners/dsl/src/access_trace.rs"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    raw = json.loads(RAW.read_text()); capture = json.loads(CAPTURE.read_text())
    baseline = json.loads(BASELINE.read_text())
    runs = raw["runs"]; traced = [r for r in runs if r["trace_enabled"]]
    old = {r["replicate"]: r for r in baseline["runs"] if r["trace_enabled"]}
    capture_checks = capture["checks"]
    checks = {
        "capture_gates_pass": all(capture_checks.values()),
        "three_traced_fresh_workers": len(traced) == 3 and len({r["pid"] for r in traced}) == 3,
        "source_stable_and_lock_matches": capture["locked_inputs"] == capture["post_run_inputs"] and all(
            r["worker_started_inputs"] == r["worker_finished_inputs"] == capture["locked_inputs"] for r in runs),
        "v2_5_baseline_hash_locked": capture["locked_inputs"]["v2_5_baseline_raw_sha256"] == sha(BASELINE),
        "native_trace_source_hash_matches": capture["locked_inputs"]["source_sha256"]["native_access_trace"] == sha(TRACE_SOURCE),
        "all_v2_5_trace_projection_parity": all(
            r["replicate"] in old and all(r[k] == old[r["replicate"]][k] for k in
                ("replies", "event_rows", "final", "whole_graph_semantic_sha256", "task_boundaries")) for r in traced),
        "every_traced_request_has_work_snapshot": all(set(r["request_traces"]) == {"request-A", "request-B"}
            and all("work_rows" in q and "work_units" in q for q in r["request_traces"].values()) for r in traced),
        "zero_work_trace_drops": all(r["operation_work"]["dropped"] == 0 and
            all(q["work_dropped"] == 0 for q in r["request_traces"].values()) for r in traced),
        "per_request_and_process_work_reconcile": all(r["operation_work"]["units"] ==
            sum(q["work_units"] for q in r["request_traces"].values()) ==
            sum(x["work_units"] for x in r["operation_work"]["rows"]) for r in traced),
        "untraced_work_stream_empty": all(r["operation_work"]["units"] == 0 and not r["operation_work"]["rows"] for r in runs if not r["trace_enabled"]),
    }
    rows = []
    for run in traced:
        for request, data in run["request_traces"].items():
            by_kind = collections.Counter(); by_rule = collections.Counter(); by_op_kind = collections.defaultdict(collections.Counter)
            op_rule = {}
            for row in data["work_rows"]:
                units = int(row["work_units"]); kind = str(row["kind"]); rule_uid = int(row["rule_uid"])
                op_id = int(row["operation_id"])
                by_kind[kind] += units
                by_rule[str(rule_uid)] += units
                by_op_kind[op_id][kind] += units
                op_rule.setdefault(op_id, rule_uid)
            rows.append({"replicate": run["replicate"], "request": request,
                         "operation_work_units": int(data["work_units"]),
                         "distinct_work_rows": len(data["work_rows"]),
                         "distinct_operations": len(op_rule),
                         "units_by_kind": dict(sorted(by_kind.items())),
                         "units_by_rule_uid": dict(sorted(by_rule.items())),
                         "rule_uid_zero_units": by_rule.get("0", 0),
                         "units_by_operation": {str(op): {"rule_uid": op_rule[op], "kinds": dict(sorted(k.items())), "total": sum(k.values())}
                                                for op, k in sorted(by_op_kind.items())},
                         "access_event_total": int(data["event_count"]),
                         "trace_interval_wall_ns": int(data["wall_ns"]),
                         "trace_interval_thread_cpu_ns": int(data["thread_cpu_ns"])})
    work_names = set()
    for run in traced:
        for q in run["request_traces"].values():
            work_names.update(x["kind"] for x in q["work_rows"])
    source_text = TRACE_SOURCE.read_text()
    checks["work_kinds_have_source_definitions"] = all(f'"{kind}"' in source_text for kind in work_names)
    report = {"schema_version": 1, "run_id": "live-describe-scene-operation-work-v2.6-analysis-20260929",
              "raw_sha256": sha(RAW), "capture_sha256": sha(CAPTURE), "baseline_v2_5_raw_sha256": sha(BASELINE),
              "capture_lock_sha256": sha(LOCK), "analysis_script_sha256": sha(Path(__file__).resolve()),
              "trace_source_sha256": sha(TRACE_SOURCE), "checks": checks, "all_checks_pass": all(checks.values()),
              "work_counter_semantics": "Native units aggregated by existing note_work call sites. These are not cycles, bytes, candidates in general, or elapsed time. Rule UID 0 denotes work recorded outside an active rule context.",
              "claim_boundary": "Scheduler/deferred operation work captured inside instrumented run_rules operations for one production route and one authored concurrency fixture; not total operation cost, full dynamic dependencies, or natural-task prevalence.",
              "rows": rows}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "row_count": len(rows), "work_units": {f"{r['replicate']}:{r['request']}": r["operation_work_units"] for r in rows}}, indent=2))
    return 0 if report["all_checks_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
