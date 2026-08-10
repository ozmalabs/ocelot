"""Tests for conflict_detection migrated to cross_mt FilterSpec
(pair-level count)."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.conflict_detection import (
    CONFLICT_STREAK_REQUIRED,
    list_conflict_events,
)
from domains.install_streak_filters import install_conflict_filter
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
               "ConflictEventFromSpec")
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


def _build_conflicting_mts(s):
    """Two Mts strongly driving a shared node in opposite directions."""
    shared = s.add_node("Concept", {"name": "shared"})
    helper_a = s.add_node("Concept", {"name": "helper_a",
                                       "external_field": +2.0})
    helper_b = s.add_node("Concept", {"name": "helper_b",
                                       "external_field": -2.0})
    mt_a = s.add_node("Microtheory", {"name": "A", "temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    mt_b = s.add_node("Microtheory", {"name": "B", "temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    s.add_edge(mt_a, "has_concept", shared, {})
    s.add_edge(mt_a, "has_concept", helper_a, {})
    s.add_edge(mt_b, "has_concept", shared, {})
    s.add_edge(mt_b, "has_concept", helper_b, {})
    s.add_edge(helper_a, "causal_influence", shared, {"weight": +1.5})
    s.add_edge(helper_b, "causal_influence", shared, {"weight": +1.5})
    return mt_a, mt_b, shared


# --- stash includes conflict count ---------------------------------------

def test_stash_pair_quantities_includes_conflict_count():
    s = _fresh_substrate()
    mt_a, mt_b, shared = _build_conflicting_mts(s)
    stash_pair_quantities(s)
    lower_id = min(mt_a.value, mt_b.value)
    higher_id = max(mt_a.value, mt_b.value)
    lower_mt = mt_a if mt_a.value < mt_b.value else mt_b
    key = f"pair_conflict_count_for_{higher_id}"
    assert key in s.node(lower_mt)["attrs"]
    # At least 1 conflicting node (the shared one).
    assert s.node(lower_mt)["attrs"][key] >= 1


# --- FilterSpec installs + fires ----------------------------------------

def test_install_conflict_filter_creates_cross_mt_spec():
    s = _fresh_substrate()
    install_conflict_filter(s)
    specs = list_filter_specs(s)
    assert len(specs) == 1
    assert specs[0]["scope"] == "cross_mt"
    assert specs[0]["name"] == "conflict_detection"


def test_conflict_filterspec_fires_for_conflicting_mts():
    """End-to-end: conflicting Mts should fire ConflictEventFromSpec."""
    s = _fresh_substrate()
    install_conflict_filter(s)
    _build_conflicting_mts(s)
    for _ in range(CONFLICT_STREAK_REQUIRED + 2):
        self_improvement_step(s)
    spec_events = list(s.nodes("ConflictEventFromSpec"))
    python_events = list_conflict_events(s)
    # Both should fire.
    assert len(spec_events) >= 1
    assert len(python_events) >= 1
