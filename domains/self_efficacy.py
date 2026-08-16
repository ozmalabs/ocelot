"""self_efficacy -- belief in one's OWN capability (Bandura 1977, 1997),
distinct from self_worth, wired into the confirmed-dead AffectiveState.
competence schema field.

SELF_EFFICACY_PREREG.md: self_efficacy_for:<domain> is FRESH and
UNCOUPLED per domain (unlike self_worth's own projected-then-decoupling
design) -- Bandura's own repeated emphasis that self-efficacy is
TASK-SPECIFIC, not a generalized expectancy. The behavioral consequence
(persistence vs. avoidance) is a genuinely different axis from every
mood/appraisal Concept elsewhere in this arc.

Pure world-adapter code (CLAUDE.md's architecture rule): mints a plain
CAN Concept (reusing the SAME node shape every belief in this arc uses),
applies evidence via the SAME concept_apply_evidence primitive, and
mechanically syncs the resulting value onto AffectiveState.competence --
no new schema, no PSI drive-competition machinery.
"""
from __future__ import annotations


def mint_domain_self_efficacy(inner, resident_can: dict, domain: str):
    """Idempotent: the resident's `self_efficacy_for:<domain>` Concept.
    Fresh and UNCOUPLED -- no causal_influence edges to any global
    Concept (SELF_EFFICACY_PREREG.md Sec2: Bandura's task-specificity,
    contrasted deliberately with self_worth's own coupled design)."""
    mt = resident_can["mt"]
    concept_name = "self_efficacy_for:%s" % domain
    for existing in inner.neighbours(mt, "has_concept"):
        if inner.node(existing)["attrs"].get("name") == concept_name:
            return existing
    concept = inner.add_node("Concept", {
        "name": concept_name, "state": 0.0, "external_field": 0.0,
        "identity_field": 0.0,
    })
    inner.add_edge(mt, "has_concept", concept, {})
    return concept


def record_self_efficacy_incident(inner, concept, *, success: bool,
                                  alpha: float = 0.3, max_steps: int = 3000) -> float:
    """ONE success/failure incident -- flat evidence, no arousal/debt
    amplification (Bandura's theory gives no basis for a passion-style
    channel here). Returns the Concept's new external_field."""
    evidence = 1.0 if success else -1.0
    inner.concept_apply_evidence(concept, evidence, alpha)
    inner.force_all_dirty()
    inner.run_rules(max_steps)
    return inner.node(concept)["attrs"]["external_field"]


def read_persistence_disposition(efficacy_value: float) -> str:
    """Bandura's own central behavioral claim, made concrete
    (SELF_EFFICACY_PREREG.md Sec2): high self-efficacy sustains effort
    (persist); low self-efficacy predicts giving up (avoid)."""
    return "persist" if efficacy_value >= 0.0 else "avoid"


def sync_competence_to_affective_state(inner, affective_state_node, efficacy_concept) -> float:
    """Writes the efficacy Concept's CURRENT external_field directly onto
    AffectiveState.competence -- the SAME schema field seeds/affective_
    state_core.json's own psi_project_canonical_affect rule already
    writes to from ModulatorState.competence, confirmed live and dead
    before this rung (SELF_EFFICACY_PREREG.md Sec0). Mechanical write,
    not a PSI drive-competition integration."""
    value = inner.node(efficacy_concept)["attrs"]["external_field"]
    inner.set_attr(affective_state_node, "competence", value)
    return value


__all__ = [
    "mint_domain_self_efficacy", "record_self_efficacy_incident",
    "read_persistence_disposition", "sync_competence_to_affective_state",
]
