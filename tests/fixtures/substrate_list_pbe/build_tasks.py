#!/usr/bin/env python3
"""Build a frozen list-transform PBE suite from explicit reference functions."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "tasks.json"

REVEALED = [
    [1, 2, 3], [-2, 0, 4], [5, 5, -1], [0, 7, -3, 2],
]
HELD_OUT = [[9, -4, 6], [-5, -1, 8, 0], [2, 2, 2, 2, 1]]

TASKS = [
    ("list_001_sum", "recurring_reduction", lambda xs: sum(xs)),
    ("list_002_length", "recurring_reduction", lambda xs: len(xs)),
    ("list_003_max", "recurring_reduction", lambda xs: max(xs)),
    ("list_004_min", "recurring_reduction", lambda xs: min(xs)),
    ("list_005_first", "recurring_projection", lambda xs: xs[0]),
    ("list_006_last", "recurring_projection", lambda xs: xs[-1]),
    ("list_007_reverse", "recurring_projection", lambda xs: list(reversed(xs))),
    ("list_008_map_plus_one", "recurring_map", lambda xs: [x + 1 for x in xs]),
    ("list_009_map_double", "recurring_map", lambda xs: [2 * x for x in xs]),
    ("list_010_map_abs", "recurring_map", lambda xs: [abs(x) for x in xs]),
    ("list_011_filter_positive", "recurring_filter", lambda xs: [x for x in xs if x > 0]),
    ("list_012_filter_negative", "recurring_filter", lambda xs: [x for x in xs if x < 0]),
    ("list_013_filter_gt_two", "recurring_filter", lambda xs: [x for x in xs if x > 2]),
    ("list_014_sum_positive", "recurring_composition", lambda xs: sum(x for x in xs if x > 0)),
    ("list_015_sum_squares", "recurring_composition", lambda xs: sum(x * x for x in xs)),
    ("list_016_count_positive", "recurring_composition", lambda xs: sum(x > 0 for x in xs)),
    ("list_017_sum_even", "recurring_composition", lambda xs: sum(x for x in xs if x % 2 == 0)),
    ("list_018_product", "recurring_reduction", lambda xs: __import__("math").prod(xs)),
    ("list_019_map_plus_three", "one_off_composition", lambda xs: [x + 3 for x in xs]),
    # Revealed rows deliberately make First and Last extensionally identical.
    ("list_020_last_degenerate", "adversarial_underdetermined", lambda xs: xs[-1]),
    # These two reference concepts require sorting or set construction, which
    # the frozen declared operator inventory does not include.
    ("list_021_median", "adversarial_out_of_inventory",
     lambda xs: sorted(xs)[len(xs) // 2]),
    ("list_022_unique_count", "adversarial_out_of_inventory",
     lambda xs: len(set(xs))),
]

ADV_REVEALED = [[1, 4, 1], [2, -3, 2], [5, 0, 5], [3, 9, 3]]
ADV_HELD_OUT = [[1, 4, 8], [7, 0, -2], [5, 3, 1]]
MED_REVEALED = [[1, 5, 3, 2, 4], [-2, 9, 0, 5, 1], [8, 4, 6, 2, 0], [7, -1, 3, 9, 5]]
MED_HELD_OUT = [[10, 0, 4, 6, 2], [-7, 1, 9, 3, 5], [11, 8, 4, 2, 6]]
UNIQUE_REVEALED = [[1, 1, 2, 2], [3, 3, 3], [-1, 0, -1, 0], [5, 6, 5, 6]]
UNIQUE_HELD_OUT = [[1, 2, 3, 4], [7, 7, -2], [0, 0, 0, 1, 1]]


def build() -> dict:
    tasks = []
    for task_id, category, fn in TASKS:
        train = ADV_REVEALED if task_id == "list_020_last_degenerate" else (
            MED_REVEALED if task_id == "list_021_median" else
            UNIQUE_REVEALED if task_id == "list_022_unique_count" else REVEALED)
        held = ADV_HELD_OUT if task_id == "list_020_last_degenerate" else (
            MED_HELD_OUT if task_id == "list_021_median" else
            UNIQUE_HELD_OUT if task_id == "list_022_unique_count" else HELD_OUT)
        tasks.append({
            "task_id": task_id,
            "category": category,
            "inputs": ["xs"],
            "revealed": [{"inputs": {"xs": xs}, "output": fn(xs)} for xs in train],
            "held_out": [{"inputs": {"xs": xs}, "output": fn(xs)} for xs in held],
        })
    return {
        "suite_id": "substrate-list-pbe-20260925-v1",
        "task_count": len(tasks),
        "design": "22 deterministic integer-list transformations with 4 revealed and 3 held-out rows each",
        "tasks": tasks,
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
