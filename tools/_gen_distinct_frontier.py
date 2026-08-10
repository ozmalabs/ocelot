"""Seed authoring tool: rewrite ground_hint_to_investigation to DEDUP by the advice's cue and
mint DISTINCT frontiers (keys from the AdviceCue node), fixing the proliferation. Deletable."""
import json, os
P = os.path.join(os.path.dirname(__file__), "..", "seeds", "investigation_teacher.json")
d = json.load(open(P))
A = lambda n, k: {"type": "Attr", "node": {"type": "Var", "name": n}, "key": k}
N = lambda n, e: {"type": "Neighbours", "node": {"type": "Var", "name": n}, "edge_type": e, "any_type": False}
rule = {
  "name": "ground_hint_to_investigation",
  "comment": "DISTINCT-FRONTIER grounding (proliferation fix): the teacher's advice is turned by "
             "the drain's thin classifier into an AdviceCue node (its distinguishing token + "
             "DISTINCT capability_keys). This Rule mints ONE from_teacher frontier per cue and "
             "DEDUPS — `grounds` count 0 means this cue has not grounded a frontier yet — so the "
             "same advice no longer proliferates identical copies; different advice -> different "
             "frontiers. The agent TESTS the cue-specific frontier (high shortfall -> picked next).",
  "match": [["imp", "about_axis", "ax"], ["imp", "names_cue", "cue"], ["ax", "investigated_by", "op"]],
  "where": {"type": "And", "items": [
    {"type": "Eq", "a": A("imp", "advice_ready"), "b": {"type": "Lit", "value": 1}},
    {"type": "Not", "arg": {"type": "Eq", "a": A("imp", "grounded"), "b": {"type": "Lit", "value": 1}}},
    {"type": "Eq", "a": {"type": "Count", "source": N("cue", "grounds")}, "b": {"type": "Lit", "value": 0}}
  ]},
  "effects": [
    ["add_node", "nax", "CapabilityAxis", {
      "is_axis": 1.0, "saturation": 0.0, "shortfall": 0.6, "min_order": 1.0,
      "investigated_count": 0, "mf_stall": 0, "from_teacher": 1.0,
      "capability_keys": {"__term__": A("cue", "capability_keys")},
      "cue": {"__term__": A("cue", "token")}}],
    ["add_edge", "nax", "investigated_by", "op"],
    ["add_edge", "cue", "grounds", "nax"],
    ["set_attr", "imp", "grounded", {"__term__": {"type": "Lit", "value": 1}}]
  ]
}
d["rules"] = [r for r in d["rules"] if r["name"] != "ground_hint_to_investigation"] + [rule]
for e, src, tgt in (("names_cue", "Impasse", "AdviceCue"), ("grounds", "AdviceCue", "CapabilityAxis")):
    d["productions"].append({"provenance": f"seed:investigation_teacher:{e}",
                             "src": {"type": src, "var": "a"}, "edge_type": e,
                             "tgt": {"type": tgt, "var": "b"}})
json.dump(d, open(P, "w"), indent=2)
print("ok: ground_hint dedup-by-cue; rules", len(d["rules"]), "productions", len(d["productions"]))
