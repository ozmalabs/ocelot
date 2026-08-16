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

from domains.bigville_theory_of_mind import mint_resident_tom_belief
from domains.shared_arousal import mint_target_arousal, mint_target_concept

HATE_STABILITY_THRESHOLD = 3
AROUSAL_INTENSITY = 0.8
AROUSAL_DECAY = 0.7


def mint_target_pattern(inner, mt, target: str):
    """Idempotent: the (mt, target)'s TargetPattern, tracking a live
    regard_for Concept, a removal_desire_for Concept, a pity_for Concept,
    and a controllability_for Concept (all minted via the existing
    shared_arousal.mint_target_concept -- reused, not reinvented).
    controllability_for IS the resident's Theory-of-Mind belief about
    the target (HATE_PITY_TOM_UNDERSTANDING_PREREG.md Sec0/2) -- the
    first resident-of-resident ToM content in bigville, built as the
    SAME per-target CAN Concept shape as every other belief in this arc,
    not a new primitive."""
    for existing in inner.neighbours(mt, "has_target_pattern"):
        if inner.node(existing)["attrs"].get("target") == target:
            return existing
    pat = inner.add_node("TargetPattern", {
        "target": target, "incident_count": 0, "confirm_streak": 0,
        "crystallized": 0.0, "resentment_debt": 0.0,
    })
    inner.add_edge(mt, "has_target_pattern", pat, {})
    regard = mint_target_concept(inner, mt, "regard_for", target)
    removal = mint_target_concept(inner, mt, "removal_desire_for", target)
    pity = mint_target_concept(inner, mt, "pity_for", target)
    # controllability is a ToM belief ABOUT the target (Weiner's
    # attribution), not the resident's own affect toward them -- minted
    # through the named ToM entry point (bigville_theory_of_mind.py),
    # not mint_target_concept directly (TOM_SYSTEM_UNIFICATION_RESULTS.md).
    controllability = mint_resident_tom_belief(inner, mt, "controllability", target)
    inner.add_edge(pat, "tracks_concept", regard, {})
    inner.add_edge(pat, "tracks_removal_desire", removal, {})
    inner.add_edge(pat, "tracks_pity", pity, {})
    inner.add_edge(pat, "tracks_controllability", controllability, {})
    arousal = mint_target_arousal(inner, mt, target)
    inner.add_edge(pat, "tracks_arousal", arousal, {})
    return pat


def record_understanding_incident(inner, pattern, *, exculpatory: bool,
                                  alpha: float = 0.3) -> float:
    """ONE piece of understanding about WHY the target behaves as they
    do -- evidences the resident's controllability_for ToM belief
    directly (HATE_PITY_TOM_UNDERSTANDING_PREREG.md Sec2). Flat,
    accumulating CAN evidence, no locus/stability layer -- a single
    piece of understanding has no "confirms a pattern" structure the way
    a repeated hostile incident does. Returns the Concept's new
    external_field."""
    evidence = -1.0 if exculpatory else 1.0
    controllability = next(iter(inner.neighbours(pattern, "tracks_controllability")))
    inner.concept_apply_evidence(controllability, evidence, alpha)
    inner.force_all_dirty()
    inner.run_rules(3000)
    return inner.node(controllability)["attrs"]["external_field"]


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
    resentment_debt = inner.node(pattern)["attrs"]["resentment_debt"]

    hate_count_after = len(list(inner.neighbours(pattern, "has_hate")))
    crystallized_this_call = hate_count_after > hate_count_before
    effective_removal_alpha = None
    consequence_route = None
    if crystallized_this_call:
        hate_node = next(iter(inner.neighbours(pattern, "has_hate")))
        consequence_route = inner.node(hate_node)["attrs"]["consequence_route"]
        # HATE_PITY_TOM_UNDERSTANDING_PREREG.md Sec2: the rule already
        # DECIDED consequence_route (Weiner's controllability dimension,
        # read from the resident's own ToM belief about the target);
        # Python only dispatches which literal Concept receives the
        # evidence -- pity_for is unamplified (not a passion channel),
        # so effective_removal_alpha stays None unless actually applied.
        if consequence_route == "removal":
            # HATE_RESENTMENT_PASSION_COUPLING_PREREG.md Sec2: BOTH
            # momentary arousal AND accumulated (never-decremented)
            # resentment_debt amplify the removal motive, multiplicatively
            # -- at resentment_debt==0 this is exactly v1.1.0's original
            # arousal-only formula.
            effective_removal_alpha = base_alpha * (1.0 + current_arousal) * (1.0 + resentment_debt)
            removal_concept = next(iter(inner.neighbours(pattern, "tracks_removal_desire")))
            inner.concept_apply_evidence(removal_concept, 1.0, effective_removal_alpha)
        else:
            pity_concept = next(iter(inner.neighbours(pattern, "tracks_pity")))
            inner.concept_apply_evidence(pity_concept, 1.0, base_alpha)

    inner.force_all_dirty()
    inner.run_rules(max_steps)

    # arousal updates AFTER every rule pass for this incident has
    # settled -- HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md's
    # crystallize_hate gate reads arousal_level too, and this second
    # run_rules() call (needed to relax the regard_for/removal_desire
    # evidence just applied) would otherwise re-fire crystallize_hate
    # using THIS incident's own bumped-up arousal instead of the
    # pre-incident value every coupling in this arc reads by design --
    # found and fixed here (previously the set_attr ran before this
    # call, corrupting crystallized_this_call's own hate-count-delta
    # detection whenever crystallization happened to land in the second
    # pass instead of the first).
    new_arousal = current_arousal * AROUSAL_DECAY + AROUSAL_INTENSITY
    inner.set_attr(arousal_node, "level", new_arousal)

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
        "resentment_debt": pat_attrs["resentment_debt"],
        "consequence_route": consequence_route,
        "pity_external_field": inner.node(
            next(iter(inner.neighbours(pattern, "tracks_pity"))))["attrs"]["external_field"],
        "controllability_external_field": inner.node(
            next(iter(inner.neighbours(pattern, "tracks_controllability"))))["attrs"]["external_field"],
    }


__all__ = ["mint_target_pattern", "record_understanding_incident",
           "record_hate_incident", "HATE_STABILITY_THRESHOLD"]
