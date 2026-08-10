"""Tests for drive_curiosity_high_entropy — the substrate's first
explicit drive. Probes high-entropy nodes via what-if + records info
gain.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.drive_curiosity import (
    CURIOSITY_AMBIVALENCE_THRESHOLD,
    CURIOSITY_PROBE_DELTA,
    find_ambivalent_nodes,
    list_curiosity_probes,
    probe_via_what_if,
    record_curiosity_probe,
    run_curiosity,
    run_curiosity_all_mts,
)
from domains.self_improvement_loop import ADAPTIVE


_NODE_TYPES = ("Microtheory", "Concept", "CuriosityProbeEvent")
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


# --- find_ambivalent_nodes -----------------------------------------------

def test_find_ambivalent_returns_high_entropy_nodes():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    a = s.add_node("Concept", {"state": 0.05})   # ambivalent
    b = s.add_node("Concept", {"state": 0.95})   # decisive
    c = s.add_node("Concept", {"state": -0.02})  # ambivalent
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(mt, "has_concept", c, {})
    ambivalent = find_ambivalent_nodes(s, mt)
    ids = [x["node_id"] for x in ambivalent]
    assert a.value in ids
    assert c.value in ids
    assert b.value not in ids


def test_ambivalent_sorted_by_proximity_to_zero():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    high = s.add_node("Concept", {"state": 0.05})
    higher = s.add_node("Concept", {"state": 0.01})
    s.add_edge(mt, "has_concept", high, {})
    s.add_edge(mt, "has_concept", higher, {})
    result = find_ambivalent_nodes(s, mt)
    # closer to 0 → higher ambivalence → first in list
    assert result[0]["node_id"] == higher.value


# --- probe_via_what_if ---------------------------------------------------

def test_probe_returns_info_gain_metrics():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    a = s.add_node("Concept", {"external_field": 0.0, "state": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    probe = probe_via_what_if(s, mt, a, h_delta=0.5)
    assert "info_gain_total_change" in probe
    assert "info_gain_max_node_change" in probe
    assert probe["concept_id"] == a.value
    # With h going from 0 to +0.5 + β=2: σ ≈ tanh(1.0) ≈ 0.76
    # So info gain ≥ 0.7.
    assert probe["info_gain_total_change"] > 0.5


def test_probe_zero_info_gain_for_pinned_node():
    """A node with very strong identity_field shouldn't move much."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    a = s.add_node("Concept", {"identity_field": +5.0, "state": +1.0})
    s.add_edge(mt, "has_concept", a, {})
    probe = probe_via_what_if(s, mt, a, h_delta=0.5)
    # Even +0.5 perturbation barely moves σ (already saturated +1).
    assert probe["info_gain_total_change"] < 0.1


# --- run_curiosity per Mt ----------------------------------------------

def test_run_curiosity_returns_ranked_probes():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    # Two ambivalent nodes — one in a tight basin (decisive when probed),
    # one in a loose basin.
    a = s.add_node("Concept", {"state": 0.05, "external_field": 0.0})
    b = s.add_node("Concept", {"state": 0.05, "external_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 1.0})
    probes = run_curiosity(s, mt, top_k=5)
    assert len(probes) == 2
    # Both should have measurable info gain.
    for p in probes:
        assert p["info_gain_total_change"] > 0


def test_run_curiosity_empty_when_no_ambivalent_nodes():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    # All nodes decisive.
    a = s.add_node("Concept", {"state": 0.9, "external_field": 1.0})
    b = s.add_node("Concept", {"state": -0.9, "external_field": -1.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    probes = run_curiosity(s, mt)
    assert probes == []


def test_run_curiosity_all_mts_iterates():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"temperature": 2.0})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0})
    a = s.add_node("Concept", {"state": 0.05})
    b = s.add_node("Concept", {"state": 0.05})
    s.add_edge(mt_a, "has_concept", a, {})
    s.add_edge(mt_b, "has_concept", b, {})
    result = run_curiosity_all_mts(s)
    assert len(result) == 2
    assert mt_a.value in result
    assert mt_b.value in result


# --- Record / list ------------------------------------------------------

def test_record_curiosity_probe_creates_event_node():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    a = s.add_node("Concept", {"state": 0.05, "external_field": 0.0,
                                "name": "x"})
    s.add_edge(mt, "has_concept", a, {})
    probe = probe_via_what_if(s, mt, a, h_delta=0.5)
    probe["concept_name"] = "x"
    node = record_curiosity_probe(s, mt, probe)
    assert node is not None
    probes = list_curiosity_probes(s)
    assert len(probes) == 1
    assert probes[0]["concept_id"] == a.value
    assert probes[0]["concept_name"] == "x"
