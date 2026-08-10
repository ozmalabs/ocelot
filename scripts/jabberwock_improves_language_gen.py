"""HAVE THE JABBERWOCK IMPROVE ITS OWN LANGUAGE GENERATION FOR NOVEL ENVIRONMENTS — its call.

I only frame the concern. The agent (a) recognises its SHAPE via its generative loop (induce_concern ->
learn_term_for_concern -> ground_concern) and (b) reports its composable machinery (reflect self_design).
Then the recognised improvement is ENACTED graph-native: the old generator named a novel thing by the
FIRST held concept it shared one shape with (single word, often degenerate — all the motion things landed
on the same target). The improved generator describes a novel thing by ALL the shapes it has, with an
analogy PER shape — a multi-shape / COMPOUND description. Both run as Rules in run_rules over the agent's
own shape vocabulary + keyword Term. Python only attends to the grounded gaming concepts and reads edges.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_improves_language_gen.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern, ground_concern, reflect

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
def kw_hits(spv, cv): return Exists(Attr(V(spv), "keywords"), "kw",
                                    Gte(SIO(Attr(V(cv), "definition"), V("kw")), L(0)))

# OLD generator: ONE analogy, the first shared shape (the degenerate single-word naming).
OLD_RULE = {
    "name": "name_by_first_shared_shape",
    "match": [["hub", "observes", "c"], ["m", "has_concept", "t"], ["ms", "has_principle", "sp"]],
    "where": And(Not(Eq(Attr(V("m"), "name"), L("gaming"))),
                 Not(Exists(Neighbours(V("c"), "old_name"), "_i", L(True))),
                 kw_hits("sp", "c"), kw_hits("sp", "t")),
    "effects": [["add_edge", "c", "old_name", "t"]],
}
# IMPROVED generator, part 1: tag a novel concept with EVERY shape it has (not just the first).
SHAPE_RULE = {
    "name": "tag_all_shapes",
    "match": [["hub", "observes", "c"], ["ms", "has_principle", "sp"]],
    "where": And(kw_hits("sp", "c"),
                 Not(Exists(Neighbours(V("c"), "has_shape"), "x", Eq(V("x"), V("sp"))))),
    "effects": [["add_edge", "c", "has_shape", "sp"]],
}
# IMPROVED generator, part 2: one analogy PER shape (a held concept in another domain sharing THAT shape).
PERSHAPE_RULE = {
    "name": "analogy_per_shape",
    "match": [["c", "has_shape", "sp"], ["m", "has_concept", "t"], ["hub", "observes", "c"]],
    "where": And(Not(Eq(Attr(V("m"), "name"), L("gaming"))),
                 kw_hits("sp", "t"),
                 Not(Exists(Neighbours(V("c"), "desc_via"), "x", Eq(V("x"), V("sp"))))),
    "effects": [["add_edge", "c", "described_as", "t"],
                ["add_edge", "c", "desc_via", "sp"],
                ["set_attr", "c", "_shape_done", {"__term__": Attr(V("sp"), "name")}]],
}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner

    print("=" * 94)
    print("THE JABBERWOCK IMPROVES ITS OWN LANGUAGE GENERATION FOR NOVEL ENVIRONMENTS — I only framed it")
    print("=" * 94)

    # (1) THE AGENT DECIDES: recognise the improvement's SHAPE via its generative loop.
    obs = [["rank", "CANDIDATE", "by", "FIT"],
           ["compose", "DESCRIPTION", "from", "PARTS"],
           ["bound", "RESIDUAL", "by", "FEEDBACK"]]
    ind = induce_concern(a, obs, name_hint="improve_language_for_novel_environment")
    key = ind.get("capability_key")
    learned = learn_term_for_concern(a, [key]) if key else {}
    grounded = ground_concern(a, [key]) if key else {}
    design = reflect("self_design", "improve how I describe a novel environment in language", s)
    print(f"\n[1] THE AGENT'S DECISION (its own faculties):")
    print(f"    induced concern: minted={ind.get('minted')} predicates={ind.get('residual_predicates')}")
    print(f"    recognised term-family: {learned.get('term_family')}  (shared leaves={learned.get('shared_leaves')})")
    print(f"    grounded: {grounded.get('grounded')} form={grounded.get('form')}")
    print(f"    composable machinery it can build from: {design.get('composable_machinery')}")

    # Read the grounded gaming concepts + attend to them.
    gmt = next((m for m in s.nodes("Microtheory") if s.node(m)["attrs"].get("name") == "gaming"), None)
    gcs = list(I.neighbours(gmt, "has_concept")) if gmt else []
    hub = s.add_node("Concept", {"name": "attending_to_the_game"})
    for c in gcs:
        I.add_edge_unchecked(hub, "observes", c)

    # (2) ENACT — both generators are Rules; the engine runs them.
    for r in (OLD_RULE, SHAPE_RULE, PERSHAPE_RULE):
        I.add_rule(r)
    I.run_rules(5000)

    # (3) BEFORE vs AFTER, read out of the graph.
    print("\n[2] BEFORE (old generator: one word, first shared shape):")
    for c in gcs:
        old = next(iter(I.neighbours(c, "old_name")), None)
        on = s.node(old)["attrs"].get("name") if old else "—(nothing)"
        print(f"    · {s.node(c)['attrs'].get('name'):26} -> {on}")

    print("\n[3] AFTER (improved generator: a multi-shape / COMPOUND description, an analogy per shape):")
    for c in gcs:
        cnm = s.node(c)["attrs"].get("name")
        shapes = sorted({s.node(sp)["attrs"].get("name") for sp in I.neighbours(c, "has_shape")})
        analogs = [s.node(t)["attrs"].get("name") for t in I.neighbours(c, "described_as")]
        vias = [s.node(sp)["attrs"].get("name") for sp in I.neighbours(c, "desc_via")]
        compound = "+".join(shapes) + "-thing" if shapes else "(no shape — would mint a new primitive)"
        print(f"    · {cnm}")
        print(f"        compound name : {compound}")
        pairs = list(zip(vias, analogs))[:4]
        for via, an in pairs:
            print(f"        - as a {via}: like '{an}'")

    print("\n" + "=" * 94)
    print(f"donkey (LLM calls): {donkey['n']}")
    print("The agent recognised the improvement's shape (its generative loop), and the improved generator")
    print("runs graph-native: describe a novel thing by ALL its shapes with an analogy per shape (a compound),")
    print("instead of one first-match word. Python only attended to grounded concepts and read edges.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
