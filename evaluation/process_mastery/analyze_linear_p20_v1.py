"""Fail-closed structural analysis for P20 development panels.

This analyzer deliberately labels all results DEVELOPMENT_ONLY. It does not
estimate the preregistered efficacy criterion and rejects held-out payloads
until the frozen analyzer implementation is added with the preregistration.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

TARGET_ARMS = {"fresh", "mapped_source", "mismatched_source"}
SOCIAL_ARMS = {"observation", "demonstration", "instruction", "reward_only"}
CONTROL_KINDS = {"wrong_frame", "missing_step", "body_mismatch", "false_description"}


def analyze(payload):
    failures = []
    if payload.get("phase") != "linear-p20-v1":
        failures.append("phase_mismatch")
    if payload.get("split") != "development" or payload.get("heldout_accessed") is not False:
        failures.append("non_development_or_holdout_access")
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
    if social.get("status") != "development_only" or target.get("status") != "development_only":
        failures.append("panel_status_mismatch")

    return {
        "phase": "linear-p20-v1", "status": "PASS" if not failures else "FAIL",
        "evidence_class": "DEVELOPMENT_ONLY", "primary_status": "NOT_ESTIMATED",
        "counts": {"target_rows": len(target_rows), "social_rows": len(social_rows),
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
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.input.read_text(encoding="utf-8")))
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
