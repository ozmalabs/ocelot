"""seeds/pursue_curiosity.json — the agent PURSUES its curiosity goals (the understand-drive's "observe ->
fold into model"), graph-native, fired by master_tick.

It already MINTS a curiosity goal per perceived-but-unresolved Feature (self_fuel_drive). Pursuing one, for a
confined agent on a dynamic world, is OBSERVATION: watch the thing it is curious about across turns and, once
its classification has held (it has a definite kind, observed for K turns), FOLD that into the model — mark the
Feature resolved. Understanding grows as it pursues; the self-budget then keeps it investing (understanding is
growing) until the unexplained is exhausted. Order-1 curiosity (what is each thing); the order-N escalation
(how the things RELATE — the mechanic) is the next curiosity once these are resolved.
"""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def ADD(a, b): return {"type": "Plus", "items": [a, b]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def GTE(a, b): return {"type": "Gte", "a": a, "b": b}
def AND(*xs): return {"type": "And", "items": list(xs)}
def ITE(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def NEIGH(var, et): return {"type": "Neighbours", "node": V(var), "edge_type": et, "any_type": False}
def EXISTS(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def T(x): return {"__term__": x}

K_OBSERVE = 10.0   # turns of stable observation before the agent folds a feature into its model (resolves it).

# pursue: for an unresolved Feature it is CURIOUS about (has_understand_goal) and that it HAS classified (a
# definite, non-unknown kind), accrue one observation per turn (frame-stamped so once per turn), and once it
# has watched it K turns, FOLD it into the model -> resolved=1 (understanding grows).
pursue_curiosity = {
    "name": "pursue_curiosity_by_observation",
    "match": [["game", "has_feature", "F"]],
    "where": AND(NEQ(P0(V("F"), "resolved"), L(1.0)),
                 EXISTS(NEIGH("F", "has_understand_goal"), "_g", L(True)),
                 NEQ(A(V("F"), "kind"), L("unknown")),
                 NEQ(P0(V("F"), "obs_stamp"), P0(V("game"), "frame"))),
    "effects": [
        ["set_attr", "F", "observed", T(ADD(P0(V("F"), "observed"), L(1.0)))],
        ["set_attr", "F", "obs_stamp", T(P0(V("game"), "frame"))],
        ["set_attr", "F", "resolved",
            T(ITE(GTE(ADD(P0(V("F"), "observed"), L(1.0)), L(K_OBSERVE)), L(1.0), L(0.0)))]]}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "pursue_curiosity", "version": "1.0.0", "depends_on": [],
        "description": ("The agent pursues its curiosity goals by OBSERVATION: pursue_curiosity_by_observation "
            "accrues a per-feature observation count each turn and folds a classified feature into the model "
            "(resolved=1) after K turns. Understanding grows as it pursues; fires natively in master_tick."),
        "nodes": [], "edges": [], "productions": [], "concepts": [], "rules": [pursue_curiosity]}
path = os.path.join(ROOT, "seeds", "pursue_curiosity.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/pursue_curiosity.json:", [r["name"] for r in seed["rules"]])
