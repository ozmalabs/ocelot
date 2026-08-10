"""Author the bigville R5 (block 253000) reputation seed -- the ONE new integration
mechanism the loop rung needs: the economy -> affect -> SOCIETY closing hop. A
creditor whose affect flipped on a DEFAULT (R4 be_default_affect set demand_cash=1)
BADMOUTHS the defaulting debtor; townsfolk who hold an opinion of that debtor read
the badmouth against the debtor's standing and their BACKING flips -- the SAME
testimony>standing credibility arithmetic the 245 bd_villager_backs rule uses,
now DRIVEN by a material economic default. Emits seeds/bigville_loop_reputation.json.

Everything else in R5 reuses R1-R4 seeds by import (movement/energy, needs/preference,
day-night/sleep/collapse, production/exchange/supply/debt/expectation) -- this file
adds no Rust and composes only existing DSL Terms. The badmouth rule roots its match
at the debtor/owe and traverses `creditor` OUTGOING (owe -creditor-> cred), the SAME
safe direction be_default/be_default_affect use -- so a creditor owed by multiple
debtors (multiple incoming `creditor` edges) does NOT break matching (probed live).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "bigville_loop_reputation.json")


def attr(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def plus0(var, key):
    # `attr + 0` -- the R4 seeds' idiom that coerces a possibly-missing attr to 0.0
    return {"type": "Plus", "items": [attr(var, key), {"type": "Lit", "value": 0}]}


def lit(v):
    return {"type": "Lit", "value": v}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


# ---- bl_badmouth: a defaulted-on, soured creditor badmouths the debtor ----------
# match the debtor's defaulted obligation to a creditor whose default-affect already
# fired (demand_cash=1). Increment the debtor's `badmouthed` reputation-harm counter
# by the creditor's `badmouth_strength`, mint a readable Badmouth node, and one-shot
# guard on the owe (badmouth_done) so it fires once per obligation.
bl_badmouth = {
    "name": "bl_badmouth",
    "comment": "ECONOMY -> AFFECT -> SOCIETY (close): a creditor soured by a DEFAULT "
               "(be_default_affect set demand_cash=1) BADMOUTHS the defaulting debtor "
               "-- a real state change: the debtor's `badmouthed` reputation-harm "
               "counter rises by the creditor's badmouth_strength, and a Badmouth node "
               "is minted (glass-box). One-shot per obligation (badmouth_done). Roots "
               "at debtor/owe, traverses `creditor` OUTGOING (multi-debtor safe).",
    "match": [["debtor", "owes", "owe"], ["owe", "creditor", "cred"]],
    "where": {"type": "And", "items": [
        eq(plus0("owe", "defaulted"), lit(1.0)),
        eq(plus0("cred", "demand_cash"), lit(1.0)),
        eq(plus0("owe", "badmouth_done"), lit(0.0)),
    ]},
    "effects": [
        ["set_attr", "debtor", "badmouthed", {"__term__": {"type": "Plus", "items": [
            plus0("debtor", "badmouthed"), plus0("cred", "badmouth_strength")]}}],
        ["add_node", "bm", "Badmouth", {"strength": 1.0}],
        ["add_edge", "cred", "badmouths", "bm"],
        ["add_edge", "bm", "about_debtor", "debtor"],
        ["set_attr", "owe", "badmouth_done", 1.0],
    ],
}

# ---- bl_townsfolk_opinion: a townsperson's backing of the debtor flips ----------
# each townsperson holds an `opines_on` edge to a debtor. Its backing is the SAME
# credibility comparison as 245's bd_villager_backs: backs iff the debtor's STANDING
# still outweighs the badmouth testimony it has accrued (badmouthed * badmouth_weight).
# Before any default badmouthed=0 -> standing>0 -> backs=1; after the cascade the
# badmouth testimony crosses standing -> backs flips 1->0. A real state change gating
# on real state -- nothing narrated.
bl_opinion = {
    "name": "bl_townsfolk_opinion",
    "comment": "THE 245 CREDIBILITY ARITHMETIC, driven by the badmouth: a townsperson "
               "backs the debtor iff standing > badmouthed*badmouth_weight (mirrors "
               "bd_villager_backs' cred comparison). badmouthed=0 -> backs=1; the "
               "cascade raises badmouthed past standing -> backs flips to 0.",
    "match": [["t", "opines_on", "deb"]],
    "where": eq(plus0("t", "opinion_on"), lit(1.0)),
    "effects": [
        ["set_attr", "t", "backs_debtor", {"__term__": {
            "type": "IfThenElse",
            "cond": {"type": "Gt",
                     "a": plus0("deb", "standing"),
                     "b": {"type": "Times", "items": [
                         plus0("deb", "badmouthed"), plus0("t", "badmouth_weight")]}},
            "then": lit(1.0), "other": lit(0.0)}}],
    ],
}

seed = {
    "id": "bigville_loop_reputation",
    "version": "1.0.0",
    "depends_on": [],
    "self_load_only": True,
    "description": "BIGVILLE R5 (block 253000) -- the economy->affect->SOCIETY closing "
                   "hop. bl_badmouth: a creditor soured by a DEFAULT (R4 be_default_affect "
                   "-> demand_cash=1) badmouths the defaulting debtor (debtor.badmouthed "
                   "rises; a Badmouth node minted). bl_townsfolk_opinion: a townsperson's "
                   "backing of that debtor flips via the SAME standing>testimony comparison "
                   "245's bd_villager_backs uses. Composes existing Terms; zero new Rust. "
                   "Roots at debtor/owe, traverses `creditor` outgoing (multi-debtor safe).",
    "nodes": [], "edges": [], "productions": [], "concepts": [],
    "rules": [bl_badmouth, bl_opinion],
}

with open(OUT, "w") as f:
    json.dump(seed, f, indent=1)
print("wrote", OUT, "with rules", [r["name"] for r in seed["rules"]])
