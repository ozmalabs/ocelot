"""Fail-closed P21 structural and registered-effect analysis."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from evaluation.process_mastery.linear_p21_v1 import (
    CAPACITIES, CURRICULUM_ARMS, SLEEP_ARMS, ROOT, _digest, _verify_preregistration,
    allocation, provenance,
)


def _auc(row):
    curve = row.get("curve", [])
    if [p.get("target_interactions") for p in curve] != [0, 1, 2]:
        return None
    values = [p.get("success") for p in curve]
    if any(v not in (0, 1) for v in values):
        return None
    return sum((values[i] + values[i + 1]) / 2 for i in range(2)) / 2


def _mean(values):
    return sum(values) / len(values) if values else None


def analyze(payload, *, preregistration=None):
    failures = []
    split = payload.get("split")
    heldout = split == "heldout"
    if payload.get("phase") != "linear-p21-v1":
        failures.append("phase_mismatch")
    if split not in {"development", "heldout"}:
        failures.append("unknown_split")
    if not heldout and payload.get("heldout_accessed") is not False:
        failures.append("development_holdout_access")
    frozen = None
    expected_plan = None
    if heldout:
        if preregistration is None:
            failures.append("heldout_analysis_requires_preregistration")
        else:
            try:
                frozen, _current, expected_plan, expected_hash = _verify_preregistration(
                    Path(preregistration).resolve())
                prereg_path = Path(preregistration).resolve()
                if payload.get("preregistration_sha256") != hashlib.sha256(
                        prereg_path.read_bytes()).hexdigest():
                    failures.append("preregistration_hash_mismatch")
                if payload.get("allocation_sha256") != expected_hash:
                    failures.append("allocation_hash_mismatch")
                if payload.get("allocation_plan") != expected_plan:
                    failures.append("allocation_content_mismatch")
                if payload.get("status") != "heldout_pending_analysis":
                    failures.append("heldout_status_mismatch")
            except Exception as exc:
                failures.append(f"preregistration_validation_failed:{type(exc).__name__}")
    current = provenance()
    provenance_payload = payload.get("provenance", {})
    if provenance_payload.get("source_file_sha256") != current.get("source_file_sha256"):
        failures.append("source_hash_mismatch")
    for key in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
                "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256"):
        if provenance_payload.get(key) != current.get(key):
            failures.append(f"provenance_mismatch:{key}")
    runtime = current.get("runtime_attestation", {})
    if runtime.get("status") != "ATTESTED" or runtime.get("issues"):
        failures.append("runtime_not_attested")
    plan = payload.get("allocation_plan", {})
    if plan.get("split") != split or payload.get("allocation_sha256") != _digest(plan):
        failures.append("allocation_digest_mismatch")
    if heldout and plan != expected_plan:
        failures.append("frozen_allocation_mismatch")

    sleep_rows = payload.get("sleep_retention", {}).get("records", [])
    curriculum_rows = payload.get("curriculum", {}).get("records", [])
    sleep_expected = {
        (stream, arm)
        for stratum in plan.get("sleep_streams", [])
        for stream in stratum.get("stream_ids", [])
        for arm in stratum.get("arms", [])
    }
    curriculum_expected = {
        (stream, selector)
        for stratum in plan.get("curriculum_streams", [])
        for stream in stratum.get("stream_ids", [])
        for selector in stratum.get("arms", [])
    }
    sleep_keys = [(r.get("stream_id"), r.get("arm")) for r in sleep_rows]
    curriculum_keys = [(r.get("stream_id"), r.get("selector")) for r in curriculum_rows]
    if len(sleep_keys) != len(set(sleep_keys)) or set(sleep_keys) != sleep_expected:
        failures.append("sleep_stream_allocation_mismatch")
    if (len(curriculum_keys) != len(set(curriculum_keys))
            or set(curriculum_keys) != curriculum_expected):
        failures.append("curriculum_stream_allocation_mismatch")

    for row in sleep_rows:
        cap = row.get("capacity_bytes")
        memory = row.get("memory", {})
        if cap not in CAPACITIES or memory.get("capacity_bytes") != cap:
            failures.append("memory_capacity_mismatch")
        if memory.get("used_bytes", cap + 1) > cap:
            failures.append("memory_over_capacity")
        if row.get("source_receipts_allocated") != 2:
            failures.append("source_receipt_exposure_mismatch")
        if row.get("source_receipts_retrieved") != 2:
            failures.append("delayed_source_unavailable")
        if _auc(row) is None:
            failures.append("learning_curve_invalid")
        if row.get("status") != "COMPLETED":
            failures.append("sleep_arm_incomplete")
        lifecycle = row.get("lifecycle", {})
        arm = row.get("arm")
        if arm == "full_sleep":
            required = {"replay", "consolidate", "decay", "library", "recombine"}
            if not lifecycle.get("completed") or not required.issubset(set(lifecycle.get("stages", []))):
                failures.append("native_sleep_stage_incomplete")
            chunk = lifecycle.get("memory_chunk", {})
            if chunk.get("status") != "stored":
                failures.append("sleep_chunk_missing")
        elif arm == "replay_only":
            if lifecycle.get("sleep_receipts") != 0 or lifecycle.get("replay_traces", 0) < 1:
                failures.append("replay_only_adapter_invalid")
        elif arm == "awake_rehearsal":
            if lifecycle.get("awake_rehearsal_steps", 0) <= 0:
                failures.append("awake_rehearsal_missing")
            if lifecycle.get("memory_chunk", {}).get("status") != "stored":
                failures.append("awake_chunk_missing")
        elif arm == "no_offline":
            if lifecycle.get("sleep_receipts", 0) or lifecycle.get("replay_traces", 0):
                failures.append("no_offline_treatment_contaminated")
        if row.get("budget_debit") is None or row.get("graph_bytes", 0) <= 0:
            failures.append("sleep_resource_accounting_missing")

    for row in curriculum_rows:
        if row.get("status") != "COMPLETED":
            failures.append("curriculum_arm_incomplete")
        if row.get("outcome_count") != 1 or row.get("task_status") != "completed":
            failures.append("curriculum_not_receipt_completed")
        if row.get("target_actions") != 2 or row.get("budget_remaining") is None:
            failures.append("curriculum_resource_mismatch")
        if row.get("capacity_bytes") not in CAPACITIES:
            failures.append("curriculum_capacity_mismatch")

    # Comparators must receive equal real work, not merely matching labels.
    sleep_index = {(r.get("stream_id"), r.get("arm")): r for r in sleep_rows}
    for stream in {key[0] for key in sleep_keys}:
        full = sleep_index.get((stream, "full_sleep"))
        awake = sleep_index.get((stream, "awake_rehearsal"))
        if full and awake:
            full_steps = full.get("lifecycle", {}).get("native_rule_steps", 0)
            awake_steps = awake.get("lifecycle", {}).get("awake_rehearsal_steps", 0)
            if not full_steps or not awake_steps or abs(full_steps - awake_steps) / full_steps > 0.05:
                failures.append("awake_compute_mismatch")
    curriculum_index = {(r.get("stream_id"), r.get("selector")): r
                        for r in curriculum_rows}
    for stream in {key[0] for key in curriculum_keys}:
        paired = [curriculum_index.get((stream, arm)) for arm in CURRICULUM_ARMS]
        if any(row is None for row in paired):
            continue
        actions = [row.get("target_actions") for row in paired]
        steps = [row.get("native_rule_steps") for row in paired]
        if len(set(actions)) != 1 or len(set(steps)) != 1:
            failures.append("curriculum_work_mismatch")

    controls = payload.get("structural_controls", [])
    expected_controls = set(plan.get("control_ids", []))
    if ({row.get("control_id") for row in controls} != expected_controls
            or len(controls) != len(expected_controls)
            or any(row.get("status") != "PASS"
                   or row.get("sealed_eval_id_exposed")
                   or row.get("answer_fields_exposed")
                   or row.get("over_capacity_readthrough") for row in controls)):
        failures.append("structural_control_failure")

    sleep_by = {}
    for cap in CAPACITIES:
        for arm in SLEEP_ARMS:
            rows = [r for r in sleep_rows if r.get("capacity_bytes") == cap and r.get("arm") == arm]
            sleep_by[(cap, arm)] = {
                "n": len(rows), "mean_auc": _mean([_auc(r) for r in rows if _auc(r) is not None]),
                "delayed_accuracy": _mean([r.get("delayed_accuracy", 0) for r in rows]),
                "new_task_accuracy": _mean([r.get("new_task_accuracy", 0) for r in rows]),
                "mean_budget_debit": _mean([r.get("budget_debit", 0) for r in rows]),
                "mean_graph_bytes": _mean([r.get("graph_bytes", 0) for r in rows]),
                "mean_memory_bytes": _mean([r.get("memory", {}).get("used_bytes", 0) for r in rows]),
            }
    sleep_differences = []
    paired_new_losses = []
    for stream in {key[0] for key in sleep_keys}:
        full = sleep_index.get((stream, "full_sleep"))
        replay = sleep_index.get((stream, "replay_only"))
        if full and replay and _auc(full) is not None and _auc(replay) is not None:
            sleep_differences.append(_auc(full) - _auc(replay))
            paired_new_losses.append(replay.get("new_task_accuracy", 0)
                                     - full.get("new_task_accuracy", 0))
    sleep_effect = _mean(sleep_differences)
    sleep_new_loss = _mean(paired_new_losses)
    if not isinstance(sleep_effect, (int, float)) or not math.isfinite(sleep_effect):
        sleep_status = "NOT_ESTABLISHED"
    elif failures:
        sleep_status = "NOT_ESTABLISHED"
    else:
        sleep_status = "PASS" if sleep_effect >= 0.10 and sleep_new_loss <= 0.02 else "FAIL"

    curriculum_by = {}
    for cap in CAPACITIES:
        for selector in CURRICULUM_ARMS:
            rows = [r for r in curriculum_rows if r.get("capacity_bytes") == cap
                    and r.get("selector") == selector]
            curriculum_by[(cap, selector)] = {
                "n": len(rows), "delayed_accuracy": _mean([r.get("delayed_accuracy", 0) for r in rows]),
                "target_actions": _mean([r.get("target_actions", 0) for r in rows]),
                "native_rule_steps": _mean([r.get("native_rule_steps", 0) for r in rows]),
                "graph_bytes": _mean([r.get("graph_bytes", 0) for r in rows]),
            }
    curriculum_differences = []
    by_stream = {(r.get("stream_id"), r.get("selector")): r for r in curriculum_rows}
    for stream in {key[0] for key in curriculum_keys}:
        residual = by_stream.get((stream, "residual"))
        random = by_stream.get((stream, "random"))
        fixed = by_stream.get((stream, "fixed"))
        if residual and random and fixed:
            curriculum_differences.append(
                residual.get("delayed_accuracy", 0)
                - (random.get("delayed_accuracy", 0) + fixed.get("delayed_accuracy", 0)) / 2)
    curriculum_effect = _mean(curriculum_differences)
    curriculum_status = ("NOT_ESTABLISHED" if failures or curriculum_effect is None
                         else "PASS" if curriculum_effect >= 0.10 else "FAIL")
    primary_status = ("NOT_ESTIMATED" if not heldout else sleep_status)
    curriculum_primary = ("NOT_ESTIMATED" if not heldout else curriculum_status)
    return {
        "phase": "linear-p21-v1", "status": "PASS" if not failures else "FAIL",
        "evidence_class": "HELDOUT" if heldout and not failures else
                          "HELDOUT_INVALID" if heldout else "DEVELOPMENT_ONLY",
        "failures": failures, "provenance_status": "ATTESTED"
            if "runtime_not_attested" not in failures else "NOT_ESTABLISHED",
        "sleep_primary": {"comparison": "full_sleep_minus_replay_only",
                          "metric": "normalized_delayed_learning_curve_auc",
                          "observed_gain": sleep_effect, "threshold": 0.10,
                          "new_task_loss": sleep_new_loss, "maximum_new_task_loss": 0.02,
                          "status": primary_status},
        "curriculum_primary": {"comparison": "residual_minus_mean_random_fixed",
                               "metric": "delayed_novel_task_accuracy",
                               "observed_gain": curriculum_effect, "threshold": 0.10,
                               "status": curriculum_primary},
        "counts": {"sleep_rows": len(sleep_rows), "curriculum_rows": len(curriculum_rows),
                   "controls": len(controls)},
        "sleep_by_capacity_arm": {f"{cap}:{arm}": value
                                  for (cap, arm), value in sleep_by.items()},
        "curriculum_by_capacity_selector": {f"{cap}:{selector}": value
                                             for (cap, selector), value in curriculum_by.items()},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preregistration", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.input.read_text(encoding="utf-8")),
                     preregistration=args.preregistration)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
