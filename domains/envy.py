"""envy -- Smith & Kim (2007)'s comparative envy, Van de Ven, Zeelenberg
& Pieters (2009)'s benign-vs-malicious split. Reuses relative_self_worth
(domains/can_self_worth_bridge.py) ENTIRELY unchanged for the upward-
comparison half; the only new piece is a deservingness appraisal.

ENVY_PREREG.md: read_envy is a PURE classification function over two
already-computed floats -- no new comparison mechanism, no accumulator
beyond the one belief this module adds.
"""
from __future__ import annotations


def mint_domain_deservingness_belief(inner, resident_can: dict, domain: str):
    """Idempotent: the resident's `deservingness_belief_for:<domain>`
    Concept -- do they believe their peers' relative advantage in this
    domain is fair. Fresh and uncoupled (mirrors self_efficacy_for's own
    shape): a situational appraisal, not a generalized expectancy."""
    mt = resident_can["mt"]
    concept_name = "deservingness_belief_for:%s" % domain
    for existing in inner.neighbours(mt, "has_concept"):
        if inner.node(existing)["attrs"].get("name") == concept_name:
            return existing
    concept = inner.add_node("Concept", {
        "name": concept_name, "state": 0.0, "external_field": 0.0,
        "identity_field": 0.0,
    })
    inner.add_edge(mt, "has_concept", concept, {})
    return concept


def record_deservingness_incident(inner, concept, *, deserved: bool,
                                  alpha: float = 0.3, max_steps: int = 3000) -> float:
    """ONE piece of evidence about whether the disparity is fair -- flat
    evidence, the same shape every belief update in this arc uses.
    Returns the Concept's new external_field."""
    evidence = 1.0 if deserved else -1.0
    inner.concept_apply_evidence(concept, evidence, alpha)
    inner.force_all_dirty()
    inner.run_rules(max_steps)
    return inner.node(concept)["attrs"]["external_field"]


def read_envy(relative_self_worth: float, deservingness_value: float) -> str:
    """ENVY_PREREG.md Sec2: Smith & Kim 2007 + Van de Ven, Zeelenberg &
    Pieters 2009. No disadvantage -> no envy. A disadvantage seen as
    DESERVED -> benign envy (aspirational, no hostility). A disadvantage
    seen as UNDESERVED -> malicious envy (hostility toward the
    advantaged party)."""
    if relative_self_worth >= 0.0:
        return "none"
    return "benign" if deservingness_value >= 0.0 else "malicious"


__all__ = [
    "mint_domain_deservingness_belief", "record_deservingness_incident", "read_envy",
]
