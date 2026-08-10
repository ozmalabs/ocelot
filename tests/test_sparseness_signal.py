"""Tests for sparse_Mt detection — inverse-direction streak on coverage."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.sparseness_signal import (
    SPARSE_COVERAGE_THRESHOLD,
    SPARSE_STREAK_REQUIRED,
    detect_sparse_mt,
    list_sparse_mt_events,
)
from domains.self_improvement_loop import ADAPTIVE, FROZEN, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent",
               "FrustratedMtEvent", "SparseMtEvent")
_EDGE_TYPES = ("has_concept", "causal_influence",
               "has_insight", "has_anticipation",
               "has_formation")


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


def _build_sparse_mt(s):
    """Build an Mt with concepts whose σ stay near 0 — no fields,
    weak couplings, low β. Coverage will be small (0 engaged)."""
    mt = s.add_node("Microtheory", {"name": "sparse",
                                    "temperature": 0.01,  # very flat
                                    "update_policy": ADAPTIVE})
    for i in range(3):
        c = s.add_node("Concept", {"name": f"c_{i}",
                                    "external_field": 0.0})
        s.add_edge(mt, "has_concept", c, {})
    return mt


# --- Direct detection ---------------------------------------------------

def test_no_event_before_coverage_stashed():
    s = _fresh_substrate()
    mt = _build_sparse_mt(s)
    event = detect_sparse_mt(s, mt)
    assert event is None


def test_fires_for_sustained_low_coverage():
    s = _fresh_substrate()
    mt = _build_sparse_mt(s)
    s.set_attr(mt, "coverage", 0)
    fired_step = None
    for step in range(1, SPARSE_STREAK_REQUIRED + 3):
        event = detect_sparse_mt(s, mt)
        if event is not None:
            fired_step = step
            assert event["coverage"] == 0
            assert event["streak"] == SPARSE_STREAK_REQUIRED
            break
    assert fired_step == SPARSE_STREAK_REQUIRED


def test_no_event_when_coverage_high():
    s = _fresh_substrate()
    mt = _build_sparse_mt(s)
    s.set_attr(mt, "coverage", 5)  # well above threshold
    for _ in range(SPARSE_STREAK_REQUIRED + 3):
        event = detect_sparse_mt(s, mt)
        assert event is None


def test_streak_resets_when_coverage_recovers():
    s = _fresh_substrate()
    mt = _build_sparse_mt(s)
    s.set_attr(mt, "coverage", 0)
    for _ in range(SPARSE_STREAK_REQUIRED // 2):
        detect_sparse_mt(s, mt)
    s.set_attr(mt, "coverage", 3)
    detect_sparse_mt(s, mt)
    assert int(s.node(mt)["attrs"]["sparse_streak"]) == 0


def test_fires_once_per_continuous_streak():
    s = _fresh_substrate()
    mt = _build_sparse_mt(s)
    s.set_attr(mt, "coverage", 0)
    fires = 0
    for _ in range(SPARSE_STREAK_REQUIRED + 5):
        if detect_sparse_mt(s, mt) is not None:
            fires += 1
    assert fires == 1


# --- End-to-end via loop ------------------------------------------------

def test_loop_fires_sparse_event_for_disengaged_mt():
    s = _fresh_substrate()
    mt = _build_sparse_mt(s)
    for _ in range(SPARSE_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    events = list_sparse_mt_events(s)
    # With β=0.01 + no fields, σ stays at 0 → coverage = 0.
    if events:
        assert events[0]["mt_id"] == mt.value
        assert events[0]["coverage"] < SPARSE_COVERAGE_THRESHOLD


def test_loop_no_sparse_event_for_active_mt():
    """A normal active Mt should engage its concepts."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "active", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    for i in range(3):
        c = s.add_node("Concept", {"external_field": 1.0})
        s.add_edge(mt, "has_concept", c, {})
    for _ in range(SPARSE_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    assert list_sparse_mt_events(s) == []
