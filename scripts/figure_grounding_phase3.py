"""PHASE 3 VERIFICATION — ground irony by phrase valence vs situation valence. NO LLM.

The figure judge's `_polarity` (a claude -p forced-choice) is retired. Irony = a literal phrase whose
sincere valence OPPOSES the situation's valence. text_valence scores phrase sentiment from the curated
Bing Liu opinion lexicon (no per-sense WSD noise). The ground_irony rule asserts opposes(literal_reading,
context) when the signs are opposite; classify_figure then reads lit's opposes edge -> irony. (Sarcasm =
irony + scalar_spike, the over-the-top marker, which is magnitude — Phase 4.)

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.figure_grounding_phase3
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
from domains.symbolic_perception import register_symbolic_handlers, text_valence

SEP = "=" * 96

# (literal phrase, intended meaning, situation, expect_irony)
CORPUS = [
    ("what lovely weather", "the weather is terrible", "a violent thunderstorm is raging", True),
    ("great job", "you failed badly", "he completely failed the task", True),
    ("I just love waiting in line", "waiting is awful", "stuck in a two-hour queue", True),
    ("what a beautiful day", "the day is lovely", "the sun is shining warmly", False),   # sincere: + over +
    ("this is fine", "it is fine", "everything works perfectly", False),                  # sincere: + over +
]


def main():
    print(SEP)
    print("PHASE 3 — irony grounded by phrase valence vs situation valence (opinion lexicon). NO LLM.")
    print(SEP)
    a = boot()
    names = register_symbolic_handlers(_N)
    for s in ("figurative_language", "figure_grounding"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    print(f"\n  registered handlers: {names}; figure_grounding seed loaded (LLM judge NOT wired)\n")

    src_dict = a.s.add_node("Source", {"name": "dictionary", "trust": 0.9})
    src_cu = a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})

    def build(name, intended, situation):
        lit = a.s.add_node("Reading", {"word": name, "gloss": name, "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": intended, "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src_dict)
        a.inner.add_edge_unchecked(fig, "claimed_by", src_cu)
        for w in name.split():
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": w}))
        ctx = a.s.add_node("Context", {"text": situation})
        a.inner.add_edge_unchecked(fig, "has_context", ctx)
        return name, situation, lit, ctx, fig

    rows = [(exp, *build(n, i, s)) for n, i, s, exp in CORPUS]
    a.inner.run_rules(20000)                        # detect_figure + ground_irony (via UseTool)
    for *_, fig in rows:
        a.inner.set_attr(fig, "scored", 1)          # host releases the classifier
    a.inner.run_rules(20000)                        # classify_figure

    print(f"  {'literal phrase':28} val | {'situation':30} val  opp  {'kind':10} verdict")
    print("  " + "-" * 96)
    npass = 0
    for exp, name, situation, lit, ctx, fig in rows:
        lv, cv = text_valence(name), text_valence(situation)
        opp = bool(a.inner.neighbours(lit, "opposes"))
        kind = a.s.node(fig)["attrs"].get("figure_kind", "?")
        is_iro = kind == "irony"
        ok = (is_iro == exp) and (opp == exp)
        npass += ok
        print(f"  {name:28} {lv:>+2} | {situation:30} {cv:>+2}  {str(opp):>5}  {kind:10} "
              f"{'PASS' if ok else 'FAIL'} (expect {exp})")

    print("\n  " + "-" * 96)
    print(f"  {npass}/{len(rows)} as expected. Irony grounded with ZERO claude -p calls — `_polarity` is")
    print(f"  retired. Literal valence vs situation valence, opposite signs -> opposes(lit, context) -> irony.")
    print(f"  Curated opinion lexicon avoids the WSD noise that sank per-sense SentiWordNet on phrases.")
    print(f"  Sincere positive-over-positive correctly stays out. (Sarcasm = irony + scalar_spike: Phase 4.)")
    print(SEP)


if __name__ == "__main__":
    main()
