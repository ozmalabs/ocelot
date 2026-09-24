"""bigville_disposition_apply -- mechanically APPLIES a generated
disposition backstory into this substrate's EXISTING belief
representation (regard_for / trust / resentment_debt / self_efficacy_for
/ etc, all built across the expanded-emotional-system phases A-G plus
RESIDENT_TRUST_PREREG.md / SELF_EFFICACY_PREREG.md / ENVY_PREREG.md).

Generation lives entirely in the sibling repo
(`../bigville/worlds/bigville_social_seed.py`) -- pure-data sampling of
who's in a resident's life (a homophily-biased slice of the same cast,
reusing bigville_bond_world's own PRIORS kind vocabulary verbatim) and
self/group priors (self-efficacy, deservingness, in-/out-group
affinity). `docs/features/bigville.md`'s adapter boundary: Ocelot no
longer owns a second Bigville world, so nothing here samples or decides
anything -- every value applied was already a decided datum in the
generator's exported JSON (`seeds/bigville_dispositions_cast100.json`).

Pure world-adapter code (CLAUDE.md's architecture rule): for every
(target, aspect) this mechanically resolves ONE value (override wins,
else the generated one -- a dict-merge, not a branch over graph state)
and applies it via the EXISTING mint_*/concept_apply_evidence primitives
this arc has used since Phase A. concept_apply_evidence is ADDITIVE
(h += alpha*evidence, confirmed in runners/dsl/src/py.rs) -- so a
(target, aspect) is resolved to exactly ONE value BEFORE any
concept_apply_evidence call is made, never generated-then-overridden as
two separate calls (that would silently sum instead of override).
"""
from __future__ import annotations

from domains.can_self_worth_bridge import find_or_build_resident_can
from domains.envy import mint_domain_deservingness_belief
from domains.hate_attribution import mint_target_pattern
from domains.resident_trust import mint_trust_beliefs
from domains.self_efficacy import mint_domain_self_efficacy

_OUTGROUP_OF = {"low": "high", "high": "low"}

_CONCEPT_EDGE = {
    "regard": "tracks_concept", "removal_desire": "tracks_removal_desire",
    "pity": "tracks_pity", "admiration": "tracks_admiration",
    "devaluation": "tracks_devaluation", "controllability": "tracks_controllability",
}
_ATTR_ASPECTS = ("resentment_debt", "gratitude_debt")


def index_bonds_by_holder(bonds):
    """{holder_name: [bond, ...]} -- mechanical grouping of the generator's
    own flat bonds list, no decision."""
    out = {}
    for bond in bonds:
        out.setdefault(bond["holder"], []).append(bond)
    return out


def _outgroup_bucket(resident):
    """The one salient out-group SES-tier bucket for `outgroup_suspicion`
    (Tajfel, Billig, Bundy & Flament 1971's minimal group paradigm -- an
    arbitrary bucket is sufficient, no richer justification required).
    Deterministic from the resident's own already-known fields, not a
    runtime coin-flip."""
    tier = resident["group"]
    if tier in _OUTGROUP_OF:
        return "group:%s" % _OUTGROUP_OF[tier]
    return "group:%s" % ("high" if sum(map(ord, resident["name"])) % 2 else "low")


def _resolve_person_aspects(bond, override_aspects):
    generated = {
        "regard": bond["belief_trust"], "devaluation": bond["affect_contempt"],
        "trust": bond["affect_trust"], "resentment_debt": bond["affect_resentment"],
        "gratitude_debt": bond["affect_gratitude"], "arousal": bond["tie_strength"],
    }
    generated.update(override_aspects or {})
    return generated


def _apply_pattern_aspects(inner, mt, target, aspects):
    pat = mint_target_pattern(inner, mt, target)
    for aspect, value in aspects.items():
        if aspect in _ATTR_ASPECTS:
            inner.set_attr(pat, aspect, value)
        elif aspect == "trust":
            trust = mint_trust_beliefs(inner, mt, target)
            inner.concept_apply_evidence(trust["competence"], value, 1.0)
            inner.concept_apply_evidence(trust["willingness"], value, 1.0)
        elif aspect == "arousal":
            arousal = next(iter(inner.neighbours(pat, "tracks_arousal")))
            inner.set_attr(arousal, "level", value)
        elif aspect in _CONCEPT_EDGE:
            concept = next(iter(inner.neighbours(pat, _CONCEPT_EDGE[aspect])))
            inner.concept_apply_evidence(concept, value, 1.0)
    return pat


def apply_person_dispositions(inner, mt, resident_name, bonds_by_holder, people_overrides=None):
    """Every generated people-in-life bond FROM `resident_name`, plus any
    hand-tuned person target with no generated bond at all (a pure
    override addition). Returns the list of applied target names."""
    people_overrides = people_overrides or {}
    bonds_by_target = {b["toward"]: b for b in bonds_by_holder.get(resident_name, [])}
    targets = set(bonds_by_target) | set(people_overrides)
    for target in targets:
        bond = bonds_by_target.get(target)
        generated = _resolve_person_aspects(bond, people_overrides.get(target)) if bond \
            else dict(people_overrides[target])
        _apply_pattern_aspects(inner, mt, target, generated)
    return sorted(targets)


def apply_group_dispositions(inner, mt, resident, self_priors, group_overrides=None):
    """The resident's own class/group/role/workplace_kind buckets get
    `ingroup_affinity`; ONE out-group SES-tier bucket gets
    `outgroup_suspicion`. Bucket SELECTION reads only the resident's own
    already-known categorical fields -- mechanical, not a graph-state
    decision. Any hand-tuned bucket not in this set is applied too."""
    group_overrides = group_overrides or {}
    ingroup = self_priors["ingroup_affinity"]
    outgroup = self_priors["outgroup_suspicion"]
    generated = {"%s:%s" % (dim, resident[dim]): {"regard": ingroup}
                 for dim in ("class", "group", "role", "workplace_kind")}
    generated[_outgroup_bucket(resident)] = {"regard": outgroup}
    targets = set(generated) | set(group_overrides)
    for target in targets:
        aspects = dict(generated.get(target, {}))
        aspects.update(group_overrides.get(target, {}))
        _apply_pattern_aspects(inner, mt, target, aspects)
    return sorted(targets)


def apply_self_priors(inner, resident_can, resident, self_priors, self_overrides=None):
    """Domain-scoped self-belief priors, domain = the resident's own role
    (Bandura: self-efficacy/deservingness are task-specific -- the
    resident's actual occupation IS the natural domain)."""
    domain = resident["role"]
    resolved = {"self_efficacy": self_priors["self_efficacy_prior"],
                "deservingness": self_priors["deservingness_prior"]}
    resolved.update(self_overrides or {})
    if "self_efficacy" in resolved:
        concept = mint_domain_self_efficacy(inner, resident_can, domain)
        inner.concept_apply_evidence(concept, resolved["self_efficacy"], 1.0)
    if "deservingness" in resolved:
        concept = mint_domain_deservingness_belief(inner, resident_can, domain)
        inner.concept_apply_evidence(concept, resolved["deservingness"], 1.0)
    return resolved


def apply_resident_dispositions(inner, resident, bonds_by_holder, self_priors_by_name,
                                overrides=None, max_steps=3000):
    """The full disposition backstory for ONE resident: people-in-life
    bonds, group buckets, and role-domain self-priors, with `overrides`
    (optional {"people": {target: {aspect: value}}, "groups": {...},
    "self": {aspect: value}}) resolved BEFORE any evidence is applied, so
    an explicit value always wins and every non-overridden (target,
    aspect) still gets its generated value. Runs the fixpoint once at the
    end (matches every other multi-write apply function in this arc).
    """
    overrides = overrides or {}
    resident_can = find_or_build_resident_can(inner, resident, max_steps=max_steps)
    mt = resident_can["mt"]
    name = resident["name"]

    people = apply_person_dispositions(inner, mt, name, bonds_by_holder,
                                       overrides.get("people"))
    groups = apply_group_dispositions(inner, mt, resident,
                                      self_priors_by_name[name], overrides.get("groups"))
    self_aspects = apply_self_priors(inner, resident_can, resident,
                                     self_priors_by_name[name], overrides.get("self"))

    inner.force_all_dirty()
    inner.add_node("NativeBigvilleDispositionReceipt", {
        "schema": "native_bigville_disposition_receipt_v1",
        "cluster": "bigville_disposition_apply.settlement",
        "provenance": "native_rule_readback:bigville_dispositions",
        "native_rule": "bigville_dispositions_native_rules",
        "native_steps": ["apply_dispositions", "force_all_dirty", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    inner.run_rules(max_steps)
    return {"resident_can": resident_can, "people": people, "groups": groups,
            "self": self_aspects}


__all__ = [
    "index_bonds_by_holder", "apply_person_dispositions", "apply_group_dispositions",
    "apply_self_priors", "apply_resident_dispositions",
]
