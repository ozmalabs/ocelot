#!/usr/bin/env python3
"""AUTHORING SCRIPT for the bigville R14 (block 262000) LIFE-CYCLE seeds. Emits
`seeds/bigville_life_rearing.json` + `seeds/bigville_life_health.json` +
`seeds/bigville_life_inheritance.json` -- deeply nested Term-tree JSON is
error-prone by hand, so this one-off builder emits it (the `tools/*` authoring
pattern; NOT agent runtime, deletable). It writes ONLY graph data (Rules
composing PRE-EXISTING DSL Terms); it makes NO decision and adds NO Rust.

THE LIFE CYCLE (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §2.9 + §3 R14):
  * REARING -> the three foundational PRIORS (world-safe / others-trust /
    self-worth) shaped by the QUALITY OF CARE. The child holds the REUSED 239000
    window-of-tolerance + co-regulation machinery (its own AffectiveState +
    WindowOfTolerance + Stressor, attended_by a caregiver); rearing IS the 239000
    stress-episode loop UNCHANGED. `bl_come_of_age` maps the 239-produced care
    signal `nurture = widen_count - narrow_count` onto the three adult priors,
    each `clamp01(nat_prior + step*nurture)` -- NATURE (inherited) MODULATED by
    NURTURE (care) -- and mints a rearing-quality `capability` PROXY (R18 school
    not built) + flags adult=1.
  * HEALTH is ONE variable, two timescales. `bl_age` (CHRONIC decline),
    `bl_acute` (ACUTE drop: illness/injury/starvation/exhaustion, RECOVERABLE),
    `bl_recover` (care/rest/doctor restores the SAME variable), and the unifying
    decision `bl_death` (health<=0 -> dead, death_cause = the route). Aging IS
    illness -- same variable, differing only in magnitude/rate.
  * DEATH -> INHERITANCE. On death the estate passes: `bl_inherit_land` (each
    owned Plot's owns edge moves dead->heir -- LAND CONSERVED, R13),
    `bl_inherit_house` (owns_house, R7), `bl_inherit_coin` (lump coin). With NO
    heir (`has_heir=0`) the estate REVERTS to the COUNCIL / commons
    (`bl_inherit_commons_*`) -- ties R13 conservation (transferred, never
    destroyed).

NO reward / punishment token anywhere (relational-ethics: dysregulation, a
mis-set prior, illness, death are STATES, never a badness). ZERO new Rust.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_DIR = os.path.join(ROOT, "seeds")

STEP = 0.03          # prior nudge per unit of (widen - narrow) care signal
CAP_STEP = 0.03      # capability nudge per unit of care signal (R18 proxy)


# ---------------------------------------------------------------- term helpers
def V(name):
    return {"type": "Var", "name": name}


def L(v):
    return {"type": "Lit", "value": float(v)}


def A(node, key):
    """Attr read coerced through Plus[Attr, 0.0] so a MISSING key reads as 0.0
    (the R7/R13 defensive pattern) -- never a match failure on an absent attr."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": V(node), "key": key}, L(0.0)]}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Lte(a, b):
    return {"type": "Lte", "a": a, "b": b}


def And(items):
    return {"type": "And", "items": items}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Plus(items):
    return {"type": "Plus", "items": items}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(items):
    return {"type": "Times", "items": items}


def Min(items):
    return {"type": "Min", "items": items}


def Max(items):
    return {"type": "Max", "items": items}


def clamp01(term):
    """clamp a value into [0, 1] with the pre-existing Min/Max Terms."""
    return Max([L(0.0), Min([L(1.0), term])])


def T(term):
    return {"__term__": term}


def rule(name, match, where, effects, *, batch=False):
    # batch=false -> SEQUENTIAL one-match-per-pass to fixpoint (the R13
    # precedent). Load-bearing for inheritance: each pass moves ONE owns edge
    # (dead->heir), then re-matches the REMAINING owned plots; the coin lump is
    # guarded once via coin_bequeathed. Always semantically safe for these rules.
    return {"name": name, "batch": bool(batch),
            "match": match, "where": where, "effects": effects}


def seed(sid, description, rules):
    return {
        "id": sid, "version": "1.0.0", "depends_on": [], "self_load_only": True,
        "description": description,
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# =============================================================== rearing seed
def rearing_rules():
    # ---- bl_come_of_age: the child MATURES into an adult. The 239000 machinery
    # (reused UNCHANGED) has already shaped the child's WindowOfTolerance through
    # rearing episodes -- widen_count/narrow_count/safety_prior encode the CARE
    # QUALITY. This rule maps the care signal onto the three FOUNDATIONAL priors:
    # nurture = widen_count - narrow_count (positive = co-regulated/secure,
    # negative = neglected/insecure). Each adult prior = clamp01(nature + step*
    # nurture): NATURE (the inherited nat_* set at birth) MODULATED by NURTURE.
    # capability is a rearing-quality PROXY (R18 school not built).
    nurture = Minus(A("wot", "widen_count"), A("wot", "narrow_count"))

    def prior(nat_key):
        return clamp01(Plus([A("child", nat_key), Times([L(STEP), nurture])]))

    bl_come_of_age = rule(
        "bl_come_of_age",
        [["child", "has_window", "wot"], ["child", "has_affective_state", "iaff"]],
        And([
            Eq(A("child", "coa_armed"), L(1.0)),
            Eq(A("child", "matured"), L(0.0)),
        ]),
        [
            ["set_attr", "child", "prior_world_safe", T(prior("nat_world_safe"))],
            ["set_attr", "child", "prior_others_trust", T(prior("nat_others_trust"))],
            ["set_attr", "child", "prior_self_worth", T(prior("nat_self_worth"))],
            ["set_attr", "child", "capability",
             T(clamp01(Plus([A("child", "base_capability"),
                             Times([L(CAP_STEP), nurture])])))],
            ["set_attr", "child", "matured", 1.0],
            ["set_attr", "child", "adult", 1.0],
            ["set_attr", "child", "coa_armed", 0.0],
        ],
    )
    return [bl_come_of_age]


# =============================================================== health seed
def health_rules():
    # HEALTH lives on a LifeState node (has_life edge) -- one variable, two
    # timescales. dead/just_died/death_cause are written onto the PERSON so the
    # inheritance rules (which key off the person's estate edges) read them.

    # ---- bl_age: CHRONIC decline. health -= age_rate per armed period; tags
    # last_cause=1 (the aging route). Floored at 0 (Max).
    bl_age = rule(
        "bl_age",
        [["p", "has_life", "life"]],
        And([Eq(A("life", "age_armed"), L(1.0)), Eq(A("p", "dead"), L(0.0))]),
        [
            ["set_attr", "life", "health",
             T(Max([L(0.0), Minus(A("life", "health"), A("life", "age_rate"))]))],
            ["set_attr", "life", "age", T(Plus([A("life", "age"), L(1.0)]))],
            ["set_attr", "life", "last_cause", 1.0],
            ["set_attr", "life", "age_armed", 0.0],
        ],
    )
    # ---- bl_acute: ACUTE drop -- the SAME variable, larger step. illness_cause
    # (opaque data) tags the route: 2=illness/injury, 3=starvation, 4=exhaustion.
    # RECOVERABLE: if health stays >0, bl_recover can restore it.
    bl_acute = rule(
        "bl_acute",
        [["p", "has_life", "life"]],
        And([Eq(A("life", "illness_armed"), L(1.0)), Eq(A("p", "dead"), L(0.0))]),
        [
            ["set_attr", "life", "health",
             T(Max([L(0.0), Minus(A("life", "health"), A("life", "illness_amount"))]))],
            ["set_attr", "life", "last_cause", T(A("life", "illness_cause"))],
            ["set_attr", "life", "illness_armed", 0.0],
        ],
    )
    # ---- bl_recover: care / rest / the doctor restore the SAME health variable
    # up to max_health (Min cap). The recoverable arm.
    bl_recover = rule(
        "bl_recover",
        [["p", "has_life", "life"]],
        And([Eq(A("life", "heal_armed"), L(1.0)), Eq(A("p", "dead"), L(0.0))]),
        [
            ["set_attr", "life", "health",
             T(Min([A("life", "max_health"),
                    Plus([A("life", "health"), A("life", "care_amount")])]))],
            ["set_attr", "life", "heal_armed", 0.0],
        ],
    )
    # ---- bl_death: the UNIFYING decision. health<=0 -> dead. death_cause is the
    # route that drove health to zero (age / illness / starvation / exhaustion).
    # Writes the flags onto the PERSON (read by inheritance) + the LifeState.
    bl_death = rule(
        "bl_death",
        [["p", "has_life", "life"]],
        And([Lte(A("life", "health"), L(0.0)), Eq(A("p", "dead"), L(0.0))]),
        [
            ["set_attr", "p", "dead", 1.0],
            ["set_attr", "p", "death_cause", T(A("life", "last_cause"))],
            ["set_attr", "p", "just_died", 1.0],
            ["set_attr", "life", "dead", 1.0],
        ],
    )
    return [bl_age, bl_acute, bl_recover, bl_death]


# =============================================================== inheritance seed
def inheritance_rules():
    # On death (dead==1) the estate passes. Every transfer MOVES an edge -- no
    # Plot/House node is minted or destroyed (conservation, R13). The has_heir
    # attr (a structural fact set at ingest -- does this person have kin?) routes
    # heir vs commons; the two branches are DISJOINT (heir edge + has_heir==1 vs
    # has_heir==0).

    # ---- bl_inherit_land: each owned Plot's owns edge moves dead->heir.
    # Sequential (batch=false): one plot per pass, re-matching the remainder,
    # terminating when dead owns no plot. LAND CONSERVED.
    bl_inherit_land = rule(
        "bl_inherit_land",
        [["dead", "owns", "plot"], ["dead", "heir", "h"]],
        And([Eq(A("dead", "dead"), L(1.0)), Eq(A("dead", "has_heir"), L(1.0))]),
        [
            ["del_edge", "dead", "owns", "plot"],
            ["add_edge", "h", "owns", "plot"],
        ],
    )
    # ---- bl_inherit_house: owns_house moves dead->heir (R7 House, conserved).
    bl_inherit_house = rule(
        "bl_inherit_house",
        [["dead", "owns_house", "house"], ["dead", "heir", "h"]],
        And([Eq(A("dead", "dead"), L(1.0)), Eq(A("dead", "has_heir"), L(1.0))]),
        [
            ["del_edge", "dead", "owns_house", "house"],
            ["add_edge", "h", "owns_house", "house"],
        ],
    )
    # ---- bl_inherit_coin: the lump coin passes dead->heir, ONCE (coin_bequeathed
    # guard). Coin conserved (transfer). Integer coin (Plus, no Div).
    bl_inherit_coin = rule(
        "bl_inherit_coin",
        [["dead", "heir", "h"]],
        And([
            Eq(A("dead", "dead"), L(1.0)),
            Eq(A("dead", "has_heir"), L(1.0)),
            Eq(A("dead", "coin_bequeathed"), L(0.0)),
            Gt(A("dead", "coin"), L(0.0)),
        ]),
        [
            ["set_attr", "h", "coin", T(Plus([A("h", "coin"), A("dead", "coin")]))],
            ["set_attr", "dead", "coin", 0.0],
            ["set_attr", "dead", "coin_bequeathed", 1.0],
        ],
    )
    # ---- bl_inherit_commons_land: NO heir (has_heir==0) -> each owned Plot
    # reverts to the COUNCIL / commons (owns moves dead->council). Ties R13
    # conservation: the land is TRANSFERRED, never destroyed. has_council is a
    # structural edge every person carries to the singleton council (ingest).
    bl_inherit_commons_land = rule(
        "bl_inherit_commons_land",
        [["dead", "owns", "plot"], ["dead", "has_council", "council"]],
        And([Eq(A("dead", "dead"), L(1.0)), Eq(A("dead", "has_heir"), L(0.0))]),
        [
            ["del_edge", "dead", "owns", "plot"],
            ["add_edge", "council", "owns", "plot"],
        ],
    )
    # ---- bl_inherit_commons_house: NO heir -> owns_house reverts to the council.
    bl_inherit_commons_house = rule(
        "bl_inherit_commons_house",
        [["dead", "owns_house", "house"], ["dead", "has_council", "council"]],
        And([Eq(A("dead", "dead"), L(1.0)), Eq(A("dead", "has_heir"), L(0.0))]),
        [
            ["del_edge", "dead", "owns_house", "house"],
            ["add_edge", "council", "owns_house", "house"],
        ],
    )
    # ---- bl_inherit_commons_coin: NO heir -> the lump coin escheats to the
    # council, ONCE. Coin conserved.
    bl_inherit_commons_coin = rule(
        "bl_inherit_commons_coin",
        [["dead", "has_council", "council"]],
        And([
            Eq(A("dead", "dead"), L(1.0)),
            Eq(A("dead", "has_heir"), L(0.0)),
            Eq(A("dead", "coin_bequeathed"), L(0.0)),
            Gt(A("dead", "coin"), L(0.0)),
        ]),
        [
            ["set_attr", "council", "coin",
             T(Plus([A("council", "coin"), A("dead", "coin")]))],
            ["set_attr", "dead", "coin", 0.0],
            ["set_attr", "dead", "coin_bequeathed", 1.0],
        ],
    )
    return [bl_inherit_land, bl_inherit_house, bl_inherit_coin,
            bl_inherit_commons_land, bl_inherit_commons_house,
            bl_inherit_commons_coin]


def main():
    rearing = seed(
        "bigville_life_rearing",
        "BIGVILLE R14 (block 262000) -- REARING shapes the three FOUNDATIONAL "
        "priors (world-safe / others-trust / self-worth) from the QUALITY OF CARE, "
        "and coming-of-age. The child holds the REUSED 239000 window-of-tolerance "
        "+ co-regulation machinery (AffectiveState + WindowOfTolerance + Stressor, "
        "attended_by a caregiver); rearing IS the 239000 stress-episode loop "
        "UNCHANGED (regulated caregiver -> widen/secure; neglected -> narrow/"
        "insecure). bl_come_of_age maps the 239-produced care signal nurture = "
        "widen_count - narrow_count onto each adult prior = clamp01(nat_prior + "
        "step*nurture) -- NATURE (inherited) MODULATED by NURTURE (care) -- mints "
        "a rearing-quality `capability` PROXY (R18 school not built) and flags "
        "adult=1. NO reward/punishment token (a prior is a STATE, never a badness). "
        "Composes existing DSL Terms; ZERO new Rust.",
        rearing_rules(),
    )
    health = seed(
        "bigville_life_health",
        "BIGVILLE R14 (block 262000) -- HEALTH is ONE variable, two timescales "
        "(aging = illness). bl_age (CHRONIC decline, tags last_cause=1) + bl_acute "
        "(ACUTE drop -- illness/injury/starvation/exhaustion, illness_cause tags "
        "the route 2/3/4, RECOVERABLE) both reduce the SAME health on a LifeState "
        "node; bl_recover (care/rest/doctor) restores it up to max_health; bl_death "
        "is the UNIFYING decision -- health<=0 -> dead, death_cause = the route "
        "(age/illness/starvation/exhaustion). Aging and illness are the SAME rule "
        "shape (a health delta). NO reward/punishment token (illness/death are "
        "STATES). Composes existing DSL Terms; ZERO new Rust.",
        health_rules(),
    )
    inheritance = seed(
        "bigville_life_inheritance",
        "BIGVILLE R14 (block 262000) -- DEATH -> INHERITANCE. On death (dead==1) "
        "the estate passes: bl_inherit_land (each owned Plot's owns edge moves "
        "dead->heir, sequential -- LAND CONSERVED, R13) + bl_inherit_house "
        "(owns_house, R7) + bl_inherit_coin (lump coin, once via coin_bequeathed). "
        "With NO heir (has_heir==0, a structural fact set at ingest) the estate "
        "REVERTS to the COUNCIL / commons (bl_inherit_commons_land/_house/_coin) -- "
        "ties R13 conservation: the estate is TRANSFERRED, never destroyed. NO rule "
        "mints or destroys a Plot/House node (no add_node/del_node); every transfer "
        "MOVES an edge. Composes existing DSL Terms; ZERO new Rust.",
        inheritance_rules(),
    )
    for s in (rearing, health, inheritance):
        path = os.path.join(SEED_DIR, s["id"] + ".json")
        with open(path, "w") as fh:
            json.dump(s, fh, indent=1)
            fh.write("\n")
        print("wrote", path, "(%d rules)" % len(s["rules"]))


if __name__ == "__main__":
    main()
