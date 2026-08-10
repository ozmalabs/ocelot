"""Drive navigation by what a feature DOES (function), not what it IS (identity).

The agent resolves IDENTITY by observation (collapse_curiosity sets `resolved` — "that's a mover") almost
instantly, and the nav treated `resolved` as "done with this feature" — so it recognised things and never went
to them. But knowing what a thing DOES requires INTERACTING with it. Three graph edits in the EXISTING
feature-nav rules:
 1) select_nav_target: target features whose FUNCTION is untested (NOT does_known), salience-ordered.
 2) untarget_nav: release a target when its function is TESTED (does_known), not when its identity is resolved.
 3) test_on_arrival (new): on reaching the targeted feature, SELECT it (test what it does) and mark does_known
    — action_effect then observes the effect. Reaching is the means; learning what-it-does is the goal.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "seeds", "feature_navigation.json")
d = json.load(open(p))

def attr(v, k): return {"type": "Attr", "node": {"type": "Var", "name": v}, "key": k}
def P0(v, k):   return {"type": "Plus", "items": [attr(v, k), {"type": "Lit", "value": 0}]}

# 1+2) in select_nav_target and untarget_nav, the "done with this feature" predicate is `resolved` (identity).
#      Swap those resolved-references to does_known (function tested). Leaves collapse_curiosity etc. untouched.
def swap_resolved_to_does_known(node):
    n = 0
    if isinstance(node, dict):
        if node.get("type") == "Attr" and node.get("key") == "resolved":
            node["key"] = "does_known"; return 1
        for v in node.values(): n += swap_resolved_to_does_known(v)
    elif isinstance(node, list):
        for v in node: n += swap_resolved_to_does_known(v)
    return n
for r in d["rules"]:
    if r["name"] in ("select_nav_target", "untarget_nav"):
        c = swap_resolved_to_does_known(r["where"])
        print(f"{r['name']}: resolved->does_known swaps = {c}")

# 3) test_on_arrival: reached the target (visited) but function not yet tested -> SELECT it + mark does_known.
test_rule = {
    "name": "test_on_arrival",
    "match": [["game", "has_feature", "F"]],
    "where": {"type": "And", "items": [
        {"type": "Eq", "a": P0("F", "is_nav_target"), "b": {"type": "Lit", "value": 1.0}},
        {"type": "Eq", "a": P0("F", "visited"), "b": {"type": "Lit", "value": 1.0}},
        {"type": "Not", "arg": {"type": "Eq", "a": P0("F", "does_known"), "b": {"type": "Lit", "value": 1.0}}},
    ]},
    "effects": [
        ["set_attr", "game", "chosen_action", "Select"],   # interact to find out what it DOES
        ["set_attr", "F", "does_known", 1.0],              # now tested; action_effect observes the effect
    ],
}
d["rules"] = [r for r in d["rules"] if r["name"] != "test_on_arrival"]
d["rules"].append(test_rule)
print("added test_on_arrival")
json.dump(d, open(p, "w"), indent=1)
