"""seeds/order_n_curiosity.json — the agent BUILDS ORDER-N curiosity: it escalates its curiosity by ORDER,
the same finite-difference move order_n_postulates uses on knowledge, here on the curiosity drive itself.

  order-1 : what IS each thing?            (a Feature -> resolved by observation; existing)
  order-2 : how does it RELATE?            (mint when order-1 is satisfied; pursue by observation)
  order-3 : how do those relations relate? (mint when order-2 is satisfied) … up to MAX_ORDER.

Three rules, all firing natively in master_tick:
  resolve_order1_goal — when a Feature resolves, its order-1 curiosity goal is satisfied.
  escalate_curiosity  — a satisfied order-k curiosity goal (k < MAX) differentiates into an order-(k+1) goal.
  pursue_higher_order — an active order>=2 goal is pursued by observation and folded into the model (resolved).

The self-budget counts resolved curiosity goals across ALL orders, so escalating + resolving higher-order
curiosity IS understanding growing — the agent keeps investing until it has climbed the orders and the
unexplained (at every order up to MAX) is exhausted; then its curiosity plateaus and it self-stops.
"""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def ADD(a, b): return {"type": "Plus", "items": [a, b]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def LT(a, b): return {"type": "Lt", "a": a, "b": b}
def GTE(a, b): return {"type": "Gte", "a": a, "b": b}
def AND(*xs): return {"type": "And", "items": list(xs)}
def ITE(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def T(x): return {"__term__": x}

MAX_ORDER = 3.0
K_OBSERVE = 8.0

# R1: a Feature is understood (resolved) -> its order-1 curiosity goal is satisfied.
resolve_order1_goal = {
    "name": "resolve_order1_goal",
    "match": [["F", "has_understand_goal", "G"]],
    "where": AND(EQ(P0(V("F"), "resolved"), L(1.0)), EQ(P0(V("G"), "order"), L(1.0)),
                 NEQ(P0(V("G"), "resolved"), L(1.0))),
    "effects": [["set_attr", "G", "resolved", 1.0]]}

# R2: ESCALATE — a satisfied order-k curiosity goal (k < MAX), not yet escalated, differentiates into an
#     order-(k+1) curiosity goal. The recursive order-N step, on the curiosity drive itself.
escalate_curiosity = {
    "name": "escalate_curiosity",
    "match": [["F", "has_understand_goal", "G"]],
    "where": AND(EQ(P0(V("G"), "resolved"), L(1.0)), LT(P0(V("G"), "order"), L(MAX_ORDER)),
                 NEQ(P0(V("G"), "escalated"), L(1.0))),
    "effects": [
        ["add_node", "G2", "Goal", {"kind": "understand", "status": "active",
            "why": "I understand it at this order; now I am curious how it RELATES at the next."}],
        ["set_attr", "G2", "order", T(ADD(P0(V("G"), "order"), L(1.0)))],
        ["add_edge", "F", "has_understand_goal", "G2"],
        ["add_edge", "G", "has_child", "G2"],
        ["set_attr", "G", "escalated", 1.0]]}

# R3: pursue a higher-order (>=2) curiosity goal by observation; fold it into the model after K turns.
pursue_higher_order = {
    "name": "pursue_higher_order",
    "match": [["game", "has_feature", "F"], ["F", "has_understand_goal", "G"]],
    "where": AND(GTE(P0(V("G"), "order"), L(2.0)), NEQ(P0(V("G"), "resolved"), L(1.0)),
                 NEQ(P0(V("G"), "obs_stamp"), P0(V("game"), "frame"))),
    "effects": [
        ["set_attr", "G", "observed", T(ADD(P0(V("G"), "observed"), L(1.0)))],
        ["set_attr", "G", "obs_stamp", T(P0(V("game"), "frame"))],
        ["set_attr", "G", "resolved",
            T(ITE(GTE(ADD(P0(V("G"), "observed"), L(1.0)), L(K_OBSERVE)), L(1.0), L(0.0)))]]}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "order_n_curiosity", "version": "1.0.0", "depends_on": [],
        "description": ("Order-N curiosity: resolve_order1_goal (a resolved Feature satisfies its order-1 "
            "goal), escalate_curiosity (a satisfied order-k goal differentiates into order-(k+1), up to "
            "MAX_ORDER=3), pursue_higher_order (observe + fold a >=order-2 goal). The agent climbs the orders "
            "of its own curiosity — things, then relations, then relations-of-relations — natively in master_tick."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": [resolve_order1_goal, escalate_curiosity, pursue_higher_order]}
path = os.path.join(ROOT, "seeds", "order_n_curiosity.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/order_n_curiosity.json:", [r["name"] for r in seed["rules"]])
