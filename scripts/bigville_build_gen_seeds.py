#!/usr/bin/env python3
"""Emit the two bigville R12 (block 260000) CONSTRUCTION seeds:

  * seeds/bigville_build_construct.json -- the construction economy: a BUILDER
    consumes RAW MATERIALS (timber + stone) + LABOUR (a per-tick fixed step whose
    SPEED scales with the builder's CONSTRUCTION skill) over TIME (a multi-tick
    project) to raise a durable BUILDING on an OWNED PLOT (R13 precondition);
    building on ANOTHER'S land is TRESPASS (refused); funding is PERSONAL (coin) or
    a BANK LOAN (R7 reserves -> builder coin + a BuildLoan obligation that ACCRUES
    like a mortgage); an existing building is MODIFIED / ADDED-ON.

  * seeds/bigville_build_mutate.json -- the MUTABLE WORLD (the new capability):
    when a building RISES its plot's map cell is marked `blocked`+`occludes` (a RULE
    mutating the persistent map-belief), and `bbnav_wall_off` SEVERS that cell's
    walkable adjacency so nav (the existing bigville_move_nav flood) RE-ROUTES around
    it; the CHURCH (an institution) EXPANDS iff its donations/funds suffice (a
    grounded lift of R9's fixed size); `bb_demolish` reverts a building so the cells
    revert.

EVERY construction decision is a RULE here -- consume / raise / trespass / fund /
loan / accrue / addon / wall-off / expand / demolish. The adapter only ingests graph
data, arms one-shots, runs `run_rules`, reflects the `built` verdict into the host
grid (occlusion), and reads. Composes ONLY existing DSL Terms (Attr / Plus / Minus /
Times / IDiv / Eq / Gte / Lt / Gt / Not / And / add_node / del_node / add_edge /
del_edge / set_attr) -- ZERO new Rust.

Run:  python scripts/bigville_build_gen_seeds.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")

# activity / good codes this rung uses (opaque data the rules match by value)
CONSTRUCTION = 9.0
TIMBER = 20.0
STONE = 21.0


# ------------------------------------------------------------------ term builders
def V(name):
    return {"type": "Var", "name": name}


def L(v):
    return {"type": "Lit", "value": v}


def A(node, key):
    """Attr with a +0.0 default (a missing key reads 0.0 -- the R13 idiom)."""
    return {"type": "Plus",
            "items": [{"type": "Attr", "node": V(node), "key": key}, L(0.0)]}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def NE(a, b):
    return {"type": "Not", "arg": {"type": "Eq", "a": a, "b": b}}


def GTE(a, b):
    return {"type": "Gte", "a": a, "b": b}


def GT(a, b):
    return {"type": "Gt", "a": a, "b": b}


def LT(a, b):
    return {"type": "Lt", "a": a, "b": b}


def AND(*items):
    return {"type": "And", "items": list(items)}


def PLUS(*items):
    return {"type": "Plus", "items": list(items)}


def MINUS(a, b):
    return {"type": "Minus", "a": a, "b": b}


def TIMES(*items):
    return {"type": "Times", "items": list(items)}


def IDIV(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def T(term):
    """Wrap a term as a computed effect value."""
    return {"__term__": term}


# ==================================================================== construct seed
def construct_seed():
    rules = []

    # ---- bb_loan: issue a construction loan from the R7 bank ------------------
    # builder wants_loan bank, principal>0, bank has reserves, no loan yet ->
    # reserves -= principal, builder coin += principal, mint BuildLoan{balance,rate},
    # accrues like a mortgage (bb_loan_accrue).
    rules.append({
        "name": "bb_loan",
        "batch": False,
        "match": [["builder", "wants_loan", "bank"]],
        "where": AND(
            GTE(A("builder", "loan_principal"), L(1.0)),
            GTE(A("bank", "reserves"), A("builder", "loan_principal")),
            EQ(A("builder", "has_build_loan"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "bank", "reserves",
             T(MINUS(A("bank", "reserves"), A("builder", "loan_principal")))],
            ["set_attr", "builder", "coin",
             T(PLUS(A("builder", "coin"), A("builder", "loan_principal")))],
            ["set_attr", "builder", "has_build_loan", 1.0],
            ["add_node", "loan", "BuildLoan", {
                "balance": T(A("builder", "loan_principal")),
                "rate_bp": T(A("bank", "rate_bp")),
                "accrue_armed": 0.0}],
            ["add_edge", "builder", "has_loan", "loan"],
            ["add_edge", "bank", "issued_loan", "loan"],
            ["del_edge", "builder", "wants_loan", "bank"],
        ],
    })

    # ---- bb_loan_accrue: interest accrues like a mortgage (bf_accrue mirror) ---
    # balance' = IDiv(balance*(10000+rate_bp), 10000) -- multiplicative, INTEGER coin
    # (the cross-frame multiplicative base; the rate is intensional, the balance
    # observed stepped).
    rules.append({
        "name": "bb_loan_accrue",
        "batch": False,
        "match": [["builder", "has_loan", "loan"]],
        "where": EQ(A("loan", "accrue_armed"), L(1.0)),
        "effects": [
            ["set_attr", "loan", "balance",
             T(IDIV(TIMES(A("loan", "balance"),
                          PLUS(L(10000.0), A("loan", "rate_bp"))),
                    L(10000.0)))],
            ["set_attr", "loan", "accrue_armed", 0.0],
        ],
    })

    # ---- bb_fund: pay the build cost from coin (savings OR loan proceeds) ------
    # DISJOINT control: coin < build_cost -> no fire -> funded stays 0 -> no build.
    rules.append({
        "name": "bb_fund",
        "batch": False,
        "match": [["builder", "funds", "plot"]],
        "where": AND(
            EQ(A("plot", "funded"), L(0.0)),
            GTE(A("builder", "coin"), A("plot", "build_cost")),
        ),
        "effects": [
            ["set_attr", "builder", "coin",
             T(MINUS(A("builder", "coin"), A("plot", "build_cost")))],
            ["set_attr", "plot", "funded", 1.0],
            ["del_edge", "builder", "funds", "plot"],
        ],
    })

    # ---- bb_consume: ONE construction tick -----------------------------------
    # builder builds an OWNED, FUNDED, unfinished plot; has a CONSTRUCTION skill and
    # enough timber+stone; a per-tick step consumes materials and advances progress
    # by the SKILL LEVEL (speed prop. skill). tick_armed makes it ONE step per tick
    # (multi-tick TIME). Ablate materials / skill / funding -> no match -> no build.
    rules.append({
        "name": "bb_consume",
        "batch": False,
        "match": [
            ["builder", "builds", "plot"],
            ["builder", "owns", "plot"],
            ["builder", "has_skill", "sk"],
            ["builder", "has_timber", "tw"],
            ["builder", "has_stone", "st"],
        ],
        "where": AND(
            EQ(A("plot", "tick_armed"), L(1.0)),
            EQ(A("plot", "funded"), L(1.0)),
            EQ(A("plot", "built"), L(0.0)),
            LT(A("plot", "progress"), A("plot", "required")),
            EQ(A("sk", "activity"), L(CONSTRUCTION)),
            GTE(A("sk", "level"), L(1.0)),
            EQ(A("tw", "good"), L(TIMBER)),
            EQ(A("st", "good"), L(STONE)),
            GTE(A("tw", "qty"), A("plot", "mat_cost")),
            GTE(A("st", "qty"), A("plot", "mat_cost")),
        ),
        "effects": [
            ["set_attr", "tw", "qty", T(MINUS(A("tw", "qty"), A("plot", "mat_cost")))],
            ["set_attr", "st", "qty", T(MINUS(A("st", "qty"), A("plot", "mat_cost")))],
            ["set_attr", "plot", "progress",
             T(PLUS(A("plot", "progress"), A("sk", "level")))],
            ["set_attr", "plot", "tick_armed", 0.0],
        ],
    })

    # ---- bb_raise: COMPLETE + mutate the map (HEADLINE) -----------------------
    # progress reached required on an owned funded plot -> built=1, mint a Building,
    # and MARK the plot's map cell blocked+occludes (the RULE mutating the map-belief;
    # bbnav_wall_off then severs its adjacency, occlusion re-queries the host grid the
    # adapter syncs from `built`).
    rules.append({
        "name": "bb_raise",
        "batch": False,
        "match": [
            ["builder", "builds", "plot"],
            ["builder", "owns", "plot"],
            ["plot", "on_cell", "c"],
        ],
        "where": AND(
            GTE(A("plot", "progress"), A("plot", "required")),
            EQ(A("plot", "built"), L(0.0)),
            EQ(A("plot", "funded"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "plot", "built", 1.0],
            ["set_attr", "c", "blocked", 1.0],
            ["set_attr", "c", "occludes", 1.0],
            ["add_node", "bldg", "Building", {"size": 1.0, "capacity": 1.0}],
            ["add_edge", "plot", "has_building", "bldg"],
            ["del_edge", "builder", "builds", "plot"],
        ],
    })

    # ---- bb_trespass: building on ANOTHER'S land is refused = TRESPASS ---------
    # builder builds a plot owned by someone ELSE -> trespass flag, build NOT applied.
    # (Unowned land matches neither bb_consume/raise nor this -> refused as absence.)
    rules.append({
        "name": "bb_trespass",
        "batch": False,
        "match": [
            ["builder", "builds", "plot"],
            ["owner", "owns", "plot"],
        ],
        "where": NE(V("builder"), V("owner")),
        "effects": [
            ["set_attr", "builder", "trespass", 1.0],
            ["del_edge", "builder", "builds", "plot"],
        ],
    })

    # ---- bb_addon: MODIFY / ADD-ON an existing building -----------------------
    # the owner extends a building on his own plot, consuming more materials ->
    # size + capacity grow (a durable modification, not a fresh build).
    rules.append({
        "name": "bb_addon",
        "batch": False,
        "match": [
            ["builder", "extends", "bldg"],
            ["plot", "has_building", "bldg"],
            ["builder", "owns", "plot"],
            ["builder", "has_timber", "tw"],
            ["builder", "has_stone", "st"],
        ],
        "where": AND(
            EQ(A("tw", "good"), L(TIMBER)),
            EQ(A("st", "good"), L(STONE)),
            GTE(A("tw", "qty"), A("bldg", "addon_cost")),
            GTE(A("st", "qty"), A("bldg", "addon_cost")),
        ),
        "effects": [
            ["set_attr", "tw", "qty", T(MINUS(A("tw", "qty"), A("bldg", "addon_cost")))],
            ["set_attr", "st", "qty", T(MINUS(A("st", "qty"), A("bldg", "addon_cost")))],
            ["set_attr", "bldg", "size", T(PLUS(A("bldg", "size"), L(1.0)))],
            ["set_attr", "bldg", "capacity", T(PLUS(A("bldg", "capacity"), L(1.0)))],
            ["del_edge", "builder", "extends", "bldg"],
        ],
    })

    return {
        "id": "bigville_build_construct",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": ("BIGVILLE R12 (block 260000) -- CONSTRUCTION economy. A BUILDER "
                        "consumes RAW MATERIALS (timber+stone) + LABOUR (a per-tick step whose "
                        "SPEED = the builder's CONSTRUCTION skill level) over TIME (multi-tick, "
                        "tick_armed) to raise a durable BUILDING on an OWNED, FUNDED plot (R13 "
                        "precondition, bb_consume/bb_raise); building on ANOTHER'S land is refused "
                        "= TRESPASS (bb_trespass; unowned land matches neither -> refused as "
                        "absence). Funding is PERSONAL (coin, bb_fund) or a BANK LOAN (bb_loan: R7 "
                        "reserves -> builder coin + a BuildLoan that ACCRUES like a mortgage, "
                        "bb_loan_accrue = IDiv(balance*(10000+rate_bp),10000), integer coin). An "
                        "existing building is MODIFIED / ADDED-ON (bb_addon: more materials -> "
                        "size+capacity grow). bb_raise ALSO marks the plot's map cell "
                        "blocked+occludes (the map mutation; the mutable-world seed severs the "
                        "adjacency). Composes existing DSL Terms only; ZERO new Rust."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": rules,
    }


# ==================================================================== mutate seed
def mutate_seed():
    rules = []

    # ---- bbnav_wall_off: sever a blocked cell's walkable adjacency ------------
    # THE MUTABLE-WORLD mechanism: any adj edge touching a `blocked` cell is removed,
    # so the existing bigville_move_nav Bellman flood (mv_relax) routes AROUND the new
    # building by construction (unknown = absence). Idempotent (once severed no edge
    # matches). Runs in the SAME substrate as nav -> nav re-queries the mutated belief.
    rules.append({
        "name": "bbnav_wall_off",
        "batch": False,
        "match": [["a", "adj", "b"]],
        "where": GTE(PLUS(A("a", "blocked"), A("b", "blocked")), L(1.0)),
        "effects": [["del_edge", "a", "adj", "b"]],
    })

    # ---- bb_church_expand: INSTITUTIONAL expansion, income-gated ---------------
    # the church (an Institution occupying a cell) EXPANDS iff its donations/funds
    # cover the cost -> capacity + size grow, funds drop (a grounded lift of R9's
    # fixed size). Control: funds < expand_cost -> no fire -> no expansion.
    rules.append({
        "name": "bb_church_expand",
        "batch": False,
        "match": [["inst", "occupies", "c"]],
        "where": AND(
            EQ(A("inst", "expand_armed"), L(1.0)),
            GTE(A("inst", "funds"), A("inst", "expand_cost")),
        ),
        "effects": [
            ["set_attr", "inst", "funds",
             T(MINUS(A("inst", "funds"), A("inst", "expand_cost")))],
            ["set_attr", "inst", "capacity", T(PLUS(A("inst", "capacity"), L(1.0)))],
            ["set_attr", "inst", "size", T(PLUS(A("inst", "size"), L(1.0)))],
            ["set_attr", "inst", "expand_armed", 0.0],
        ],
    })

    # ---- bb_demolish: remove a building -> the cells REVERT --------------------
    # clears built + the cell's blocked/occludes and drops the Building; the adapter
    # re-establishes the cell's walkable adjacency (mechanical re-ingest) so nav
    # routes through again -- "remove it -> the cells revert".
    rules.append({
        "name": "bb_demolish",
        "batch": False,
        "match": [
            ["plot", "has_building", "bldg"],
            ["plot", "on_cell", "c"],
        ],
        "where": EQ(A("bldg", "demolish_armed"), L(1.0)),
        "effects": [
            ["set_attr", "plot", "built", 0.0],
            ["set_attr", "c", "blocked", 0.0],
            ["set_attr", "c", "occludes", 0.0],
            ["del_edge", "plot", "has_building", "bldg"],
            ["del_node", "bldg"],
        ],
    })

    return {
        "id": "bigville_build_mutate",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": ("BIGVILLE R12 (block 260000) -- the MUTABLE WORLD (the new capability). "
                        "bbnav_wall_off SEVERS the walkable adjacency of any `blocked` map cell so "
                        "the existing bigville_move_nav Bellman flood RE-ROUTES around a new "
                        "building (the map-belief is graph data a rule mutated; nav re-queries it). "
                        "bb_church_expand grows an Institution's capacity+size IFF its "
                        "donations/funds suffice (a grounded lift of R9's fixed size; control = "
                        "funds<cost -> no expansion). bb_demolish reverts a building (clears "
                        "built/blocked/occludes, drops the Building) so the cells revert. Composes "
                        "existing DSL Terms only; ZERO new Rust."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": rules,
    }


def main():
    for seed in (construct_seed(), mutate_seed()):
        path = os.path.join(SEEDS, seed["id"] + ".json")
        with open(path, "w") as fh:
            json.dump(seed, fh, indent=1)
            fh.write("\n")
        print("wrote", path, "(%d rules)" % len(seed["rules"]))


if __name__ == "__main__":
    main()
