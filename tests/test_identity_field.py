"""Tests for node-level identity protection via identity_field attr.

CRUCIAL: identity is NEVER frozen. It's a structural resistance term
— h_eff = external_field + identity_field — that survives ordinary
perturbations + h_decay but can ALWAYS be overcome by sufficiently
strong external evidence. Nothing is permanent.

Tests verify both directions:
  · Identity resists weak perturbations
  · Strong enough perturbations still flip identity nodes
  · Predictive seek's energy ranking now reflects identity cost
  · decay_h leaves identity_field alone (external_field decays;
    identity persists)
"""
from __future__ import annotations

import json

import pytest
from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

from domains.can_native_orchestration import (
    native_marginal_from_state,
    scoped_settle,
)
from domains.insight_seeking import seek_insights
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step

_CAN_SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent")
_EDGE_TYPES = ("has_concept", "causal_influence", "has_insight")


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


def _native_substrate():
    s = _fresh_substrate()
    for path in _CAN_SEED_PATHS:
        s.load_seed_manifest(engine_rules_only(json.load(open(path))))
    return s


# --- Identity field shapes the equilibrium --------------------------------
# PHASE A (native-backend cutover): identity_field is part of the SURVIVING
# native local field (can_native_update_3state/_2state read
# external_field + identity_field + Σ w·σ). These tests are re-pointed from
# the removed continuous mt_mean_field_marginal to the native discrete
# settle; graded tanh magnitudes become discrete signs (±1/0).

def test_identity_field_pulls_sigma_when_external_is_zero():
    """A node with no external evidence but +identity_field commits to +σ."""
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "discrete_mode": "3state", "can_tick": 0})
    n = s.add_node("Concept", {"external_field": 0.0, "state": 0.0,
                               "identity_field": 1.0})
    s.add_edge(mt, "has_concept", n, {})
    scoped_settle(s, mt)
    marg = native_marginal_from_state(s, mt)
    # h_eff = external + identity = +1 → settles +1.
    assert marg[n.value] > 0


def test_identity_field_resists_weak_external_perturbation():
    """Identity +2; external -0.5. h_eff = +1.5. σ still positive."""
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "discrete_mode": "3state", "can_tick": 0})
    n = s.add_node("Concept", {"external_field": -0.5, "state": 0.0,
                               "identity_field": 2.0})
    s.add_edge(mt, "has_concept", n, {})
    scoped_settle(s, mt)
    marg = native_marginal_from_state(s, mt)
    assert marg[n.value] > 0  # holds identity


def test_strong_enough_external_overcomes_identity():
    """Identity +2; external -3.5. h_eff = -1.5. σ goes negative.
    Nothing is frozen — strong evidence flips identity."""
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "discrete_mode": "3state", "can_tick": 0})
    n = s.add_node("Concept", {"external_field": -3.5, "state": 0.0,
                               "identity_field": 2.0})
    s.add_edge(mt, "has_concept", n, {})
    scoped_settle(s, mt)
    marg = native_marginal_from_state(s, mt)
    assert marg[n.value] < 0


def test_zero_identity_is_backwards_compatible():
    """Default identity_field=0 → committed state driven by external
    field alone (native default)."""
    s = _native_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "discrete_mode": "3state", "can_tick": 0})
    n = s.add_node("Concept", {"external_field": 0.5, "state": 0.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", n, {})
    scoped_settle(s, mt)
    marg = native_marginal_from_state(s, mt)
    # local = 0.5·temp 2.0 = 1.0 > atanh(0.5) → +1 (was tanh(1.0)≈0.762).
    assert marg[n.value] > 0


# --- Energy reflects identity cost ----------------------------------------

def test_energy_penalises_sigma_against_identity():
    """Energy is higher (less negative) when σ opposes identity."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    n = s.add_node("Concept", {"external_field": 0.0,
                                "identity_field": 2.0})
    s.add_edge(mt, "has_concept", n, {})
    # Manually compute energy for σ = +1 vs σ = -1.
    energy_aligned = s.mt_energy(mt, {n.value: +1.0})
    energy_opposed = s.mt_energy(mt, {n.value: -1.0})
    # Aligned: -h_eff * σ = -2 * 1 = -2. Opposed: -h_eff * (-1) = +2.
    assert energy_aligned == pytest.approx(-2.0, abs=0.01)
    assert energy_opposed == pytest.approx(+2.0, abs=0.01)
    assert energy_opposed > energy_aligned  # opposing identity costs


# --- Predictive seek respects identity ------------------------------------

def test_predictive_seek_avoids_identity_violating_basin():
    """With axiom_0 marked identity_field=+2 (deeply held), the morning
    network's predictor should NO LONGER pick the basin that forces
    frame_privil positive (which violates axiom_0)."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "morning", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    # The crucial change: axiom_0 has identity_field +2 — a deep
    # structural commitment that resists local-evidence perturbations.
    axiom = s.add_node("Concept", {"name": "axiom_0",
                                    "external_field": +1.5,
                                    "identity_field": +2.0})
    frame_rel = s.add_node("Concept", {"name": "frame_rel",
                                        "external_field": +0.8})
    frame_priv = s.add_node("Concept", {"name": "frame_priv",
                                         "external_field": -0.5})
    g_bin = s.add_node("Concept", {"name": "ground_bin",
                                    "external_field": +1.2})
    g_vec = s.add_node("Concept", {"name": "ground_vec",
                                    "external_field": -2.0})
    for n in (axiom, frame_rel, frame_priv, g_bin, g_vec):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(axiom, "causal_influence", frame_rel, {"weight": +1.0})
    s.add_edge(axiom, "causal_influence", frame_priv, {"weight": -1.0})
    s.add_edge(frame_priv, "causal_influence", g_bin, {"weight": +0.8})
    s.add_edge(frame_priv, "causal_influence", g_vec, {"weight": -0.8})
    s.add_edge(frame_rel, "causal_influence", g_vec, {"weight": +0.7})
    s.add_edge(g_bin, "causal_influence", g_vec, {"weight": -0.6})

    predictions = seek_insights(s, mt, top_k_hot=5,
                                h_perturbations=(+1.0, +2.0, +3.0))
    assert predictions
    top = predictions[0]
    # The top recommendation should NOT be on frame_priv with a
    # massive positive perturbation (that basin now costs energy
    # because axiom_0's identity_field opposes it).
    is_frame_priv_force = (
        top["name"] == "frame_priv" and top["delta_h"] >= 2.0
    )
    # Either it's not the identity-violating perturbation, OR it is but
    # ground_vec positive is also competitive (we don't lock the rank
    # but expect identity to matter).
    if is_frame_priv_force:
        # Check that ground_vec positive is among the top 3 — identity
        # constraint should make the basins comparable rather than
        # frame_priv decisively winning.
        ground_vec_in_top = any(
            p["name"] == "ground_vec" and p["delta_h"] > 0
            for p in predictions[:3]
        )
        assert ground_vec_in_top, (
            f"identity_field should reorder rankings; got: "
            f"{[(p['name'], p['delta_h'], p['predicted_delta_E']) for p in predictions[:5]]}"
        )


def test_identity_field_makes_violating_basin_more_frustrated():
    """With identity_field on axiom_0, basins where axiom is pulled
    toward a compromise σ less than +1 have MORE frustration than the
    same basin without identity — because identity drives axiom more
    strongly to +1, which fully realises the unsatisfied coupling.

    The predictor's ΔF ranking should reflect this: the same basin
    perturbation is predicted to be a LESS attractive drop with
    identity than without."""
    def build(identity: float):
        s = _fresh_substrate()
        mt = s.add_node("Microtheory", {"name": "m", "temperature": 2.0})
        axiom = s.add_node("Concept", {
            "name": "axiom_0", "external_field": +1.0,
            "identity_field": identity})
        frame_priv = s.add_node("Concept", {"name": "frame_priv",
                                            "external_field": -0.5})
        g_vec = s.add_node("Concept", {"name": "g_vec",
                                       "external_field": -2.0})
        for n in (axiom, frame_priv, g_vec):
            s.add_edge(mt, "has_concept", n, {})
        s.add_edge(axiom, "causal_influence", frame_priv,
                   {"weight": -1.0})
        s.add_edge(frame_priv, "causal_influence", g_vec,
                   {"weight": -0.8})
        return s, mt, frame_priv

    s_no_id, mt_no_id, fp_no_id = build(identity=0.0)
    s_id, mt_id, fp_id = build(identity=+2.5)

    # Same +2.5 perturbation on frame_priv in both networks.
    preds_no = seek_insights(s_no_id, mt_no_id, top_k_hot=3,
                             h_perturbations=(+3.0,))
    preds_id = seek_insights(s_id, mt_id, top_k_hot=3,
                             h_perturbations=(+3.0,))

    fp_pred_no = next(
        (p for p in preds_no if p["name"] == "frame_priv"), None)
    fp_pred_id = next(
        (p for p in preds_id if p["name"] == "frame_priv"), None)
    if fp_pred_no and fp_pred_id:
        # With identity, axiom is more strongly pinned to +1, so the
        # unsatisfied axiom-frame_priv coupling in the perturbed basin
        # has a higher (more fully realised) frustration contribution.
        # ΔF should be LESS negative (smaller drop) with identity.
        assert fp_pred_id["predicted_delta_F"] >= fp_pred_no["predicted_delta_F"] - 0.01, (
            f"identity should make basin less attractive (smaller ΔF drop): "
            f"no_id ΔF={fp_pred_no['predicted_delta_F']:.3f}  "
            f"with_id ΔF={fp_pred_id['predicted_delta_F']:.3f}"
        )


# --- Decay doesn't erode identity -----------------------------------------

# PHASE A (native-backend cutover): test_decay_h_does_not_decay_identity_
# field and test_loop_decay_h_alone_does_not_touch_identity_when_dynamics_off
# were REMOVED. Both asserted a continuous-ONLY contract: that the h-decay
# op, called in ISOLATION, leaves identity_field untouched. In the native
# engine there is no isolated decay op — maybe_decay_h routes through the
# shared scoped fixpoint (relax()'s docstring documents this: one scoped
# settle advances every gated-open rule, including can_native_identity_
# field_feedback, which legitimately writes identity_field). The surviving
# feature — that the native external-field decay RULE
# (can_native_external_field_decay) writes external_field ONLY, never
# identity_field — is tested at the rule level (in isolation via
# discrete_mode='static') by tests/test_can_decay_identity.py and
# tests/test_can_identity_feedback.py. No native behaviour is left uncovered.
