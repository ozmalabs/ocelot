#!/usr/bin/env python3
"""Validate and compare the current and operation-augmented gap keys."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/gap_grounder_operation_key_v1_2/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/gap_grounder_operation_key_v1_2_lock_20260929.json"
OUT = ROOT / "evaluation/reports/gap_grounder_operation_key_v1_2/analysis.json"
EXPECTED = {"isolated_A": ["A"], "isolated_B": ["B"],
            "isolated_B_value": ["B_value"], "repeat_B": ["B", "B"],
            "B_then_B_value": ["B", "B_value"],
            "A_then_B": ["A", "B"], "B_then_A": ["B", "A"]}


def summarize(e: dict) -> dict:
    obs = e["new_observations"][-1]["attrs"] if e["new_observations"] else {}
    result = e["result"]
    verified = result.get("verified") or {}
    return {"case": e["case"], "observation_status": obs.get("status"),
            "observation_signature": obs.get("signature"), "observation_key": obs.get("key"),
            "concern_key": result.get("concern_key"), "outcome": result.get("outcome"),
            "path": result.get("path"), "composition": result.get("composition"),
            "accepted": result.get("accepted"), "verification_accepted": verified.get("accepted"),
            "verification_reason": verified.get("reason"),
            "verification_gates": {k: verified.get(k) for k in
                                   ("real_pass", "twin_pass", "discriminates",
                                    "no_regression", "grounded", "verdict")},
            "axis_delta": e["axis_delta"], "primitive_request_delta": e["primitive_request_delta"],
            "held_primitive_delta": e["held_primitive_delta"],
            "codebook_epoch": e["after"]["codebook_epoch"],
            "native_steps": e["after"]["latest_native_steps"]}


def main() -> None:
    capture, lock = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text())
    assert capture["input_lock"] == lock == capture["post_run_input_lock"]
    runs = {(r["arm"], r["sequence_id"]): r for r in capture["runs"]}
    arms = ("faculty", "faculty_plus_operations")
    assert len(runs) == 14
    summary = {}
    for arm in arms:
        for seq, cases in EXPECTED.items():
            run = runs[(arm, seq)]
            assert [e["case"] for e in run["events"]] == cases
            summary[f"{arm}:{seq}"] = [summarize(e) for e in run["events"]]
    def signature(label: str) -> str:
        event = runs[("faculty_plus_operations", label)]["events"][0]
        return json.dumps(event["new_observations"][0]["attrs"].get("signature"),
                          sort_keys=True, separators=(",", ":"))
    assert signature("isolated_B") != signature("isolated_B_value")
    assert sorted(x[0] for x in GAPS_HEADS("B")) == sorted(x[0] for x in GAPS_HEADS("B_value"))
    assert sorted(x[0] for x in GAPS_HEADS("A")) != sorted(x[0] for x in GAPS_HEADS("B"))
    comparisons = {}
    for arm in arms:
        def at(seq, i=-1): return summary[f"{arm}:{seq}"][i]
        comparisons[arm] = {
            "repeat_B_second_vs_isolated_B": {
                "isolated": at("isolated_B"), "second": at("repeat_B")},
            "B_value_second_vs_isolated_B": {
                "isolated_B": at("isolated_B"), "isolated_B_value": at("isolated_B_value"),
                "second": at("B_then_B_value")},
            "A_then_B_second_vs_isolated_B": {
                "isolated": at("isolated_B"), "second": at("A_then_B")},
            "B_then_A_second_vs_isolated_A": {
                "isolated": at("isolated_A"), "second": at("B_then_A")},
        }
    analysis = {"schema_version": 1,
                "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
                "lock_matches_pre_and_post_run": True, "arms": list(arms),
                "sequence_count": 14, "call_count": sum(len(r["events"]) for r in capture["runs"]),
                "signatures": {"B_vs_B_value_distinct": True,
                               "B_vs_B_value_same_operation_multiset": True,
                               "A_vs_B_different_operation_multiset": True},
                "comparisons": comparisons,
                "claim_boundary": "One authored gap family pair and argument-renamed variant; operation identity ignores argument roles/topology, and verification/outcome must be evaluated independently.",
                "event_rows": {k: v for k, v in summary.items()}}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "arms": 2,
                      "sequences": 14, "calls": analysis["call_count"]}, indent=2))


def GAPS_HEADS(label: str) -> list[list[str]]:
    runner_path = ROOT / "evaluation/substrate_capability/gap_grounder_operation_key_v1_2.py"
    # Read the frozen fixture definitions from the locked runner module namespace.
    import importlib.util
    spec = importlib.util.spec_from_file_location("gap_operation_runner", runner_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.GAPS[label]["observation"]


if __name__ == "__main__":
    main()
