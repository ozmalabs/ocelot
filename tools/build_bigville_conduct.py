"""Emit seeds/bigville_conduct.json -- DIRECTED, BOND-COUPLED CONDUCT (block
281000). The affordance vocabulary (280000) offers agent-directed actions
(harm/help/transfer/communicate) whenever a target is in range. In a town with
RELATIONSHIPS, WHOM you act on is not arbitrary -- it reads the held Bond. These
rules couple the DEEP (model-value / plan_value) score of each directed action to
the actor's held Bond toward its target:

  * harm(o).plan_value  = plan_base + resent_gain*resentment(o) - aff_gain*affection(o)
  * help(o).plan_value  = plan_base + aff_gain*affection(o)
  * transfer(o).plan_value = plan_base + aff_gain*affection(o)

So the decision core (279000) collapse -- when it deepens -- directs harm toward a
RESENTED rival (not a loved friend), and help/giving toward those the actor cares
for. The FAST pull (impulse = the vocabulary base_weight: harm LOW, help HIGH) is
unchanged; the Bond only shapes the DEEP, model-based re-score. Reading the held
affect is a graph read (a RULE), not adapter arithmetic -- the motivational
structure lives in the graph.

FALSIFIER: conduct_resent_gain = conduct_affection_gain = 0 -> plan_value collapses
to plan_base for every directed action -> the collapse cannot tell rival from
friend (no directedness). The control that shows the Bond does the directing.

Authoring script (tools/* emit seed manifests). NO new Rust: composes existing
DSL Terms (Plus/Minus/Times/Attr/Eq). Gains are knobs on the ConductState.
"""
from __future__ import annotations
import json
import os


def V(n):        return {"type": "Var", "name": n}
def A(node, k):  return {"type": "Attr", "node": node, "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def Plus(*it):   return {"type": "Plus", "items": list(it)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*it):  return {"type": "Times", "items": list(it)}
def T(term):     return {"__term__": term}

# match binds: d (the directed DecAction), o (its target), bond (m's Bond->o).
_MATCH = [["m", "in_scene", "d"], ["d", "aims_at", "o"],
         ["m", "holds_bond", "bond"], ["bond", "toward", "o"]]

# plan_base is the ActionType's default plan_value, stored on the DecAction at
# mint; the rule recomputes plan_value = plan_base + coupling every pass
# (idempotent -- no guard, always derived from plan_base + the current Bond).
_RESENT = A(V("m"), "conduct_resent_gain")
_AFF = A(V("m"), "conduct_affection_gain")
_PLANBASE = A(V("d"), "plan_base")
_RESENTMENT = A(V("bond"), "affect_resentment")
_AFFECTION = A(V("bond"), "affect_affection")


def couple(name, plan_value_term, comment):
    return {
        "name": f"conduct_couple_{name}",
        "batch": False,
        "comment": comment,
        "match": _MATCH,
        "where": Eq(A(V("d"), "name"), L(name)),
        "effects": [["set_attr", "d", "plan_value", T(plan_value_term)]],
    }


RULES = [
    couple("harm",
           # plan_base + resent_gain*resentment - aff_gain*affection
           Minus(Plus(_PLANBASE, Times(_RESENT, _RESENTMENT)),
                 Times(_AFF, _AFFECTION)),
           "DIRECTED HARM couples to the held Bond: resentment RAISES the deep "
           "value of harming this target, affection LOWERS it. You do not harm "
           "someone you love; a resented rival scores higher. The fast pull "
           "(impulse) stays the LOW harm prior -- the Bond only shapes the deep "
           "re-score, so violence stays rare and, when it happens, is DIRECTED."),
    couple("help",
           Plus(_PLANBASE, Times(_AFF, _AFFECTION)),
           "DIRECTED HELP couples to affection: you aid those you care for. "
           "help's fast pull is already HIGH (pro-social prior); the Bond points "
           "it at the right person."),
    couple("transfer",
           Plus(_PLANBASE, Times(_AFF, _AFFECTION)),
           "DIRECTED GIVING couples to affection (Mauss: the gift builds the "
           "bond; you give to those you are close to)."),
]


def build():
    return {
        "id": "bigville_conduct",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "DIRECTED, BOND-COUPLED CONDUCT (block 281000). The affordance "
            "vocabulary (280000) offers agent-directed actions whenever a target "
            "is in range; these rules make WHOM you act on read the held Bond "
            "(277000). Each directed action's DEEP (plan_value) score = plan_base "
            "+ a coupling to the Bond's affect toward its target: harm rises with "
            "resentment and falls with affection; help/transfer rise with "
            "affection. The FAST pull (impulse = vocabulary base_weight; harm LOW, "
            "help HIGH) is unchanged -- the Bond only shapes the model-based "
            "re-score, so the decision core (279000) collapse directs harm at a "
            "resented rival (not a friend) and giving/aid toward the cared-for, "
            "while violence stays rare. Reading held affect is a RULE (graph "
            "read), not adapter arithmetic. FALSIFIER: conduct_resent_gain = "
            "conduct_affection_gain = 0 collapses plan_value to plan_base -> no "
            "directedness (rival indistinguishable from friend). Gains are knobs "
            "on the ConductState. ZERO new Rust; self_load_only."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": RULES,
    }


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "seeds", "bigville_conduct.json")
    with open(out, "w") as f:
        json.dump(build(), f, indent=1)
    print(f"wrote {out}: {len(build()['rules'])} coupling rules")
