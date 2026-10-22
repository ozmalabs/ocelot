"""Fail-closed analysis of frozen P20 panels and development checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from evaluation.process_mastery.linear_p20_v1 import (
    PROVENANCE_FILES, ROOT, _verify_preregistration,
)

TARGET_ARMS = {"fresh", "mapped_source", "mismatched_source"}
SOCIAL_ARMS = {"observation", "demonstration", "instruction", "reward_only"}
CONTROL_KINDS = {"wrong_frame", "missing_step", "body_mismatch", "false_description"}


def analyze(payload, *, preregistration=None):
    failures = []
    split = payload.get("split")
    heldout = split == "heldout"
    if payload.get("phase") != "linear-p20-v1":
        failures.append("phase_mismatch")
    if split not in {"development", "heldout"}:
        failures.append("unknown_split")
    if (not heldout and payload.get("heldout_accessed") is not False):
        failures.append("development_holdout_access")
    frozen = None
    if heldout:
        if preregistration is None:
            failures.append("heldout_analysis_requires_preregistration")
        else:
            try:
                frozen, _current_provenance, expected_allocation, expected_sha = (
                    _verify_preregistration(Path(preregistration).resolve()))
                if payload.get("preregistration_sha256") != hashlib.sha256(
                        Path(preregistration).read_bytes()).hexdigest():
                    failures.append("preregistration_hash_mismatch")
                if payload.get("allocation_sha256") != expected_sha:
                    failures.append("heldout_allocation_mismatch")
                if payload.get("allocation_plan") != expected_allocation:
                    failures.append("heldout_allocation_content_mismatch")
                if payload.get("status") != "heldout_pending_analysis":
                    failures.append("heldout_payload_status_mismatch")
            except Exception as exc:
                failures.append(f"preregistration_validation_failed:{type(exc).__name__}")
    provenance = payload.get("provenance", {})
    runtime = provenance.get("runtime_attestation", {})
    source_hashes = provenance.get("source_file_sha256", {})
    current_source = hashlib.sha256()
    source_match = set(source_hashes) == set(PROVENANCE_FILES)
    if source_match:
        for relative in PROVENANCE_FILES:
            path = ROOT / relative
            if not path.is_file():
                source_match = False
                break
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != source_hashes.get(relative):
                source_match = False
            current_source.update(relative.encode() + b"\0" + data + b"\0")
    if (runtime.get("status") != "ATTESTED"
            or runtime.get("native_symbols_bound") is not True
            or runtime.get("build_sources_match") is not True
            or runtime.get("wrapper_sha256") != provenance.get("wrapper_sha256")
            or runtime.get("loaded_extension_sha256")
            != provenance.get("loaded_extension_sha256")
            or runtime.get("build_receipt_sha256") != provenance.get("build_receipt_sha256")
            or not provenance.get("source_bundle_sha256")
            or not source_match
            or current_source.hexdigest() != provenance.get("source_bundle_sha256")
            or not provenance.get("wrapper_sha256")
            or not provenance.get("loaded_extension_sha256")
            or not provenance.get("build_receipt_sha256")):
        failures.append("runtime_provenance_unattested")
    if heldout and frozen:
        for field in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
                      "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                      "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256"):
            if frozen.get(field) != provenance.get(field):
                failures.append(f"frozen_provenance_mismatch:{field}")
    allocation_plan = payload.get("allocation_plan", {})
    allocation_sha = hashlib.sha256(json.dumps(
        allocation_plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if allocation_sha != payload.get("allocation_sha256"):
        failures.append("allocation_digest_mismatch")
    if allocation_plan.get("split") != split:
        failures.append("allocation_split_mismatch")
    if allocation_plan.get("primary") != {
            "metric": "normalized_learning_curve_auc",
            "comparison": "mapped_source_minus_fresh", "minimum_gain": 0.20}:
        failures.append("primary_criterion_mismatch")
    target = payload.get("target_learning", {})
    expected_pairs = set(target.get("domain_pairs", []))
    streams_per_pair = payload.get("allocation", {}).get("target_streams_per_pair")
    target_rows = target.get("records", [])
    target_keys = set()
    target_counts = Counter()
    for row in target_rows:
        arm, stream_id = row.get("arm"), row.get("stream_id", "")
        pair = next((name for name in expected_pairs if name in stream_id), None)
        key = (pair, arm, stream_id)
        if pair is None or arm not in TARGET_ARMS:
            failures.append(f"unexpected_target_row:{stream_id}:{arm}")
        if key in target_keys:
            failures.append(f"duplicate_target_row:{stream_id}:{arm}")
        target_keys.add(key)
        target_counts[(pair, arm)] += 1
        if row.get("target_actions", 0) < 0 or row.get("native_rule_steps", 0) <= 0:
            failures.append(f"invalid_target_resources:{stream_id}:{arm}")
        if arm == "mapped_source" and (row.get("map_status") != "verified"
                                         or row.get("target_effect_status") != "verified"):
            failures.append(f"mapped_source_missing_receipt:{stream_id}")
        if arm == "mismatched_source" and row.get("map_status") != "abstained_conflicting_source":
            failures.append(f"mismatched_source_did_not_abstain:{stream_id}")
    for pair in expected_pairs:
        for arm in TARGET_ARMS:
            if target_counts[(pair, arm)] != streams_per_pair:
                failures.append(f"target_allocation_mismatch:{pair}:{arm}")
    planned_target_keys = {(row.get("domain_pair"), row.get("stream_id"), arm)
                           for row in allocation_plan.get("target", [])
                           for arm in row.get("arms", [])}
    observed_target_keys = {(next((name for name in expected_pairs
                                   if name in row.get("stream_id", "")), None),
                             row.get("stream_id"), row.get("arm"))
                            for row in target_rows}
    if observed_target_keys != planned_target_keys:
        failures.append("target_rows_do_not_match_allocation")
    if set(target.get("curves", {})) != TARGET_ARMS:
        failures.append("target_curve_arm_mismatch")
    if set(target.get("normalized_auc", {})) != TARGET_ARMS:
        failures.append("target_auc_arm_mismatch")

    social = payload.get("social_acquisition", {})
    social_per_arm = payload.get("allocation", {}).get("social_streams_per_arm")
    social_rows = social.get("records", [])
    social_counts = Counter(row.get("arm") for row in social_rows)
    social_keys = set()
    social_outcomes = Counter()
    for row in social_rows:
        arm, stream = row.get("arm"), row.get("stream_id")
        if arm not in SOCIAL_ARMS:
            failures.append(f"unexpected_social_arm:{arm}")
        if (arm, stream) in social_keys:
            failures.append(f"duplicate_social_row:{arm}:{stream}")
        social_keys.add((arm, stream))
        social_outcomes[(arm, row.get("outcome"))] += 1
        if row.get("budget_debits", 0) < 1 or row.get("graph_nodes", 0) <= 0:
            failures.append(f"missing_social_accounting:{arm}:{stream}")
        if arm == "reward_only":
            if (row.get("outcome") != "abstained_underidentified"
                    or row.get("own_actions") != 0 or row.get("solved") is not False):
                failures.append(f"reward_only_false_inference:{stream}")
        elif (row.get("outcome") != "verified_and_executed" or row.get("solved") is not True
              or row.get("verification_status") != "VERIFIED"
              or row.get("own_actions") != 2):
            failures.append(f"social_execution_failure:{arm}:{stream}")
    for arm in SOCIAL_ARMS:
        if social_counts[arm] != social_per_arm:
            failures.append(f"social_allocation_mismatch:{arm}")
    planned_social = {(row.get("arm"), row.get("stream_id"))
                      for row in allocation_plan.get("social", [])}
    if {(row.get("arm"), row.get("stream_id")) for row in social_rows} != planned_social:
        failures.append("social_rows_do_not_match_allocation")

    controls = payload.get("structural_controls", [])
    control_per_kind = payload.get("allocation", {}).get("social_controls_per_kind")
    control_counts = Counter(row.get("kind") for row in controls)
    if set(control_counts) - CONTROL_KINDS:
        failures.append("unexpected_control_kind")
    for kind in CONTROL_KINDS:
        if control_counts[kind] != control_per_kind:
            failures.append(f"control_allocation_mismatch:{kind}")
    for row in controls:
        if (row.get("status") != "PASS" or row.get("state_unchanged") is not True
                or row.get("false_candidate_count") != 0):
            failures.append(f"control_failure:{row.get('kind')}:{row.get('control_id')}")
    if {(row.get("kind"), row.get("control_id")) for row in controls} != {
            (row.get("kind"), row.get("control_id"))
            for row in allocation_plan.get("controls", [])}:
        failures.append("control_rows_do_not_match_allocation")
    expected_panel_status = "heldout_unanalyzed" if heldout else "development_only"
    if (social.get("status") != expected_panel_status
            or target.get("status") != expected_panel_status):
        failures.append("panel_status_mismatch")

    explanations = payload.get("explanation_rebuild", {})
    explanation_rows = explanations.get("records", [])
    expected_explanations = payload.get("allocation", {}).get("explanation_streams")
    if (explanations.get("status") != expected_panel_status
            or len(explanation_rows) != expected_explanations):
        failures.append("explanation_allocation_mismatch")
    for row in explanation_rows:
        if (row.get("status") != "verified_and_adopted"
                or row.get("fidelity_match") is not True
                or row.get("counterexample_rejected") is not True
                or row.get("adopted_process_count") != 1
                or row.get("source_ast_included") is not False
                or row.get("receiver_source_leakage") is not False
                or row.get("semantic_steps") != 2
                or row.get("fresh_world_actions") != 2
                or row.get("source_budget_debits") != 1
                or row.get("receiver_budget_debits") != 2
                or row.get("source_graph_bytes", 0) <= 0
                or row.get("receiver_graph_bytes", 0) <= 0):
            failures.append(f"explanation_failure:{row.get('trial_id')}")
    if {row.get("trial_id") for row in explanation_rows} != set(
            allocation_plan.get("explanations", [])):
        failures.append("explanation_rows_do_not_match_allocation")

    effect = target.get("paired_auc_difference_mapped_minus_fresh")
    if not isinstance(effect, (int, float)):
        failures.append("primary_effect_missing")
    if not heldout:
        primary_status = "NOT_ESTIMATED"
        evidence_class = "DEVELOPMENT_ONLY"
    elif failures:
        primary_status = "NOT_ESTABLISHED"
        evidence_class = "HELDOUT_INVALID"
    else:
        primary_status = "PASS" if effect >= 0.20 else "FAIL"
        evidence_class = "HELDOUT"
    return {
        "phase": "linear-p20-v1", "status": "PASS" if not failures else "FAIL",
        "evidence_class": evidence_class, "primary_status": primary_status,
        "provenance_status": "ATTESTED" if "runtime_provenance_unattested" not in failures
                            else "NOT_ESTABLISHED",
        "primary": {"comparison": "mapped_source_minus_fresh",
                    "metric": "normalized_learning_curve_auc",
                    "observed_gain": effect, "threshold": 0.20,
                    "status": primary_status},
        "counts": {"target_rows": len(target_rows), "social_rows": len(social_rows),
                   "explanation_rows": len(explanation_rows),
                   "controls": len(controls), "target_by_pair_arm": {
                       f"{pair}/{arm}": target_counts[(pair, arm)]
                       for pair in sorted(expected_pairs) for arm in sorted(TARGET_ARMS)},
                   "social_by_arm": dict(social_counts),
                   "social_outcomes": {f"{arm}/{outcome}": count
                                       for (arm, outcome), count in social_outcomes.items()},
                   "control_by_kind": dict(control_counts)},
        "target_learning": {"normalized_auc": target.get("normalized_auc"),
                            "paired_auc_difference_mapped_minus_fresh":
                                target.get("paired_auc_difference_mapped_minus_fresh")},
        "registered_development_criterion": allocation_plan.get("primary"),
        "failures": failures,
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
