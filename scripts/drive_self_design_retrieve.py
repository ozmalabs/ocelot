"""DRIVE THE REAL AGENT — #4: compose from its OWN held machinery, and ground what's missing from wiki (no LLM).

(A) RETRIEVAL OVER THE REAL 30 HELD RULES: introspect each held Rule's stored effect/match clauses to derive
    what it PRODUCES (node-types via add_node, edge-types via add_edge, attrs via set_attr) and CONSUMES (the
    edge-types it matches), minting Rule--produces-->Kind / Rule--consumes-->Kind into the graph. The composer
    can then retrieve "which of MY real rules produces X?" over its actual machinery — not hand-declared toys.
(B) WIKI-GROUND THE MISSING PIECE: for a kind NO held rule produces and the agent does not already hold, it
    grounds the concept from the on-disk wikipedia (the non-LLM knowledge source) — filling the gap instead of
    stalling or calling an LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_self_design_retrieve.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.wiki_library import WikipediaLibrary

def _clauses(v):
    return list(v) if isinstance(v,(list,tuple)) else []

def characterize(agent):
    """Introspect every held Rule -> mint produces/consumes edges to Kind nodes. Mechanical reading of the
    agent's OWN rule structure (like a reflective faculty reading microtheories)."""
    kinds={}
    def kind(name):
        if name not in kinds:
            kinds[name]=agent.s.add_node("Kind",{"name":str(name)})
        return kinds[name]
    nrules=0
    for r in agent.s.nodes("Rule"):
        at=agent.s.node(r)["attrs"]; nrules+=1
        for cl in _clauses(at.get("effect")):
            if not isinstance(cl,(list,tuple)) or not cl: continue
            op=cl[0]
            if op=="add_node" and len(cl)>=3: agent.inner.add_edge_unchecked(r,"produces",kind(cl[2]))
            elif op=="add_edge" and len(cl)>=3: agent.inner.add_edge_unchecked(r,"produces",kind(cl[2]))
            elif op=="set_attr" and len(cl)>=3: agent.inner.add_edge_unchecked(r,"produces",kind(cl[2]))
        for cl in _clauses(at.get("match")):
            if isinstance(cl,(list,tuple)) and len(cl)>=2: agent.inner.add_edge_unchecked(r,"consumes",kind(cl[1]))
    return nrules, kinds

def producers_of(agent, kind_name):
    return sorted(agent.s.node(r)["attrs"].get("id") or str(r)
                  for k in agent.s.nodes("Kind") if agent.s.node(k)["attrs"].get("name")==kind_name
                  for r in agent.inner.in_neighbours(k,"produces"))

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])
    nrules,kinds=characterize(a)
    print(f"  characterized {nrules} REAL held rules -> {len(kinds)} produced/consumed kinds")

    # (A) RETRIEVE over the agent's ACTUAL rules: which of MY rules produces each needed kind?
    for need in ("Intent","expects_response","Unknown"):
        prod=producers_of(a,need)
        print(f"  retrieve: my held rules that PRODUCE {need!r}: {prod}")
    retrieval_ok = ("rule_intent_from_claim" in producers_of(a,"Intent")
                    and len(producers_of(a,"expects_response"))>=1)

    # (B) WIKI-GROUND a missing piece: a kind NO held rule produces and the agent does not hold
    missing="Tetromino"
    have_producer = bool(producers_of(a,missing))
    have_concept = any(a.s.node(c)["attrs"].get("name")==missing for c in a.s.nodes("Concept"))
    print(f"  gap kind {missing!r}: any held rule produces it? {have_producer}  already a held concept? {have_concept}")
    lib=WikipediaLibrary(); art=lib.article(missing) or lib.article("Tetromino") or lib.article("Tetris")
    grounded=None
    if art is not None:
        gloss=(getattr(art,"summary",None) or (art.section_text(0) if hasattr(art,"section_text") else ""))[:200]
        c=a.s.add_node("Concept",{"name":missing,"gloss":gloss,"source":"wikipedia"})
        a.inner.add_edge_unchecked(a.agent,"knows_concept",c); grounded=gloss
    print(f"  wiki-grounded the missing piece from disk: {missing!r} -> {str(grounded)[:90]!r}")
    ground_ok = (not have_producer) and (grounded is not None)

    ok = retrieval_ok and ground_ok and calls["n"]==0
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — #4: the agent RETRIEVED over its OWN 30 held rules (introspected "
          f"produces/consumes -> 'which of my rules makes Intent/expects_response') and, for a piece none of "
          f"them makes (Tetromino), GROUNDED it from the on-disk wikipedia — composing from its real machinery "
          f"and filling the gap from a non-LLM source. calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
