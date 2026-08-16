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

v1.1.0 (HATE_PASSION_COUPLING_PREREG.md): the target's TargetPattern also
tracks the SAME shared TargetArousal pool `shared_arousal.py` already
built (Sternberg 2003's passion component) -- every incident contributes
to it (valence-blind intensity, Schachter & Singer 1962), and the
crystallizing incident's removal_desire_for alpha is amplified by
whatever arousal has built up, read BEFORE this incident's own
contribution, the same read-before/update-after convention `shared_
arousal.record_targeted_incident` already established.
"""
from __future__ import annotations

from domains.shared_arousal import mint_target_arousal, mint_target_concept

HATE_STABILITY_THRESHOLD = 3
AROUSAL_INTENSITY = 0.8
AROUSAL_DECAY = 0.7


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
    arousal = mint_target_arousal(inner, mt, target)
    inner.add_edge(pat, "tracks_arousal", arousal, {})
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
    crystallized_this_call, regard_state, removal_desire_state,
    arousal_level, effective_removal_alpha}.
    """
    signal = 1.0 if not negative else -1.0
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

    arousal_node = next(iter(inner.neighbours(pattern, "tracks_arousal")))
    current_arousal = inner.node(arousal_node)["attrs"]["level"]

    hate_count_after = len(list(inner.neighbours(pattern, "has_hate")))
    crystallized_this_call = hate_count_after > hate_count_before
    effective_removal_alpha = None
    if crystallized_this_call:
        effective_removal_alpha = base_alpha * (1.0 + current_arousal)
        removal_concept = next(iter(inner.neighbours(pattern, "tracks_removal_desire")))
        inner.concept_apply_evidence(removal_concept, 1.0, effective_removal_alpha)

    new_arousal = current_arousal * AROUSAL_DECAY + AROUSAL_INTENSITY
    inner.set_attr(arousal_node, "level", new_arousal)

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
        "arousal_level": new_arousal,
        "effective_removal_alpha": effective_removal_alpha,
    }


__all__ = ["mint_target_pattern", "record_hate_incident", "HATE_STABILITY_THRESHOLD"]
