"""shared_arousal -- excitation transfer between co-target beliefs
(SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md).

Per Schachter & Singer (1962) and Zillmann (1971, 1983): arousal is
largely undifferentiated at its source. A hostile incident toward a
target and a desire-relevant incident toward the SAME target draw on the
SAME arousal pool -- confirmed here as a real amplification effect on
whichever belief update happens while arousal is still elevated (Dutton &
Aron 1974), regardless of which relation caused the spike.

Pure world-adapter code (CLAUDE.md's architecture rule): mints plain CAN
Concept nodes (reusing the SAME shape domain-scoped self_worth Concepts
already use, generalized from `self_worth:<domain>` to
`<relation>:<target>`), reads/writes a per-(resident, target) arousal
scalar via mechanical bookkeeping (the same class of operation
`dispute_count`/`incident_count` tracking already established in this
arc), and calls the engine's OWN `concept_apply_evidence` to make the
actual belief-update decision. No narrative or depictive content --
every artifact here is a scalar, a Concept name, or a Term formula.
"""
from __future__ import annotations


def mint_target_concept(inner, mt, relation: str, target: str, *, affinity=None):
    """Idempotent: the (mt, relation, target)-scoped Concept, e.g.
    `desire_for:Alice` or `regard_for:Alice`. Mirrors mint_domain_self_
    worth's own idempotent-by-name lookup exactly.

    `affinity` (optional dict, e.g. {"affinity_warm": 1.0}) tags the
    Concept with the small DATA-level affinity shape the generic
    affect-coupling rule (seeds/affect_coupling.json,
    AFFECT_COUPLING_SHAPE_PREREG.md) matches on -- set ONLY at creation,
    the same one-time-init discipline `state`/`external_field` already
    use here. This function does NOT add the couples_affect_to edge --
    that requires a resident's own AffectCoupler, which is an adapter-
    level concern (worlds/bigville_ocelot_adapter.py), not a generic CAN
    operation."""
    concept_name = "%s:%s" % (relation, target)
    for existing in inner.neighbours(mt, "has_concept"):
        if inner.node(existing)["attrs"].get("name") == concept_name:
            return existing
    attrs = {"name": concept_name, "state": 0.0, "external_field": 0.0,
             "identity_field": 0.0}
    if affinity:
        attrs.update(affinity)
    concept = inner.add_node("Concept", attrs)
    inner.add_edge(mt, "has_concept", concept, {})
    return concept


def mint_target_arousal(inner, mt, target: str):
    """Idempotent: the (mt, target)'s shared TargetArousal node -- ONE
    per target, read/written by EVERY relation-Concept toward that
    target, which is the entire mechanism (PREREG Sec2)."""
    for existing in inner.neighbours(mt, "has_target_arousal"):
        if inner.node(existing)["attrs"].get("target") == target:
            return existing
    node = inner.add_node("TargetArousal", {"target": target, "level": 0.0})
    inner.add_edge(mt, "has_target_arousal", node, {})
    return node


def record_targeted_incident(inner, concept, arousal_node, *, evidence: float,
                             intensity: float, base_alpha: float = 0.3,
                             decay: float = 0.7, max_steps: int = 3000) -> dict:
    """ONE incident about a target-scoped Concept, reading and updating the
    SHARED arousal pool for that target (PREREG Sec2):

        effective_alpha = base_alpha * (1 + arousal.level)   [current, pre-update]
        concept <- concept_apply_evidence(evidence, effective_alpha)
        arousal.level <- arousal.level*decay + intensity     [after]

    `intensity` is valence-blind (a fear-, anger-, or excitement-driving
    incident all raise arousal the same way) -- deliberately a SEPARATE
    parameter from `evidence` (which carries the belief's own sign).
    `decay` is a documented, un-fitted physiological time-constant (same
    honesty class as this arc's other constants), NOT an online-estimated
    rate -- checked against EVIDENCE_AND_AUDIENCE_WEIGHTING_RESULTS.md's
    own retracted 1/n anti-pattern before registering (PREREG Sec2): this
    is a fixed multiplicative decay toward a bounded quantity, not a
    shrinking learning rate trying to track a changing statistic.

    Returns {state, arousal_level, effective_alpha}.
    """
    current_arousal = inner.node(arousal_node)["attrs"]["level"]
    effective_alpha = base_alpha * (1.0 + current_arousal)
    inner.concept_apply_evidence(concept, evidence, effective_alpha)
    inner.force_all_dirty()
    inner.run_rules(max_steps)
    new_arousal = current_arousal * decay + intensity
    inner.set_attr(arousal_node, "level", new_arousal)
    return {
        "state": inner.node(concept)["attrs"]["state"],
        "external_field": inner.node(concept)["attrs"]["external_field"],
        "arousal_level": new_arousal,
        "effective_alpha": effective_alpha,
    }


__all__ = ["mint_target_concept", "mint_target_arousal", "record_targeted_incident"]
