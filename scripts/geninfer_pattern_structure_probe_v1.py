#!/usr/bin/env python3
"""Factorial GenInfer probe over geometry and predicate grouping at fixed search bound."""
from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line

engine_preamble()
from substrate_rs import _native  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_geninfer_pattern_structure_v1_20260926.json"
MATRIX = [2, 1, 1, 1]
SHAPES = {
    "elbow": [(0, 0), (0, 1), (1, 0), (2, 0)],
    "staircase": [(0, 0), (0, 1), (1, 1), (2, 0)],
    "branch": [(0, 0), (1, 0), (1, 1), (2, 0)],
    "long_arm": [(0, 0), (0, 1), (1, 0), (1, 2)],
}
GROUPINGS = ("shared", "paired", "unique")
REPETITIONS = 5
SCHEDULE_SEED = 20260926


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def predicate_labels(grouping: str) -> list[str]:
    if grouping == "shared":
        return ["cell"] * 4
    if grouping == "paired":
        return ["cell_a", "cell_a", "cell_b", "cell_b"]
    if grouping == "unique":
        return [f"cell_{i}" for i in range(4)]
    raise ValueError(grouping)


def signatures(shape: str, grouping: str) -> tuple[list, list]:
    labels = predicate_labels(grouping)
    base, target = [], []
    for predicate, (row, col) in zip(labels, SHAPES[shape]):
        base.append([predicate, row, col, "red"])
        target.append([predicate, MATRIX[0] * row + MATRIX[1] * col,
                       MATRIX[2] * row + MATRIX[3] * col, "red"])
    return base, target


def main() -> None:
    conditions = {}
    for shape in SHAPES:
        for grouping in GROUPINGS:
            base, target = signatures(shape, grouping)
            sub = _native.Substrate()
            sub.add_node("ShapeSignature", {"name": f"{shape}_{grouping}",
                "signature": json.dumps(base), "kind": "faculty",
                "faculty": f"{shape}_{grouping}",
                "dim_types": ["pred", "coord:r", "coord:c", "val"]})
            term = {"type": "GenInfer", "goal": {"type": "Lit", "value": target},
                "codebook_type": "ShapeSignature", "max_dims": 2, "field": "matrix"}
            conditions[(shape, grouping)] = {"substrate": sub, "term": term,
                "base": base, "target": target}

    # One declared untimed warm-up on the first fixed cell.
    first = conditions[("elbow", "shared")]
    first["substrate"].evaluate(first["term"], {})
    samples = []
    rng = random.Random(SCHEDULE_SEED)
    schedule_by_repetition = {}
    for repetition in range(1, REPETITIONS + 1):
        schedule = list(conditions)
        rng.shuffle(schedule)
        schedule_by_repetition[str(repetition)] = [[shape, grouping] for shape, grouping in schedule]
        for shape, grouping in schedule:
            cell = conditions[(shape, grouping)]
            started = time.perf_counter()
            matrix = [int(value) for value in cell["substrate"].evaluate(cell["term"], {})]
            elapsed = time.perf_counter() - started
            samples.append({"repetition": repetition, "shape": shape,
                "predicate_grouping": grouping, "base_relation_count": len(cell["base"]),
                "goal_relation_count": len(cell["target"]), "matrix": matrix,
                "elapsed_seconds": elapsed})

    candidate_counts = {}
    for (shape, grouping), cell in conditions.items():
        candidate_counts[f"{shape}/{grouping}"] = int(cell["substrate"].evaluate(
            {**cell["term"], "field": "checked"}, {}))

    extension = Path(_native.__file__).resolve()
    source_paths = ("scripts/geninfer_pattern_structure_probe_v1.py",
        "scripts/analyze_substrate_geninfer_pattern_structure_probe_v1.py",
        "docs/research/engine_substrate/SUBSTRATE_GENINFER_PATTERN_STRUCTURE_PREREG_20260926.md",
        "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
        "runners/dsl/python/substrate_rs/_native.build.json")
    report = {"schema_version": 1,
        "run_id": "substrate-geninfer-pattern-structure-v1-20260926",
        "engine": provenance_line(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "protocol": {"shapes": list(SHAPES), "predicate_groupings": list(GROUPINGS),
            "matrix": MATRIX, "relation_count": 4, "bound": 4,
            "candidate_count_per_call": 6560, "repetitions": REPETITIONS,
            "schedule_seed": SCHEDULE_SEED, "schedule_by_repetition": schedule_by_repetition,
            "warmup": "one untimed evaluation on elbow/shared",
            "timed_call": "direct GenInfer evaluation, field=matrix"},
        "shape_coordinates": {key: [list(x) for x in value] for key, value in SHAPES.items()},
        "predicate_labels": {key: predicate_labels(key) for key in GROUPINGS},
        "candidate_counts": candidate_counts, "samples": samples,
        "provenance": {"source_sha256": {rel: sha(ROOT / rel) for rel in source_paths},
            "native_extension_path": str(extension), "native_extension_sha256": sha(extension)},
        "claim_boundary": "Twelve small positive 2-D structures in one linear transform class; no noise, negative, higher-dimensional, closure, minting, or natural-task inference."}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": report["run_id"], "cells": len(conditions),
        "samples": len(samples), "candidate_counts": candidate_counts, "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
