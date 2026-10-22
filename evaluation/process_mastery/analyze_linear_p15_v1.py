"""P15 scorecard integrity analyzer; no outcomes are imputed or rescored."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARMS = {"unchanged_operator", "adaptive_curriculum", "full_system"}


def analyze(payload):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    meta = payload.get("metadata", {})
    if meta.get("phase") != "linear-p15-v1" or meta.get("split") != "development":
        raise ValueError("scorecard phase/split mismatch")
    if meta.get("human_comparison") != "UNAVAILABLE_PROTOCOL_NOT_MATCHED":
        raise ValueError("unsupported human comparison claim")
    rows = payload.get("records")
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty scorecard")
    paired = defaultdict(dict)
    failures = {"status": 0, "pairing": 0, "world": 0, "inputs": 0,
                "invariants": 0, "actions": 0, "work": 0, "family": 0}
    for row in rows:
        if row.get("family") != "permutation_process_macro":
            failures["family"] += 1
        arm, seed = row.get("profile"), row.get("seed")
        if arm not in ARMS or arm in paired[seed]:
            failures["pairing"] += 1
            continue
        paired[seed][arm] = row
        failures["status"] += row.get("status") != "COMPLETED"
        audit = row.get("input_audit", {})
        failures["inputs"] += int(not all(audit.get(k) is True for k in
            ("answer_fields_absent", "hidden_strategy_absent", "sealed_ids_absent")))
        failures["invariants"] += int(row.get("invariant_checks_passed") != 1)
        failures["actions"] += int(row.get("actions") != 0)
        expected_work = (2 * int(row.get("generation", 0)) + 2
                         if arm == "full_system" else 1)
        failures["work"] += int(row.get("agent_work_units") != expected_work)
    n_per_generation = int(meta.get("n_per_generation_per_arm", 0))
    generations = meta.get("completed_generations", [])
    expected_n = n_per_generation * len(generations)
    for seed, group in paired.items():
        failures["pairing"] += int(set(group) != ARMS)
        failures["world"] += int(len({r.get("world_sha256") for r in group.values()}) != 1)
        failures["world"] += int(len({r.get("world_access_sha256") for r in group.values()}) != 1)
    failures["pairing"] += int(len(paired) != expected_n)
    rates = {}
    for arm in sorted(ARMS):
        values = [bool(group[arm].get("solved")) for group in paired.values() if arm in group]
        rates[arm] = {"solved": sum(values), "n": len(values),
                      "accuracy": sum(values) / len(values) if values else None}
    by_generation = {}
    for generation in generations:
        by_generation[str(generation)] = {}
        for arm in sorted(ARMS):
            values = [bool(row.get("solved")) for row in rows
                      if row.get("generation") == generation and row.get("profile") == arm]
            by_generation[str(generation)][arm] = {
                "solved": sum(values), "n": len(values),
                "accuracy": sum(values) / len(values) if values else None}
    integrity_failures = sum(failures.values())
    return {"schema": "pmb-linear-p15-v1-analysis-v1", "phase": meta["phase"],
            "split": meta["split"], "family": "permutation_process_macro",
            "paired_tasks": len(paired), "arms": rates, "by_generation": by_generation,
            "integrity_failures": failures,
            "integrity_status": "PASS" if integrity_failures == 0 else "FAIL",
            "full_vs_unchanged_difference": (
                rates["full_system"]["accuracy"] - rates["unchanged_operator"]["accuracy"]
                if rates["full_system"]["accuracy"] is not None
                and rates["unchanged_operator"]["accuracy"] is not None else None),
            "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED",
            "claim_boundary": "development adapter integrity and outcomes only; no trend or efficacy claim"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        from evaluation.process_mastery.linear_p15_v1 import run
        payload = run(n=2, self_check=True)
    elif args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        parser.error("provide a scorecard or --self-check")
    result = analyze(payload)
    if result["integrity_status"] != "PASS":
        raise SystemExit(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
