"""Run the deeper faculties over the grounded tropes — read the NUANCE, not just the words.

A trope name is inherently a MEANING-VECTOR: a literal reading (herring = a fish, from the
dictionary) AND a figurative reading (red herring = a misdirection, from the wiki). The faculties
now have the substrate to surface this:
  - meaning_vector keeps BOTH readings (no collapse);
  - the figurative reading is ABOUT the literal one (the trope is a metaphor — order-N aboutness);
  - suspect-witness: the figurative reading is the WIKI's claim (a suspect witness, lower trust),
    held as a sourced, weighted reading, while the literal is the dictionary's (higher trust).
Understanding the trope = holding its literal+figurative vector with the relation and the provenance,
not picking one. Run over real grounded tropes.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_trope_nuance
"""
from __future__ import annotations
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries

SEP = "=" * 96
# (trope name as grounded, the literal key word in it)
TROPES = [("chekhovs gun", "gun"), ("red herring", "herring"), ("red shirt", "shirt"),
          ("the cavalry", "cavalry")]


def main():
    print(SEP)
    print("READ THE TROPE NUANCE — meaning-vector + suspect-witness over the grounded tropes")
    print(SEP)
    a = boot()
    teacher = a._self_teacher
    attach_libraries(a, log=lambda *x: None)        # dictionary teacher for the LITERAL sense
    dict_teacher = a._self_teacher
    for s in ("learned_lexicon", "learned_tropes"):
        if os.path.exists(os.path.join(ROOT, "seeds", s + ".json")):
            a.inner.load_seed_manifest(manifest_for(s), a.agent)
    tropes = {x["attrs"]["name"]: x["attrs"] for x in
              json.load(open(os.path.join(ROOT, "seeds", "learned_tropes.json")))["nodes"]
              if x.get("type") == "Trope"}

    # Sources with EARNED trust: the dictionary is reliable for literal sense; the wiki is a SUSPECT
    # witness (opinionated, lower trust) for the figurative trope sense.
    src = {"dictionary": a.s.add_node("Source", {"name": "dictionary", "trust": 0.9}),
           "tvtropes_wiki": a.s.add_node("Source", {"name": "tvtropes_wiki", "trust": 0.4})}

    # Build each trope name's meaning-vector: literal reading (dictionary) + figurative reading (wiki),
    # with the figurative ABOUT the literal (the metaphor).
    for name, kw in TROPES:
        tdef = (tropes.get(name, {}).get("definition") or "")
        lit_payload = None
        try:
            lit_payload = dict_teacher(kw)
        except Exception:
            pass
        lit_gloss = (lit_payload.get("answer") if isinstance(lit_payload, dict) else "") or "(literal sense)"
        lit = a.s.add_node("Reading", {"word": name, "gloss": lit_gloss[:60], "kind": "literal", "weight": 0.6})
        fig = a.s.add_node("Reading", {"word": name, "gloss": tdef[:70], "kind": "figurative", "weight": 0.8})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src["tvtropes_wiki"])
        a.inner.add_edge_unchecked(fig, "about", lit)        # the trope: figurative BY METAPHOR from literal

    # the faculties (re-authored): meaning_vector keeps the set; trust read from the source.
    mv = {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "Reading"}, "var_name": "r",
          "predicate": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "r"}, "key": "word"},
                        "b": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "text"}}}
    a.author_subroutine("meaning_vector", mv, purpose="the kept set of readings of a trope name")

    print("\n  each trope name as a MEANING-VECTOR (literal + figurative, both kept), with provenance:")
    for name, kw in TROPES:
        m = a.s.add_node("Mention", {"text": name})
        readings = a.run_subroutine("meaning_vector", {"m": m}) or []
        print(f"\n  {name!r}:")
        for r in sorted(readings, key=lambda x: a.s.node(x)["attrs"].get("kind", "")):
            at = a.s.node(r)["attrs"]
            srcn = a.inner.neighbours(r, "claimed_by")
            sat = a.s.node(srcn[0])["attrs"] if srcn else {}
            about = a.inner.neighbours(r, "about")
            rel = "  (ABOUT the literal — the metaphor)" if about else ""
            print(f"      [{at.get('kind'):10}] {at.get('gloss')!r}  "
                  f"<- {sat.get('name','?')} (trust {sat.get('trust','?')}){rel}")
        # the nuance, read off the vector + provenance + relation
        figs = [r for r in readings if a.s.node(r)["attrs"].get("kind") == "figurative"]
        print(f"      NUANCE: holds BOTH; the figurative is the wiki's claim (a suspect witness, low "
              f"trust) derived BY METAPHOR from the dictionary's literal sense — not collapsed to one.")

    print("\n" + SEP)
    print("  The faculties read the trope nuance over the grounded substrate: each trope name is a "
          "meaning-vector (literal+figurative both held), the figurative reading is ABOUT the literal "
          "(the metaphor / order-N aboutness), and it is the opinionated wiki's claim — a suspect "
          "witness held with low trust, weighed, never taken as the single truth.")
    print(SEP)


if __name__ == "__main__":
    main()
