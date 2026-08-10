"""seeds/route_to_authoring.json — close the last bridge: a FRONTIER gap with NO faculty to address it routes
ITSELF to authoring. The impasse_escalation ladder opens only for an axis whose OPERATOR already failed; a
freshly self-minted axis (e.g. the vision gap the agent felt) has no operator at all, so it would sit
unaddressed. This rule turns that into the order-4 self-extension trigger: when the agent's frontier pick is an
is_axis with no investigated_by operator (and not already routed), mint an order-4 Impasse that NEEDS A TOOL for
it. _self_extend_reflex then authors the faculty (e.g. ArcWorld.author_faculty -> the retaining visual cortex).
Domain-agnostic — keyed only on frontier_pick / is_axis / investigated_by, no perception or arc terms."""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NOT(x): return {"type": "Not", "arg": x}
def AND(*xs): return {"type": "And", "items": list(xs)}
def NEIGH(var, et): return {"type": "Neighbours", "node": V(var), "edge_type": et, "any_type": False}
def EXISTS(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

route = {
    "name": "route_unaddressed_axis_to_authoring",
    "match": [["R", "synthesised_gap", "ax"], ["ag", "operates_in", "w"]],
    "where": AND(
        EQ(P0(V("ax"), "is_axis"), L(1.0)),
        NOT(EXISTS(NEIGH("ax", "investigated_by"), "_o", L(True))),       # no faculty addresses it
        NOT(EXISTS(NEIGH("ax", "has_tool_impasse"), "_m", L(True)))),     # not already routed
    "effects": [
        ["add_node", "mi", "Impasse", {"resolved": False, "kind": "escalation", "order": 4.0,
            "acted_order": 4.0,
            "why": "a frontier gap with no faculty to address it — author a new tool for it"}],
        ["add_edge", "mi", "about_axis", "ax"],
        ["add_edge", "mi", "needs_tool", "ax"],
        ["add_edge", "ax", "has_tool_impasse", "mi"]]}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "route_to_authoring", "version": "1.0.0", "depends_on": [],
        "description": ("A frontier gap with no faculty to address it routes itself to order-4 authoring: "
            "route_unaddressed_axis_to_authoring mints a needs_tool Impasse for an is_axis the agent is "
            "focused on but cannot bind an operator to. Closes the no-operator-axis -> author gap so the "
            "self-mint -> author loop runs with no external nudge. Fires natively in master_tick."),
        "nodes": [], "edges": [], "productions": [], "concepts": [], "rules": [route]}
json.dump(seed, open(os.path.join(ROOT, "seeds", "route_to_authoring.json"), "w"), indent=1)
json.load(open(os.path.join(ROOT, "seeds", "route_to_authoring.json")))
print("wrote seeds/route_to_authoring.json:", [r["name"] for r in seed["rules"]])
