"""seeds/collapse_curiosity.json — NOT escalation. Form the order-N curiosity STRUCTURE, then pursue goals
for MAXIMUM COLLAPSE with MINIMUM EFFORT.

The unexplained is not a flat list — it has structure. Features that share a kind are ONE thing seen many
times (order-2: the "same-as" relation); kinds that share a meta-property are one thing again (order-3); …
Understanding a representative COLLAPSES the whole group — one observation explains many. So curiosity is a
field of uncertainty over that structure, and the efficient way to discharge it is to probe the point of
MAXIMUM LEVERAGE (the largest group — most collapse) at MINIMUM COST (one cheap observation), then let the
collapse PROPAGATE. This is the compression principle: explain the most with the least.

Six rules, all firing natively in master_tick:
  stamp_collapse        — each unresolved feature's collapse potential = how many same-kind unknowns it covers.
  select_collapse_target— target the unresolved feature of MAXIMUM collapse (argmax leverage; effort uniform = one probe).
  probe_target          — spend ONE observation on the target (minimum effort) and resolve it.
  collapse_kind         — a resolved feature COLLAPSES every same-kind unknown (propagation — the maximum collapse).
  release_target        — drop the target once collapsed so the next-highest-leverage probe is chosen.
  satisfy_goal          — a collapsed feature satisfies the curiosity goal about it.

Result: N features explained in ~(#kinds) cheap probes, biggest groups first — not N×K observations.
"""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def ADD(a, b): return {"type": "Plus", "items": [a, b]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def NOT(x): return {"type": "Not", "arg": x}
def GT(a, b): return {"type": "Gt", "a": a, "b": b}
def GTE(a, b): return {"type": "Gte", "a": a, "b": b}
def AND(*xs): return {"type": "And", "items": list(xs)}
def OR(*xs): return {"type": "Or", "items": list(xs)}
def LT(a, b): return {"type": "Lt", "a": a, "b": b}
def ITE(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def NEIGH(var, et): return {"type": "Neighbours", "node": V(var), "edge_type": et, "any_type": False}
def FILTER(s, v, p): return {"type": "Filter", "source": s, "var_name": v, "predicate": p}
def NODESOF(t): return {"type": "NodesOfType", "node_type": t}
def COUNT(s): return {"type": "Count", "source": s}
def EXISTS(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def T(x): return {"__term__": x}

K_PROBE = 2.0   # MINIMUM effort: observations to confirm a representative before the collapse propagates.

unresolved = lambda v: NEQ(P0(V(v), "resolved"), L(1.0))

# Group by VALUE (the cell colour): same-value features are instances of ONE thing (5 value-9 objects, 3
# value-5, …). kind is "unknown" until the eye has watched motion; value is the immediate visual structure.
# The collapse potential of a feature = how many same-value unknowns probing it would cover (its leverage).
grp_count = COUNT(FILTER(NODESOF("Feature"), "g",
    AND(EQ(A(V("g"), "value"), A(V("F"), "value")), NEQ(P0(V("g"), "resolved"), L(1.0)))))

stamp_collapse = {
    "name": "stamp_collapse",
    "match": [["game", "has_feature", "F"]],
    "where": AND(unresolved("F"), NEQ(P0(V("F"), "grp_stamp"), P0(V("game"), "frame"))),
    "effects": [["set_attr", "F", "grp", T(grp_count)],
                ["set_attr", "F", "grp_stamp", T(P0(V("game"), "frame"))]]}

# F is its group's REPRESENTATIVE: the min-(cx,cy) unresolved feature of its value. Because the rule engine
# applies all matches at once, a global "one target" guard can't serialise — so the representative is fixed
# STRUCTURALLY (exactly one per group), and only representatives are ever probed. The rest collapse for free.
is_rep = NOT(EXISTS(NODESOF("Feature"), "g",
    AND(EQ(A(V("g"), "value"), A(V("F"), "value")), unresolved("g"),
        OR(LT(A(V("g"), "cx"), A(V("F"), "cx")),
           AND(EQ(A(V("g"), "cx"), A(V("F"), "cx")), LT(A(V("g"), "cy"), A(V("F"), "cy")))))))
# F's group is the largest still unexplained — MAXIMUM collapse first.
is_max_grp = NOT(EXISTS(NODESOF("Feature"), "g",
    AND(unresolved("g"), GT(P0(V("g"), "grp"), P0(V("F"), "grp")))))

# probe the representative of the biggest unexplained group (max collapse), one observation per turn (min
# effort), and resolve it after K_PROBE. No per-instance investigation — only one probe per group.
probe_representative = {
    "name": "probe_representative",
    "match": [["game", "has_feature", "F"]],
    "where": AND(unresolved("F"), GT(P0(V("F"), "grp"), L(0.0)),
                 NEQ(P0(V("F"), "obs_stamp"), P0(V("game"), "frame")), is_max_grp, is_rep),
    "effects": [
        ["set_attr", "F", "observed", T(ADD(P0(V("F"), "observed"), L(1.0)))],
        ["set_attr", "F", "obs_stamp", T(P0(V("game"), "frame"))],
        ["set_attr", "game", "probes", T(ADD(P0(V("game"), "probes"), L(1.0)))],
        ["set_attr", "F", "resolved",
            T(ITE(GTE(ADD(P0(V("F"), "observed"), L(1.0)), L(K_PROBE)), L(1.0), L(0.0)))]]}

# THE COLLAPSE: a resolved representative explains every same-value unknown in one stroke (propagation).
collapse_kind = {
    "name": "collapse_kind",
    "match": [["game", "has_feature", "F"], ["game", "has_feature", "G"]],
    "where": AND(EQ(P0(V("F"), "resolved"), L(1.0)), NEQ(P0(V("G"), "resolved"), L(1.0)),
                 EQ(A(V("F"), "value"), A(V("G"), "value"))),
    "effects": [["set_attr", "G", "resolved", 1.0],
                ["set_attr", "G", "collapsed", 1.0]]}   # marked: explained by leverage, not by its own probe.

# a collapsed feature satisfies the curiosity goal about it.
satisfy_goal = {
    "name": "satisfy_goal",
    "match": [["F", "has_understand_goal", "G"]],
    "where": AND(EQ(P0(V("F"), "resolved"), L(1.0)), NEQ(P0(V("G"), "resolved"), L(1.0))),
    "effects": [["set_attr", "G", "resolved", 1.0], ["set_attr", "G", "status", "satisfied"]]}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "collapse_curiosity", "version": "1.0.0", "depends_on": [],
        "description": ("Form the order-N curiosity structure and pursue it for MAXIMUM COLLAPSE, MINIMUM "
            "EFFORT: stamp_collapse (leverage = same-kind unknowns covered), select_collapse_target (argmax "
            "leverage), probe_target (one cheap observation), collapse_kind (a resolved feature propagates to "
            "every same-kind unknown), release_target, satisfy_goal. N features explained in ~#kinds probes, "
            "biggest groups first. Fires natively in master_tick."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": [stamp_collapse, probe_representative, collapse_kind, satisfy_goal]}
path = os.path.join(ROOT, "seeds", "collapse_curiosity.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/collapse_curiosity.json:", [r["name"] for r in seed["rules"]])
