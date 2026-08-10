"""Tests for autonomous insight detection — large ΔF + node flips.

The substrate flags large frustration drops between steps as insight
events when at least one node also flipped, and consolidates the new
basin via elevated Hebbian on adaptive Mts.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.insight_detection import (
    INSIGHT_CONSOLIDATION_ETA,
    INSIGHT_FRUSTRATION_DROP_THRESHOLD,
    INSIGHT_PREVIOUS_FRUSTRATION_MIN,
    consolidate_insight,
    detect_insight,
    read_previous_state,
)
from domains.self_improvement_loop import (
    ADAPTIVE,
    FROZEN,
    self_improvement_step,
)


_NODE_TYPES = ("Microtheory", "Concept")
_EDGE_TYPES = ("has_concept", "causal_influence")


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


# --- detect_insight --------------------------------------------------------

def test_detect_insight_triggers_on_real_drop():
    """Previous frustration 4.0, current 1.0 → ΔF = -3.0, big enough.
    Node 1 went from +0.9 to -0.9 → flipped."""
    event = detect_insight(
        previous_frustration=4.0,
        previous_state={1: +0.9, 2: -0.1},
        current_audit={
            "frustration": 1.0,
            "marginal": {1: -0.9, 2: +0.7},
            "energy": -3.0,
            "coverage": 2,
        },
        mt_id=42,
    )
    assert event is not None
    assert event["mt_id"] == 42
    assert event["delta_F"] == pytest.approx(-3.0)
    assert event["magnitude"] == pytest.approx(3.0)
    flipped = event["flipped_nodes"]
    assert len(flipped) == 2  # both nodes shifted > 0.5
    flipped_node_ids = {f["node"] for f in flipped}
    assert flipped_node_ids == {1, 2}


def test_detect_insight_returns_none_when_drop_too_small():
    event = detect_insight(
        previous_frustration=4.0,
        previous_state={1: +0.9},
        current_audit={
            "frustration": 3.5,  # only 0.5 drop, below threshold
            "marginal": {1: -0.9},
            "energy": -1.0,
            "coverage": 1,
        },
        mt_id=1,
    )
    assert event is None


def test_detect_insight_returns_none_when_previously_calm():
    """If the substrate wasn't substantially frustrated, a drop isn't
    an insight — it's drift."""
    event = detect_insight(
        previous_frustration=0.1,  # below min
        previous_state={1: +0.9},
        current_audit={
            "frustration": 0.0,
            "marginal": {1: -0.9},
            "energy": -1.0,
            "coverage": 1,
        },
        mt_id=1,
    )
    assert event is None


def test_detect_insight_returns_none_when_no_node_flipped():
    """Frustration dropped but no node shifted significantly — strange
    but possible (e.g., coupling weight changed). Not an insight."""
    event = detect_insight(
        previous_frustration=4.0,
        previous_state={1: +0.5, 2: -0.5},
        current_audit={
            "frustration": 1.0,
            "marginal": {1: +0.45, 2: -0.45},  # tiny shifts
            "energy": -1.0,
            "coverage": 2,
        },
        mt_id=1,
    )
    assert event is None


# --- consolidate_insight ---------------------------------------------------

def test_consolidate_insight_runs_extra_hebbian_on_adaptive():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {
        "name": "adaptive", "temperature": 1.5,
        "update_policy": ADAPTIVE,
    })
    a = s.add_node("Concept", {"state": +0.9, "external_field": 0.8})
    b = s.add_node("Concept", {"state": +0.9, "external_field": 0.8})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.3})

    edges = consolidate_insight(s, mt, eta=0.1)
    assert edges == 1


def test_consolidate_insight_skips_frozen():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {
        "name": "frozen", "update_policy": FROZEN, "temperature": 1.5,
    })
    a = s.add_node("Concept", {"state": +0.9, "external_field": 0.8})
    b = s.add_node("Concept", {"state": +0.9, "external_field": 0.8})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.3})

    edges = consolidate_insight(s, mt, eta=0.1)
    assert edges == 0  # frozen Mt: no consolidation


# --- end-to-end via the loop -----------------------------------------------

def test_first_step_does_not_flag_insight():
    """First step has no previous state to compare against. No
    insight should fire — the network is just being born."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"external_field": 0.8})
    s.add_edge(mt, "has_concept", a, {})
    result = self_improvement_step(s)
    assert result[mt.value]["insight"] is None


def test_loop_detects_morning_insight_via_consecutive_steps():
    """End-to-end: replicate the morning's grounding=vector realisation
    through the loop, not by hand. Step 1 stabilises the frustrated
    configuration; the candidate node's h is lifted; step 2's relax
    discovers the coherent basin; the substrate flags the insight
    autonomously."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "morning", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    axiom = s.add_node("Concept", {"external_field": +1.5})
    frame_rel = s.add_node("Concept", {"external_field": +0.8})
    frame_priv = s.add_node("Concept", {"external_field": -0.5})
    g_bin = s.add_node("Concept", {"external_field": +1.2})
    g_vec = s.add_node("Concept", {"external_field": -2.0})  # not yet considered
    for n in (axiom, frame_rel, frame_priv, g_bin, g_vec):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(axiom, "causal_influence", frame_rel, {"weight": +1.0})
    s.add_edge(axiom, "causal_influence", frame_priv, {"weight": -1.0})
    s.add_edge(frame_priv, "causal_influence", g_bin, {"weight": +0.8})
    s.add_edge(frame_priv, "causal_influence", g_vec, {"weight": -0.8})
    s.add_edge(frame_rel, "causal_influence", g_vec, {"weight": +0.7})
    s.add_edge(g_bin, "causal_influence", g_vec, {"weight": -0.6})

    # Step 1: relax to frustrated stable configuration. No previous
    # state to compare to, so no insight expected this step.
    step1 = self_improvement_step(s)
    assert step1[mt.value]["insight"] is None
    step1_F = step1[mt.value]["post_audit"]["frustration"]
    assert step1_F > INSIGHT_PREVIOUS_FRUSTRATION_MIN, (
        f"expected substantial frustration after step 1; got {step1_F}")

    # The moment: lift the pin on grounding_vector.
    s.set_attr(g_vec, "external_field", 0.3)

    # Step 2: relax discovers the coherent basin; insight flagged.
    step2 = self_improvement_step(s)
    insight = step2[mt.value]["insight"]
    assert insight is not None, (
        f"insight expected; step1 F={step1_F:.2f} "
        f"step2 F={step2[mt.value]['post_audit']['frustration']:.2f}")
    assert insight["delta_F"] < -INSIGHT_FRUSTRATION_DROP_THRESHOLD
    assert insight["magnitude"] > 1.0
    assert len(insight["flipped_nodes"]) >= 2  # multiple commitments rearranged
    # Consolidation should have run (adaptive Mt).
    assert step2[mt.value]["consolidation_edges"] > 0


def test_loop_does_not_flag_insight_when_network_stable():
    """A coherent network running idle should not flag insights."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "stable", "temperature": 1.5,
                                    "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"external_field": 1.0})
    b = s.add_node("Concept", {"external_field": 1.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.5})

    # Run a few steps. Network coheres; no insights expected.
    for _ in range(3):
        result = self_improvement_step(s)
        assert result[mt.value]["insight"] is None


def test_loop_stashes_previous_state_attrs():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m", "temperature": 1.5})
    a = s.add_node("Concept", {"external_field": 1.0})
    s.add_edge(mt, "has_concept", a, {})

    # Before any step: no previous attrs.
    assert "previous_frustration" not in s.node(mt)["attrs"]
    sigma_key = f"previous_sigma_{a.value}"
    assert sigma_key not in s.node(mt)["attrs"]

    self_improvement_step(s)

    # After: Mt-side attrs exist.
    mt_attrs = s.node(mt)["attrs"]
    assert "previous_frustration" in mt_attrs
    assert sigma_key in mt_attrs
    # Concept state should be ~+1 (single node, +field, β=1.5).
    assert mt_attrs[sigma_key] > 0.7


def test_read_previous_state_round_trips():
    s = _fresh_substrate()
    a = s.add_node("Concept", {})
    mt = s.add_node("Microtheory", {
        "name": "m",
        "previous_frustration": 2.5,
        f"previous_sigma_{a.value}": 0.7,
    })
    s.add_edge(mt, "has_concept", a, {})
    prev_f, prev_state = read_previous_state(s, mt)
    assert prev_f == 2.5
    assert prev_state[a.value] == pytest.approx(0.7)
