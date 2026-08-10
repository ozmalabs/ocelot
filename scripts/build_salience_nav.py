"""Make the EXISTING feature-nav SALIENCE-driven, graph-native (no new faculty, no Python target list):
 1) mark_feature_salience — salience = MOTION (movers stand out, +10) − population(value) (rarer colour stands
    out): pop-out / signal-over-noise, the arc3_game salience principle, now also temporal contrast.
 2) re-order select_nav_target by salience instead of reach_dist — it already picks the unexplained reachable
    feature; now it picks the MOST SALIENT one, so the agent attends to what stands out instead of the nearest.
Idempotent: re-running only updates the salience rule (the reach_dist->salience swap won't re-match).
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "seeds", "feature_navigation.json")
d = json.load(open(p))

def attr(v, k): return {"type": "Attr", "node": {"type": "Var", "name": v}, "key": k}
def P0(v, k):   return {"type": "Plus", "items": [attr(v, k), {"type": "Lit", "value": 0}]}

population = {"type": "Count", "source": {"type": "Filter",
    "source": {"type": "NodesOfType", "node_type": "Feature"}, "var_name": "F2",
    "predicate": {"type": "Eq", "a": attr("F2", "value"), "b": attr("F", "value")}}}
motion = {"type": "IfThenElse", "cond": {"type": "Eq", "a": attr("F", "kind"), "b": {"type": "Lit", "value": "mover"}},
          "then": {"type": "Lit", "value": 10.0}, "other": {"type": "Lit", "value": 0.0}}
salience_term = {"type": "Plus", "items": [motion, {"type": "Times", "items": [{"type": "Lit", "value": -1.0}, population]}]}
mark = {
    "name": "mark_feature_salience",
    "match": [["game", "has_feature", "F"]],
    "where": {"type": "Not", "arg": {"type": "Eq", "a": P0("F", "sal_stamp"), "b": P0("game", "frame")}},
    "effects": [
        ["set_attr", "F", "salience", {"__term__": salience_term}],
        ["set_attr", "F", "sal_stamp", {"__term__": P0("game", "frame")}],
    ],
}
d["rules"] = [r for r in d["rules"] if r["name"] != "mark_feature_salience"]
d["rules"].insert(0, mark)
print("set mark_feature_salience (motion + rarity)")

def has_rd(x): return "reach_dist" in json.dumps(x)
swapped = 0
def walk(node):
    global swapped
    if isinstance(node, dict):
        if node.get("type") == "Lt" and has_rd(node.get("a")) and has_rd(node.get("b")):
            node["type"] = "Gt"; node["a"] = P0("F2", "salience"); node["b"] = P0("F", "salience"); swapped += 1
            return
        for v in node.values(): walk(v)
    elif isinstance(node, list):
        for v in node: walk(v)
for r in d["rules"]:
    if r["name"] == "select_nav_target":
        walk(r["where"])
print("select_nav_target reach_dist->salience swaps this run:", swapped, "(0 = already salience-ordered)")
json.dump(d, open(p, "w"), indent=1)
