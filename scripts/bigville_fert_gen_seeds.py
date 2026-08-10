#!/usr/bin/env python3
"""bigville R23 (block 271000) -- FERTILITY: emit seeds/bigville_fert_decide.json.

Fertility becomes a graph DECISION, NEVER a rule keyed on wealth. Three staged
one-shot rules (armed -> clear, guaranteed termination) compose ONLY existing DSL
Terms (IfThenElse/Eq/And/Gte/Plus/Minus/Times/Max/Min/Div/Attr/Var/Lit +
set_attr). ZERO new Rust.

  bf_oldage             the old-age-security (insurance) motive:
                          oldage_motive = safety_net==1 ? 0 : oldage_value
                        No pension/safety-net -> children as old-age insurance
                        (motive ON); add a safety net (R9) -> motive OFF.

  bf_quantity_quality   the Becker decision (decision_value = benefit - cost):
                          decision_value  = base_target + child_labour_benefit
                                            + oldage_motive - school_cost - opp_cost
                          desired_surviving = max(floor, decision_value)
                        Cheap children (no school, child labour useful) -> more
                        (quantity); expensive children (schooling R18 + the
                        mother's opportunity cost) -> fewer, invested (quality).

  bf_mortality_replace  the demographic-transition engine (ties R22):
                          survival  = max(eps, 1 - mortality)
                          fertility = desired_surviving / survival
                        High child mortality (poor, no R22 well-baby care) ->
                        more births to ensure some survive; ablate mortality
                        (free public health, R22's lever) -> fertility falls.

`fertility` is the decision_value read-off (a desired-births RATE). Actual birth
stays the honest R14 ingest boundary but is now GATED/scaled by this decision (the
adapter's beget() mints floor(fertility) children). NO wealth/coin/class attr is
read by ANY rule -- the wealth->fertility gradient, if any, comes THROUGH the
mechanism inputs only (the anti-tuning source-audit). NO reward/punishment token.

Run:  python scripts/bigville_fert_gen_seeds.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_PATH = os.path.join(ROOT, "seeds", "bigville_fert_decide.json")


# ---------------------------------------------------------------- Term helpers
def L(v):
    return {"type": "Lit", "value": float(v)}


def A(var, key):
    # missing-tolerant attr read: Plus[Attr, Lit 0]  (the R14/R22 idiom)
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}, L(0.0)]}


def PLUS(a, b):
    return {"type": "Plus", "items": [a, b]}


def MINUS(a, b):
    return {"type": "Minus", "a": a, "b": b}


def MAXV(a, b):
    return {"type": "Max", "items": [a, b]}


def DIV(a, b):
    return {"type": "Div", "a": a, "b": b}


def ITE(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def AND(*items):
    return {"type": "And", "items": list(items)}


def T(term):
    return {"__term__": term}


# ----------------------------------------------------------------------- rules
def _rules():
    rules = []

    # 1. bf_oldage -- the old-age-security (insurance) motive. No safety net ->
    #    children ARE the pension (motive ON); a safety net (R9) -> motive OFF.
    #    Arms stage 2 (qq_armed). Reads NO wealth -- only safety_net/oldage_value.
    oldage_motive = ITE(EQ(A("f", "safety_net"), L(1.0)), L(0.0), A("f", "oldage_value"))
    rules.append({
        "name": "bf_oldage",
        "batch": False,
        "match": [["p", "has_fertility", "f"]],
        "where": AND(EQ(A("f", "decide_armed"), L(1.0))),
        "effects": [
            ["set_attr", "f", "oldage_motive", T(oldage_motive)],
            ["set_attr", "f", "qq_armed", 1.0],
            ["set_attr", "f", "decide_armed", 0.0],
        ],
    })

    # 2. bf_quantity_quality -- the Becker decision: decision_value = benefit - cost.
    #    benefit = base_target + child_labour_benefit + oldage_motive
    #    cost    = school_cost + opp_cost      (R18 schooling + the mother's opp cost)
    #    desired_surviving = max(floor, decision_value).
    #    Cheap children -> more (quantity); expensive -> fewer, invested (quality).
    #    Reads the stage-1 output oldage_motive (already set). NO wealth.
    benefit = PLUS(PLUS(A("f", "base_target"), A("f", "child_labour_benefit")),
                   A("f", "oldage_motive"))
    cost = PLUS(A("f", "school_cost"), A("f", "opp_cost"))
    decision_value = MINUS(benefit, cost)
    desired = MAXV(A("f", "floor"), decision_value)
    rules.append({
        "name": "bf_quantity_quality",
        "batch": False,
        "match": [["p", "has_fertility", "f"]],
        "where": AND(EQ(A("f", "qq_armed"), L(1.0))),
        "effects": [
            ["set_attr", "f", "decision_value", T(decision_value)],
            ["set_attr", "f", "desired_surviving", T(desired)],
            ["set_attr", "f", "mort_armed", 1.0],
            ["set_attr", "f", "qq_armed", 0.0],
        ],
    })

    # 3. bf_mortality_replace -- the demographic-transition engine (ties R22):
    #    survival  = max(eps, 1 - mortality)      (eps guards Div-by-zero)
    #    fertility = desired_surviving / survival (replacement -> overshoot births)
    #    High mortality -> more births; ablate mortality (public health) -> falls.
    #    Reads the stage-2 output desired_surviving (already set). NO wealth.
    survival = MAXV(A("f", "eps"), MINUS(L(1.0), A("f", "mortality")))
    fertility = DIV(A("f", "desired_surviving"), survival)
    rules.append({
        "name": "bf_mortality_replace",
        "batch": False,
        "match": [["p", "has_fertility", "f"]],
        "where": AND(EQ(A("f", "mort_armed"), L(1.0))),
        "effects": [
            ["set_attr", "f", "survival", T(survival)],
            ["set_attr", "f", "fertility", T(fertility)],
            ["set_attr", "f", "mort_armed", 0.0],
        ],
    })

    return rules


def build():
    return {
        "id": "bigville_fert_decide",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R23 (block 271000) -- FERTILITY: the quantity-quality "
            "decision as a GRAPH DECISION, NEVER keyed on wealth. Three staged "
            "one-shot rules: bf_oldage (oldage_motive = safety_net?0:oldage_value "
            "-- the old-age-security insurance motive, R9), bf_quantity_quality "
            "(decision_value = base_target + child_labour_benefit + oldage_motive "
            "- school_cost - opp_cost; desired_surviving = max(floor, "
            "decision_value) -- the Becker quantity-quality tradeoff, R18 school + "
            "mother opp cost), bf_mortality_replace (survival = max(eps, "
            "1-mortality); fertility = desired_surviving / survival -- the "
            "demographic-transition replacement, ties R22 child mortality). "
            "`fertility` is a desired-births RATE; birth stays the honest R14 "
            "ingest boundary but GATED by this decision. NO wealth/coin/class attr "
            "is read by ANY rule: the wealth->fertility gradient, if any, must come "
            "THROUGH the mechanism inputs (the anti-tuning source-audit). NO "
            "reward/punishment token. Composes existing DSL Terms; ZERO new Rust."),
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
