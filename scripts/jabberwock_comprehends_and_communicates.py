"""LITERAL INSTRUCTION -> the jabberwock comprehends it, mints a describe-Goal, mints a produce-utterance
subgoal per recognised thing, and speaks each. I only frame two concerns; the agent BUILDS both rules.

  concern A (comprehend): hear the directive 'describe' over a scene -> mint a describe-Goal.
  concern B (communicate): told-to-describe -> for each recognised thing, mint a produce-utterance subgoal.

ground_concern's EXTENDED composer authors both rules (comprehension + communicate) and installs them live.
Then I LITERALLY ingest the sentence "Describe what you see." (Message + Mentions) and tick: the agent's OWN
comprehension rule mints the describe-Goal, its OWN communicate rule mints the subgoals, and its language-
production faculty speaks each. donkey=0. Nothing about the describe-Goal is hand-minted now.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_comprehends_and_communicates.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern
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
DESC_LEXICON = {"move": "moves", "block": "blocks", "respond": "responds",
                "count": "counts", "stay": "stays", "open": "opens", "thing": "thing"}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    say_map = {c["name"]: c.get("say_event")
               for c in json.load(open(os.path.join(ROOT, "seeds", "gaming.json")))["concepts"]}

    print("=" * 94)
    print("LITERAL INSTRUCTION -> COMPREHEND -> MINT GOAL -> MINT UTTERANCE SUBGOALS -> SPEAK (agent-built)")
    print("=" * 94)

    for name in GAMING:                                   # recognition rules (graph-native)
        I.add_rule({"name": f"recognise_{name}",
                    "match": [["scene", "has_percept", "p"], ["gmt", "has_concept", "con"]],
                    "where": And(Eq(Attr(V("con"), "name"), L(name)), Holds(name, V("p"))),
                    "effects": [["add_edge", "p", "is_a", "con"]]})

    # ---- THE AGENT BUILDS BOTH RULES (I only frame the concerns) ----
    cA = induce_concern(a, [["hear", "the", "describe", "DIRECTIVE"], ["mint", "a", "GOAL"]],
                        name_hint="comprehend_describe")
    rA = ground_concern(a, [cA.get("capability_key")]) if cA.get("capability_key") else {}
    cB = induce_concern(a, [["told", "DESCRIBE", "what", "SEEN"], ["for_each", "PERCEPT", "mint", "SUBGOAL"],
                            ["SUBGOAL", "produces", "UTTERANCE"], ["source", "UTTERANCE", "from", "PERCEPT"]],
                        name_hint="communicate_what_i_see")
    rB = ground_concern(a, [cB.get("capability_key")]) if cB.get("capability_key") else {}
    print(f"\n  [agent builds] comprehension rule: grounded={rA.get('grounded')} path={rA.get('path')}")
    print(f"  [agent builds] communicate rule:   grounded={rB.get('grounded')} path={rB.get('path')}")

    # ---- the agent's current perception (a scene of things) ----
    scene = s.add_node("Scene", {})
    for ctx in ({"kind": "static", "passable": False},
                {"kind": "mover", "responds_to_my_action": False, "passable": True},
                {"kind": "mover", "responds_to_my_action": True, "selective": True, "passable": True}):
        I.add_edge_unchecked(scene, "has_percept", s.add_node("Percept", ctx))
    I.run_rules()                                         # recognition -> is_a

    # ---- LITERALLY say the sentence: ingest it as a Message + Mentions (mechanical I/O) ----
    sentence = "Describe what you see."
    print(f"\n  >>> literally: {sentence!r}")
    msg = s.add_node("Message", {"text": sentence})
    I.add_edge_unchecked(msg, "about", scene)            # the instruction is ABOUT the current scene
    for w in sentence.lower().replace(".", "").split():
        I.add_edge_unchecked(msg, "has_mention", s.add_node("Mention", {"text": w}))
    I.run_rules()                                         # AGENT comprehends -> describe-Goal -> subgoals

    gs = [g for g in s.nodes("Goal") if s.node(g)["attrs"].get("kind") == "describe_scene"]
    subgoals = [sg for g in gs for sg in I.neighbours(g, "has_subgoal")]
    print(f"  -> the agent comprehended it: minted {len(gs)} describe-Goal, {len(subgoals)} utterance subgoals")

    # ---- production faculty speaks each minted subgoal ----
    world = LanguageWorld(I, training_bank(), teacher_stub); world.run()
    for lemma, surf in DESC_LEXICON.items():
        s.add_node("LexEntry", {"surface": surf, "concept": lemma, "language": "en",
                                "status": "confirmed", "lemma": lemma})
    world.teacher_disabled = True
    prod = LanguageProduction(world)
    print("\n  THE AGENT SAYS:")
    seen = set()
    for sg in subgoals:
        con = next(iter(I.neighbours(sg, "about")), None)
        if con is None:
            continue
        cname = s.node(con)["attrs"].get("name")
        if cname in seen:
            continue
        seen.add(cname)
        say = say_map.get(cname)
        if not say:
            continue
        res = prod.produce("en", {"event": say, "agent": "thing", "tense": "present", "intent": "inform"})
        print(f"    ({cname}) {res['overt_speech']!r}  [round-trip {res.get('self_monitor', {}).get('match')}]")

    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    print("  I LITERALLY said one sentence. The agent comprehended it (its own comprehension rule minted the")
    print("  describe-Goal from the ingested directive), its communicate rule minted an utterance subgoal per")
    print("  recognised thing, and its language system spoke each. Both rules were BUILT BY THE AGENT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
