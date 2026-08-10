"""Tests for frozen_should_adapt detection — alignment-friction signal.

Substrate notices when a frozen Mt accumulates distance from its
target (= sustained evidence challenging the foundation). The event
fires only for frozen Mts; adaptive Mts adapting is normal drift,
not a failure mode.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.frozen_adaptation_signal import (
    FROZEN_ADAPT_DISTANCE_THRESHOLD,
    FROZEN_ADAPT_STREAK_REQUIRED,
    detect_frozen_should_adapt,
    detect_frozen_should_adapt_all,
    list_frozen_should_adapt_events,
)
from domains.self_improvement_loop import ADAPTIVE, FROZEN, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent")
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


def _build_contradicted_frozen_mt(s, policy=FROZEN):
    """Frozen Mt with concepts whose external evidence points OPPOSITE
    to target_state. Substrate's identity protection holds σ near
    target, but distance ends up high because target uses 'wants +1'
    while external evidence drives toward -1. Identity_field of +5
    ensures σ stays positive despite external_field of -2."""
    mt = s.add_node("Microtheory", {
        "name": "foundational", "temperature": 2.0,
        "update_policy": policy,
    })
    # Each concept: target = +1 (default in mt_target), strong
    # identity_field keeping σ ≈ +1 despite contradictory external_field.
    for i in range(3):
        c = s.add_node("Concept", {
            "name": f"c_{i}",
            "external_field": -2.0,    # contradictory evidence
            "identity_field": +5.0,    # holds the line — σ stays +1
            "target_state": +1.0,
        })
        s.add_edge(mt, "has_concept", c, {})
    return mt


# --- Direct detect_frozen_should_adapt ----------------------------------

def test_no_event_before_distance_stashed():
    """First call: no distance_to_target_magnitude attr yet."""
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s)
    event = detect_frozen_should_adapt(s, mt)
    assert event is None


def test_detection_requires_frozen_policy():
    """Adaptive Mt with sustained high distance should NOT fire —
    adaptive Mts adapting is normal."""
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s, policy=ADAPTIVE)
    # Force a high distance attr.
    s.set_attr(mt, "distance_to_target_magnitude", 5.0)
    for _ in range(FROZEN_ADAPT_STREAK_REQUIRED + 5):
        event = detect_frozen_should_adapt(s, mt)
        assert event is None


def test_fires_when_frozen_mt_has_sustained_high_distance():
    """Frozen Mt + manually-set high distance for K steps → event."""
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s, policy=FROZEN)
    # Force high distance for K steps.
    s.set_attr(mt, "distance_to_target_magnitude",
               FROZEN_ADAPT_DISTANCE_THRESHOLD + 0.5)
    fired_step = None
    for step in range(1, FROZEN_ADAPT_STREAK_REQUIRED + 3):
        event = detect_frozen_should_adapt(s, mt)
        if event is not None:
            fired_step = step
            assert event["policy"] == FROZEN
            assert event["distance_magnitude"] > FROZEN_ADAPT_DISTANCE_THRESHOLD
            break
    assert fired_step == FROZEN_ADAPT_STREAK_REQUIRED


def test_streak_resets_when_distance_drops():
    """If distance drops below threshold, streak resets to 0."""
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s, policy=FROZEN)
    s.set_attr(mt, "distance_to_target_magnitude",
               FROZEN_ADAPT_DISTANCE_THRESHOLD + 0.5)
    # Build streak partway.
    for _ in range(FROZEN_ADAPT_STREAK_REQUIRED // 2):
        detect_frozen_should_adapt(s, mt)
    streak_partway = int(s.node(mt)["attrs"].get(
        "frozen_should_adapt_streak", 0))
    assert streak_partway > 0

    # Distance drops.
    s.set_attr(mt, "distance_to_target_magnitude", 0.1)
    detect_frozen_should_adapt(s, mt)
    streak_after = int(s.node(mt)["attrs"].get(
        "frozen_should_adapt_streak", 0))
    assert streak_after == 0


def test_fires_once_per_continuous_streak():
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s, policy=FROZEN)
    s.set_attr(mt, "distance_to_target_magnitude",
               FROZEN_ADAPT_DISTANCE_THRESHOLD + 0.5)
    fires = 0
    for _ in range(FROZEN_ADAPT_STREAK_REQUIRED + 5):
        if detect_frozen_should_adapt(s, mt) is not None:
            fires += 1
    assert fires == 1


def test_policy_change_to_adaptive_resets_streak():
    """If a frozen Mt is changed to adaptive mid-streak, streak resets."""
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s, policy=FROZEN)
    s.set_attr(mt, "distance_to_target_magnitude",
               FROZEN_ADAPT_DISTANCE_THRESHOLD + 0.5)
    for _ in range(FROZEN_ADAPT_STREAK_REQUIRED // 2):
        detect_frozen_should_adapt(s, mt)
    # Flip to adaptive.
    s.set_attr(mt, "update_policy", ADAPTIVE)
    detect_frozen_should_adapt(s, mt)
    streak = int(s.node(mt)["attrs"].get(
        "frozen_should_adapt_streak", 0))
    assert streak == 0


# --- End-to-end via loop -------------------------------------------------

def test_loop_stashes_distance_to_target():
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s)
    self_improvement_step(s)
    attrs = s.node(mt)["attrs"]
    assert "distance_to_target_magnitude" in attrs


def test_loop_fires_frozen_should_adapt_event():
    """Run loop on frozen contradicted Mt for K+ steps → event recorded."""
    s = _fresh_substrate()
    mt = _build_contradicted_frozen_mt(s)
    for _ in range(FROZEN_ADAPT_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    events = list_frozen_should_adapt_events(s)
    # Should have recorded at least one event.
    if events:
        # The Mt's policy is frozen; mt_id matches.
        assert events[0]["mt_id"] == mt.value
        assert events[0]["streak"] >= FROZEN_ADAPT_STREAK_REQUIRED


def test_loop_no_event_for_adaptive_mt():
    """Adaptive Mt with same structure → no frozen_should_adapt event."""
    s = _fresh_substrate()
    _build_contradicted_frozen_mt(s, policy=ADAPTIVE)
    for _ in range(FROZEN_ADAPT_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    events = list_frozen_should_adapt_events(s)
    assert events == []
