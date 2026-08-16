"""hate_attribution -- global+stable negative attribution about ANOTHER
agent (HATE_ATTRIBUTION_PREREG.md), generalizing ATTRIBUTION_LOCUS_AS_
RESIDUAL_PREREG.md's self-directed residual outward.

Per Sternberg (2003)'s Duplex Theory of Hate and Fischer, Halperin,
Canetti & Jasini (2018): hate is not a single angry appraisal -- it is a
STABLE, over-time commitment to a global-negative attribution about a
target, and it uniquely motivates a goal of removing/eliminating the
target (distinct from anger's goal of correcting behavior).

Pure world-adapter code (CLAUDE.md's architecture rule): mints
TargetPattern/IncidentReport nodes and the target's regard_for /
removal_desire_for Concepts (reusing shared_arousal.mint_target_concept
verbatim), then calls run_rules() to let the seeded rules DECIDE
attribution_locus and crystallization -- the only Python "decisions" here
are the literal recodings `evidence = 1.0 if standard_met else -1.0`-style
bool->float mappings this arc has used since record_incident_outcome, not
branches over graph state. concept_apply_evidence (the belief-update
primitive) is only ever called from Python, driven by values the rules
already decided.
"""
from __future__ import annotations

from domains.shared_arousal import mint_target_concept

HATE_STABILITY_THRESHOLD = 3


def mint_target_pattern(inner, mt, target: str):
    """Idempotent: the (mt, target)'s TargetPattern, tracking a live
    regard_for Concept and a removal_desire_for Concept (both minted via
    the existing shared_arousal.mint_target_concept -- reused, not
    reinvented)."""
    for existing in inner.neighbours(mt, "has_target_pattern"):
        if inner.node(existing)["attrs"].get("target") == target:
            return existing
    pat = inner.add_node("TargetPattern", {
        "target": target, "incident_count": 0, "confirm_streak": 0,
        "crystallized": 0.0,
    })
    inner.add_edge(mt, "has_target_pattern", pat, {})
    regard = mint_target_concept(inner, mt, "regard_for", target)
    removal = mint_target_concept(inner, mt, "removal_desire_for", target)
    inner.add_edge(pat, "tracks_concept", regard, {})
    inner.add_edge(pat, "tracks_removal_desire", removal, {})
    return pat


def record_hate_incident(inner, mt, pattern, *, negative: bool,
                         base_alpha: float = 0.3, max_steps: int = 3000) -> dict:
    """ONE incident about a target: mints an IncidentReport, lets the
    seeded rules derive attribution_locus (a residual against the
    tracked regard_for Concept's CURRENT, pre-this-incident state) and
    update the stability gate, THEN applies evidence (HATE_ATTRIBUTION_
    PREREG.md Sec2):

        regard_for         <- concept_apply_evidence(this incident's own signal)   [every incident]
        removal_desire_for <- concept_apply_evidence(+1.0)   [ONLY the incident that crystallizes hate]

    Returns {attribution_locus, confirm_streak, crystallized,
    crystallized_this_call, regard_state, removal_desire_state}.
    """
    signal = 1.0 if not negative else -1.0
    regard = inner.node(pattern)["attrs"]
    hate_count_before = len(list(inner.neighbours(pattern, "has_hate")))

    ir = inner.add_node("IncidentReport", {
        "target": inner.node(pattern)["attrs"]["target"],
        "signal": signal, "status": "pending",
    })
    inner.add_edge(mt, "has_incident_report", ir, {})
    inner.add_edge(ir, "about_pattern", pattern, {})
    inner.force_all_dirty()
    inner.run_rules(max_steps)

    appraisal = next(iter(inner.neighbours(ir, "has_appraisal")))
    attribution_locus = inner.node(appraisal)["attrs"]["attribution_locus"]

    regard_concept = next(iter(inner.neighbours(pattern, "tracks_concept")))
    inner.concept_apply_evidence(regard_concept, signal, base_alpha)

    hate_count_after = len(list(inner.neighbours(pattern, "has_hate")))
    crystallized_this_call = hate_count_after > hate_count_before
    if crystallized_this_call:
        removal_concept = next(iter(inner.neighbours(pattern, "tracks_removal_desire")))
        inner.concept_apply_evidence(removal_concept, 1.0, base_alpha)

    inner.force_all_dirty()
    inner.run_rules(max_steps)

    pat_attrs = inner.node(pattern)["attrs"]
    regard_attrs = inner.node(regard_concept)["attrs"]
    removal_concept = next(iter(inner.neighbours(pattern, "tracks_removal_desire")))
    removal_attrs = inner.node(removal_concept)["attrs"]
    # `state` is the DISCRETE relaxed 3-state value -- for a standalone
    # Concept with no causal_influence edges (regard_for/removal_desire_for
    # are freestanding accumulators here, not wired into a causal network)
    # it does not relax off 0.0 regardless of external_field, the same
    # behavior this arc's shared_arousal rung already worked around by
    # reporting external_field, not state. external_field is the real,
    # moving observable this mechanism's own residual reads.
    return {
        "attribution_locus": attribution_locus,
        "confirm_streak": pat_attrs["confirm_streak"],
        "crystallized": bool(pat_attrs["crystallized"]),
        "crystallized_this_call": crystallized_this_call,
        "regard_external_field": regard_attrs["external_field"],
        "regard_state": regard_attrs["state"],
        "removal_desire_external_field": removal_attrs["external_field"],
        "removal_desire_state": removal_attrs["state"],
    }


__all__ = ["mint_target_pattern", "record_hate_incident", "HATE_STABILITY_THRESHOLD"]
