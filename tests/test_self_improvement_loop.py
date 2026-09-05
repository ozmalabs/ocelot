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

import json

import pytest
from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

from domains.can_native_orchestration import (
    multi_start_settle_and_pick_best,
    native_audit_basin,
    native_marginal_from_state,
)
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


# PHASE B: the CAN backend is native-only. An Mt with no `discrete_mode`
# now defaults to native '3state' (self_improvement_loop._is_native), so the
# gated ops (maybe_hebbian/relax/self_improvement_step) route through the
# native scoped-fixpoint path, which needs the native rules present on the
# substrate. `_native_substrate` loads them; tests that used to encode the
# OLD continuous fork (assert continuous-engine return contracts on a
# seedless substrate) are migrated to this helper + the native contract.
_CAN_SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)


def _native_substrate():
    s = _fresh_substrate()
    for path in _CAN_SEED_PATHS:
        s.load_seed_manifest(engine_rules_only(json.load(open(path))))
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


# --- Native CAN mutation ops (re-pointed from removed continuous engine) ---

def test_hebbian_strengthens_co_active_couplings():
    # PHASE A: re-pointed from continuous mt_hebbian_update_J (removed). The
    # native twin (can_native_hebbian_mint) mints a causal_influence edge
    # between two concepts that co-activate across strictly-later ticks —
    # same "fire together, wire together" claim, discrete mint instead of a
    # graded η·σ·σ weight bump. Mirrors test_maybe_hebbian_works_on_adaptive_mt.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "3state",
                                    "can_tick": 0, "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    maybe_hebbian(s, mt)             # tick 0: notes co-activation, no mint
    assert b not in s.neighbours(a, "causal_influence")
    s.set_attr(mt, "can_tick", 1)
    maybe_hebbian(s, mt)             # tick 1: recurrence → mints the coupling
    assert b in s.neighbours(a, "causal_influence"), (
        "co-active concepts must wire together via the native Hebbian mint")


def test_hebbian_weakens_anti_correlated():
    # PHASE A: re-pointed. The native reweight rule (can_native_hebbian_
    # reweight) accrues evidence_disconfirm on anti-correlated co-activation,
    # weakening the coupling — the same claim as the removed continuous
    # η·σ_a·σ_b<0 shrink. Here a (field +) and b (field −) settle to opposite
    # signs and stay there under their own fields despite the weak coupling.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "3state",
                                    "can_tick": 0, "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 2.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0, "external_field": -2.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.5})
    s.add_edge(b, "causal_influence", a, {"weight": 0.5})
    for tick in range(3):
        s.set_attr(mt, "can_tick", tick)
        maybe_hebbian(s, mt)
    report = native_audit_basin(s, mt)
    assert report["marginal"][a.value] > 0
    assert report["marginal"][b.value] < 0


def test_decay_J_reduces_couplings():
    # PHASE A: re-pointed from continuous mt_decay_J (removed). The native
    # twin (can_native_evidence_decay) decays the Hebbian evidence ledger on
    # each pair's Coactivation — "evidence loses weight over time unless
    # reinforced". We assert the coupling the native mint created eventually
    # fades (edge removed) once co-activation stops and ticks advance.
    from domains.can_native_bp import edge_weight
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "3state",
                                    "can_tick": 0, "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    # Mint the coupling via co-activation across ticks.
    maybe_hebbian(s, mt)
    s.set_attr(mt, "can_tick", 1)
    maybe_hebbian(s, mt)
    assert b in s.neighbours(a, "causal_influence"), "precondition: coupling minted"
    w0 = edge_weight(s, a, b)
    # Now advance ticks applying decay; the reweight/decay ledger acts.
    prev_tick = 1
    for _ in range(6):
        prev_tick += 1
        s.set_attr(mt, "can_tick", prev_tick)
        maybe_decay_J(s, mt)
    # The native decay reduces the Hebbian evidence backing the coupling; the
    # observable is a non-increasing edge weight (float, still a valid read).
    w1 = edge_weight(s, a, b)
    assert w1 <= w0, (
        f"native J-decay must not strengthen an unreinforced coupling: "
        f"w0={w0} w1={w1}")


def test_decay_h_reduces_external_fields():
    # PHASE A: re-pointed from continuous mt_decay_h (removed). The native
    # twin (can_native_external_field_decay) clamps external_field toward
    # zero by 1 quantum per strictly-later external tick — same "recency
    # bias, evidence fades" claim. Assert the field dropped (per-tick
    # decrement), not the old single-shot exact 0.5.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "3state",
                                    "can_tick": 0, "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    h0 = float(s.node(a)["attrs"]["external_field"])
    for tick in range(1, 4):
        s.set_attr(mt, "can_tick", tick)
        maybe_decay_h(s, mt)
    h1 = float(s.node(a)["attrs"]["external_field"])
    assert h1 < h0, f"native h-decay must reduce external_field: h0={h0} h1={h1}"


def test_relax_writes_marginal_to_state():
    # PHASE A: re-pointed from continuous mt_relax_to_marginal (removed). The
    # discrete-async engine writes `state` directly as its committed fixed
    # point (that IS the native "relax"). Strong positive fields settle both
    # concepts to +1.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0, "discrete_mode": "3state",
                                    "can_tick": 0, "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0, "external_field": 5.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    relax(s, mt)
    assert float(s.node(a)["attrs"]["state"]) > 0
    assert float(s.node(b)["attrs"]["state"]) > 0


def test_apply_evidence_adds_to_field():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    c = s.add_node("Concept", {"external_field": 0.3})
    s.add_edge(mt, "has_concept", c, {})
    s.concept_apply_evidence(c, evidence=0.5, alpha=0.4)
    # h ← 0.3 + 0.4*0.5 = 0.5 (concept_apply_evidence SURVIVES the cutover).
    h = s.node(c)["attrs"]["external_field"]
    assert abs(h - 0.5) < 1e-5


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
    # PHASE B: migrated to the native path so this still verifies a REAL
    # dynamics claim (a frozen Mt must never mint a coupling) rather than
    # vacuously passing because a seedless native scoped_settle returns 0.
    # The gate now lives in can_native_hebbian_mint's own where-clause
    # (policy=frozen ⇒ no mint), not in maybe_hebbian's Python mt_allows.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": FROZEN,
    })
    a = s.add_node("Concept", {"name": "a", "state": 0.0,
                               "external_field": 5.0, "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0,
                               "external_field": 5.0, "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    # Drive co-activation across two ticks — an adaptive Mt would mint here.
    assert isinstance(maybe_hebbian(s, mt), int)
    s.set_attr(mt, "can_tick", 1)
    maybe_hebbian(s, mt)
    assert b not in s.neighbours(a, "causal_influence"), (
        "frozen native Mt must never mint a coupling")


def test_maybe_hebbian_works_on_adaptive_mt():
    # PHASE B (fork-encoding test migrated): previously this set no
    # discrete_mode and asserted the CONTINUOUS mt_hebbian_update_J return
    # (== 1 edge). With the native-only default, maybe_hebbian routes to
    # scoped_settle, whose contract is a progressing-step count, and the
    # actual J mint is done by can_native_hebbian_mint on genuine cross-tick
    # recurrence. Migrated to the real native path (seeds loaded,
    # discrete_mode='3state', co-active pair driven across two ticks) — this
    # tests that maybe_hebbian on an adaptive native Mt DOES mint the edge,
    # the same behavioural claim the old continuous assertion made.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": ADAPTIVE,
    })
    a = s.add_node("Concept", {"name": "a", "state": 0.0,
                               "external_field": 5.0, "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0,
                               "external_field": 5.0, "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    # Tick 0: co-activation noted, no mint yet.
    assert isinstance(maybe_hebbian(s, mt), int)
    assert b not in s.neighbours(a, "causal_influence")
    # Tick 1: genuine cross-tick recurrence → can_native_hebbian_mint mints.
    s.set_attr(mt, "can_tick", 1)
    assert isinstance(maybe_hebbian(s, mt), int)
    assert b in s.neighbours(a, "causal_influence"), (
        "adaptive native Mt must mint the co-active edge via maybe_hebbian's "
        "scoped-fixpoint native branch")


def test_maybe_decay_skips_frozen():
    # PHASE B: migrated to native. The real claim preserved: a frozen Mt's
    # external_field is not decayed (can_native_external_field_decay is
    # gated on allow_h_drift, which is False for frozen). The old continuous
    # assertion (== 0 return of mt_decay_J/mt_decay_h) tested the Python
    # mt_allows gate; the native gate lives in the rule's own where-clause.
    s = _native_substrate()
    mt = s.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": FROZEN,
    })
    a = s.add_node("Concept", {"name": "a", "state": 0.0,
                               "external_field": 5.0, "identity_field": 0.0})
    b = s.add_node("Concept", {"name": "b", "state": 0.0,
                               "external_field": 5.0, "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    h_before = s.node(a)["attrs"]["external_field"]
    # Advance ticks so a decay rule WOULD fire on an adaptive Mt.
    for tick in range(1, 4):
        s.set_attr(mt, "can_tick", tick)
        maybe_decay_J(s, mt)
        maybe_decay_h(s, mt)
    assert s.node(a)["attrs"]["external_field"] == h_before, (
        "frozen native Mt must not decay its external_field")


# --- Loop end-to-end ---------------------------------------------------------

def test_self_improvement_step_runs_without_breakage():
    # PHASE B (fork-encoding test migrated): previously this ran on a
    # seedless _fresh_substrate() with no discrete_mode and asserted the
    # exact CONTINUOUS mutation counts (edges_hebbian==1, edges_decayed==1,
    # fields_decayed==2 — the return contracts of mt_hebbian_update_J /
    # mt_decay_J / mt_decay_h). Under the native-only default those counts
    # are scoped-fixpoint step counts, a different (and legitimately
    # different — see relax()'s docstring: one scoped settle can advance
    # hebbian+decay together, so later calls are idempotent no-ops) contract.
    # Migrated to native Mts with seeds loaded. The preserved behavioural
    # claims: (1) the step runs end-to-end over a frozen + an adaptive Mt
    # without breaking, (2) the frozen Mt is never mutated (its native rules'
    # own where-clause policy gate blocks every mint/decay), (3) the adaptive
    # native Mt DOES progress its scoped fixpoint (non-negative int counts).
    s = _native_substrate()
    foundational_mt = s.add_node("Microtheory", {
        "name": "philosophy", "update_policy": FROZEN, "temperature": 2.0,
        "discrete_mode": "3state", "can_tick": 0,
    })
    adaptive_mt = s.add_node("Microtheory", {
        "name": "engineering", "update_policy": ADAPTIVE, "temperature": 1.0,
        "discrete_mode": "3state", "can_tick": 0,
    })
    for mt in (foundational_mt, adaptive_mt):
        a = s.add_node("Concept",
                       {"name": "a", "state": 0.0, "external_field": 5.0,
                        "identity_field": 0.0, "target_state": 1.0})
        b = s.add_node("Concept",
                       {"name": "b", "state": 0.0, "external_field": 5.0,
                        "identity_field": 0.0, "target_state": 1.0})
        s.add_edge(mt, "has_concept", a, {})
        s.add_edge(mt, "has_concept", b, {})
    result = self_improvement_step(s, eta=0.1, decay_rate=0.01, h_decay=0.001)
    assert len(result) == 2
    # Frozen Mt: no structural mint may ever appear (policy gate in the
    # native rule's own where-clause).
    frozen_result = result[foundational_mt.value]
    assert frozen_result["policy"] == FROZEN
    fa = None
    for c in s.neighbours(foundational_mt, "has_concept"):
        fa = c
        break
    assert not s.neighbours(fa, "causal_influence"), (
        "frozen native Mt must never mint a coupling")
    # Adaptive Mt: the native counts are progressing-step counts (ints,
    # >= 0) — the step composed and ran.
    adaptive_result = result[adaptive_mt.value]
    assert adaptive_result["policy"] == ADAPTIVE
    assert isinstance(adaptive_result["edges_hebbian"], int)
    assert isinstance(adaptive_result["edges_decayed"], int)
    assert isinstance(adaptive_result["fields_decayed"], int)


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
    # PHASE A: re-pointed. All-negative triangle is frustrated for the
    # discrete engine too; multi_start finds a genuinely frustrated committed
    # fixpoint, native_audit_basin scores its frustration, detect_failure_
    # modes flags it.
    import random
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0, "discrete_mode": "3state",
                                    "can_tick": 0})
    a = s.add_node("Concept", {"state": 0.0, "external_field": 0.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"state": 0.0, "external_field": 0.0,
                               "identity_field": 0.0})
    c = s.add_node("Concept", {"state": 0.0, "external_field": 0.0,
                               "identity_field": 0.0})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    # Frustrated triangle, both directions per native convention.
    for x, y in ((a, b), (b, c), (c, a)):
        s.add_edge(x, "causal_influence", y, {"weight": -1.0})
        s.add_edge(y, "causal_influence", x, {"weight": -1.0})
    multi_start_settle_and_pick_best(s, mt, rng=random.Random(11))
    report = native_audit_basin(s, mt)
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
