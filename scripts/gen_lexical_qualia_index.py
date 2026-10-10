#!/usr/bin/env python3
"""Emit seeds/lexical_qualia.json -- the persisted LEXICAL QUALIA INDEX.

Every held word links to one or more qualia. A quale is a native graph node,
`Quale{name, dimension, extent}`, and the index is one
edge type, `has_quale`:

  Concept(word) -has_quale-> Quale(sense)          every sense of the word
  Quale(sense)  -has_quale-> Quale(broader sense)  the hypernym DAG

so `ReachableFrom(word, "has_quale")` is a word's whole quale closure in one
native Term. Two words match FUZZILY by the qualia they share: "alphabetise"
and "tabulate" meet at "arrange" though they share no letters. The match is
still exact at the chosen grain: identity of Quale nodes, an integer
`extent` (how many held words' closures contain the quale), and an aperture
that says which dimensions are resolved and how general a shared quale may be
before it stops discriminating ("entity" is shared by most nouns).

Dimensions:
  lexical:sense   -- a WordNet synset (the word's senses and their hypernyms),
                     read from the persisted sense table
                     domain_data/wordnet_senses.sqlite (domains/wordnet_table)
  closed_class    -- a grammatical role held in domain_data/reading_constructions
                     ClosedClass (determiner, preposition, auxiliary, ...), or
                     (v1.1.0) for a word with no WordNet sense, the role the
                     held function-word faculty gives it (pronoun, conjunction,
                     ...): the quale of a function word is its role, not a sense
  lexical:definition -- (v1.1.0) a held word with no sense and no role whose
                     held DEFINITION names a genus: Quale{name:"definition:<w>",
                     genus} with has_quale parents = the genus's WordNet noun
                     senses ("kubernetes: Container orchestrator ..." ->
                     orchestrator.n.*). The genus reader is
                     domains/lexical_qualia.definition_genus; the genus is kept
                     on the quale so every pick is auditable.
  lexical:identity-- the word's own identity quale, ONLY for a held word with no
                     sense and no role (proper names, jargon). It is the honest
                     degenerate quale until the word is grounded; the count is
                     reported so the gap is visible.

Held words = the single-token names of every Concept on a full boot.

The seed carries the Quale nodes and the quale->quale DAG as native nodes and
edges. The word->sense links are listed in `word_qualia` ({word: [local ids]})
and installed at boot by substrate.boot_all's mechanical pass via the
Concept.name index (a per-edge cross-seed name ref would be resolved by a
linear scan of every Concept, ~30k times). Deterministic: sorted words,
sorted synsets, stable local ids. Run again to refresh after the lexicon grows.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
OUT = ROOT / "seeds/lexical_qualia.json"
WORD_RE = re.compile(r"^[a-z][a-z'-]*$")


def held_words():
    """{word: definition-or-None} over every single-token Concept name on a
    full boot. The definition is the first string `definition` attr among the
    Concepts of that name, in node-id order (deterministic)."""
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a, skip=("lexical_qualia",))
    names = {}
    for c in a.s.nodes("Concept"):          # node-id (mint) order
        at = a.s.node(c)["attrs"]
        nm = at.get("name")
        if isinstance(nm, str) and WORD_RE.match(nm):
            d = at.get("definition")
            if names.get(nm) is None:
                names[nm] = d if isinstance(d, str) and d.strip() else None
    return dict(sorted(names.items()))


def build(words):
    """The one precedence rule (domains/lexical_qualia.qualia_plan) applied to
    every held word: closed_class role > WordNet senses > function-word role >
    definition genus > identity."""
    from domains import wordnet_table as wt
    from domains import lexical_qualia as lq
    qualia = {}            # name -> attrs
    parents = {}           # name -> set(parent names)
    word_q = {}            # word -> [quale names]
    via = {}               # word -> how its qualia were grounded

    def add_sense(nm):
        if nm in qualia:
            return
        qualia[nm] = {"name": nm, "dimension": "lexical:sense"}
        ps = set(wt.hypernyms(nm))
        parents[nm] = ps
        for p in sorted(ps):
            add_sense(p)

    for w, definition in words.items():
        plan = lq.qualia_plan(w, definition, allow_identity=True)
        via[w] = plan["via"]
        names = []
        for name, dim, extra, sense_parents in plan["qualia"]:
            if dim == "lexical:sense":
                add_sense(name)
            else:
                attrs = {"name": name, "dimension": dim}
                attrs.update(extra)
                qualia.setdefault(name, attrs)
                ps = parents.setdefault(name, set())
                for sp in sense_parents or []:
                    add_sense(sp)
                    ps.add(sp)
            names.append(name)
        word_q[w] = names

    # extent: how many held words' closures contain each quale (exact count)
    closure_cache = {}

    def closure(q):
        if q in closure_cache:
            return closure_cache[q]
        out = {q}
        for p in parents.get(q, ()):
            out |= closure(p)
        closure_cache[q] = out
        return out

    sys.setrecursionlimit(10000)
    extent = {q: 0 for q in qualia}
    for w, qs in word_q.items():
        c = set()
        for q in qs:
            c |= closure(q)
        for q in c:
            extent[q] += 1
    for q in qualia:
        qualia[q]["extent"] = extent[q]
    return qualia, parents, word_q, via


def _dump(seed) -> str:
    """One JSON object per line for the big lists (diffable, ~half the size of
    indent=1); valid JSON, deterministic."""
    c = lambda v: json.dumps(v, ensure_ascii=True, separators=(",", ":"))
    out = ["{"]
    keys = list(seed)
    for i, k in enumerate(keys):
        v = seed[k]
        tail = "," if i < len(keys) - 1 else ""
        if isinstance(v, list) and len(v) > 4:
            out.append(" %s: [" % c(k))
            out += ["  %s%s" % (c(x), "," if j < len(v) - 1 else "") for j, x in enumerate(v)]
            out.append(" ]" + tail)
        elif isinstance(v, dict) and len(v) > 50:
            out.append(" %s: {" % c(k))
            items = list(v.items())
            out += ["  %s:%s%s" % (c(kk), c(vv), "," if j < len(items) - 1 else "") for j, (kk, vv) in enumerate(items)]
            out.append(" }" + tail)
        else:
            out.append(" %s: %s%s" % (c(k), c(v), tail))
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    words = held_words()
    qualia, parents, word_q, via = build(words)
    names = sorted(qualia)
    local = {nm: i + 1 for i, nm in enumerate(names)}
    nodes = [{"local_id": 0, "type": "QualiaIndex",
              "attrs": {"name": "lexical_qualia", "words": len(word_q), "qualia": len(names),
                        "edge_type": "has_quale"}}]
    nodes += [{"local_id": local[nm], "type": "Quale", "attrs": qualia[nm]} for nm in names]
    edges = [{"src": {"local": local[c]}, "type": "has_quale", "tgt": {"local": local[p]}, "attrs": {}}
             for c in names for p in sorted(parents.get(c, ()))]
    dims = {}
    for q in qualia.values():
        dims[q["dimension"]] = dims.get(q["dimension"], 0) + 1
    identity_words = sorted(w for w, v in via.items() if v == "identity")
    by_via = {}
    for v in via.values():
        by_via[v] = by_via.get(v, 0) + 1
    seed = {
        "id": "lexical_qualia", "version": "1.1.0", "depends_on": [],
        "description": __doc__,
        "stats": {"held_words": len(word_q), "qualia": len(names), "dag_edges": len(edges),
                  "word_links": sum(len(v) for v in word_q.values()), "by_dimension": dims,
                  "identity_only_words": len(identity_words), "words_by_grounding": by_via},
        "nodes": nodes, "edges": edges, "rules": [],
        "productions": [
            {"provenance": "seed:lexical_qualia:has_quale_word", "src": {"type": "Concept", "var": "w"},
             "edge_type": "has_quale", "tgt": {"type": "Quale", "var": "q"}},
            {"provenance": "seed:lexical_qualia:has_quale_dag", "src": {"type": "Quale", "var": "q"},
             "edge_type": "has_quale", "tgt": {"type": "Quale", "var": "p"}}],
        "word_qualia": {w: [local[q] for q in word_q[w]] for w in sorted(word_q)},
    }
    OUT.write_text(_dump(seed))
    print("wrote", OUT.relative_to(ROOT), json.dumps(seed["stats"]))


if __name__ == "__main__":
    main()
