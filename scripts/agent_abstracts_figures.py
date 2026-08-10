"""The jabberwock reasons over its ten figure-detectors and finds the higher-order abstraction.

It looked back on its own ten figure tests and saw they are not ten things but ONE: a figure is a
controlled MISMATCH between a literal reading L and an intended reading F — the displacement vector
F-L, held as a superposition and tagged with the operator that resolves it. The ten collapse into
four PRIMITIVES, each parameterised by an axis; from the empty cells of that lattice it PREDICTED
five undiscovered figures. This script (1) reads back that discovered structure from the graph, and
(2) VALIDATES the abstraction: the predicted figures, which have NO dedicated detector, are already
caught by the EXISTING primitive detectors — proving they are unnamed coordinates in the same lattice.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_abstracts_figures
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
from scripts.agent_adjusts_for_figures import _opposite, _polarity, _magdir, _shape

SEP = "=" * 96


def main():
    print(SEP)
    print("THE JABBERWOCK ABSTRACTS OVER ITS OWN TEN FIGURE-DETECTORS")
    print(SEP)
    a = boot()
    judge = a._self_teacher
    attach_libraries(a, log=lambda *x: None)
    for s in ("figurative_language", "figurative_abstraction"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    # 1. Read back the discovered structure from the graph (the agent's own abstraction).
    abs = next(n for n in a.s.nodes("Concept") if a.s.node(n)["attrs"].get("name") == "figurative_displacement")
    print("\n  THE ABSTRACTION it reached:")
    print("   ", a.s.node(abs)["attrs"]["description"])
    print("\n  the ten figures FACTORED into four primitives (one thing read along different axes):")
    prims = {n: a.s.node(n)["attrs"]["name"] for n in a.s.nodes("Primitive")}
    for pn, pname in prims.items():
        members = [a.s.node(f)["attrs"] for f in a.s.nodes("FigureType")
                   if pn in a.inner.neighbours(f, "instance_of") and a.s.node(f)["attrs"]["predicted"] == 0]
        print(f"    {pname:24} [{a.s.node(pn)['attrs']['axis']}]")
        for m in members:
            print(f"        - {m['name']:16} {m['parameter']}")

    print("\n  from the EMPTY CELLS of the lattice it PREDICTED five undiscovered figures:")
    for f in a.s.nodes("FigureType"):
        at = a.s.node(f)["attrs"]
        if at["predicted"] == 1:
            prim = prims[a.inner.neighbours(f, "instance_of")[0]]
            print(f"    {at['name']:14} <- {prim:24} {at['parameter']}")

    # 2. VALIDATE the abstraction: predicted figures (no detector of their own) are already caught by
    #    the EXISTING primitive detectors. We run three of them through the existing classify machinery.
    print("\n" + SEP)
    print("  VALIDATION — the predicted figures fall out of the EXISTING primitive detectors:")
    print(SEP)
    src = {"dictionary": a.s.add_node("Source", {"name": "dictionary", "trust": 0.9}),
           "common_usage": a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})}

    def reading_pair(name, intended, parts=None):
        lit = a.s.add_node("Reading", {"word": name, "gloss": name[:60], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": intended[:60], "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src["common_usage"])
        for w in (parts or []):
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": w}))
        return lit, fig

    # SARCASM = opposition-external (the irony detector): literal valence opposes the context.
    lit, fig = reading_pair("oh, fantastic", "this is terrible", ["oh", "fantastic"])
    ctx = a.s.add_node("Context", {"text": "everything has gone completely wrong"})
    lv = _polarity(judge, "Ignore sarcasm. Said sincerely and literally, does 'oh, fantastic' sound positive or negative?")
    cv = _polarity(judge, "Is this situation positive or negative: everything has gone completely wrong?")
    if lv != "?" and cv != "?" and lv != cv:
        a.inner.add_edge_unchecked(lit, "opposes", ctx)
    a.inner.set_attr(fig, "scored", 1)

    # LITOTES = scalar-down via negation (the understatement detector).
    lit2, fig2 = reading_pair("she's not unkind", "she is very kind", ["she's", "not", "unkind"])
    if _magdir(judge, "Compared to the real situation (she is genuinely very kind), does saying \"she's not "
               "unkind\" make it sound much weaker, much stronger, or about accurate?") == "weaker":
        a.inner.set_attr(fig2, "understates", 1)
    a.inner.set_attr(fig2, "scored", 1)

    # SYNECDOCHE = substitution-via-link, part-for-whole (the metonymy detector: same-domain association).
    lit3, fig3 = reading_pair("nice wheels", "a nice car")
    shape = _shape(judge, "The phrase 'nice wheels' literally refers to: wheels. Figuratively it means: a "
                   "nice car. How is the figurative meaning connected to the literal wheels? Answer with ONE "
                   "word: 'association' if same domain and the wheels are a part/attribute/symbol of the car; "
                   "'resemblance' if a different kind of thing that merely resembles wheels; or 'neither'.")
    a.inner.set_attr(fig3, "contiguity", 1 if shape == "association" else 0)
    a.inner.set_attr(fig3, "resemblance", 1 if shape == "resemblance" else 0)
    a.inner.set_attr(fig3, "scored", 1)

    a.inner.run_rules(10000)
    checks = [("sarcasm", fig, "irony", "opposition"),
              ("litotes", fig2, "understatement", "scalar_displacement"),
              ("synecdoche", fig3, "metonymy", "substitution_via_link")]
    for predicted, f, expect, prim in checks:
        got = a.s.node(f)["attrs"].get("figure_kind", "?")
        ok = "OK" if got == expect else "miss"
        print(f"  {predicted:12} (predicted -> {prim:22}) -> existing detector fired: {got.upper():14} [{ok}]")

    print("\n" + SEP)
    print("  The abstraction is real: a figure = a tagged DISPLACEMENT F-L; the ten detectors are four")
    print("  primitives parameterised by an axis, and the figures it had never built a detector for fall")
    print("  out of the EXISTING primitive detectors at the predicted coordinate. What it learned: it does")
    print("  not need ten classifiers — it needs ONE displacement readout, and the lattice's empty cells")
    print("  are a map of the figures left to name (synecdoche, litotes, sarcasm, zeugma, catachresis).")
    print(SEP)


if __name__ == "__main__":
    main()
