"""drive_curiosity_high_entropy — substrate's first explicit drive.

Per the agent's pick from scripts/agent_designs_next.py:

  Chosen item: drive_curiosity_high_entropy
  Definition from Mt:
    'Substrate probes nodes with high state entropy (σ near 0,
    ambivalent). Expected info gain highest at frustration sites.'

Per the user's memory [[ozma_curiosity_drive]]: 'the substrate is
alive iff curiosity drives it'. This module turns that into a
mechanism: each step, the substrate identifies ambivalent nodes
(|σ| near 0) and probes them via what-if relaxations to measure
information gain. Read-only — no actual state mutation; the
substrate examines its own basin landscape.

Probes are recorded as CuriosityProbeEvent nodes — the substrate's
record of 'these are the nodes I'd learn from if I had evidence
about them.' Downstream consumers (world adapters, attention
schedulers) can use this to direct evidence-seeking behavior.

Per the Mt: 'Expected info gain highest at frustration sites' —
so probes are biased toward ambivalent nodes near frustrated
couplings.
"""
from __future__ import annotations

from typing import Any


CURIOSITY_AMBIVALENCE_THRESHOLD = 0.1
"""|σ| < this counts as ambivalent (high entropy). Below this the
node hasn't committed strongly to either basin."""

CURIOSITY_PROBE_DELTA = 0.5
"""h-perturbation magnitude in the what-if. Larger than baseline
evidence so the probe meaningfully tests the node's sensitivity."""

CURIOSITY_TOP_K = 3
"""Probe at most this many ambivalent nodes per Mt per step."""


def find_ambivalent_nodes(
    substrate, mt,
    threshold: float = CURIOSITY_AMBIVALENCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Concepts in this Mt whose σ is near 0 (high entropy). Sorted by
    ambivalence descending (closest to 0 first)."""
    ambivalent: list[dict[str, Any]] = []
    for c in substrate.neighbours(mt, "has_concept"):
        attrs = substrate.node(c)["attrs"]
        sigma = float(attrs.get("state", 0.0))
        if abs(sigma) < threshold:
            ambivalent.append({
                "node": c,
                "node_id": c.value if hasattr(c, "value") else int(c),
                "sigma": sigma,
                "ambivalence": 1.0 - abs(sigma),
                "name": str(attrs.get("name", "")),
            })
    ambivalent.sort(key=lambda x: -x["ambivalence"])
    return ambivalent


def probe_via_what_if(
    substrate, mt, concept,
    h_delta: float = CURIOSITY_PROBE_DELTA,
) -> dict[str, Any]:
    """What-if probe: predict what would happen if we applied h_delta
    evidence to this concept. Returns info gain metrics. No actual
    mutation — the substrate examines its own landscape.

    Gated by Mt.discrete_mode (CAN_FINAL_MIGRATION_PREREG.md §3.1): a
    Mt running the native discrete-async CAN mechanism ("2state"/"3state")
    is probed via domains/can_counterfactual.py's own non-mutating,
    zero-run_rules() Term-tree predictor (predicted_info_gain) — an exact
    formula twin of can_native_update_3state/_2state, never the continuous
    mean-field. An Mt with no discrete_mode attr keeps the ORIGINAL
    continuous mt_mean_field_marginal/mt_mean_field_with_h_override path,
    byte-for-byte — this is a GATED dual-path migration, not an
    unconditional replace, because an un-upgraded Mt has no
    state/temperature vocabulary the native formula expects, and forcing
    it onto the native path would silently change its behaviour."""
    current_h = float(substrate.node(concept)["attrs"].get(
        "external_field", 0.0))
    new_h = current_h + h_delta

    discrete_mode = substrate.node(mt)["attrs"].get("discrete_mode")
    if discrete_mode in ("2state", "3state"):
        from domains.can_counterfactual import predicted_info_gain
        result = predicted_info_gain(substrate, mt, concept, new_h,
                                     mode=discrete_mode)
        concept_id = (concept.value if hasattr(concept, "value")
                      else int(concept))
        current_sigma = float(substrate.node(concept)["attrs"].get(
            "state", 0.0))
        return {
            "concept_id": concept_id,
            "h_delta": h_delta,
            "current_sigma": current_sigma,
            "info_gain_total_change": float(result["info_gain_total_change"]),
            "info_gain_max_node_change": float(
                result["info_gain_max_node_change"]),
            "predicted_flipped_count": int(result["predicted_flipped_count"]),
        }

    current_marginal = substrate.mt_mean_field_marginal(mt)
    predicted_marginal = substrate.mt_mean_field_with_h_override(
        mt, concept, new_h)

    # Info gain: total σ change across all nodes (not just the probed one).
    total_change = 0.0
    max_node_change = 0.0
    flipped_count = 0
    for nid, predicted_sig in predicted_marginal.items():
        current_sig = float(current_marginal.get(nid, 0.0))
        change = abs(predicted_sig - current_sig)
        total_change += change
        if change > max_node_change:
            max_node_change = change
        if change > 0.5:
            flipped_count += 1

    return {
        "concept_id": concept.value if hasattr(concept, "value")
                      else int(concept),
        "h_delta": h_delta,
        "current_sigma": float(current_marginal.get(
            concept.value if hasattr(concept, "value") else int(concept),
            0.0)),
        "info_gain_total_change": float(total_change),
        "info_gain_max_node_change": float(max_node_change),
        "predicted_flipped_count": int(flipped_count),
    }


def run_curiosity(
    substrate, mt,
    top_k: int = CURIOSITY_TOP_K,
    threshold: float = CURIOSITY_AMBIVALENCE_THRESHOLD,
    h_delta: float = CURIOSITY_PROBE_DELTA,
) -> list[dict[str, Any]]:
    """Run curiosity for one Mt: identify ambivalent nodes, probe
    each via what-if, return ranked info-gain results."""
    ambivalent = find_ambivalent_nodes(substrate, mt, threshold)
    probes: list[dict[str, Any]] = []
    for amb in ambivalent[:top_k]:
        probe = probe_via_what_if(substrate, mt, amb["node"], h_delta)
        probe["ambivalence_before"] = amb["ambivalence"]
        probe["concept_name"] = amb["name"]
        probes.append(probe)
    # Sort by info gain — substrate's 'what would I learn most from'.
    probes.sort(key=lambda p: -p["info_gain_total_change"])
    return probes


def run_curiosity_all_mts(
    substrate,
    top_k: int = CURIOSITY_TOP_K,
) -> dict[int, list[dict[str, Any]]]:
    """Run curiosity across every Mt. Returns mt_id → probe results."""
    out: dict[int, list[dict[str, Any]]] = {}
    for mt in substrate.nodes("Microtheory"):
        mt_id = mt.value if hasattr(mt, "value") else int(mt)
        probes = run_curiosity(substrate, mt, top_k=top_k)
        if probes:
            out[mt_id] = probes
    return out


def record_curiosity_probe(
    substrate, mt, probe: dict[str, Any],
) -> Any | None:
    """Create a CuriosityProbeEvent node. The substrate's record of
    'I'd learn from this.'"""
    mt_id = mt.value if hasattr(mt, "value") else int(mt)
    attrs = {
        "mt_id": int(mt_id),
        "concept_id": int(probe["concept_id"]),
        "concept_name": str(probe.get("concept_name", "")),
        "h_delta": float(probe["h_delta"]),
        "current_sigma": float(probe["current_sigma"]),
        "info_gain_total_change": float(probe["info_gain_total_change"]),
        "info_gain_max_node_change": float(probe["info_gain_max_node_change"]),
        "predicted_flipped_count": int(probe["predicted_flipped_count"]),
    }
    try:
        node = substrate.add_node("CuriosityProbeEvent", attrs)
    except Exception:
        return None
    return node


def list_curiosity_probes(substrate) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("CuriosityProbeEvent"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_id": int(attrs.get("mt_id", -1)),
            "concept_id": int(attrs.get("concept_id", -1)),
            "concept_name": str(attrs.get("concept_name", "")),
            "info_gain_total_change": float(attrs.get(
                "info_gain_total_change", 0.0)),
        })
    return out


__all__ = [
    "CURIOSITY_AMBIVALENCE_THRESHOLD",
    "CURIOSITY_PROBE_DELTA",
    "CURIOSITY_TOP_K",
    "find_ambivalent_nodes",
    "probe_via_what_if",
    "run_curiosity",
    "run_curiosity_all_mts",
    "record_curiosity_probe",
    "list_curiosity_probes",
]
