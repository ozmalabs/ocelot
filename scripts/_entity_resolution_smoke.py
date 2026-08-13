"""Throwaway smoke test for the entity_concept_correspondence seed -- NOT
part of the shipped test suite. Verifies the two Rules fire correctly on a
minimal hand-built graph before wiring domains/reasoning_can_bridge.py."""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import engine_rules_only
from domains import name_variant_merge as nvm
from worlds.bigville_can_beliefs import install_productions, build_resident_can_mt

a = WorldAdapter(seeds=())
install_productions(a.s)
d = json.load(open(os.path.join(_ROOT, "seeds", "entity_concept_correspondence.json")))
a.inner.load_seed_manifest(engine_rules_only(d))


def resident(name, index=0):
    return {"name": name, "index": index, "params": {
        "resolution_bins": 7, "arousal": 0.2, "mood_bias": 0.30,
        "w_supergraph": 0.50, "prior_world_safe": 0.5,
        "prior_self_worth": 0.5, "charm_weight": 0.5, "hostile_weight": 0.2,
        "prior_others_trust": 0.5, "claim_weight": 0.5, "w_spite": 0.1,
    }}


def mk_entity(name):
    nid = a.s.add_node("SmEntity", {"name": name})
    a.inner.add_edge_unchecked(nid, "is_entity", nid)
    return nid


def tokens(nid):
    nm = a.s.node(nid)["attrs"]["name"]
    a.s.set_attr(nid, "name_tokens",
                 frozenset(nvm._name_tokens(str(nm).replace(" ", "_"))))


# --- case 1: exact match -----------------------------------------------
built_avery = build_resident_can_mt(a.s, resident("avery"))
e_avery = mk_entity("avery")
tokens(e_avery)
tokens(built_avery["resident_node"])

# --- case 2: name-token containment (surname only) ----------------------
built_verity = build_resident_can_mt(a.s, resident("Verity Peaseblossom", index=1))
e_surname = mk_entity("peaseblossom")
tokens(e_surname)
tokens(built_verity["resident_node"])

steps = a.inner.run_rules(2000)
print("run_rules steps (cases 1+2 only):", steps)


def denoted_mt(e):
    outs = list(a.inner.neighbours(e, "denotes"))
    return [a.s.node(x)["attrs"].get("name") for x in outs]


print("avery denotes:", denoted_mt(e_avery), "expect avery_beliefs")
print("peaseblossom(surname) denotes:", denoted_mt(e_surname),
      "expect Verity Peaseblossom_beliefs")

# --- case 3: a SECOND Peaseblossom resident now exists -- a FRESH entity
# named by that shared surname must be refused (ambiguity guard), and the
# EARLIER e_surname resolution (already minted, case 2) must NOT be undone.
built_p2 = build_resident_can_mt(a.s, resident("Radella Peaseblossom", index=2))
tokens(built_p2["resident_node"])
e_amb = mk_entity("peaseblossom2")
a.s.set_attr(e_amb, "name", "peaseblossom")
tokens(e_amb)
a.inner.run_rules(2000)
print("ambiguous peaseblossom (fresh entity) denotes:", denoted_mt(e_amb),
      "expect [] (refused)")
print("earlier peaseblossom(surname) still denotes:", denoted_mt(e_surname),
      "expect unchanged, Verity Peaseblossom_beliefs")
