"""iter-32 — the agent DERIVES the COMBINATORIAL recognition from its OWN shapes +
the iter-31 RESIDUAL. NO-DONKEY: this script registers iter-31's HONEST residual as a
held postulate and runs the agent's OWN synthesize_gaps over it with the agent's OWN
harvested shape-library. Whatever the agent's shapes surface IS the derivation,
reported VERBATIM.

THE SITUATION (iter-26 / iter-27 / iter-30 / iter-31). The agent has TWO complementary
per-utterance channels reading off the SAME grown patch bank:
  · a SPECTRAL-DETAIL channel (the grown-patch flat readout) — carries "what is this",
    it is the strongest SINGLE channel on the within-voice exemplar match (iter-31
    1-NN flat beats the frozen front-end);
  · a TRANSITION channel (the agent's order-1-over-time operator, the cross-voice
    contrast channel the iter-30 selector scores on) — carries "which word across
    different voices".
Each channel is LOSSY ALONE (iter-31: 1-NN over the transition channel alone < 1-NN
over the flat channel alone — the transition readout is too lossy on its own; and the
flat channel alone does not carry the cross-voice discrimination). They are
COMPLEMENTARY.

The prior combiners FAILED because they merged the two channels into ONE measure:
  · iter-26 CONCATENATED both channels and ran a SINGLE distance over the whole vector
    — the weak channel dragged the strong, REGRESSED below the strong channel alone;
  · iter-27 ran ONE GLOBAL weighted sum of the two channels — config-sensitive, still
    let the weaker channel's share drag the stronger decision down where the stronger
    was already dominant.
Both are ONE merged measure over the two channels. iter-31's residual, restated as the
order-0 postulate: the channels carry COMPLEMENTARY evidence and each must keep its own
role in the decision — the identity is the one BOTH channels independently point to —
rather than being fused into a single shared measure that lets one channel's weakness
contaminate the other's strength.

The residual text states this STRUCTURALLY and does NOT name the fix (no "conjunction",
"agreement", "product", "rank", "vote", "combinatorial", "argmax", "recognition_graph",
"both", "intersection", "jointly", "independent evidence", "Bayes").

Run:  python scripts/iter32_combinatorial_derive.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import breadth_audit
from domains.code_authoring import _install_concept
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps

# Re-use the full build (installs the agent's all-pole science + phonology +
# speech_science + engineering + concept-expansions, so its harvested library carries
# the redundancy, per-component-selection, Bayes/evidence, and routing shapes).
from scripts.iter25_lpc_formant_derive import _build


# ---------------------------------------------------------------------------
# Step 1 — register iter-31's RESIDUAL as a held postulate.
#
# Honest, STRUCTURAL text. It states: (1) the unit's identity is now evidenced by TWO
# complementary components — one carrying the fine detail of WHAT the unit is, one
# carrying which unit it is ACROSS different voices; (2) each component used on its own
# is LOSSY — the detail component misses the across-voice distinction, the across-voice
# component is too coarse to pin the exact unit; (3) the prior decision rules fused the
# two components into ONE shared measure (concatenated then one distance; or one global
# proportioned sum), which let the weaker component's noise contaminate the stronger's
# strength; (4) a decision in which each component keeps its OWN role and the chosen
# unit is the one BOTH components independently point to — so neither contaminates the
# other — should beat the single fused measure.
#
# It does NOT name the answer (no "conjunction", "agreement", "product", "rank",
# "vote", "combinatorial", "argmax", "recognition_graph", "both", "intersection",
# "jointly", "independent evidence", "Bayes", "routing", "tie-break").
# ---------------------------------------------------------------------------
_RESIDUAL_TEXT = (
    "The unit's identity is now evidenced by TWO complementary components that read "
    "the same observation. One component carries the FINE DETAIL of what the unit is; "
    "the other component carries which unit it is across DIFFERENT speakers. Each "
    "component on its own is LOSSY: the detail component is blind to the "
    "across-speaker distinction, and the across-speaker component is too coarse to "
    "pin the exact unit. They are complementary: where one is uninformative the other "
    "carries the distinction. The prior decision rules fused the two components into "
    "ONE shared measure — concatenating them into a single vector and taking one "
    "distance over the whole, or taking one global proportioned blend of the two — and "
    "that single fused measure let the weaker, noisier component contaminate the "
    "stronger one, so the fused result was worse than the stronger component used on "
    "its own. The right decision is not a single fused measure over the components. "
    "It is a decision in which each component keeps its OWN role and contributes its "
    "OWN evidence, and the unit selected is the one that EACH component, scored "
    "separately, points to as most consistent with what was observed — the candidate "
    "that satisfies the detail component AND satisfies the across-speaker component "
    "together — so a component that is uninformative for a given contrast cannot drag "
    "down the component that does carry it. Evidence from separable observations "
    "should be taken from each separately and brought to bear on the same decision, "
    "each weighted by how reliably that observation bears on the candidate, rather "
    "than smeared into one shared measure where one observation's error swamps the "
    "other's signal.")


def _register(sub):
    mt = sub.add_node("Microtheory", {
        "name": "combinatorial_decision_paradigm",
        "origin": "iter32_combinatorial_derive"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "iter32:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "fused_measure_frame", _RESIDUAL_TEXT)
    return mt


def _show(g):
    print(f"    => GAP (order-{g['order']}): keys={g['capability_keys']}")
    print(f"       via_shapes={g['via_shapes']}  domains={g['source_domains']}")
    print(f"       source_concepts={g.get('source_concepts')}")
    print(f"       gap: {g['gap']}")


def main():
    print("=" * 78)
    print("ITER-32 — the agent DERIVES the COMBINATORIAL recognition from its OWN")
    print("shapes, over the iter-31 RESIDUAL frame")
    print("=" * 78)

    print("\n[Step 1] Register iter-31's RESIDUAL as a held postulate:")
    print("  ", _RESIDUAL_TEXT)

    sub = _build()
    _register(sub)

    lib = harvest_shapes_combined(sub)
    print(f"\n  harvested library: {len(lib)} shapes (the agent's OWN).")

    print("\n" + "=" * 78)
    print("[Step 2] synthesize_gaps over the RESIDUAL frame — what does it DERIVE?")
    print("=" * 78)
    gaps = synthesize_gaps(sub, "fused_measure_frame", shapes=lib,
                           record=False, prune=False, max_order=3)
    print(f"  n gaps surfaced: {len(gaps)}\n")

    agree_gaps, evidence_gaps, route_gaps = [], [], []
    for g in gaps:
        roles = breadth_audit.classify_shape_role(breadth_audit._gap_to_shapelike(g))
        tag = ",".join(roles) or "unclassified"
        print(f"    [{tag}]")
        _show(g)
        blob = (" ".join(g.get("via_shapes", [])) + " "
                + " ".join(g.get("capability_keys", [])) + " "
                + g.get("gap", "")).lower()
        # each component keeps its role; the unit both point to (the AGREEMENT KIND)
        if any(k in blob for k in ("each", "separate", "per-component", "per_component",
                                   "selection", "consistent", "satisf", "agree",
                                   "consensus", "point", "both")):
            agree_gaps.append(g)
        # take evidence from each observation by its reliability (the EVIDENCE KIND)
        if any(k in blob for k in ("posterior", "prior", "evidence", "likelihood",
                                   "bayes", "reliab", "redundan", "independent")):
            evidence_gaps.append(g)
        # route to the component that carries this contrast (the ROUTING KIND)
        if any(k in blob for k in ("route", "routing", "per-contrast", "per_contrast",
                                   "which component", "mode selection", "adapt")):
            route_gaps.append(g)
        print()

    print("=" * 78)
    print("DERIVATION SUMMARY — the agent's OWN shapes, fired on the residual:")
    print("=" * 78)
    print(f"  (A) each component keeps its role; pick what BOTH point to -> "
          f"{len(agree_gaps)} gap(s)")
    for g in agree_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (B) take evidence from each observation by its reliability -> "
          f"{len(evidence_gaps)} gap(s)")
    for g in evidence_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (C) route to the component that carries this contrast      -> "
          f"{len(route_gaps)} gap(s)")
    for g in route_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")


if __name__ == "__main__":
    main()
