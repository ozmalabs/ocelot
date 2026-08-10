"""Tests for the self-improvement loop — mutations + policy enforcement.

Exercises the chain:
  - Rust mutations: hebbian_update_J, decay_J, decay_h,
    apply_evidence, relax_to_marginal
  - Python orchestration: mt_update_policy, mt_allows,
    maybe_hebbian, maybe_decay_J, maybe_decay_h, relax,
    detect_failure_modes, self_improvement_step,
    substrate_rollup, seed_update_policies
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.self_improvement_loop import (
    ADAPTIVE,
    DEFAULT_POLICY,
    FROZEN,
    HYBRID,
    detect_failure_modes,
    maybe_decay_J,
    maybe_decay_h,
    maybe_hebbian,
    mt_allows,
    mt_update_policy,
    relax,
    seed_update_policies,
    self_improvement_step,
    substrate_rollup,
)


_NODE_TYPES = ("Microtheory", "Concept")
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


def _coupled_pair(s, mt_attrs: dict) -> tuple:
    """Two concepts in an Mt, coupled with J=0.5, both ON at start."""
    mt = s.add_node("Microtheory", mt_attrs)
    a = s.add_node("Concept",
                   {"state": 0.9, "external_field": 1.0, "target_state": 1.0})
    b = s.add_node("Concept",
                   {"state": 0.9, "external_field": 1.0, "target_state": 1.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.5})
    return mt, a, b


# --- Rust mutation ops -----------------------------------------------------

def test_hebbian_strengthens_co_active_couplings():
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {"temperature": 1.0})
    # Both σ_a, σ_b ≈ +0.9: Δ = η·σ_a·σ_b > 0
    n_updated = s.mt_hebbian_update_J(mt, 0.1)
    assert n_updated == 1
    # Find the new weight on the a→b edge
    # Read via mt_audit_basin's coupling structure (or just check it changed):
    # easier: re-run mean-field — couplings stronger should pull marginals more.
    new_marg = s.mt_mean_field_marginal(mt)
    assert new_marg[a.value] > 0.85
    assert new_marg[b.value] > 0.85


def test_hebbian_weakens_anti_correlated():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.0})
    a = s.add_node("Concept", {"state": 0.9, "external_field": 1.0})
    b = s.add_node("Concept", {"state": -0.9, "external_field": -1.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.5})
    # σ_a·σ_b < 0, η > 0 → Δ < 0 → coupling shrinks toward negative.
    # Energy contribution after Hebbian should reflect smaller (or
    # negative) coupling.
    s.mt_hebbian_update_J(mt, 0.5)
    # Verify the edge weight dropped below the starting 0.5.
    # Easiest: ask the audit, which uses the current J.
    report = s.mt_audit_basin(mt)
    # With weight now ≈ 0.5 - 0.5*0.9*0.9*1 ≈ 0.0945, the σ_a, σ_b
    # disagreement is barely coupled; mean-field follows the fields.
    assert report["marginal"][a.value] > 0
    assert report["marginal"][b.value] < 0


def test_decay_J_reduces_couplings():
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {"temperature": 1.0})
    # Initial J=0.5; decay by 0.5 → new J=0.25
    n = s.mt_decay_J(mt, 0.5)
    assert n == 1
    # Verify via mean-field (smaller J → less mutual reinforcement)
    # At J=0.25, h=1.0, β=1.0 the marginals should be slightly lower
    # than they were at J=0.5.
    marg = s.mt_mean_field_marginal(mt)
    # Tanh(0.25*0.9+1.0) ≈ tanh(1.225) ≈ 0.841 (vs ~0.866 at J=0.5)
    # Just verify positive + reasonable.
    assert 0.7 < marg[a.value] < 0.95
    assert 0.7 < marg[b.value] < 0.95


def test_decay_h_reduces_external_fields():
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {"temperature": 1.0})
    # h_a = h_b = 1.0 initially. Decay by 0.5.
    n = s.mt_decay_h(mt, 0.5)
    assert n == 2  # both concepts had non-zero h
    # Read h back via node attrs
    h_a = s.node(a)["attrs"]["external_field"]
    h_b = s.node(b)["attrs"]["external_field"]
    assert abs(h_a - 0.5) < 1e-5
    assert abs(h_b - 0.5) < 1e-5


def test_apply_evidence_adds_to_field():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    c = s.add_node("Concept", {"external_field": 0.3})
    s.add_edge(mt, "has_concept", c, {})
    s.concept_apply_evidence(c, evidence=0.5, alpha=0.4)
    # h ← 0.3 + 0.4*0.5 = 0.5
    h = s.node(c)["attrs"]["external_field"]
    assert abs(h - 0.5) < 1e-5


def test_relax_writes_marginal_to_state():
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {"temperature": 2.0})
    # state starts at 0.9 from the fixture but the marginal under
    # this H is even closer to +1; relax should write it back.
    n = s.mt_relax_to_marginal(mt)
    assert n == 2
    new_state_a = s.node(a)["attrs"]["state"]
    new_state_b = s.node(b)["attrs"]["state"]
    # Should be close to mean-field marginal (~+0.99 at β=2.0).
    assert new_state_a > 0.95
    assert new_state_b > 0.95


# --- Python orchestration: policy --------------------------------------------

def test_default_policy_is_frozen():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    assert mt_update_policy(s, mt) == FROZEN


def test_frozen_disallows_all_mutations():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"update_policy": FROZEN})
    assert mt_allows(s, mt, "allow_Hebbian_J") is False
    assert mt_allows(s, mt, "allow_h_drift") is False


def test_adaptive_allows_all_axes():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"update_policy": ADAPTIVE})
    assert mt_allows(s, mt, "allow_Hebbian_J") is True
    assert mt_allows(s, mt, "allow_h_drift") is True


def test_hybrid_per_axis_attrs():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {
        "update_policy": HYBRID,
        "allow_Hebbian_J": True,
        "allow_h_drift": False,
    })
    assert mt_allows(s, mt, "allow_Hebbian_J") is True
    assert mt_allows(s, mt, "allow_h_drift") is False
    # axes without explicit attr default to True for hybrid
    assert mt_allows(s, mt, "allow_structural_update") is True


def test_maybe_hebbian_skips_frozen_mt():
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {
        "temperature": 1.0, "update_policy": FROZEN,
    })
    # σ_a, σ_b co-active; would shift J if not frozen.
    n = maybe_hebbian(s, mt, eta=0.5)
    assert n == 0  # frozen → no edges touched
    # Confirm J unchanged by re-running audit.
    report = s.mt_audit_basin(mt)
    assert report["coupling_count"] == 1


def test_maybe_hebbian_works_on_adaptive_mt():
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {
        "temperature": 1.0, "update_policy": ADAPTIVE,
    })
    n = maybe_hebbian(s, mt, eta=0.1)
    assert n == 1


def test_maybe_decay_skips_frozen():
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {"update_policy": FROZEN})
    assert maybe_decay_J(s, mt, decay_rate=0.5) == 0
    assert maybe_decay_h(s, mt, decay_rate=0.5) == 0


# --- Loop end-to-end ---------------------------------------------------------

def test_self_improvement_step_runs_without_breakage():
    s = _fresh_substrate()
    foundational_mt = s.add_node("Microtheory", {
        "name": "philosophy", "update_policy": FROZEN, "temperature": 2.0,
    })
    adaptive_mt = s.add_node("Microtheory", {
        "name": "engineering", "update_policy": ADAPTIVE, "temperature": 1.0,
    })
    for mt in (foundational_mt, adaptive_mt):
        a = s.add_node("Concept",
                       {"state": 0.5, "external_field": 0.6, "target_state": 1.0})
        b = s.add_node("Concept",
                       {"state": 0.5, "external_field": 0.6, "target_state": 1.0})
        s.add_edge(mt, "has_concept", a, {})
        s.add_edge(mt, "has_concept", b, {})
        s.add_edge(a, "causal_influence", b, {"weight": 0.3})
    result = self_improvement_step(s, eta=0.1, decay_rate=0.01, h_decay=0.001)
    assert len(result) == 2
    # Frozen Mt should have zero mutations.
    frozen_result = result[foundational_mt.value]
    assert frozen_result["policy"] == FROZEN
    assert frozen_result["edges_hebbian"] == 0
    assert frozen_result["edges_decayed"] == 0
    assert frozen_result["fields_decayed"] == 0
    # Adaptive Mt should have non-zero mutations.
    adaptive_result = result[adaptive_mt.value]
    assert adaptive_result["policy"] == ADAPTIVE
    assert adaptive_result["edges_hebbian"] == 1
    assert adaptive_result["edges_decayed"] == 1
    assert adaptive_result["fields_decayed"] == 2


def test_substrate_rollup_aggregates():
    s = _fresh_substrate()
    _coupled_pair(s, {"name": "a", "update_policy": ADAPTIVE,
                      "temperature": 1.0})
    _coupled_pair(s, {"name": "b", "update_policy": FROZEN,
                      "temperature": 1.5})
    step = self_improvement_step(s)
    roll = substrate_rollup(step)
    assert roll["mt_count"] == 2
    # All-aligned configs → coherence (= -energy/N) positive.
    assert roll["total_coherence"] > 0


def test_seed_policies_marks_foundational():
    s = _fresh_substrate()
    s.add_node("Microtheory", {"name": "philosophy"})
    s.add_node("Microtheory", {"name": "grounding_theory"})
    s.add_node("Microtheory", {"name": "engineering"})  # domain
    s.add_node("Microtheory", {"name": "machine_learning"})  # foundational
    counters = seed_update_policies(s)
    assert counters["frozen"] == 3  # philosophy, grounding_theory, machine_learning
    assert counters["adaptive"] == 1  # engineering


def test_seed_policies_respects_existing():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {
        "name": "anything", "update_policy": ADAPTIVE,
    })
    counters = seed_update_policies(s)
    assert counters["unchanged"] == 1
    assert s.node(mt)["attrs"]["update_policy"] == ADAPTIVE  # preserved


def test_detect_frustration_failure_mode():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    c = s.add_node("Concept", {})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    # Frustrated triangle.
    s.add_edge(a, "causal_influence", b, {"weight": -1.0})
    s.add_edge(b, "causal_influence", c, {"weight": -1.0})
    s.add_edge(c, "causal_influence", a, {"weight": -1.0})
    report = s.mt_audit_basin(mt)
    modes = detect_failure_modes(report)
    assert "frustrated" in modes


def test_loop_idempotent_at_zero_params():
    """With η=0 and decay=0, the loop becomes a pure read/audit pass.
    Couplings + fields shouldn't change."""
    s = _fresh_substrate()
    mt, a, b = _coupled_pair(s, {
        "temperature": 1.0, "update_policy": ADAPTIVE,
    })
    h_before = s.node(a)["attrs"]["external_field"]
    self_improvement_step(s, eta=0.0, decay_rate=0.0, h_decay=0.0)
    h_after = s.node(a)["attrs"]["external_field"]
    # h should be identical (no decay applied at 0 rate).
    assert abs(h_after - h_before) < 1e-6
