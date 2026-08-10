"""Function-word grounding test — show that FUNCTION WORDS (the / on / が /
を / に / en / el …) are GROUNDED on the comprehension side (as FunctionWord
graph nodes carrying function + grammatical_role), not filtered, and that this
(a) recovers the LOCATIVE role in comprehension and (b) lets production emit
fluent function words so the production self-monitor round-trip MATCHES.

Identity + function come from the REFERENCES (Wiktionary POS, already
ingested) + the grounded grammar (case-particle → role). NO hand-authored
meaning list.

Sections:
  1. Comprehension grounding — parse the sit-sentence per language; show the
     function words are grounded FunctionWord nodes and the frame recovers
     location (NOT patient).
  2. Round-trip lift — produce the sit-frame (now WITH function words), parse
     back, location recovered, round-trip matches. Before/after strings.
  3. Production fluency — the en/es/ja sit utterances now include the grounded
     function words.
  4. No regression — run the comprehension bank twice (12/12, 0 teacher pass
     2) and the held-out structural pass.

Per CLAUDE.md a thin runner: instantiate the native substrate, train
comprehension, drive production, print.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank, heldout_bank


SIT = {
    "en": "The cat sat on the mat.",
    "es": "El gato se sentó en la alfombra.",
    "ja": "猫がマットの上に座った。",
    "zh": "猫坐在垫子上。",
}


def _function_words(world, language):
    rows = []
    for fid in world.s.nodes("FunctionWord"):
        a = world.s.node(fid)["attrs"]
        if a.get("language") == language:
            rows.append(a)
    return rows


def main(argv: list[str]) -> int:
    s = _native.Substrate()
    world = LanguageWorld(s, training_bank(), teacher_stub)

    print("=" * 72)
    print("Setup: train comprehension on the 12-sentence bank (grounds grammar,")
    print("       lexicon, AND function words)")
    print("=" * 72)
    world.run()              # pass 1 — teacher grounds (incl. function words)
    log2 = world.run()       # pass 2 — parse from grounded knowledge
    matched2 = sum(1 for e in log2 if e["matched"])
    calls2 = sum(e["teacher_calls"] for e in log2)
    print(f"  pass 2: {matched2}/12 matched, {calls2} teacher calls")
    print(f"  FunctionWord nodes grounded: {len(s.nodes('FunctionWord'))}")
    print()

    print("=" * 72)
    print("1. COMPREHENSION GROUNDING — function words grounded, location")
    print("   recovered (NOT patient)")
    print("=" * 72)
    world.teacher_disabled = True
    for lang in ("en", "es", "zh", "ja"):
        text = SIT[lang]
        _l, _sk, shape = world._identify(text, lang)
        frame = world._parse_with_grounded(text, lang, shape)
        print(f"\n  [{lang}] {text!r}")
        print(f"    frame              : {frame}")
        loc = frame.get("location")
        pat = frame.get("patient")
        ok = (loc == "mat" and pat is None)
        print(f"    location=mat,no pat: {'YES' if ok else 'NO'} "
              f"(location={loc!r} patient={pat!r})")
        print(f"    grounded FunctionWords used:")
        for a in _function_words(world, lang):
            role = a.get("grammatical_role")
            defi = a.get("definiteness")
            extra = (f" role={role}" if role else "") + (
                f" def={defi}" if defi else "")
            print(f"        {a['surface']!r:8} function={a['function']:12}"
                  f"{extra}  [{a.get('source')}]")

    print()
    print("=" * 72)
    print("2. ROUND-TRIP LIFT — produce sit-frame WITH function words, parse")
    print("   back, location recovered")
    print("=" * 72)
    prod = LanguageProduction(world)
    base = {"event": "sit", "agent": "cat", "location": "mat",
            "tense": "past", "intent": "inform"}
    before_after = {
        "en": ("Cat sat mat.", None),
        "es": ("Gato sentó alfombra.", None),
        "ja": ("猫マット座った。", None),
        "zh": ("猫坐垫子。", None),
    }
    rt_match = 0
    for lang in ("en", "es", "ja", "zh"):
        goal = dict(base)
        if lang == "zh":
            goal.pop("tense", None)
        r = prod.produce(lang, goal)
        mon = r["self_monitor"]
        before = before_after[lang][0]
        print(f"\n  [{lang}]")
        print(f"    before (lemma-level): {before!r}")
        print(f"    after  (with fn-wds): {r['overt_speech']!r}")
        print(f"    recovered frame     : {mon['recovered_frame']}")
        print(f"    ROUND-TRIP MATCH    : {mon['match']}")
        if mon["match"]:
            rt_match += 1
    print(f"\n  round-trip match (sit-frame, all langs): {rt_match}/4 "
          f"(was 0/4 lemma-level)")

    print()
    print("=" * 72)
    print("3. PRODUCTION FLUENCY — sit utterances now carry grounded fn-words")
    print("=" * 72)
    for lang in ("en", "es", "ja"):
        goal = dict(base)
        r = prod.produce(lang, goal)
        print(f"  [{lang}] {r['overt_speech']!r}")

    print()
    print("=" * 72)
    print("4. NO REGRESSION")
    print("=" * 72)
    # Fresh substrate to mirror language_test exactly.
    s2 = _native.Substrate()
    w2 = LanguageWorld(s2, training_bank(), teacher_stub)
    w2.run()
    l2 = w2.run()
    m2 = sum(1 for e in l2 if e["matched"])
    c2 = sum(e["teacher_calls"] for e in l2)
    print(f"  comprehension pass 2: {m2}/12 matched, {c2} teacher calls "
          f"(expect 12/12, 0)")
    wh = LanguageWorld(s2, heldout_bank(), teacher_stub, teacher_disabled=True)
    lh = wh.run()
    strict = sum(1 for e in lh if e["matched"])
    struct = sum(1 for e in lh if e.get("structural_match"))
    print(f"  held-out: strict {strict}/4, structural {struct}/4 "
          f"(expect structural 4/4)")

    print()
    print("HONEST NOTES")
    print("  * Identity + function: Wiktionary POS (wikt_pos_<lang> slabs).")
    print("    Role: grounded grammar (ja が→agent を→patient に→location;")
    print("    en/es spatial preposition → location).")
    print("  * COARSE preposition→location only: the SPATIAL preposition")
    print("    subset maps to location; other prepositions (es personal/dative")
    print("    'a', 'de'; en 'to'/'of') ground as prepositions with NO location")
    print("    role so they don't steal the patient. Fine-grained on/in/with/to")
    print("    → distinct roles is a LATER reference pass (preposition-sense).")
    print("  * zh 在 is grounded but emitted POST-noun in production (idiomatic")
    print("    Mandarin is 在NP上 pre-noun); the frame still round-trips. zh")
    print("    pre-noun ordering is a later production-order refinement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
