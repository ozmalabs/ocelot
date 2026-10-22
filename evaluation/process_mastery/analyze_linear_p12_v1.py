"""Integrity checks and preregistered verdicts for linear_p12_v1."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def analyze(payload):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("scorecard has no records")
    if any(r.get("status") not in {"NOT_RUN", "UNSUPPORTED", "TIMEOUT", "FAILED", "COMPLETED"}
           for r in records):
        raise ValueError("invalid trial status")
    social = [r for r in records if r.get("family") == "social_acquisition"]
    rebuild = [r for r in records if r.get("family") == "explain_rebuild"]
    if not social or not rebuild:
        raise ValueError("missing social acquisition or isolated rebuild family")

    grouped = defaultdict(list)
    for row in social:
        grouped[(row.get("seed"), row.get("control"))].append(row)
    pair_hash_failures = 0
    missing_arm_pairs = 0
    for (seed, control), rows in grouped.items():
        if control is not None:
            continue
        by_arm = {row.get("profile"): row for row in rows}
        if not {"observation", "demonstration", "instruction", "reward_only"}.issubset(by_arm):
            missing_arm_pairs += 1
            continue
        pair_hash_failures += (len({r.get("world_access_sha256") for r in by_arm.values()}) != 1
                               or len({r.get("agent_input_audit", {}).get(
                                   "common_model_access_sha256") for r in by_arm.values()}) != 1)

    allocation = payload.get("metadata", {}).get("seed_allocation", {})
    expected_social = int(allocation.get("social_per_arm", 0))
    expected_social_controls = int(allocation.get("controls_each", 0))
    expected_rebuild = int(allocation.get("rebuild", 0))
    expected_redaction = int(allocation.get("rebuild_redaction_controls_each", 0))
    allocation_failures = 0
    if not all((expected_social, expected_social_controls, expected_rebuild, expected_redaction)):
        allocation_failures += 1
    for arm in ("observation", "demonstration", "instruction", "reward_only"):
        allocation_failures += sum(r.get("profile") == arm and not r.get("control")
                                   for r in social) != expected_social
    for control in ("shuffled", "missing", "body_mismatch"):
        allocation_failures += sum(r.get("control") == control for r in social) != expected_social_controls
    allocation_failures += sum(not r.get("control") for r in rebuild) != expected_rebuild
    for control in ("source_ids_removed", "source_expressions_removed"):
        allocation_failures += sum(r.get("control") == control for r in rebuild) != expected_redaction

    social_audit_failures = sum(
        r.get("agent_input_audit", {}).get("target_absent") is not True
        or not r.get("agent_input_audit", {}).get("common_model_access_sha256")
        or r.get("agent_input_audit", {}).get("equal_world_hash") != r.get("world_access_sha256")
        or r.get("evidence_opportunities") != 8
        for r in social)
    rebuild_audit_failures = sum(
        r.get("agent_input_audit", {}).get("source_schema_absent") is not True
        or r.get("agent_input_audit", {}).get("source_ast_absent") is not True
        or r.get("agent_input_audit", {}).get("only_public_explanation_and_shared_vocabulary") is not True
        or r.get("source_leakage") is not False
        for r in rebuild)
    redaction_expectations = {
        "source_ids_removed": {"source_schema_id", "source_actor_id", "source_process_id"},
        "source_expressions_removed": {"source_ast", "source_fingerprint", "candidate_strategy"},
    }
    redaction_controls = {}
    redaction_failures = 0
    for control, expected_fields in redaction_expectations.items():
        rows = [r for r in rebuild if r.get("control") == control]
        failures = sum(set(r.get("redacted_forbidden_fields", [])) != expected_fields
                       or r.get("effect_agreement") is not True
                       or r.get("source_leakage") is not False for r in rows)
        redaction_failures += failures
        redaction_controls[control] = {"n": len(rows), "failures": failures,
                                       "effect_agreement_rate": (
                                           sum(r.get("effect_agreement") is True for r in rows) / len(rows)
                                           if rows else None)}
    completion_failures = sum(r.get("status") != "COMPLETED" for r in social + rebuild)
    false_own_grounding = sum(int(r.get("false_own_grounding", 1)) for r in social)
    unverified_candidate_adoptions = sum(
        r.get("unverified_adoption_count", 1) > 0 for r in social)

    arms = {}
    for arm in ("observation", "demonstration", "instruction", "reward_only"):
        rows = [r for r in social if r.get("profile") == arm and not r.get("control")]
        successes = sum(r.get("own_trial_success") is True for r in rows)
        arms[arm] = {"n": len(rows), "own_trial_successes": successes,
                     "own_trial_rate": successes / len(rows) if rows else None,
                     "adoptions": sum(r.get("candidate_adoption") in {
                         "adopted", "adopted_reward_candidate"} for r in rows),
                     "mean_evidence_opportunities": (
                         sum(r.get("evidence_opportunities", 0) for r in rows) / len(rows)
                         if rows else None),
                     "mean_informative_opportunities": (
                         sum(r.get("informative_opportunities", 0) for r in rows) / len(rows)
                         if rows else None),
                     "mean_world_action_calls": (
                         sum(r.get("world_action_calls", 0) for r in rows) / len(rows)
                         if rows else None),
                     "mean_boot_seconds": (sum(r.get("boot_seconds", 0) for r in rows) / len(rows)
                                           if rows else None),
                     "mean_graph_node_growth": (
                         sum(r.get("graph_node_growth", 0) for r in rows) / len(rows)
                         if rows else None),
                     "mean_graph_estimated_bytes_growth": (
                         sum(r.get("graph_estimated_bytes_end", 0)
                             - r.get("graph_estimated_bytes_start", 0) for r in rows) / len(rows)
                         if rows else None),
                     "mean_budget_remaining": (
                         sum(r.get("budget_remaining_graph", 0) for r in rows) / len(rows)
                         if rows else None),
                     "mean_budget_request_debits": (
                         sum(r.get("budget_request_debits", 0) for r in rows) / len(rows)
                         if rows else None),
                     "mean_receipts": (sum(len(r.get("receipt_ids", [])) for r in rows) / len(rows)
                                       if rows else None)}
    source_rows = [r for r in social if r.get("profile") in {
        "observation", "demonstration", "instruction"} and not r.get("control")]
    source_rate = (sum(r.get("own_trial_success") is True for r in source_rows) / len(source_rows)
                   if source_rows else None)
    reward_rate = arms["reward_only"]["own_trial_rate"]
    social_gain = source_rate - reward_rate if source_rate is not None and reward_rate is not None else None

    controls = {kind: [r for r in social if r.get("control") == kind] for kind in
                ("shuffled", "missing", "body_mismatch")}
    control_summary = {kind: {"n": len(rows),
                              "false_adoptions": sum(r.get("candidate_adoption") in {"adopted", "false_adoption"}
                                                      for r in rows),
                              "own_trial_successes": sum(r.get("own_trial_success") is True for r in rows),
                              "unverified_candidates": sum(r.get("unverified_candidate_count", 1) > 0
                                                            for r in rows)}
                       for kind, rows in controls.items()}
    control_failures = sum(x["false_adoptions"] + x["own_trial_successes"] + x["unverified_candidates"]
                           for x in control_summary.values())
    rebuild_agreement = (sum(r.get("effect_agreement") is True for r in rebuild) / len(rebuild))
    rebuild_adoption = (sum(r.get("adopted_process") is True for r in rebuild) / len(rebuild))
    rebuild_tokens = sum(r.get("explanation_tokens", 0) for r in rebuild) / len(rebuild)
    rebuild_telemetry = {
        "mean_boot_seconds": sum(r.get("boot_seconds", 0) for r in rebuild) / len(rebuild),
        "mean_graph_node_growth": sum(r.get("graph_node_growth", 0) for r in rebuild) / len(rebuild),
        "mean_graph_estimated_bytes_growth": sum(
            r.get("graph_estimated_bytes_end", 0) - r.get("graph_estimated_bytes_start", 0)
            for r in rebuild) / len(rebuild),
        "mean_budget_remaining": sum(r.get("budget_remaining_graph", 0) for r in rebuild) / len(rebuild),
        "mean_budget_request_debits": sum(r.get("budget_request_debits", 0)
                                           for r in rebuild) / len(rebuild),
        "mean_explanation_tokens": rebuild_tokens,
        "mean_evidence_exposures": sum(r.get("evidence_exposures", 0) for r in rebuild) / len(rebuild),
    }
    integrity_failures = (pair_hash_failures + missing_arm_pairs + social_audit_failures
                          + rebuild_audit_failures + completion_failures
                          + false_own_grounding + unverified_candidate_adoptions
                          + redaction_failures + allocation_failures)
    if integrity_failures:
        primary = "INVALID"
    elif social_gain is None:
        primary = "NOT_ESTABLISHED"
    elif social_gain >= 0.20 and control_failures == 0:
        primary = "PASS"
    else:
        primary = "FAIL"
    rebuild_status = ("INVALID" if rebuild_audit_failures or completion_failures
                      else "PASS" if rebuild_agreement >= 0.95 and rebuild_adoption >= 0.95
                      else "FAIL")
    return {"schema": "pmb-linear-p12-v1-analysis-v1",
            "phase": payload.get("metadata", {}).get("phase"),
            "split": payload.get("metadata", {}).get("split"),
            "n_records": len(records), "social_records": len(social),
            "rebuild_records": len(rebuild), "arms": arms,
            "pooled_social_own_trial_rate": source_rate,
            "reward_only_own_trial_rate": reward_rate,
            "social_own_trial_gain": social_gain,
            "paired_world_hash_failures": pair_hash_failures,
            "allocation_failures": allocation_failures,
            "missing_arm_pairs": missing_arm_pairs,
            "social_agent_input_audit_failures": social_audit_failures,
            "rebuild_agent_input_audit_failures": rebuild_audit_failures,
            "completion_failures": completion_failures,
            "false_own_grounding": false_own_grounding,
            "unverified_candidate_adoptions": unverified_candidate_adoptions,
            "controls": control_summary, "control_failures": control_failures,
            "rebuild_redaction_controls": redaction_controls,
            "rebuild_effect_agreement": rebuild_agreement,
            "rebuild_adoption_rate": rebuild_adoption,
            "mean_explanation_tokens": rebuild_tokens,
            "rebuild_telemetry": rebuild_telemetry,
            "primary_status": primary,
            "rebuild_status": rebuild_status,
            "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED",
            "scope": "bounded_synthetic_single_primitive_mechanism"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path, nargs="?")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        sample = {"schema": "pmb-scorecard-v1", "metadata": {"phase": "linear-p12-v1",
                                                                   "split": "development",
                                                                   "seed_allocation": {
                                                                       "social_per_arm": 1,
                                                                       "controls_each": 1,
                                                                       "rebuild": 1,
                                                                       "rebuild_redaction_controls_each": 1}},
                  "records": []}
        for arm, success in (("observation", True), ("demonstration", True),
                             ("instruction", True), ("reward_only", False)):
            sample["records"].append({
                "status": "COMPLETED", "family": "social_acquisition", "seed": 1,
                "profile": arm, "split": "development", "world_access_sha256": "same",
                "outcome": "own_trial_success" if success else "own_trial_failure",
                "own_trial_success": success, "candidate_adoption": "adopted" if success else "no_social_input",
                "evidence_opportunities": 8, "unverified_candidate_count": 0,
                "unverified_adoption_count": 0, "false_own_grounding": 0,
                "agent_input_audit": {"target_absent": True, "equal_world_hash": "same",
                                       "common_model_access_sha256": "same-models"}})
        for control in ("shuffled", "missing", "body_mismatch"):
            sample["records"].append({
                "status": "COMPLETED", "family": "social_acquisition", "seed": 4,
                "profile": "demonstration", "split": "development", "control": control,
                "world_access_sha256": "control-world", "own_trial_success": False,
                "candidate_adoption": "rejected_control", "evidence_opportunities": 8,
                "unverified_candidate_count": 0, "unverified_adoption_count": 0,
                "false_own_grounding": 0,
                "agent_input_audit": {"target_absent": True,
                                       "equal_world_hash": "control-world",
                                       "common_model_access_sha256": "same-models"}})
        sample["records"].append({
            "status": "COMPLETED", "family": "explain_rebuild", "seed": 2,
            "profile": "isolated_receiver", "split": "development", "effect_agreement": True,
            "adopted_process": True, "source_leakage": False,
            "agent_input_audit": {"source_schema_absent": True, "source_ast_absent": True,
                                   "only_public_explanation_and_shared_vocabulary": True}})
        for control, fields in (
            ("source_ids_removed", ["source_schema_id", "source_actor_id", "source_process_id"]),
            ("source_expressions_removed", ["source_ast", "source_fingerprint", "candidate_strategy"])):
            sample["records"].append({
                "status": "COMPLETED", "family": "explain_rebuild", "seed": 3,
                "profile": "isolated_receiver", "split": "development", "control": control,
                "effect_agreement": True, "adopted_process": True, "source_leakage": False,
                "redacted_forbidden_fields": fields,
                "agent_input_audit": {"source_schema_absent": True, "source_ast_absent": True,
                                       "only_public_explanation_and_shared_vocabulary": True}})
        result = analyze(sample)
        assert result["primary_status"] == "PASS"
        assert result["rebuild_status"] == "PASS"
        assert result["paired_world_hash_failures"] == 0
        print("linear_p12_v1 analyzer self-check: PASS")
        return
    if args.scorecard is None:
        parser.error("scorecard is required unless --self-check is used")
    print(json.dumps(analyze(json.loads(args.scorecard.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
