#!/usr/bin/env python3
"""Independent expected-output and paired-arm audit for the contrast pilot."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe_contrast/tasks.json"
RAW = ROOT / "evaluation/reports/substrate_string_pbe_contrast_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_string_pbe_contrast_analysis_20260925.json"
REPLACE = [("a", "x"), ("e", "q"), ("-", "_")]
SEPS = ["|", ",", ";"]
SUFFIXES = ["!", "::", "_done"]


def oracle(family: str, ordinal: int, s: str):
    if family == "replace_first":
        old, new = REPLACE[ordinal - 1]
        return s.replace(old, new, 1)
    if family == "reverse_split":
        return list(reversed(s.split(SEPS[ordinal - 1])))
    if family == "replace_all":
        old, new = REPLACE[ordinal - 1]
        return s.replace(old, new)
    if family == "reverse_string":
        return s[::-1]
    if family == "fold_suffix":
        return s.casefold() + SUFFIXES[ordinal - 1]
    if family == "fold_replace":
        old, new = REPLACE[ordinal - 1]
        return s.casefold().replace(old, new)
    raise ValueError(family)


def main() -> None:
    suite = json.loads(FIXTURE.read_text())
    raw = json.loads(RAW.read_text())
    fixture_errors = []
    inputs_checked = 0
    for task in suite["tasks"]:
        suffix = task["id"].rsplit("_", 1)[1]
        ordinal = int(suffix)
        family = task["family"]
        all_rows = task["example_rows"] + task["held_out_rows"]
        if len(task["example_rows"]) != 4 or len(task["held_out_rows"]) != 3:
            fixture_errors.append({"task": task["id"], "error": "split-size"})
        if len({json.dumps(r["inputs"], sort_keys=True) for r in all_rows}) != 7:
            fixture_errors.append({"task": task["id"], "error": "duplicate-input"})
        old = REPLACE[ordinal - 1][0] if family in ("replace_first", "replace_all", "fold_replace") else None
        sep = SEPS[ordinal - 1] if family == "reverse_split" else None
        if family == "replace_first":
            if not all(r["inputs"]["s"].count(old) == 1 for r in task["example_rows"]):
                fixture_errors.append({"task": task["id"], "error": "revealed-not-ambiguous"})
            if not all(r["inputs"]["s"].count(old) >= 2 for r in task["held_out_rows"]):
                fixture_errors.append({"task": task["id"], "error": "holdout-not-discriminating"})
        if family == "reverse_split":
            for r in task["example_rows"]:
                parts = r["inputs"]["s"].split(sep)
                if len(parts) != 2 or parts[0] != parts[1]:
                    fixture_errors.append({"task": task["id"], "error": "revealed-not-symmetric"})
            for r in task["held_out_rows"]:
                parts = r["inputs"]["s"].split(sep)
                if len(parts) != 3 or parts == list(reversed(parts)):
                    fixture_errors.append({"task": task["id"], "error": "holdout-not-discriminating"})
        if family == "replace_all" and not all(r["inputs"]["s"].count(old) >= 2 for r in all_rows):
            fixture_errors.append({"task": task["id"], "error": "replace-all-case-not-repeated"})
        for row in all_rows:
            inputs_checked += 1
            value = oracle(family, ordinal, row["inputs"]["s"])
            if value != row["expected"]:
                fixture_errors.append({"task": task["id"], "inputs": row["inputs"],
                                       "fixture": row["expected"], "oracle": value})
    arm_maps = {arm: {r["task_id"]: r for r in raw["cases"][arm]}
                for arm in ("main", "no_retrieval", "no_retrieval_escalated", "main_replay")}
    paired_mismatches = []
    for task_id in arm_maps["main"]:
        if (arm_maps["main"][task_id]["outcome"] !=
                arm_maps["main_replay"][task_id]["outcome"]):
            paired_mismatches.append(task_id)
    payload = {
        "analysis": "substrate-string-pbe-contrast-independent-audit-v1",
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "task_count": len(suite["tasks"]), "input_outputs_checked": inputs_checked,
        "fixture_errors": fixture_errors,
        "main_replay_outcome_mismatches": paired_mismatches,
        "arms": {},
    }
    for arm, tasks in arm_maps.items():
        payload["arms"][arm] = {
            "tasks": len(tasks),
            "outcomes": dict(Counter(r["outcome"] for r in tasks.values())),
            "per_family": {family: dict(Counter(r["outcome"] for r in tasks.values()
                                                    if r["family"] == family))
                           for family in sorted({t["family"] for t in suite["tasks"]})},
        }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
