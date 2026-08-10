"""jabberwock_reads_curie — THE COMPLETE READ of the Marie Curie Wikipedia
article, and the three residuals FIXED.

The register/source faculty (domains/register_source.py) routes an encyclopedic
page to `subject_by_salience`. Reading the FULL article (44K chars, ~373
sentences) exposed three residuals, each fixed here and reported honestly:

  (1) THE CAP — `route_reading` inherited read_and_comprehend's default
      max_sentences=40, truncating the article to ~14%. FIXED: the routed read
      comprehends the WHOLE article (a high cap kept as a perf param).

  (2) NAME-VARIANT FRAGMENTATION — the subject split four ways
      (curie / maria / skłodowska / marie_curie), all Marie Curie. FIXED
      (domains/name_variant_merge.py): a person's name forms are unified into ONE
      entity by name-part overlap + first-name variant + 'née X' alias, into the
      salient subject — generically (Pierre Curie's forms also merge), with no
      over-merge (Pierre stays distinct from Marie though they share the surname).

  (3) GENDER-LEAK — the dominant female 'she' bled female onto a date (1891), a
      substance (radium), an institution (university), and onto Pierre. FIXED:
      gender is decoded PER-ENTITY (animate-gate + own-evidence): a
      date/substance/institution carries NO gender; an animate person's gender is
      its own he/she (Pierre -> male via his full-name form).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_curie.py
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import reading_collapse as rc                      # noqa: E402
from domains import register_source as rs                       # noqa: E402

_CURIE_CACHE = os.path.join(ROOT, "data", "register", "curie.txt")
_SUBJECT_FORMS = ("curie", "maria", "marie", "marie_curie", "skłodowska")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _entities(agent):
    sub = agent.s
    out = {}
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if isinstance(nm, str) and nm:
            out[nm] = {"mentions": float(at.get("coref_mentions", 0.0) or 0.0),
                       "gender": at.get("coref_gender") or "",
                       "animate": float(at.get("coref_animate", 1.0) or 0.0),
                       "merged_into": at.get("merged_into")}
    return out


def _leak_count(ents):
    """Entities wrongly female that SHOULD be non-animate — a date/number, or a
    word the reader's dictionary types as a concrete inanimate thing
    (substance/location/group/institution). This is the honest gender-leak metric:
    a female animate person/role is NOT wrong here; a female 'radium'/'university'/
    '1891' is. Merged-away forms are excluded."""
    from domains import name_variant_merge as nvm
    out = []
    for nm, e in ents.items():
        if e["merged_into"] or e["gender"] != "female":
            continue
        if str(nm).isdigit() or nvm._wordnet_inanimate(nm):
            out.append(nm)
    return sorted(out)


def run(text: str | None = None) -> dict:
    dl.warm_wordnet("en")
    if text is None:
        with open(_CURIE_CACHE) as f:
            text = f.read()
    n_sentences = len([s for s in rc._split_sentences(text) if s.strip()])

    # BEFORE — the routed read WITHOUT the name-variant/gender refinement (the
    # read-time animacy gate is in place; this isolates the post-read pass's effect).
    ag0 = _fresh()
    rs.route_reading(ag0, text, merge_variants=False)
    before = _entities(ag0)

    # AFTER — the complete routed read WITH refinement.
    ag = _fresh()
    t0 = time.time()
    routed = rs.route_reading(ag, text)
    dt = time.time() - t0
    after = _entities(ag)
    refine = routed["result"].get("refine", {})

    return {"n_sentences": n_sentences, "seconds": dt, "routed": routed,
            "before": before, "after": after, "refine": refine,
            "n_entities": len(after)}


def _print(rep: dict) -> None:
    routed = rep["routed"]
    res = routed["result"]
    after = rep["after"]
    print("=" * 70)
    print("THE COMPLETE READ — Marie Curie (Wikipedia)")
    print("=" * 70)
    print("register       : %s / %s -> %s" % (routed["register"], routed["family"],
                                               routed["read_approach"]))
    print("sentences read : %d   entities: %d   time: %.1fs"
          % (rep["n_sentences"], rep["n_entities"], rep["seconds"]))
    print("SUBJECT        : %s  (mentions %s)" % (res["subject"], res["mentions"]))
    print()
    print("(2) NAME-VARIANT MERGE")
    for c in rep["refine"].get("merge", {}).get("clusters", []):
        print("   %-8s <- %s   (%d -> %d mentions)"
              % (c["canonical"], ", ".join(c["absorbed"]),
                 int(c["mentions_before"]), int(c["mentions_after"])))
    print("   aliases (née/known-as): %s"
          % ", ".join(rep["refine"].get("merge", {}).get("aliases", [])))
    print()
    print("(3) GENDER PRECISION")
    for nm in ("curie", "pierre", "1891", "radium", "university"):
        e = after.get(nm)
        if e:
            print("   %-11s gender=%-7r animate=%s mentions=%d"
                  % (nm, e["gender"], e["animate"], int(e["mentions"])))
    print("   gender-leak (non-animate wrongly female):")
    print("       before refine: %s" % _leak_count(rep["before"]))
    print("       after  refine: %s" % _leak_count(after))
    print("=" * 70)


if __name__ == "__main__":
    _print(run())
