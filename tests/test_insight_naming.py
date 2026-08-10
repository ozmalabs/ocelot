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

def test_loop_records_morning_insight_with_name():
    """When the loop detects the morning insight, it records the event
    as an InsightEvent node carrying the short_name."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)

    # Step 1: frustrated stable state.
    self_improvement_step(s)

    # The moment.
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)

    # Step 2: detect + name + record.
    step2 = self_improvement_step(s)
    insight = step2[mt.value]["insight"]
    assert insight is not None
    assert "names" in insight
    names = insight["names"]
    # Primary flipped node is ground_vec (largest |Δ|).
    assert names["short_name"] == "ground_vec+"
    assert "ground_vec" in names["full_name"]
    assert "recorded_as_node" in insight

    # The event is queryable via list_insights.
    insights = list_insights(s, mt)
    assert len(insights) == 1
    assert insights[0]["short_name"] == "ground_vec+"
    assert insights[0]["fingerprint"]


def test_loop_dedupes_repeated_insight_via_recurrence():
    """Same insight (same fingerprint) twice should result in ONE
    InsightEvent with recurrence_count=2, not two separate nodes."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)

    # First detection: lift ground_vec.
    self_improvement_step(s)
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    self_improvement_step(s)

    insights_after_first = list_insights(s, mt)
    assert len(insights_after_first) == 1
    first_count = insights_after_first[0]["recurrence_count"]
    assert first_count == 1

    # Push back to frustrated state, then resolve again — same
    # fingerprint should match.
    s.set_attr(nodes["ground_vec"], "external_field", -2.0)
    self_improvement_step(s)
    s.set_attr(nodes["ground_vec"], "external_field", 0.5)
    self_improvement_step(s)

    insights_after_second = list_insights(s, mt)
    # Still ONE node, count should have grown.
    assert len(insights_after_second) == 1
    assert insights_after_second[0]["recurrence_count"] >= 2
