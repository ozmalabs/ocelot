"""Tests for redundancy_detection migrated to cross_mt FilterSpec."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.install_streak_filters import install_redundancy_filter
from domains.redundancy_detection import (
    REDUNDANCY_STREAK_REQUIRED,
    list_redundancy_events,
)
from domains.runtime_discovery import (
    list_filter_specs,
    stash_pair_quantities,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent",
               "FrustratedMtEvent", "SparseMtEvent",
               "CorrectionAppliedEvent", "CuriosityProbeEvent",
               "FilterSpec", "ActionSpec",
               "FrustratedMtEventFromSpec", "SparseMtEventFromSpec",
               "FrozenShouldAdaptEventFromSpec",
               "DriftedPastAnchorEventFromSpec",
               "RedundancyEventFromSpec")
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


def _build_twin_mts(s, n_concepts: int = 4):
    """Two Mts sharing all concepts with identical couplings → similarity ≈ 1."""
    concepts = []
    for i in range(n_concepts):
        c = s.add_node("Concept",
                       {"external_field": +1.0 if i % 2 == 0 else -0.5})
        concepts.append(c)
    mt_a = s.add_node("Microtheory", {"name": "A", "temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    mt_b = s.add_node("Microtheory", {"name": "B", "temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    for c in concepts:
        s.add_edge(mt_a, "has_concept", c, {})
        s.add_edge(mt_b, "has_concept", c, {})
    s.add_edge(concepts[0], "causal_influence", concepts[1], {"weight": 0.8})
    s.add_edge(concepts[2], "causal_influence", concepts[3], {"weight": 0.8})
    return mt_a, mt_b


# --- stash_pair_quantities -----------------------------------------------

def test_stash_pair_quantities_writes_attrs():
    s = _fresh_substrate()
    mt_a, mt_b = _build_twin_mts(s)
    count = stash_pair_quantities(s)
    assert count >= 1
    # Lower-id Mt should now have pair_similarity_for_<higher_id> attr.
    lower_id = min(mt_a.value, mt_b.value)
    higher_id = max(mt_a.value, mt_b.value)
    lower_mt = mt_a if mt_a.value < mt_b.value else mt_b
    key = f"pair_similarity_for_{higher_id}"
    assert key in s.node(lower_mt)["attrs"]
    # Twin Mts should have similarity near 1.
    sim = float(s.node(lower_mt)["attrs"][key])
    assert sim > 0.99


def test_stash_skips_pairs_with_no_shared_concepts():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {})
    mt_b = s.add_node("Microtheory", {})
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    s.add_edge(mt_a, "has_concept", a, {})
    s.add_edge(mt_b, "has_concept", b, {})
    count = stash_pair_quantities(s)
    assert count == 0


# --- FilterSpec installs + fires ----------------------------------------

def test_install_redundancy_filter_creates_cross_mt_spec():
    s = _fresh_substrate()
    install_redundancy_filter(s)
    specs = list_filter_specs(s)
    assert len(specs) == 1
    assert specs[0]["scope"] == "cross_mt"
    assert specs[0]["name"] == "redundancy_detection"


def test_redundancy_filterspec_fires_for_twins_via_loop():
    """End-to-end: install the FilterSpec, run loop, twin Mts should
    fire RedundancyEventFromSpec."""
    s = _fresh_substrate()
    install_redundancy_filter(s)
    _build_twin_mts(s)
    for _ in range(REDUNDANCY_STREAK_REQUIRED + 2):
        self_improvement_step(s)
    spec_events = list(s.nodes("RedundancyEventFromSpec"))
    python_events = list_redundancy_events(s)
    # Both should fire on the same twin Mts.
    assert len(spec_events) >= 1
    assert len(python_events) >= 1
