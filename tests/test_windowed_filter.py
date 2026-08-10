"""Tests for the shared WindowedFilter primitive.

The same primitive backs insight ΔF detection, anticipation (∂²F),
and identity-formation Δh_id. These tests exercise the primitive
directly to lock its semantics + show how it generalises to custom
kernels (cross-correlation, etc.).
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.windowed_filter import (
    all_attrs_present,
    attr_sample,
    compose_and_evaluate,
    evaluate_filter,
    order_n_kernel,
    var_sample,
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in ("Microtheory", "Concept"):
        for tgt_t in ("Microtheory", "Concept"):
            for et in ("has_concept",):
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


# --- Sample helpers -------------------------------------------------------

def test_attr_sample_builds_attr_term():
    s = attr_sample("mt", "previous_F")
    d = s.to_dict()
    assert d["type"] == "Attr"
    assert d["key"] == "previous_F"
    assert d["node"]["type"] == "Var"
    assert d["node"]["name"] == "mt"


def test_var_sample_builds_var_term():
    s = var_sample("current_F")
    d = s.to_dict()
    assert d["type"] == "Var"
    assert d["name"] == "current_F"


# --- Kernel composition --------------------------------------------------

def test_order_1_kernel_is_minus():
    samples = [attr_sample("mt", "a"), var_sample("b")]
    k = order_n_kernel(samples, 1)
    assert k is not None
    assert k.to_dict()["type"] == "Minus"


def test_order_2_kernel_is_nested_minus():
    samples = [
        attr_sample("mt", "a"),
        attr_sample("mt", "b"),
        var_sample("c"),
    ]
    k = order_n_kernel(samples, 2)
    assert k is not None
    d = k.to_dict()
    assert d["type"] == "Minus"
    # Each side is itself a Minus (second-difference structure).
    assert d["a"]["type"] == "Minus"
    assert d["b"]["type"] == "Minus"


def test_kernel_returns_none_when_window_too_small():
    samples = [var_sample("a")]
    # Can't take order-1 of a single sample.
    assert order_n_kernel(samples, 1) is None


# --- Evaluation ----------------------------------------------------------

def test_evaluate_filter_runs_substrate_eval():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"a": 0.5})
    term = order_n_kernel([attr_sample("mt", "a"), var_sample("b")], 1)
    result = evaluate_filter(s, term, {"mt": mt, "b": 0.9})
    # 0.9 - 0.5 = 0.4
    assert abs(result - 0.4) < 1e-5


def test_all_attrs_present_checks_window():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"a": 1.0, "b": 2.0})
    assert all_attrs_present(s, mt, ["a", "b"])
    assert not all_attrs_present(s, mt, ["a", "c"])
    assert not all_attrs_present(s, mt, ["c"])
    assert all_attrs_present(s, mt, [])  # empty list trivially present


# --- compose_and_evaluate one-shot ---------------------------------------

def test_compose_and_evaluate_full_pipeline():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"prev": 3.0, "prev_prev": 4.0})
    samples = [
        attr_sample("mt", "prev_prev"),
        attr_sample("mt", "prev"),
        var_sample("cur"),
    ]
    # Order-2: cur - 2*prev + prev_prev
    result = compose_and_evaluate(
        s, mt, samples, order=2, env={"mt": mt, "cur": 1.0},
        required_attrs=["prev", "prev_prev"],
    )
    # 1.0 - 2*3.0 + 4.0 = -1.0
    assert abs(result - (-1.0)) < 1e-5


def test_compose_and_evaluate_returns_none_when_window_not_ready():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"prev": 3.0})  # missing prev_prev
    samples = [
        attr_sample("mt", "prev_prev"),
        attr_sample("mt", "prev"),
        var_sample("cur"),
    ]
    result = compose_and_evaluate(
        s, mt, samples, order=2, env={"mt": mt, "cur": 1.0},
        required_attrs=["prev", "prev_prev"],
    )
    assert result is None


# --- Demonstrate generality: custom filter beyond ΔF / ∂²F ---------------

def test_custom_filter_three_step_avg_via_order_1_telescoping():
    """Show the primitive isn't tied to specific kernel families. Build
    a custom filter — here, the simplest case: just F[t] - F[t-1]
    (order-1) BUT using arbitrary attr names so it could be any
    quantity at any sampling rate."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {
        "my_metric_t_minus_1": 5.0,
    })
    samples = [
        attr_sample("mt", "my_metric_t_minus_1"),
        var_sample("my_metric_now"),
    ]
    result = compose_and_evaluate(
        s, mt, samples, order=1,
        env={"mt": mt, "my_metric_now": 8.0},
        required_attrs=["my_metric_t_minus_1"],
    )
    assert abs(result - 3.0) < 1e-5
