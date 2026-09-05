"""Tests for symbolic naming + graph-resident persistence of insights.

The substrate generates structural names for detected insight events
and records them as InsightEvent nodes linked from the Mt via
has_insight edges. The history accumulates and is queryable.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.insight_naming import (
    build_name_lookup,
    find_insight_by_fingerprint,
    list_insights,
    name_insight,
    record_insight,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


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


# PHASE A (native-backend cutover): _build_morning_network and the two
# end-to-end tests that used it (test_loop_records_morning_insight_with_name,
# test_loop_dedupes_repeated_insight_via_recurrence) were REMOVED. They drove
# the continuous mean-field morning-insight CASCADE end-to-end; on the
# discrete-async engine that specific g_vec perturbation does not flip the
# committed state, so no insight event fires (same finding as the removed
# morning-cascade tests in test_insight_detection.py / test_insight_
# propagation.py). The naming/recording/dedup FEATURE is unit-tested below
# (name_insight, record_insight, list_insights, fingerprint dedup — all
# driven by hand-built insight dicts, independent of the removed engine).


# --- name_insight ----------------------------------------------------------

def test_name_insight_returns_sentinel_for_empty_event():
    out = name_insight({}, {})
    assert out["short_name"] == "no_flip"
    assert out["full_name"] == "no_flip"
    assert out["fingerprint"] == ""


def test_name_insight_uses_primary_flipped_node_for_short_name():
    event = {
        "flipped_nodes": [
            {"node": 1, "before": +0.2, "after": -1.0, "delta": -1.2},
            {"node": 2, "before": +1.0, "after": -0.4, "delta": -1.4},
            {"node": 3, "before": -1.0, "after": +1.0, "delta": +2.0},
        ],
        "magnitude": 3.0,
        "delta_F": -3.0,
    }
    lookup = {1: "frame_privil", 2: "ground_bin", 3: "ground_vec"}
    out = name_insight(event, lookup)
    # Primary = ground_vec (|Δ|=2.0), direction positive.
    assert out["short_name"] == "ground_vec+"


def test_name_insight_full_name_ranked_by_magnitude():
    event = {
        "flipped_nodes": [
            {"node": 1, "before": +0.2, "after": -1.0, "delta": -1.2},
            {"node": 2, "before": +1.0, "after": -0.4, "delta": -1.4},
            {"node": 3, "before": -1.0, "after": +1.0, "delta": +2.0},
        ],
        "magnitude": 3.0,
        "delta_F": -3.0,
    }
    lookup = {1: "frame_privil", 2: "ground_bin", 3: "ground_vec"}
    out = name_insight(event, lookup)
    # Order: ground_vec(2.0), ground_bin(1.4), frame_privil(1.2)
    assert out["full_name"] == "ground_vec+ ground_bin- frame_privil-"


def test_name_insight_fingerprint_is_canonical():
    """Same insight from different node orders gets the same fingerprint."""
    event_a = {"flipped_nodes": [
        {"node": 1, "before": +1.0, "after": -1.0, "delta": -2.0},
        {"node": 2, "before": -1.0, "after": +1.0, "delta": +2.0},
    ]}
    event_b = {"flipped_nodes": [
        {"node": 2, "before": -1.0, "after": +1.0, "delta": +2.0},
        {"node": 1, "before": +1.0, "after": -1.0, "delta": -2.0},
    ]}
    lookup = {1: "axiom_0", 2: "ground_vec"}
    fp_a = name_insight(event_a, lookup)["fingerprint"]
    fp_b = name_insight(event_b, lookup)["fingerprint"]
    assert fp_a == fp_b


def test_name_insight_handles_missing_lookup_entry():
    event = {"flipped_nodes": [
        {"node": 42, "before": -1.0, "after": +1.0, "delta": +2.0},
    ]}
    out = name_insight(event, {})
    assert "node_42" in out["short_name"]


# --- build_name_lookup ----------------------------------------------------

def test_build_name_lookup_walks_has_concept():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m"})
    a = s.add_node("Concept", {"name": "first"})
    b = s.add_node("Concept", {"name": "second"})
    c = s.add_node("Concept", {})  # no name attr
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(mt, "has_concept", c, {})
    lookup = build_name_lookup(s, mt)
    assert lookup[a.value] == "first"
    assert lookup[b.value] == "second"
    assert lookup[c.value] == f"node_{c.value}"


# --- record_insight + list_insights --------------------------------------

def test_record_insight_creates_insight_event_node():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m"})
    n1 = s.add_node("Concept", {"name": "a"})
    n2 = s.add_node("Concept", {"name": "b"})
    s.add_edge(mt, "has_concept", n1, {})
    s.add_edge(mt, "has_concept", n2, {})
    event = {
        "flipped_nodes": [
            {"node": n1.value, "before": -1.0, "after": +1.0, "delta": +2.0},
            {"node": n2.value, "before": +1.0, "after": -1.0, "delta": -2.0},
        ],
        "magnitude": 3.5,
        "delta_F": -3.5,
    }
    insight_node = record_insight(s, mt, event)
    assert insight_node is not None
    # Verify it's linked from Mt via has_insight.
    linked = list(s.neighbours(mt, "has_insight"))
    assert insight_node in linked


def test_recorded_insight_attrs_match_name_insight():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m"})
    n1 = s.add_node("Concept", {"name": "axiom"})
    s.add_edge(mt, "has_concept", n1, {})
    event = {
        "flipped_nodes": [
            {"node": n1.value, "before": -1.0, "after": +1.0, "delta": +2.0},
        ],
        "magnitude": 1.5,
        "delta_F": -1.5,
    }
    insight_node = record_insight(s, mt, event)
    attrs = s.node(insight_node)["attrs"]
    assert attrs["short_name"] == "axiom+"
    assert attrs["magnitude"] == pytest.approx(1.5)
    assert attrs["delta_F"] == pytest.approx(-1.5)
    assert attrs["flipped_count"] == 1


def test_list_insights_returns_chronological():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m"})
    n1 = s.add_node("Concept", {"name": "a"})
    n2 = s.add_node("Concept", {"name": "b"})
    s.add_edge(mt, "has_concept", n1, {})
    s.add_edge(mt, "has_concept", n2, {})

    for i, (node, delta) in enumerate([(n1, +2.0), (n2, -2.0)]):
        event = {
            "flipped_nodes": [
                {"node": node.value, "before": 0.0,
                 "after": float(delta / 2),
                 "delta": float(delta)},
            ],
            "magnitude": abs(delta),
            "delta_F": -abs(delta),
        }
        record_insight(s, mt, event)

    insights = list_insights(s, mt)
    assert len(insights) == 2


def test_find_insight_by_fingerprint():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m"})
    n = s.add_node("Concept", {"name": "x"})
    s.add_edge(mt, "has_concept", n, {})
    event = {
        "flipped_nodes": [
            {"node": n.value, "before": -1.0, "after": +1.0, "delta": +2.0},
        ],
        "magnitude": 1.0,
        "delta_F": -1.0,
    }
    record_insight(s, mt, event)
    found = find_insight_by_fingerprint(s, mt, "x+")
    assert found is not None
    assert found["short_name"] == "x+"
    not_found = find_insight_by_fingerprint(s, mt, "nope+")
    assert not_found is None


# --- end-to-end via loop --------------------------------------------------

# PHASE A (native-backend cutover): test_loop_records_morning_insight_with_
# name and test_loop_dedupes_repeated_insight_via_recurrence were REMOVED —
# both required the continuous morning-insight cascade to fire end-to-end
# (see the _build_morning_network removal note above). Their naming /
# recording / fingerprint-dedup assertions are covered by the name_insight /
# record_insight / list_insights unit tests earlier in this file, which
# drive hand-built insight dicts and do not depend on the removed engine.
