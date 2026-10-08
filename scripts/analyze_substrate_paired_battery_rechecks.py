#!/usr/bin/env python3
"""Paired task-level reanalysis of the saved P6 and MBPP current rechecks.

This is a descriptive reanalysis of fixed benchmark task sets. It reports
discordant pairs and the exact two-sided McNemar/binomial test. It does not
turn benchmark tasks into an independent sample of natural-world tasks.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "p6": ROOT / "evaluation/reports/substrate_p6_current_recheck_20260925.json",
    "mbpp": ROOT / "evaluation/reports/substrate_mbpp_arc3_current_recheck_20260925.json",
}
OUTPUT = ROOT / "evaluation/reports/substrate_paired_battery_rechecks_analysis_20260930.json"
PASS_OUTCOMES = {"pass", "accepted_holdout_ok"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_mcnemar(gains: int, losses: int) -> dict[str, Any]:
    """Exact conditional two-sided binomial test on discordant task pairs."""
    n = gains + losses
    if n == 0:
        return {"discordant_n": 0, "two_sided_p": 1.0}
    low = min(gains, losses)
    p = min(1.0, 2.0 * sum(math.comb(n, j) for j in range(low + 1)) / (2**n))
    return {"discordant_n": n, "two_sided_p": p}


def get_rows(document: dict[str, Any], arm: str) -> list[dict[str, Any]]:
    data = document["arms"][arm]
    rows = data.get("rows") or data.get("runnable_rows")
    if not isinstance(rows, list):
        raise ValueError(f"arm {arm!r} has no row list")
    return rows


def analyze(path: Path, left_arm: str, right_arm: str) -> dict[str, Any]:
    document = json.loads(path.read_text())
    left_rows = get_rows(document, left_arm)
    right_rows = get_rows(document, right_arm)
    left = {str(row["task_id"]): row for row in left_rows}
    right = {str(row["task_id"]): row for row in right_rows}
    if len(left) != len(left_rows) or len(right) != len(right_rows):
        raise ValueError("duplicate task IDs")
    shared = sorted(left.keys() & right.keys())

    cells = {"both_pass": 0, "left_only_pass": 0, "right_only_pass": 0, "neither_pass": 0}
    strata: dict[str, dict[str, int]] = {}
    for task_id in shared:
        left_pass = left[task_id]["outcome"] in PASS_OUTCOMES
        right_pass = right[task_id]["outcome"] in PASS_OUTCOMES
        cell = (
            "both_pass" if left_pass and right_pass else
            "left_only_pass" if left_pass else
            "right_only_pass" if right_pass else
            "neither_pass"
        )
        cells[cell] += 1
        stratum = left[task_id].get("stratum") or "not_recorded"
        strata.setdefault(str(stratum), {key: 0 for key in cells})[cell] += 1

    gains, losses = cells["left_only_pass"], cells["right_only_pass"]
    n = len(shared)
    return {
        "input": str(path.relative_to(ROOT)),
        "input_sha256": sha256(path),
        "left_arm": left_arm,
        "right_arm": right_arm,
        "left_only_task_ids": [task_id for task_id in shared if
                               left[task_id]["outcome"] in PASS_OUTCOMES and
                               right[task_id]["outcome"] not in PASS_OUTCOMES],
        "right_only_task_ids": [task_id for task_id in shared if
                                right[task_id]["outcome"] in PASS_OUTCOMES and
                                left[task_id]["outcome"] not in PASS_OUTCOMES],
        "paired_cells": cells,
        "strata": strata,
        "paired_delta_left_minus_right": (gains - losses) / n if n else None,
        "paired_delta_percentage_points": 100.0 * (gains - losses) / n if n else None,
        "exact_mcnemar": exact_mcnemar(gains, losses),
        "interpretation_limit": (
            "Fixed-set paired reanalysis. The exact McNemar value summarizes discordance "
            "under task-level exchangeability; it is not evidence of generalization to "
            "natural task populations, and no task-family cluster adjustment is applied."
        ),
    }


def main() -> None:
    analyses = {
        "p6_main_vs_frozen": analyze(INPUTS["p6"], "main", "frozen"),
        "mbpp_full_r3_vs_no_retrieval": analyze(INPUTS["mbpp"], "full_r3", "no_retrieval"),
    }
    report = {
        "title": "Paired battery current-recheck reanalysis",
        "created_on": "2026-09-30",
        "method": "Task-ID alignment, binary strict held-out pass, discordance table, exact two-sided McNemar/binomial test.",
        "not_a_population_claim": True,
        "analyses": analyses,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
