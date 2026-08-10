"""Tests for predictive insight-seeking — substrate generates + ranks
candidate perturbations.

The substrate identifies hot nodes (high local frustration), sweeps
h-perturbations on each via what-if relaxation, and returns ranked
predictions of ΔE."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.insight_seeking import (
    DEFAULT_H_PERTURBATIONS,
    HOT_NODE_FRUSTRATION_MIN,
    apply_top_insight_candidate,
    find_hot_nodes,
    predict_perturbation_impact,
    seek_insights,
)
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


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


def _build_morning_network(s):
    """Pre-insight morning network — same as
    demos/cognitive_phenomena.py experiment 4."""
    mt = s.add_node("Microtheory", {"name": "morning", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})
    nodes = {}
    setups = [
        ("axiom_0",       +1.5),
        ("frame_rel",     +0.8),
        ("frame_privil",  -0.5),
        ("ground_bin",    +1.2),
        ("ground_vec",    -2.0),
    ]
    for name, h in setups:
        nid = s.add_node("Concept", {"name": name,
                                     "external_field": float(h)})
        s.add_edge(mt, "has_concept", nid, {})
        nodes[name] = nid
    couplings = [
        ("axiom_0",      "frame_rel",     +1.0),
        ("axiom_0",      "frame_privil",  -1.0),
        ("frame_privil", "ground_bin",    +0.8),
        ("frame_privil", "ground_vec",    -0.8),
        ("frame_rel",    "ground_vec",    +0.7),
        ("ground_bin",   "ground_vec",    -0.6),
    ]
    for a, b, w in couplings:
        s.add_edge(nodes[a], "causal_influence",
                   nodes[b], {"weight": float(w)})
    return mt, nodes


# --- node_local_frustration / find_hot_nodes -------------------------------

def test_node_local_frustration_zero_for_satisfied():
    """A node with all couplings satisfied has 0 local frustration."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    a = s.add_node("Concept", {"state": +1.0, "external_field": 1.0})
    b = s.add_node("Concept", {"state": +1.0, "external_field": 1.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 1.0})
    s.mt_relax_to_marginal(mt)
    assert s.node_local_frustration(mt, a) == pytest.approx(0.0, abs=0.01)


def test_node_local_frustration_high_for_unsatisfied():
    """A node forced against a strong coupling has high local frustration."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 5.0})
    a = s.add_node("Concept", {"state": +1.0, "external_field": 5.0})
    b = s.add_node("Concept", {"state": -1.0, "external_field": -5.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    # Strong positive coupling wants same sign; fields force opposite.
    s.add_edge(a, "causal_influence", b, {"weight": 1.0})
    s.mt_relax_to_marginal(mt)
    # The coupling is unsatisfied (σ_a σ_b ≈ -1, J = +1 → -J σσ ≈ +1
    # actual; ideal -|J| = -1; difference ≈ 2).
    assert s.node_local_frustration(mt, a) > 1.0


def test_find_hot_nodes_morning_network():
    """In the pre-insight morning state, frame_privil (the node sitting
    at σ≈+0.2, half-acknowledged inconsistency) should be a top hot
    node."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)
    s.mt_relax_to_marginal(mt)
    hot = find_hot_nodes(s, mt, top_k=3)
    hot_names = {row["name"] for row in hot}
    # frame_privil is the localised dissonance — should show up.
    assert "frame_privil" in hot_names


# --- predict_perturbation_impact -------------------------------------------

def test_predict_perturbation_does_not_modify_graph():
    """What-if predictions must not change actual h or state attrs."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)
    s.mt_relax_to_marginal(mt)
    h_before = s.node(nodes["ground_vec"])["attrs"]["external_field"]
    sigma_before = s.node(nodes["ground_vec"])["attrs"]["state"]
    predict_perturbation_impact(s, mt, nodes["ground_vec"], new_h=+1.0)
    h_after = s.node(nodes["ground_vec"])["attrs"]["external_field"]
    sigma_after = s.node(nodes["ground_vec"])["attrs"]["state"]
    assert h_after == h_before
    assert sigma_after == sigma_before


def test_predict_perturbation_returns_predicted_marginal():
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)
    s.mt_relax_to_marginal(mt)
    result = predict_perturbation_impact(
        s, mt, nodes["ground_vec"], new_h=+0.5)
    assert "predicted_marginal" in result
    assert "predicted_energy" in result
    assert "flipped_nodes" in result
    # ground_vec should flip from negative to positive under +h.
    pred_marg = result["predicted_marginal"]
    assert pred_marg[nodes["ground_vec"].value] > 0


# --- seek_insights ---------------------------------------------------------

def test_seek_insights_finds_lower_energy_basin():
    """On the pre-insight morning network, seek_insights should find
    SOME perturbation that drops energy. The substrate's predictor
    explores the basin landscape without respecting node-level
    identity protection (that's a later capability) — so it may
    propose a basin that the user's frozen Axiom 0 would reject.
    What we check here is that it correctly identifies multiple
    basins exist, and ranks them by mechanical depth.
    """
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)
    predictions = seek_insights(s, mt, top_k_hot=5,
                                h_perturbations=(+0.5, +1.0, +2.0, +3.0))
    assert len(predictions) > 0
    top = predictions[0]
    # The top recommendation should drop energy substantially.
    assert top["predicted_delta_E"] < -0.5
    # The morning's actual resolution (positive perturbation on
    # ground_vec) should be among the candidates the predictor
    # considered, even if not top — the substrate sees the basin.
    ground_vec_positive_predictions = [
        p for p in predictions
        if p["name"] == "ground_vec" and p["delta_h"] > 0
    ]
    assert ground_vec_positive_predictions, (
        f"ground_vec positive perturbation should appear in candidates; "
        f"got: {[(p['name'], p['delta_h']) for p in predictions[:8]]}")
    # And that basin should also drop energy (i.e., the user's chosen
    # basin is a valid resolution, even if it's not the deepest one
    # the substrate found).
    best_ground_vec = min(ground_vec_positive_predictions,
                          key=lambda p: p["predicted_delta_E"])
    assert best_ground_vec["predicted_delta_E"] < 0


def test_seek_insights_empty_when_not_frustrated():
    """A coherent network has no hot nodes → no predictions."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.5,
                                    "update_policy": ADAPTIVE})
    a = s.add_node("Concept", {"external_field": 1.0})
    b = s.add_node("Concept", {"external_field": 1.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "causal_influence", b, {"weight": 0.5})
    predictions = seek_insights(s, mt)
    assert predictions == []


# --- apply_top_insight_candidate -------------------------------------------

def test_apply_top_candidate_writes_new_h():
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)
    predictions = seek_insights(s, mt, top_k_hot=5)
    applied = apply_top_insight_candidate(s, mt, predictions)
    assert applied is not None
    # Look up which concept was modified + verify h actually changed.
    for c in s.neighbours(mt, "has_concept"):
        if c.value == applied["concept_id"]:
            current_h = s.node(c)["attrs"]["external_field"]
            assert current_h == applied["new_h"]
            break
    else:
        pytest.fail("applied concept not found in Mt's has_concept")


def test_apply_top_candidate_returns_none_when_no_improvement():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 1.5,
                                    "update_policy": ADAPTIVE})
    # Single happy node.
    n = s.add_node("Concept", {"external_field": 1.0})
    s.add_edge(mt, "has_concept", n, {})
    predictions = seek_insights(s, mt)
    result = apply_top_insight_candidate(s, mt, predictions)
    assert result is None


# --- end-to-end: seek + apply + loop detects insight ----------------------

def test_seek_apply_drops_frustration():
    """The substrate's predictive seek+apply reliably drops frustration
    — the signal insight detection actually uses. The predictor now
    ranks by predicted ΔF and the top candidate consistently picks a
    basin where frustration drops substantially."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)

    step0 = self_improvement_step(s)
    f_before = step0[mt.value]["post_audit"]["frustration"]

    predictions = seek_insights(s, mt, top_k_hot=5,
                                h_perturbations=(+1.0, +2.0, +3.0))
    applied = apply_top_insight_candidate(s, mt, predictions)
    assert applied is not None
    # Top recommendation predicts substantial frustration drop.
    assert applied["predicted_delta_F"] < -1.0

    step1 = self_improvement_step(s)
    f_after = step1[mt.value]["post_audit"]["frustration"]

    # The substrate's prediction was directionally correct.
    assert f_after < f_before, (
        f"applied={applied['name']} new_h={applied['new_h']:.2f} "
        f"predicted ΔF={applied['predicted_delta_F']:+.3f} "
        f"actual F before={f_before:.2f} after={f_after:.2f}")


def test_seek_apply_with_morning_resolution_triggers_insight():
    """When the substrate APPLIES the perturbation that matches the
    user's actual morning insight (positive h on ground_vec, since
    Axiom 0 is foundational and shouldn't be violated), the next step
    flags a full insight event. This is the basin that respects
    identity-preservation."""
    s = _fresh_substrate()
    mt, nodes = _build_morning_network(s)

    step0 = self_improvement_step(s)
    f_before = step0[mt.value]["post_audit"]["frustration"]

    # Among the predictions, find the ground_vec positive perturbation
    # — the substrate's mechanical foresight DOES see this basin even
    # if it ranks a different one higher.
    predictions = seek_insights(s, mt, top_k_hot=5,
                                h_perturbations=(+1.0, +2.0, +3.0))
    morning_basin = [
        p for p in predictions
        if p["name"] == "ground_vec" and p["delta_h"] > 0
    ]
    assert morning_basin
    chosen = min(morning_basin, key=lambda p: p["predicted_delta_E"])

    # Apply this specific basin (the one that preserves Axiom 0).
    for c in s.neighbours(mt, "has_concept"):
        if c.value == chosen["concept_id"]:
            s.set_attr(c, "external_field", float(chosen["new_h"]))
            break

    step1 = self_improvement_step(s)
    insight = step1[mt.value]["insight"]
    f_after = step1[mt.value]["post_audit"]["frustration"]
    assert insight is not None, (
        f"chosen new_h={chosen['new_h']:.2f} "
        f"predicted ΔE={chosen['predicted_delta_E']:+.3f}; "
        f"actual F before={f_before:.2f} after={f_after:.2f}")
