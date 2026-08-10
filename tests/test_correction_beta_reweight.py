"""Tests for correction_beta_reweight — substrate's second correction.
Closes the loop:
  detect (conflicting_reflexes) → correct (beta_reweight) → verify.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.conflict_detection import CONFLICT_STREAK_REQUIRED
from domains.correction_beta_reweight import (
    BETA_MAX, BETA_MIN, BETA_REWEIGHT_DELTA,
    apply_beta_reweight,
)
from domains.correction_raise_plasticity import list_corrections_applied
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


# --- Direct apply_beta_reweight -----------------------------------------

def test_apply_beta_reweight_winner_gets_higher_beta():
    """|σ_a| > |σ_b| → mt_a wins; β_a +=, β_b -=."""
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"temperature": 2.0})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0})
    result = apply_beta_reweight(s, mt_a, mt_b,
                                  sigma_a=+0.9, sigma_b=-0.3)
    assert result["mt_a_beta"] == pytest.approx(2.0 + BETA_REWEIGHT_DELTA)
    assert result["mt_b_beta"] == pytest.approx(2.0 - BETA_REWEIGHT_DELTA)


def test_apply_beta_reweight_other_winner():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"temperature": 2.0})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0})
    result = apply_beta_reweight(s, mt_a, mt_b,
                                  sigma_a=+0.3, sigma_b=-0.9)
    assert result["mt_a_beta"] == pytest.approx(2.0 - BETA_REWEIGHT_DELTA)
    assert result["mt_b_beta"] == pytest.approx(2.0 + BETA_REWEIGHT_DELTA)


def test_apply_beta_reweight_tie_no_change():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"temperature": 2.0})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0})
    # Equal magnitudes → tie.
    result = apply_beta_reweight(s, mt_a, mt_b,
                                  sigma_a=+0.5, sigma_b=-0.5)
    assert result["mt_a_beta"] == pytest.approx(2.0)
    assert result["mt_b_beta"] == pytest.approx(2.0)


def test_apply_beta_reweight_respects_min_floor():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"temperature": 2.0})
    mt_b = s.add_node("Microtheory", {"temperature": BETA_MIN})
    # mt_a wins; mt_b should NOT go below BETA_MIN.
    result = apply_beta_reweight(s, mt_a, mt_b,
                                  sigma_a=+0.9, sigma_b=-0.3)
    assert result["mt_b_beta"] == pytest.approx(BETA_MIN)


def test_apply_beta_reweight_respects_max_ceiling():
    s = _fresh_substrate()
    mt_a = s.add_node("Microtheory", {"temperature": BETA_MAX})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0})
    # mt_a wins; should NOT exceed BETA_MAX.
    result = apply_beta_reweight(s, mt_a, mt_b,
                                  sigma_a=+0.9, sigma_b=-0.3)
    assert result["mt_a_beta"] == pytest.approx(BETA_MAX)


# --- End-to-end via loop ------------------------------------------------

def _build_conflicting_mts(s):
    """Two Mts strongly driving shared node in opposite directions."""
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


def test_loop_applies_beta_reweight_after_conflict():
    """Sustained conflict → ConflictEvent → beta_reweight applied."""
    s = _fresh_substrate()
    mt_a, mt_b, shared = _build_conflicting_mts(s)
    initial_beta_a = float(s.node(mt_a)["attrs"]["temperature"])
    initial_beta_b = float(s.node(mt_b)["attrs"]["temperature"])
    for _ in range(CONFLICT_STREAK_REQUIRED + 2):
        self_improvement_step(s)
    # If ConflictEvent fired, betas should have shifted (one up, one down).
    final_beta_a = float(s.node(mt_a)["attrs"]["temperature"])
    final_beta_b = float(s.node(mt_b)["attrs"]["temperature"])
    correction_applied = (
        abs(final_beta_a - initial_beta_a) > 1e-4
        or abs(final_beta_b - initial_beta_b) > 1e-4
    )
    # We expect SOMETHING to have shifted (or for the correction to
    # have been recorded).
    corrections = list_corrections_applied(s)
    has_beta_record = any(c["correction"] == "beta_reweight"
                          for c in corrections)
    assert correction_applied or has_beta_record


def test_loop_no_beta_reweight_for_agreeing_mts():
    """If two Mts agree (no conflict), no beta_reweight applied."""
    s = _fresh_substrate()
    shared = s.add_node("Concept", {"external_field": +1.0})
    mt_a = s.add_node("Microtheory", {"temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    mt_b = s.add_node("Microtheory", {"temperature": 2.0,
                                       "update_policy": ADAPTIVE})
    s.add_edge(mt_a, "has_concept", shared, {})
    s.add_edge(mt_b, "has_concept", shared, {})
    for _ in range(CONFLICT_STREAK_REQUIRED + 3):
        self_improvement_step(s)
    # No conflict → no β change.
    final_beta_a = float(s.node(mt_a)["attrs"]["temperature"])
    final_beta_b = float(s.node(mt_b)["attrs"]["temperature"])
    assert final_beta_a == pytest.approx(2.0)
    assert final_beta_b == pytest.approx(2.0)
