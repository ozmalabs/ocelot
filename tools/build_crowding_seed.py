#!/usr/bin/env python3
"""Emit seeds/vision_crowding.json — CROWDING (T8), eccentricity-scaled pooling.

A one-shot seed BUILDER (CLAUDE.md: tools/* emit graph data; not agent runtime).
The seed is committed as DATA; this file is the source that produced it. Re-run:
    python tools/build_crowding_seed.py

Crowding = recognition reads a POOLED summary over an eccentricity-scaled region.
pool(item) = {item} ∪ {n : dist²(n,item) ≤ (bouma·ecc(item))²}. recognized = the
pool contains ONLY the target. All decisions are seed rules; NO Python agent logic,
NO new Rust. Flag CrowdParams.crowd OFF by default (PROTOCOL §9).
"""
from __future__ import annotations
import json
import os

# ---- DSL term builders (mirror seeds/vision_ground.json / vision_border_ownership) --

def var(n):            return {"type": "Var", "name": n}
def lit(v):            return {"type": "Lit", "value": v}
def attr(node, key):   return {"type": "Attr", "node": node, "key": key}
def vattr(v, key):     return attr(var(v), key)
def params(key):       return attr({"type": "PickUnique",
                                    "source": {"type": "NodesOfType",
                                               "node_type": "CrowdParams"}}, key)
def minus(a, b):       return {"type": "Minus", "a": a, "b": b}
def plus(*items):      return {"type": "Plus", "items": list(items)}
def times(*items):     return {"type": "Times", "items": list(items)}
def div(a, b):         return {"type": "Div", "a": a, "b": b}
def sq(x):             return times(x, x)              # exact square (Times[x,x])
def gt(a, b):          return {"type": "Gt", "a": a, "b": b}
def gte(a, b):         return {"type": "Gte", "a": a, "b": b}
def lt(a, b):          return {"type": "Lt", "a": a, "b": b}
def lte(a, b):         return {"type": "Lte", "a": a, "b": b}
def andt(*items):      return {"type": "And", "items": list(items)}
def ite(cond, then, other): return {"type": "IfThenElse", "cond": cond,
                                    "then": then, "other": other}
def neighbours(v, edge): return {"type": "Neighbours", "node": var(v),
                                 "edge_type": edge, "any_type": False}
def filt(src, vn, pred): return {"type": "Filter", "source": src,
                                 "var_name": vn, "predicate": pred}
def count(src):        return {"type": "Count", "source": src}
def sumt(src, vn, val): return {"type": "Sum", "source": src,
                                "var_name": vn, "value": val}
def setattr_(v, key, term): return ["set_attr", v, key, {"__term__": term}]

FLAG_ON = gt(params("crowd"), lit(0.5))

# ---- geometry over the matched target `t` and its field `field` --------------------
# ecc² of target from the fixation (gaze) — the eccentricity from the ungrounded origin.
ECC2 = plus(sq(minus(vattr("t", "irow"), vattr("field", "gaze_row"))),
            sq(minus(vattr("t", "icol"), vattr("field", "gaze_col"))))
# pooling radius² = bouma²·ecc²  (R = bouma·ecc — the eccentricity-scaled pool).
POOL_R2 = times(sq(params("bouma")), ECC2)

# a co_item neighbour `n` is a FLANKER IN THE POOL iff dist²(n,t) ≤ target's pool_radius².
DIST2_nt = plus(sq(minus(vattr("n", "irow"), vattr("t", "irow"))),
                sq(minus(vattr("n", "icol"), vattr("t", "icol"))))
IN_POOL = lte(DIST2_nt, vattr("t", "pool_radius2"))
FLANKERS = filt(neighbours("t", "co_item"), "n", IN_POOL)
N_FLANK = count(FLANKERS)
SUM_FLANK_IDENT = sumt(FLANKERS, "n", vattr("n", "ident"))
POOL_N = plus(lit(1.0), N_FLANK)
# the SUMMARY STATISTIC the periphery reports: mean ident over the pool (target + pooled
# flankers). Isolated ⇒ mean == own ident (survives); flanked ⇒ mixed (identity lost).
POOLED_IDENT = div(plus(vattr("t", "ident"), SUM_FLANK_IDENT), POOL_N)

# ---- the two rules -----------------------------------------------------------------
RULE_ECC = {
    "name": "cr_ecc",
    "comment": "Per item: ecc² from the fixation and the eccentricity-scaled pooling "
               "radius² = bouma²·ecc². Pure geometry — the item's eccentricity from the "
               "ungrounded gaze origin (the foveation prior's eccentricity-decay, made a "
               "pooling radius). Fires once (ecc_done guard). Gated on CrowdParams.crowd "
               "(OFF by default). No magic number: bouma is agent-revisable graph data; "
               "coordinates are in-frame integers, the radius a cross-frame read.",
    "match": [["field", "has_item", "t"]],
    "where": andt(FLAG_ON, lt(vattr("t", "ecc_done"), lit(0.5))),
    "effects": [
        setattr_("t", "ecc2", ECC2),
        setattr_("t", "pool_radius2", POOL_R2),
        setattr_("t", "ecc_done", lit(1.0)),
    ],
}

RULE_POOL = {
    "name": "cr_pool",
    "comment": "Per item, once its radius is known (ecc_done): pool = the item ∪ its "
               "co_item neighbours within pool_radius². pool_n = 1 + flankers-in-pool; "
               "pooled_ident = mean ident over the pool (the SUMMARY STATISTIC — mixes "
               "when a flanker is pooled); crowded = a flanker is in the pool; recognized "
               "= the pool holds ONLY the target (identity survives). Recognition READS "
               "the pooled summary — isolated peripheral target survives (pool={target}), "
               "flanked it does not. Fires once (pool_done). The pool is LOCAL over the "
               "co_item 2-clique (NOT a global NodesOfType grab). Every decision is here, "
               "in the graph; the adapter only ingests items and reads attrs back.",
    "match": [["field", "has_item", "t"]],
    "where": andt(FLAG_ON,
                  gt(vattr("t", "ecc_done"), lit(0.5)),
                  lt(vattr("t", "pool_done"), lit(0.5))),
    "effects": [
        setattr_("t", "pool_n", POOL_N),
        setattr_("t", "n_flank_in_pool", N_FLANK),
        setattr_("t", "pooled_ident", POOLED_IDENT),
        setattr_("t", "crowded", ite(gte(N_FLANK, lit(1.0)), lit(1.0), lit(0.0))),
        setattr_("t", "recognized", ite(gte(N_FLANK, lit(1.0)), lit(0.0), lit(1.0))),
        setattr_("t", "pool_done", lit(1.0)),
    ],
}

SEED = {
    "id": "vision_crowding",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "CROWDING (T8) — eccentricity-scaled statistical pooling, validating the eye's "
        "foveation / eccentricity-decay prior (Bouma 1970). Recognition READS a pooled "
        "summary over a region whose radius R=bouma·ecc grows with eccentricity from the "
        "fixation (the ungrounded gaze origin): an isolated peripheral target survives "
        "(pool={target}), a flanked one is JUMBLED (pool=target+flankers, the mean ident "
        "mixes). A FOVEAL target is SPARED — R~0 at the fovea — even by the SAME flankers "
        "(the risked dissociation). Critical spacing grows with ecc (Bouma; ENTAILED by "
        "R=bouma·ecc, reported not banked — §13.1). Pure seed rules (cr_ecc / cr_pool) "
        "over the LOCAL co_item fold; NO new Rust. bouma is agent-revisable graph data, "
        "NOT a biological constant. Flag CrowdParams.crowd OFF by default (§9). See "
        "VISION_CROWDING_PREREG.md."),
    "microtheory": {
        "name": "eccentricity_scaled_pooling",
        "description": "The periphery reports a summary statistic over an "
                       "eccentricity-scaled pooling region; identity survives only where "
                       "the pool contains the target alone. Crowding, foveal sparing and "
                       "Bouma's critical-spacing law are the one mechanism read at "
                       "different eccentricities and clutter."},
    "nodes": [
        {"local_id": 0, "type": "CrowdParams", "attrs": {"crowd": 0.0, "bouma": 0.6}}
    ],
    "edges": [],
    "productions": [],
    "rules": [RULE_ECC, RULE_POOL],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_crowding.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "|", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
