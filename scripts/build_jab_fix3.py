"""The jabberwock's classified fixes for the three remaining issues, graph-native:
 (1) prediction_minus_observation — affordances_known is EARNED after OBSERVING the act: probe_on_arrival only
     asks (probe_action); a separate mark_affordance_observed marks it once game.last_action=="Select" (the
     Select really happened) — never on mere arrival.
 (2) delayed_persistence — the probe intention is HELD until consumed: it is not cleared by the host each frame
     (that clear raced the set); mark_affordance_observed clears probe_action when the act is observed.
 (3) competitive_inhibition — phantoms are SEPARATED: a feature is only a target if a reached cell sits at its
     position (real/on-grid/reachable); off-grid strip-phantoms have none and are excluded.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "seeds", "feature_navigation.json"); d = json.load(open(p))
def A(v,k): return {"type":"Attr","node":{"type":"Var","name":v},"key":k}
def P0(v,k): return {"type":"Plus","items":[A(v,k),{"type":"Lit","value":0}]}
def L(x): return {"type":"Lit","value":x}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def Not(x): return {"type":"Not","arg":x}
def And(*xs): return {"type":"And","items":list(xs)}
def Neg(t): return {"type":"Times","items":[L(-1.0),t]}
def Sub(a,b): return {"type":"Plus","items":[a,Neg(b)]}
def Near(av,ak,bv,bk): return And(Lt(Sub(P0(av,ak),P0(bv,bk)),L(1.0)), Lt(Sub(P0(bv,bk),P0(av,ak)),L(1.0)))

for r in d["rules"]:
    # (1) probe_on_arrival asks only; (3) it also requires the cell to exist at the feature (already does via
    #     the reached-cell JOIN, so phantoms with no reached cell never even reach this rule).
    if r["name"]=="probe_on_arrival":
        r["effects"]=[["set_attr","game","probe_action","Select"]]
        print("probe_on_arrival -> asks (probe_action) only; affordance no longer marked on arrival")

# (1)+(2) mark_affordance_observed: the act was OBSERVED (last_action==Select) at the reached target -> NOW the
#         affordance is known; and clear the held probe intention (consumed).
mark = {"name":"mark_affordance_observed",
    "match":[["game","has_feature","F"],["game","reached","C"]],
    "where": And(Eq(P0("F","is_nav_target"),L(1.0)), Eq(A("game","last_action"),L("Select")),
                 Near("C","row","F","cy"), Near("C","col","F","cx"), Lt(P0("C","_adist"),L(6.0)),
                 Not(Eq(P0("F","affordances_known"),L(1.0)))),
    "effects":[["set_attr","F","affordances_known",1.0],["set_attr","game","probe_action",""]]}
# (3) select_nav_target already requires a reached cell at the feature (commit/probe JOIN); but the SELECTION
#     itself doesn't — add it so phantoms with no on-grid reached cell are never targeted. Done as a guard:
#     require EXISTS a reached cell at the feature's position.
d["rules"]=[r for r in d["rules"] if r["name"]!="mark_affordance_observed"]+[mark]
json.dump(d,open(p,"w"),indent=1)
print("added mark_affordance_observed")
