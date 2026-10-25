"""Offline full-information change-of-basis and metric reference.

This module is diagnostic only. It cannot select agent frames or candidates.
The paper's rounded Eq. 4 matrix is frozen as a particular approximate map;
invariance claims here are mathematical checks for that defined matrix, not a
claim that the printed values reproduce the article's original full-precision
empirical coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np

from evaluation.ousiometrics.source_manifest import PAPER_TRANSFORM


PAPER_EQ4_DISPLAY = np.asarray(PAPER_TRANSFORM["printed_vad_to_pds"], dtype=np.float64)
GPADS_FROM_GAS = np.asarray([
    [1.0, 0.0, 0.0],
    [1 / math.sqrt(2), 1 / math.sqrt(2), 0.0],
    [0.0, 1.0, 0.0],
    [-1 / math.sqrt(2), 1 / math.sqrt(2), 0.0],
    [0.0, 0.0, 1.0],
], dtype=np.float64)


@dataclass(frozen=True)
class TransformAudit:
    dimension: int
    rank: int
    determinant: float
    condition_number_2: float
    max_abs_inverse_error: float
    precision_note: str


def _matrix(value: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not matrix.size:
        raise ValueError("transform must be a nonempty square matrix")
    if not np.isfinite(matrix).all():
        raise ValueError("transform must contain only finite values")
    return matrix


def inverse(transform: Sequence[Sequence[float]] | np.ndarray, *, max_condition: float = 1e10) -> np.ndarray:
    matrix = _matrix(transform)
    rank = int(np.linalg.matrix_rank(matrix))
    condition = float(np.linalg.cond(matrix, 2))
    if rank != matrix.shape[0] or not math.isfinite(condition) or condition > max_condition:
        raise ValueError("transform is singular or ill-conditioned for the declared bound")
    return np.linalg.inv(matrix)


def source_normalize_vad(values: Iterable[Iterable[float]]) -> np.ndarray:
    """Center NRC source V/A/D values from [0,1] by the paper's 0.5 shift."""
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != 3 or not np.isfinite(matrix).all():
        raise ValueError("VAD source values must be finite rows of exactly three coordinates")
    if np.any(matrix < 0.0) or np.any(matrix > 1.0):
        raise ValueError("VAD source values outside the declared [0,1] units")
    return matrix - 0.5


def transform_rows(values: Iterable[Iterable[float]], transform: Sequence[Sequence[float]]) -> np.ndarray:
    matrix = _matrix(transform)
    rows = np.asarray(values, dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1] != matrix.shape[1] or not np.isfinite(rows).all():
        raise ValueError("coordinate rows must be finite and match transform dimension")
    return rows @ matrix.T


def inverse_rows(values: Iterable[Iterable[float]], transform: Sequence[Sequence[float]]) -> np.ndarray:
    matrix = _matrix(transform)
    inverse_matrix = inverse(matrix)
    rows = np.asarray(values, dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1] != matrix.shape[0] or not np.isfinite(rows).all():
        raise ValueError("coordinate rows must be finite and match inverse dimension")
    return rows @ inverse_matrix.T


def audit_transform(transform: Sequence[Sequence[float]] = PAPER_EQ4_DISPLAY) -> TransformAudit:
    matrix = _matrix(transform)
    inverse_matrix = inverse(matrix)
    round_trip = matrix @ inverse_matrix
    return TransformAudit(
        dimension=matrix.shape[0], rank=int(np.linalg.matrix_rank(matrix)),
        determinant=float(np.linalg.det(matrix)),
        condition_number_2=float(np.linalg.cond(matrix, 2)),
        max_abs_inverse_error=float(np.max(np.abs(round_trip - np.eye(matrix.shape[0])))),
        precision_note="computed float64 inverse of frozen coefficients; paper Eq. 4 is rounded display",
    )


def transported_linear_weights(weights_source: Iterable[float], transform: Sequence[Sequence[float]]) -> np.ndarray:
    matrix = _matrix(transform)
    weights = np.asarray(weights_source, dtype=np.float64)
    if weights.shape != (matrix.shape[1],) or not np.isfinite(weights).all():
        raise ValueError("linear weights must be a finite vector matching source dimension")
    # For y=T x and f(x)=wᵀx, f(y)=(T⁻ᵀw)ᵀy.
    return np.linalg.solve(matrix.T, weights)


def linear_predictions(rows: Iterable[Iterable[float]], weights: Iterable[float], bias: float = 0.0) -> np.ndarray:
    values = np.asarray(rows, dtype=np.float64)
    vector = np.asarray(weights, dtype=np.float64)
    if values.ndim != 2 or vector.shape != (values.shape[1],) or not np.isfinite(values).all() or not np.isfinite(vector).all() or not math.isfinite(bias):
        raise ValueError("prediction inputs must be finite and dimension-matched")
    return values @ vector + float(bias)


def l1_distance(left: Iterable[float], right: Iterable[float]) -> float:
    a, b = np.asarray(left, dtype=np.float64), np.asarray(right, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("distance coordinates must be finite vectors with equal dimensions")
    return float(np.sum(np.abs(a - b)))


def transported_l1_distance(left_transformed: Iterable[float], right_transformed: Iterable[float], transform: Sequence[Sequence[float]]) -> float:
    matrix = _matrix(transform)
    left, right = np.asarray(left_transformed, dtype=np.float64), np.asarray(right_transformed, dtype=np.float64)
    if left.shape != (matrix.shape[0],) or right.shape != left.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("transformed distance coordinates must be finite and dimension-matched")
    return l1_distance(inverse(matrix) @ left, inverse(matrix) @ right)


def transported_quadratic_metric(metric_source: Sequence[Sequence[float]], transform: Sequence[Sequence[float]]) -> np.ndarray:
    matrix = _matrix(transform)
    metric = _matrix(metric_source)
    if metric.shape != matrix.shape:
        raise ValueError("source metric and transform dimensions must match")
    inv = inverse(matrix)
    return inv.T @ metric @ inv


def neighbor_order(query: Iterable[float], candidates: Sequence[Iterable[float]]) -> list[int]:
    return sorted(range(len(candidates)), key=lambda i: (l1_distance(query, candidates[i]), i))


def transported_neighbor_order(query_y: Iterable[float], candidates_y: Sequence[Iterable[float]], transform: Sequence[Sequence[float]]) -> list[int]:
    return sorted(range(len(candidates_y)), key=lambda i: (transported_l1_distance(query_y, candidates_y[i], transform), i))


def gpads_coordinate_rank() -> int:
    return int(np.linalg.matrix_rank(GPADS_FROM_GAS))


__all__ = ["GPADS_FROM_GAS", "PAPER_EQ4_DISPLAY", "TransformAudit", "audit_transform",
           "gpads_coordinate_rank", "inverse", "inverse_rows", "l1_distance",
           "linear_predictions", "neighbor_order", "source_normalize_vad",
           "transform_rows", "transported_l1_distance", "transported_linear_weights",
           "transported_neighbor_order", "transported_quadratic_metric"]
