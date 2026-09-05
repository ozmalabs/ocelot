"""End-to-end tests for the Rust can_ops bindings on the substrate.

Exercises the chain Concept (state, external_field, target_state) +
causal_influence(weight) + Microtheory(temperature) via the NATIVE
discrete-async engine: scoped_settle → native_marginal_from_state →
mt_energy → mt_target → mt_distance_to_target → native_audit_basin.

PHASE A (native-backend cutover): the continuous Ising engine
(mt_mean_field_marginal / mt_audit_basin) was removed. Tests that asserted
its continuous NUMERICS directly (σ=tanh(βh), the temperature-diffusion
curve, the coupling_count topology field native_audit_basin omits) are
removed with justification. Tests of features that survive (basin
resolution direction, energy sign, distance-to-target, frustration) are
re-pointed to the native path — committed discrete state (±1/0) settled by
the native rules, scored by the surviving representation-agnostic
mt_energy / mt_frustration_given_state. couplings are added in BOTH
directions (the native local-field reads a node's out-edges only, unlike
the removed mean-field's symmetric in+out walk).
"""
from __future__ import annotations

import json

import pytest
from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

from domains.can_native_orchestration import (
    multi_start_settle_and_pick_best,
    native_audit_basin,
    native_marginal_from_state,
    scoped_settle,
)

_CAN_SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)


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


def _native_substrate():
    """Seed-loaded substrate so the discrete-async native rules
    (can_native_update_3state/_2state + decay/identity) fire under
    scoped_settle."""
    s = _fresh_substrate()
    for path in _CAN_SEED_PATHS:
        s.load_seed_manifest(engine_rules_only(json.load(open(path))))
    return s


def _build_small_mt(s, temperature=1.5):
    """Native 3-state Mt. Couplings added in BOTH directions (native
    convention). Concepts start at state 0.0; scoped_settle settles them."""
    mt = s.add_node("Microtheory", {"name": "tiny", "temperature": temperature,
                                    "discrete_mode": "3state", "can_tick": 0})
    a = s.add_node("Concept",
                   {"name": "A", "state": 0.0, "external_field": 1.0,
                    "identity_field": 0.0, "target_state": 1.0})
    b = s.add_node("Concept",
                   {"name": "B", "state": 0.0, "external_field": 0.5,
                    "identity_field": 0.0, "target_state": 1.0})
    c = s.add_node("Concept",
                   {"name": "C", "state": 0.0, "external_field": -0.8,
                    "identity_field": 0.0, "target_state": -1.0})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.8})
    s.add_edge(b, "causal_influence", a, {"weight": 0.8})
    s.add_edge(a, "causal_influence", c, {"weight": -0.6})
    s.add_edge(c, "causal_influence", a, {"weight": -0.6})
    return mt, a, b, c


# PHASE A: test_marginal_aligned_with_field_when_uncoupled was REMOVED — it
# asserted the continuous mean-field identity σ = tanh(β·h) (tanh(3.0) ≈
# 0.995), a numeric property of the removed engine. The discrete 3-state
# rule thresholds to {-1,0,+1}; there is no tanh value to recover.


def test_marginal_resolves_with_couplings():
    s = _native_substrate()
    mt, a, b, c = _build_small_mt(s)
    scoped_settle(s, mt)
    marg = native_marginal_from_state(s, mt)
    # A settles +1 (positive field, reinforced via B).
    assert marg[a.value] > 0
    # B follows A (positive field + positive coupling).
    assert marg[b.value] > 0
    # C settles negative (own negative field + anti-ferro coupling to A).
    assert marg[c.value] < 0


def test_energy_negative_at_resolved_basin():
    s = _native_substrate()
    mt, _, _, _ = _build_small_mt(s)
    scoped_settle(s, mt)
    marg = native_marginal_from_state(s, mt)
    energy = s.mt_energy(mt, marg)
    # Couplings + fields aligned in this small case → negative energy.
    assert energy < 0


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
    s = _native_substrate()
    mt, _, _, _ = _build_small_mt(s, temperature=2.5)
    scoped_settle(s, mt)  # commit state to the fixed point FIRST
    dist = s.mt_distance_to_target(mt)
    # Settled ±1 states meet their ±1 targets → near-zero distance.
    assert dist["magnitude"] < 0.1
    assert dist["max_dev_node"] is not None


def test_distance_large_when_field_opposes_target():
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "discrete_mode": "3state", "can_tick": 0})
    # Mt's target says +1, but field strongly pushes -1.
    n = s.add_node("Concept", {"state": 0.0, "external_field": -2.0,
                               "identity_field": 0.0, "target_state": 1.0})
    s.add_edge(mt, "has_concept", n, {})
    scoped_settle(s, mt)  # settles to -1
    dist = s.mt_distance_to_target(mt)
    # Committed -1, target +1 → distance = 2.0.
    assert dist["magnitude"] > 1.5


def test_audit_basin_reports_topology():
    s = _native_substrate()
    mt, _, _, _ = _build_small_mt(s)
    scoped_settle(s, mt)
    report = native_audit_basin(s, mt)
    assert report["concept_count"] == 3
    # PHASE A: coupling_count assertion DROPPED — native_audit_basin omits
    # it (no consumer reads it).
    assert report["coverage"] == 3
    # Aligned case: low frustration.
    assert report["frustration"] < 0.1
    assert report["energy"] < 0
    assert len(report["marginal"]) == 3


# PHASE A: test_audit_counts_cycle_couplings was REMOVED — its sole
# assertion was report["coupling_count"] == 3, and native_audit_basin
# intentionally omits coupling_count (no live consumer reads it).


def test_audit_basin_high_frustration_with_competing_couplings():
    """A triangle with all negative couplings is frustrated — no
    assignment satisfies all three. (Native: couplings bidirectional;
    multi_start finds a genuinely frustrated committed fixpoint.)"""
    import random
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "discrete_mode": "3state", "can_tick": 0})
    a = s.add_node("Concept", {"state": 0.0, "external_field": 0.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"state": 0.0, "external_field": 0.0,
                               "identity_field": 0.0})
    c = s.add_node("Concept", {"state": 0.0, "external_field": 0.0,
                               "identity_field": 0.0})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    # All-negative triangle, both directions per native convention.
    for x, y in ((a, b), (b, c), (c, a)):
        s.add_edge(x, "causal_influence", y, {"weight": -1.0})
        s.add_edge(y, "causal_influence", x, {"weight": -1.0})
    multi_start_settle_and_pick_best(s, mt, rng=random.Random(7))
    report = native_audit_basin(s, mt)
    # No assignment can satisfy all three anti-ferro couplings → frustrated.
    assert report["frustration"] > 0.5


def test_empty_mt_returns_empty_marginal():
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"discrete_mode": "3state"})
    assert native_marginal_from_state(s, mt) == {}
    assert native_audit_basin(s, mt)["concept_count"] == 0


# PHASE A: test_higher_temperature_diffuses_state was REMOVED — it asserted
# the continuous tanh temperature-diffusion curve (β→0 ⇒ σ→0 graded, vs
# β→∞ ⇒ σ→±1), a numeric property of the removed mean-field engine. The
# discrete 3-state rule thresholds temperature-scaled local field to
# {-1,0,+1} and does not produce a graded 0.025-vs-0.987 curve.
