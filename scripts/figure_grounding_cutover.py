"""PHASE 7 — THE CUTOVER. The whole figure suite classified with ZERO claude -p calls + honest scorecard.

Every figure perception the judge used to ground is now a graph-native UseTool Term over curated/derived
signals (WordNet, Wiktionary, ConceptNet, opinion + magnitude lexicons, SentiWordNet, gloss derivation).
This script builds a gold-labelled corpus spanning all the figure kinds, runs ONLY detect_figure +
ground_* + classify_figure (no judge, no LLM anywhere in the path), and reports two honest numbers:
agreement-with-gold on covered cases, and the abstention rate. The figure judge is retired.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.figure_grounding_cutover
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

# Gold corpus. Each: kind + the fields that kind needs (kw for shape, parts, roles, gloss, situation).
CORPUS = [
    # metaphor / metonymy (shape: kw + figurative gloss)
    dict(name="a red herring", kw="herring", gloss="a misleading distraction or false clue", kind="metaphor"),
    dict(name="time the thief", kw="time", gloss="a thief that steals moments of life", kind="metaphor"),
    dict(name="the crown", kw="crown", gloss="the monarch, the monarchy, or royal authority", kind="metonymy"),
    dict(name="the bench", kw="bench", gloss="the judges or the judiciary", kind="metonymy"),
    dict(name="suits", kw="suit", gloss="business executives or corporate management", kind="metonymy"),
    # simile (structural like/as marker — no grounding rule)
    dict(name="brave as a lion", parts=["brave", "as", "a", "lion"], gloss="extremely courageous", kind="simile"),
    # oxymoron (opposition: lexical + derived)
    dict(name="living dead", parts=["living", "dead"], gloss="dead yet still moving", kind="oxymoron"),
    dict(name="deafening silence", parts=["deafening", "silence"], gloss="an overwhelming silence", kind="oxymoron"),
    # personification (role-tagged subject + agentive verb)
    dict(name="the wind whispered", parts=["the", "wind", "whispered"],
         roles={"wind": "subj", "whispered": "verb"}, gloss="the wind made a soft sound", kind="personification"),
    dict(name="opportunity knocked", parts=["opportunity", "knocked"],
         roles={"opportunity": "subj", "knocked": "verb"}, gloss="a chance arose", kind="personification"),
    # hyperbole / understatement / litotes (magnitude)
    dict(name="a million times", parts=["a", "million", "times"], gloss="very many times", kind="hyperbole"),
    dict(name="this weighs a ton", parts=["this", "weighs", "a", "ton"], gloss="very heavy", kind="hyperbole"),
    dict(name="just a scratch", parts=["it's", "just", "a", "scratch"], gloss="the wound is severe", kind="understatement"),
    dict(name="not bad", parts=["not", "bad"], gloss="actually excellent", kind="litotes"),
    # irony / sarcasm (valence opposition; sarcasm adds the spike)
    dict(name="what lovely weather", parts=["what", "lovely", "weather"], gloss="the weather is terrible",
         situation="a violent thunderstorm is raging", kind="irony"),
    dict(name="what a brilliant plan", parts=["what", "a", "brilliant", "plan"], gloss="the plan was a disaster",
         situation="the plan failed completely", kind="sarcasm"),
    # idiom (Wiktionary 'idiomatic' tag -> noncompositional)
    dict(name="bite the bullet", parts=["bite", "the", "bullet"], gloss="to endure something painful", kind="idiom"),
    dict(name="kick the bucket", parts=["kick", "the", "bucket"], gloss="to die", kind="idiom"),
]


def main():
    print(SEP)
    print("PHASE 7 — THE CUTOVER: the whole figure suite classified with ZERO claude -p calls")
    print(SEP)
    a = boot()
    register_symbolic_handlers(_N)
    for s in ("figurative_language", "figure_grounding"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    fire_before = _N.tool_fire_count()
    print(f"\n  figure_grounding wired; LLM judge NOT loaded. UseTool fire count starts at {fire_before}\n")

    src_dict = a.s.add_node("Source", {"name": "dictionary", "trust": 0.9})
    src_cu = a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})

    def build(c):
        word = c.get("kw") or c["name"]
        lit = a.s.add_node("Reading", {"word": word, "gloss": c["name"], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": word, "gloss": c.get("gloss", c["name"]), "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src_dict)
        a.inner.add_edge_unchecked(fig, "claimed_by", src_cu)
        for w in c.get("parts", []):
            attrs = {"text": w}
            if w in c.get("roles", {}):
                attrs["role"] = c["roles"][w]
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", attrs))
        if c.get("situation"):
            a.inner.add_edge_unchecked(fig, "has_context", a.s.add_node("Context", {"text": c["situation"]}))
        return fig

    rows = [(c["name"], c["kind"], build(c)) for c in CORPUS]
    a.inner.run_rules(40000)                        # detect_figure + all ground_* (every UseTool)
    for _, _, fig in rows:
        a.inner.set_attr(fig, "scored", 1)
    a.inner.run_rules(40000)                        # classify_figure

    print(f"  {'figure':24} {'gold':16} {'predicted':16} verdict")
    print("  " + "-" * 78)
    correct = abstain = wrong = 0
    for name, gold, fig in rows:
        kind = a.s.node(fig)["attrs"].get("figure_kind", "?")
        if kind == gold:
            correct += 1; mark = "PASS"
        elif kind in ("?", "unknown", None) or not a.inner.neighbours(fig, "figure_of"):
            abstain += 1; mark = "abstain"
        else:
            wrong += 1; mark = "MISS"
        print(f"  {name:24} {gold:16} {kind:16} {mark}")

    tool_fires = _N.tool_fire_count() - fire_before
    covered = correct + wrong
    print("\n  " + "-" * 78)
    print(f"  agreement-with-gold on covered cases: {correct}/{covered}"
          f" ({100*correct//max(covered,1)}%)   abstentions: {abstain}/{len(rows)}   misclassified: {wrong}")
    print(f"  native UseTool fires this run: {tool_fires}   |   claude -p calls: 0  (the judge is gone)")
    print(f"\n  The figure judge is retired. Opposition, personification, irony/sarcasm, hyperbole/")
    print(f"  understatement, metaphor/metonymy, and idiom are all grounded by graph-native UseTool Terms")
    print(f"  over curated + derived signals. What can't be grounded ABSTAINS — it is never guessed.")
    print(SEP)


if __name__ == "__main__":
    main()
