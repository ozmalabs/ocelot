"""Tests for identity_formation migrated to per_concept FilterSpec."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.identity_formation import IDENTITY_FORMATION_STREAK_REQUIRED
from domains.install_streak_filters import install_identity_formation_filter
from domains.runtime_discovery import (
    list_filter_specs,
    stash_delta_identity_per_concept,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent",
               "FrustratedMtEvent", "SparseMtEvent",
               "CorrectionAppliedEvent", "CuriosityProbeEvent",
               "FilterSpec", "ActionSpec",
               "IdentityFormationEventFromSpec")
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


# --- stash_delta_identity_per_concept -----------------------------------

def test_stash_delta_identity_computes_diff():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    c = s.add_node("Concept", {"identity_field": 0.7})
    s.add_edge(mt, "has_concept", c, {})
    s.set_attr(mt, f"previous_identity_{c.value}", 0.5)
    count = stash_delta_identity_per_concept(s)
    assert count == 1
    assert s.node(c)["attrs"]["delta_identity"] == pytest.approx(0.2)


def test_stash_skips_concepts_without_history():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    c = s.add_node("Concept", {"identity_field": 0.7})
    s.add_edge(mt, "has_concept", c, {})
    # No previous_identity attr.
    count = stash_delta_identity_per_concept(s)
    assert count == 0


# --- FilterSpec installs + fires ----------------------------------------

def test_install_identity_formation_creates_per_concept_spec():
    s = _fresh_substrate()
    install_identity_formation_filter(s)
    specs = list_filter_specs(s)
    assert len(specs) == 1
    assert specs[0]["scope"] == "per_concept"
    assert specs[0]["name"] == "identity_formation"


def test_identity_formation_spec_fires_on_sustained_drift():
    """A Concept with consistently positive σ + identity dynamics
    on → identity drifts up → FilterSpec fires."""
    s = _fresh_substrate()
    install_identity_formation_filter(s)
    mt = s.add_node("Microtheory", {"name": "m", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    c = s.add_node("Concept", {"name": "axiom",
                                "external_field": +1.5,
                                "identity_field": 0.0})
    s.add_edge(mt, "has_concept", c, {})
    # Use aggressive identity_alpha to make the test converge fast.
    for _ in range(30):
        self_improvement_step(s, identity_alpha=0.05,
                                identity_beta=0.001)
    spec_events = list(s.nodes("IdentityFormationEventFromSpec"))
    assert len(spec_events) >= 1
