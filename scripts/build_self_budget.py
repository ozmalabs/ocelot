"""seeds/self_budget.json — the jabberwock's SELF-DEFINED BUDGET, composed from its own shape-reading.

The problem (informed to it): ls20's meter is a TURN meter, not a clock; ARC-AGI has NO time limit. So nothing
external governs how long it runs — its budget is ITS OWN to define. Its shape faculty reads this as
feedback_control: regulate my investment toward a set_point by negative feedback. The set_point is curiosity
satisfied (understanding still growing); the feedback is the PAYOFF — keep spending turns while understanding
grows, and when it PLATEAUS (no new feature understood for K turns) the negative feedback says "I have invested
enough here" -> budget_spent. The host loop then just keeps ticking until the agent itself declares its budget
spent (or the game ends). No clock, no fixed cap — the budget is self-defined.
"""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def ADD(a, b): return {"type": "Plus", "items": [a, b]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def GT(a, b): return {"type": "Gt", "a": a, "b": b}
def GTE(a, b): return {"type": "Gte", "a": a, "b": b}
def AND(*xs): return {"type": "And", "items": list(xs)}
def ITE(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def FILTER(s, v, p): return {"type": "Filter", "source": s, "var_name": v, "predicate": p}
def NODESOF(t): return {"type": "NodesOfType", "node_type": t}
def COUNT(s): return {"type": "Count", "source": s}
def T(x): return {"__term__": x}
is_av = lambda v: EQ(P0(V(v), "is_avatar_cell"), L(1.0))

K_PATIENCE = 20.0   # the agent's SELF-DEFINED patience: invest this many turns of no new understanding, then stop.

# understanding = features the collapse has explained (resolved, whether probed directly or collapsed by
# leverage). Investment pays while collapse is still discharging unexplained structure; when it plateaus
# (nothing left cheap enough to collapse), the agent self-declares the budget spent.
understood = COUNT(FILTER(NODESOF("Feature"), "f", EQ(P0(V("f"), "resolved"), L(1.0))))
grew = GT(understood, P0(V("game"), "understood_seen"))
plateau_new = ITE(grew, L(0.0), ADD(P0(V("game"), "plateau"), L(1.0)))

# feedback_control, once per turn (guarded on budget_stamp != frame): reset the plateau when understanding
# grows (the investment paid off), else advance it; when the plateau reaches the self-defined patience,
# declare the budget spent. NO external clock — the agent regulates its own investment by its own payoff.
regulate_budget = {
    "name": "regulate_budget",
    "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), NEQ(P0(V("game"), "budget_stamp"), P0(V("game"), "frame"))),
    "effects": [
        ["set_attr", "game", "plateau", T(plateau_new)],
        ["set_attr", "game", "understood_seen", T(understood)],
        ["set_attr", "game", "budget_spent", T(ITE(GTE(plateau_new, L(K_PATIENCE)), L(1.0), L(0.0)))],
        ["set_attr", "game", "budget_stamp", T(P0(V("game"), "frame"))]]}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "self_budget", "version": "1.0.0", "depends_on": [],
        "description": ("The agent's self-defined budget (feedback_control): regulate_budget keeps the run "
            "going while understanding grows and declares `budget_spent` when it plateaus for K turns. No "
            "clock, no fixed cap — the budget is the agent's own, set by the payoff of its curiosity."),
        "nodes": [], "edges": [], "productions": [], "concepts": [], "rules": [regulate_budget]}
path = os.path.join(ROOT, "seeds", "self_budget.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/self_budget.json:", [r["name"] for r in seed["rules"]])
