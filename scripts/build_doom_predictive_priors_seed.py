"""Emit the graph-native Doom structural-prior seed (block 162000).

This is authoring code only. Runtime cognition is seed data executed by Rust:
partial passable SpaceQuantum boxes are decoded as room/corridor hypotheses,
their unseen walls are projected as MapPrediction boxes, and later ObsCells
mint confirmation/correction outcomes plus residuals.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "doom_predictive_priors.json")


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Neighbours(n, et): return {"type": "Neighbours", "node": n, "edge_type": et, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Idx(seq, i): return {"type": "IndexAt", "seq": seq, "index": L(i)}
def Vec(*xs): return {"type": "Vec", "items": list(xs)}


GAME = V("game")
QLO, QHI = A("Q", "lo"), A("Q", "hi")
EXT0 = Plus(Minus(Idx(QHI, 0), Idx(QLO, 0)), L(1))
EXT1 = Plus(Minus(Idx(QHI, 1), Idx(QLO, 1)), L(1))
BW = A("game", "body_w")


def enabled():
    return And(Eq(A("game", "map_mode"), L("doom")),
               Eq(A("game", "predictive_map"), L(1.0)))


def same_box(a, b):
    return And(Eq(Idx(A(a, "lo"), 0), Idx(A(b, "lo"), 0)),
               Eq(Idx(A(a, "lo"), 1), Idx(A(b, "lo"), 1)),
               Eq(Idx(A(a, "hi"), 0), Idx(A(b, "hi"), 0)),
               Eq(Idx(A(a, "hi"), 1), Idx(A(b, "hi"), 1)))


def contains(box_var, pose):
    return And(*[
        And(Gte(Idx(pose, d), Idx(A(box_var, "lo"), d)),
            Lte(Idx(pose, d), Idx(A(box_var, "hi"), d)))
        for d in range(2)
    ])


def computed(x):
    return {"__term__": x}


def hypothesis_absent(schema):
    return Not(Exists(
        Neighbours(GAME, "has_hypothesis"), "H2",
        And(Eq(A("H2", "schema"), L(schema)),
            Eq(A("H2", "epoch"), A("Q", "epoch")),
            same_box("H2", "Q"))))


def projection_rule(name, schema, condition, sides):
    """One rule mints the whole hypothesis and all of its projected wall sides."""
    effects = [
        ["add_node", "H", "SpatialHypothesis", {
            "schema": schema, "lo": computed(QLO), "hi": computed(QHI),
            "epoch": computed(A("Q", "epoch")), "status": "projected",
        }],
        ["add_edge", "game", "has_hypothesis", "H", {}],
        ["add_edge", "H", "based_on", "Q", {}],
    ]
    for i, (role, lo, hi) in enumerate(sides):
        p = f"P{i}"
        effects.extend([
            ["add_node", p, "MapPrediction", {
                "world_type": "CellBox", "schema": schema, "role": role,
                "lo": computed(lo), "hi": computed(hi), "value": 1.0,
                "epoch": computed(A("Q", "epoch")), "status": "confabulated",
            }],
            ["add_edge", "game", "has_prediction", p, {}],
            ["add_edge", "H", "projects", p, {}],
        ])
    return {
        "name": name,
        "comment": (
            f"TOP-DOWN {schema}: decode a partial passable quantum and immediately "
            "project the schema's unseen wall structure. This deliberately predicts "
            "more than has been observed; no has_cell belief is written."
        ),
        "match": [["Q", "in_space", "game"]],
        "where": And(enabled(), Eq(A("Q", "kind"), L("passable")),
                     condition, hypothesis_absent(schema)),
        "effects": effects,
    }


ONE = L(1)
LO0, LO1, HI0, HI1 = Idx(QLO, 0), Idx(QLO, 1), Idx(QHI, 0), Idx(QHI, 1)

# Complete rectangular perimeter. Dim-0 sides carry the corners; dim-1 sides
# cover the remaining spans, so the four boxes do not overlap.
ENCLOSURE_SIDES = [
    ("wall_dim0_low", Vec(Minus(LO0, ONE), Minus(LO1, ONE)),
     Vec(Minus(LO0, ONE), Plus(HI1, ONE))),
    ("wall_dim0_high", Vec(Plus(HI0, ONE), Minus(LO1, ONE)),
     Vec(Plus(HI0, ONE), Plus(HI1, ONE))),
    ("wall_dim1_low", Vec(LO0, Minus(LO1, ONE)),
     Vec(HI0, Minus(LO1, ONE))),
    ("wall_dim1_high", Vec(LO0, Plus(HI1, ONE)),
     Vec(HI0, Plus(HI1, ONE))),
]

CORRIDOR_NARROW_0 = [
    ("parallel_wall_low", Vec(Minus(LO0, ONE), LO1), Vec(Minus(LO0, ONE), HI1)),
    ("parallel_wall_high", Vec(Plus(HI0, ONE), LO1), Vec(Plus(HI0, ONE), HI1)),
]
CORRIDOR_NARROW_1 = [
    ("parallel_wall_low", Vec(LO0, Minus(LO1, ONE)), Vec(HI0, Minus(LO1, ONE))),
    ("parallel_wall_high", Vec(LO0, Plus(HI1, ONE)), Vec(HI0, Plus(HI1, ONE))),
]

RULES = [
    projection_rule(
        "dpp_project_room", "room",
        And(Gt(EXT0, BW), Gt(EXT1, BW)),
        ENCLOSURE_SIDES),
    projection_rule(
        "dpp_project_minimal_enclosure", "minimal_enclosure",
        And(Eq(EXT0, BW), Eq(EXT1, BW)),
        ENCLOSURE_SIDES),
    projection_rule(
        "dpp_project_corridor_dim0", "corridor",
        And(Eq(EXT0, BW), Gt(EXT1, BW)),
        CORRIDOR_NARROW_0),
    projection_rule(
        "dpp_project_corridor_dim1", "corridor",
        And(Eq(EXT1, BW), Gt(EXT0, BW)),
        CORRIDOR_NARROW_1),
]


def outcome_absent():
    return Not(Exists(
        Neighbours(GAME, "has_prediction_outcome"), "X",
        And(Eq(A("X", "prediction_epoch"), A("P", "epoch")),
            Eq(A("X", "observation_epoch"), A("O", "obs_epoch")),
            Eq(A("X", "pose"), A("O", "pose")),
            Eq(A("X", "prediction_lo"), A("P", "lo")),
            Eq(A("X", "prediction_hi"), A("P", "hi")))))


def outcome_rule(name, srcs, observed_value, result):
    correction = result == "corrected"
    effects = [
        ["add_node", "X", "PredictionOutcome", {
            "result": result,
            "pose": computed(A("O", "pose")),
            "predicted_value": 1.0, "observed_value": float(observed_value),
            "schema": computed(A("P", "schema")),
            "prediction_lo": computed(A("P", "lo")),
            "prediction_hi": computed(A("P", "hi")),
            "prediction_epoch": computed(A("P", "epoch")),
            "observation_epoch": computed(A("O", "obs_epoch")),
        }],
        ["add_edge", "game", "has_prediction_outcome", "X", {}],
        ["add_edge", "X", "tests_prediction", "P", {}],
    ]
    if correction:
        effects.extend([
            ["add_node", "R", "MapResidual", {
                "kind": "prediction_minus_observation",
                "pose": computed(A("O", "pose")),
                "predicted_value": 1.0, "observed_value": float(observed_value),
                "schema": computed(A("P", "schema")),
                "prediction_epoch": computed(A("P", "epoch")),
                "observation_epoch": computed(A("O", "obs_epoch")),
            }],
            ["add_edge", "game", "has_map_residual", "R", {}],
            ["add_edge", "R", "from_prediction", "P", {}],
        ])
    return {
        "name": name,
        "comment": (
            f"Compare a later bottom-up observation with the preceding top-down "
            f"wall projection; mint a durable {result} outcome"
            + (" and prediction-minus-observation residual." if correction else ".")
        ),
        "match": [["game", "observed", "O"], ["game", "has_prediction", "P"]],
        "where": And(
            enabled(),
            Or(*[Eq(A("O", "src"), L(s)) for s in srcs]),
            Eq(A("P", "epoch"), Minus(A("O", "obs_epoch"), ONE)),
            contains("P", A("O", "pose")),
            outcome_absent()),
        "effects": effects,
    }


RULES.extend([
    outcome_rule("dpp_confirm_wall", ("depth_wall",), 1, "confirmed"),
    outcome_rule("dpp_correct_wall_to_free", ("walk", "depth_free"), 0, "corrected"),
])

MANIFEST = {
    "id": "doom_predictive_priors",
    "version": "1.0.0",
    "depends_on": ["doom_ingraph_map"],
    "description": (
        "Graph-native top-down structural confabulation over the observed Doom map. "
        "Partial passable SpaceQuantum boxes are decoded as room/corridor/minimal-"
        "enclosure hypotheses; rules project complete unseen wall structure at the "
        "same tick as bottom-up accumulation. Later ObsCells mint confirmation or "
        "prediction-minus-observation residuals. Predictions never write has_cell."
    ),
    "microtheory": {
        "name": "doom_predictive_priors",
        "description": "partial spatial evidence -> whole room/corridor hypothesis -> projected walls -> residual",
    },
    "nodes": [],
    "edges": [],
    "productions": [],
    "concepts": [],
    "rules": RULES,
}


if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
    print(f"wrote {OUT} with {len(RULES)} rules")
