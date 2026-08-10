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
    for c in concepts:
        local_f = substrate.node_local_frustration(mt, c)
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
    """
    # Read current state for comparison.
    current_marginal = substrate.mt_mean_field_marginal(mt)
    current_audit = substrate.mt_audit_basin(mt)

    # Predicted marginal under the hypothetical h.
    predicted_marginal = substrate.mt_mean_field_with_h_override(
        mt, concept, new_h)

    # Predicted energy via mt_energy on the predicted marginal, plus a
    # correction for the field term: mt_energy reads h from the graph
    # attrs, so the field contribution at `concept` is computed with
    # the OLD external_field. We applied the override to the marginal
    # but not to the energy formula's field term. Correct by adding
    # the field delta:
    #   E_old_h_term = -old_h * σ
    #   E_new_h_term = -new_h * σ
    #   correction = E_new - E_old = (old_h - new_h) * σ
    # (identity_field unchanged on both sides of the equation.)
    predicted_energy_uncorrected = substrate.mt_energy(mt, predicted_marginal)
    old_h = float(substrate.node(concept)["attrs"].get(
        "external_field", 0.0))
    sigma_at_concept = float(predicted_marginal.get(concept.value, 0.0))
    energy_correction = sigma_at_concept * (old_h - new_h)
    predicted_energy = predicted_energy_uncorrected + energy_correction
    delta_E_estimate = predicted_energy - current_audit["energy"]

    # Predicted frustration — what the insight detector actually uses.
    # Frustration depends only on couplings + σ; no h-correction needed.
    predicted_frustration = substrate.mt_frustration_given_state(
        mt, predicted_marginal)
    delta_F_estimate = predicted_frustration - current_audit["frustration"]

    # Per-node flip detection.
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
    # Ensure state attrs reflect equilibrium.
    substrate.mt_relax_to_marginal(mt)

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
