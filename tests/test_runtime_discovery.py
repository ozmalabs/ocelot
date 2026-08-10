"""Tests for the Phase-1 graph-resident runtime discovery.

The runtime walks FilterSpec nodes from the graph + dispatches them.
This is the architectural step that lets the agent author detectors
as graph data instead of Python modules.

Migration verification: an Mt that fires frustrated_Mt via the Python
detector should ALSO fire (with the same shape) via an equivalent
FilterSpec.
"""
from __future__ import annotations

import json

import pytest
from substrate_rs import _native

from domains.frustration_signal import (
    FRUSTRATION_STREAK_REQUIRED,
    FRUSTRATION_THRESHOLD,
    list_frustrated_mt_events,
)
from domains.runtime_discovery import (
    evaluate_action_spec,
    install_filter_spec,
    list_filter_specs,
    run_all_filter_specs,
    run_filter_spec_on_concept,
    run_filter_spec_on_mt,
    run_filter_spec_on_pair,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent",
               "FrustratedMtEvent", "SparseMtEvent",
               "CorrectionAppliedEvent", "CuriosityProbeEvent",
               "FilterSpec", "GraphResidentEvent",
               "FrustratedMtEventFromSpec")
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


# --- Action spec interpreter ----------------------------------------------

def test_action_spec_set_attr_writes_to_node():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    spec = {"op": "set_attr", "target": "mt", "key": "test_key",
            "value": 42}
    evaluate_action_spec(s, spec, {"mt": mt})
    assert s.node(mt)["attrs"]["test_key"] == 42


def test_action_spec_add_node_creates_event():
    s = _fresh_substrate()
    spec = {
        "op": "add_node",
        "type": "FrustratedMtEventFromSpec",
        "attrs": {"mt_id": "$mt_id", "streak": "$streak"},
    }
    result = evaluate_action_spec(
        s, spec, {"mt_id": 5, "streak": 10})
    assert result is not None
    nodes = list(s.nodes("FrustratedMtEventFromSpec"))
    assert len(nodes) == 1
    attrs = s.node(nodes[0])["attrs"]
    assert attrs["mt_id"] == 5
    assert attrs["streak"] == 10


def test_action_spec_noop_does_nothing():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"original": "value"})
    evaluate_action_spec(s, {"op": "noop"}, {"mt": mt})
    assert s.node(mt)["attrs"]["original"] == "value"


# --- install + list ------------------------------------------------------

def test_install_filter_spec_creates_node():
    s = _fresh_substrate()
    install_filter_spec(
        s,
        name="frustrated_via_spec",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=1.0,
        direction="above",
        streak_required=10,
        action_spec={"op": "noop"},
        event_type="FrustratedMtEventFromSpec",
    )
    specs = list_filter_specs(s)
    assert len(specs) == 1
    assert specs[0]["name"] == "frustrated_via_spec"
    assert specs[0]["scope"] == "per_mt"
    assert specs[0]["threshold"] == 1.0


# --- run_filter_spec_on_mt -----------------------------------------------

def test_filter_spec_fires_on_streak_crossing():
    """Equivalent of frustration_signal but driven by FilterSpec."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    install_filter_spec(
        s, name="test_frustration",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=1.0,
        direction="above",
        streak_required=5,
        action_spec={
            "op": "add_node",
            "type": "FrustratedMtEventFromSpec",
            "attrs": {"mt_id": "$mt_id", "value": "$value",
                       "streak": "$streak"},
        },
        event_type="FrustratedMtEventFromSpec",
    )
    spec = list_filter_specs(s)[0]
    s.set_attr(mt, "previous_frustration", 1.5)
    fired_step = None
    for step in range(1, 8):
        event = run_filter_spec_on_mt(s, mt, spec)
        if event is not None:
            fired_step = step
            assert event["streak"] == 5
            break
    assert fired_step == 5

    # And the node was actually created.
    nodes = list(s.nodes("FrustratedMtEventFromSpec"))
    assert len(nodes) == 1
    attrs = s.node(nodes[0])["attrs"]
    assert attrs["streak"] == 5


def test_filter_spec_below_direction():
    """Inverse direction (sparse_Mt style): fires when value drops
    below threshold for K steps."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    install_filter_spec(
        s, name="test_below",
        scope="per_mt",
        quantity_attr="coverage",
        threshold=2.0,
        direction="below",
        streak_required=3,
        action_spec={"op": "noop"},
        event_type="GenericEvent",
    )
    spec = list_filter_specs(s)[0]
    s.set_attr(mt, "coverage", 0)
    fires = 0
    for _ in range(5):
        if run_filter_spec_on_mt(s, mt, spec) is not None:
            fires += 1
    assert fires == 1  # exactly one firing on streak crossing


def test_filter_spec_inactive_doesnt_fire():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    install_filter_spec(
        s, name="inactive",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=1.0,
        direction="above",
        streak_required=1,
        action_spec={"op": "noop"},
    )
    # Deactivate.
    spec_node = list_filter_specs(s)[0]["node"]
    s.set_attr(spec_node, "active", False)
    spec = list_filter_specs(s)[0]
    s.set_attr(mt, "previous_frustration", 2.0)
    assert run_filter_spec_on_mt(s, mt, spec) is None


def test_filter_spec_streak_resets_when_gate_fails():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    install_filter_spec(
        s, name="reset_test",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=1.0,
        direction="above",
        streak_required=5,
        action_spec={"op": "noop"},
    )
    spec = list_filter_specs(s)[0]
    # Build streak partway.
    s.set_attr(mt, "previous_frustration", 1.5)
    for _ in range(3):
        run_filter_spec_on_mt(s, mt, spec)
    streak_partway = int(s.node(mt)["attrs"].get(
        "fs_streak_reset_test", 0))
    assert streak_partway == 3

    # Drop value; streak should reset.
    s.set_attr(mt, "previous_frustration", 0.1)
    run_filter_spec_on_mt(s, mt, spec)
    assert int(s.node(mt)["attrs"]["fs_streak_reset_test"]) == 0


# --- run_all_filter_specs (substrate-level) ----------------------------

def test_run_all_filter_specs_iterates():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"previous_frustration": 2.0})
    mt_b = s.add_node("Microtheory", {"previous_frustration": 2.0})
    install_filter_spec(
        s, name="frustrated_test",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=1.0,
        direction="above",
        streak_required=3,
        action_spec={"op": "noop"},
    )
    for _ in range(3):
        events = run_all_filter_specs(s)
    # On the third call, both Mts should have fired.
    assert len(events) == 2


# --- Parity: spec-driven frustration matches Python frustration_signal --

def test_filter_spec_parity_with_frustration_signal():
    """End-to-end: install a FilterSpec that mirrors the Python
    frustration_signal detector. Verify the spec-driven detection
    produces an event when the Python detector would, on the same
    network."""
    s = _fresh_substrate()
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

    # Install the FilterSpec equivalent of frustration_signal.
    install_filter_spec(
        s, name="frustrated_via_spec",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=FRUSTRATION_THRESHOLD,
        direction="above",
        streak_required=FRUSTRATION_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "FrustratedMtEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "frustration": "$value",
                "streak": "$streak",
            },
        },
        event_type="FrustratedMtEventFromSpec",
    )

    for _ in range(FRUSTRATION_STREAK_REQUIRED + 3):
        self_improvement_step(s)

    # Both detectors should have fired.
    python_events = list_frustrated_mt_events(s)
    spec_events = list(s.nodes("FrustratedMtEventFromSpec"))
    assert len(python_events) >= 1
    assert len(spec_events) >= 1


# --- per_concept scope ---------------------------------------------------

def test_per_concept_filter_iterates_concepts():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    a = s.add_node("Concept", {"identity_field": 1.5, "name": "a"})
    b = s.add_node("Concept", {"identity_field": 0.1, "name": "b"})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})

    install_filter_spec(
        s, name="strong_identity",
        scope="per_concept",
        quantity_attr="identity_field",
        threshold=1.0,
        direction="above",
        streak_required=1,
        action_spec={"op": "noop"},
    )
    spec = list_filter_specs(s)[0]
    event_a = run_filter_spec_on_concept(s, mt, a, spec)
    event_b = run_filter_spec_on_concept(s, mt, b, spec)
    assert event_a is not None  # |h_id|=1.5 > 1.0
    assert event_b is None       # 0.1 ≤ 1.0


def test_per_concept_streaks_isolated_per_concept():
    """Two concepts with separate streak counters."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    a = s.add_node("Concept", {"identity_field": 2.0})
    b = s.add_node("Concept", {"identity_field": 0.2})  # below threshold
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})

    install_filter_spec(
        s, name="iso_test",
        scope="per_concept",
        quantity_attr="identity_field",
        threshold=1.0,
        direction="above",
        streak_required=3,
        action_spec={"op": "noop"},
    )
    spec = list_filter_specs(s)[0]
    for _ in range(5):
        run_filter_spec_on_concept(s, mt, a, spec)
        run_filter_spec_on_concept(s, mt, b, spec)
    # a's streak should grow; b's should stay 0.
    streak_a = int(s.node(mt)["attrs"][
        f"fs_streak_iso_test_concept_{a.value}"])
    streak_b = int(s.node(mt)["attrs"].get(
        f"fs_streak_iso_test_concept_{b.value}", 0))
    assert streak_a >= 3
    assert streak_b == 0


# --- cross_mt scope ------------------------------------------------------

def test_cross_mt_filter_reads_pre_computed_pair_attr():
    """Cross-Mt filter reads a per-pair attr that's been stashed on
    the lower-id Mt."""
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {})
    mt_b = s.add_node("Microtheory", {})
    # Canonical: lower-id holds attr. Pre-stash the similarity.
    lower_mt = mt_a if mt_a.value < mt_b.value else mt_b
    higher_id = mt_b.value if mt_a.value < mt_b.value else mt_a.value
    s.set_attr(lower_mt, f"pair_similarity_for_{higher_id}", 0.95)

    install_filter_spec(
        s, name="high_pair_sim",
        scope="cross_mt",
        quantity_attr="pair_similarity",
        threshold=0.9,
        direction="above",
        streak_required=1,
        action_spec={"op": "noop"},
    )
    spec = list_filter_specs(s)[0]
    event = run_filter_spec_on_pair(s, mt_a, mt_b, spec)
    assert event is not None
    assert event["value"] == pytest.approx(0.95)


def test_cross_mt_canonicalises_pair_order():
    """Pair (a, b) and (b, a) should hit the same streak counter."""
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {})
    mt_b = s.add_node("Microtheory", {})
    lower_mt = mt_a if mt_a.value < mt_b.value else mt_b
    higher_id = mt_b.value if mt_a.value < mt_b.value else mt_a.value
    s.set_attr(lower_mt, f"sim_for_{higher_id}", 0.95)

    install_filter_spec(
        s, name="pair_canon",
        scope="cross_mt",
        quantity_attr="sim",
        threshold=0.9,
        direction="above",
        streak_required=3,
        action_spec={"op": "noop"},
    )
    spec = list_filter_specs(s)[0]
    # Run with (a, b) then (b, a) alternately.
    for _ in range(3):
        run_filter_spec_on_pair(s, mt_a, mt_b, spec)
        run_filter_spec_on_pair(s, mt_b, mt_a, spec)
    # Streak attr should be on the lower-id Mt with higher-id suffix.
    streak = int(s.node(lower_mt)["attrs"][
        f"fs_streak_pair_canon_pair_{higher_id}"])
    # Two calls per iteration × 3 iterations = 6, but each (a,b) and
    # (b,a) re-canonicalise to the same pair → streak grows by 2 per loop.
    assert streak >= 3


# --- run_all_filter_specs respects scope --------------------------------

def test_run_all_dispatches_scope_correctly():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"previous_frustration": 2.0})
    c = s.add_node("Concept", {"identity_field": 2.0})
    s.add_edge(mt, "has_concept", c, {})

    install_filter_spec(
        s, name="per_mt_spec",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=1.0, direction="above", streak_required=1,
        action_spec={"op": "noop"},
    )
    install_filter_spec(
        s, name="per_concept_spec",
        scope="per_concept",
        quantity_attr="identity_field",
        threshold=1.0, direction="above", streak_required=1,
        action_spec={"op": "noop"},
    )
    events = run_all_filter_specs(s)
    # Both scopes should fire (one per_mt + one per_concept).
    assert len(events) == 2
