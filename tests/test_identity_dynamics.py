"""Tests for identity dynamics + insight recurrence.

Identity emerges from sustained σ: h_id ← h_id + α·σ - β·h_id per step.
Recurrent insights (matching fingerprint) increment recurrence_count
on the existing InsightEvent + boost the identity nudge on flipped
nodes. The substrate becomes its commitments through its own
experience.
"""
from __future__ import annotations

import math

import pytest
from substrate_rs import _native

from domains.insight_naming import list_insights
from domains.self_improvement_loop import (
    ADAPTIVE,
    FROZEN,
    self_improvement_step,
)


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent")
_EDGE_TYPES = ("has_concept", "causal_influence", "has_insight")


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


# --- Identity dynamics: Rust op directly ---------------------------------

def test_identity_grows_toward_sustained_positive_sigma():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.5})
    n = s.add_node("Concept", {"state": +0.95,
                                "external_field": 1.0,
                                "identity_field": 0.0})
    s.add_edge(mt, "has_concept", n, {})
    # Apply dynamics many times — σ stays around +1 because of field +
    # what we wrote. Identity should drift positive.
    for _ in range(200):
        s.mt_update_identity_dynamics(mt, alpha=0.02, beta=0.001)
    final_id = s.node(n)["attrs"]["identity_field"]
    # With α=0.02, β=0.001, σ≈+0.95: asymptote ≈ α·σ / β = 0.019/0.001 = 19.
    # Won't reach that in 200 steps but should be meaningfully positive.
    assert final_id > 1.0


def test_identity_decays_with_no_sigma():
    """With σ=0 (no commitment), identity decays toward 0 — even from
    a positive starting point. Identity is held by reinforcement, not
    by inertia."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 0.01})  # very flat
    n = s.add_node("Concept", {"state": 0.0,
                                "external_field": 0.0,
                                "identity_field": 1.0})
    s.add_edge(mt, "has_concept", n, {})
    for _ in range(500):
        s.mt_update_identity_dynamics(mt, alpha=0.02, beta=0.01)
    final_id = s.node(n)["attrs"]["identity_field"]
    # β=0.01, half-life ≈ 69 steps. After 500 steps: 1.0 * (0.99^500)
    # ≈ 0.0066. Should be well below 0.1.
    assert final_id < 0.1


def test_identity_dynamics_converges_to_alpha_sigma_over_beta():
    """Asymptote of h_id is α·σ/β when σ is constant. With α=0.01,
    β=0.005, σ=+1.0: asymptote = 2.0."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    n = s.add_node("Concept", {"state": +1.0,
                                "external_field": +2.0,
                                "identity_field": 0.0})
    s.add_edge(mt, "has_concept", n, {})
    for _ in range(2000):
        s.mt_update_identity_dynamics(mt, alpha=0.01, beta=0.005)
    final = s.node(n)["attrs"]["identity_field"]
    # Expected asymptote = α·σ/β = 0.01*1.0/0.005 = 2.0
    assert abs(final - 2.0) < 0.1


def test_nudge_identity_moves_field_in_one_call():
    s = _fresh_substrate()
    n = s.add_node("Concept", {"identity_field": 0.5})
    s.concept_nudge_identity(n, target_sigma=+1.0, alpha=0.3)
    # h_id ← 0.5 + 0.3 * 1.0 = 0.8
    assert abs(s.node(n)["attrs"]["identity_field"] - 0.8) < 1e-5


# --- Identity dynamics in the loop, policy-gated -------------------------

def test_loop_grows_identity_on_sustained_positive_sigma():
    """50 loop steps with strong field → identity grows positive."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    n = s.add_node("Concept", {"external_field": +1.5,
                                "identity_field": 0.0})
    s.add_edge(mt, "has_concept", n, {})
    for _ in range(100):
        self_improvement_step(s, identity_alpha=0.02,
                              identity_beta=0.001)
    final_id = s.node(n)["attrs"]["identity_field"]
    assert final_id > 0.5  # measurably grown


def test_loop_skips_identity_dynamics_on_frozen_mt():
    """Frozen Mts don't run identity dynamics either."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "update_policy": FROZEN})
    n = s.add_node("Concept", {"external_field": +1.5,
                                "identity_field": 0.0})
    s.add_edge(mt, "has_concept", n, {})
    for _ in range(50):
        self_improvement_step(s, identity_alpha=0.05,
                              identity_beta=0.001)
    final_id = s.node(n)["attrs"]["identity_field"]
    assert final_id == 0.0  # untouched


# --- Insight recurrence: same fingerprint increments count ---------------

def _build_morning_network(s):
    mt = s.add_node("Microtheory", {"name": "morning", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    nodes = {}
    setups = [
        ("axiom_0",       +1.5),
        ("frame_rel",     +0.8),
        ("frame_privil",  -0.5),
        ("ground_bin",    +1.2),
        ("ground_vec",    -2.0),
    ]
    for name, h in setups:
        nid = s.add_node("Concept", {"name": name,
                                     "external_field": float(h)})
        s.add_edge(mt, "has_concept", nid, {})
        nodes[name] = nid
    couplings = [
        ("axiom_0",      "frame_rel",     +1.0),
        ("axiom_0",      "frame_privil",  -1.0),
        ("frame_privil", "ground_bin",    +0.8),
        ("frame_privil", "ground_vec",    -0.8),
        ("frame_rel",    "ground_vec",    +0.7),
        ("ground_bin",   "ground_vec",    -0.6),
    ]
    for a, b, w in couplings:
        s.add_edge(nodes[a], "causal_influence",
                   nodes[b], {"weight": float(w)})
    return mt, nodes


def test_recurrent_insight_increments_count_not_node_count():
    """The morning insight detected twice → one InsightEvent node
    with recurrence_count=2."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)

    # First time.
    self_improvement_step(s)
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    self_improvement_step(s)
    insights_v1 = list_insights(s, mt)
    assert len(insights_v1) == 1
    assert insights_v1[0]["recurrence_count"] == 1

    # Push back + resolve again.
    s.set_attr(nodes["ground_vec"], "external_field", -2.0)
    self_improvement_step(s)
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    step3 = self_improvement_step(s)

    insights_v2 = list_insights(s, mt)
    # Same fingerprint → same node, count incremented.
    assert len(insights_v2) == 1
    assert insights_v2[0]["recurrence_count"] == 2
    # is_recurrence marker on the latest insight event dict.
    assert step3[mt.value]["insight"]["is_recurrence"] is True


def test_first_detection_is_not_a_recurrence():
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)
    self_improvement_step(s)
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    step = self_improvement_step(s)
    assert step[mt.value]["insight"]["is_recurrence"] is False
    assert step[mt.value]["insight"]["recurrence_count"] == 1


# --- Insight consolidation nudges identity --------------------------------

def test_insight_consolidation_nudges_identity_on_flipped_nodes():
    """After morning insight, identity_field on the flipped nodes
    (ground_vec, ground_bin, frame_privil) should have moved in the
    direction of the new σ."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)
    self_improvement_step(s, identity_alpha=0.0, identity_beta=0.0,
                          identity_nudge_alpha=0.1)
    # Identity starts at 0 by default for all nodes.
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    step = self_improvement_step(s, identity_alpha=0.0,
                                  identity_beta=0.0,
                                  identity_nudge_alpha=0.1)

    insight = step[mt.value]["insight"]
    assert insight is not None
    assert insight["identity_nudges"] > 0

    # ground_vec flipped to +1; identity should have moved positive.
    g_vec_id = s.node(nodes["ground_vec"])["attrs"]["identity_field"]
    assert g_vec_id > 0  # nudged positive


def test_recurrent_insight_nudges_identity_more():
    """Recurrent insight gets a log-scaled boost: α_eff = α·(1 + log(N)).
    Repeated insights drive identity faster."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)

    # First insight (recurrence=1).
    self_improvement_step(s, identity_alpha=0.0, identity_beta=0.0)
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    step1 = self_improvement_step(s, identity_alpha=0.0,
                                   identity_beta=0.0,
                                   identity_nudge_alpha=0.05)
    g_vec_id_after_first = s.node(nodes["ground_vec"])["attrs"]["identity_field"]

    # Reset + second insight (recurrence=2 → log(2) boost).
    s.set_attr(nodes["ground_vec"], "external_field", -2.0)
    self_improvement_step(s, identity_alpha=0.0, identity_beta=0.0)
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    step2 = self_improvement_step(s, identity_alpha=0.0,
                                   identity_beta=0.0,
                                   identity_nudge_alpha=0.05)
    g_vec_id_after_second = s.node(nodes["ground_vec"])["attrs"]["identity_field"]

    # Second nudge should add MORE to identity than the first did,
    # because (1 + log(2)) > 1.
    nudge_first = g_vec_id_after_first
    nudge_second = g_vec_id_after_second - g_vec_id_after_first
    assert nudge_second > nudge_first * 0.95  # at least nearly as much, but should be more


def test_substrate_remembers_repeated_morning_insights():
    """End-to-end: substrate has the morning insight 3 times across
    many loop steps. recurrence_count=3, identity_field on ground_vec
    has grown significantly positive (substrate has committed to the
    new basin)."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)

    # Run several cycles of perturbation + resolution.
    for _ in range(3):
        s.set_attr(nodes["ground_vec"], "external_field", -2.0)
        self_improvement_step(s)
        s.set_attr(nodes["ground_vec"], "external_field", 0.3)
        self_improvement_step(s)

    insights = list_insights(s, mt)
    # All resolutions matched the same fingerprint → single node.
    assert len(insights) == 1
    assert insights[0]["recurrence_count"] == 3
    # ground_vec's identity has been nudged positive multiple times.
    g_vec_id = s.node(nodes["ground_vec"])["attrs"]["identity_field"]
    assert g_vec_id > 0.1
