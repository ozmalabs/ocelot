"""resident_trust -- trust as competence x willingness (Castelfranchi &
Falcone's cognitive trust theory), generalizing trust_mayor
(worlds/bigville_can_beliefs.py, confirmed a real evidence-driven CAN
node before this rung, but fixed to "the mayor specifically") to ANY
target.

RESIDENT_TRUST_PREREG.md: competence_for/willingness_for are genuine
ToM beliefs about the TARGET's own properties (can they do it; will they
choose to) -- minted via the SAME named entry point
bigville_theory_of_mind.mint_resident_tom_belief already established for
controllability_for, not a forked parallel representation. Trust itself
is a COMPUTED READ (min of the two), not a third accumulating Concept --
a pure function of two already-tracked beliefs, not duplicated state.

trust_mayor stays completely UNCHANGED -- this is a new, separate,
target-generic primitive alongside it, not a replacement.
"""
from __future__ import annotations

from domains.bigville_theory_of_mind import mint_resident_tom_belief


def mint_trust_beliefs(inner, mt, target: str, *, prior_others_trust=None) -> dict:
    """Idempotent: the (mt, target)'s competence_for and willingness_for
    ToM beliefs. Returns {"competence": <Concept>, "willingness": <Concept>}.

    `prior_others_trust` (optional): a cold-start PRIOR -- the gap this
    module's own docstring named ("Optionally consumes ... a cold-start
    prior ... named, not required") and AFFECT_COUPLING Phase 5 closes.
    Applied ONCE, only if these beliefs are being minted fresh for the
    first time (checked BEFORE minting, mirroring the hate_count_before-
    style before/after idiom used elsewhere in this arc) -- a resident's
    own drawn `prior_others_trust` trait (bigville_town100_world.py
    `_PARAM_SPEC`) becomes the starting point before any real trust
    incident, the same "prior before evidence" shape `trust_mayor`
    already uses. Byte-identical for every existing no-arg caller."""
    existing_names = {inner.node(c)["attrs"].get("name")
                      for c in inner.neighbours(mt, "has_concept")}
    is_fresh = ("competence_for:%s" % target) not in existing_names
    competence = mint_resident_tom_belief(inner, mt, "competence", target)
    willingness = mint_resident_tom_belief(inner, mt, "willingness", target)
    if is_fresh and prior_others_trust is not None:
        inner.concept_apply_evidence(competence, float(prior_others_trust), 1.0)
        inner.concept_apply_evidence(willingness, float(prior_others_trust), 1.0)
        inner.force_all_dirty()
        inner.run_rules()
    return {"competence": competence, "willingness": willingness}


def record_trust_incident(inner, beliefs: dict, *, dimension: str, positive: bool,
                          alpha: float = 0.3, max_steps: int = 3000) -> float:
    """ONE incident about a target's competence OR willingness --
    `dimension` is caller-supplied data (which kind of incident this was),
    not a decision. Applies flat evidence to the matching Concept via the
    SAME concept_apply_evidence primitive every belief update in this arc
    uses. Returns that Concept's new external_field."""
    concept = beliefs[dimension]
    evidence = 1.0 if positive else -1.0
    inner.concept_apply_evidence(concept, evidence, alpha)
    inner.force_all_dirty()
    inner.run_rules(max_steps)
    return inner.node(concept)["attrs"]["external_field"]


def read_trust(inner, beliefs: dict) -> float:
    """RESIDENT_TRUST_PREREG.md Sec2: trust = min(competence, willingness)
    -- the weakest-link operationalization of Castelfranchi's AND-like
    requirement (a target competent but unwilling, or willing but
    incompetent, is not trusted; trust cannot exceed its worst
    dimension). A computed read, not a stored Concept."""
    competence_ef = inner.node(beliefs["competence"])["attrs"]["external_field"]
    willingness_ef = inner.node(beliefs["willingness"])["attrs"]["external_field"]
    return min(competence_ef, willingness_ef)


__all__ = ["mint_trust_beliefs", "record_trust_incident", "read_trust"]
