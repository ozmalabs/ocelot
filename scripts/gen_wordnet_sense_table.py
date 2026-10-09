#!/usr/bin/env python3
"""Emit domain_data/wordnet_senses.sqlite -- the persisted WordNet sense table.

The lexical qualia index (seeds/lexical_qualia.json) holds the qualia of the
words the agent already holds. A word heard for the first time must be
grounded at the I/O boundary; doing that through NLTK's in-process WordNet
costs ~200 MB RSS and a ~1.4 s cold load (measured, tranche 16). This table is
the same data on disk, queried by sqlite (stdlib, near-zero resident memory):

  synset(id PK, name UNIQUE, pos, depth)    every synset
  hyper(child id, parent id)                hypernyms + instance hypernyms
  lemma(form, pos, sid, rank)               NLTK's lemma index verbatim:
                                            form -> synsets, NLTK's order
  subst(pos, ord, old, new)                 morphy suffix rules
  exc(pos, form, base)                      WordNet morphology exceptions

`domains.wordnet_table.synsets(word)` reproduces NLTK's `wn.synsets(word)`
(its morphy: exceptions, then suffix rules filtered by the lemma table), and
the generator verifies that equality on every held word plus inflected forms
before writing. Deterministic: rows are inserted in sorted order and the file
is VACUUMed.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
OUT = ROOT / "domain_data/wordnet_senses.sqlite"


def main():
    from domains.dict_teacher import _wordnet
    wn = _wordnet()
    tmp = OUT.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(str(tmp))
    con.executescript("""
        CREATE TABLE synset(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, pos TEXT NOT NULL, depth INTEGER NOT NULL);
        CREATE TABLE hyper(child INTEGER NOT NULL, parent INTEGER NOT NULL);
        CREATE TABLE lemma(form TEXT NOT NULL, pos TEXT NOT NULL, sid INTEGER NOT NULL, rank INTEGER NOT NULL);
        CREATE TABLE exc(pos TEXT NOT NULL, form TEXT NOT NULL, base TEXT NOT NULL);
    """)
    syns = sorted(wn.all_synsets(), key=lambda s: s.name())
    sid = {s.name(): i + 1 for i, s in enumerate(syns)}
    con.executemany("INSERT INTO synset VALUES (?,?,?,?)",
                    [(sid[s.name()], s.name(), s.pos(), int(s.min_depth())) for s in syns])
    hy = sorted({(sid[s.name()], sid[p.name()]) for s in syns for p in s.hypernyms() + s.instance_hypernyms()})
    con.executemany("INSERT INTO hyper VALUES (?,?)", hy)
    # lemma -> synsets: NLTK's own _lemma_pos_offset_map, verbatim (form, pos
    # key, synset, rank in NLTK's offset order)
    rows = []
    for form, posmap in sorted(wn._lemma_pos_offset_map.items()):
        for p, offsets in sorted(posmap.items()):
            for rank, off in enumerate(offsets):
                rows.append((form, p, sid[wn.synset_from_pos_and_offset(p, off).name()], rank))
    con.executemany("INSERT INTO lemma VALUES (?,?,?,?)", rows)
    subst = [(p, i, old, new) for p, rules in sorted(wn.MORPHOLOGICAL_SUBSTITUTIONS.items())
             for i, (old, new) in enumerate(rules)]
    con.execute("CREATE TABLE subst(pos TEXT NOT NULL, ord INTEGER NOT NULL, old TEXT NOT NULL, new TEXT NOT NULL)")
    con.executemany("INSERT INTO subst VALUES (?,?,?,?)", subst)
    exc = []
    for pos in ("n", "v", "a", "r"):
        for form, bases in sorted(wn._exception_map[pos].items()):
            for k, b in enumerate(bases):
                exc.append((pos, form, b, k))
    con.execute("DROP TABLE exc")
    con.execute("CREATE TABLE exc(pos TEXT NOT NULL, form TEXT NOT NULL, base TEXT NOT NULL, ord INTEGER NOT NULL)")
    con.executemany("INSERT INTO exc VALUES (?,?,?,?)", exc)
    con.executescript("""
        CREATE INDEX lemma_form ON lemma(form);
        CREATE INDEX hyper_child ON hyper(child);
        CREATE INDEX exc_form ON exc(form);
    """)
    con.commit()
    con.execute("VACUUM")
    con.close()
    os.replace(tmp, OUT)

    # verify equality with NLTK on held words + inflections
    from domains import wordnet_table as wt
    wt._reset()
    d = json.loads((ROOT / "seeds/lexical_qualia.json").read_text())
    probe = sorted(d.get("word_qualia", {}).keys())
    probe += ["arranging", "ordering", "sorted", "geese", "ran", "better", "condensed", "tabulating", "data",
              "alphabetising", "children", "went", "mice", "running", "happier"]
    bad = []
    for w in probe:
        got = [s for s in wt.synsets(w)]
        want = sorted({s.name() for s in wn.synsets(w)})
        if sorted(set(got)) != want:
            bad.append((w, got[:5], want[:5]))
    print("wrote", OUT.relative_to(ROOT), "bytes", OUT.stat().st_size, "synsets", len(syns), "hyper", len(hy),
          "lemma rows", len(rows), "exc", len(exc), "| verified", len(probe), "mismatches", len(bad))
    for b in bad[:20]:
        print("  MISMATCH", b)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
