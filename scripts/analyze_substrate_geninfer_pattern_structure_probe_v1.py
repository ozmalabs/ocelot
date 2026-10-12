#!/usr/bin/env python3
"""Independent validation and descriptive factorial summary for GenInfer shapes."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_geninfer_pattern_structure_v1_20260926.json"
OUTPUT = ROOT / "evaluation/reports/substrate_geninfer_pattern_structure_v1_analysis_20260926.json"
SHAPES = {
    "elbow": [(0, 0), (0, 1), (1, 0), (2, 0)],
    "staircase": [(0, 0), (0, 1), (1, 1), (2, 0)],
    "branch": [(0, 0), (1, 0), (1, 1), (2, 0)],
    "long_arm": [(0, 0), (0, 1), (1, 0), (1, 2)],
}
GROUPINGS = {
    "shared": ["cell"] * 4,
    "paired": ["cell_a", "cell_a", "cell_b", "cell_b"],
    "unique": [f"cell_{i}" for i in range(4)],
}
MATRIX = [2, 1, 1, 1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    expected_cells = {(shape, grouping) for shape in SHAPES for grouping in GROUPINGS}
    grouped = defaultdict(list)
    for sample in raw["samples"]:
        grouped[(sample["shape"], sample["predicate_grouping"])].append(sample)
    derived = {}
    for shape, points in SHAPES.items():
        target = [(MATRIX[0] * r + MATRIX[1] * c,
                   MATRIX[2] * r + MATRIX[3] * c) for r, c in points]
        base_bound = max(max(r for r, _ in points) - min(r for r, _ in points),
                         max(c for _, c in points) - min(c for _, c in points))
        goal_bound = max(max(r for r, _ in target) - min(r for r, _ in target),
                         max(c for _, c in target) - min(c for _, c in target))
        derived[shape] = {"base": [[p, r, c, "red"] for p, (r, c) in zip(GROUPINGS["shared"], points)],
                          "target_shared": [[p, r, c, "red"] for p, (r, c) in zip(GROUPINGS["shared"], target)],
                          "base_bound": base_bound, "goal_bound": goal_bound,
                          "search_bound": max(base_bound, goal_bound)}
    schedule = raw["protocol"].get("schedule_by_repetition", {})
    schedule_ok = set(schedule) == {str(i) for i in range(1, 6)} and all(
        len(schedule[str(i)]) == len(expected_cells)
        and {tuple(cell) for cell in schedule[str(i)]} == expected_cells for i in range(1, 6))
    checks = {
        "exact_factorial_cells_present": set(grouped) == expected_cells,
        "five_samples_per_cell": all(len(grouped[cell]) == 5 for cell in expected_cells),
        "exact_locked_shape_and_group_definitions": (
            raw["shape_coordinates"] == {k: [list(x) for x in v] for k, v in SHAPES.items()}
            and raw["predicate_labels"] == GROUPINGS),
        "relation_counts_exact": all(s["base_relation_count"] == 4 and s["goal_relation_count"] == 4
            for samples in grouped.values() for s in samples),
        "fixed_candidate_bound_derived": all(row["search_bound"] == 4 for row in derived.values())
            and raw["protocol"]["bound"] == 4
            and raw["protocol"]["candidate_count_per_call"] == 6560
            and all(int(v) == 6560 for v in raw["candidate_counts"].values()),
        "every_call_recovers_locked_matrix": all(s["matrix"] == MATRIX
            for samples in grouped.values() for s in samples),
        "positive_finite_timing_samples": all(math.isfinite(float(s["elapsed_seconds"]))
            and float(s["elapsed_seconds"]) > 0 for samples in grouped.values() for s in samples),
        "deterministic_balanced_schedule": schedule_ok
            and raw["protocol"]["schedule_seed"] == 20260926
            and len(raw["samples"]) == 60,
        "native_hash_current": sha(Path(raw["provenance"]["native_extension_path"]))
            == raw["provenance"]["native_extension_sha256"],
        "source_hashes_current": all(sha(ROOT / rel) == digest
            for rel, digest in raw["provenance"]["source_sha256"].items()),
    }
    by_cell = {}
    for cell in sorted(expected_cells):
        times = [float(s["elapsed_seconds"]) for s in grouped[cell]]
        by_cell[f"{cell[0]}/{cell[1]}"] = {"samples": len(times),
            "median_seconds": statistics.median(times), "min_seconds": min(times),
            "max_seconds": max(times), "candidate_count_per_call": 6560}
    by_shape = {}
    for shape in SHAPES:
        vals = [by_cell[f"{shape}/{group}"]["median_seconds"] for group in GROUPINGS]
        by_shape[shape] = {"mean_of_group_medians_seconds": statistics.mean(vals),
            "median_of_group_medians_seconds": statistics.median(vals)}
    by_grouping = {}
    for grouping in GROUPINGS:
        vals = [by_cell[f"{shape}/{grouping}"]["median_seconds"] for shape in SHAPES]
        by_grouping[grouping] = {"mean_of_shape_medians_seconds": statistics.mean(vals),
            "median_of_shape_medians_seconds": statistics.median(vals)}
    result = {"schema_version": 1, "source": str(SOURCE.relative_to(ROOT)),
        "checks": checks, "all_checks_pass": all(checks.values()),
        "derived_shape_bounds": derived, "by_cell": by_cell,
        "descriptive_geometry_summary": by_shape,
        "descriptive_predicate_grouping_summary": by_grouping,
        "interpretation": "All 12 authored positive cells recover the same transform at B=4 and four relations; timings only describe geometry/predicate effects inside this 2-D linear class."}
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUTPUT), "all_checks_pass": result["all_checks_pass"],
        "checks": checks, "descriptive_geometry_summary": by_shape,
        "descriptive_predicate_grouping_summary": by_grouping}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
