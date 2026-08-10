"""Measure the WordNet dictionary-fill layer on LanguageWorld.

Boots a LanguageWorld with the dictionary layer active and the LLM
teacher DISABLED, then parses held-out sentences that received NO prior
training. The headline checks:

  * Common nouns / verbs resolve mechanically from WordNet to canonical
    English concepts — no teacher, no context-guess.
  * Cross-lingual NOUNS map to the SAME English concept (perro→dog,
    pelota→ball, 犬→dog, ボール→ball) with no LLM.
  * The honest gaps surface in the per-word source column: inflected
    non-English verbs (persiguió, 追了, 追いかけた) that don't lemmatize
    fall through to context / unresolved, and WordNet sense-1 drift
    (zh 追→pursue) shows up as the resolved concept.

Per CLAUDE.md this is a thin runner.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import (
    LanguageWorld,
    teacher_stub,
    _detect_language,
    _frame_equal,
    _LATIN_FUNCTION_WORDS,
    _CJK_PARTICLES,
)


def heldout_bank() -> list[dict]:
    """Held-out sentences, NO prior training (teacher disabled)."""
    return [
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
    ]


def content_tokens(text: str, language: str,
                   lex: dict[str, str]) -> list[str]:
    """Content tokens for per-word reporting. For CJK we greedy-match
    against the GROUNDED lexicon surfaces first (so multi-char words like
    ボール / 追いかけた report as one unit, not char-by-char), then emit
    leftover single chars; particles are dropped."""
    if language in ("zh", "ja"):
        surfaces = sorted(lex.keys(), key=len, reverse=True)
        particles = _CJK_PARTICLES.get(language, set())
        out: list[str] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch.isspace() or (0x3000 <= ord(ch) <= 0x303F) \
                    or ch in ("。", "？", "、"):
                i += 1
                continue
            matched = False
            for surf in surfaces:
                if text.startswith(surf, i):
                    out.append(surf)
                    i += len(surf)
                    matched = True
                    break
            if matched:
                continue
            if ch not in particles:
                out.append(ch)
            i += 1
        return out
    toks = [t.lower() for t in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+", text)]
    fw = _LATIN_FUNCTION_WORDS.get(language, set())
    return [t for t in toks if t not in fw]


def lex_source(world: LanguageWorld, language: str, surface: str) -> str:
    """Read back the grounded LexEntry's source for a surface, if any."""
    lex_attrs = None
    for eid in world.s.nodes("LexEntry"):
        a = world.s.node(eid)["attrs"]
        if a.get("language") == language and a.get("surface") == surface:
            lex_attrs = a
    if lex_attrs is None:
        return "-"
    return lex_attrs.get("source", "?")


def main() -> int:
    print("=" * 72)
    print("WordNet dictionary-fill — held-out, teacher DISABLED, NO training")
    print("=" * 72)

    held = heldout_bank()
    s = _native.Substrate()
    # Cold substrate, teacher disabled — the dictionary is the only
    # vocabulary source (plus context-typing for what it misses).
    world = LanguageWorld(s, held, teacher_stub, teacher_disabled=True)
    log = world.run()
    summ = LanguageWorld.summary(log)

    strict_after = 0
    for e in log:
        lang = e["language"]
        print()
        print("-" * 72)
        print(f"[{lang}] {e['text']}")
        print(f"  expected = {e['expected']}")
        print(f"  frame    = {e['frame']}")
        # Per-word resolution.
        resolved_map = {surf: cand for (_p, surf, cand, _w) in e["inferred"]}
        lex_cache = world._lexicon_cache.get(lang, {})
        for tok in content_tokens(e["text"], lang, lex_cache):
            concept = lex_cache.get(tok) or resolved_map.get(tok)
            if concept is None:
                print(f"    {tok!r:>14} → UNRESOLVED")
                continue
            src = lex_source(world, lang, tok)
            cat = None
            for cid in world.s.nodes("Concept"):
                ca = world.s.node(cid)["attrs"]
                if ca.get("name") == concept:
                    cat = ca.get("category")
                    break
            print(f"    {tok!r:>14} → {concept:<12} "
                  f"cat={cat}  source={src}")
        ok = _frame_equal(e["frame"], e["expected"])
        if ok:
            strict_after += 1
        print(f"  STRICT match: {'YES' if ok else 'no'}")

    print()
    print("=" * 72)
    print("Summary")
    print("=" * 72)
    print(f"  held-out strict BEFORE (en only, no dictionary): 1/4")
    print(f"  held-out strict AFTER  (WordNet dictionary):     "
          f"{strict_after}/4")
    print(f"  structural matched: {summ['structural_matched']}/4")
    print(f"  teacher calls:      {summ['teacher_calls']} (teacher disabled)")
    print(f"  per-language strict: {summ['per_language_matched']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
