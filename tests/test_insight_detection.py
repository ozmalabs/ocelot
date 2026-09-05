"""Tests for autonomous insight detection — large ΔF + node flips.

The substrate flags large frustration drops between steps as insight
events when at least one node also flipped, and consolidates the new
basin via elevated Hebbian on adaptive Mts.
"""
from __future__ import annotations

import json

import pytest
from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

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

_CAN_SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
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


def _native_substrate():
    s = _fresh_substrate()
    for path in _CAN_SEED_PATHS:
        s.load_seed_manifest(engine_rules_only(json.load(open(path))))
    return s


# PHASE B (native-backend cutover): the gated ops now default an Mt with no
# `discrete_mode` to the NATIVE discrete engine. The tests below validate the
# CONTINUOUS mean-field relaxation DYNAMICS themselves (frustration drops,
# node flips, extra-Hebbian counts) — real-dynamics coverage of the still-
# compiled can_ops.rs engine, NOT the fork. To keep exercising that engine
# they explicitly opt into it via CONTINUOUS_MODE (a non-discrete
# `discrete_mode` sentinel — the only remaining route into the continuous
# branch, which Phase A removes along with can_ops.rs). This is an opt-in, not
# a weakening: every assertion on the continuous dynamics is preserved verbatim.
CONTINUOUS_MODE = "continuous"


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
    # PHASE A (native): re-pointed. consolidate_insight is native-only; on an
    # adaptive native Mt it mints a causal_influence coupling between two
    # cross-tick co-recurrent concepts (can_native_hebbian_mint). Mirrors
    # test_can_mt_scoped_consumers.test_consolidate_insight_native_mints_on_
    # recurrence_gated_by_policy. (Was: continuous mt_hebbian_update_J
    # returning edges==1.)
    s = _native_substrate()
    mt = s.add_node("Microtheory", {
        "name": "adaptive", "temperature": 1.5, "update_policy": ADAPTIVE,
        "discrete_mode": "3state", "can_tick": 0,
    })
    a = s.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    consolidate_insight(s, mt)          # tick 0: notes co-activation
    assert b not in s.neighbours(a, "causal_influence")
    s.set_attr(mt, "can_tick", 1)
    consolidate_insight(s, mt)          # tick 1: recurrence → mint
    assert b in s.neighbours(a, "causal_influence")


def test_consolidate_insight_skips_frozen():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {
        "name": "frozen", "update_policy": FROZEN, "temperature": 1.5,
        "discrete_mode": CONTINUOUS_MODE,
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
                                    "update_policy": ADAPTIVE,
                                    "discrete_mode": CONTINUOUS_MODE})
    a = s.add_node("Concept", {"external_field": 0.8})
    s.add_edge(mt, "has_concept", a, {})
    result = self_improvement_step(s)
    assert result[mt.value]["insight"] is None


# PHASE A (native-backend cutover): test_loop_detects_morning_insight_via_
# consecutive_steps was REMOVED. It drove a specific continuous mean-field
# frustration-drop CASCADE (lifting g_vec's field from -2.0 to +0.3 triggers
# a graded multi-node rearrangement that crosses the insight-detection ΔF
# threshold). On the discrete-async engine this exact perturbation does NOT
# flip the committed state (measured: step1 F=3.40 → step2 F=3.40 unchanged),
# because the discrete threshold keeps g_vec pinned by its couplings — the
# graded cascade was a property of the removed continuous engine on this
# specific network, not of the insight-detection feature. The surviving
# insight machinery is covered by the detect_insight unit tests above (pure
# logic over an audit dict) and by tests/test_can_mt_scoped_consumers.py's
# native consolidate_insight coverage. Re-expressing the cascade natively
# would require a hand-designed discrete scenario that is a NEW test, not a
# faithful migration of this continuous one.


def test_loop_does_not_flag_insight_when_network_stable():
    """A coherent network running idle should not flag insights."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "stable", "temperature": 1.5,
                                    "update_policy": ADAPTIVE,
                                    "discrete_mode": CONTINUOUS_MODE})
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
    # PHASE A (native): re-pointed to a native 3-state Mt. self_improvement_
    # step settles committed state via the native discrete engine; the
    # single +field node settles to +1 and is stashed.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"name": "m", "temperature": 1.5,
                                    "discrete_mode": "3state", "can_tick": 0,
                                    "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"external_field": 1.0, "state": 0.0,
                               "identity_field": 0.0})
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
    # Concept state should be +1 (single node, +field, native 3-state).
    assert mt_attrs[sigma_key] > 0


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
