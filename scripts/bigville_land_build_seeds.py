#!/usr/bin/env python3
"""AUTHORING SCRIPT for the bigville R13 (block 261000) LAND seeds. Emits
`seeds/bigville_land_market.json` + `seeds/bigville_land_tenure.json` -- deeply
nested Term-tree JSON is error-prone by hand, so this one-off builder emits it
(the `tools/*` authoring-script pattern; NOT agent runtime, deletable). It writes
ONLY graph data (Rules composing PRE-EXISTING DSL Terms); it makes NO decision and
adds NO Rust.

LAND is the foundational scarce asset: FINITE / NON-PRODUCED / CONSERVED. Plots are
nodes, `owns` is an edge, and Sigma(Plot) is INVARIANT -- no rule mints or destroys a
Plot node (no add_node/del_node anywhere); acquisition only MOVES `owns` edges.
Acquired by BUY (seller-priced market), CLAIM (unowned frontier, first-come homestead)
or GRANT (council). The structural levers that reopen land to the landless -- land TAX
(-> forfeit -> council -> grant), ENCLOSURE-REVERSAL (owned -> frontier commons) -- are
rules too. Foreclosure transfers the LAND (grounds R7's proxied land-as-collateral by
keying off R7's own `foreclosed` flag).
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_DIR = os.path.join(ROOT, "seeds")


# ---------------------------------------------------------------- term helpers
def V(name):
    return {"type": "Var", "name": name}


def L(v):
    return {"type": "Lit", "value": float(v)}


def A(node, key):
    """Attr read coerced through Plus[Attr, 0.0] so a MISSING key reads as 0.0
    (the R7 defensive pattern) -- never a match failure on an absent attr."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": V(node), "key": key}, L(0.0)]}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def NodeEq(a, b):
    """Identity comparison of two bound node Vars (Eq compares Value::Node by id)."""
    return {"type": "Eq", "a": V(a), "b": V(b)}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def And(items):
    return {"type": "And", "items": items}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Plus(items):
    return {"type": "Plus", "items": items}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def T(term):
    return {"__term__": term}


def rule(name, match, where, effects):
    # batch=false -> SEQUENTIAL one-match-per-pass to fixpoint (the
    # retire_duplicate_gap precedent). Load-bearing: a market SWEEP must spend a
    # shrinking BUDGET (bl_buy re-evaluates coin>=price after each purchase) and a
    # CLAIM must be FIRST-COME (the first claimant sets owned=1, blocking the rest);
    # the engine's derived snapshot-batch proof does NOT model the coin coupling, so
    # we pin sequential explicitly. Always semantically safe for these rules.
    return {"name": name, "batch": False,
            "match": match, "where": where, "effects": effects}


def seed(sid, description, rules):
    return {
        "id": sid, "version": "1.0.0", "depends_on": [], "self_load_only": True,
        "description": description,
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# =============================================================== market seed
def market_rules():
    # ---- bl_buy: seller-priced MARKET purchase. The `wants_to_buy` edge IS the
    # arming (a rich buyer with many such edges buys each affordable plot in one
    # fixpoint, subject to a shrinking budget); the DECISION (afford? not self?
    # listed?) is this rule. Transfers coin AND moves the `owns` edge (Sigma
    # conserved).
    bl_buy = rule(
        "bl_buy",
        [["buyer", "wants_to_buy", "plot"], ["seller", "owns", "plot"]],
        And([
            Not(NodeEq("buyer", "seller")),
            Eq(A("plot", "for_sale"), L(1.0)),
            Gte(A("buyer", "coin"), A("plot", "price")),
        ]),
        [
            ["set_attr", "buyer", "coin",
             T(Minus(A("buyer", "coin"), A("plot", "price")))],
            ["set_attr", "seller", "coin",
             T(Plus([A("seller", "coin"), A("plot", "price")]))],
            ["del_edge", "seller", "owns", "plot"],
            ["add_edge", "buyer", "owns", "plot"],
            ["set_attr", "plot", "for_sale", 0.0],
            ["set_attr", "plot", "owned", 1.0],
            ["del_edge", "buyer", "wants_to_buy", "plot"],
        ],
    )
    # ---- bl_buy_fail: the CAN'T-AFFORD control. Same match; coin < price -> NO
    # transfer, no ownership change (a landless/poor buyer cannot buy into the
    # market by wanting to).
    bl_buy_fail = rule(
        "bl_buy_fail",
        [["buyer", "wants_to_buy", "plot"], ["seller", "owns", "plot"]],
        And([
            Not(NodeEq("buyer", "seller")),
            Eq(A("plot", "for_sale"), L(1.0)),
            Lt(A("buyer", "coin"), A("plot", "price")),
        ]),
        [
            ["set_attr", "buyer", "buy_failed", 1.0],
            ["del_edge", "buyer", "wants_to_buy", "plot"],
        ],
    )
    # ---- bl_claim: HOMESTEAD unowned FRONTIER land (first-come). Guard
    # owned==0 -> once one claimant takes it, a second's `wants_to_claim` to the
    # SAME plot no longer matches (first-come is graph-native). No node minted:
    # a pre-existing frontier Plot merely GAINS an `owns` edge.
    bl_claim = rule(
        "bl_claim",
        [["claimant", "wants_to_claim", "plot"]],
        And([
            Eq(A("plot", "frontier"), L(1.0)),
            Eq(A("plot", "owned"), L(0.0)),
        ]),
        [
            ["add_edge", "claimant", "owns", "plot"],
            ["set_attr", "plot", "owned", 1.0],
            ["set_attr", "plot", "frontier", 0.0],
            ["del_edge", "claimant", "wants_to_claim", "plot"],
        ],
    )
    # ---- bl_grant: COUNCIL grant (R9). The council (is_council==1) holds a plot
    # and a `granted_to` edge names the recipient -> the `owns` edge MOVES
    # council -> recipient (Sigma conserved). The structural lever + the third
    # acquisition mode.
    bl_grant = rule(
        "bl_grant",
        [["council", "owns", "plot"], ["plot", "granted_to", "recipient"]],
        Eq(A("council", "is_council"), L(1.0)),
        [
            ["del_edge", "council", "owns", "plot"],
            ["add_edge", "recipient", "owns", "plot"],
            ["set_attr", "plot", "owned", 1.0],
            ["del_edge", "plot", "granted_to", "recipient"],
        ],
    )
    return [bl_buy, bl_buy_fail, bl_claim, bl_grant]


# =============================================================== tenure seed
def tenure_rules():
    # ---- bl_build: construction REQUIRES owning the plot (R12 precondition,
    # grounded here). Matches builder-owns-plot + wants_to_build -> built.
    bl_build = rule(
        "bl_build",
        [["builder", "wants_to_build", "plot"], ["builder", "owns", "plot"]],
        Eq(A("plot", "built"), L(0.0)),
        [
            ["set_attr", "plot", "built", 1.0],
            ["del_edge", "builder", "wants_to_build", "plot"],
        ],
    )
    # ---- bl_build_trespass: building on ANOTHER'S land is refused = TRESPASS.
    # Owner != builder -> flag trespass, build NOT applied. (Building on unowned
    # frontier matches NEITHER rule -> built stays 0: refusal as absence.)
    bl_build_trespass = rule(
        "bl_build_trespass",
        [["builder", "wants_to_build", "plot"], ["owner", "owns", "plot"]],
        Not(NodeEq("builder", "owner")),
        [
            ["set_attr", "builder", "trespass", 1.0],
            ["del_edge", "builder", "wants_to_build", "plot"],
        ],
    )
    # ---- bl_foreclose_land: FORECLOSURE transfers the LAND. Keys off R7's OWN
    # `foreclosed` flag (the R7 rule made the decision, over the house); R13
    # extends the consequence to the LAND parcel the same mortgage is
    # `secured_on_plot` -- grounding R7's proxied land-as-ultimate-collateral.
    # The `owns` edge MOVES debtor -> bank (Sigma conserved). Once-only via
    # land_transferred.
    bl_foreclose_land = rule(
        "bl_foreclose_land",
        [["debtor", "owns", "plot"], ["mort", "secured_on_plot", "plot"],
         ["bank", "issued", "mort"]],
        And([
            Eq(A("mort", "foreclosed"), L(1.0)),
            Eq(A("mort", "land_transferred"), L(0.0)),
        ]),
        [
            ["set_attr", "mort", "land_transferred", 1.0],
            ["del_edge", "debtor", "owns", "plot"],
            ["add_edge", "bank", "owns", "plot"],
        ],
    )
    # ---- bl_land_tax: the GEORGIST land tax lever. An owner pays `tax` per owned
    # plot to the jurisdiction (`taxed_by`), iff affordable. Integer coin.
    bl_land_tax = rule(
        "bl_land_tax",
        [["owner", "owns", "plot"], ["plot", "taxed_by", "council"]],
        And([
            Eq(A("plot", "tax_armed"), L(1.0)),
            Gte(A("owner", "coin"), A("plot", "tax")),
        ]),
        [
            ["set_attr", "owner", "coin",
             T(Minus(A("owner", "coin"), A("plot", "tax")))],
            ["set_attr", "council", "coin",
             T(Plus([A("council", "coin"), A("plot", "tax")]))],
            ["set_attr", "plot", "tax_armed", 0.0],
        ],
    )
    # ---- bl_tax_forfeit: can't pay the tax -> the plot FORFEITS to the council
    # (the redistribution SOURCE -- an over-concentrated / idle holding returns to
    # the commons pool the council then grants). `owns` MOVES owner -> council.
    bl_tax_forfeit = rule(
        "bl_tax_forfeit",
        [["owner", "owns", "plot"], ["plot", "taxed_by", "council"]],
        And([
            Eq(A("plot", "tax_armed"), L(1.0)),
            Lt(A("owner", "coin"), A("plot", "tax")),
        ]),
        [
            ["del_edge", "owner", "owns", "plot"],
            ["add_edge", "council", "owns", "plot"],
            ["set_attr", "plot", "tax_armed", 0.0],
            ["set_attr", "plot", "forfeited", 1.0],
        ],
    )
    # ---- bl_enclosure_reversal: ENCLOSURE-REVERSAL. An owned plot reverts to
    # unowned FRONTIER commons (the `owns` edge is removed; owned->0, frontier->1)
    # -> a landless claimant can now CLAIM it. The third structural lever.
    bl_enclosure_reversal = rule(
        "bl_enclosure_reversal",
        [["owner", "owns", "plot"]],
        Eq(A("plot", "revert_armed"), L(1.0)),
        [
            ["del_edge", "owner", "owns", "plot"],
            ["set_attr", "plot", "owned", 0.0],
            ["set_attr", "plot", "frontier", 1.0],
            ["set_attr", "plot", "revert_armed", 0.0],
        ],
    )
    return [bl_build, bl_build_trespass, bl_foreclose_land,
            bl_land_tax, bl_tax_forfeit, bl_enclosure_reversal]


def main():
    market = seed(
        "bigville_land_market",
        "BIGVILLE R13 (block 261000) -- LAND ACQUISITION: the three modes by which "
        "a plot changes hands, all graph-native. bl_buy (seller-priced MARKET, "
        "transfers coin + moves the `owns` edge, Sigma conserved) + bl_buy_fail "
        "(the CAN'T-AFFORD control: coin<price -> no transfer). bl_claim "
        "(HOMESTEAD unowned FRONTIER land, first-come via the owned==0 guard: a "
        "second claimant to the same plot no longer matches). bl_grant (COUNCIL "
        "grant, R9: the council holds a plot + a `granted_to` edge -> `owns` moves "
        "council->recipient). LAND is FINITE / NON-PRODUCED / CONSERVED: NO rule "
        "mints or destroys a Plot node (no add_node/del_node); every mode only "
        "MOVES or ADDS an `owns` edge over a fixed set of pre-existing Plot nodes. "
        "The structural-exclusion control is ABSENCE: all-owned + no-seller + "
        "no-grant -> nothing matches -> the landless acquire nothing by wanting. "
        "Composes existing DSL Terms; ZERO new Rust.",
        market_rules(),
    )
    tenure = seed(
        "bigville_land_tenure",
        "BIGVILLE R13 (block 261000) -- LAND AS THE ROOT of tenure / construction / "
        "collateral, and the STRUCTURAL levers. bl_build (construction REQUIRES "
        "owning the plot -- the R12 precondition) + bl_build_trespass (building on "
        "ANOTHER'S land is refused = trespass; unowned frontier matches neither -> "
        "built stays 0, refusal as absence). bl_foreclose_land grounds R7's "
        "PROXIED land-as-collateral: it keys off R7's OWN `foreclosed` flag (R7 "
        "decided, over the house) and MOVES the `owns` edge of the plot the same "
        "mortgage is `secured_on_plot` from debtor to bank -- foreclosure transfers "
        "the LAND. The structural levers that reopen land to the landless: "
        "bl_land_tax (the GEORGIST per-plot tax to the jurisdiction) + "
        "bl_tax_forfeit (can't pay -> the plot forfeits to the council, the "
        "redistribution source) + bl_enclosure_reversal (owned plot -> unowned "
        "frontier commons, re-claimable). Every plot transfer MOVES an `owns` edge; "
        "no Plot node is minted or destroyed (Sigma conserved). Composes existing "
        "DSL Terms; ZERO new Rust.",
        tenure_rules(),
    )
    for s in (market, tenure):
        path = os.path.join(SEED_DIR, s["id"] + ".json")
        with open(path, "w") as fh:
            json.dump(s, fh, indent=1)
            fh.write("\n")
        print("wrote", path, "(%d rules)" % len(s["rules"]))


if __name__ == "__main__":
    main()
