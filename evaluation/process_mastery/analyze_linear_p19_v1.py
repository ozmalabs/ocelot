"""Fail-closed analysis of the frozen P19 matched-arm scorecard."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from evaluation.process_mastery.linear_p19_v1 import (
    ARMS, HELDOUT_PER_CELL, MODEL_QUERY_CAP, PRIMITIVE_CAP, allocation,
)
from evaluation.process_mastery.linear_p19_worlds import FAMILIES, TASK_KINDS, generate_task


def analyze(payload):
    trials = payload.get("trials", [])
    controls = payload.get("controls", [])
    expected = allocation("heldout")["tasks"]
    expected_keys = {(row["family"], row["task_kind"], row["seed"])
                     for row in expected}
    audit = {"failures": [], "authorization_pending": 0,
             "receipt_failures": 0, "resource_failures": 0,
             "non_template_verified": 0, "unseen_binding_strategy_solved": 0}
    by_key = defaultdict(dict)
    for row in trials:
        key = (row.get("family"), row.get("task_kind"), row.get("seed"))
        arm = row.get("arm")
        if key not in expected_keys or arm not in ARMS:
            audit["failures"].append({"kind": "unexpected_trial", "key": key, "arm": arm})
            continue
        if arm in by_key[key]:
            audit["failures"].append({"kind": "duplicate_arm_row", "key": key, "arm": arm})
            continue
        by_key[key][arm] = row
        if row.get("status") == "AWAITING_CANDIDATE_APPROVAL":
            audit["authorization_pending"] += 1
        input_audit = row.get("input_audit", {})
        if input_audit.get("hidden_witness_absent") is not True \
                or input_audit.get("goal_action_absent") is not True:
            audit["failures"].append({"kind": "answer_or_witness_exposure", "key": key, "arm": arm})
        if row.get("primitives", 0) > PRIMITIVE_CAP or row.get("model_queries", 0) > MODEL_QUERY_CAP:
            audit["resource_failures"] += 1
            audit["failures"].append({"kind": "resource_cap_exceeded", "key": key, "arm": arm})
        if row.get("expression_key", "").startswith(("compose:", "compose[", "power:", "inverse:")):
            audit["non_template_verified"] += int(row.get("status") == "COMPLETED"
                and row.get("solved") is True and row.get("receipt_verified", True))
        reuse = row.get("unseen_binding_strategy") or {}
        audit["unseen_binding_strategy_solved"] += int(bool(reuse.get("solved"))
            and reuse.get("binding_changed") is True and reuse.get("goal_changed") is True)
        task, world, _witness = generate_task(key[0], key[1], key[2])
        if row.get("world_sha256") != world.task_digest(task):
            audit["failures"].append({"kind": "world_hash_mismatch", "key": key, "arm": arm})
        for receipt in row.get("receipts", []):
            actions = receipt.get("requested_actions")
            replayed = world.transition_sequence(actions or (),
                requested_process=receipt.get("requested_process"))
            if (not world.verify_receipt(receipt) or replayed != receipt
                    or not world.verify_receipt(replayed)):
                audit["receipt_failures"] += 1
                audit["failures"].append({"kind": "receipt_mismatch", "key": key, "arm": arm})
                break
        if row.get("solved") is True and tuple(world.state) != tuple(world.goal):
            audit["failures"].append({"kind": "solved_state_mismatch", "key": key, "arm": arm})

    missing = []
    for key in expected_keys:
        absent = sorted(set(ARMS) - set(by_key.get(key, {})))
        if absent:
            missing.append({"key": key, "arms": absent})
    if missing:
        audit["failures"].append({"kind": "missing_matched_arm_rows", "count": len(missing),
                                   "examples": missing[:10]})
    for key, arm_rows in by_key.items():
        world_hashes = {row.get("world_sha256") for row in arm_rows.values()}
        if len(world_hashes) > 1:
            audit["failures"].append({"kind": "matched_world_mismatch", "key": key})
    expected_controls = {(row["kind"], row["seed"])
                         for row in allocation("heldout")["controls"]}
    observed_controls = {(row.get("kind"), row.get("seed")) for row in controls}
    if len(controls) != 100 or observed_controls != expected_controls:
        audit["failures"].append({"kind": "control_count", "observed": len(controls), "expected": 100})
    control_counts = Counter(control.get("kind") for control in controls)
    if control_counts != Counter({"impossible_goal": 34, "illegal_action": 33,
                                  "precondition_failure": 33}):
        audit["failures"].append({"kind": "control_allocation_mismatch",
                                   "observed": dict(control_counts)})
    if any(control.get("status") != "PASS" or control.get("state_unchanged") is not True
           for control in controls):
        audit["failures"].append({"kind": "control_structural_failure"})
    if any(control.get("kind") == "impossible_goal" and control.get("goal_reachable") is not False
           for control in controls):
        audit["failures"].append({"kind": "impossible_goal_control_reachable"})

    cells = {}
    total_success = Counter()
    total_n = Counter()
    for family in FAMILIES:
        for task_kind in TASK_KINDS:
            cell = {arm: {"n": 0, "solved": 0, "primitives": [], "model_queries": []}
                    for arm in ARMS}
            for key, arm_rows in by_key.items():
                if key[:2] != (family, task_kind):
                    continue
                for arm, row in arm_rows.items():
                    cell[arm]["n"] += 1
                    cell[arm]["solved"] += int(row.get("solved") is True)
                    cell[arm]["primitives"].append(int(row.get("primitives", 0)))
                    cell[arm]["model_queries"].append(int(row.get("model_queries", 0)))
            for arm, values in cell.items():
                status_counts = Counter(row.get("status", "unknown") for key, arm_rows in by_key.items()
                    if key[:2] == (family, task_kind) and arm in arm_rows
                    for row in (arm_rows[arm],))
                points = sorted({(int(row.get("primitives", 0)),
                                  int(row.get("model_queries", 0)),
                                  bool(row.get("solved")))
                    for key, arm_rows in by_key.items() if key[:2] == (family, task_kind)
                    for row in ([arm_rows[arm]] if arm in arm_rows else [])})
                frontier = [point for point in points if not any(
                    other[2] == point[2] and other != point
                    and other[0] <= point[0] and other[1] <= point[1]
                    and (other[0] < point[0] or other[1] < point[1]) for other in points)]
                values["status_counts"] = dict(status_counts)
                values["resource_frontier"] = [
                    {"primitives": p, "model_queries": q, "solved": solved}
                    for p, q, solved in frontier]
                values["solve_rate"] = values["solved"] / values["n"] if values["n"] else None
                values["mean_primitives"] = (sum(values["primitives"]) / len(values["primitives"])
                                              if values["primitives"] else None)
                values["mean_model_queries"] = (sum(values["model_queries"]) / len(values["model_queries"])
                                                if values["model_queries"] else None)
                total_success[arm] += values["solved"]
                total_n[arm] += values["n"]
            cells[f"{family}/{task_kind}"] = cell

    complete = not missing and not audit["failures"]
    primary_computable = complete and audit["authorization_pending"] == 0
    if primary_computable:
        invention_rate = total_success["invention_discovery"] / total_n["invention_discovery"]
        comparator_rates = [total_success[arm] / total_n[arm]
                            for arm in ("measured_greedy", "native_primitive_search")]
        gain = invention_rate - max(comparator_rates)
        primary = {"status": "PASS" if gain >= 0.20 else "FAIL",
                   "invention_rate": invention_rate,
                   "strongest_comparator_rate": max(comparator_rates),
                   "observed_gain": gain, "threshold": 0.20}
    else:
        primary = {"status": "NOT_ESTABLISHED",
                   "reason": "incomplete matched panel or candidate approval pending"}
    mechanism = {
        "non_template_verified_process": {
            "status": "PASS" if audit["non_template_verified"] >= 1 else "FAIL",
            "count": audit["non_template_verified"], "minimum": 1},
        "unseen_binding_strategy_use": {
            "status": "PASS" if audit["unseen_binding_strategy_solved"] >= 1 else "FAIL",
            "count": audit["unseen_binding_strategy_solved"], "minimum": 1},
    }
    prereg = payload.get("provenance", {})
    provenance_ok = prereg.get("runtime_attestation", {}).get("status") == "ATTESTED"
    if not provenance_ok:
        audit["failures"].append({"kind": "runtime_provenance_unattested"})
    return {"phase": "linear-p19-v1", "status": "PASS" if not audit["failures"] else "FAIL",
            "primary": primary, "mechanism_criteria": mechanism, "cells": cells,
            "counts": {"trials": len(trials), "expected_trials": len(expected) * len(ARMS),
                       "controls": len(controls), "authorization_pending": audit["authorization_pending"]},
            "audit": audit, "provenance_status": "ATTESTED" if provenance_ok else "NOT_ESTABLISHED"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.input.read_text()))
    encoded = json.dumps(result, sort_keys=True, indent=2)
    if args.output:
        args.output.write_text(encoded + "\n")
    else:
        print(encoded)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
