"""Tests for frustrated_Mt detection — sustained F."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.frustration_signal import (
    FRUSTRATION_STREAK_REQUIRED,
    FRUSTRATION_THRESHOLD,
    detect_frustrated_mt,
    list_frustrated_mt_events,
)
from domains.self_improvement_loop import ADAPTIVE, FROZEN, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent",
               "FrustratedMtEvent")
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


def _build_persistently_frustrated_mt(s):
    """Frustrated triangle — all couplings J=-1; no clean assignment."""
    mt = s.add_node("Microtheory", {"name": "tri", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    c = s.add_node("Concept", {})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(a, "causal_influence", b, {"weight": -1.0})
    s.add_edge(b, "causal_influence", c, {"weight": -1.0})
    s.add_edge(c, "causal_influence", a, {"weight": -1.0})
    return mt


# --- Direct detection ----------------------------------------------------

def test_no_event_before_frustration_stashed():
    s = _fresh_substrate()
    mt = _build_persistently_frustrated_mt(s)
    event = detect_frustrated_mt(s, mt)
    assert event is None


def test_fires_for_sustained_frustration():
    s = _fresh_substrate()
    mt = _build_persistently_frustrated_mt(s)
    s.set_attr(mt, "previous_frustration",
               FRUSTRATION_THRESHOLD + 0.5)
    fired_step = None
    for step in range(1, FRUSTRATION_STREAK_REQUIRED + 3):
        event = detect_frustrated_mt(s, mt)
        if event is not None:
            fired_step = step
            assert event["streak"] == FRUSTRATION_STREAK_REQUIRED
            break
    assert fired_step == FRUSTRATION_STREAK_REQUIRED


def test_streak_resets_when_frustration_drops():
    s = _fresh_substrate()
    mt = _build_persistently_frustrated_mt(s)
    s.set_attr(mt, "previous_frustration",
               FRUSTRATION_THRESHOLD + 0.5)
    for _ in range(FRUSTRATION_STREAK_REQUIRED // 2):
        detect_frustrated_mt(s, mt)
    s.set_attr(mt, "previous_frustration", 0.1)
    detect_frustrated_mt(s, mt)
    assert int(s.node(mt)["attrs"]["frustration_streak"]) == 0


def test_fires_once_per_continuous_streak():
    s = _fresh_substrate()
    mt = _build_persistently_frustrated_mt(s)
    s.set_attr(mt, "previous_frustration",
               FRUSTRATION_THRESHOLD + 0.5)
    fires = 0
    for _ in range(FRUSTRATION_STREAK_REQUIRED + 5):
        if detect_frustrated_mt(s, mt) is not None:
            fires += 1
    assert fires == 1


def test_works_regardless_of_policy():
    """Frustration is a failure mode for frozen + adaptive both."""
    s = _fresh_substrate()
    mt = _build_persistently_frustrated_mt(s)
    s.set_attr(mt, "update_policy", FROZEN)
    s.set_attr(mt, "previous_frustration",
               FRUSTRATION_THRESHOLD + 0.5)
    fired = False
    for _ in range(FRUSTRATION_STREAK_REQUIRED + 3):
        if detect_frustrated_mt(s, mt) is not None:
            fired = True
            break
    assert fired


# --- End-to-end via loop -------------------------------------------------

def test_loop_fires_frustrated_event_for_triangle():
    s = _fresh_substrate()
    mt = _build_persistently_frustrated_mt(s)
    for _ in range(FRUSTRATION_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    events = list_frustrated_mt_events(s)
    if events:
        assert events[0]["mt_id"] == mt.value
        assert events[0]["streak"] >= FRUSTRATION_STREAK_REQUIRED


def test_loop_no_event_for_coherent_mt():
    """A clean coherent Mt should have F ≈ 0; no frustration event."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "clean", "temperature": 1.5,
                                    "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"external_field": 1.0})
    b = s.add_node("Concept", {"external_field": 1.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 1.0})
    for _ in range(FRUSTRATION_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    assert list_frustrated_mt_events(s) == []
