"""THE JABBERWOCK DESCRIBES A THING BY CONTEXT, AND SAYS IT THROUGH ITS LANGUAGE-PRODUCTION SYSTEM.

Two graph-native stages, one agent:
  1 RECOGNISE BY CONTEXT (run_rules): one rule per held concept whose `where` fires the agent's own Holds
    term over that concept's predicate (Holds binds the perceived node as `x`). The concept HOLDS of the
    thing iff its behavioural predicate is satisfied by the thing's observed context -> add `is_a` edge.
    Domain-agnostic: missing context makes a predicate False, so it self-guards. No Python recognition loop.
  2 SAY IT THROUGH PRODUCTION: every utterance goes through the agent's full language-production pipeline
    (conceptual_preparation -> grammatical_encoding -> morphophonological -> articulation -> self_monitor),
    NOT a raw print. Each recognised concept carries a `say_event` (graph data: the behavioural verb it
    says itself with); the agent builds a goal frame and PRODUCES the utterance, self-monitoring by parsing
    its own output back. A raw string would be "dumping bytes from its brain"; this is it COMMUNICATING.

Honest cap (the production system's, stated in its own tests): function words aren't grounded, so overt
speech is lemma-level content words ("thing move"), and the round-trip is the real metric.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_describes_through_speech.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank

def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def Attr(node, key): return {"type": "Attr", "node": node, "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Holds(name, node): return {"type": "Holds", "concept": name, "node": node}

GAMING = ["the_thing_i_control", "a_thing_that_moves_itself", "a_thing_that_stays_put",
          "a_counter", "a_barrier_i_cannot_pass", "a_way_i_can_pass"]

# The description vocabulary, grounded as DATA (LexEntry concept<->surface) — no LLM teacher needed for
# the agent's own controlled words. The canonical bank grounds the GRAMMAR + function words; these add the
# domain words the grammar then orders. (status=confirmed so production prefers them.)
DESC_LEXICON = {"move": "moves", "block": "blocks", "respond": "responds",
                "count": "counts", "stay": "stays", "open": "opens", "thing": "thing"}

def ground_desc_lexicon(s):
    for lemma, surf in DESC_LEXICON.items():
        s.add_node("LexEntry", {"surface": surf, "concept": lemma, "language": "en",
                                "status": "confirmed", "lemma": lemma})


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner

    print("=" * 94)
    print("THE JABBERWOCK DESCRIBES BY CONTEXT, AND SAYS IT THROUGH ITS LANGUAGE-PRODUCTION SYSTEM")
    print("=" * 94)

    # ---- STAGE 1: recognise by context (graph-native, run_rules) ----
    for name in GAMING:
        I.add_rule({
            "name": f"recognise_{name}",
            "match": [["scene", "has_percept", "p"], ["gmt", "has_concept", "con"]],
            "where": And(Eq(Attr(V("con"), "name"), L(name)), Holds(name, V("p"))),
            "effects": [["add_edge", "p", "is_a", "con"]],
        })
    scene = s.add_node("Scene", {})
    # three perceived things with different observed context (what the agent's perception would emit):
    percepts = [
        ("a thing that is static and I cannot pass", {"kind": "static", "passable": False}),
        ("a thing that moves on its own",            {"kind": "mover", "responds_to_my_action": False, "passable": True}),
        ("a thing I control",                        {"kind": "mover", "responds_to_my_action": True, "selective": True, "passable": True}),
    ]
    pnodes = []
    for _desc, ctx in percepts:
        p = s.add_node("Percept", ctx); I.add_edge_unchecked(scene, "has_percept", p); pnodes.append(p)
    I.run_rules()
    for (desc, _ctx), p in zip(percepts, pnodes):
        isa = [s.node(c)["attrs"].get("name") for c in I.neighbours(p, "is_a")]
        print(f"  recognised {desc!r} -> is_a {isa}")

    # ---- STAGE 2: SAY each recognition through the production pipeline ----
    print("\n  grounding language: canonical bank -> grammar+function words; + description LEXICON as data...")
    world = LanguageWorld(I, training_bank(), teacher_stub); world.run()
    ground_desc_lexicon(s)                       # add the domain words as LexEntry data (donkey=0)
    world.teacher_disabled = True
    prod = LanguageProduction(world)
    print(f"  grounded: {len(s.nodes('LexEntry'))} LexEntry nodes\n")

    # how each concept says itself (graph data the agent authored in seeds/gaming.json)
    import json as _json
    say_map = {c["name"]: c.get("say_event")
               for c in _json.load(open(os.path.join(ROOT, "seeds", "gaming.json")))["concepts"]}

    for (desc, _ctx), p in zip(percepts, pnodes):
        cons = [s.node(c)["attrs"].get("name") for c in I.neighbours(p, "is_a")]
        print(f"  PERCEIVED: {desc}")
        for cname in cons:
            say = say_map.get(cname)
            if not say:
                print(f"    IS-A '{cname}' (no say_event)")
                continue
            goal = {"event": say, "agent": "thing", "tense": "present", "intent": "inform"}
            try:
                res = prod.produce("en", goal)
                mon = res.get("self_monitor", {})
                print(f"    IS-A '{cname}' -> SAYS (via production pipeline): {res['overt_speech']!r}"
                      f"   [round-trip match={mon.get('match')}]")
            except Exception as e:
                print(f"    IS-A '{cname}' -> produce ERR: {type(e).__name__}: {e}")

    print("\n" + "=" * 94)
    print(f"donkey (LLM calls): {donkey['n']}")
    print("Recognition is graph-native (Holds in run_rules over the agent's own predicates). The description")
    print("is not a raw string — it goes through the agent's full language-production pipeline (and self-")
    print("monitors by parsing its own output back). That is the agent COMMUNICATING, not dumping bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
