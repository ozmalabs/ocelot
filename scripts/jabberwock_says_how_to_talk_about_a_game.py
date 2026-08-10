"""ASK THE JABBERWOCK how it talks about what it's doing in a game — GRAPH-NATIVE, over GROUNDED concepts.

The gaming concepts are now GROUNDED in the agent (seeds/gaming.json: the 'gaming' microtheory — what it
controls, what moves itself, fixed structure, a counter, its own step, the score-signal). The agent HOLDS
them across boots. A SPATIAL principle is grounded in its shape vocabulary (seeds/shape_vocabulary.json:
ShapePrinciple 'spatial_motion' under MetaShape 'spatial_dynamics') so it can talk about the motion things.

The naming is the agent's: ONE Rule, run by the Rust engine in run_rules(), maps each grounded gaming
concept onto a held concept in ANOTHER domain that shares a SHAPE (a principle whose keywords hit BOTH
definitions — the agent's own _kw_hit_term over its own shape vocabulary). Python only: attend to the
grounded gaming concepts (observes edges = perception selection) and read the talks_about edges out.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_says_how_to_talk_about_a_game.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

# ---- Term / rule JSON builders (plain JSON — add_rule()'s parse_rule_json / term_from_json path) -----
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def Attr(node, key): return {"type": "Attr", "node": node, "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*items): return {"type": "And", "items": list(items)}
def Exists(source, var, pred): return {"type": "Exists", "source": source, "var_name": var, "predicate": pred}
def Neighbours(node, et): return {"type": "Neighbours", "node": node, "edge_type": et}
def SIO(hay, needle): return {"type": "StringIndexOf", "haystack": hay, "needle": needle}

def kw_hits(spvar, cvar):
    """the agent's held keyword-match Term: does principle `spvar`'s keywords hit `cvar`'s definition?"""
    return Exists(Attr(V(spvar), "keywords"), "kw",
                  Gte(SIO(Attr(V(cvar), "definition"), V("kw")), L(0)))

# The analogical-naming faculty: ONE rule, run by the Rust engine. c = an attended gaming concept;
# t = a held concept in another (non-gaming) domain; sp = a ShapePrinciple. Link iff sp's shape is in
# BOTH definitions (shared SHAPE, not spelling) and c isn't named yet (fixpoint guard).
TALK_RULE = {
    "name": "talk_about_game_by_shared_shape",
    "match": [["hub", "observes", "c"],
              ["m", "has_concept", "t"],
              ["ms", "has_principle", "sp"]],
    "where": And(
        Not(Eq(Attr(V("m"), "name"), L("gaming"))),               # map to OTHER domains, not gaming->gaming
        Not(Exists(Neighbours(V("c"), "talks_about"), "_ign", L(True))),  # c not yet named (fixpoint guard)
        kw_hits("sp", "c"),                                       # sp's shape is present in c ...
        kw_hits("sp", "t"),                                       # ... AND in t  => SHARED SHAPE
    ),
    "effects": [
        ["add_edge", "c", "talks_about", "t"],
        ["add_edge", "c", "talks_via", "sp"],
        ["add_edge", "c", "talks_in", "m"],
    ],
}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner

    print("=" * 92)
    print("ASKED THE JABBERWOCK (graph-native, over GROUNDED concepts): how do you talk about a game?")
    print("=" * 92)

    # The gaming concepts are GROUNDED — read them out of the held 'gaming' microtheory.
    gmt = next((m for m in s.nodes("Microtheory") if s.node(m)["attrs"].get("name") == "gaming"), None)
    game_concepts = list(I.neighbours(gmt, "has_concept")) if gmt else []
    print(f"  grounded 'gaming' microtheory holds {len(game_concepts)} concepts (has_concept-wired): "
          f"{gmt is not None}")
    spm = any(s.node(n)["attrs"].get("name") == "spatial_motion" for n in s.nodes("ShapePrinciple"))
    print(f"  grounded spatial principle 'spatial_motion' in the shape vocabulary: {spm}")

    # Attend to them (perception selection: hub -observes-> each grounded gaming concept). Mechanical I/O.
    hub = s.add_node("Concept", {"name": "attending_to_the_game"})
    for c in game_concepts:
        I.add_edge_unchecked(hub, "observes", c)

    # Install the naming faculty into the live engine; the agent runs it.
    ridx = I.add_rule(TALK_RULE)
    I.run_rules()

    print("\n  HOW IT TALKS ABOUT EACH GROUNDED GAME CONCEPT (its own analogy, by SHARED SHAPE — donkey=0):\n")
    for c in game_concepts:
        cnm = s.node(c)["attrs"].get("name")
        ts = list(I.neighbours(c, "talks_about"))
        if ts:
            t = ts[0]; tnm = s.node(t)["attrs"].get("name")
            sp = next(iter(I.neighbours(c, "talks_via")), None)
            m = next(iter(I.neighbours(c, "talks_in")), None)
            spnm = s.node(sp)["attrs"].get("name") if sp else "?"
            mnm = s.node(m)["attrs"].get("name") if m else "?"
            print(f"    · '{cnm}'")
            print(f"        -> talks about it AS  '{tnm}'  (from its '{mnm}' domain)")
            print(f"        -> they share the SHAPE  '{spnm}'")
        else:
            print(f"    · '{cnm}'")
            print(f"        -> NO held concept shares its shape -> would COIN A COMPOUND from the residual shape.")

    print("\n" + "=" * 92)
    print(f"donkey (LLM calls): {donkey['n']}")
    print("Grounded: the gaming concepts are held in the agent's 'gaming' microtheory; a spatial principle")
    print("is held in its shape vocabulary. The naming is a Rule in run_rules over the agent's own shape")
    print("vocabulary + keyword Term. Python only attended to the concepts and read the edges out.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
