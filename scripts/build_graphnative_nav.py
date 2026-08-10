"""The jabberwock builds the drive-to-stable-and-probe loop GRAPH-NATIVE — no Python decisions. Uses what the
graph already holds: persistent Features with vel_row/vel_col (identity + motion), reached cells with row/col/
_adist (reachability + arrival). Five rules added to feature_navigation.json:
  kind_mover / kind_static  — static-vs-mover from VELOCITY (the invariant identity layer, as a rule not a host
                              tracker): a feature that moves is a mover; an unclassified still one is static.
  commit_feature_goal       — DRIVE: the nav-target feature's reached cell becomes the committed goal (replaces
                              the host bridge); the existing flood/hop drives there.
  probe_on_arrival          — PROBE: when the avatar is ON the target (its cell's _adist==0), Select it + mark
                              affordances_known. A rule, so it runs in the SAME fixpoint as the hop (no override).
  release_feature_goal      — clear the committed goal once probed, so the next salient target can commit.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "seeds", "feature_navigation.json")
d = json.load(open(p))

def A(v, k): return {"type": "Attr", "node": {"type": "Var", "name": v}, "key": k}
def P0(v, k): return {"type": "Plus", "items": [A(v, k), {"type": "Lit", "value": 0}]}
def L(x): return {"type": "Lit", "value": x}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Neg(t): return {"type": "Times", "items": [L(-1.0), t]}
def Sub(a, b): return {"type": "Plus", "items": [a, Neg(b)]}
def Near(av, ak, bv, bk):           # |a.ak - b.bk| < 1   (centroid ~ cell)
    return And(Lt(Sub(P0(av, ak), P0(bv, bk)), L(1.0)), Lt(Sub(P0(bv, bk), P0(av, ak)), L(1.0)))
def speed_sq(v):
    return {"type": "Plus", "items": [{"type": "Times", "items": [P0(v, "vel_row"), P0(v, "vel_row")]},
                                       {"type": "Times", "items": [P0(v, "vel_col"), P0(v, "vel_col")]}]}

rules = [
    {"name": "kind_mover", "match": [["game", "has_feature", "F"]],
     "where": And(Gt(speed_sq("F"), L(1.0)), Not(Eq(A("F", "kind"), L("mover"))), Not(Eq(A("F", "kind"), L("meter")))),
     "effects": [["set_attr", "F", "kind", "mover"]]},
    {"name": "kind_static", "match": [["game", "has_feature", "F"]],
     "where": And(Eq(A("F", "kind"), L("unknown")), Not(Gt(speed_sq("F"), L(1.0)))),
     "effects": [["set_attr", "F", "kind", "static"]]},
    {"name": "commit_feature_goal", "match": [["game", "has_feature", "F"], ["game", "reached", "C"]],
     "where": And(Eq(P0("F", "is_nav_target"), L(1.0)), Near("C", "row", "F", "cy"), Near("C", "col", "F", "cx")),
     "effects": [["add_edge", "game", "committed_goal", "C"]]},
    {"name": "probe_on_arrival", "match": [["game", "has_feature", "F"], ["game", "reached", "C"]],
     "where": And(Eq(P0("F", "is_nav_target"), L(1.0)), Near("C", "row", "F", "cy"), Near("C", "col", "F", "cx"),
                  Lt(P0("C", "_adist"), L(1.0)), Not(Eq(P0("F", "affordances_known"), L(1.0)))),
     "effects": [["set_attr", "game", "chosen_action", "Select"], ["set_attr", "F", "affordances_known", 1.0]]},
    {"name": "release_feature_goal", "match": [["game", "has_feature", "F"], ["game", "committed_goal", "C"]],
     "where": And(Eq(P0("F", "is_nav_target"), L(1.0)), Eq(P0("F", "affordances_known"), L(1.0)),
                  Near("C", "row", "F", "cy"), Near("C", "col", "F", "cx")),
     "effects": [["del_edge", "game", "committed_goal", "C"], ["set_attr", "F", "is_nav_target", 0.0]]},
]
names = {r["name"] for r in rules}
d["rules"] = [r for r in d["rules"] if r["name"] not in names] + rules
json.dump(d, open(p, "w"), indent=1)
print("added graph-native rules:", sorted(names))
