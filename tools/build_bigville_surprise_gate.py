"""Emit seeds/bigville_surprise_gate.json (block 284000) -- the graph-native
SURPRISE gate: a decision fires when observation diverges from the held social
prediction, as RULES (not a Python dict). The residual becomes graph-resident.

A resident holds a SocialPrediction as `predicts_near` edges (m -> Person it
expects nearby). The adapter mints observation as `sees` edges (proximity). Then:

  * sg_surprise: a `sees` with NO matching `predicts_near` (an UNPREDICTED other
    nearby) sets `m.surprised = 1` -- the prediction residual, computed by a rule.
    A PREDICTED co-presence (predicts_near already present) matches NOTHING here,
    so it fires no surprise. This is the surprise-vs-event discriminator, in a rule.
  * sg_absorb: the same unpredicted `sees` adds `m -predicts_near-> o`, so the
    prediction ABSORBS the surprise -- re-seeing the same person next tick is no
    longer surprising (held-prediction update, the perception held-surface analog).

`m.surprised` is the gate the conduct collapse (282000) reads: only a surprised
resident decides; between surprises it continues its durative action (the habitual
fast path). Edge-absence uses the standard Not(Exists(Neighbours ... == o)) form
(allocentric_world_view.json / bigville_need_drive_goal.json precedent). ZERO new
Rust; self_load_only.
"""
from __future__ import annotations
import json
import os


def V(n):        return {"type": "Var", "name": n}
def A(node, k):  return {"type": "Attr", "node": node, "key": k}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}


def _o_not_predicted():
    """where-term: o is NOT in m's predicts_near set (an unpredicted co-presence)."""
    return {"type": "Not", "arg": {
        "type": "Exists",
        "source": {"type": "Neighbours", "node": V("m"),
                   "edge_type": "predicts_near", "any_type": False},
        "var_name": "p",
        "predicate": Eq(V("p"), V("o"))}}


RULES = [
    {
        "name": "sg_provide_directed",
        "batch": False,
        "comment": ("DIRECTED affordance provision: a directed option is afforded "
                    "(impulse := base_weight) iff ITS OWN target is co-present "
                    "(matches d aims_at o AND m sees o). Unlike the target-agnostic "
                    "280000 aff_provide rules, harm@B is offered only when B is "
                    "seen, not when anyone is -- required once options are "
                    "pre-minted toward every resident."),
        "match": [["m", "in_scene", "d"], ["d", "aims_at", "o"], ["m", "sees", "o"]],
        "effects": [["set_attr", "d", "impulse", {"__term__": A(V("d"), "base_weight")}],
                    ["set_attr", "d", "afforded", 1.0]],
    },
    {
        "name": "sg_surprise",
        "batch": False,
        "comment": ("SURPRISE = observation != held prediction, as a rule. A `sees` "
                    "edge to an other NOT in predicts_near sets m.surprised=1 -- the "
                    "prediction residual. A PREDICTED co-presence (predicts_near "
                    "present) does not match, so it fires no surprise. m.surprised "
                    "is the gate the conduct collapse (282000) reads: only a "
                    "surprised resident decides."),
        "match": [["m", "sees", "o"]],
        "where": _o_not_predicted(),
        "effects": [["set_attr", "m", "surprised", 1.0]],
    },
    {
        "name": "sg_absorb",
        "batch": False,
        "comment": ("The prediction ABSORBS the surprise: the unpredicted other is "
                    "added to predicts_near, so re-seeing it next tick is no longer "
                    "surprising (held-prediction update -- the perception "
                    "held-surface analog). Same match as sg_surprise, so both fire "
                    "on the residual in one fixpoint; next tick the residual is gone."),
        "match": [["m", "sees", "o"]],
        "where": _o_not_predicted(),
        "effects": [["add_edge", "m", "predicts_near", "o"]],
    },
]


def build():
    return {
        "id": "bigville_surprise_gate",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "GRAPH-NATIVE SURPRISE GATE (block 284000). A decision fires on SURPRISE "
            "-- observation != held social prediction -- as RULES, not a Python "
            "dict. A resident holds a SocialPrediction as predicts_near edges; the "
            "adapter mints observation as sees edges (proximity). sg_surprise: a "
            "sees with no matching predicts_near sets m.surprised=1 (the prediction "
            "residual, computed by a rule) -- a PREDICTED co-presence fires nothing. "
            "sg_absorb: the same unpredicted sees adds predicts_near, so the "
            "prediction absorbs the surprise (held-prediction update). m.surprised "
            "gates the conduct collapse (282000): only a surprised resident decides; "
            "between surprises it continues its durative action. Edge-absence uses "
            "the standard Not(Exists(Neighbours...==o)) form. This is the "
            "graph-native realization of block 283000's Python time-model "
            "demonstrator, composing with the supergraph town. ZERO new Rust; "
            "self_load_only."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": RULES,
    }


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "seeds", "bigville_surprise_gate.json")
    with open(out, "w") as f:
        json.dump(build(), f, indent=1)
    print(f"wrote {out}: {len(build()['rules'])} rules")
