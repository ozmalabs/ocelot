#!/usr/bin/env python3
"""Generate a held-out list-PBE evaluation matrix for the P4 route pilot."""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "tasks.json"


def even(xs):
    return [x for x in xs if x % 2 == 0]


def positive(xs):
    return [x for x in xs if x > 0]


def negative(xs):
    return [x for x in xs if x < 0]


def abs_list(xs):
    return [abs(x) for x in xs]


TASK_SPECS = [
    ("fresh_001_sum", "reduction", "returns the sum of the list", lambda x: sum(x), None),
    ("fresh_002_length", "reduction", "returns the number of items in the list", lambda x: len(x), None),
    ("fresh_003_max", "reduction", "returns the largest item in the list", lambda x: max(x), None),
    ("fresh_004_min", "reduction", "returns the smallest item in the list", lambda x: min(x), None),
    ("fresh_005_first", "projection", "returns the first item in the list", lambda x: x[0], None),
    ("fresh_006_last", "projection", "returns the last item in the list", lambda x: x[-1], None),
    ("fresh_007_reverse", "projection", "returns the list in reverse order", lambda x: list(reversed(x)), None),
    ("fresh_008_map_plus_two", "map", "adds two to every item in the list", lambda x: [v + 2 for v in x], None),
    ("fresh_009_map_plus_five", "map", "adds five to every item in the list", lambda x: [v + 5 for v in x], None),
    ("fresh_010_map_minus_three", "map", "subtracts three from every item in the list", lambda x: [v - 3 for v in x], None),
    ("fresh_011_map_times_three", "map", "multiplies every item in the list by three", lambda x: [v * 3 for v in x], None),
    ("fresh_012_absolute_values", "map", "replaces every item with its absolute value", abs_list, None),
    ("fresh_013_filter_gt_two", "filter", "keeps only items greater than two", lambda x: [v for v in x if v > 2], None),
    ("fresh_014_filter_gt_minus_one", "filter", "keeps only items greater than negative one", lambda x: [v for v in x if v > -1], None),
    ("fresh_015_filter_lt_zero", "filter", "keeps only negative items", negative, None),
    ("fresh_016_filter_even", "filter", "keeps only even items", even, None),
    ("fresh_017_filter_zero", "filter", "keeps only items equal to zero", lambda x: [v for v in x if v == 0], "zero"),
    ("fresh_018_sum_positive", "composition", "returns the sum of only the positive items", lambda x: sum(positive(x)), None),
    ("fresh_019_sum_negative", "composition", "returns the sum of only the negative items", lambda x: sum(negative(x)), None),
    ("fresh_020_sum_squares", "composition", "returns the sum of the squares of all items", lambda x: sum(v * v for v in x), None),
    ("fresh_021_sum_even", "composition", "returns the sum of only the even items", lambda x: sum(even(x)), None),
    ("fresh_022_count_positive", "composition", "counts the positive items", lambda x: len(positive(x)), None),
    ("fresh_023_product", "reduction", "returns the product of all items", lambda x: __import__("math").prod(x), None),
    ("fresh_024_reverse_positive", "composition", "keeps positive items and returns them in reverse order", lambda x: list(reversed(positive(x))), None),
    ("fresh_025_sum_absolute", "composition", "returns the sum of the absolute values of the items", lambda x: sum(abs_list(x)), None),
    ("fresh_026_length_positive", "composition", "returns how many positive items are in the list", lambda x: len(positive(x)), None),
    ("fresh_027_count_even", "composition", "counts the even items in the list", lambda x: len(even(x)), None),
    ("fresh_028_min_positive", "composition", "returns the smallest positive item", lambda x: min(positive(x)), "positive"),
    ("fresh_029_median", "out_of_inventory", "returns the median item in the list", lambda x: sorted(x)[len(x) // 2], None),
    ("fresh_030_unique_count", "out_of_inventory", "counts the distinct items in the list", lambda x: len(set(x)), None),
]


def examples_for(index: int, constraint: str | None):
    rng = random.Random(920260925 + index * 7919)
    rows = []
    while len(rows) < 7:
        size = rng.randint(3, 7)
        xs = [rng.randint(-9, 12) for _ in range(size)]
        if constraint == "positive" and not any(v > 0 for v in xs):
            continue
        if constraint == "zero" and 0 not in xs:
            continue
        row = {"xs": xs}
        if any(existing["inputs"] == row for existing in rows):
            continue
        rows.append({"inputs": row, "expected": None})
    return rows


def build():
    tasks = []
    for index, (task_id, category, description, fn, constraint) in enumerate(TASK_SPECS, 1):
        rows = examples_for(index, constraint)
        for row in rows:
            row["expected"] = fn(row["inputs"]["xs"])
        tasks.append({
            "id": task_id,
            "family": category,
            "request_text": f"Write a function that {description}.",
            "example_rows": rows[:4],
            "held_out_rows": rows[4:],
        })
    return {
        "suite_id": "substrate-list-pbe-compositions-20260925-v1",
        "task_count": len(tasks),
        "design": "30 integer-list concepts across reductions, projections, maps, filters, compositions, and out-of-inventory controls; 4 revealed and 3 held-out examples per task",
        "generation_seed_rule": "per-task Python random.Random(920260925 + one_based_index * 7919)",
        "tasks": tasks,
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
