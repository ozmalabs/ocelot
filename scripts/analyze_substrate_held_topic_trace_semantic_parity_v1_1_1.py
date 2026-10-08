#!/usr/bin/env python3
"""Independent paired semantic and trace-integrity analysis."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/held_topic_trace_semantic_parity_v1_1_20260928.json"
OUT = ROOT / "evaluation/reports/held_topic_trace_semantic_parity_v1_1_1_analysis_20260928.json"

from scripts.analyze_substrate_held_topic_structural_trace_capture_v1 import (  # noqa: E402
    access_summary, independent_task_oracle, reconcile_work, verify_schema,
)

SEMANTIC_TURN_FIELDS = (
    "prompt", "expected_topic", "expected_path", "reply", "message",
    "comprehension", "goals", "answer_topic_goal_ids", "held_answer_ids",
    "held_answers", "evidence_ids", "evidence", "receipts", "reply_messages",
    "grounder_calls", "matching_requests_after",
)
FRAME_FIELDS = (
    "node_ids", "node_count", "internal_edge_count", "boundary_incidence_count",
    "boundary_unique_external_node_count", "boundary_edge_type_counts",
    "boundary_external_node_type_counts", "internal_edges", "boundary_edges",
    "member_induced_treewidth_upper_bound",
)


def digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def signature(run: dict) -> dict:
    return {
        "teaching": [{key: row.get(key) for key in (
            "topic", "expected_answer", "returned_answer")} for row in run["teaching"]],
        "turns": [{
            **{key: row.get(key) for key in SEMANTIC_TURN_FIELDS},
            "task_frame": {key: row["task_frame"].get(key) for key in FRAME_FIELDS},
        } for row in run["turns"]],
    }


def oracle_summary(run: dict) -> dict:
    teaching = [{"topic": row["topic"], "passed": row["returned_answer"] == row["expected_answer"]}
                for row in run["teaching"]]
    queries = [{"prompt": row["prompt"], "topic": row["expected_topic"],
                **independent_task_oracle(row)} for row in run["turns"]]
    return {"teaching": teaching, "queries": queries,
            "passed": sum(row["passed"] for row in teaching + queries),
            "total": len(teaching) + len(queries)}


def analyze_trace(run: dict) -> dict:
    calls = list(run["teaching"]) + list(run["turns"])
    per_call = []
    for index, call in enumerate(calls):
        work = call["work"]
        access = access_summary(work)
        reconciliation = reconcile_work(work)
        per_call.append({
            "index": index, "operation": "teaching" if index < 3 else "query",
            "access": access,
            "work_reconciliation": reconciliation,
            "checks": {
                "access_count_conserves": access["recorded_weight_conserves"],
                "access_zero_drops": access["dropped_events"] == 0,
                "all_access_uids_resolve": not access["unresolved_rule_uids"],
                "no_static_mismatch": not access["static_mismatch_event_weights"],
                "work_zero_drops": reconciliation["dropped_rows"] == 0,
                "work_rows_valid": reconciliation["valid_rows"],
                "scope_work_reconciles": reconciliation["all_scope_counters_reconcile"],
                "global_work_assigned": reconciliation["all_global_work_assigned_to_scopes"],
                "operation_markers_complete": reconciliation[
                    "every_operation_has_exactly_one_kind_marker"],
            },
        })
    frame_checks = [verify_schema(turn["task_frame"]) for turn in run["turns"]]
    return {"calls": per_call, "task_frame_checks": frame_checks,
            "weighted_access_events_by_call": [row["access"]["weighted_access_events"]
                                                for row in per_call]}


def main() -> None:
    raw = json.loads(RAW.read_text())
    checks = {
        "three_workers": len(raw["runs"]) == 3,
        "three_distinct_pids": len({row["pid"] for row in raw["runs"]}) == 3,
        "source_stable_global": raw["locked_inputs"] == raw["post_run_inputs"],
        "three_replicate_ids": sorted(row["replicate"] for row in raw["runs"]) == [0, 1, 2],
    }
    workers = []
    for row in raw["runs"]:
        rep = int(row["replicate"])
        arms = row["runs"]
        plain, traced = arms["baseline"], arms["trace"]
        checks[f"replicate_{rep}_worker_lock_stable"] = (
            row["source_started"] == raw["locked_inputs"]["source_lock"] == row["source_finished"]
            and plain["worker_started_inputs"] == plain["worker_finished_inputs"]
            and traced["worker_started_inputs"] == traced["worker_finished_inputs"]
            and plain["worker_started_inputs"] == traced["worker_started_inputs"]
            == raw["locked_inputs"]["source_lock"]["base_fingerprint"])
        checks[f"replicate_{rep}_semantic_parity"] = signature(plain) == signature(traced)
        checks[f"replicate_{rep}_fixed_schedule"] = (
            len(plain["teaching"]) == len(traced["teaching"]) == 3
            and len(plain["turns"]) == len(traced["turns"]) == 7)
        plain_oracle, trace_oracle = oracle_summary(plain), oracle_summary(traced)
        checks[f"replicate_{rep}_oracle_arm_parity"] = plain_oracle == trace_oracle
        trace_analysis = analyze_trace(traced)
        checks[f"replicate_{rep}_trace_checks"] = all(
            all(call["checks"].values()) for call in trace_analysis["calls"])
        checks[f"replicate_{rep}_frame_schema_checks"] = all(
            all(frame.values()) for frame in trace_analysis["task_frame_checks"])
        workers.append({
            "replicate": rep, "pid": row["pid"], "arm_order": row["arm_order"],
            "baseline_signature_sha256": digest(signature(plain)),
            "trace_signature_sha256": digest(signature(traced)),
            "baseline_oracle": plain_oracle,
            "trace_oracle": trace_oracle,
            "trace_analysis": trace_analysis,
        })
    # Repetition compares semantic signatures across processes for each arm.
    baseline_hashes = {worker["baseline_signature_sha256"] for worker in workers}
    trace_hashes = {worker["trace_signature_sha256"] for worker in workers}
    checks["baseline_repeats_across_workers"] = len(baseline_hashes) == 1
    checks["trace_repeats_across_workers"] = len(trace_hashes) == 1
    trace_transparency = all(checks.get(f"replicate_{i}_semantic_parity", False)
                             for i in range(3))
    capability_pass = all(worker["trace_oracle"]["passed"] == worker["trace_oracle"]["total"]
                          for worker in workers)
    result = {
        "schema_version": 1,
        "run_id": raw["run_id"],
        "input_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "trace_semantic_transparency_pass": trace_transparency,
        "trace_capability_oracle_pass": capability_pass,
        "worker_analyses": workers,
        "claim_boundary": (
            "Paired baseline/trace evidence is limited to the fixed seven-query held-topic suite, "
            "the locked source/native build, and the measured trace surface."),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"],
                      "trace_semantic_transparency_pass": trace_transparency,
                      "trace_capability_oracle_pass": capability_pass,
                      "check_count": len(checks),
                      "failed_checks": [key for key, value in checks.items() if not value],
                      "output": str(OUT.relative_to(ROOT))}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("paired semantic-parity analysis failed")


if __name__ == "__main__":
    main()
