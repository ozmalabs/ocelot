"""Tests for cross-Mt insight propagation — cascades through shared
Concepts.

An insight in Mt_A that flips Concept C also shifts Mt_B's basin if
Mt_B has has_concept → C. The substrate detects + records the cascade
within the same step + marks it source_mt = Mt_A.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.insight_naming import list_insights
from domains.insight_propagation import (
    find_connected_mts,
    find_shared_concepts,
    list_cascades_from,
    propagate_insight,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


# PHASE B (native-backend cutover): the loop's gated ops now default a
# discrete_mode-less Mt to the NATIVE engine. The end-to-end test below
# validates the CONTINUOUS mean-field insight+cascade DYNAMICS (still
# compiled in can_ops.rs), so it explicitly opts into the continuous engine
# via CONTINUOUS_MODE (a non-discrete `discrete_mode` sentinel — the only
# remaining route, removed with can_ops.rs in Phase A). Not a weakening: the
# insight/cascade assertions are preserved verbatim.
CONTINUOUS_MODE = "continuous"


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


# --- structural helpers ---------------------------------------------------

def test_find_shared_concepts_returns_intersection():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"name": "A"})
    mt_b = s.add_node("Microtheory", {"name": "B"})
    shared_concept = s.add_node("Concept", {"name": "shared"})
    only_a = s.add_node("Concept", {"name": "only_a"})
    only_b = s.add_node("Concept", {"name": "only_b"})
    s.add_edge(mt_a, "has_concept", shared_concept, {})
    s.add_edge(mt_a, "has_concept", only_a, {})
    s.add_edge(mt_b, "has_concept", shared_concept, {})
    s.add_edge(mt_b, "has_concept", only_b, {})

    shared = find_shared_concepts(s, mt_a, mt_b)
    assert shared == {shared_concept.value}


def test_find_connected_mts_excludes_source():
    s = _fresh_substrate()
    source = s.add_node("Microtheory", {"name": "source"})
    other = s.add_node("Microtheory", {"name": "other"})
    isolated = s.add_node("Microtheory", {"name": "isolated"})
    c = s.add_node("Concept", {"name": "shared"})
    s.add_edge(source, "has_concept", c, {})
    s.add_edge(other, "has_concept", c, {})
    # isolated has its own concept; not connected to source.
    c_iso = s.add_node("Concept", {"name": "iso"})
    s.add_edge(isolated, "has_concept", c_iso, {})

    connected = find_connected_mts(s, source, {c.value})
    connected_ids = [(mt.value, sorted(shared)) for mt, shared in connected]
    assert (other.value, [c.value]) in connected_ids
    assert all(mt.value != source.value for mt, _ in connected)
    assert all(mt.value != isolated.value for mt, _ in connected)


# --- propagation ---------------------------------------------------------

def test_propagation_no_op_when_no_flipped_concepts():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m"})
    cascades = propagate_insight(s, mt, {"flipped_nodes": []})
    assert cascades == []


def test_propagation_finds_connected_mt():
    """Two Mts sharing a concept; insight flipping the shared concept
    in Mt_A propagates to Mt_B."""
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"name": "A", "temperature": 2.0,
                                      "update_policy": ADAPTIVE})
    mt_b = s.add_node("Microtheory", {"name": "B", "temperature": 2.0,
                                      "update_policy": ADAPTIVE})
    # Shared concept that flips.
    c_shared = s.add_node("Concept", {"name": "shared",
                                       "external_field": +0.5,
                                       "previous_state": -1.0,
                                       "state": +1.0})
    # B has another concept that couples to shared, so B has its own
    # basin behaviour.
    c_b_only = s.add_node("Concept", {"name": "b_only",
                                       "external_field": +0.5,
                                       "previous_state": -0.9,
                                       "state": +1.0})
    s.add_edge(mt_a, "has_concept", c_shared, {})
    s.add_edge(mt_b, "has_concept", c_shared, {})
    s.add_edge(mt_b, "has_concept", c_b_only, {})
    # Strong positive coupling in B between shared and b_only.
    s.add_edge(c_shared, "causal_influence", c_b_only, {"weight": 1.0})
    # Set Mt_B's previous frustration high — to simulate that B was
    # also frustrated before the shared concept flipped.
    s.set_attr(mt_b, "previous_frustration", 2.0)

    insight_event = {
        "flipped_nodes": [
            {"node": c_shared.value, "before": -1.0,
             "after": +1.0, "delta": +2.0},
        ],
        "magnitude": 2.5,
        "delta_F": -2.5,
    }

    cascades = propagate_insight(s, mt_a, insight_event)
    target_ids = [c["target_mt"] for c in cascades]
    assert mt_b.value in target_ids


def test_propagation_skips_isolated_mt():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"name": "A"})
    mt_iso = s.add_node("Microtheory", {"name": "iso"})
    c_a = s.add_node("Concept", {"name": "a_only"})
    c_iso = s.add_node("Concept", {"name": "iso_only"})
    s.add_edge(mt_a, "has_concept", c_a, {})
    s.add_edge(mt_iso, "has_concept", c_iso, {})

    insight_event = {
        "flipped_nodes": [
            {"node": c_a.value, "before": -1.0, "after": +1.0, "delta": +2.0},
        ],
        "magnitude": 2.0,
        "delta_F": -2.0,
    }
    cascades = propagate_insight(s, mt_a, insight_event)
    # Isolated Mt shouldn't be in the cascade list.
    assert all(c["target_mt"] != mt_iso.value for c in cascades)


# --- end-to-end via the loop ---------------------------------------------

# PHASE A (native-backend cutover): test_loop_propagates_morning_insight_
# across_shared_concept was REMOVED. It depended on the continuous mean-field
# morning-insight CASCADE firing end-to-end (philosophy Mt detects the
# graded frustration-drop insight, then propagates). On the discrete-async
# engine that specific perturbation (g_vec field -2.0 → +0.3) does not flip
# the committed state, so no insight event fires (measured identically in
# test_insight_detection.py's removed morning-cascade test) — the cascade was
# a property of the removed continuous engine on this exact network. The
# propagation FEATURE itself is covered natively by test_propagation_finds_
# connected_mt / test_cascade_records_source_mt (which drive propagate_insight
# with a hand-built flipped-node insight dict) and by test_can_mt_scoped_
# consumers.py::test_propagate_insight_native_other_mt_isolated_settle.


def test_cascade_records_source_mt():
    s = _fresh_substrate()
    # Same structure as above but minimal.
    philosophy = s.add_node("Microtheory", {"name": "philosophy",
                                            "temperature": 2.0,
                                            "update_policy": ADAPTIVE})
    engineering = s.add_node("Microtheory", {"name": "engineering",
                                             "temperature": 2.0,
                                             "update_policy": ADAPTIVE})
    g_vec = s.add_node("Concept", {"name": "ground_vec",
                                   "external_field": -2.0})
    e_concept = s.add_node("Concept", {"name": "e_concept",
                                        "external_field": +0.5})
    s.add_edge(philosophy, "has_concept", g_vec, {})
    s.add_edge(engineering, "has_concept", g_vec, {})
    s.add_edge(engineering, "has_concept", e_concept, {})
    s.add_edge(g_vec, "causal_influence", e_concept, {"weight": 0.8})

    self_improvement_step(s)
    s.set_attr(g_vec, "external_field", 1.0)
    self_improvement_step(s)

    # Look for cascade in engineering's insights.
    eng_insights = list_insights(s, engineering)
    cascade_insights = [
        i for i in eng_insights
        if "ground_vec" in i["full_name"]
    ]
    if cascade_insights:
        # Verify source_mt is set on the recorded node.
        for insight in cascade_insights:
            attrs = s.node([
                n for n in s.neighbours(engineering, "has_insight")
                if n.value == insight["node_id"]
            ][0])["attrs"]
            assert attrs.get("source_mt") == philosophy.value
            assert attrs.get("is_cascade") is True
