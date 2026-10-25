from __future__ import annotations

import numpy as np
import pytest

from evaluation.ousiometrics.geometry_reference import (
    GPADS_FROM_GAS,
    PAPER_EQ4_DISPLAY,
    audit_transform,
    gpads_coordinate_rank,
    inverse,
    linear_predictions,
    neighbor_order,
    source_normalize_vad,
    transform_rows,
    transported_l1_distance,
    transported_linear_weights,
    transported_neighbor_order,
)


def test_full_information_predictions_equivalent():
    rng = np.random.default_rng(2803)
    x = rng.uniform(-0.5, 0.5, size=(100, 3))
    w = rng.normal(size=3)
    bias = -0.31
    y = transform_rows(x, PAPER_EQ4_DISPLAY)
    w_y = transported_linear_weights(w, PAPER_EQ4_DISPLAY)
    prediction_x = linear_predictions(x, w, bias)
    prediction_y = linear_predictions(y, w_y, bias)
    np.testing.assert_allclose(prediction_x, prediction_y, atol=2e-15, rtol=2e-15)
    audit = audit_transform(PAPER_EQ4_DISPLAY)
    assert audit.rank == 3
    assert audit.condition_number_2 < 1.02
    assert audit.max_abs_inverse_error < 1e-15


def test_transported_metric_same_neighbors():
    query = np.array([0.2, -0.1, 0.4])
    candidates = [
        np.array([0.3, -0.1, 0.4]),
        np.array([0.2, 0.15, 0.4]),
        np.array([-0.1, -0.1, 0.2]),
        np.array([0.21, -0.09, 0.39]),
    ]
    query_y = transform_rows([query], PAPER_EQ4_DISPLAY)[0]
    candidates_y = [transform_rows([candidate], PAPER_EQ4_DISPLAY)[0] for candidate in candidates]
    assert neighbor_order(query, candidates) == transported_neighbor_order(query_y, candidates_y, PAPER_EQ4_DISPLAY)
    for source, target in zip(candidates, candidates_y):
        assert transported_l1_distance(query_y, target, PAPER_EQ4_DISPLAY) == pytest.approx(
            np.sum(np.abs(query - source)), abs=1e-15
        )


def test_fixed_l1_rotation_effect_is_explicit():
    query = np.zeros(3)
    candidates = [np.array([1.0, 0.0, 0.0]), np.array([0.5, 0.7, 0.0])]
    source_order = neighbor_order(query, candidates)
    transformed_query = transform_rows([query], PAPER_EQ4_DISPLAY)[0]
    transformed_candidates = [transform_rows([candidate], PAPER_EQ4_DISPLAY)[0] for candidate in candidates]
    fixed_pds_order = neighbor_order(transformed_query, transformed_candidates)
    assert source_order == [0, 1]
    assert fixed_pds_order == [1, 0]
    assert "rounded" in audit_transform().precision_note


def test_gpads_rank_not_five_independent_axes():
    assert GPADS_FROM_GAS.shape == (5, 3)
    assert gpads_coordinate_rank() == 3
    np.testing.assert_allclose(GPADS_FROM_GAS[1], (GPADS_FROM_GAS[0] + GPADS_FROM_GAS[2]) / np.sqrt(2))


def test_bad_inverse_refused():
    with pytest.raises(ValueError, match="square"):
        inverse([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    with pytest.raises(ValueError, match="singular"):
        inverse([[1.0, 0.0], [0.0, 0.0]])
    with pytest.raises(ValueError, match="finite"):
        inverse([[1.0, float("nan")], [0.0, 1.0]])


def test_source_normalization_is_paper_centering():
    normalized = source_normalize_vad([[0.0, 0.5, 1.0], [1.0, 0.0, 0.5]])
    np.testing.assert_array_equal(normalized, [[-0.5, 0.0, 0.5], [0.5, -0.5, 0.0]])
    with pytest.raises(ValueError, match=r"\[0,1\]"):
        source_normalize_vad([[1.1, 0.2, 0.3]])
