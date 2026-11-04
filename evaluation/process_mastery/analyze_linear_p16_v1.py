"""Integrity and conformance analyzer for the frozen P16 PMB scorecard."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs/research/engine_substrate/COGNITION_LINEAR_P16_PREREG.md"
ARMS = ("primitive_search", "graph_expression")
FAMILIES = ("permutation", "state_dependent_tool")
CONTROL_KINDS = ("missing_expression", "stale_expression", "tampered_expression",
                 "wrapper_native_mismatch", "unauthorized_emission")


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _frozen_contract():
    if not PREREG.is_file():
        raise ValueError("P16 standalone preregistration is missing")
    text = PREREG.read_text()
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not match:
        raise ValueError("P16 preregistration has no frozen JSON contract")
    return json.loads(match.group(1))


def _check_provenance(metadata, split):
    actual = metadata.get("artifact_provenance", {})
    required = ("source_bundle_sha256", "runner_sha256", "analyzer_sha256",
                "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256",
                "engine_source_sha256")
    missing = [key for key in required if not actual.get(key)]
    if missing:
        raise ValueError(f"P16 artifact provenance missing {missing}")
    attestation = actual.get("runtime_attestation", {})
    if (attestation.get("status") != "ATTESTED"
            or attestation.get("native_symbols_bound") is not True
            or attestation.get("build_sources_match") is not True
            or attestation.get("loaded_extension_sha256") != actual["loaded_extension_sha256"]
            or attestation.get("wrapper_sha256") != actual["wrapper_sha256"]
            or attestation.get("build_receipt_sha256") != actual["build_receipt_sha256"]):
        raise ValueError("P16 runtime attestation does not bind the recorded artifacts")
    if split == "heldout":
        frozen = _frozen_contract()
        artifact_mismatches = {key: (actual.get(key), frozen.get("artifacts", {}).get(key))
            for key in required if actual.get(key) != frozen.get("artifacts", {}).get(key)}
        runtime_keys = ("wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                        "build_source_fingerprint")
        runtime_mismatches = {key: (attestation.get(key), frozen.get("runtime", {}).get(key))
            for key in runtime_keys if attestation.get(key) != frozen.get("runtime", {}).get(key)}
        if artifact_mismatches or runtime_mismatches:
            raise ValueError("held-out artifact hash mismatch: "
                             f"artifacts={artifact_mismatches}, runtime={runtime_mismatches}")


def _verify_world(row):
    from evaluation.process_mastery.native_world_comparators import NativeWorldAdapter
    from evaluation.process_mastery.puzzle_worlds import p16_task

    task = p16_task(row["family"], int(row["seed"]))
    if _digest(task) != row.get("world_sha256"):
        return False, "world_hash_mismatch"
    access = _digest({"initial_state": task["initial_state"], "goal_state": task["goal_state"],
        "primitive_affordances": task["primitive_affordances"],
        "legal_actions_by_state": task["legal_actions_by_state"],
        "transition_model": task["transition_model"]})
    if access != row.get("world_access_sha256"):
        return False, "world_access_hash_mismatch"
    if row.get("input_audit", {}).get("same_primitive_access_hash") != access:
        return False, "arm_access_mismatch"
    if row.get("input_audit", {}).get("answer_fields_absent") is not True:
        return False, "answer_input_leak"
    if row.get("input_audit", {}).get("hidden_solution_absent") is not True:
        return False, "hidden_solution_leak"
    receipt = row.get("receipt")
    if not receipt:
        if row.get("actions") != 0:
            return False, "action_without_receipt"
        return True, None
    world = NativeWorldAdapter.from_task(task, world_id=f"{task['family']}:{task['seed']}")
    world.epoch = int(receipt.get("world_epoch", 0))
    if not world.verify_receipt(receipt):
        return False, "external_receipt_mismatch"
    if tuple(receipt.get("before_state", ())) != tuple(task["initial_state"]):
        return False, "receipt_wrong_initial_state"
    if tuple(receipt.get("observed_state", ())) != tuple(row.get("observed_state", ())):
        return False, "receipt_row_state_mismatch"
    if row.get("receipt_verified") is not True:
        return False, "runner_receipt_verification_false"
    if row.get("actions") != 1:
        return False, "receipt_action_count_mismatch"
    return True, None


def analyze(payload, *, _skip_integrity=False):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    metadata = payload.get("metadata", {})
    split = metadata.get("split")
    if metadata.get("phase") != "linear-p16-v1" or split not in {"development", "heldout"}:
        raise ValueError("P16 scorecard phase/split mismatch")
    _check_provenance(metadata, split)
    n = metadata.get("n_per_family_per_arm")
    expected_n = 2 if metadata.get("self_check") else (8 if split == "development" else 200)
    if n != expected_n:
        raise ValueError(f"P16 {split} panel must contain exactly {expected_n} paired tasks/family/arm")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("P16 records must be an array")
    expected_rows = len(FAMILIES) * n * len(ARMS)
    if len(records) != expected_rows:
        raise ValueError(f"P16 record count mismatch: expected {expected_rows}, got {len(records)}")
    paired = defaultdict(dict)
    failures = defaultdict(int)
    family_counts = defaultdict(lambda: defaultdict(lambda: {"n": 0, "completed": 0,
        "solved": 0, "actions": 0, "receipt_verified": 0, "seconds": 0.0,
        "work": 0, "graph_nodes": 0, "bytes": 0}))
    offset = int(metadata.get("split_offset", -1))
    expected_offset = 0 if split == "development" else 1_000_000
    if offset != expected_offset:
        raise ValueError("P16 split seed offset mismatch")
    seed_seen = set()
    for row in records:
        family, seed, arm = row.get("family"), row.get("seed"), row.get("profile")
        if family not in FAMILIES or arm not in ARMS or not isinstance(seed, int):
            failures["invalid_identity"] += 1
            continue
        if arm in paired[(family, seed)]:
            failures["duplicate_arm"] += 1
            continue
        paired[(family, seed)][arm] = row
        family_index = FAMILIES.index(family)
        lo = 26_160_000 + offset + family_index * 10_000
        if not (lo <= seed < lo + n):
            failures["seed_out_of_allocation"] += 1
        seed_seen.add((family, seed))
        if row.get("status") != "COMPLETED":
            failures["incomplete_execution"] += 1
        if row.get("outcome") != ("solved" if tuple(row.get("observed_state", ())) ==
                                   tuple(row.get("goal_state", ())) else "unsolved"):
            failures["outcome_mismatch"] += 1
        verified, reason = _verify_world(row)
        if not verified:
            failures[reason or "world_verification"] += 1
        if row.get("profile") == "primitive_search":
            if row.get("planner_status") != "solved" or row.get("search_expansions", 0) < 1:
                failures["primitive_search_not_native_solved"] += 1
        else:
            audit = row.get("input_audit", {})
            if audit.get("selected_by_graph") is not True or not audit.get("source_nodes_owned"):
                failures["expression_not_graph_selected"] += 1
            meter = row.get("meter", {})
            if row.get("status") == "COMPLETED" and (
                    meter.get("expression_visits", 0) < 1
                    or meter.get("compositions", 0) < 1
                    or meter.get("applications", 0) != 1):
                failures["expression_meter_invalid"] += 1
        r = family_counts[family][arm]
        r["n"] += 1
        r["completed"] += int(row.get("status") == "COMPLETED")
        r["solved"] += int(row.get("outcome") == "solved")
        r["actions"] += int(row.get("actions", 0))
        r["receipt_verified"] += int(row.get("receipt_verified") is True)
        elapsed = row.get("task_seconds")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            failures["invalid_elapsed"] += 1
        else:
            r["seconds"] += elapsed
        resources = row.get("resource_counts", {})
        r["work"] += resources.get("search_expansions", resources.get("compositions", 0)) or 0
        r["graph_nodes"] += row.get("graph_nodes_end") or 0
        r["bytes"] += row.get("graph_serialized_bytes") or 0
    if len(seed_seen) != len(FAMILIES) * n:
        failures["missing_paired_world"] += len(FAMILIES) * n - len(seed_seen)
    for key, arms in paired.items():
        if set(arms) != set(ARMS):
            failures["pair_missing_arm"] += 1
            continue
        left, right = arms[ARMS[0]], arms[ARMS[1]]
        for field in ("world_sha256", "world_access_sha256"):
            if left.get(field) != right.get(field):
                failures["paired_world_mismatch"] += 1
        for row in (left, right):
            if row.get("input_audit", {}).get("same_primitive_access_hash") != left.get("world_access_sha256"):
                failures["paired_access_audit_mismatch"] += 1
    controls = metadata.get("controls", [])
    expected_controls = metadata.get("control_n_per_kind", 0)
    controls_by_kind = defaultdict(list)
    for control in controls:
        if control.get("control") not in CONTROL_KINDS:
            failures["unknown_control"] += 1
            continue
        controls_by_kind[control["control"]].append(control)
        if control.get("passed") is not True or control.get("actions", 0) != 0:
            failures["control_failed"] += 1
    control_summary = {}
    for kind in CONTROL_KINDS:
        values = controls_by_kind[kind]
        if len(values) != expected_controls:
            failures["control_count_mismatch"] += abs(len(values) - expected_controls) or 1
        control_summary[kind] = {"n": len(values), "passed": sum(x.get("passed") is True for x in values),
                                 "failed": sum(x.get("passed") is not True for x in values)}
    if len(controls) != expected_controls * len(CONTROL_KINDS):
        failures["control_total_mismatch"] += 1
    out = {"phase": "linear-p16-v1", "split": split,
        "integrity_status": "PASS" if not failures else "FAIL",
        "registered_conformance_status": "PASS" if not failures else "FAIL",
        "n_per_family_per_arm": n, "rows": len(records),
        "paired_worlds": len(seed_seen), "failures": dict(sorted(failures.items())),
        "controls": control_summary,
        "families": {family: {arm: values for arm, values in arms.items()}
                     for family, arms in family_counts.items()},
        "metrics_boundary": "success counts are descriptive; registered pass is native/world conformance and zero-tolerance controls",
        "capability_boundary": "finite one-step 4-element permutation and state-dependent finite-tool worlds only; no general search or physical capability claim"}
    return out


def _integrity_controls(payload):
    results = []
    for index, field in enumerate(("world_sha256", "world_access_sha256", "status", "actions", "receipt_verified")):
        altered = {**payload, "records": [dict(row) for row in payload["records"]]}
        row = altered["records"][index % len(altered["records"])]
        if field in {"world_sha256", "world_access_sha256"}:
            row[field] = "tampered"
        elif field == "status":
            row[field] = "FAILED"
        elif field == "actions":
            row[field] = 0
        else:
            row[field] = False
        try:
            detected = analyze(altered, _skip_integrity=True)["integrity_status"] == "FAIL"
        except (ValueError, KeyError, TypeError):
            detected = True
        results.append({"field": field, "tampering_detected": detected})
    return {"n": len(results), "passed": sum(row["tampering_detected"] for row in results),
            "failed": sum(not row["tampering_detected"] for row in results), "cases": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.scorecard.read_text())
    report = analyze(payload)
    report["analyzer_tampering_controls"] = _integrity_controls(payload)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
