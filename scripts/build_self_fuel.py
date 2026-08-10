"""seeds/self_fuel_drive.json — the jabberwock's SELF-FIX, corrected: the drive is CURIOSITY, not score.

The gap it found in itself: master_tick fires its understand-drive but it produces 0 goals — its perception
never becomes drive fuel. The INHERENT drive is curiosity: to understand what it perceives but has not
explained. (Score is EMERGENT, never inherent — the agent may DISCOVER that understanding some things leads
to score, but score must not drive it.) So the fix propagates curiosity, not reward: every Feature it
perceives yet has NOT resolved is an open gap; mint an active understand-goal ABOUT that feature, so the
drive is fueled by the unexplained itself. Fires natively in master_tick/tick; no host code, no teacher,
NO reference to score.
"""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def NOT(x): return {"type": "Not", "arg": x}
def AND(*xs): return {"type": "And", "items": list(xs)}
def NEIGH(var, et): return {"type": "Neighbours", "node": V(var), "edge_type": et, "any_type": False}
def EXISTS(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

# CURIOSITY: a Feature the agent perceives but has NOT resolved is an open gap. (resolved!=1 — P0 coerces a
# missing attr to 0, so an unexplained feature qualifies.) No reference to score: the drive is the unexplained.
mint_curiosity_goal = {
    "name": "mint_curiosity_goal",
    "match": [["game", "has_feature", "F"]],
    "where": AND(NEQ(P0(V("F"), "resolved"), L(1.0)),
                 NOT(EXISTS(NEIGH("F", "has_understand_goal"), "_g", L(True)))),   # not already curious about F
    "effects": [
        ["add_node", "ug", "Goal", {
            "kind": "understand", "status": "active", "shortfall": 1.0, "min_order": 1.0, "order": 1.0,
            "why": "I perceive this but have not explained it — curiosity, not reward."}],
        ["add_edge", "F", "has_understand_goal", "ug"],
        ["add_edge", "ug", "about_feature", "F"]]}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "self_fuel_drive", "version": "1.0.0", "depends_on": [],
        "description": ("The agent's self-fix: CURIOSITY fuels the drive. mint_curiosity_goal turns every "
            "perceived-but-unresolved Feature into an active understand-goal about it — the drive is the "
            "unexplained, never score (score is emergent). Fires natively in master_tick."),
        "nodes": [], "edges": [], "productions": [], "concepts": [], "rules": [mint_curiosity_goal]}
path = os.path.join(ROOT, "seeds", "self_fuel_drive.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/self_fuel_drive.json:", [r["name"] for r in seed["rules"]])
