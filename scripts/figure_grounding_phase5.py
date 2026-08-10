"""PHASE 5 VERIFICATION — ground metaphor vs metonymy by the SHAPE of the figure_of mapping. NO LLM.

The figure judge's `_shape` (a claude -p forced-choice) is retired. The governing asymmetry: metonymy is
a LINK with no shared property; metaphor is a SHARED PROPERTY across far domains with NO link — so find the
link FIRST. The strongest link-finder is Wiktionary's OWN sense tags (a word's conventional metonymy is one
Wiktionary records as a 'metonymically'/'figuratively' sense), corroborated by WordNet meronymy / ConceptNet
contiguity. Resemblance fires only when no link is found AND the terms cross WordNet domains.

  contiguity=1 -> METONYMY ; resemblance=1 -> METAPHOR. classify_figure unchanged.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.figure_grounding_phase5
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs._native as _N
from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.symbolic_perception import register_symbolic_handlers, wikt_metonymic, cn_contiguity, shape_cross_domain

SEP = "=" * 96

# (name, literal keyword, figurative meaning, expected kind)
CORPUS = [
    ("the crown",      "crown",   "the monarch, the monarchy, or royal authority", "metonymy"),
    ("the bench",      "bench",   "the judges or the judiciary", "metonymy"),
    ("suits",          "suit",    "business executives or corporate management", "metonymy"),
    ("a red herring",  "herring", "a misleading distraction or false clue", "metaphor"),
    ("time the thief", "time",    "a thief that steals moments of life", "metaphor"),
]


def main():
    print(SEP)
    print("PHASE 5 — metaphor vs metonymy grounded by mapping SHAPE (Wiktionary sense tags + WordNet). NO LLM.")
    print(SEP)
    a = boot()
    names = register_symbolic_handlers(_N)
    for s in ("figurative_language", "figure_grounding"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    print(f"\n  registered handlers: {names}; figure_grounding seed loaded (LLM judge NOT wired)\n")

    src_dict = a.s.add_node("Source", {"name": "dictionary", "trust": 0.9})
    src_cu = a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})

    def build(kw, fig_gloss):
        lit = a.s.add_node("Reading", {"word": kw, "gloss": kw, "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": kw, "gloss": fig_gloss, "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src_dict)
        a.inner.add_edge_unchecked(fig, "claimed_by", src_cu)
        return lit, fig

    rows = [(name, kw, fg, exp, *build(kw, fg)) for name, kw, fg, exp in CORPUS]
    a.inner.run_rules(20000)                        # detect_figure + ground_contiguity/resemblance (via UseTool)
    for *_, fig in rows:
        a.inner.set_attr(fig, "scored", 1)          # host releases the classifier
    a.inner.run_rules(20000)                        # classify_figure

    print(f"  {'figure':16} {'kw':9} wkt cn cross  {'flags':22} {'kind':10} verdict")
    print("  " + "-" * 90)
    npass = 0
    for name, kw, fg, exp, lit, fig in rows:
        m, c, x = wikt_metonymic(kw, fg), cn_contiguity(kw, fg), shape_cross_domain(kw, fg)
        at = a.s.node(fig)["attrs"]
        flags = f"contig={at.get('contiguity','-')} resem={at.get('resemblance','-')}"
        kind = at.get("figure_kind", "?")
        ok = kind == exp
        npass += ok
        print(f"  {name:16} {kw:9} {m:>3} {c:>2} {x:>5}  {flags:22} {kind:10} "
              f"{'PASS' if ok else 'FAIL'} (expect {exp})")

    print("\n  " + "-" * 90)
    print(f"  {npass}/{len(rows)} as expected. metaphor vs metonymy grounded with ZERO claude -p calls — `_shape`")
    print(f"  is retired. The crux the creator found: Wiktionary LABELS its metonymic senses (crown ->")
    print(f"  'metonymically: the sovereign'; suit -> 'metonymically: a boss'), so conventional metonymy is a")
    print(f"  direct curated signal — what no WordNet/ConceptNet edge could supply. Resemblance fires only")
    print(f"  when that link search comes up empty AND the terms cross WordNet domains. Abstains otherwise.")
    print(SEP)


if __name__ == "__main__":
    main()
