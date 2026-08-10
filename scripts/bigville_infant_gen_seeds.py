#!/usr/bin/env python3
"""Generate seeds/bigville_infant_care.json -- bigville R22b (block 272000):
INFANT MORTALITY. Well-baby care drops infant mortality (the sharpest inequality
face). This EMITS graph data (seed manifest) -- it is authoring tooling, not agent
runtime (a deletable generator; the seed it writes is the artefact). ZERO new Rust.

The three rules are R22's preventive/public machinery applied to the infant:
  * bi_wellbaby        -- a PRIVATE well-baby visit (affordability-gated), well_baby=1
  * bi_wellbaby_public -- a COUNCIL-FUNDED well-baby visit (treasury pays), well_baby=1
  * bi_onset           -- infant disease onset; effective drop
                          D = max(0, disease_base + (well_baby?0:infant_fragility)),
                          handed to R14 bl_acute -> bl_death. Matches its OWN arm
                          (infant_disease_armed) + guards infant==1 so R22's bd_onset
                          (which reads disease_armed) is never double-fired.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "bigville_infant_care.json")


def lit(v):
    return {"type": "Lit", "value": float(v)}


def attr(node, key):
    # missing-tolerant read (matches the R22 seed's Plus[Attr, Lit 0] idiom).
    return {"type": "Plus",
            "items": [{"type": "Attr", "node": {"type": "Var", "name": node}, "key": key},
                      lit(0.0)]}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def term(t):
    return {"__term__": t}


# ---- coin/funds CONSERVED transfer effects (payer -= fee; doctor += fee) ----
def pay_from(payer, key, doc):
    """payer.<key> -= doc.wellbaby_fee ; doc.coin += doc.wellbaby_fee (conserved)."""
    fee = attr("doc", "wellbaby_fee")
    return [
        ["set_attr", payer, key, term(minus(attr(payer, key), fee))],
        ["set_attr", "doc", "coin", term(plus(attr("doc", "coin"), fee))],
    ]


# ---- the well-baby visit rules (R22 preventive arm applied to the infant) ----
def bi_wellbaby():
    return {
        "name": "bi_wellbaby",
        "batch": False,
        "match": [["p", "has_life", "life"], ["p", "sees_doctor", "doc"]],
        "where": And(
            eq(attr("life", "wellbaby_armed"), lit(1.0)),
            eq(attr("life", "public_health"), lit(0.0)),
            gte(attr("p", "coin"), attr("doc", "wellbaby_fee")),
            eq(attr("p", "dead"), lit(0.0)),
        ),
        "effects": pay_from("p", "coin", "doc") + [
            ["set_attr", "life", "well_baby", 1.0],
            ["set_attr", "life", "wellbaby_armed", 0.0],
        ],
    }


def bi_wellbaby_public():
    return {
        "name": "bi_wellbaby_public",
        "batch": False,
        "match": [["p", "has_life", "life"], ["p", "sees_doctor", "doc"],
                  ["doc", "funded_by", "treasury"]],
        "where": And(
            eq(attr("life", "wellbaby_armed"), lit(1.0)),
            eq(attr("life", "public_health"), lit(1.0)),
            gte(attr("treasury", "funds"), attr("doc", "wellbaby_fee")),
            eq(attr("p", "dead"), lit(0.0)),
        ),
        "effects": pay_from("treasury", "funds", "doc") + [
            ["set_attr", "life", "well_baby", 1.0],
            ["set_attr", "life", "wellbaby_armed", 0.0],
        ],
    }


def bi_onset():
    # D = max(0, disease_base + (well_baby==1 ? 0 : infant_fragility))
    fragility = {
        "type": "IfThenElse",
        "cond": eq(attr("life", "well_baby"), lit(1.0)),
        "then": lit(0.0),
        "other": attr("life", "infant_fragility"),
    }
    drop = {"type": "Max", "items": [lit(0.0),
                                     plus(attr("life", "disease_base"), fragility)]}
    return {
        "name": "bi_onset",
        "batch": False,
        "match": [["p", "has_life", "life"]],
        "where": And(
            eq(attr("life", "infant_disease_armed"), lit(1.0)),
            eq(attr("life", "infant"), lit(1.0)),
            eq(attr("p", "dead"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "life", "illness_amount", term(drop)],
            ["set_attr", "life", "illness_cause", 2.0],
            ["set_attr", "life", "illness_armed", 1.0],
            ["set_attr", "life", "infant_disease_armed", 0.0],
        ],
    }


def build():
    return {
        "id": "bigville_infant_care",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R22b (block 272000) -- INFANT MORTALITY: well-baby care drops "
            "infant mortality, the SHARPEST inequality face. Three rules apply R22's "
            "preventive/public machinery to a HIGH-FRAGILITY R14 infant life stage. "
            "bi_onset computes the effective acute drop D = max(0, disease_base + "
            "(well_baby?0:infant_fragility)) -- an UNSEEN infant takes the fragility "
            "penalty and can die of a shock an adult (or a seen baby) survives; a baby "
            "under regular well-baby care (well_baby=1) takes the base drop only. "
            "bi_wellbaby (PRIVATE, out-of-pocket, affordability-gated -- the poor can't "
            "afford regular visits -> their infants die -> infant mortality TRACKS "
            "wealth) and bi_wellbaby_public (COUNCIL-FUNDED, treasury pays, R9 shape -- "
            "the STRUCTURAL LEVER that dissolves the wealth-infant-mortality gradient). "
            "The fee is a CONSERVED coin transfer; affordability is the where Gte gate. "
            "well_baby removes the fragility penalty exactly as R22's screened removes "
            "progression. Matches its OWN arm (infant_disease_armed) + guards infant==1 "
            "so R22's bd_onset (disease_armed) is never double-fired. NO reward/"
            "punishment token (illness/death are STATES; the RESTORE is well-baby care / "
            "public provision). Composes existing DSL Terms; ZERO new Rust. The infant-"
            "mortality lever is the demographic-transition driver R23 needs."
        ),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": [bi_wellbaby(), bi_wellbaby_public(), bi_onset()],
    }


if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(build(), f, indent=1)
        f.write("\n")
    print("wrote", OUT)
