"""deep_comp_diagnose — diagnostic on real long Grimm tales. Measures the
deep-comprehension break: entity categorisation, unknown fraction, coref
over-segmentation, protagonist tracking. Read-only; no mutation of the stack."""
from __future__ import annotations

import os
import sys
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.reading_corpus as rc
from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import comprehension_reader as cr


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def diagnose(label, text, protagonists, max_sentences=60):
    agent = _fresh()
    graph = cr.read_and_comprehend(agent, text, window=2,
                                   max_sentences=max_sentences)
    spine = graph["spine"]
    sm = spine["situation_model"]
    n_sent = len([tb for tb in spine["textbase"] if (tb.get("predications"))])
    n_sent_all = len(spine["textbase"])
    cats = collections.Counter(v.get("coref_category") for v in sm.values())
    n_ent = len(sm)
    unknown = cats.get("unknown", 0)
    print("\n" + "=" * 70)
    print("TALE:", label)
    print("=" * 70)
    print("sentences(with preds)=%d  sentences(all)=%d  entities=%d  ent/sent=%.2f"
          % (n_sent, n_sent_all, n_ent, n_ent / max(n_sent_all, 1)))
    print("categories:", dict(cats))
    print("UNKNOWN fraction: %d/%d = %.1f%%" % (unknown, n_ent, 100.0 * unknown / max(n_ent, 1)))
    print("animals found:", cats.get("animal", 0), " persons:", cats.get("person", 0),
          " objects:", cats.get("object", 0))
    # protagonist tracking: is each protagonist ONE entity, and its category?
    print("\nPROTAGONIST TRACKING:")
    for p in protagonists:
        matches = {nm: st for nm, st in sm.items() if p == nm or nm.startswith(p + "_") or ("_" + p) in nm}
        exact = sm.get(p)
        cat = (exact or {}).get("coref_category") if exact else None
        mentions = (exact or {}).get("coref_mentions") if exact else None
        print("  %-10s exact_entity=%s cat=%s mentions=%s  (#name-variants=%d: %s)"
              % (p, exact is not None, cat, mentions, len(matches), list(matches)[:6]))
    # show the entity names (to see over-segmentation / junk)
    print("\nALL ENTITY NAMES (name -> category):")
    for nm in sorted(sm):
        print("   %-40s %s" % (nm[:40], sm[nm].get("coref_category")))
    return graph, sm, cats


if __name__ == "__main__":
    dl.warm_wordnet("en")
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    units = rc.load_units(sources=grimm)
    by = {u["label"]: u for u in units}
    tales = [
        ("THE TRAVELLING MUSICIANS", ["ass", "dog", "cat", "cock"]),
        ("OLD SULTAN", ["wolf", "dog", "sultan", "boar", "cat"]),
        ("THE WOLF AND THE SEVEN LITTLE KIDS", ["wolf", "goat", "kid"]),
        ("CAT AND MOUSE IN PARTNERSHIP", ["cat", "mouse"]),
    ]
    for label, prot in tales:
        if label in by:
            diagnose(label, by[label]["text"], prot)
        else:
            print("MISSING:", label)
