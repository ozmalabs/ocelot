"""End-to-end tests for the Rust can_ops bindings on the substrate.

Exercises the chain Concept (state, external_field, target_state) +
causal_influence(weight) + Microtheory(temperature) →
mt_mean_field_marginal → mt_energy → mt_target → mt_distance_to_target
→ mt_audit_basin.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in ("Microtheory", "Concept"):
        for tgt_t in ("Microtheory", "Concept"):
            for et in ("has_concept", "causal_influence"):
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


def _build_small_mt(s, temperature=1.5):
    mt = s.add_node("Microtheory", {"name": "tiny", "temperature": temperature})
    a = s.add_node("Concept",
                   {"name": "A", "external_field": 1.0, "target_state": 1.0})
    b = s.add_node("Concept",
                   {"name": "B", "external_field": 0.5, "target_state": 1.0})
    c = s.add_node("Concept",
                   {"name": "C", "external_field": -0.8, "target_state": -1.0})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.8})
    s.add_edge(a, "causal_influence", c, {"weight": -0.6})
    return mt, a, b, c


def test_marginal_aligned_with_field_when_uncoupled():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m", "temperature": 2.0})
    n = s.add_node("Concept", {"external_field": 1.5})
    s.add_edge(mt, "has_concept", n, {})
    marg = s.mt_mean_field_marginal(mt)
    # σ = tanh(β h) = tanh(2.0 * 1.5) = tanh(3.0) ≈ 0.995
    assert abs(marg[n.value] - 0.995) < 0.01


def test_marginal_resolves_with_couplings():
    s = _fresh_substrate()
    mt, a, b, c = _build_small_mt(s)
    marg = s.mt_mean_field_marginal(mt)
    # A strongly +1 (positive field, reinforced via B)
    assert marg[a.value] > 0.9
    # B follows A (positive field + positive coupling)
    assert marg[b.value] > 0.5
    # C goes -1 (own negative field + anti-ferromagnetic coupling to A)
    assert marg[c.value] < -0.5


def test_energy_negative_at_resolved_basin():
    s = _fresh_substrate()
    mt, _, _, _ = _build_small_mt(s)
    marg = s.mt_mean_field_marginal(mt)
    energy = s.mt_energy(mt, marg)
    # Couplings + fields all aligned in this small case → deep negative.
    assert energy < -1.0


def test_target_returns_committed_states():
    s = _fresh_substrate()
    mt, a, b, c = _build_small_mt(s)
    target = s.mt_target(mt)
    assert target[a.value] == 1.0
    assert target[b.value] == 1.0
    assert target[c.value] == -1.0


def test_target_defaults_to_plus_one_when_unset():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    n = s.add_node("Concept", {})  # no target_state attr
    s.add_edge(mt, "has_concept", n, {})
    target = s.mt_target(mt)
    assert target[n.value] == 1.0


def test_distance_small_when_marginal_matches_target():
    s = _fresh_substrate()
    mt, _, _, _ = _build_small_mt(s, temperature=2.5)
    dist = s.mt_distance_to_target(mt)
    # All three concepts close to their targets at high enough β.
    assert dist["magnitude"] < 0.1
    assert dist["max_dev_node"] is not None


def test_distance_large_when_field_opposes_target():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    # Mt's target says +1, but field strongly pushes -1.
    n = s.add_node("Concept", {"external_field": -2.0, "target_state": 1.0})
    s.add_edge(mt, "has_concept", n, {})
    dist = s.mt_distance_to_target(mt)
    # Marginal goes to ~-0.999, target is +1 → distance ~ 2.0.
    assert dist["magnitude"] > 1.5


def test_audit_basin_reports_topology():
    s = _fresh_substrate()
    mt, _, _, _ = _build_small_mt(s)
    report = s.mt_audit_basin(mt)
    assert report["concept_count"] == 3
    assert report["coupling_count"] == 2
    assert report["coverage"] == 3
    # Aligned case: low frustration.
    assert report["frustration"] < 0.1
    assert report["energy"] < 0
    assert len(report["marginal"]) == 3


def test_audit_counts_cycle_couplings():
    """A directed triangle has 3 distinct undirected couplings even
    though the i.0 < j.0 ordering on out-edges only catches 2 of them.
    The audit must walk in-edges too + dedupe via canonical (min, max)
    ordering."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.0})
    nodes = [s.add_node("Concept", {}) for _ in range(3)]
    for n in nodes:
        s.add_edge(mt, "has_concept", n, {})
    # Triangle: a->b->c->a (one direction each; cycle).
    s.add_edge(nodes[0], "causal_influence", nodes[1], {"weight": 1.0})
    s.add_edge(nodes[1], "causal_influence", nodes[2], {"weight": 1.0})
    s.add_edge(nodes[2], "causal_influence", nodes[0], {"weight": 1.0})
    report = s.mt_audit_basin(mt)
    assert report["coupling_count"] == 3


def test_audit_basin_high_frustration_with_competing_couplings():
    """A triangle with all negative couplings is frustrated — no
    assignment satisfies all three."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    c = s.add_node("Concept", {})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    # All-negative triangle.
    s.add_edge(a, "causal_influence", b, {"weight": -1.0})
    s.add_edge(b, "causal_influence", c, {"weight": -1.0})
    s.add_edge(c, "causal_influence", a, {"weight": -1.0})
    report = s.mt_audit_basin(mt)
    # No assignment can satisfy all three anti-ferro couplings.
    # Frustration index > 0 (at least one coupling has actual > ideal).
    assert report["frustration"] > 0.5


def test_empty_mt_returns_empty_marginal():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    assert s.mt_mean_field_marginal(mt) == {}
    assert s.mt_audit_basin(mt)["concept_count"] == 0


def test_higher_temperature_diffuses_state():
    """β → 0 (T → ∞) drives the marginal toward 0 — no commitment."""
    s = _fresh_substrate()
    mt_cold = s.add_node("Microtheory", {"temperature": 0.05})
    mt_hot = s.add_node("Microtheory", {"temperature": 5.0})
    a_cold = s.add_node("Concept", {"external_field": 0.5})
    a_hot = s.add_node("Concept", {"external_field": 0.5})
    s.add_edge(mt_cold, "has_concept", a_cold, {})
    s.add_edge(mt_hot, "has_concept", a_hot, {})
    marg_cold = s.mt_mean_field_marginal(mt_cold)
    marg_hot = s.mt_mean_field_marginal(mt_hot)
    # tanh(0.05 * 0.5) ≈ 0.025 (diffuse) vs tanh(5 * 0.5) ≈ 0.987 (sharp)
    assert abs(marg_cold[a_cold.value]) < 0.1
    assert abs(marg_hot[a_hot.value]) > 0.9
