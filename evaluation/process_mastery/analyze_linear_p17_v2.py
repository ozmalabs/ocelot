"""Integrity, provenance and efficacy analysis for the P17 later-behavior panel."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs/research/engine_substrate/COGNITION_LINEAR_P17_V2_PREREG.md"
FAMILIES = ("tool_contact", "social_request_repair")
ARMS = ("acquired", "frozen", "shuffled", "no_experience")
CONTROLS = ("orthogonal", "reversal")
ARTIFACT_KEYS = ("source_bundle_sha256", "runner_sha256", "analyzer_sha256",
    "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
    "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256",
    "engine_source_sha256")


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _contract():
    if not PREREG.is_file():
        raise ValueError("P17 standalone preregistration is missing")
    match = re.search(r"```json\s*(\{.*?\})\s*```", PREREG.read_text(), re.S)
    if not match:
        raise ValueError("P17 preregistration has no machine-readable contract")
    return json.loads(match.group(1))


def _check_provenance(metadata):
    actual = metadata.get("artifact_provenance", {})
    missing = [key for key in ARTIFACT_KEYS if not actual.get(key)]
    if missing:
        raise ValueError(f"P17 artifact provenance missing {missing}")
    runtime = actual.get("runtime_attestation", {})
    if (runtime.get("status") != "ATTESTED" or runtime.get("native_symbols_bound") is not True
            or runtime.get("build_sources_match") is not True
            or runtime.get("loaded_extension_sha256") != actual["loaded_extension_sha256"]
            or runtime.get("wrapper_sha256") != actual["wrapper_sha256"]
            or runtime.get("build_receipt_sha256") != actual["build_receipt_sha256"]):
        raise ValueError("P17 runtime attestation does not bind the loaded native artifact")
    if metadata.get("split") == "heldout":
        frozen = _contract()
        mismatches = {k: (actual.get(k), frozen.get("artifacts", {}).get(k))
                      for k in ARTIFACT_KEYS if actual.get(k) != frozen.get("artifacts", {}).get(k)}
        runtime_keys = ("wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                        "build_source_fingerprint")
        runtime_mismatches = {k: (runtime.get(k), frozen.get("runtime", {}).get(k))
                              for k in runtime_keys if runtime.get(k) != frozen.get("runtime", {}).get(k)}
        if mismatches or runtime_mismatches:
            raise ValueError(f"P17 held-out artifact mismatch: artifacts={mismatches}, runtime={runtime_mismatches}")


def _verify_row(row):
    from evaluation.process_mastery.native_world_comparators import NativeWorldAdapter
    from evaluation.process_mastery.qualia_behavior_worlds import task

    world = task(row["family"], int(row["seed"]))
    if _digest(world) != row.get("world_sha256"):
        return False, "world_hash_mismatch"
    access = {k: world[k] for k in ("family", "initial_state", "goal_state",
        "primitive_affordances", "legal_actions_by_state", "feature_key", "feature_family", "feature_value")}
    access_hash = _digest(access)
    if row.get("world_access_sha256") != access_hash:
        return False, "world_access_hash_mismatch"
    audit = row.get("input_audit", {})
    if (audit.get("answer_fields_absent") is not True or audit.get("hidden_solution_absent") is not True
            or audit.get("same_primitive_access_hash") != access_hash):
        return False, "input_audit_failure"
    receipt = row.get("receipt")
    if row.get("actions") == 0:
        if receipt is not None or row.get("receipt_verified") is not False:
            return False, "abstention_receipt_mismatch"
        if row.get("profile") == "acquired":
            return False, "acquired_arm_missing_action"
        return True, None
    if not receipt:
        return False, "action_without_receipt"
    authorization = row.get("authorization")
    if (not authorization or authorization.get("status") != "authorized"
            or authorization.get("action_id") != row.get("action")
            or authorization.get("event_id") != f"event:fresh:{row['seed']}"
            or authorization.get("world_id") != receipt.get("world_id")
            or authorization.get("world_epoch") != receipt.get("world_epoch", 0) - 1):
        return False, "native_action_authorization_mismatch"
    adapter = NativeWorldAdapter.from_task(world, world_id=f"p17:{row['family']}:{row['seed']}")
    adapter.epoch = int(receipt.get("world_epoch", 0))
    if not adapter.verify_receipt(receipt):
        return False, "external_receipt_mismatch"
    if tuple(receipt.get("before_state", ())) != tuple(world["initial_state"]):
        return False, "receipt_wrong_initial_state"
    if row.get("receipt_verified") is not True or receipt.get("action") != row.get("action"):
        return False, "receipt_row_mismatch"
    if row.get("action_correct") is not (row.get("action") == world["expected_action"]):
        return False, "action_score_mismatch"
    expected_prediction = ("goal_reached:" + row["action"] if row.get("action_correct")
                           else "goal_missed:" + row["action"])
    if row.get("prediction_correct") is not (row.get("prediction") == expected_prediction):
        return False, "prediction_score_mismatch"
    return True, None


def analyze(payload, *, _skip_integrity=False):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    metadata = payload.get("metadata", {})
    split = metadata.get("split")
    if metadata.get("phase") != "linear-p17-v2" or split not in {"development", "heldout"}:
        raise ValueError("P17 scorecard phase/split mismatch")
    _check_provenance(metadata)
    expected_n = 2 if metadata.get("self_check") else (8 if split == "development" else 200)
    if metadata.get("n_per_family_per_arm") != expected_n:
        raise ValueError(f"P17 {split} allocation must contain {expected_n} worlds per family/arm")
    offset = 0 if split == "development" else 2_000_000
    if metadata.get("split_offset") != offset:
        raise ValueError("P17 split offset mismatch")
    records = payload.get("records")
    expected_rows = len(FAMILIES) * len(ARMS) * expected_n
    failures = defaultdict(int)
    paired = defaultdict(dict)
    summaries = defaultdict(lambda: {"n": 0, "completed": 0, "actions": 0,
        "solved": 0, "behavior_success": 0, "prediction_correct": 0, "receipt_verified": 0,
        "candidate_count": 0, "seconds": 0.0, "graph_nodes": 0, "training_episodes": 0})
    if len(records) != expected_rows:
        failures["row_count_mismatch"] += 1
    for row in records:
        family, arm, seed = row.get("family"), row.get("profile"), row.get("seed")
        if family not in FAMILIES or arm not in ARMS or not isinstance(seed, int):
            failures["invalid_identity"] += 1
            continue
        if arm in paired[(family, seed)]:
            failures["duplicate_arm"] += 1
            continue
        paired[(family, seed)][arm] = row
        f_ix = FAMILIES.index(family)
        lo = 31_000_000 + offset + f_ix * 10_000
        if not lo <= seed < lo + expected_n:
            failures["seed_out_of_allocation"] += 1
        if row.get("status") not in {"COMPLETED", "ABSTAIN"}:
            failures["invalid_execution_status"] += 1
        if row.get("input_audit", {}).get("prediction_source_bound") is not (row.get("actions") == 1):
            failures["prediction_source_binding"] += 1
        verified, reason = _verify_row(row)
        if not verified:
            failures[reason or "row_verification"] += 1
        r = summaries[(family, arm)]
        r["n"] += 1
        r["completed"] += int(row.get("status") == "COMPLETED")
        r["actions"] += int(row.get("actions", 0))
        r["solved"] += int(row.get("action_correct") is True)
        r["behavior_success"] += int(row.get("outcome") == "behavior_success")
        r["prediction_correct"] += int(row.get("prediction_correct") is True)
        r["receipt_verified"] += int(row.get("receipt_verified") is True)
        r["candidate_count"] += row.get("candidate_count", 0) or 0
        r["graph_nodes"] += row.get("resource_counts", {}).get("graph_nodes", 0) or 0
        r["training_episodes"] += row.get("resource_counts", {}).get("training_episodes", 0) or 0
        elapsed = row.get("task_seconds")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            failures["invalid_elapsed"] += 1
        else:
            r["seconds"] += elapsed
        truth = row.get("truth", {}).get("expected_action")
        if truth is None:
            failures["missing_detached_truth"] += 1
    if len(paired) != len(FAMILIES) * expected_n:
        failures["missing_paired_world"] += 1
    for key, arms in paired.items():
        if set(arms) != set(ARMS):
            failures["missing_arm"] += 1
            continue
        for field in ("world_sha256", "world_access_sha256"):
            if len({row.get(field) for row in arms.values()}) != 1:
                failures["paired_world_mismatch"] += 1
        for row in arms.values():
            bound = row.get("input_audit", {}).get("same_primitive_access_hash")
            if bound != arms[ARMS[0]].get("world_access_sha256"):
                failures["paired_access_mismatch"] += 1
    control_rows = metadata.get("controls", [])
    n_controls = metadata.get("control_n_per_kind_per_family", 0)
    controls_by = defaultdict(list)
    for row in control_rows:
        key = row.get("family"), row.get("control")
        if key[0] not in FAMILIES or key[1] not in CONTROLS:
            failures["invalid_control"] += 1
            continue
        controls_by[key].append(row)
        if row.get("passed") is not True:
            failures["control_failed"] += 1
    control_summary = {}
    for family in FAMILIES:
        for kind in CONTROLS:
            rows = controls_by[(family, kind)]
            if len(rows) != n_controls:
                failures["control_count_mismatch"] += 1
            control_summary[f"{family}:{kind}"] = {"n": len(rows),
                "passed": sum(row.get("passed") is True for row in rows),
                "failed": sum(row.get("passed") is not True for row in rows)}
    efficacy = {}
    for family in FAMILIES:
        rates = {arm: summaries[(family, arm)]["solved"] / expected_n for arm in ARMS}
        behavior_rates = {arm: summaries[(family, arm)]["behavior_success"] / expected_n for arm in ARMS}
        efficacy[family] = {"action_accuracy": rates, "prediction_action_success": behavior_rates,
            "acquired_gain_vs": {arm: behavior_rates["acquired"] - behavior_rates[arm]
                                 for arm in ARMS if arm != "acquired"}}
        for arm in ARMS:
            if summaries[(family, arm)]["n"] != expected_n:
                failures["arm_count_mismatch"] += 1
        if any(behavior_rates["acquired"] - behavior_rates[arm] < 0.20
               for arm in ARMS if arm != "acquired"):
            failures["registered_efficacy_threshold"] += 1
    report = {"phase": "linear-p17-v2", "split": split,
        "integrity_status": "PASS" if not failures else "FAIL",
        "registered_conformance_status": "PASS" if not failures else "FAIL",
        "registered_efficacy_status": "PASS" if not failures else "FAIL",
        "rows": len(records), "n_per_family_per_arm": expected_n,
        "paired_worlds": len(paired), "failures": dict(sorted(failures.items())),
        "controls": control_summary,
        "families": {family: {arm: summaries[(family, arm)] for arm in ARMS}
                      for family in FAMILIES}, "efficacy": efficacy,
        "claim_boundary": "finite categorical tool/contact and social repair worlds; no physical or open-world claim"}
    if not _skip_integrity:
        report["analyzer_tampering_controls"] = _integrity_controls(payload)
        if report["analyzer_tampering_controls"]["failed"]:
            report["integrity_status"] = report["registered_conformance_status"] = "FAIL"
    return report


def _integrity_controls(payload):
    results = []
    for index, field in enumerate(("world_sha256", "world_access_sha256", "status", "actions", "receipt_verified")):
        altered = {**payload, "records": [dict(row) for row in payload["records"]]}
        if field == "actions":
            row = next(row for row in altered["records"] if row.get("actions") == 1)
        else:
            row = altered["records"][index % len(altered["records"])]
        row[field] = "tampered" if field in {"world_sha256", "world_access_sha256", "status"} else (0 if field == "actions" else False)
        try:
            detected = analyze(altered, _skip_integrity=True)["integrity_status"] == "FAIL"
        except (ValueError, KeyError, TypeError):
            detected = True
        results.append({"field": field, "tampering_detected": detected})
    return {"n": len(results), "passed": sum(x["tampering_detected"] for x in results),
            "failed": sum(not x["tampering_detected"] for x in results), "cases": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze(json.loads(args.scorecard.read_text()))
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
