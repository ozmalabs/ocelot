"""PHASE 4 VERIFICATION — ground magnitude figures (hyperbole / understatement / litotes / sarcasm). NO LLM.

The figure judge's `_magdir` / exaggeration `_yn` (claude -p calls) are retired. Curated magnitude/intensity
lexicons (no WSD): scalar_violation = an extreme magnitude in the literal (hyperbole); understates = a
minimizer over a severe reality (understatement/litotes); scalar_spike = an over-the-top intensifier which,
with the irony opposes edge (Phase 3), makes SARCASM. classify_figure unchanged.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.figure_grounding_phase4
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
from domains.symbolic_perception import register_symbolic_handlers

SEP = "=" * 96

# (name, parts, intended meaning, situation-or-None, expected kind)
CORPUS = [
    ("a million times",      ["a", "million", "times"],          "very many times", None, "hyperbole"),
    ("waited forever",       ["waited", "forever"],              "waited a long time", None, "hyperbole"),
    ("this weighs a ton",    ["this", "weighs", "a", "ton"],     "very heavy", None, "hyperbole"),
    ("it's just a scratch",  ["it's", "just", "a", "scratch"],   "the wound is severe", None, "understatement"),
    ("a bit chilly",         ["a", "bit", "chilly"],             "it is freezing cold", None, "understatement"),
    ("not bad",              ["not", "bad"],                     "actually excellent", None, "litotes"),
    ("what a brilliant plan", ["what", "a", "brilliant", "plan"], "the plan was a disaster",
     "the plan failed completely", "sarcasm"),
]


def main():
    print(SEP)
    print("PHASE 4 — magnitude figures grounded by curated lexicons (hyperbole/understatement/sarcasm). NO LLM.")
    print(SEP)
    a = boot()
    names = register_symbolic_handlers(_N)
    for s in ("figurative_language", "figure_grounding"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    print(f"\n  registered handlers: {names}; figure_grounding seed loaded (LLM judge NOT wired)\n")

    src_dict = a.s.add_node("Source", {"name": "dictionary", "trust": 0.9})
    src_cu = a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})

    def build(name, parts, intended, situation):
        lit = a.s.add_node("Reading", {"word": name, "gloss": name, "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": intended, "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src_dict)
        a.inner.add_edge_unchecked(fig, "claimed_by", src_cu)
        for w in parts:
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": w}))
        if situation:
            ctx = a.s.add_node("Context", {"text": situation})
            a.inner.add_edge_unchecked(fig, "has_context", ctx)
        return fig

    rows = [(name, exp, build(name, parts, intended, sit)) for name, parts, intended, sit, exp in CORPUS]
    a.inner.run_rules(20000)                        # detect + ground_scalar_violation/understates/spike/irony
    for _, _, fig in rows:
        a.inner.set_attr(fig, "scored", 1)
    a.inner.run_rules(20000)                        # classify_figure

    print(f"  {'figure':22} {'flags':46} {'kind':15} verdict")
    print("  " + "-" * 96)
    npass = 0
    for name, exp, fig in rows:
        at = a.s.node(fig)["attrs"]
        flags = (f"sv={at.get('scalar_violation','-')} und={at.get('understates','-')} "
                 f"spike={at.get('scalar_spike','-')} opp={1 if a.inner.neighbours(fig, 'figure_of') and any(a.inner.neighbours(l,'opposes') for l in a.inner.neighbours(fig,'figure_of')) else '-'}")
        kind = at.get("figure_kind", "?")
        ok = kind == exp
        npass += ok
        print(f"  {name:22} {flags:46} {kind:15} {'PASS' if ok else 'FAIL'} (expect {exp})")

    print("\n  " + "-" * 96)
    print(f"  {npass}/{len(rows)} as expected. Magnitude figures grounded with ZERO claude -p calls — `_magdir`")
    print(f"  is retired. Extreme magnitude (million/ton/forever) -> hyperbole; a minimizer (just/a-bit/not)")
    print(f"  over a severe reality -> understatement/litotes; an over-the-top intensifier (brilliant) + the")
    print(f"  irony opposes edge -> SARCASM. All five figure perceptions are now LLM-free.")
    print(SEP)


if __name__ == "__main__":
    main()
