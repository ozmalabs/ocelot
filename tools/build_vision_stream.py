#!/usr/bin/env python3
"""Emit seeds/vision_stream.json — THE STREAM: a bounded budget spent by
SALIENCE x SCALE, as pure graph data (NO new Rust).

See VISION_STREAM_PREREG.md. ONE rule, `stream_resolve_salient`, spends a
Scene.budget by resolving the Argmax-residual region per run_rules pass and
counting the budget up as graph data. Coarse-first, budget-allocation and
preemption/tunnel are EMERGENT consequences of that one water-filling rule;
there is NO preemption threshold (PROTOCOL §13). Flag-gated on
StreamParams.stream, OFF by default (§9).

This is a seed BUILDER (emits graph data) — admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_stream.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms used by seeds/vision_ground.json) --
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}
def Eq(a, b):           return {"type": "Eq", "a": a, "b": b}
def And(items):         return {"type": "And", "items": items}
def Plus(items):        return {"type": "Plus", "items": items}
def Neigh(node, edge):  return {"type": "Neighbours", "node": node,
                                "edge_type": edge, "any_type": False}
def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Argmax(src, var, value):
    return {"type": "Argmax", "source": src, "var_name": var, "value": value}
def PickParams():
    return {"type": "PickUnique",
            "source": {"type": "NodesOfType", "node_type": "StreamParams"}}
def term(x):            return {"__term__": x}


# The competing candidate set: this scene's unresolved, positive-residual regions.
def _candidates(scene):
    return Filter(
        src=Neigh(scene, "has_region"),
        var="cand",
        pred=And([
            Lt(A(V("cand"), "resolved"), Lit(0.5)),
            Gt(A(V("cand"), "residual"), Lit(0.0)),
        ]),
    )


STREAM_RULE = {
    "name": "stream_resolve_salient",
    "comment": (
        "THE STREAM (the one contribution rule). Per run_rules pass, resolve the "
        "single highest-residual (Argmax) unresolved region of the scene while the "
        "budget is not spent, record its stream position (order = spent), and "
        "count the budget up (spent += 1). Exactly one region -- the unique Argmax "
        "winner (deterministic first-encountered tiebreak, the qf_frontier_goal "
        "idiom) -- passes the where per pass, so the budget advances by one and the "
        "regions stream in DESCENDING residual order until spent==budget or no "
        "unresolved positive-residual region remains. Coarse-first (a large/coarse "
        "structure carries more residual MASS -> wins first), budget-allocation "
        "(water-filling to the salient region), and preemption/tunnel (a "
        "majority-mass 'spear' drains the budget -> periphery left at render grain) "
        "are ALL consequences of this one rule -- there is NO preemption threshold "
        "(§13: preemption falls OUT of the argmax). Flag-gated on "
        "StreamParams.stream>0.5, OFF by default (§9): inert without it."
    ),
    "match": [["scene", "has_region", "R"]],
    "where": And([
        # (i) flag on
        Gt(A(PickParams(), "stream"), Lit(0.5)),
        # (ii) budget remaining
        Lt(A(V("scene"), "spent"), A(V("scene"), "budget")),
        # (iii) R unresolved
        Lt(A(V("R"), "resolved"), Lit(0.5)),
        # (iv) R has positive residual (no surprise -> not resolved: the floor)
        Gt(A(V("R"), "residual"), Lit(0.0)),
        # (v) R IS the salience winner (Argmax over the competing candidates)
        Eq(V("R"), Argmax(_candidates(V("scene")), "cand",
                          A(V("cand"), "residual"))),
    ]),
    "effects": [
        ["set_attr", "R", "resolved", term(Lit(1.0))],
        # the stream position: 0-indexed, from the pre-mutation snapshot of spent.
        ["set_attr", "R", "order", term(A(V("scene"), "spent"))],
        # count the budget up (spent += 1) as graph data.
        ["set_attr", "scene", "spent", term(Plus([A(V("scene"), "spent"), Lit(1.0)]))],
    ],
}


SEED = {
    "id": "vision_stream",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "THE STREAM -- perception spends a BOUNDED budget, ordered by SALIENCE x "
        "SCALE. Vision is not delivered all-at-once and uniform: it is STREAMED -- "
        "coarse-to-fine by scale (large low-frequency structure resolves first; "
        "detail refines on the residual, order-N), allocated by salience (the "
        "bounded refinement budget is spent on the largest-residual region first), "
        "and PREEMPTIBLE (a maximally-salient 'spear' captures the budget and the "
        "rest degrades to the top-down render -- tunnel vision). ONE water-filling "
        "rule (stream_resolve_salient) over a residual-mass region field: the "
        "salience order is a pure Argmax, the budget is a Scene attr counted up as "
        "graph data, and coarse-first / budget-allocation / preemption all fall OUT "
        "with ZERO magic numbers (no preemption threshold -- §13). NO new Rust: "
        "reuses the Argmax/Plus/Neighbours/Filter DSL and the run_rules fixpoint. "
        "Composes the just-landed bidirectional loop: salience = the render-vs-input "
        "residual mass. In-frame/integer only (the frame/continuum invariant). "
        "Flag-gated on StreamParams.stream, OFF by default (§9). See "
        "VISION_STREAM_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_stream_mt",
        "label": "the visual stream: a salience-ordered bounded budget",
    },
    "nodes": [
        {"local_id": 0, "type": "StreamParams", "attrs": {"stream": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [STREAM_RULE],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_stream.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
