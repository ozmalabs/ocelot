#!/usr/bin/env python3
"""Independent fixture/output and paired-result integrity analysis."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe/tasks.json"
RAW = ROOT / "evaluation/reports/substrate_string_pbe_transfer_pilot_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_string_pbe_transfer_analysis_20260926.json"
PARAMS = {
    "replace": [("a", "x"), ("e", "q"), ("-", "_"), ("A", "z")],
    "split": [",", "|", "-", ";"],
    "count": ["a", "th", "xy", "!"],
    "append": ["!", "__end", "?", " #"],
    "prefix": ["pre_", "[", "go:", "Z"],
    "fold_suffix": ["!", "::", "_done", "X"],
}


def expected(family: str, ordinal: int, value: str):
    arg = PARAMS[family][ordinal - 1]
    if family == "replace":
        old, new = arg
        return value.replace(old, new)
    if family == "split":
        return value.split(arg)
    if family == "count":
        return value.count(arg)
    if family == "append":
        return value + arg
    if family == "prefix":
        return arg + value
    if family == "fold_suffix":
        return value.casefold() + arg
    raise ValueError(family)


def main() -> None:
    suite = json.loads(FIXTURE.read_text())
    raw = json.loads(RAW.read_text())
    fixture_errors = []
    inputs_checked = 0
    for task in suite["tasks"]:
        family, ordinal_text = task["id"][len("string_"):].rsplit("_", 1)
        ordinal = int(ordinal_text)
        rows = task["example_rows"] + task["held_out_rows"]
        if len(task["example_rows"]) != 4 or len(task["held_out_rows"]) != 3:
            fixture_errors.append({"task": task["id"], "error": "split size"})
        if len({json.dumps(row["inputs"], sort_keys=True) for row in rows}) != 7:
            fixture_errors.append({"task": task["id"], "error": "duplicate inputs"})
        for row in rows:
            inputs_checked += 1
            got = expected(family, ordinal, row["inputs"]["s"])
            if got != row["expected"]:
                fixture_errors.append({"task": task["id"], "inputs": row["inputs"],
                                       "expected_in_fixture": row["expected"],
                                       "independent_value": got})
    arm_maps = {a: {r["task_id"]: r for r in raw["cases"][a]}
                for a in ("main", "frozen", "main_replication")}
    paired_errors = []
    for task_id in arm_maps["main"]:
        outcomes = {arm: arm_maps[arm][task_id]["outcome"] for arm in arm_maps}
        if len(set(outcomes.values())) != 1:
            paired_errors.append({"task_id": task_id, "outcomes": outcomes})
    payload = {
        "analysis": "substrate-string-pbe-transfer-independent-audit-v1",
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "tasks": len(suite["tasks"]), "input_outputs_checked": inputs_checked,
        "fixture_errors": fixture_errors,
        "paired_arm_outcome_errors": paired_errors,
        "per_family": {},
    }
    for family in PARAMS:
        task_ids = [t["id"] for t in suite["tasks"] if t["family"] == family]
        payload["per_family"][family] = {
            "tasks": len(task_ids),
            "main_outcomes": dict(Counter(arm_maps["main"][i]["outcome"] for i in task_ids)),
            "main_construction": dict(Counter(str(arm_maps["main"][i]["construction"])
                                               for i in task_ids)),
        }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
