#!/usr/bin/env python3
"""bigville R22 (block 270000) -- THE DOCTOR: emit seeds/bigville_doctor_care.json.

Health becomes a MONEY-GATED market good. The doctor MODULATES R14's illness
engine (bigville_life_health) -- it does NOT re-implement it. Six graph rules,
every one a DECISION, composing ONLY existing DSL Terms (IfThenElse/Eq/And/Gte/Gt/
Plus/Minus/Max/Min/Attr/Var/Lit + set_attr). ZERO new Rust.

  bd_checkup         PRIVATE preventive  -- patient pays doctor; screened=1
  bd_checkup_public  COUNCIL-FUNDED prev  -- treasury pays doctor; screened=1
  bd_treat           PRIVATE curative    -- patient pays doctor; treated=1
  bd_treat_public    COUNCIL-FUNDED cur   -- treasury pays doctor; treated=1
  bd_onset           disease progression -- effective drop = f(screened, treated),
                                            handed to R14 illness_amount + bl_acute
  bd_recover         recovery tick        -- treated heal fast / untreated slow

The fee is a CONSERVED coin transfer (payer -= fee; doctor += fee). Affordability
is the GATE (a `where` Gte on coin / treasury funds) -- can't afford -> the rule
does not fire -> NO care (the marshmallow dissolution: no myopia attr, it is
AFFORDABILITY). The public-health path (treasury pays) makes the patient's coin
irrelevant -- the systemic lever. Private/public rules are mutually exclusive by
the `public_health` guard. NO reward/punishment token anywhere (illness/death are
STATES; the RESTORE is treatment/public provision).

Run:  python scripts/bigville_doctor_gen_seeds.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_PATH = os.path.join(ROOT, "seeds", "bigville_doctor_care.json")


# ---------------------------------------------------------------- Term helpers
def L(v):
    return {"type": "Lit", "value": float(v)}


def A(var, key):
    # missing-tolerant attr read: Plus[Attr, Lit 0]  (the R14 idiom)
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}, L(0.0)]}


def PLUS(a, b):
    return {"type": "Plus", "items": [a, b]}


def MINUS(a, b):
    return {"type": "Minus", "a": a, "b": b}


def MAXZ(x):
    return {"type": "Max", "items": [L(0.0), x]}


def MIN(a, b):
    return {"type": "Min", "items": [a, b]}


def ITE(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def GTE(a, b):
    return {"type": "Gte", "a": a, "b": b}


def AND(*items):
    return {"type": "And", "items": list(items)}


def T(term):
    return {"__term__": term}


# ------------------------------------------------------------------ transfers
def _pay(payer, fee_src, fee_key, payee):
    """A CONSERVED fee: payer.<balance> -= fee; payee.coin += fee. `payer` is a
    (var, balance_key) pair; the fee lives on `fee_src`.<fee_key>; `payee` is the
    doctor var (gains coin)."""
    pvar, pbal = payer
    fee = A(fee_src, fee_key)
    return [
        ["set_attr", pvar, pbal, T(MINUS(A(pvar, pbal), fee))],
        ["set_attr", payee, "coin", T(PLUS(A(payee, "coin"), fee))],
    ]


# ----------------------------------------------------------------------- rules
def _rules():
    rules = []

    # 1. bd_checkup -- PRIVATE preventive screening (patient pays out of pocket).
    rules.append({
        "name": "bd_checkup",
        "batch": False,
        "match": [["p", "has_life", "life"], ["p", "sees_doctor", "doc"]],
        "where": AND(
            EQ(A("life", "checkup_armed"), L(1.0)),
            EQ(A("life", "public_health"), L(0.0)),
            GTE(A("p", "coin"), A("doc", "checkup_fee")),
            EQ(A("p", "dead"), L(0.0)),
        ),
        "effects": _pay(("p", "coin"), "doc", "checkup_fee", "doc") + [
            ["set_attr", "life", "screened", 1.0],
            ["set_attr", "life", "checkup_armed", 0.0],
        ],
    })

    # 2. bd_checkup_public -- COUNCIL-FUNDED preventive (treasury pays; the lever).
    rules.append({
        "name": "bd_checkup_public",
        "batch": False,
        "match": [["p", "has_life", "life"], ["p", "sees_doctor", "doc"],
                  ["doc", "funded_by", "treasury"]],
        "where": AND(
            EQ(A("life", "checkup_armed"), L(1.0)),
            EQ(A("life", "public_health"), L(1.0)),
            GTE(A("treasury", "funds"), A("doc", "checkup_fee")),
            EQ(A("p", "dead"), L(0.0)),
        ),
        "effects": _pay(("treasury", "funds"), "doc", "checkup_fee", "doc") + [
            ["set_attr", "life", "screened", 1.0],
            ["set_attr", "life", "checkup_armed", 0.0],
        ],
    })

    # 3. bd_treat -- PRIVATE curative treatment (patient pays out of pocket).
    rules.append({
        "name": "bd_treat",
        "batch": False,
        "match": [["p", "has_life", "life"], ["p", "sees_doctor", "doc"]],
        "where": AND(
            EQ(A("life", "treat_armed"), L(1.0)),
            EQ(A("life", "public_health"), L(0.0)),
            GTE(A("p", "coin"), A("doc", "treat_fee")),
            EQ(A("p", "dead"), L(0.0)),
        ),
        "effects": _pay(("p", "coin"), "doc", "treat_fee", "doc") + [
            ["set_attr", "life", "treated", 1.0],
            ["set_attr", "life", "treat_armed", 0.0],
        ],
    })

    # 4. bd_treat_public -- COUNCIL-FUNDED curative (treasury pays; the lever).
    rules.append({
        "name": "bd_treat_public",
        "batch": False,
        "match": [["p", "has_life", "life"], ["p", "sees_doctor", "doc"],
                  ["doc", "funded_by", "treasury"]],
        "where": AND(
            EQ(A("life", "treat_armed"), L(1.0)),
            EQ(A("life", "public_health"), L(1.0)),
            GTE(A("treasury", "funds"), A("doc", "treat_fee")),
            EQ(A("p", "dead"), L(0.0)),
        ),
        "effects": _pay(("treasury", "funds"), "doc", "treat_fee", "doc") + [
            ["set_attr", "life", "treated", 1.0],
            ["set_attr", "life", "treat_armed", 0.0],
        ],
    })

    # 5. bd_onset -- disease PROGRESSION. The effective acute drop is DECIDED here
    #    from the screened/treated state, then handed to R14 (illness_amount +
    #    illness_armed -> bl_acute applies it; bl_death fires or not).
    #    D = max(0, disease_base + (screened?0:progression) - (treated?treat_relief:0))
    penalty = ITE(EQ(A("life", "screened"), L(1.0)), L(0.0), A("life", "progression"))
    relief = ITE(EQ(A("life", "treated"), L(1.0)), A("life", "treat_relief"), L(0.0))
    drop = MAXZ(MINUS(PLUS(A("life", "disease_base"), penalty), relief))
    rules.append({
        "name": "bd_onset",
        "batch": False,
        "match": [["p", "has_life", "life"]],
        "where": AND(
            EQ(A("life", "disease_armed"), L(1.0)),
            EQ(A("p", "dead"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "life", "illness_amount", T(drop)],
            ["set_attr", "life", "illness_cause", 2.0],
            ["set_attr", "life", "illness_armed", 1.0],   # hand to R14 bl_acute
            ["set_attr", "life", "disease_armed", 0.0],
        ],
    })

    # 6. bd_recover -- one recovery tick. Treated -> heals by doctor_care (fast);
    #    untreated -> natural_care (slow). A SEPARATE armed flag (rec_armed) so it
    #    never clashes with R14 bl_recover (which reads heal_armed).
    heal = MIN(A("life", "max_health"),
               PLUS(A("life", "health"),
                    ITE(EQ(A("life", "treated"), L(1.0)),
                        A("life", "doctor_care"), A("life", "natural_care"))))
    rules.append({
        "name": "bd_recover",
        "batch": False,
        "match": [["p", "has_life", "life"]],
        "where": AND(
            EQ(A("life", "rec_armed"), L(1.0)),
            EQ(A("p", "dead"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "life", "health", T(heal)],
            ["set_attr", "life", "rec_armed", 0.0],
        ],
    })

    return rules


def build():
    return {
        "id": "bigville_doctor_care",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R22 (block 270000) -- THE DOCTOR: health as a MONEY-GATED "
            "market good. Six rules MODULATE R14's illness engine "
            "(bigville_life_health): bd_checkup/bd_checkup_public (preventive "
            "screening -> screened, PRIVATE out-of-pocket vs COUNCIL-FUNDED), "
            "bd_treat/bd_treat_public (curative -> treated), bd_onset (effective "
            "acute drop = disease_base + (screened?0:progression) - "
            "(treated?treat_relief:0), handed to R14 illness_amount/bl_acute), "
            "bd_recover (treated heal fast / untreated slow). The fee is a "
            "CONSERVED coin transfer (payer -= fee; doctor += fee); affordability "
            "is the GATE (a where Gte) -- can't afford -> NO care (the marshmallow "
            "dissolution). The public-health path (treasury pays, R9 shape) makes "
            "patient coin irrelevant -> dissolves the wealth-health gradient. NO "
            "reward/punishment token (illness/death are STATES; the RESTORE is "
            "treatment/public provision). Composes existing DSL Terms; ZERO new "
            "Rust."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": _rules(),
    }


def main():
    seed = build()
    with open(SEED_PATH, "w") as f:
        json.dump(seed, f, indent=1)
        f.write("\n")
    print("wrote %s (%d rules)" % (SEED_PATH, len(seed["rules"])))


if __name__ == "__main__":
    main()
