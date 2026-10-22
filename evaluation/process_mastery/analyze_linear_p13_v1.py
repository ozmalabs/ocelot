"""Integrity and preregistered verdicts for linear_p13_v1."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ARMS = {"full_sleep", "replay_only", "awake_rehearsal", "no_offline"}
STATUSES = {"NOT_RUN", "UNSUPPORTED", "TIMEOUT", "FAILED", "COMPLETED"}


def analyze(payload):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    rows = payload.get("records")
    if not isinstance(rows, list) or not rows:
        raise ValueError("scorecard has no records")
    if any(row.get("status") not in STATUSES for row in rows):
        raise ValueError("scorecard contains a missing or unknown trial status")
    paired = [row for row in rows if row.get("family") == "paired_delayed_task"]
    controls = [row for row in rows if row.get("family") == "interrupt_restart_control"]
    if not paired or not controls:
        raise ValueError("missing paired delayed-task family or restart controls")

    by_seed = defaultdict(list)
    for row in paired:
        by_seed[row.get("seed")].append(row)
    missing_arm_pairs = 0
    duplicate_arm_pairs = 0
    world_hash_mismatches = 0
    access_hash_mismatches = 0
    input_audit_failures = 0
    completion_failures = 0
    compute_match_failures = 0
    for seed, group in by_seed.items():
        counts = Counter(row.get("profile") for row in group)
        missing_arm_pairs += sum(counts[arm] == 0 for arm in ARMS)
        duplicate_arm_pairs += sum(max(0, counts[arm] - 1) for arm in ARMS)
        world_hash_mismatches += len({row.get("world_sha256") for row in group}) != 1
        access_hash_mismatches += len({row.get("world_access_sha256") for row in group}) != 1
        input_audit_failures += sum(
            not row.get("input_audit", {}).get("answer_fields_absent")
            or not row.get("input_audit", {}).get("no_hidden_delayed_strategy")
            or not row.get("input_audit", {}).get("same_primitive_access_hash")
            or not row.get("world_sha256") or not row.get("world_access_sha256")
            for row in group)
        completion_failures += sum(row.get("status") != "COMPLETED" for row in group)
        by_arm = {row.get("profile"): row for row in group}
        if ARMS.issubset(by_arm):
            sleep_steps = float(by_arm["full_sleep"].get("sleep_native_rule_steps", 0))
            rehearsal_steps = float(by_arm["awake_rehearsal"].get(
                "awake_rehearsal_native_rule_steps", 0))
            if sleep_steps <= 0 or abs(rehearsal_steps - sleep_steps) / sleep_steps > 0.05:
                compute_match_failures += 1
            if by_arm["full_sleep"].get("strategy_delayed_status") != "solved":
                completion_failures += 1
            if (by_arm["full_sleep"].get("library_chunks", 0) < 1
                    or not by_arm["full_sleep"].get("library_reuse")
                    or not by_arm["full_sleep"].get("strategy_recalled")):
                completion_failures += 1
            if ("approved" not in by_arm["full_sleep"].get("strategy_recall_request_statuses", [])
                    or by_arm["full_sleep"].get("strategy_recall_fallbacks", 0) != 0):
                completion_failures += 1
            if by_arm["replay_only"].get("sleep", {}).get("replay_traces", 0) < 1:
                completion_failures += 1
            if by_arm["full_sleep"].get("library_source_trace_length", 0) < 8:
                completion_failures += 1

    arm_metrics = {}
    for arm in sorted(ARMS):
        group = [row for row in paired if row.get("profile") == arm]
        if not group:
            arm_metrics[arm] = {"n": 0, "accuracy": None}
            continue
        arm_metrics[arm] = {
            "n": len(group),
            "accuracy": sum(float(row.get("accuracy", 0)) for row in group) / len(group),
            "mean_delayed_steps": sum(float(row.get("delayed_steps", 0)) for row in group) / len(group),
            "mean_library_chunks": sum(float(row.get("library_chunks", 0)) for row in group) / len(group),
            "mean_library_exact_work_reduction": sum(
                float(row.get("library_exact_work_reduction", 0)) for row in group) / len(group),
            "mean_strategy_recall_rate": sum(bool(row.get("strategy_recalled")) for row in group) / len(group),
            "mean_budget_debit": sum(float(row.get("budget_debit", 0)) for row in group) / len(group),
            "mean_boot_seconds": sum(float(row.get("boot_seconds", 0)) for row in group) / len(group),
            "mean_graph_node_growth": sum(float(row.get("graph_node_growth", 0)) for row in group) / len(group),
            "mean_graph_estimated_bytes_end": sum(
                float(row.get("graph_estimated_bytes_end", 0)) for row in group) / len(group),
            "mean_evidence_exposures": sum(float(row.get("evidence_exposures", 0)) for row in group) / len(group),
            "mean_world_actions": sum(float(row.get("world_actions", 0)) for row in group) / len(group),
        }

    full_accuracy = arm_metrics["full_sleep"]["accuracy"]
    replay_accuracy = arm_metrics["replay_only"]["accuracy"]
    accuracy_gain = (full_accuracy - replay_accuracy
                     if full_accuracy is not None and replay_accuracy is not None else None)
    new_task_loss = (max(0.0, replay_accuracy - full_accuracy)
                     if accuracy_gain is not None else None)
    library_gain = arm_metrics["full_sleep"]["mean_library_exact_work_reduction"]

    control_failures = sum(
        row.get("status") != "COMPLETED"
        or row.get("foreground_pending") is not True
        or row.get("restart_cursor_persisted") is not True
        or row.get("restart_resumed_next_stage") is not True
        or row.get("same_epoch_no_duplicate_receipt") is not True
        or row.get("budget_remaining_after_resume") != row.get("budget_remaining_after_repeat")
        for row in controls)
    p13_receipt_audit_failures = 0
    for row in paired:
        if row.get("profile") != "full_sleep":
            continue
        audits = row.get("sleep", {}).get("receipt_audit", [])
        p13_receipt_audit_failures += sum(
            audit.get("provenance_kind") != "offline_sleep_stage"
            or audit.get("observation_status") != "not_observed"
            or audit.get("shared_budget_debit") is None
            for audit in audits)
        if not audits or not {"replay", "library"}.issubset(
                {audit.get("stage") for audit in audits}):
            p13_receipt_audit_failures += 1
    integrity_failures = (missing_arm_pairs + duplicate_arm_pairs + world_hash_mismatches
                          + access_hash_mismatches + input_audit_failures
                          + completion_failures + control_failures
                          + p13_receipt_audit_failures + compute_match_failures)
    if integrity_failures:
        primary_status = "INVALID"
    elif accuracy_gain is not None and accuracy_gain >= 0.10 and new_task_loss <= 0.02:
        primary_status = "PASS"
    else:
        primary_status = "FAIL"
    if integrity_failures:
        library_status = "INVALID"
    elif library_gain >= 0.25:
        library_status = "PASS"
    else:
        library_status = "FAIL"
    metadata = payload.get("metadata", {})
    allocation = metadata.get("seed_allocation", {})
    allocation_failures = (
        int(allocation.get("paired_streams_per_arm", 0)) != len(by_seed)
        or int(allocation.get("interrupt_restart_controls", 0)) != len(controls)
        or any(len(rows_for_arm) != len(by_seed) for rows_for_arm in
               ([r for r in paired if r.get("profile") == arm] for arm in ARMS)))
    if allocation_failures:
        primary_status = library_status = "INVALID"
    return {
        "schema": "pmb-linear-p13-v1-analysis-v1",
        "phase": metadata.get("phase"), "split": metadata.get("split"),
        "paired_streams": len(by_seed), "paired_records": len(paired),
        "interrupt_restart_controls": len(controls), "arms": arm_metrics,
        "delayed_accuracy_gain_vs_replay_only": accuracy_gain,
        "new_task_loss": new_task_loss,
        "library_exact_work_reduction": library_gain,
        "paired_world_hash_mismatches": world_hash_mismatches,
        "paired_primitive_access_hash_mismatches": access_hash_mismatches,
        "missing_arm_pairs": missing_arm_pairs, "duplicate_arm_pairs": duplicate_arm_pairs,
        "input_audit_failures": input_audit_failures,
        "completion_failures": completion_failures,
        "awake_rehearsal_compute_match_failures": compute_match_failures,
        "interrupt_restart_control_failures": control_failures,
        "sleep_receipt_provenance_failures": p13_receipt_audit_failures,
        "allocation_failures": int(allocation_failures),
        "integrity_failures": integrity_failures,
        "primary_status": primary_status,
        "library_status": library_status,
        "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED",
        "scope": "paired_native_process_delayed_task_and_sleep_restart_controls",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path, nargs="?")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        records = []
        for arm, steps in (("full_sleep", 1), ("replay_only", 32),
                           ("awake_rehearsal", 32), ("no_offline", 32)):
            records.append({
                "status": "COMPLETED", "family": "paired_delayed_task", "seed": 13,
                "profile": arm, "accuracy": 1, "delayed_steps": steps,
                "library_exact_work_reduction": 0.359, "library_chunks": int(arm == "full_sleep"),
                "strategy_recalled": arm == "full_sleep", "budget_debit": 1,
                "library_reuse": arm == "full_sleep",
                "strategy_recall_request_statuses": ["approved"] if arm == "full_sleep" else [],
                "strategy_recall_fallbacks": 0,
                "native_rule_steps": 200,
                "sleep_native_rule_steps": 50 if arm == "full_sleep" else 0,
                "awake_rehearsal_native_rule_steps": 51 if arm == "awake_rehearsal" else 0,
                "strategy_delayed_status": "solved",
                "library_source_trace_length": 32,
                "boot_seconds": 0.2, "graph_node_growth": 10,
                "graph_estimated_bytes_end": 1000, "evidence_exposures": 3,
                "world_actions": 0, "world_sha256": "same", "world_access_sha256": "same",
                "input_audit": {"answer_fields_absent": True,
                                "no_hidden_delayed_strategy": True,
                                "same_primitive_access_hash": "same"},
                "sleep": {"replay_traces": int(arm == "replay_only"),
                          "receipt_audit": ([{"stage": "replay", "provenance_kind": "offline_sleep_stage",
                                               "observation_status": "not_observed",
                                               "shared_budget_debit": 1},
                                              {"stage": "library", "provenance_kind": "offline_sleep_stage",
                                               "observation_status": "not_observed",
                                               "shared_budget_debit": 1}]
                                              if arm == "full_sleep" else [])},
            })
        records.append({"status": "COMPLETED", "family": "interrupt_restart_control",
                        "seed": 50, "foreground_pending": True,
                        "restart_cursor_persisted": True, "restart_resumed_next_stage": True,
                        "same_epoch_no_duplicate_receipt": True,
                        "budget_remaining_after_resume": 5,
                        "budget_remaining_after_repeat": 5})
        result = analyze({"schema": "pmb-scorecard-v1",
                          "metadata": {"phase": "linear-p13-v1", "split": "development",
                                       "seed_allocation": {"paired_streams_per_arm": 1,
                                                            "interrupt_restart_controls": 1}},
                          "records": records})
        assert result["integrity_failures"] == 0
        assert result["primary_status"] == "FAIL"  # identical task accuracy is retained
        assert result["library_status"] == "PASS"
        print("linear_p13 analyzer self-check: PASS")
        return
    if args.scorecard is None:
        parser.error("scorecard is required unless --self-check is used")
    print(json.dumps(analyze(json.loads(args.scorecard.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
