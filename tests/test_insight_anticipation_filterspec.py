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


def _build_morning_network(s):
    mt = s.add_node("Microtheory", {"name": "morning", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    axiom = s.add_node("Concept", {"external_field": +1.5})
    frame_rel = s.add_node("Concept", {"external_field": +0.8})
    frame_priv = s.add_node("Concept", {"external_field": -0.5})
    g_bin = s.add_node("Concept", {"external_field": +1.2})
    g_vec = s.add_node("Concept", {"external_field": -2.0})
    for n in (axiom, frame_rel, frame_priv, g_bin, g_vec):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(axiom, "causal_influence", frame_rel, {"weight": +1.0})
    s.add_edge(axiom, "causal_influence", frame_priv, {"weight": -1.0})
    s.add_edge(frame_priv, "causal_influence", g_bin, {"weight": +0.8})
    s.add_edge(frame_priv, "causal_influence", g_vec, {"weight": -0.8})
    s.add_edge(frame_rel, "causal_influence", g_vec, {"weight": +0.7})
    s.add_edge(g_bin, "causal_influence", g_vec, {"weight": -0.6})
    return mt, g_vec


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

def test_insight_signal_fires_on_morning_resolution():
    """Replicate morning's basin transition; spec should detect ΔF drop."""
    s = _fresh_substrate()
    install_insight_filter(s)
    mt, g_vec = _build_morning_network(s)
    self_improvement_step(s)
    # The moment.
    s.set_attr(g_vec, "external_field", 0.3)
    self_improvement_step(s)
    signals = list(s.nodes("InsightSignalFromSpec"))
    assert len(signals) >= 1


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
