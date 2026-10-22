"""Integrity checks and preregistered verdicts for linear_p14_v1."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARMS = {"held_operator", "authored_operator"}
STATUSES = {"NOT_RUN", "UNSUPPORTED", "TIMEOUT", "FAILED", "COMPLETED"}
PREREG = ROOT / "docs/research/engine_substrate/COGNITION_LINEAR_P14_PREREG.md"
FROZEN_COMPONENTS = {
    "Source bundle": "source_bundle_sha256", "P14 runner": "runner_sha256",
    "Analyzer": "analyzer_sha256", "Cognition-on profile": "profile_sha256",
    "World adapter": "world_adapter_sha256", "Engine source": "engine_source_sha256",
    "Native engine binary": "engine_binary_sha256", "P14 protocol bundle": "protocol_bundle_sha256",
}


def frozen_hashes():
    if not PREREG.is_file():
        raise ValueError("frozen P14 preregistration is missing")
    out = {}
    for line in PREREG.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or cells[0] not in FROZEN_COMPONENTS:
            continue
        value = cells[1].strip("`")
        if len(value) == 64 and all(char in "0123456789abcdef" for char in value):
            out[FROZEN_COMPONENTS[cells[0]]] = value
    if len(out) != len(FROZEN_COMPONENTS):
        raise ValueError("P14 preregistration has an incomplete component hash table")
    return out


def analyze(payload, *, verify_fingerprints=True):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    rows = payload.get("records")
    if not isinstance(rows, list) or not rows or any(r.get("status") not in STATUSES for r in rows):
        raise ValueError("scorecard has no records or an invalid record status")
    by_family = defaultdict(list)
    for row in rows:
        by_family[row.get("family")].append(row)
    operators = by_family["candidate_operator"]
    laws = by_family["law_claim"]
    controls = by_family["tampering_control"]
    if not operators or not laws or not controls:
        raise ValueError("missing operator, law, or tampering-control records")

    paired = defaultdict(list)
    for row in operators:
        paired[row.get("seed")].append(row)
    missing_or_duplicate_pairs = sum(
        Counter(row.get("profile") for row in group) != Counter({arm: 1 for arm in ARMS})
        for group in paired.values())
    world_hash_mismatches = access_hash_mismatches = input_audit_failures = 0
    invariant_failures = status_failures = 0
    work_accounting_failures = 0
    for group in paired.values():
        world_hash_mismatches += len({r.get("world_sha256") for r in group}) != 1
        access_hash_mismatches += len({r.get("world_access_sha256") for r in group}) != 1
        input_audit_failures += sum(
            not r.get("input_audit", {}).get("answer_fields_absent")
            or not r.get("input_audit", {}).get("hidden_strategy_absent")
            or not r.get("input_audit", {}).get("same_primitive_access_hash")
            or not r.get("world_sha256") or not r.get("world_access_sha256")
            for r in group)
        status_failures += sum(r.get("status") != "COMPLETED" for r in group)
        work_accounting_failures += sum(
            int(r.get("agent_work_units", -1)) != (1 if r.get("profile") == "held_operator" else 4)
            for r in group)
        invariant_failures += sum(int(r.get("invariant_checks_passed", 0)) != 1
                                  for r in group if r.get("profile") == "authored_operator")
        status_by_arm = {r.get("profile"): r for r in group}
        if ARMS.issubset(status_by_arm) and status_by_arm["authored_operator"].get("solved"):
            if status_by_arm["authored_operator"].get("operator_calls") != 1:
                status_failures += 1

    law_false_proofs = sum(
        r.get("expected_status") == "rejected" and
        (r.get("actual_status") == "checked" or r.get("proven") == 1 or r.get("proof_reference_count", 0) > 0)
        for r in laws)
    law_missing_checks = sum(
        r.get("expected_status") == "checked" and
        (r.get("actual_status") != "checked" or r.get("proof_reference_count") != 1
         or not r.get("proof_binding_valid") or not r.get("correct"))
        for r in laws)
    law_counterexample_failures = sum(
        r.get("expected_status") == "rejected" and not r.get("counterexample_validated") for r in laws)
    control_failures = sum(not r.get("control_passed") or r.get("status") != "COMPLETED" for r in controls)
    proof_controls = sum(r.get("control_kind") == "proof_reference_tamper" for r in controls)
    criterion_controls = sum(r.get("control_kind") == "criterion_digest_tamper" for r in controls)
    allocation = payload.get("metadata", {}).get("seed_allocation", {})
    heldout = payload.get("metadata", {}).get("split") == "heldout"
    required_candidate_n = 200 if heldout else int(allocation.get("candidate_operator_cases", 0))
    required_law_n = 200 if heldout else int(allocation.get("law_cases", 0))
    required_control_n = 100 if heldout else int(allocation.get("proof_criterion_tampering_controls", 0))
    expected_law_kinds = Counter({"valid_structural": required_law_n // 2,
                                  "false_finite_sample": required_law_n // 2})
    law_kind_counts = Counter(r.get("claim_kind") for r in laws)
    allocation_failures = int(
        len(paired) != required_candidate_n or len(laws) != required_law_n
        or len(controls) != required_control_n or proof_controls != required_control_n // 2
        or criterion_controls != required_control_n // 2
        or law_kind_counts != expected_law_kinds
        or any(len(group) != 2 for group in paired.values()))
    if heldout:
        allocation_failures += int(
            {r.get("seed") for r in operators} != set(range(14_100_000, 14_100_200))
            or {r.get("seed") for r in laws} != set(range(14_120_000, 14_120_200))
            or {r.get("seed") for r in controls} != set(range(14_140_000, 14_140_100)))
    provenance = payload.get("metadata", {}).get("artifact_provenance", {})
    provenance_mismatches = (sum(provenance.get(key) != expected
                                 for key, expected in frozen_hashes().items())
                             if verify_fingerprints else 0)
    if verify_fingerprints and not provenance:
        provenance_mismatches = len(FROZEN_COMPONENTS)
    input_audit_failures += sum(
        not r.get("input_audit", {}).get("hidden_truth_label_absent")
        or not r.get("input_audit", {}).get("answer_fields_absent")
        for r in laws)
    action_failures = sum(int(r.get("actions", r.get("world_actions", 0))) != 0 for r in rows)

    base_success = sum(bool(r.get("solved")) for r in operators if r.get("profile") == "held_operator")
    authored_success = sum(bool(r.get("solved")) for r in operators if r.get("profile") == "authored_operator")
    n = len(paired)
    base_rate = base_success / n if n else None
    authored_rate = authored_success / n if n else None
    gain = authored_rate - base_rate if n else None
    development = payload.get("metadata", {}).get("development_selection", {})
    development_qualified = (development.get("candidate_status") == "awaiting_human"
                             and development.get("candidate_yield", 0) > development.get("parent_yield", 0)
                             and development.get("invariant_checks", 0) == 8
                             and development.get("candidate_work", 10**9) <= 32)
    integrity = (missing_or_duplicate_pairs + world_hash_mismatches + access_hash_mismatches
                 + input_audit_failures + invariant_failures + status_failures
                 + work_accounting_failures
                 + law_false_proofs + law_missing_checks + law_counterexample_failures
                 + control_failures + allocation_failures + provenance_mismatches + action_failures)
    operator_status = "PASS" if integrity == 0 and development_qualified and gain is not None and gain >= 0.20 else "FAIL"
    law_status = "PASS" if not (law_false_proofs + law_missing_checks + law_counterexample_failures + allocation_failures) else "FAIL"
    safety_status = "PASS" if not (control_failures + allocation_failures) else "FAIL"
    return {
        "schema": "pmb-linear-p14-v1-analysis-v1",
        "phase": payload.get("metadata", {}).get("phase"),
        "split": payload.get("metadata", {}).get("split"),
        "candidate_operator_cases": n, "law_cases": len(laws), "tampering_controls": len(controls),
        "arms": {"held_operator": {"solved": base_success, "n": n, "accuracy": base_rate},
                 "authored_operator": {"solved": authored_success, "n": n, "accuracy": authored_rate}},
        "mean_agent_work_units": {
            arm: (sum(int(r.get("agent_work_units", 0)) for r in operators if r.get("profile") == arm) / n
                  if n else None) for arm in sorted(ARMS)},
        "authored_operator_gain": gain,
        "development_selection": development,
        "development_qualified": development_qualified,
        "law_false_proofs": law_false_proofs, "law_missing_checks": law_missing_checks,
        "law_counterexample_failures": law_counterexample_failures,
        "tampering_control_failures": control_failures,
        "proof_reference_tamper_controls": proof_controls,
        "criterion_digest_tamper_controls": criterion_controls,
        "missing_or_duplicate_arm_pairs": missing_or_duplicate_pairs,
        "world_hash_mismatches": world_hash_mismatches,
        "primitive_access_hash_mismatches": access_hash_mismatches,
        "input_audit_failures": input_audit_failures,
        "invariant_check_failures": invariant_failures,
        "completion_failures": status_failures,
        "work_accounting_failures": work_accounting_failures,
        "allocation_failures": allocation_failures,
        "provenance_mismatches": provenance_mismatches,
        "external_action_failures": action_failures,
        "integrity_failures": integrity,
        "operator_status": operator_status, "law_status": law_status,
        "safety_status": safety_status,
        "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED",
        "scope": "finite_permutation_commutator_law_and_one_step_operator_macro",
    }


def _self_check_payload():
    rows = []
    for seed in (1, 2):
        world = f"world-{seed}"
        access = "same-access"
        for arm, solved in (("held_operator", False), ("authored_operator", True)):
            rows.append({"status": "COMPLETED", "family": "candidate_operator", "seed": seed,
                         "profile": arm, "solved": solved, "operator_calls": 1,
                         "agent_work_units": 1 if arm == "held_operator" else 4,
                         "invariant_checks_passed": 1, "world_sha256": world,
                         "world_access_sha256": access,
                         "input_audit": {"answer_fields_absent": True, "hidden_strategy_absent": True,
                                         "same_primitive_access_hash": access}})
    for seed, kind in ((1, "valid_structural"), (2, "false_finite_sample"),
                       (3, "valid_structural"), (4, "false_finite_sample")):
        valid = kind == "valid_structural"
        rows.append({"status": "COMPLETED", "family": "law_claim", "seed": seed,
                     "claim_kind": kind,
                     "expected_status": "checked" if valid else "rejected",
                     "actual_status": "checked" if valid else "rejected",
                     "proven": int(valid), "proof_reference_count": int(valid), "correct": True,
                     "proof_binding_valid": True,
                     "input_audit": {"hidden_truth_label_absent": True, "answer_fields_absent": True},
                     "counterexample_validated": True})
    for seed in range(4):
        rows.append({"status": "COMPLETED", "family": "tampering_control", "seed": seed,
                     "control_kind": "proof_reference_tamper" if seed % 2 == 0 else "criterion_digest_tamper",
                     "control_passed": True})
    return {"schema": "pmb-scorecard-v1", "metadata": {
        "phase": "linear-p14-v1", "split": "development",
        "seed_allocation": {"candidate_operator_cases": 2, "law_cases": 4,
                             "proof_criterion_tampering_controls": 4},
        "development_selection": {"candidate_status": "awaiting_human", "candidate_yield": 8,
                                   "parent_yield": 0, "invariant_checks": 8, "candidate_work": 32},
    }, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path, nargs="?")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        result = analyze(_self_check_payload(), verify_fingerprints=False)
        assert result["integrity_failures"] == 0 and result["operator_status"] == "PASS"
        assert result["law_status"] == result["safety_status"] == "PASS"
        print("linear_p14 analyzer self-check: PASS")
        return
    if args.scorecard is None:
        parser.error("scorecard is required unless --self-check is used")
    print(json.dumps(analyze(json.loads(args.scorecard.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
