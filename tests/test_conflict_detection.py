"""Tests for conflict detection — second filter designed by the agent
(2nd pass of scripts/agent_designs_filter.py).

Targets fail_mode_conflicting_reflexes: two Mts driving the same node
in opposite directions with substantial magnitude.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.conflict_detection import (
    CONFLICT_MAGNITUDE_THRESHOLD,
    CONFLICT_STREAK_REQUIRED,
    detect_conflicts_all_pairs,
    detect_conflicts_for_pair,
    list_conflict_events,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent")
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


# --- mt_conflicting_nodes Rust op ----------------------------------------

def test_no_conflicts_when_marginals_agree():
    s = _fresh_substrate()
    a = s.add_node("Concept", {"external_field": +1.0})
    b = s.add_node("Concept", {"external_field": +1.0})
    mt_a = s.add_node("Microtheory", {"temperature": 2.0})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0})
    for n in (a, b):
        s.add_edge(mt_a, "has_concept", n, {})
        s.add_edge(mt_b, "has_concept", n, {})
    conflicts = s.mt_conflicting_nodes(mt_a, mt_b, 0.5)
    assert conflicts == []


def test_conflict_when_each_mt_drives_node_opposite_via_couplings():
    """Build two Mts that share a node but each Mt's couplings push
    that node toward opposite signs. mt_a couples shared_node → strongly
    activated other_a; mt_b couples shared_node → strongly inhibited
    other_b — neither is exactly the spec but it's the closest we can
    get given couplings being Mt-shared via edges."""
    s = _fresh_substrate()
    shared = s.add_node("Concept", {})
    helper_a = s.add_node("Concept", {"external_field": +2.0})  # strongly +
    helper_b = s.add_node("Concept", {"external_field": -2.0})  # strongly -
    mt_a = s.add_node("Microtheory", {"name": "A", "temperature": 2.0})
    mt_b = s.add_node("Microtheory", {"name": "B", "temperature": 2.0})
    s.add_edge(mt_a, "has_concept", shared, {})
    s.add_edge(mt_a, "has_concept", helper_a, {})
    s.add_edge(mt_b, "has_concept", shared, {})
    s.add_edge(mt_b, "has_concept", helper_b, {})
    # mt_a's coupling: helper_a (+) wants shared (+).
    s.add_edge(helper_a, "causal_influence", shared, {"weight": +1.5})
    # mt_b's coupling: helper_b (−) wants shared (+ also via negative J?).
    # If J(helper_b, shared) = +1.5 and helper_b is -1, then -J σσ
    # contribution to shared's local field is +1.5*(-1) = -1.5 → shared
    # pushed negative. Good.
    s.add_edge(helper_b, "causal_influence", shared, {"weight": +1.5})

    conflicts = s.mt_conflicting_nodes(mt_a, mt_b, 0.5)
    assert len(conflicts) == 1
    assert int(conflicts[0]["node_id"]) == shared.value
    # mt_a's marginal on shared is positive; mt_b's is negative.
    assert conflicts[0]["sigma_a"] > 0
    assert conflicts[0]["sigma_b"] < 0


def test_no_conflicts_below_magnitude_threshold():
    """If σ_a or σ_b is weak (below magnitude_threshold), it's not a
    'high-β commitment' so no conflict."""
    s = _fresh_substrate()
    shared = s.add_node("Concept", {})
    mt_a = s.add_node("Microtheory", {"temperature": 0.1})  # near-zero β
    mt_b = s.add_node("Microtheory", {"temperature": 0.1})
    s.add_edge(mt_a, "has_concept", shared, {})
    s.add_edge(mt_b, "has_concept", shared, {})
    s.set_attr(shared, "external_field", 0.01)
    conflicts = s.mt_conflicting_nodes(mt_a, mt_b, 0.5)
    # Even if marginals differ slightly, they won't exceed magnitude
    # threshold.
    assert conflicts == []


# --- Detection orchestration ---------------------------------------------

def _build_conflicting_mts(s):
    """Two Mts that strongly drive a shared node in opposite directions
    via Mt-specific helper concepts + couplings."""
    shared = s.add_node("Concept", {"name": "shared"})
    helper_a = s.add_node("Concept", {"name": "helper_a",
                                       "external_field": +2.0})
    helper_b = s.add_node("Concept", {"name": "helper_b",
                                       "external_field": -2.0})
    mt_a = s.add_node("Microtheory", {"name": "A", "temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    mt_b = s.add_node("Microtheory", {"name": "B", "temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    s.add_edge(mt_a, "has_concept", shared, {})
    s.add_edge(mt_a, "has_concept", helper_a, {})
    s.add_edge(mt_b, "has_concept", shared, {})
    s.add_edge(mt_b, "has_concept", helper_b, {})
    s.add_edge(helper_a, "causal_influence", shared, {"weight": +1.5})
    s.add_edge(helper_b, "causal_influence", shared, {"weight": +1.5})
    return mt_a, mt_b, shared


def test_conflict_streak_increments_per_node():
    s = _fresh_substrate()
    mt_a, mt_b, shared = _build_conflicting_mts(s)
    for step in range(1, CONFLICT_STREAK_REQUIRED + 2):
        detect_conflicts_for_pair(s, mt_a, mt_b)
    # Streak attr should have been incremented.
    # Canonical order: lower-id holds streak.
    mt_lower = mt_a if mt_a.value < mt_b.value else mt_b
    mt_higher = mt_b if mt_a.value < mt_b.value else mt_a
    key = f"conflict_streak_for_{mt_higher.value}_node_{shared.value}"
    streak = int(s.node(mt_lower)["attrs"].get(key, 0))
    # Should be at least CONFLICT_STREAK_REQUIRED.
    assert streak >= CONFLICT_STREAK_REQUIRED


def test_conflict_fires_event_on_streak_crossing():
    s = _fresh_substrate()
    mt_a, mt_b, shared = _build_conflicting_mts(s)

    fired_step = None
    for step in range(1, CONFLICT_STREAK_REQUIRED + 3):
        events = detect_conflicts_for_pair(s, mt_a, mt_b)
        if events:
            fired_step = step
            # Should target the specific shared node.
            assert events[0]["node_id"] == shared.value
            assert events[0]["node_name"] == "shared"
            break
    assert fired_step == CONFLICT_STREAK_REQUIRED


def test_no_conflict_for_agreeing_mts():
    s = _fresh_substrate()
    shared = s.add_node("Concept", {"external_field": +1.0})
    mt_a = s.add_node("Microtheory", {"temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    s.add_edge(mt_a, "has_concept", shared, {})
    s.add_edge(mt_b, "has_concept", shared, {})
    for _ in range(CONFLICT_STREAK_REQUIRED + 3):
        events = detect_conflicts_for_pair(s, mt_a, mt_b)
        assert events == []


def test_conflict_fires_once_per_continuous_streak():
    s = _fresh_substrate()
    mt_a, mt_b, shared = _build_conflicting_mts(s)
    fires = 0
    for _ in range(CONFLICT_STREAK_REQUIRED + 4):
        events = detect_conflicts_for_pair(s, mt_a, mt_b)
        fires += len(events)
    assert fires == 1


# --- End-to-end via loop -------------------------------------------------

def test_loop_records_conflict_event():
    s = _fresh_substrate()
    mt_a, mt_b, shared = _build_conflicting_mts(s)
    for _ in range(CONFLICT_STREAK_REQUIRED + 2):
        self_improvement_step(s)
    events = list_conflict_events(s)
    assert len(events) >= 1
    assert events[0]["conflicted_node_id"] == shared.value
    assert events[0]["conflicted_node_name"] == "shared"
