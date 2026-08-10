"""THE JABBERWOCK BUILDS ITS COMMUNICATE FACULTY ITSELF, then USES it: told to describe what it sees, it
mints a produce-utterance subgoal per recognised thing and speaks each through its language system.

I only frame the concern. The agent's EXTENDED self-build composer (ground_concern -> _compose_communicate_
rule) authors the communicate RULE from the grounded relations and installs it live. Then giving the agent
the describe-instruction (a describe-Goal over the scene) makes its OWN rule mint the subgoals; the language-
production faculty satisfies each. Graph-native; donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_self_built_communication.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern, ground_concern
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank

def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def Attr(node, key): return {"type": "Attr", "node": node, "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Neighbours(node, et): return {"type": "Neighbours", "node": node, "edge_type": et}
def SIO(h, n): return {"type": "StringIndexOf", "haystack": h, "needle": n}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Holds(name, node): return {"type": "Holds", "concept": name, "node": node}

GAMING = ["the_thing_i_control", "a_thing_that_moves_itself", "a_thing_that_stays_put",
          "a_counter", "a_barrier_i_cannot_pass", "a_way_i_can_pass"]
DESC_LEXICON = {"move": "moves", "block": "blocks", "respond": "responds",
                "count": "counts", "stay": "stays", "open": "opens", "thing": "thing"}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    say_map = {c["name"]: c.get("say_event")
               for c in json.load(open(os.path.join(ROOT, "seeds", "gaming.json")))["concepts"]}

    print("=" * 94)
    print("THE JABBERWOCK BUILDS ITS COMMUNICATE FACULTY (self-build composer), THEN USES IT")
    print("=" * 94)

    # recognition rules (graph-native, by context)
    for name in GAMING:
        I.add_rule({"name": f"recognise_{name}",
                    "match": [["scene", "has_percept", "p"], ["gmt", "has_concept", "con"]],
                    "where": And(Eq(Attr(V("con"), "name"), L(name)), Holds(name, V("p"))),
                    "effects": [["add_edge", "p", "is_a", "con"]]})

    # ---- THE AGENT BUILDS THE COMMUNICATE RULE (I only frame the concern) ----
    obs = [["told", "DESCRIBE", "what", "SEEN"], ["for_each", "PERCEPT", "mint", "SUBGOAL"],
           ["SUBGOAL", "produces", "UTTERANCE"], ["source", "UTTERANCE", "from", "PERCEPT"]]
    ind = induce_concern(a, obs, name_hint="communicate_what_i_see")
    key = ind.get("capability_key")
    learn = learn_term_for_concern(a, [key]) if key else {}
    g_res = ground_concern(a, [key]) if key else {}
    print(f"\n  [induce] residual_predicates={ind.get('residual_predicates')}")
    print(f"  [ground] grounded={g_res.get('grounded')} path={g_res.get('path')} form={g_res.get('form')}")
    print(f"           grounded_relations={[r[0] for r in (g_res.get('grounded_relations') or [])]}")
    if g_res.get("rule"):
        print(f"           AUTHORED RULE: match={g_res['rule']['match']}")
        print(f"                          effects={g_res['rule']['effects']}")

    # ---- USE IT: give the literal describe-instruction (a describe-Goal over a scene) ----
    print("\n  INSTRUCTION (a describe-Goal over the scene = 'describe what you see')")
    scene = s.add_node("Scene", {})
    g = s.add_node("Goal", {"kind": "describe_scene"}); I.add_edge_unchecked(g, "describes", scene)
    percepts = [("static & impassable", {"kind": "static", "passable": False}),
                ("moves on its own",    {"kind": "mover", "responds_to_my_action": False, "passable": True}),
                ("I control it",        {"kind": "mover", "responds_to_my_action": True, "selective": True, "passable": True})]
    for _d, ctx in percepts:
        pn = s.add_node("Percept", ctx); I.add_edge_unchecked(scene, "has_percept", pn)
    I.run_rules()                          # recognition -> is_a ; THE AGENT'S communicate rule -> subgoals

    subgoals = [n for n in I.neighbours(g, "has_subgoal")]
    print(f"  -> the agent's OWN rule minted {len(subgoals)} produce-utterance subgoals")

    # ---- production faculty satisfies each minted subgoal ----
    world = LanguageWorld(I, training_bank(), teacher_stub); world.run()
    for lemma, surf in DESC_LEXICON.items():
        s.add_node("LexEntry", {"surface": surf, "concept": lemma, "language": "en",
                                "status": "confirmed", "lemma": lemma})
    world.teacher_disabled = True
    prod = LanguageProduction(world)

    print("\n  THE AGENT SAYS (each minted subgoal, through its production pipeline):")
    for sg in subgoals:
        con = next(iter(I.neighbours(sg, "about")), None)
        if con is None:
            continue
        cname = s.node(con)["attrs"].get("name"); say = say_map.get(cname)
        if not say:
            continue
        res = prod.produce("en", {"event": say, "agent": "thing", "tense": "present", "intent": "inform"})
        print(f"    subgoal about '{cname}'  -> {res['overt_speech']!r}  "
              f"[round-trip {res.get('self_monitor', {}).get('match')}]")

    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    print("  The communicate faculty was BUILT BY THE AGENT (ground_concern composed the rule from grounded")
    print("  relations and installed it live). Told to describe what it sees, ITS OWN rule minted a produce-")
    print("  utterance subgoal per recognised thing, and its language system spoke each. I only framed it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
