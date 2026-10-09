#!/usr/bin/env python3
"""Emit seeds/lexical_qualia.json -- the persisted LEXICAL QUALIA INDEX.

Every held word links to one or more qualia. A quale is a native graph node,
`Quale{name, dimension, lemma, pos, depth, extent}`, and the index is one
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
  lexical:sense   -- a WordNet synset (the word's senses and their hypernyms)
  closed_class    -- a grammatical role held in domain_data/reading_constructions
                     ClosedClass (determiner, preposition, auxiliary, ...): the
                     quale of a function word is its role, not a WordNet sense
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
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a, skip=("lexical_qualia",))
    names = set()
    for c in a.s.nodes("Concept"):
        nm = a.s.node(c)["attrs"].get("name")
        if isinstance(nm, str) and WORD_RE.match(nm):
            names.add(nm)
    return sorted(names)


def closed_class_roles():
    d = json.loads((ROOT / "domain_data/reading_constructions.json").read_text())
    roles = {}
    for n in d.get("nodes", []):
        if n.get("type") != "ClosedClass":
            continue
        role = n.get("attrs", {}).get("role")
        for f in n.get("attrs", {}).get("forms") or []:
            roles.setdefault(str(f).lower(), set()).add(str(role))
    return roles


def build(words):
    from domains.dict_teacher import _wordnet
    wn = _wordnet()
    roles = closed_class_roles()
    qualia = {}            # name -> attrs
    parents = {}           # name -> set(parent names)
    word_q = {}            # word -> [quale names]

    def add_sense(s):
        nm = s.name()
        if nm in qualia:
            return
        qualia[nm] = {"name": nm, "dimension": "lexical:sense", "lemma": s.lemmas()[0].name().lower(),
                      "pos": s.pos(), "depth": int(s.min_depth())}
        ps = set(s.hypernyms()) | set(s.instance_hypernyms())
        parents[nm] = {p.name() for p in ps}
        for p in ps:
            add_sense(p)

    for w in words:
        if w in roles:
            names = []
            for r in sorted(roles[w]):
                q = "closed_class:" + r
                qualia.setdefault(q, {"name": q, "dimension": "closed_class", "lemma": r, "pos": "", "depth": 0})
                parents.setdefault(q, set())
                names.append(q)
            word_q[w] = names
            continue
        syns = sorted(wn.synsets(w), key=lambda s: s.name())
        if syns:
            for s in syns:
                add_sense(s)
            word_q[w] = [s.name() for s in syns]
            continue
        q = "identity:" + w
        qualia[q] = {"name": q, "dimension": "lexical:identity", "lemma": w, "pos": "", "depth": 0}
        parents[q] = set()
        word_q[w] = [q]

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
    return qualia, parents, word_q


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
    qualia, parents, word_q = build(words)
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
    identity_words = sorted(w for w, qs in word_q.items() if qs and qs[0].startswith("identity:"))
    seed = {
        "id": "lexical_qualia", "version": "1.0.0", "depends_on": [],
        "description": __doc__,
        "stats": {"held_words": len(word_q), "qualia": len(names), "dag_edges": len(edges),
                  "word_links": sum(len(v) for v in word_q.values()), "by_dimension": dims,
                  "identity_only_words": len(identity_words)},
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
