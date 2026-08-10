"""Emit seeds/bigville_supergraph_conduct.json (block 282000-a) -- conduct
valuation re-expressed as a SUPERGRAPH sum: the town is a supergraph (a level of
selection above the individual), and a directed action's value is the actor's own
stake PLUS how much it weights the target's fulfilment change.

  plan_value(d) = plan_base(d)  +  ( ep.w_supergraph · bond_w(m->o) ) · target_effect(d)

  bond_w(m->o)  = altruism_bias(m->o) + k·affect_affection(m->o) - k·affect_resentment(m->o)

This ONE action-type-agnostic rule REPLACES the three hand-tuned
`conduct_couple_{harm,help,transfer}` rules (281000). The sign of the coupling
now lives in `target_effect` (harm LOWERS the target's fulfilment = negative;
help/transfer RAISE it = positive) times a SIGNED per-pair weight `bond_w`, so:
  * harming a RESENTED rival (bond_w < 0) × (target_effect < 0) -> scores UP;
  * helping a LOVED friend (bond_w > 0) × (target_effect > 0) -> scores UP;
  * harming a friend, or helping a rival, scores DOWN.

WHAT THE SUPERGRAPH FORM ADDS OVER THE 281000 COUPLING (design doc
TOWN_SUPERGRAPH_BRIDGE_DESIGN.md, verified against the code):
  * `ep.w_supergraph` -- the PER-AGENT psychopathy knob (EmotionParams,
    core_emotions.json) -- multiplies ALL per-pair care: a global psychopath
    (w_supergraph=0) weights NO ONE regardless of any Bond. (In 281000 there was
    no such knob.)
  * `altruism_bias` -- a purpose-named Bond slot that was DEAD (minted by
    bigville_bond_world, read by ZERO rules; blood-kin seeds it to 0.3) -- now
    does work: it is the per-pair care PRIOR, dissociable from the transient
    affect slots ("you do not need to LIKE your kin").
  * SPITE gets a principled per-pair form: a negative `bond_w` IS per-pair spite
    (the negative mirror of the collective weight), no separate knob.

Term shape is the ONLY existing multiplicative `w_supergraph · magnitude`
precedent: `bc_pick_cheapest_hands` in bigville_coll_evict.json. ZERO new Rust.
`target_effect` is published per directed DecAction by the world adapter (the
same adapter-publishes-magnitude split as `supergraph_contribution`/`injury_mag`).
Load this seed INSTEAD OF bigville_conduct (both write plan_value -- supersede,
never coexist). self_load_only.
"""
from __future__ import annotations
import json
import os


def V(n):        return {"type": "Var", "name": n}
def A(node, k):  return {"type": "Attr", "node": node, "key": k}
def Plus(*it):   return {"type": "Plus", "items": list(it)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*it):  return {"type": "Times", "items": list(it)}
def T(term):     return {"__term__": term}

# bond_w(m->o) = altruism_bias + k*affect_affection - k*affect_resentment
_K = A(V("m"), "conduct_k")
_BOND_W = Minus(
    Plus(A(V("bond"), "altruism_bias"), Times(_K, A(V("bond"), "affect_affection"))),
    Times(_K, A(V("bond"), "affect_resentment")))

# w_super_eff = ep.w_supergraph * bond_w  (global psychopathy gate * per-pair)
_W_EFF = Times(A(V("ep"), "w_supergraph"), _BOND_W)

# plan_value = plan_base + w_super_eff * target_effect
_PLAN = Plus(A(V("d"), "plan_base"), Times(_W_EFF, A(V("d"), "target_effect")))

RULE = {
    "name": "conduct_supergraph_value",
    "batch": False,
    "comment": (
        "SUPERGRAPH CONDUCT VALUATION (block 282000). One action-type-agnostic "
        "rule replacing the three conduct_couple_* rules: a directed action's "
        "plan_value = plan_base + (ep.w_supergraph * bond_w) * target_effect, "
        "bond_w = altruism_bias + k*affect_affection - k*affect_resentment. The "
        "town is a supergraph -- the actor weights the target's fulfilment change "
        "(target_effect) by how much it cares about that target (signed per-pair "
        "bond_w) scaled by the global psychopathy gate (ep.w_supergraph). Sign "
        "lives in target_effect (harm<0, help/transfer>0), so a negative bond_w "
        "(resentment) times a negative harm-effect scores harming a rival UP, "
        "while helping a friend (positive*positive) scores UP. Matches the "
        "existing conduct edges (in_scene/aims_at/holds_bond/toward) + the actor's "
        "EmotionParams (has_ep). Only fires on DIRECTED actions (aims_at present). "
        "Term shape = bigville_coll_evict.json bc_pick_cheapest_hands. ZERO new "
        "Rust. FALSIFIER: conduct_k=0 AND altruism_bias=0 -> bond_w=0 -> "
        "plan_value=plan_base -> no directedness. PSYCHOPATHY: ep.w_supergraph=0 "
        "-> no per-pair care at all."),
    "match": [["m", "in_scene", "d"], ["d", "aims_at", "o"],
              ["m", "holds_bond", "bond"], ["bond", "toward", "o"],
              ["m", "has_ep", "ep"]],
    "effects": [["set_attr", "d", "plan_value", T(_PLAN)]],
}


def build():
    return {
        "id": "bigville_supergraph_conduct",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "SUPERGRAPH CONDUCT VALUATION (block 282000). The town is a supergraph "
            "(a level of selection above the individual); a directed action's value "
            "is the actor's own stake (plan_base) PLUS the target's fulfilment "
            "change (target_effect) weighted by how much the actor cares about that "
            "target -- a SIGNED per-pair weight bond_w (from the Bond) scaled by the "
            "global psychopathy gate ep.w_supergraph. ONE action-type-agnostic rule "
            "conduct_supergraph_value replaces the three hand-tuned conduct_couple_* "
            "rules (281000): plan_value = plan_base + (ep.w_supergraph*bond_w)"
            "*target_effect, bond_w = altruism_bias + k*affect_affection "
            "- k*affect_resentment. Revives the DEAD Bond slot altruism_bias (the "
            "per-pair care prior), adds the per-agent psychopathy knob (w_supergraph"
            "=0 -> weights no one), and gives spite a principled per-pair form "
            "(negative bond_w). Term shape = coll_evict bc_pick_cheapest_hands (the "
            "only existing multiplicative w_supergraph*magnitude); ZERO new Rust. "
            "target_effect published per directed DecAction by the world adapter. "
            "Load INSTEAD OF bigville_conduct (both write plan_value). self_load_only."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": [RULE],
    }


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "seeds", "bigville_supergraph_conduct.json")
    with open(out, "w") as f:
        json.dump(build(), f, indent=1)
    print(f"wrote {out}: 1 unified supergraph rule")
