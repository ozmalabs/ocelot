"""GROUND the describe vocabulary AS GRAPH DATA — so nothing about *what to say* lives in Python.

The jabberwock reads each gaming concept's OWN NAME through its POS faculty and records the head noun + the
predicate verb as ATTRS on the concept (graph data the rules read), replacing the host-authored say_event table.
It also stamps a clean `label` on each shape prototype, and seeds a LexEntry per surface (concept nouns/verbs,
shape labels, palette colours) so the production faculty can realize them. Authoring step (emits graph data),
run once; re-run to refresh. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_grounds_describe_words.py
"""
from __future__ import annotations
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import construction_grammar as cg
from worlds.arc import _ARC_COLOUR

_MODALS = {"can", "cannot", "cant", "could", "will", "would", "may", "might",
           "must", "shall", "should", "do", "does", "did"}


def _noun_verb(a, concept_name):
    """Head noun + predicate verb of a concept name, via the agent's own POS faculty (parse_with_gaps).
    The verb is already inflected in the name ('a thing that MOVES itself'); modals are skipped."""
    els = cg.parse_with_gaps(concept_name.replace("_", " "), substrate=a.s).get("elements", [])
    noun = next((e["surface"] for e in els if e.get("role") == "content" and e.get("pos") == "noun"), None)
    verb = next((e["surface"] for e in els if e.get("role") == "content" and e.get("pos") == "verb"
                 and e["surface"].lower() not in _MODALS), None)
    return noun, verb


def _clean_shape(name):
    return (name or "").replace("_shape", "").replace("_", " ").strip()


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    surfaces = set()

    # 1) gaming concept words: the concept loader whitelists Concept attrs (name/definition/domain), so the
    # noun/verb can't live on the Concept node. Emit a GamingWord LIBRARY (plain nodes keep their attrs), keyed
    # by name, joined to the concept in the assembly rules. Also drop the dead say_event table from gaming.json.
    gp = os.path.join(ROOT, "seeds", "gaming.json")
    gaming = json.load(open(gp))
    print("grounding gaming concept words (noun/verb from the concept's own name):")
    gw_nodes = [{"local_id": 1, "type": "GamingLexicon", "attrs": {"name": "gaming_words"}}]
    gw_edges = []
    for i, c in enumerate(gaming["concepts"]):
        c.pop("say_event", None); c.pop("noun", None); c.pop("verb", None)   # keep concepts clean
        noun, verb = _noun_verb(a, c["name"])
        attrs = {"name": c["name"], "noun": noun or "thing"}
        if verb:
            attrs["verb"] = verb
        wid = 10 + i
        gw_nodes.append({"local_id": wid, "type": "GamingWord", "attrs": attrs})
        gw_edges.append({"src": {"local": 1}, "type": "has_word", "tgt": {"local": wid}, "attrs": {}})
        surfaces.add(attrs["noun"]); surfaces.update([verb] if verb else [])
        print(f"  {c['name']:28} noun={attrs['noun']!r:10} verb={verb!r}")
    json.dump(gaming, open(gp, "w"), indent=2)
    json.dump({"id": "gaming_words", "version": "1.0.0", "depends_on": ["gaming"],
               "description": "The spoken words for each gaming concept (head noun + predicate verb, read by the "
                              "agent from the concept's own name). A GamingLexicon holds them via has_word; the "
                              "describe_utterance rules join by name. Words live here because Concept nodes "
                              "whitelist their attrs.",
               "nodes": gw_nodes, "edges": gw_edges, "productions": [], "concepts": [], "rules": []},
              open(os.path.join(ROOT, "seeds", "gaming_words.json"), "w"), indent=2)
    print(f"  -> gaming_words.json: {len(gw_nodes)-1} GamingWord nodes")

    # 2) shape prototypes: a clean `label` (the spoken word for the shape).
    sp = os.path.join(ROOT, "seeds", "shape_library.json")
    lib = json.load(open(sp))
    for n in lib["nodes"]:
        if n.get("type") == "ShapePrototype":
            n["attrs"]["label"] = _clean_shape(n["attrs"]["name"])
            surfaces.add(n["attrs"]["label"])
    json.dump(lib, open(sp, "w"), indent=2)
    print(f"stamped labels on {sum(1 for n in lib['nodes'] if n.get('type')=='ShapePrototype')} shape prototypes")

    # 3) palette colours are spoken words too.
    surfaces.update(_ARC_COLOUR.values())

    # 4) seed a LexEntry per surface so the production faculty can realize them (graph data, not a Python dict).
    surfaces = sorted(w for w in surfaces if w)
    nodes = [{"local_id": i + 1, "type": "LexEntry",
              "attrs": {"surface": w, "concept": w, "language": "en", "status": "confirmed"}}
             for i, w in enumerate(surfaces)]
    seed = {"id": "describe_lexicon", "version": "1.0.0", "depends_on": [],
            "description": "Grounded LexEntry surfaces for the self-report vocabulary — concept nouns/verbs "
                           "(from the concepts' own names), geometric-shape labels, and palette colours. The "
                           "agent's voice for describing what it perceives; graph data, not a host dict.",
            "nodes": nodes, "edges": [], "productions": [], "concepts": [], "rules": []}
    json.dump(seed, open(os.path.join(ROOT, "seeds", "describe_lexicon.json"), "w"), indent=2)
    print(f"seeded describe_lexicon.json: {len(nodes)} LexEntries -> {surfaces}")
    print(f"donkey: {donkey['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
