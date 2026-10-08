#!/usr/bin/env python3
"""Exact-rational fixture identifiability check for a bounded 2-D quadratic map."""
from __future__ import annotations

import itertools
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/nonlinear_quadratic_basis_preflight_v1_20261006.json"
TRAIN = [(1, 0), (2, 0), (0, 1), (0, 2), (1, 1)]
VALIDATION_POINTS = [(3, 1), (4, 1)]
TRANSFER = [(2, 1), (1, 3), (3, 2), (2, 3), (5, 1), (3, 3)]
OLD_TRAIN = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)]
COUPLED_QUADRATIC = lambda x, y: (x + x * y, y + x * x)


def features(point: tuple[int, int]) -> list[Fraction]:
    x, y = point
    return list(map(Fraction, (x, y, x * x, x * y, y * y)))


def rref_rank(matrix: list[list[Fraction]]) -> tuple[int, list[list[Fraction]]]:
    a = [row[:] for row in matrix]
    rows, cols = len(a), len(a[0]) if a else 0
    pivot_row = 0
    pivots = []
    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if a[r][col]), None)
        if pivot is None:
            continue
        a[pivot_row], a[pivot] = a[pivot], a[pivot_row]
        q = a[pivot_row][col]
        a[pivot_row] = [v / q for v in a[pivot_row]]
        for r in range(rows):
            if r != pivot_row and a[r][col]:
                q = a[r][col]
                a[r] = [u - q * v for u, v in zip(a[r], a[pivot_row])]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == rows:
            break
    return len(pivots), a


def solve_unique(a: list[list[Fraction]], y: list[Fraction]) -> list[Fraction] | None:
    aug = [row[:] + [target] for row, target in zip(a, y)]
    rank, red = rref_rank(aug)
    coefficient_rank, _ = rref_rank(a)
    if coefficient_rank != len(a[0]) or rank != coefficient_rank:
        return None
    return [red[i][-1] for i in range(coefficient_rank)]


def determinant(matrix: list[list[Fraction]]) -> Fraction:
    a = [row[:] for row in matrix]
    result = Fraction(1)
    for i in range(len(a)):
        pivot = next((r for r in range(i, len(a)) if a[r][i]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != i:
            a[i], a[pivot] = a[pivot], a[i]
            result = -result
        q = a[i][i]
        result *= q
        for r in range(i + 1, len(a)):
            factor = a[r][i] / q
            for c in range(i + 1, len(a)):
                a[r][c] -= factor * a[i][c]
            a[r][i] = 0
    return result


def affine_linear_fits(points: list[tuple[int, int]], outputs: list[tuple[int, int]], bound: int) -> list[list[int]]:
    matches = []
    lower, upper = range(-bound, bound + 1), range(-bound, bound + 1)
    for matrix in itertools.product(lower, repeat=4):
        residuals = []
        for (x, y), (u, v) in zip(points, outputs):
            residuals.append((u - matrix[0] * x - matrix[1] * y,
                              v - matrix[2] * x - matrix[3] * y))
        if residuals and all(r == residuals[0] for r in residuals):
            matches.append([*matrix, *residuals[0]])
    return matches


def main() -> int:
    basis_design = [features(p) for p in TRAIN]
    all_train = TRAIN + VALIDATION_POINTS
    all_features = [features(p) for p in all_train]
    reference_features = all_features[0]
    design = [[u - v for u, v in zip(row, reference_features)] for row in all_features[1:]]
    train_outputs = [COUPLED_QUADRATIC(*p) for p in all_train]
    transfer_origin = (min(x for x, _ in TRANSFER), min(y for _, y in TRANSFER))
    transfer_outputs = [COUPLED_QUADRATIC(x - transfer_origin[0], y - transfer_origin[1])
                        for x, y in TRANSFER]
    reference_output = train_outputs[0]
    coeffs = [solve_unique(design, [Fraction(v[axis] - reference_output[axis])
                                     for v in train_outputs[1:]])
              for axis in range(2)]
    if any(c is None or any(v.denominator != 1 for v in c) for c in coeffs):
        raise SystemExit("registered target did not yield unique integer coefficients")
    recovered = [[int(v) for v in c] for c in coeffs]
    predicted_transfer = [tuple(sum(c[j] * int(features((p[0] - transfer_origin[0], p[1] - transfer_origin[1]))[j])
                                     for j in range(5)) for c in recovered) for p in TRANSFER]
    old_design = [features(p) for p in OLD_TRAIN]
    linear_fits = affine_linear_fits(all_train, train_outputs, 8)
    cubic_outputs = [(x, y + x ** 3) for x, y in all_train]
    cubic_coefficients = [solve_unique(design,
        [Fraction(v[axis] - cubic_outputs[0][axis]) for v in cubic_outputs[1:]])
        for axis in range(2)]
    cubic_refused = any(c is None for c in cubic_coefficients)
    result = {
        "schema": "NonlinearQuadraticBasisPreflightV1",
        "family": "F(x,y)=(x+x*y,y+x^2)",
        "basis_order": ["x", "y", "x^2", "x*y", "y^2"],
        "training_points": [list(p) for p in TRAIN],
        "training_validation_points": [list(p) for p in VALIDATION_POINTS],
        "training_design_rank": rref_rank(design)[0],
        "training_basis_determinant": str(determinant(basis_design)),
        "recovered_integer_coefficients": recovered,
        "transfer_points": [list(p) for p in TRANSFER],
        "transfer_normalization_origin": list(transfer_origin),
        "transfer_outputs": [list(p) for p in transfer_outputs],
        "exact_transfer_match": predicted_transfer == transfer_outputs,
        "bounded_affine_linear_fits_at_entry_bound_8": len(linear_fits),
        "cubic_x3_in_family_refused_by_overdetermined_difference_fit": cubic_refused,
        "previous_v1_5_training_points": [list(p) for p in OLD_TRAIN],
        "previous_training_feature_rank": rref_rank(old_design)[0],
        "previous_training_has_x_squared_alias": all(x * x == x for x, _ in OLD_TRAIN),
        "interpretation_limit": "fixture identifiability preflight only; no engine learner was evaluated",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(),
        "rank": result["training_design_rank"], "determinant": result["training_basis_determinant"],
        "exact_transfer_match": result["exact_transfer_match"],
        "bounded_affine_linear_fits": result["bounded_affine_linear_fits_at_entry_bound_8"],
        "previous_training_rank": result["previous_training_feature_rank"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
