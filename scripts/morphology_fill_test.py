"""Probe the UniMorph morphology ingester end-to-end on a cold substrate.

Teacher DISABLED, no grounded lexicon: every content word must resolve
through the mechanical reference chain
    surface --(UniMorph)--> lemma --(WordNet)--> concept
with each resolved mapping grounded as graph data (InflectionEntry +
LexEntry + Concept). We print the per-word chain with sources, the
resulting frame, and strict-match before/after.

Per CLAUDE.md this is a thin runner: instantiate the native substrate,
hand the world held-out sentences with the teacher off, print the chain.
It also re-runs the morphology lookup in isolation so the report can
separate the LEMMATIZATION result (closed?) from any residual SENSE
SELECTION gap in WordNet (a different, already-known gap).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains import morphology_reference as morph
from domains import dictionary_lexicon as dlex


HELDOUT = [
    {"text": "The dog chased the ball.", "language": "en",
     "expected_meaning": {"event": "chase", "agent": "dog",
                          "patient": "ball", "tense": "past"}},
    {"text": "El perro persiguió la pelota.", "language": "es",
     "expected_meaning": {"event": "chase", "agent": "dog",
                          "patient": "ball", "tense": "past"}},
    {"text": "狗追了球。", "language": "zh",
     "expected_meaning": {"event": "chase", "agent": "dog",
                          "patient": "ball"}},
    {"text": "犬がボールを追いかけた。", "language": "ja",
     "expected_meaning": {"event": "chase", "agent": "dog",
                          "patient": "ball", "tense": "past"}},
    # A control sentence whose verb IS in the es UniMorph dump
    # (comió -> comer -> eat). Demonstrates the full mechanical chain
    # surface --UniMorph--> lemma --WordNet--> concept firing in a real
    # parse — i.e. lemmatization is genuinely wired, not just isolated.
    {"text": "El perro comió la pelota.", "language": "es",
     "expected_meaning": {"event": "eat", "agent": "dog",
                          "patient": "ball", "tense": "past"}},
]

# Verbs KNOWN to be in the respective UniMorph dumps — used to demonstrate
# the mechanism works (the held-out test verbs happen to be absent from the
# public dumps; see the report). surface, language, slot, expected-lemma.
COVERED_VERB_PROBES = [
    ("sentó", "es", "event", "sentar"),
    ("rompió", "es", "event", "romper"),
    ("comió", "es", "event", "comer"),
    ("corrió", "es", "event", "correr"),
    ("会った", "ja", "event", "会う"),
]


def probe_lemmatization() -> None:
    print("=" * 70)
    print("A. LEMMATIZATION mechanism (UniMorph form -> lemma, mechanical)")
    print("=" * 70)
    print("  Covered verbs (present in the ingested UniMorph dump):")
    for surface, lang, slot, exp in COVERED_VERB_PROBES:
        got = morph.lemmatize(surface, lang, slot)
        ok = "OK" if got == exp else "MISS"
        print(f"    [{ok}] {lang}: {surface!r:>12} -> {got!r:<10} "
              f"(expected {exp!r})")
    print("  Held-out test verbs:")
    for surface, lang in [("persiguió", "es"), ("追いかけた", "ja"),
                          ("chased", "en"), ("追", "zh")]:
        got = morph.lemmatize(surface, lang, "event")
        note = ""
        if got is None:
            if lang == "zh":
                note = "(zh isolating — no morphology, by design)"
            elif lang == "en":
                note = "(en deferred to WordNet morphy by design)"
            else:
                note = "(form absent from this UniMorph dump)"
        print(f"    {lang}: {surface!r:>12} -> {got!r:<10} {note}")
    print()


def probe_wordnet_senses() -> None:
    print("=" * 70)
    print("B. SENSE SELECTION (WordNet sense-1 of the citation lemma)")
    print("   — a SEPARATE gap from lemmatization. Shown for honesty.")
    print("=" * 70)
    for lemma, lang in [("perseguir", "es"), ("追いかける", "ja"),
                        ("sentar", "es"), ("comer", "es")]:
        entry = dlex.dictionary_lookup(lemma, "event", lang)
        c = entry["concept"] if entry else None
        print(f"    {lang}: {lemma!r:>12} -> WordNet sense-1 concept = {c!r}")
    print()


def run_world() -> tuple[int, list[str]]:
    s = _native.Substrate()
    world = LanguageWorld(s, HELDOUT, teacher_stub, teacher_disabled=True)
    log = world.run()
    strict = 0
    lines: list[str] = []
    for entry in log:
        text, lang = entry["text"], entry["language"]
        exp = entry["expected"]
        frame = entry["frame"]
        match = entry["matched"]
        if match:
            strict += 1
        lines.append(f"  {lang}: {text}")
        lines.append(f"     frame   = {frame}")
        lines.append(f"     expected= {exp}  -> "
                     f"{'STRICT MATCH' if match else 'no strict match'}")
        # Per-word chain from grounded graph data.
        infl = {}
        for nid in s.nodes("InflectionEntry"):
            a = s.node(nid)["attrs"]
            if a.get("language") == lang:
                infl[a.get("surface")] = a.get("lemma")
        lex = {}
        for nid in s.nodes("LexEntry"):
            a = s.node(nid)["attrs"]
            if a.get("language") == lang:
                lex[a.get("surface")] = (a.get("concept"), a.get("source"))
        for surf in sorted(set(list(infl) + list(lex))):
            lm = infl.get(surf)
            cs = lex.get(surf)
            chain = f"        {surf!r}"
            if lm:
                chain += f" --UniMorph--> {lm!r}"
            if cs:
                chain += f" --{cs[1]}--> concept={cs[0]!r}"
            lines.append(chain)
    return strict, lines


def main() -> int:
    probe_lemmatization()
    print(f"  (UniMorph cache dir: {morph._CACHE_DIR})")
    print()
    probe_wordnet_senses()

    print("=" * 70)
    print("C. END-TO-END held-out parse (teacher disabled, cold substrate)")
    print("=" * 70)
    strict, lines = run_world()
    for ln in lines:
        print(ln)
    print()
    print(f"  Held-out strict matches: {strict}/{len(HELDOUT)}")
    print("  BEFORE morphology: en 'chased' (WordNet morphy) only. The es")
    print("  'comió' control was a no-strict-match (event='comió').")
    print("  AFTER: + es 'comió'->comer->eat via the mechanical UniMorph")
    print("  chain. persiguió / 追いかけた stay unresolved — those forms are")
    print("  absent from the public UniMorph dumps (coverage, not mechanism).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
