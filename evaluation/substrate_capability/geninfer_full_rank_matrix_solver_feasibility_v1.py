#!/usr/bin/env python3
"""Measure an exact full-rank solver route for higher-dimensional GenInfer.

This is an algorithm-feasibility probe, not a native-engine benchmark. It
uses integer identity-aligned points, exact Fraction elimination, and held-out
points. The output explicitly separates solvable full-rank cases from rank-
deficient abstentions and records the current exhaustive search envelope.
"""
from __future__ import annotations

import hashlib
import json
import platform
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
OUT = ROOT / "evaluation/reports/geninfer_full_rank_matrix_solver_feasibility_v1_20261006.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FULL_RANK_MATRIX_SOLVER_FEASIBILITY_V1_PREREG_20261006.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_geninfer_full_rank_matrix_solver_feasibility_v1.py"
MATRICES = {
    1: [[-1]],
    2: [[1, 1], [0, 2]],
    3: [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_square(a: list[list[int]], b: list[list[int]]) -> list[list[Fraction]] | None:
    """Solve X*A=B exactly, returning X or None when A is rank deficient."""
    n = len(a)
    aug = [[Fraction(a[row][col]) for col in range(n)] +
           [Fraction(b[row][col]) for col in range(len(b[0]))] for row in range(n)]
    for col in range(n):
        pivot = next((row for row in range(col, n) if aug[row][col]), None)
        if pivot is None:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [v / scale for v in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [x - factor * y for x, y in zip(aug[row], aug[col])]
    return [row[n:] for row in aug]


def infer_full_rank(source: list[list[int]], target: list[list[int]], d: int):
    if len(source) != len(target) or len(source) < d + 1:
        return None
    origin = source[0]
    origin_out = target[0]
    # The first d independent displacement vectors form A's columns.
    basis: list[list[int]] = []
    outputs: list[list[int]] = []
    for x, y in zip(source[1:], target[1:]):
        candidate = [x[j] - origin[j] for j in range(d)]
        trial = [*basis, candidate]
        if _rank(trial) > len(basis):
            basis.append(candidate)
            outputs.append([y[j] - origin_out[j] for j in range(d)])
        if len(basis) == d:
            break
    if len(basis) != d:
        return None
    # A has source displacement vectors as columns; Y has their target vectors.
    # Rows of `basis` are source vectors, so this solves A^T M^T = Y^T.
    solved = solve_square(basis, outputs)
    if solved is None or any(v.denominator != 1 for row in solved for v in row):
        return None
    matrix = [[int(solved[j][i]) for j in range(d)] for i in range(d)]
    # Verify every training correspondence, including points outside the basis.
    for x, y in zip(source, target):
        normalized = [x[j] - origin[j] for j in range(d)]
        predicted = [origin_out[i] + sum(matrix[i][j] * normalized[j] for j in range(d))
                     for i in range(d)]
        if predicted != y:
            return None
    return matrix


def _rank(rows: list[list[int]]) -> int:
    if not rows:
        return 0
    a = [[Fraction(v) for v in row] for row in rows]
    rank = 0
    for col in range(len(a[0])):
        pivot = next((r for r in range(rank, len(a)) if a[r][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        scale = a[rank][col]
        a[rank] = [v / scale for v in a[rank]]
        for r in range(len(a)):
            if r != rank and a[r][col]:
                factor = a[r][col]
                a[r] = [x - factor * y for x, y in zip(a[r], a[rank])]
        rank += 1
        if rank == len(a):
            break
    return rank


def apply(matrix: list[list[int]], point: list[int]) -> list[int]:
    return [sum(v * point[j] for j, v in enumerate(row)) for row in matrix]


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rows = []
    for d, matrix in MATRICES.items():
        train = [[0] * d, *[[int(i == j) for i in range(d)] for j in range(d)],
                 [1] * d, [2 if i % 2 == 0 else 1 for i in range(d)]]
        heldout = [[3 if i == j else (1 if (i + j) % 2 else 0) for j in range(d)]
                   for i in range(d + 2)]
        train_out = [apply(matrix, x) for x in train]
        heldout_out = [apply(matrix, x) for x in heldout]
        t0 = time.perf_counter_ns()
        recovered = infer_full_rank(train, train_out, d)
        elapsed = time.perf_counter_ns() - t0
        heldout_exact = recovered is not None and [apply(recovered, x) for x in heldout] == heldout_out
        deficient = [[0] * d for _ in range(d + 2)]
        deficient_out = [apply(matrix, x) for x in deficient]
        deficient_result = infer_full_rank(deficient, deficient_out, d)
        bound = max(max(abs(v) for v in p) for p in train + train_out)
        rows.append({"dimension": d, "matrix": matrix, "training_points": len(train),
            "heldout_points": len(heldout), "recovered_matrix": recovered,
            "training_exact": recovered == matrix, "heldout_exact": heldout_exact,
            "training_source": train, "training_target": train_out,
            "heldout_source": heldout, "heldout_target": heldout_out,
            "rank_deficient_source": deficient, "rank_deficient_target": deficient_out,
            "solver_wall_ns": elapsed, "rank_deficient_abstained": deficient_result is None,
            "rank_deficient_result": deficient_result, "matrix_bound": bound,
            "exhaustive_candidate_count": (2 * bound + 1) ** (d * d) - 1})
    payload = {"schema": "GenInferFullRankMatrixSolverFeasibilityV1",
        "runner_sha256": sha(RUNNER), "analyzer_sha256": sha(ANALYZER),
        "protocol_sha256": sha(PROTOCOL),
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.platform(), "cases": rows,
        "interpretation_limit": "Exact algorithm feasibility on authored integer fixtures only; not a native Substrate or production timing result."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "cases": len(rows),
                      "all_exact": all(r["training_exact"] and r["heldout_exact"] and r["rank_deficient_abstained"] for r in rows),
                      "candidate_counts": [r["exhaustive_candidate_count"] for r in rows]}, indent=2))


if __name__ == "__main__":
    main()
