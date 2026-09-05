"""Predictive insight-seeking — the substrate looks for insights.

When the substrate is frustrated, it identifies which nodes are
contributing most to the frustration (hot nodes), sweeps candidate
h-perturbations on each, and ranks them by predicted ΔF. This is
curiosity made mechanical: the substrate generates its own
hypotheses about what evidence might unlock the basin.

No mutation — what-if relaxations use mt_mean_field_with_h_override
which doesn't touch the graph. The substrate ASKS "what would
happen if?" and gets a numeric answer.

Workflow:
  1. relax + audit current state
  2. find_hot_nodes — identify top-k frustration contributors
  3. for each hot node × candidate h-delta:
       predict new frustration under that perturbation (what-if)
  4. rank predictions by predicted ΔF (most negative = best)
  5. return ranked predictions

The substrate can then choose to apply the top candidate (by
injecting evidence on that node) or record it as a hypothesis
to investigate.
"""
from __future__ import annotations

from typing import Any


# Default sweep — small +/- h perturbations relative to current.
DEFAULT_H_PERTURBATIONS: tuple[float, ...] = (-2.0, -1.0, -0.5, +0.5, +1.0, +2.0)

# Minimum local frustration to consider a node 'hot' enough to test.
HOT_NODE_FRUSTRATION_MIN = 0.05


def find_hot_nodes(
    substrate,
    mt,
    top_k: int = 5,
    min_frustration: float = HOT_NODE_FRUSTRATION_MIN,
) -> list[dict[str, Any]]:
    """Identify Concepts contributing most to current local frustration.

    Assumes the network has been relaxed (state attrs reflect equilibrium).
    Returns a list of {node, local_frustration, current_h, current_sigma}
    sorted descending by local_frustration, capped at top_k. Concepts
    below min_frustration are filtered out.
    """
    concepts = substrate.neighbours(mt, "has_concept")
    rows: list[dict[str, Any]] = []
    from domains.can_native_orchestration import native_node_local_frustration
    for c in concepts:
        local_f = native_node_local_frustration(substrate, mt, c)
        if local_f <= min_frustration:
            continue
        attrs = substrate.node(c)["attrs"]
        rows.append({
            "node": c,
            "node_id": c.value,
            "local_frustration": local_f,
            "current_h": float(attrs.get("external_field", 0.0)),
            "current_sigma": float(attrs.get("state", 0.0)),
            "name": attrs.get("name", f"#{c.value}"),
        })
    rows.sort(key=lambda r: -r["local_frustration"])
    return rows[:top_k]


def predict_perturbation_impact(
    substrate,
    mt,
    concept,
    new_h: float,
) -> dict[str, Any]:
    """What would happen if this node's h were set to new_h?

    Returns a dict with the predicted marginal + predicted frustration
    + per-node deviation from current state. The graph is NOT modified.

    PHASE A (native-backend cutover): native-only. The prediction runs via
    domains/can_counterfactual.py's predict_ripple (the discrete-async
    non-mutating twin) — the continuous mean-field path
    (mt_mean_field_marginal/mt_mean_field_with_h_override) is removed. An
    Mt with no explicit discrete_mode defaults to '3state'. mt_energy /
    mt_frustration_given_state are representation-agnostic, closed-form
    scorers over predict_ripple's own predicted state (no field-correction
    hack needed), and are KEPT.
    """
    discrete_mode = substrate.node(mt)["attrs"].get("discrete_mode")
    mode = discrete_mode if discrete_mode in ("2state", "3state") else "3state"
    from domains.can_counterfactual import predict_ripple

    old_h = float(substrate.node(concept)["attrs"].get(
        "external_field", 0.0))
    current_marginal = {
        c.value: float(substrate.node(c)["attrs"].get("state", 0.0))
        for c in substrate.neighbours(mt, "has_concept")
    }
    current_energy = substrate.mt_energy(mt, current_marginal)
    current_frustration = substrate.mt_frustration_given_state(
        mt, current_marginal)

    ripple = predict_ripple(substrate, mt, concept, new_h, mode=mode)
    predicted_marginal = ripple["predicted_state"]
    predicted_energy = substrate.mt_energy(mt, predicted_marginal)
    delta_E_estimate = predicted_energy - current_energy
    predicted_frustration = substrate.mt_frustration_given_state(
        mt, predicted_marginal)
    delta_F_estimate = predicted_frustration - current_frustration

    flipped: list[dict[str, Any]] = []
    for nid, predicted_sig in predicted_marginal.items():
        current_sig = float(current_marginal.get(nid, 0.0))
        if abs(predicted_sig - current_sig) > 0.5:
            flipped.append({
                "node": int(nid),
                "before": current_sig,
                "after": float(predicted_sig),
                "delta": float(predicted_sig - current_sig),
            })

    return {
        "concept_id": concept.value,
        "new_h": new_h,
        "current_h": old_h,
        "predicted_marginal": predicted_marginal,
        "predicted_energy": predicted_energy,
        "predicted_delta_E": delta_E_estimate,
        "predicted_frustration": predicted_frustration,
        "predicted_delta_F": delta_F_estimate,
        "flipped_nodes": flipped,
    }


def seek_insights(
    substrate,
    mt,
    top_k_hot: int = 5,
    h_perturbations: tuple[float, ...] = DEFAULT_H_PERTURBATIONS,
) -> list[dict[str, Any]]:
    """Search for candidate perturbations that would release frustration.

    For each hot node, sweep h-perturbations and predict their impact.
    Returns ranked list of predictions sorted by predicted ΔE
    (most negative = predicted best — biggest drop in energy →
    largest basin transition).

    Each prediction dict carries: concept_id, name, current_h, new_h,
    predicted_energy, predicted_delta_E, flipped_nodes.

    Empty list if the network is not substantially frustrated (no
    hot nodes above threshold).
    """
    # PHASE A (native-backend cutover): no relax call. A discrete_mode Mt's
    # `state` is already the committed fixed point (kept current by
    # whatever externally drives run_rules() — CAN_FINAL_MIGRATION_PREREG.md
    # §1); find_hot_nodes (native_node_local_frustration) and
    # predict_perturbation_impact both read that committed state directly.
    # The old continuous `mt_relax_to_marginal` fallback (which would have
    # CONTAMINATED `state` with tanh relaxation) is removed with the engine.
    hot = find_hot_nodes(substrate, mt, top_k=top_k_hot)
    if not hot:
        return []

    predictions: list[dict[str, Any]] = []
    for hot_row in hot:
        concept = hot_row["node"]
        current_h = hot_row["current_h"]
        for delta_h in h_perturbations:
            new_h = current_h + delta_h
            pred = predict_perturbation_impact(substrate, mt, concept, new_h)
            pred["name"] = hot_row["name"]
            pred["delta_h"] = delta_h
            pred["local_frustration_before"] = hot_row["local_frustration"]
            predictions.append(pred)

    # Rank by predicted ΔF — what the insight detector actually uses,
    # not ΔE. A basin that drops energy but doesn't release frustration
    # (e.g., by satisfying a field at the cost of an inhibitory
    # coupling) isn't what we want.
    predictions.sort(key=lambda p: p["predicted_delta_F"])
    return predictions


def apply_top_insight_candidate(
    substrate,
    mt,
    predictions: list[dict[str, Any]],
    require_negative_delta: bool = True,
) -> dict[str, Any] | None:
    """Apply the top-ranked predicted perturbation by writing the new
    h to the actual graph. Substrate has committed to investigating
    the hypothesis.

    Returns the applied prediction dict, or None if no candidate
    qualifies (e.g., all predicted deltas non-negative).
    """
    if not predictions:
        return None
    top = predictions[0]
    if require_negative_delta and top["predicted_delta_F"] >= 0:
        return None
    # Look up node handle by id (we need a PyNodeID, not just the int).
    for c in substrate.neighbours(mt, "has_concept"):
        if c.value == top["concept_id"]:
            substrate.set_attr(c, "external_field", float(top["new_h"]))
            return top
    return None


__all__ = [
    "DEFAULT_H_PERTURBATIONS",
    "HOT_NODE_FRUSTRATION_MIN",
    "find_hot_nodes",
    "predict_perturbation_impact",
    "seek_insights",
    "apply_top_insight_candidate",
]
