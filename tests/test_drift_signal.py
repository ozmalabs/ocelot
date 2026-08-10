"""Tests for drifted-past-anchor detection — symmetric counterpart
to frozen_should_adapt. Adaptive Mt + sustained high distance fires.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.drift_signal import (
    DRIFT_DISTANCE_THRESHOLD,
    DRIFT_STREAK_REQUIRED,
    detect_drifted_past_anchor,
    list_drift_events,
)
from domains.self_improvement_loop import ADAPTIVE, FROZEN, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent")
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


def _build_drifted_adaptive_mt(s, policy=ADAPTIVE):
    """Adaptive Mt with concepts whose external evidence drives them
    AWAY from target_state. No identity_field — they're free to drift.
    """
    mt = s.add_node("Microtheory", {
        "name": "drifted", "temperature": 2.0,
        "update_policy": policy,
    })
    for i in range(3):
        c = s.add_node("Concept", {
            "name": f"c_{i}",
            "external_field": -2.0,    # contradicts target
            "target_state": +1.0,      # but Mt declares wants +1
        })
        s.add_edge(mt, "has_concept", c, {})
    return mt


# --- Direct detection ---------------------------------------------------

def test_no_event_before_distance_stashed():
    s = _fresh_substrate()
    mt = _build_drifted_adaptive_mt(s)
    event = detect_drifted_past_anchor(s, mt)
    assert event is None


def test_detection_excludes_frozen_policy():
    """Frozen Mts handled by frozen_should_adapt — this one excludes."""
    s = _fresh_substrate()
    mt = _build_drifted_adaptive_mt(s, policy=FROZEN)
    s.set_attr(mt, "distance_to_target_magnitude", 5.0)
    for _ in range(DRIFT_STREAK_REQUIRED + 5):
        event = detect_drifted_past_anchor(s, mt)
        assert event is None


def test_fires_for_adaptive_mt_with_sustained_distance():
    s = _fresh_substrate()
    mt = _build_drifted_adaptive_mt(s, policy=ADAPTIVE)
    s.set_attr(mt, "distance_to_target_magnitude",
               DRIFT_DISTANCE_THRESHOLD + 0.5)
    fired_step = None
    for step in range(1, DRIFT_STREAK_REQUIRED + 3):
        event = detect_drifted_past_anchor(s, mt)
        if event is not None:
            fired_step = step
            assert event["policy"] == ADAPTIVE
            assert event["distance_magnitude"] > DRIFT_DISTANCE_THRESHOLD
            break
    assert fired_step == DRIFT_STREAK_REQUIRED


def test_streak_resets_when_distance_drops():
    s = _fresh_substrate()
    mt = _build_drifted_adaptive_mt(s, policy=ADAPTIVE)
    s.set_attr(mt, "distance_to_target_magnitude",
               DRIFT_DISTANCE_THRESHOLD + 0.5)
    for _ in range(DRIFT_STREAK_REQUIRED // 2):
        detect_drifted_past_anchor(s, mt)
    streak_partway = int(s.node(mt)["attrs"].get("drift_streak", 0))
    assert streak_partway > 0
    s.set_attr(mt, "distance_to_target_magnitude", 0.1)
    detect_drifted_past_anchor(s, mt)
    streak_after = int(s.node(mt)["attrs"].get("drift_streak", 0))
    assert streak_after == 0


def test_fires_once_per_continuous_streak():
    s = _fresh_substrate()
    mt = _build_drifted_adaptive_mt(s, policy=ADAPTIVE)
    s.set_attr(mt, "distance_to_target_magnitude",
               DRIFT_DISTANCE_THRESHOLD + 0.5)
    fires = 0
    for _ in range(DRIFT_STREAK_REQUIRED + 5):
        if detect_drifted_past_anchor(s, mt) is not None:
            fires += 1
    assert fires == 1


# --- End-to-end via loop ------------------------------------------------

def test_loop_fires_drift_event_for_adaptive_mt():
    s = _fresh_substrate()
    mt = _build_drifted_adaptive_mt(s, policy=ADAPTIVE)
    for _ in range(DRIFT_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    events = list_drift_events(s)
    if events:
        assert events[0]["mt_id"] == mt.value
        assert events[0]["streak"] >= DRIFT_STREAK_REQUIRED


def test_loop_no_drift_event_for_frozen_mt():
    """Frozen Mt handled by frozen_should_adapt, not drift."""
    s = _fresh_substrate()
    _build_drifted_adaptive_mt(s, policy=FROZEN)
    for _ in range(DRIFT_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    assert list_drift_events(s) == []


def test_frozen_and_drift_complementary():
    """Build both: one frozen, one adaptive, both contradicted. Each
    should fire its respective event; not the other's."""
    s = _fresh_substrate()
    frozen_mt = _build_drifted_adaptive_mt(s, policy=FROZEN)
    # _build_drifted_adaptive_mt adds concepts to a fresh Mt. Need
    # to make sure the second call doesn't share concept names with
    # the first (it doesn't — each call mints new Concepts).
    adaptive_mt = _build_drifted_adaptive_mt(s, policy=ADAPTIVE)

    for _ in range(DRIFT_STREAK_REQUIRED + 3):
        self_improvement_step(s)

    from domains.frozen_adaptation_signal import (
        list_frozen_should_adapt_events,
    )
    frozen_events = list_frozen_should_adapt_events(s)
    drift_events = list_drift_events(s)

    # Drift events should only be from adaptive_mt.
    for event in drift_events:
        assert event["mt_id"] == adaptive_mt.value
    # Frozen events should only be from frozen_mt.
    for event in frozen_events:
        assert event["mt_id"] == frozen_mt.value
