"""Tests for identity-formation signal — sustained drift in identity_field
fires an IdentityFormationEvent.

Same order_n_concepts machinery, applied to per-Concept h_id values
over time. The substrate notices its own commitments forming.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.identity_formation import (
    IDENTITY_FORMATION_DRIFT_THRESHOLD,
    IDENTITY_FORMATION_STREAK_REQUIRED,
    compose_delta_identity_term,
    compute_delta_identity,
    detect_identity_formation,
    list_formations,
    record_identity_formation,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent")
_EDGE_TYPES = ("has_concept", "causal_influence",
               "has_insight", "has_anticipation", "has_formation")


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


# --- Term composition + evaluation ---------------------------------------

def test_compose_delta_identity_returns_minus_term():
    term = compose_delta_identity_term(concept_id=42)
    assert term is not None
    d = term.to_dict()
    assert d["type"] == "Minus"
    assert d["a"]["type"] == "Var"
    assert d["a"]["name"] == "current_h_id"
    assert d["b"]["type"] == "Attr"
    assert d["b"]["key"] == "previous_identity_42"


def test_compute_delta_identity_matches_subtraction():
    s = _fresh_substrate()
    n = s.add_node("Concept", {"identity_field": 0.7})
    mt = s.add_node("Microtheory", {f"previous_identity_{n.value}": 0.5})
    s.add_edge(mt, "has_concept", n, {})
    result = compute_delta_identity(s, mt, n.value, current_h_id=0.7)
    # 0.7 - 0.5 = 0.2
    assert abs(result - 0.2) < 1e-5


def test_compute_delta_identity_returns_zero_without_history():
    s = _fresh_substrate()
    n = s.add_node("Concept", {"identity_field": 0.7})
    mt = s.add_node("Microtheory", {})  # no previous_identity
    s.add_edge(mt, "has_concept", n, {})
    assert compute_delta_identity(s, mt, n.value, 0.7) == 0.0


# --- Streak tracking + formation firing ----------------------------------

def test_streak_increments_on_consistent_drift():
    """Each call with positive Δh_id should grow the streak."""
    s = _fresh_substrate()
    n = s.add_node("Concept", {"name": "n", "identity_field": 0.0})
    mt = s.add_node("Microtheory", {f"previous_identity_{n.value}": 0.0})
    s.add_edge(mt, "has_concept", n, {})

    # Bump h_id repeatedly, calling detect each time + updating previous.
    streak_key = f"formation_streak_{n.value}"
    for step in range(1, 5):
        s.set_attr(n, "identity_field", step * 0.01)  # growing
        detect_identity_formation(s, mt)
        # Update previous_identity for next call.
        s.set_attr(mt, f"previous_identity_{n.value}",
                   s.node(n)["attrs"]["identity_field"])

    # After 4 positive-direction calls, streak should be at least 3
    # (first call needed to set initial direction; subsequent grow).
    streak = int(s.node(mt)["attrs"].get(streak_key, 0))
    assert streak >= 3


def test_streak_resets_on_direction_change():
    s = _fresh_substrate()
    n = s.add_node("Concept", {"name": "n", "identity_field": 0.0})
    mt = s.add_node("Microtheory", {f"previous_identity_{n.value}": 0.0})
    s.add_edge(mt, "has_concept", n, {})
    streak_key = f"formation_streak_{n.value}"

    # 3 positive steps.
    for step in range(1, 4):
        s.set_attr(n, "identity_field", step * 0.01)
        detect_identity_formation(s, mt)
        s.set_attr(mt, f"previous_identity_{n.value}",
                   s.node(n)["attrs"]["identity_field"])
    positive_streak = int(s.node(mt)["attrs"][streak_key])
    assert positive_streak >= 2

    # Now drop h_id sharply (negative direction).
    s.set_attr(n, "identity_field", -0.02)
    detect_identity_formation(s, mt)
    # Streak should reset to 1 (new direction).
    new_streak = int(s.node(mt)["attrs"][streak_key])
    assert new_streak == 1
    direction_key = f"formation_direction_{n.value}"
    assert int(s.node(mt)["attrs"][direction_key]) == -1


def test_formation_event_fires_when_streak_crosses_threshold():
    """Direct call: bump h_id by 0.01 per step for K=10 steps; event
    fires on the 10th step."""
    s = _fresh_substrate()
    n = s.add_node("Concept", {"name": "axiom",
                                "identity_field": 0.0})
    mt = s.add_node("Microtheory", {f"previous_identity_{n.value}": 0.0})
    s.add_edge(mt, "has_concept", n, {})

    events_per_step = []
    for step in range(1, IDENTITY_FORMATION_STREAK_REQUIRED + 2):
        s.set_attr(n, "identity_field", step * 0.01)
        evs = detect_identity_formation(s, mt)
        events_per_step.append(evs)
        # Stash previous for next step.
        s.set_attr(mt, f"previous_identity_{n.value}",
                   s.node(n)["attrs"]["identity_field"])

    # Event should have fired on step K (where streak first crosses K).
    fired_step = None
    for i, evs in enumerate(events_per_step, start=1):
        if evs:
            fired_step = i
            break
    assert fired_step is not None
    assert events_per_step[fired_step - 1][0]["concept_name"] == "axiom"


# --- Loop integration ----------------------------------------------------

def test_loop_fires_formation_after_sustained_sigma():
    """With consistent +σ on a Concept, identity dynamics grows h_id
    every step. After ~K steps, formation fires."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    n = s.add_node("Concept", {"name": "axiom",
                                "external_field": +1.5,
                                "identity_field": 0.0})
    s.add_edge(mt, "has_concept", n, {})

    saw_formation = False
    formation_step = None
    for step in range(1, 30):
        # Use aggressive identity_alpha to make the test fast.
        result = self_improvement_step(s, identity_alpha=0.05,
                                        identity_beta=0.001)
        formations = result[mt.value].get("identity_formations", [])
        if formations:
            saw_formation = True
            formation_step = step
            break

    assert saw_formation, (
        f"expected identity formation event within 30 steps; "
        f"final h_id={s.node(n)['attrs']['identity_field']:.4f}")
    # Should fire after enough sustained drift but well within 30 steps.
    assert formation_step is not None
    assert formation_step <= 25


def test_loop_does_not_fire_formation_with_no_dynamics():
    """If identity_alpha=0, h_id doesn't drift, no formation event."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    n = s.add_node("Concept", {"external_field": +1.5})
    s.add_edge(mt, "has_concept", n, {})

    for _ in range(30):
        result = self_improvement_step(s, identity_alpha=0.0,
                                        identity_beta=0.0)
        assert result[mt.value]["identity_formations"] == []


def test_formation_record_round_trip():
    s = _fresh_substrate()
    n = s.add_node("Concept", {"name": "x"})
    mt = s.add_node("Microtheory", {"name": "m"})
    s.add_edge(mt, "has_concept", n, {})
    event = {
        "concept_id": n.value,
        "concept_name": "x",
        "current_h_id": 0.5,
        "delta_h_id": 0.01,
        "direction": 1,
        "streak": 10,
    }
    recorded = record_identity_formation(s, mt, event)
    assert recorded is not None
    listed = list_formations(s, mt)
    assert len(listed) == 1
    assert listed[0]["concept_name"] == "x"
    assert listed[0]["direction"] == 1
    assert listed[0]["streak"] == 10
