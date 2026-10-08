#!/usr/bin/env python3
"""Fixed-bound GenInfer relation-count scaling probe."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line

engine_preamble()

from substrate_rs import _native  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_geninfer_relation_count_probe_v1_20260926.json"
MATRIX = [2, 1, 1, 1]
RELATION_COUNTS = (4, 8, 16, 32, 64)
REPETITIONS = 5
BASE_PATTERN = [[0, 0], [0, 1], [1, 0], [2, 0]]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_signatures(relation_count: int) -> tuple[list, list]:
    groups = relation_count // len(BASE_PATTERN)
    base, target = [], []
    for group in range(groups):
        pred = f"cell_{group}"
        for row, col in BASE_PATTERN:
            base.append([pred, row, col, "red"])
            target.append([pred, MATRIX[0] * row + MATRIX[1] * col,
                           MATRIX[2] * row + MATRIX[3] * col, "red"])
    return base, target


def main() -> None:
    conditions = {}
    for relation_count in RELATION_COUNTS:
        base, target = make_signatures(relation_count)
        sub = _native.Substrate()
        sub.add_node("ShapeSignature", {
            "name": f"base_{relation_count}", "signature": json.dumps(base),
            "kind": "faculty", "faculty": f"base_{relation_count}",
            "dim_types": ["pred", "coord:r", "coord:c", "val"]})
        term = {"type": "GenInfer", "goal": {"type": "Lit", "value": target},
                "codebook_type": "ShapeSignature", "max_dims": 2, "field": "matrix"}
        conditions[relation_count] = (sub, term, base, target)

    # Declared single untimed warm-up on the smallest relation-count fixture.
    conditions[4][0].evaluate(conditions[4][1], {})
    samples = []
    for repetition in range(REPETITIONS):
        for relation_count in RELATION_COUNTS:
            sub, term, base, target = conditions[relation_count]
            started = time.perf_counter()
            matrix = [int(x) for x in sub.evaluate(term, {})]
            elapsed = time.perf_counter() - started
            samples.append({"repetition": repetition + 1,
                            "relation_count": relation_count,
                            "base_relation_count": len(base),
                            "goal_relation_count": len(target),
                            "matrix": matrix,
                            "elapsed_seconds": elapsed})

    counts = {}
    for relation_count, (sub, term, _, _) in conditions.items():
        counts[str(relation_count)] = int(sub.evaluate({**term, "field": "checked"}, {}))

    extension = Path(_native.__file__).resolve()
    source_paths = (
        "scripts/geninfer_relation_count_probe_v1.py",
        "scripts/analyze_substrate_geninfer_relation_count_probe_v1.py",
        "docs/research/engine_substrate/SUBSTRATE_GENINFER_RELATION_COUNT_PREREG_20260926.md",
        "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
        "runners/dsl/python/substrate_rs/_native.build.json")
    report = {
        "schema_version": 1,
        "run_id": "substrate-geninfer-relation-count-probe-v1-20260926",
        "engine": provenance_line(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "protocol": {"relation_counts": list(RELATION_COUNTS),
                     "bound": 4, "matrix": MATRIX,
                     "candidate_count_per_call": 6560,
                     "repetitions": REPETITIONS,
                     "warmup": "one untimed call on the 4-relation fixture",
                     "timed_call": "direct GenInfer evaluation, field=matrix"},
        "provenance": {
            "source_sha256": {rel: sha(ROOT / rel) for rel in source_paths},
            "native_extension_path": str(extension),
            "native_extension_sha256": sha(extension)},
        "candidate_counts_by_relation_count": counts,
        "samples": samples,
        "claim_boundary": (
            "Fixed B=4 and one positive repeated motif, with 4–64 relations. "
            "No diverse-shape, higher-dimensional, closure, memory, or "
            "natural-task scaling claim."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": report["run_id"], "engine": report["engine"],
                      "samples": len(samples),
                      "candidate_counts_by_relation_count": counts,
                      "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
