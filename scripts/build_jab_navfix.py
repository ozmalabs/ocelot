"""The jabberwock's classified fix for drive-to-and-probe-affordances:
 (1) competitive_inhibition / pattern-separation: SEPARATE reachable STABLE things from fleeing MOVERS — the
     reach-and-probe target excludes movers (a mover is noticed/salient but you can't reach it by chasing; it
     needs tracking, a separate faculty). So select_nav_target gains `NOT kind==mover`.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "seeds", "feature_navigation.json")
d = json.load(open(p))
not_mover = {"type": "Not", "arg": {"type": "Eq",
    "a": {"type": "Attr", "node": {"type": "Var", "name": "F"}, "key": "kind"},   # plain Attr (string, not P0)
    "b": {"type": "Lit", "value": "mover"}}}
for r in d["rules"]:
    if r["name"] == "select_nav_target":
        items = r["where"]["items"]
        if not any(json.dumps(it) == json.dumps(not_mover) for it in items):
            items.append(not_mover)
            print("select_nav_target: added NOT kind==mover (reach STABLE things, not fleeing movers)")
json.dump(d, open(p, "w"), indent=1)
