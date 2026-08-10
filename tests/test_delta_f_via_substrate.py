"""Tests for ΔF computed via Term-tree + substrate's native evaluator.

ΔF used to be a Python subtraction (current - previous). It's now a
Term-tree composed via the order_n_concepts machinery (Minus over a
2-sample window) and evaluated by the substrate. Mechanically
identical; the substrate computes its own derivative.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.insight_detection import (
    compose_delta_f_term,
    compute_delta_f_via_substrate,
    detect_insight,
)
from domains.insight_naming import list_insights
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent", "AnticipationEvent")
_EDGE_TYPES = ("has_concept", "causal_influence",
               "has_insight", "has_anticipation")


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


# --- Term composition ----------------------------------------------------

def test_compose_delta_f_returns_minus_term():
    term = compose_delta_f_term()
    assert term is not None
    d = term.to_dict()
    assert d["type"] == "Minus"
    # a = Var("current_F"), b = Attr(Var("mt"), "previous_frustration")
    assert d["a"]["type"] == "Var"
    assert d["a"]["name"] == "current_F"
    assert d["b"]["type"] == "Attr"
    assert d["b"]["key"] == "previous_frustration"


# --- Native evaluation matches Python arithmetic -------------------------

def test_substrate_eval_matches_python_subtraction_drop():
    """Substrate's Term-tree ΔF should equal current - previous."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"previous_frustration": 3.5})
    result = compute_delta_f_via_substrate(s, mt, current_f=1.2)
    assert abs(result - (-2.3)) < 1e-5


def test_substrate_eval_matches_python_subtraction_growth():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"previous_frustration": 0.5})
    result = compute_delta_f_via_substrate(s, mt, current_f=2.7)
    assert abs(result - (+2.2)) < 1e-5


def test_substrate_eval_zero_when_unchanged():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"previous_frustration": 1.0})
    result = compute_delta_f_via_substrate(s, mt, current_f=1.0)
    assert abs(result) < 1e-5


# --- detect_insight uses precomputed delta_f -----------------------------

def test_detect_insight_uses_precomputed_delta_f_when_supplied():
    """Pass delta_f explicitly (as the loop now does)."""
    event = detect_insight(
        previous_frustration=4.0,
        previous_state={1: +0.9},
        current_audit={
            "frustration": 1.0,
            "marginal": {1: -0.9},
            "energy": -1.0,
            "coverage": 1,
        },
        mt_id=42,
        delta_f=-3.0,  # explicit
    )
    assert event is not None
    assert event["delta_F"] == pytest.approx(-3.0)


def test_detect_insight_falls_back_to_python_when_delta_f_none():
    """No substrate? Python subtraction still works (unit-test path)."""
    event = detect_insight(
        previous_frustration=4.0,
        previous_state={1: +0.9},
        current_audit={
            "frustration": 1.0,
            "marginal": {1: -0.9},
            "energy": -1.0,
            "coverage": 1,
        },
        mt_id=42,
        delta_f=None,
    )
    assert event is not None
    assert event["delta_F"] == pytest.approx(-3.0)


# --- End-to-end: loop computes ΔF via substrate --------------------------

def test_loop_detects_morning_insight_using_substrate_delta_f():
    """The morning scenario should still fire insight detection now
    that ΔF is computed via the substrate's evaluator."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "morning", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    axiom = s.add_node("Concept", {"external_field": +1.5})
    frame_rel = s.add_node("Concept", {"external_field": +0.8})
    frame_priv = s.add_node("Concept", {"external_field": -0.5})
    g_bin = s.add_node("Concept", {"external_field": +1.2})
    g_vec = s.add_node("Concept", {"external_field": -2.0})
    for n in (axiom, frame_rel, frame_priv, g_bin, g_vec):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(axiom, "causal_influence", frame_rel, {"weight": +1.0})
    s.add_edge(axiom, "causal_influence", frame_priv, {"weight": -1.0})
    s.add_edge(frame_priv, "causal_influence", g_bin, {"weight": +0.8})
    s.add_edge(frame_priv, "causal_influence", g_vec, {"weight": -0.8})
    s.add_edge(frame_rel, "causal_influence", g_vec, {"weight": +0.7})
    s.add_edge(g_bin, "causal_influence", g_vec, {"weight": -0.6})

    self_improvement_step(s)
    s.set_attr(g_vec, "external_field", 0.3)
    result = self_improvement_step(s)
    insight = result[mt.value]["insight"]
    assert insight is not None
    assert insight["delta_F"] < -1.0
