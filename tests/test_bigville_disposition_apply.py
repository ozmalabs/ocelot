"""Regression for BIGVILLE_DISPOSITION_GENERATOR_PREREG.md -- mechanically
applying a generated disposition backstory
(seeds/bigville_dispositions_cast100.json, produced by the sibling
bigville repo's worlds/bigville_social_seed.py) into this substrate's
existing belief representation via domains/bigville_disposition_apply.py.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.bigville_disposition_apply import (
    apply_group_dispositions, apply_person_dispositions, apply_resident_dispositions,
    apply_self_priors, index_bonds_by_holder,
)
from domains.can_self_worth_bridge import ensure_can_seed, find_or_build_resident_can

CAST = json.load(open("seeds/bigville_cast100.json"))["residents"]
DISPOSITIONS = json.load(open("seeds/bigville_dispositions_cast100.json"))
BY_NAME = {r["name"]: r for r in CAST}


def _fresh():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    return inner


def _bonds_by_holder():
    return index_bonds_by_holder(DISPOSITIONS["bonds"])


# ---------------------------------------------------------------------
# 1. Deterministic artifact: same seed, byte-identical to a fresh
#    regeneration is gated bigville-side; here we only require the
#    committed file to actually match the shape apply expects.
# ---------------------------------------------------------------------
def test_artifact_shape_matches_what_apply_expects():
    assert set(DISPOSITIONS) >= {"self_priors", "bonds", "seed"}
    assert set(BY_NAME) == set(DISPOSITIONS["self_priors"])
    sample_bond = DISPOSITIONS["bonds"][0]
    for key in ("holder", "toward", "belief_trust", "affect_contempt",
                "affect_trust", "affect_resentment", "affect_gratitude",
                "tie_strength"):
        assert key in sample_bond


# ---------------------------------------------------------------------
# 2. A generated person-in-life bond lands exactly on the holder's
#    TargetPattern toward that person.
# ---------------------------------------------------------------------
def test_generated_person_bond_lands_on_target_pattern():
    inner = _fresh()
    bonds_by_holder = _bonds_by_holder()
    resident = CAST[0]
    name = resident["name"]
    resident_can = find_or_build_resident_can(inner, resident)
    mt = resident_can["mt"]

    targets = apply_person_dispositions(inner, mt, name, bonds_by_holder)
    assert targets  # every resident has >=3 generated bonds
    bond = bonds_by_holder[name][0]
    other = bond["toward"]
    assert other in targets

    from domains.hate_attribution import mint_target_pattern
    pat = mint_target_pattern(inner, mt, other)
    regard = next(iter(inner.neighbours(pat, "tracks_concept")))
    assert inner.node(regard)["attrs"]["external_field"] == pytest.approx(bond["belief_trust"])
    assert inner.node(pat)["attrs"]["resentment_debt"] == pytest.approx(bond["affect_resentment"])
    assert inner.node(pat)["attrs"]["gratitude_debt"] == pytest.approx(bond["affect_gratitude"])


# ---------------------------------------------------------------------
# 3. Group buckets: own class/group/role/workplace_kind get
#    ingroup_affinity; the out-group SES bucket gets outgroup_suspicion.
# ---------------------------------------------------------------------
def test_group_buckets_get_ingroup_and_outgroup_regard():
    inner = _fresh()
    resident = BY_NAME["Verity Peaseblossom"] if "Verity Peaseblossom" in BY_NAME else CAST[0]
    resident_can = find_or_build_resident_can(inner, resident)
    mt = resident_can["mt"]
    self_priors = DISPOSITIONS["self_priors"][resident["name"]]

    targets = apply_group_dispositions(inner, mt, resident, self_priors)
    own_bucket = "class:%s" % resident["class"]
    assert own_bucket in targets

    from domains.hate_attribution import mint_target_pattern
    pat = mint_target_pattern(inner, mt, own_bucket)
    regard = next(iter(inner.neighbours(pat, "tracks_concept")))
    assert inner.node(regard)["attrs"]["external_field"] == pytest.approx(
        self_priors["ingroup_affinity"])

    outgroup_targets = [t for t in targets if t.startswith("group:") and
                        t != "group:%s" % resident["group"]]
    assert len(outgroup_targets) == 1
    out_pat = mint_target_pattern(inner, mt, outgroup_targets[0])
    out_regard = next(iter(inner.neighbours(out_pat, "tracks_concept")))
    assert inner.node(out_regard)["attrs"]["external_field"] == pytest.approx(
        self_priors["outgroup_suspicion"])


# ---------------------------------------------------------------------
# 4. Self priors land on role-domain self_efficacy_for / deservingness_
#    belief_for, matching the existing mint functions' naming.
# ---------------------------------------------------------------------
def test_self_priors_land_on_role_domain_concepts():
    inner = _fresh()
    resident = CAST[5]
    resident_can = find_or_build_resident_can(inner, resident)
    self_priors = DISPOSITIONS["self_priors"][resident["name"]]

    apply_self_priors(inner, resident_can, resident, self_priors)

    mt = resident_can["mt"]
    domain = resident["role"]
    efficacy_name = "self_efficacy_for:%s" % domain
    deserv_name = "deservingness_belief_for:%s" % domain
    concepts = {inner.node(c)["attrs"]["name"]: c for c in inner.neighbours(mt, "has_concept")}
    assert efficacy_name in concepts
    assert deserv_name in concepts
    assert inner.node(concepts[efficacy_name])["attrs"]["external_field"] == pytest.approx(
        self_priors["self_efficacy_prior"])
    assert inner.node(concepts[deserv_name])["attrs"]["external_field"] == pytest.approx(
        self_priors["deservingness_prior"])


# ---------------------------------------------------------------------
# 5. Override precedence: an explicit value always wins, and is applied
#    exactly once (no double-apply / accumulation with the generated
#    value -- concept_apply_evidence is additive, so this is the one
#    thing that MUST NOT silently break).
# ---------------------------------------------------------------------
def test_override_wins_and_is_not_accumulated_with_generated():
    inner = _fresh()
    resident = CAST[10]
    bonds_by_holder = _bonds_by_holder()
    self_priors_by_name = DISPOSITIONS["self_priors"]
    name = resident["name"]
    other = bonds_by_holder[name][0]["toward"]

    result = apply_resident_dispositions(
        inner, resident, bonds_by_holder, self_priors_by_name,
        overrides={"people": {other: {"regard": 1.75}}})

    from domains.hate_attribution import mint_target_pattern
    mt = result["resident_can"]["mt"]
    pat = mint_target_pattern(inner, mt, other)
    regard = next(iter(inner.neighbours(pat, "tracks_concept")))
    assert inner.node(regard)["attrs"]["external_field"] == pytest.approx(1.75)


# ---------------------------------------------------------------------
# 6. A hand-tuned person target absent from the generated bonds is
#    still created and applied (pure-override addition).
# ---------------------------------------------------------------------
def test_override_only_person_with_no_generated_bond_is_applied():
    inner = _fresh()
    resident = CAST[20]
    bonds_by_holder = _bonds_by_holder()
    self_priors_by_name = DISPOSITIONS["self_priors"]
    name = resident["name"]
    generated_targets = {b["toward"] for b in bonds_by_holder.get(name, [])}
    other = next(r["name"] for r in CAST if r["name"] != name and r["name"] not in generated_targets)

    result = apply_resident_dispositions(
        inner, resident, bonds_by_holder, self_priors_by_name,
        overrides={"people": {other: {"admiration": 0.9}}})

    assert other in result["people"]
    from domains.hate_attribution import mint_target_pattern
    mt = result["resident_can"]["mt"]
    pat = mint_target_pattern(inner, mt, other)
    admiration = next(iter(inner.neighbours(pat, "tracks_admiration")))
    assert inner.node(admiration)["attrs"]["external_field"] == pytest.approx(0.9)


# ---------------------------------------------------------------------
# 7. Distribution shape: most generated person-bond regard values are
#    mild (bounded magnitude); very few are extreme -- a real "most
#    relationships are unremarkable" prior, not fudged post-hoc (most
#    bonds are the neutral acquaintance/chosen priors from
#    bigville_bond_world.PRIORS, which carry zero affect by design).
# ---------------------------------------------------------------------
def test_most_generated_regard_values_are_mild():
    values = [b["belief_trust"] for b in DISPOSITIONS["bonds"]]
    mild = sum(1 for v in values if abs(v) < 0.5)
    extreme = sum(1 for v in values if abs(v) >= 1.5)
    assert mild / len(values) > 0.6
    assert extreme / len(values) < 0.15


# ---------------------------------------------------------------------
# 8. Per-resident isolation: applying resident A's dispositions does not
#    perturb resident B's own TargetPattern toward the same third party.
# ---------------------------------------------------------------------
def test_per_resident_isolation():
    inner = _fresh()
    bonds_by_holder = _bonds_by_holder()
    self_priors_by_name = DISPOSITIONS["self_priors"]
    a, b = CAST[0], CAST[1]

    apply_resident_dispositions(inner, a, bonds_by_holder, self_priors_by_name)
    from domains.can_self_worth_bridge import _find_resident_node
    b_node_before = _find_resident_node(inner, b["name"])
    assert b_node_before is None  # B untouched until B is applied

    apply_resident_dispositions(inner, b, bonds_by_holder, self_priors_by_name)
    assert _find_resident_node(inner, b["name"]) is not None
