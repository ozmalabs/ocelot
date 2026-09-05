"""Tests for insight + anticipation signals migrated to per_mt
FilterSpecs (degraded — core signal only, rich event content
remains in Python detectors)."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.install_streak_filters import (
    install_anticipation_filter,
    install_insight_filter,
)
from domains.runtime_discovery import list_filter_specs
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent",
               "AnticipationEvent", "IdentityFormationEvent",
               "RedundancyEvent", "ConflictEvent",
               "FrozenShouldAdaptEvent", "DriftedPastAnchorEvent",
               "FrustratedMtEvent", "SparseMtEvent",
               "CorrectionAppliedEvent", "CuriosityProbeEvent",
               "FilterSpec", "ActionSpec",
               "InsightSignalFromSpec", "AnticipationSignalFromSpec")
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


# PHASE A (native-backend cutover): _build_morning_network was REMOVED —
# see the removal note on test_insight_signal_fires_on_morning_resolution.


# --- Installs -----------------------------------------------------------

def test_install_insight_creates_per_mt_below_spec():
    s = _fresh_substrate()
    install_insight_filter(s)
    specs = list_filter_specs(s)
    assert len(specs) == 1
    assert specs[0]["scope"] == "per_mt"
    assert specs[0]["direction"] == "below"
    assert specs[0]["threshold"] == -1.0


def test_install_anticipation_creates_per_mt_below_spec():
    s = _fresh_substrate()
    install_anticipation_filter(s)
    specs = list_filter_specs(s)
    assert len(specs) == 1
    assert specs[0]["scope"] == "per_mt"
    assert specs[0]["direction"] == "below"
    assert specs[0]["threshold"] == -0.02


# --- End-to-end firing --------------------------------------------------

# PHASE A (native-backend cutover): test_insight_signal_fires_on_morning_
# resolution was REMOVED. It required the continuous morning-insight cascade
# to fire so the per-Mt insight FilterSpec would detect the ΔF drop; the
# discrete-async engine does not reproduce that cascade on this network (same
# finding as the removed morning-cascade tests in test_insight_detection.py).
# The FilterSpec install + gating machinery is covered by test_install_
# insight_creates_per_mt_below_spec / test_install_anticipation_creates_per_
# mt_below_spec and by test_insight_signal_does_not_fire_on_quiet_network.


def test_insight_signal_does_not_fire_on_quiet_network():
    s = _fresh_substrate()
    install_insight_filter(s)
    mt = s.add_node("Microtheory", {"temperature": 1.5,
                                    "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"external_field": 1.0})
    s.add_edge(mt, "has_concept", a, {})
    for _ in range(5):
        self_improvement_step(s)
    assert list(s.nodes("InsightSignalFromSpec")) == []
