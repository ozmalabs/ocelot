#!/usr/bin/env python3
"""Reanalyze locked live-task traces as per-rule/task concrete-touch matrices."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_1_workers_raw_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_live_task_rule_touch_matrix_v1_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_request(request: dict, owned_a: set[int], owned_b: set[int]) -> dict:
    rule_rows: dict[int, dict] = {}
    event_buckets: Counter[str] = Counter()
    for row in request["event_rows"]:
        uid = int(row["rule_uid"])
        nodes = {int(n) for n in (row["node"], row["peer"]) if n is not None}
        touches_a = bool(nodes & owned_a)
        touches_b = bool(nodes & owned_b)
        bucket = "both" if touches_a and touches_b else "a_only" if touches_a else "b_only" if touches_b else "neither"
        count = int(row["count"])
        event_buckets[bucket] += count
        entry = rule_rows.setdefault(uid, {"rule_name": row.get("rule_name"), "events": 0,
                                            "touches_a": False, "touches_b": False,
                                            "a_events": 0, "b_events": 0,
                                            "cross_task_events": 0})
        if entry["rule_name"] not in (None, row.get("rule_name")):
            raise ValueError(f"RuleUID {uid} has inconsistent names")
        entry["events"] += count
        entry["touches_a"] |= touches_a
        entry["touches_b"] |= touches_b
        entry["a_events"] += count if touches_a else 0
        entry["b_events"] += count if touches_b else 0
        entry["cross_task_events"] += count if bucket == "both" else 0
    summary = {
        "event_count": sum(event_buckets.values()),
        "distinct_event_rows": len(request["event_rows"]),
        "rules_observed": len(rule_rows),
        "rules_touching_a": sum(row["touches_a"] for row in rule_rows.values()),
        "rules_touching_b": sum(row["touches_b"] for row in rule_rows.values()),
        "rules_touching_both_across_events": sum(row["touches_a"] and row["touches_b"] for row in rule_rows.values()),
        "event_counts_by_task_touch": dict(sorted(event_buckets.items())),
        "per_rule": {str(uid): rule_rows[uid] for uid in sorted(rule_rows)},
    }
    return summary


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    traced = [run for run in runs if run["trace_enabled"]]
    untraced = [run for run in runs if not run["trace_enabled"]]
    results = {}
    worker_stable = len(runs) == 6 and len(traced) == 3 and len(untraced) == 3
    trace_complete = True
    for run in runs:
        worker_stable &= run["worker_started_inputs"] == raw["locked_inputs"]
        worker_stable &= run["worker_finished_inputs"] == raw["locked_inputs"]
        if run["trace_enabled"]:
            worker_stable &= set(run["request_traces"]) == {"request-A", "request-B"}
            worker_stable &= run["access_trace"]["event_count"] == sum(
                request["event_count"] for request in run["request_traces"].values())
            trace_complete &= run["access_trace"]["dropped"] == 0
        else:
            worker_stable &= not run["access_trace"]["event_rows"]
    signatures = []
    for run in sorted(traced, key=lambda row: row["replicate"]):
        a = set(run["task_boundaries"]["a"]["owned_node_ids"])
        b = set(run["task_boundaries"]["b"]["owned_node_ids"])
        request_results = {name: analyze_request(value, a, b)
                           for name, value in sorted(run["request_traces"].items())}
        signatures.append(json.dumps(request_results, sort_keys=True, separators=(",", ":")))
        results[str(run["replicate"])] = {
            "owned_a_node_count": len(a), "owned_b_node_count": len(b),
            "requests": request_results,
        }
    checks = {
        "six_workers_three_traced_three_untraced": len(runs) == 6 and len(traced) == 3 and len(untraced) == 3,
        "worker_source_locks_stable": bool(worker_stable),
        "trace_rows_have_no_drops_and_counts_reconcile": bool(trace_complete),
        "per_rule_task_touch_matrix_repeats_exactly": len(set(signatures)) == 1,
        "request_node_sets_are_disjoint": all(
            set(run["task_boundaries"]["a"]["owned_node_ids"]).isdisjoint(
                run["task_boundaries"]["b"]["owned_node_ids"]) for run in traced),
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-live-task-rule-touch-matrix-v1-20260926",
        "source_capture": str(RAW.relative_to(ROOT)),
        "source_capture_sha256": sha(RAW),
        "source_lock_sha256": sha(ROOT / "evaluation/substrate_capability/live_describe_scene_access_trace_v2_1_lock_20260926.json"),
        "analysis_script_sha256": sha(Path(__file__).resolve()),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "replicates": results,
        "claim_boundary": "This is a reanalysis of partial selected native events in one authored serialized two-request describe_scene schedule. A recorded event concretely touches a listed task vertex; no recorded touch is not evidence of independence because the trace omits some scans, host work, scheduler activity, and operations outside an active RuleUID. Rule touch across both sets is aggregated across events unless counted in cross_task_events. The result does not establish complete rule dependencies, natural-task prevalence, or safe partitioned execution.",
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "all_checks_pass": payload["all_checks_pass"],
                      "checks": checks}, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
