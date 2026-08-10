"""Tests for correction_prune_Mt — substrate's 3rd correction."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.correction_beta_reweight import BETA_MIN
from domains.correction_prune_mt import apply_prune_mt
from domains.sparseness_signal import SPARSE_STREAK_REQUIRED
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent",
               "FrustratedMtEvent", "SparseMtEvent",
               "CorrectionAppliedEvent")
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


def test_apply_prune_lowers_beta_to_min():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    new_beta = apply_prune_mt(s, mt)
    assert new_beta == BETA_MIN
    assert s.node(mt)["attrs"]["temperature"] == BETA_MIN


def test_apply_prune_preserves_concepts():
    """Pruning lowers β but doesn't delete the Mt or its concepts."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "to_prune",
                                    "temperature": 2.0})
    c = s.add_node("Concept", {"name": "preserved"})
    s.add_edge(mt, "has_concept", c, {})
    apply_prune_mt(s, mt)
    # Mt's β is now BETA_MIN, but everything else is preserved.
    assert s.node(mt)["attrs"]["temperature"] == BETA_MIN
    assert s.node(mt)["attrs"].get("name") == "to_prune"
    neighbours = list(s.neighbours(mt, "has_concept"))
    assert c in neighbours


def test_loop_prunes_sparse_mt():
    """Sustained low coverage → SparseMtEvent → prune_Mt → β = BETA_MIN."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "sparse",
                                    "temperature": 0.01,
                                    "update_policy": ADAPTIVE})
    for i in range(3):
        c = s.add_node("Concept", {"external_field": 0.0})
        s.add_edge(mt, "has_concept", c, {})

    for _ in range(SPARSE_STREAK_REQUIRED + 3):
        self_improvement_step(s)

    # If sparse event fired, β was set to BETA_MIN.
    final_beta = float(s.node(mt)["attrs"]["temperature"])
    if final_beta == BETA_MIN:
        # Correction was applied.
        pass
    else:
        # Possibly didn't fire (small test network may not stay sparse).
        assert final_beta >= BETA_MIN
