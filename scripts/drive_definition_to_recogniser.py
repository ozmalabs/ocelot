"""DRIVE THE REAL AGENT — first chip at NL->fireable-rule: a DEFINITION-CONSTRUCTION -> RECOGNISER-SCHEMA.

For a definition of the shape "[a] X is ... composed of N P" (a genus-differentia-by-composition), the agent
parses (concept=X, count=N via its number words, part=P) and SYNTHESISES a structured recogniser rule:
    match a node with has_<P> edges; where Count(has_<P>) == N; effect set is_<X> = 1
then COMPILES it through its real rule compiler (a.inner.add_rule) and the recogniser FIRES — recognising things
that fit the definition and rejecting those that don't. Bounded to this one definition shape (the honest first
chip), but it GENERALISES across any concept of that shape (run on tetromino N=4 AND hexomino N=6). No LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_definition_to_recogniser.py
"""
from __future__ import annotations
import os, sys, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

WORDNUM={"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}

def parse_composed_of(gloss):
    """Constrained parse of '[a] X is ... composed of N P' -> (concept, count, part). The honest bounded part."""
    g=gloss.lower()
    m=re.search(r"\b(a|an)\s+([a-z]+)\s+is\b", g)
    concept=m.group(2) if m else None
    m2=re.search(r"composed of\s+([a-z]+)\s+([a-z]+)", g)
    if not (concept and m2): return None
    count=WORDNUM.get(m2.group(1))
    part=m2.group(2)
    part=part[:-1] if part.endswith("s") else part      # squares -> square
    if count is None: return None
    return concept, count, part

def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}
def synthesise_recogniser(concept, count, part):
    """genus-differentia-by-composition -> a structured recogniser rule (the SCHEMA)."""
    pe=f"has_{part}"
    return {"name":f"recog_{concept}",
      "match":[["sh",pe,"p"]],
      "where":{"type":"Eq","a":{"type":"Count","source":{"type":"Neighbours","node":{"type":"Var","name":"sh"},
               "edge_type":pe,"any_type":False}},"b":{"type":"Lit","value":float(count)}},
      "effects":[["set_attr","sh",f"is_{concept}",1.0]]}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    DEFS=["A tetromino is a geometric shape composed of four squares connected orthogonally",
          "A hexomino is a polyomino composed of six squares"]
    results=[]
    for gloss in DEFS:
        parsed=parse_composed_of(gloss)
        print(f"  definition: {gloss!r}")
        print(f"    parsed (concept,count,part) = {parsed}")
        if not parsed: results.append(False); continue
        concept,count,part=parsed
        rule=synthesise_recogniser(concept,count,part)
        print(f"    synthesised recogniser: match has_{part}; where count(has_{part})=={count}; set is_{concept}")
        a.inner.add_rule(rule)                                  # COMPILE via the agent's real rule compiler

        # GATE: a thing that FITS the definition (count parts) is recognised; one that doesn't is rejected
        pos=a.s.add_node("Shape",{});
        for _ in range(count):
            sq=a.s.add_node(part.capitalize(),{}); a.inner.add_edge_unchecked(pos,f"has_{part}",sq)
        neg=a.s.add_node("Shape",{})
        for _ in range(count-1):
            sq=a.s.add_node(part.capitalize(),{}); a.inner.add_edge_unchecked(neg,f"has_{part}",sq)
        a.inner.run_rules(40)
        pos_rec=a.s.node(pos)["attrs"].get(f"is_{concept}")==1.0
        neg_rec=a.s.node(neg)["attrs"].get(f"is_{concept}")==1.0
        ok=pos_rec and not neg_rec
        print(f"    GATE: {count}-{part} shape recognised={pos_rec}  {count-1}-{part} shape recognised={neg_rec}  -> {ok}")
        results.append(ok)

    ok=all(results) and calls["n"]==0
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — definition->recogniser: from a 'X is composed of N P' definition the "
          f"agent SYNTHESISED a fireable recogniser rule, compiled it through its real rule compiler, and it "
          f"recognised things fitting the definition while rejecting those that don't — for BOTH tetromino(4) "
          f"and hexomino(6), so it's a reusable schema, not a one-off. First chip at NL->rule, calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
