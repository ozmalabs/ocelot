#!/usr/bin/env python3
"""Analyze same-operation role wiring and task-verifier behavior."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/gap_grounder_role_wiring_v1_3/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/gap_grounder_role_wiring_v1_3_lock_20260929.json"
OUT = ROOT / "evaluation/reports/gap_grounder_role_wiring_v1_3/analysis.json"
EXPECTED = {"isolated_B": ["B"], "isolated_C": ["C"],
            "repeat_B": ["B", "B"], "B_then_C": ["B", "C"],
            "C_then_B": ["C", "B"]}
ARMS = ("faculty", "faculty_plus_operations")


def summarize(event: dict) -> dict:
    obs = event["new_observations"][-1]["attrs"] if event["new_observations"] else {}
    result = event["result"]
    verified = result.get("verified") or {}
    return {"case": event["case"], "gap_attrs": event["gap_attrs"],
            "observation_status": obs.get("status"),
            "observation_signature": obs.get("signature"), "observation_key": obs.get("key"),
            "concern_key": result.get("concern_key"), "outcome": result.get("outcome"),
            "primitive_name": result.get("name"), "operation": result.get("operation"),
            "construction": result.get("construction"), "term_tree": result.get("term_tree"),
            "accepted": result.get("accepted"), "verification_accepted": verified.get("accepted"),
            "verification_reason": verified.get("reason"),
            "verification_gates": {k: verified.get(k) for k in
                ("real_pass", "twin_pass", "discriminates", "no_regression", "grounded", "verdict")},
            "axis_delta": event["axis_delta"],
            "primitive_request_delta": event["primitive_request_delta"],
            "held_primitive_delta": event["held_primitive_delta"],
            "codebook_epoch": event["after"]["codebook_epoch"],
            "native_steps": event["after"]["latest_native_steps"]}


def fixture_heads():
    p = ROOT / "evaluation/substrate_capability/gap_grounder_role_wiring_v1_3.py"
    spec = importlib.util.spec_from_file_location("role_wiring_runner", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {k: [x[0] for x in v["observation"]] for k, v in mod.GAPS.items()}


def main() -> None:
    capture, lock = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text())
    assert capture["input_lock"] == lock == capture["post_run_input_lock"]
    runs = {(r["arm"], r["sequence_id"]): r for r in capture["runs"]}
    assert len(runs) == 10
    rows = {}
    for arm in ARMS:
        for seq, labels in EXPECTED.items():
            run = runs[(arm, seq)]
            assert [e["case"] for e in run["events"]] == labels
            rows[f"{arm}:{seq}"] = [summarize(e) for e in run["events"]]
    heads = fixture_heads()
    assert sorted(heads["B"]) == sorted(heads["C"])
    assert sum(len(r["events"]) for r in capture["runs"]) == 16
    def at(arm: str, seq: str, i: int = -1) -> dict:
        return rows[f"{arm}:{seq}"][i]
    comparisons = {}
    for arm in ARMS:
        comparisons[arm] = {
            "isolated_B": at(arm, "isolated_B"),
            "isolated_C": at(arm, "isolated_C"),
            "repeat_B_second": at(arm, "repeat_B"),
            "B_then_C_second": at(arm, "B_then_C"),
            "C_then_B_second": at(arm, "C_then_B"),
        }
    btree = comparisons["faculty_plus_operations"]["isolated_B"].get("term_tree")
    ctree = comparisons["faculty_plus_operations"]["isolated_C"].get("term_tree")
    same_candidate_key = (
        comparisons["faculty_plus_operations"]["isolated_B"].get("concern_key") ==
        comparisons["faculty_plus_operations"]["isolated_C"].get("concern_key"))
    same_accepted_term_for_different_io = (
        btree == ctree and
        comparisons["faculty_plus_operations"]["isolated_C"].get("accepted") is True and
        comparisons["faculty_plus_operations"]["isolated_B"]["gap_attrs"].get("inputs") !=
        comparisons["faculty_plus_operations"]["isolated_C"]["gap_attrs"].get("inputs") and
        comparisons["faculty_plus_operations"]["isolated_B"]["gap_attrs"].get("outputs") !=
        comparisons["faculty_plus_operations"]["isolated_C"]["gap_attrs"].get("outputs"))
    analysis = {
        "schema_version": 1,
        "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "pre_post_lock_match": True, "arm_count": 2, "fresh_graph_count": 10,
        "call_count": 16,
        "fixtures": {"B_C_same_predicate_multiset": True,
                     "B_C_distinct_full_observation_signatures": (
                         comparisons["faculty"]["isolated_B"].get("observation_signature") !=
                         comparisons["faculty"]["isolated_C"].get("observation_signature")),
                     "declared_io_contracts_differ": (
                         comparisons["faculty"]["isolated_B"]["gap_attrs"].get("inputs") !=
                         comparisons["faculty"]["isolated_C"]["gap_attrs"].get("inputs") and
                         comparisons["faculty"]["isolated_B"]["gap_attrs"].get("outputs") !=
                         comparisons["faculty"]["isolated_C"]["gap_attrs"].get("outputs"))},
        "candidate_key_same_for_B_C": same_candidate_key,
        "isolated_forward_and_inverse_term_trees_equal": btree == ctree,
        "accepted_same_term_for_different_declared_io": same_accepted_term_for_different_io,
        "comparisons": comparisons, "event_rows": rows,
        "claim_boundary": ("One authored forward/inverse-like spectral pair. Identical operation heads do not encode role wiring; "
                           "a passing forward-tone peak-bin gate is not an inverse-task oracle or a natural-rate estimate."),
    }
    assert analysis["fixtures"]["B_C_same_predicate_multiset"]
    assert analysis["fixtures"]["B_C_distinct_full_observation_signatures"]
    assert analysis["fixtures"]["declared_io_contracts_differ"]
    assert analysis["candidate_key_same_for_B_C"]
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "graphs": 10, "calls": 16,
                      "same_operation_key": analysis["candidate_key_same_for_B_C"],
                      "term_trees_equal": analysis["isolated_forward_and_inverse_term_trees_equal"]}, indent=2))


if __name__ == "__main__":
    main()
