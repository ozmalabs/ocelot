"""Emit seeds/world_affordances.json -- the GENERAL base affordance vocabulary
(block 280000). A world provides AFFORDANCES (admissible actions) + observations;
the agent's decision COLLAPSES over the afforded set. This seed is the vocabulary
+ the provision mechanism + the effect rewrites, all graph-native.

GROUNDING: AFFORDANCE_VOCABULARY_SCIENCE.md -- a spanning, minimal-ish basis from
effect-class x ontological-target, corroborated by Gibson / NSM+Jackendoff+VerbNet
/ anthropology (Mauss) / core-knowledge (Spelke,Hamlin). Each ActionType is a
STRIPS schema: precondition (= the affordance condition) + effect (= the world
rewrite) + base_weight (= the collapse prior). `harm` is a MEMBER of the basis,
representable and available, but -- like every action -- OFFERED ONLY WHEN ITS
PRECONDITION HOLDS (a target in range), never permanently on the menu.

THE SEAM TO THE DECISION CORE (block 279000): the decision core collapses over
`DecAction` nodes and prunes by `impulse > consideration_threshold`. So the
affordance layer sits UPSTREAM and needs NO change to the decision core: a
provision rule sets `impulse = base_weight` ONLY when the precondition holds
(default 0 -> pruned, never scored). "The world provides the afforded subset" is
purely additive through the impulse channel.

This is an AUTHORING script (tools/* emit seed manifests). It is NOT agent
runtime. NO new Rust: provision + effects compose existing DSL Terms + the
add_node/add_edge/del_edge/set_attr effect ops.
"""
from __future__ import annotations
import json
import os

# ---- Term helpers ---------------------------------------------------------
def V(n):            return {"type": "Var", "name": n}
def A(node, k):      return {"type": "Attr", "node": node, "key": k}
def L(v):            return {"type": "Lit", "value": v}
def Eq(a, b):        return {"type": "Eq", "a": a, "b": b}
def Gt(a, b):        return {"type": "Gt", "a": a, "b": b}
def And(*it):        return {"type": "And", "items": list(it)}
def Plus(*it):       return {"type": "Plus", "items": list(it)}
def Minus(a, b):     return {"type": "Minus", "a": a, "b": b}
def T(term):         return {"__term__": term}

# ---- THE BASE VOCABULARY (AFFORDANCE_VOCABULARY_SCIENCE.md sec 3, minimal 8) --
# name, base_weight (collapse prior), effect_class, target, transgressive, plan_value
ACTIONS = [
    ("move",             0.50, "position",    "env",   0.0,  0.50),
    ("extract_resource", 0.55, "existence",   "env",   0.0,  0.60),
    ("transform",        0.50, "existence",   "env",   0.0,  0.65),
    ("transfer",         0.50, "possession",  "other", 0.0,  0.55),
    ("communicate",      0.60, "information", "other", 0.0,  0.55),
    ("ingest",           0.65, "vital",       "self",  0.0,  0.70),
    ("rest",             0.15, "none",        "self",  0.0,  0.20),
    ("harm",             0.20, "vital",       "other", 1.0, -0.40),
    # help/aid -- harm's PRO-SOCIAL mirror (core-knowledge help-vs-hinder is a
    # primitive social category; Spelke/Hamlin). Same precondition as harm (an
    # agent in range) but a HIGH prior. Added with block 281000 (multi-agent
    # norms), per the science doc's deferred-until-needed build order.
    ("help",             0.70, "vital",       "other", 0.0,  0.60),
]

# ---- PRECONDITIONS (the affordance condition per type) --------------------
# Each provision rule always binds `d` via [m,in_scene,d] and gates on d.name.
# extra match-rows bind the scene structure the precondition needs; `cond`
# adds any attribute test (e.g. a source must still hold stock).
#   rows:  extra match triples beyond [m,in_scene,d]
#   cond:  extra where-term beyond Eq(d.name,<name>)  (or None = precondition
#          is just "the bound scene structure exists")
PRECOND = {
    # rest: the null action -- ALWAYS afforded (no extra structure).
    "rest":             dict(rows=[],                              cond=None),
    # move: a traversable adjacent cell affords locomotion.
    "move":             dict(rows=[["m", "adjacent", "c"]],        cond=None),
    # harm/communicate: another agent in range (harm = ill-valence pole of the
    # ordinary agent affordance -- Gibson's knife cuts or is-cut).
    "harm":             dict(rows=[["m", "sees", "o"]],            cond=None),
    "help":             dict(rows=[["m", "sees", "o"]],            cond=None),
    "communicate":      dict(rows=[["m", "sees", "o"]],            cond=None),
    # extract: co-located source that still holds stock.
    "extract_resource": dict(rows=[["m", "at_source", "src"]],
                             cond=Gt(A(V("src"), "stock"), L(0.0))),
    # transfer: hold a transferable good AND a recipient present.
    "transfer":         dict(rows=[["m", "holds", "g"],
                                   ["m", "sees", "o"]],            cond=None),
    # ingest: hold something consumable.
    "ingest":           dict(rows=[["m", "holds", "g"]],
                             cond=Gt(A(V("g"), "consumable"), L(0.0))),
    # transform: hold an input good (+ a recipe/skill, folded to holding input).
    "transform":        dict(rows=[["m", "holds", "g"]],
                             cond=Gt(A(V("g"), "is_input"), L(0.0))),
}


def provision_rule(name):
    """A provision rule: precondition holds -> set impulse=base_weight (the
    action enters the decision core's afforded/considered set) + mark afforded."""
    pc = PRECOND[name]
    rows = [["m", "in_scene", "d"]] + pc["rows"]
    name_test = Eq(A(V("d"), "name"), L(name))
    where = And(name_test, pc["cond"]) if pc["cond"] is not None else name_test
    return {
        "name": f"aff_provide_{name}",
        "batch": False,
        "comment": (f"AFFORDANCE PROVISION for `{name}`: the world offers this "
                    f"action iff its precondition holds. When it does, impulse := "
                    f"base_weight so the decision core CONSIDERS it; otherwise "
                    f"impulse stays 0 and the collapse never scores it. This IS "
                    f"admissible_moves generalised to the base action vocabulary."),
        "match": rows,
        "where": where,
        "effects": [
            ["set_attr", "d", "afforded", 1.0],
            ["set_attr", "d", "impulse", T(A(V("d"), "base_weight"))],
        ],
    }


# ---- EFFECTS (the world rewrite per type; STRIPS add/delete) ---------------
# Every effect rule is gated on: this action was committed (m.committed_action
# == name) AND not yet enacted (d.enacted == 0), and fires ONCE (sets enacted).
def _committed(name):
    return And(Eq(A(V("m"), "committed_action"), L(name)),
               Eq(Plus(A(V("d"), "enacted"), L(0.0)), L(0.0)))


def effect_rule(name, rows, effects):
    base = [["m", "in_scene", "d"]] + rows
    return {
        "name": f"aff_do_{name}",
        "batch": False,
        "comment": (f"EFFECT of `{name}` (STRIPS add/delete = the world rewrite). "
                    f"Fires once when the agent commits to it."),
        "match": base,
        "where": And(Eq(A(V("d"), "name"), L(name)), _committed(name)),
        "effects": effects + [["set_attr", "d", "enacted", 1.0]],
    }


EFFECTS = [
    # rest: recover vital state, no external rewrite.
    effect_rule("rest", [], [
        ["set_attr", "m", "energy", T(Plus(A(V("m"), "energy"), L(10.0)))],
    ]),
    # move: change the actor's own position (demonstrator marks the step).
    effect_rule("move", [["m", "adjacent", "c"]], [
        ["set_attr", "m", "did_move", 1.0],
        ["add_edge", "m", "moved_to", "c"],
    ]),
    # extract_resource: decrement source stock; MINT a raw good held by actor.
    effect_rule("extract_resource", [["m", "at_source", "src"]], [
        ["set_attr", "src", "stock", T(Minus(A(V("src"), "stock"), L(1.0)))],
        ["add_node", "g2", "RawGood", {"kind": T(A(V("src"), "kind")),
                                       "is_input": 1.0, "consumable": 0.0}],
        ["add_edge", "m", "holds", "g2"],
    ]),
    # transform: consume an input good; MINT an artifact held by actor.
    effect_rule("transform", [["m", "holds", "g"]], [
        ["del_edge", "m", "holds", "g"],
        ["add_node", "art", "Artifact", {"made_from": T(A(V("g"), "kind"))}],
        ["add_edge", "m", "holds", "art"],
    ]),
    # transfer (give): move the ownership edge from actor to recipient.
    effect_rule("transfer", [["m", "holds", "g"], ["m", "sees", "o"]], [
        ["del_edge", "m", "holds", "g"],
        ["add_edge", "o", "holds", "g"],
    ]),
    # communicate: MINT a Sign conveyed to the audience (write = durable Sign).
    effect_rule("communicate", [["m", "sees", "o"]], [
        ["add_node", "sign", "Sign", {"content": "utterance", "durable": 0.0}],
        ["add_edge", "sign", "conveys", "o"],
    ]),
    # ingest: consume the item; change the actor's vital attributes.
    effect_rule("ingest", [["m", "holds", "g"]], [
        ["del_edge", "m", "holds", "g"],
        ["set_attr", "m", "energy", T(Plus(A(V("m"), "energy"), L(8.0)))],
    ]),
    # harm: reduce the target's vital state (ill-valence agent affordance).
    effect_rule("harm", [["m", "sees", "o"]], [
        ["set_attr", "o", "health", T(Minus(A(V("o"), "health"), L(25.0)))],
        ["set_attr", "o", "harmed", 1.0],
    ]),
    # help: improve the target's vital state (pro-social agent affordance).
    effect_rule("help", [["m", "sees", "o"]], [
        ["set_attr", "o", "health", T(Plus(A(V("o"), "health"), L(15.0)))],
        ["set_attr", "o", "helped", 1.0],
    ]),
]


def build():
    nodes = []
    for i, (name, bw, ec, tgt, tr, pv) in enumerate(ACTIONS):
        nodes.append({
            "local_id": i,
            "type": "ActionType",
            "attrs": {"name": name, "base_weight": bw, "effect_class": ec,
                      "target": tgt, "transgressive": tr, "plan_value": pv,
                      "index": float(i)},
        })
    rules = [provision_rule(n) for (n, *_ ) in ACTIONS] + EFFECTS
    return {
        "id": "world_affordances",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "GENERAL BASE AFFORDANCE VOCABULARY (block 280000). A world provides "
            "AFFORDANCES (admissible actions) + observations; the agent's decision "
            "COLLAPSES over the afforded set. The 8-type minimal basis (move, "
            "extract_resource, transform, transfer, communicate, ingest, rest, "
            "harm) spans all six effect classes (position/existence/configuration/"
            "possession/information/vital) x targets, grounded in "
            "AFFORDANCE_VOCABULARY_SCIENCE.md (Gibson affordance taxonomy; NSM/"
            "Jackendoff/VerbNet action primitives; Mauss gift-vs-trade; Spelke/"
            "Hamlin core-knowledge help-vs-harm). Each ActionType is a STRIPS "
            "schema: precondition (=affordance condition) + effect (=world "
            "rewrite) + base_weight (=collapse prior). PROVISION rules set "
            "impulse=base_weight ONLY when the precondition holds (else 0 -> the "
            "decision core prunes it, never scored), so 'the world provides the "
            "afforded subset' is purely additive over the block-279000 decision "
            "core -- NO decision-core change. `harm` is a MEMBER of the basis, "
            "offered ONLY when a target is in range (precondition-gated, not "
            "permanently on the menu), at a LOW base prior -- representable so a "
            "norm against it is representable, but rarely afforded and rarely "
            "selected. EFFECT rules perform the STRIPS rewrite once the agent "
            "commits. ZERO new Rust (composes existing DSL Terms + add_node/"
            "add_edge/del_edge/set_attr). self_load_only."),
        "nodes": nodes,
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": rules,
    }


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "seeds", "world_affordances.json")
    doc = build()
    with open(out, "w") as f:
        json.dump(doc, f, indent=1)
    print(f"wrote {out}: {len(doc['nodes'])} ActionTypes, {len(doc['rules'])} rules")
