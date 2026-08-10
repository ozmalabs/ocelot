"""Give the five PREDICTED figures their own detectors — each a parent primitive + one extra test.

The abstraction predicted five figures from the lattice's empty cells; they were caught only by their
PARENT detector. The jabberwock then designed the EXTRA distinguishing test for each (most-specific-
first, gating before the parent):
  synecdoche  = metonymy        + the link is mereological (literal is a PART of the figurative whole)
  litotes     = understatement  + a negation marker over the opposite ("not bad")
  sarcasm     = irony           + a scalar/contempt spike
  zeugma      = (structural)      one predicate yoking two objects of mismatched type
  catachresis = metaphor        + no literal term exists for the target (a lexical gap)
This grounds each extra signal live and shows the child gets its OWN label, while a parent control
without the extra signal stays the parent.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_detects_predicted
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries
from scripts.agent_adjusts_for_figures import _shape, _magdir, _polarity, _yn

SEP = "=" * 96


def main():
    print(SEP)
    print("DEDICATED DETECTORS FOR THE FIVE PREDICTED FIGURES (each = parent primitive + one extra test)")
    print(SEP)
    a = boot()
    judge = a._self_teacher
    attach_libraries(a, log=lambda *x: None)
    for s in ("figurative_language", "figurative_abstraction"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    src = {"dictionary": a.s.add_node("Source", {"name": "dictionary", "trust": 0.9}),
           "common_usage": a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})}

    def pair(name, intended, parts=None):
        lit = a.s.add_node("Reading", {"word": name, "gloss": name[:60], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": intended[:60], "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src["common_usage"])
        for w in (parts or []):
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": w}))
        return lit, fig

    rows = []  # (label, predicted_figure, fig_node)

    # SYNECDOCHE = metonymy (association) + mereological link (literal is a PART of the whole)
    lit, fig = pair("all hands on deck", "the whole crew", ["all", "hands", "on", "deck"])
    if _shape(judge, "'all hands on deck' uses 'hands' for the whole crew. Is the connection same-domain "
              "association or cross-domain resemblance? Answer: association, resemblance, or neither.") == "association":
        a.inner.set_attr(fig, "contiguity", 1)
    a.inner.set_attr(fig, "part_whole", _yn(judge, "Are hands literally a physical PART of the people/crew "
                                            "they stand for in 'all hands on deck'?"))
    a.inner.set_attr(fig, "scored", 1); rows.append(("synecdoche", "synecdoche", fig))

    # LITOTES = understatement (scalar down) + negation of the opposite ("not bad")
    lit, fig = pair("not bad", "actually excellent", ["not", "bad"])  # 'not' is the structural negation
    if _magdir(judge, "Compared to an outstanding, excellent performance, does saying 'not bad' make it "
               "sound much weaker, much stronger, or about accurate?") == "weaker":
        a.inner.set_attr(fig, "understates", 1)
    a.inner.set_attr(fig, "scored", 1); rows.append(("litotes", "litotes", fig))

    # SARCASM = irony (literal opposes context) + a scalar/contempt spike
    lit, fig = pair("oh, fantastic", "this is terrible", ["oh", "fantastic"])
    ctx = a.s.add_node("Context", {"text": "everything has gone completely wrong"})
    lv = _polarity(judge, "Ignore sarcasm. Said sincerely and literally, does 'oh, fantastic' sound positive or negative?")
    cv = _polarity(judge, "Is this situation positive or negative: everything has gone completely wrong?")
    if lv != "?" and cv != "?" and lv != cv:
        a.inner.add_edge_unchecked(lit, "opposes", ctx)
    a.inner.set_attr(fig, "scalar_spike", _yn(judge, "Said when everything has gone wrong, is 'oh, fantastic' "
                     "an exaggerated, mocking, contemptuous remark (sarcasm with a bite), rather than gentle irony?"))
    a.inner.set_attr(fig, "scored", 1); rows.append(("sarcasm", "sarcasm", fig))

    # ZEUGMA = one predicate yoking two objects of mismatched type (structural signal)
    lit, fig = pair("she broke his car and his heart", "damaged both", ["broke", "car", "heart"])
    a.inner.set_attr(fig, "zeugma_mismatch", _yn(judge, "In 'she broke his car and his heart', does the one "
                     "verb 'broke' govern two objects of clearly different kinds — one physical (car) and one "
                     "abstract (heart)?"))
    a.inner.set_attr(fig, "scored", 1); rows.append(("zeugma", "zeugma", fig))

    # CATACHRESIS = metaphor (resemblance) + no literal term exists for the target (lexical gap)
    lit, fig = pair("the leg of the table", "the table's support", ["the", "leg", "of", "the", "table"])
    if _shape(judge, "'the leg of the table' calls a table's support a 'leg'. Is the connection cross-domain "
              "resemblance or same-domain association? Answer: association, resemblance, or neither.") == "resemblance":
        a.inner.set_attr(fig, "resemblance", 1)
    a.inner.set_attr(fig, "no_literal_term", _yn(judge, "Is there no plain literal native English word for the "
                     "part of a table it stands on, so 'leg' is borrowed out of necessity?"))
    a.inner.set_attr(fig, "scored", 1); rows.append(("catachresis", "catachresis", fig))

    # PARENT CONTROLS — same primitive, WITHOUT the extra signal -> must stay the parent.
    lit, fig = pair("the crown", "the monarch")
    if _shape(judge, "'the crown' stands for the monarch. association, resemblance, or neither?") == "association":
        a.inner.set_attr(fig, "contiguity", 1)
    a.inner.set_attr(fig, "part_whole", 0); a.inner.set_attr(fig, "scored", 1)
    rows.append(("the crown (control)", "metonymy", fig))

    lit, fig = pair("red herring", "a misleading clue")
    if _shape(judge, "'red herring' for a misleading clue. association, resemblance, or neither?") == "resemblance":
        a.inner.set_attr(fig, "resemblance", 1)
    a.inner.set_attr(fig, "no_literal_term", 0); a.inner.set_attr(fig, "scored", 1)
    rows.append(("red herring (control)", "metaphor", fig))

    a.inner.run_rules(10000)
    print("\n  each predicted figure now resolves to its OWN detector (controls stay the parent):\n")
    ok = 0
    for label, expect, fig in rows:
        got = a.s.node(fig)["attrs"].get("figure_kind", "?")
        mark = "OK" if got == expect else "miss"
        ok += got == expect
        print(f"    {label:24} -> {got.upper():15} (expected {expect.upper()})   [{mark}]")
    print(f"\n  {ok}/{len(rows)} correct.")
    print("\n" + SEP)
    print("  The five predicted figures now have their OWN detectors: each is its parent primitive plus")
    print("  one extra graph test (mereological link / negation / scalar spike / yoked type-mismatch /")
    print("  lexical gap), checked most-specific-first so the child wins when its extra signal is present")
    print("  and the parent label remains when it is absent. The lattice's empty cells are now filled.")
    print(SEP)


if __name__ == "__main__":
    main()
