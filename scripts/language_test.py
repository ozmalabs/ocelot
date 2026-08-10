"""Drive the LanguageWorld over a 12-sentence multi-language bank
(English / Spanish / Mandarin / Japanese × 3) twice — show the
second pass costs ~0 teacher calls because the substrate has
grounded a (Grammar, Lexicon) per language. Then run a held-out
pass of 4 NEW sentences in the same languages with the teacher
DISABLED, to verify the substrate parses them from grounded
knowledge alone.

The point: language is treated as a CLASS — the same machinery
identifies the language, looks up its grammar/lexicon, parses,
and produces a language-independent semantic frame. English is
not privileged; it sits inside the same multi-language framework.

Per CLAUDE.md this is a thin runner. It instantiates the native
substrate, hands the world the task bank + a teacher, and prints
the deltas.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import (
    LanguageWorld,
    teacher_stub,
    teacher_via_claude,
)


def training_bank() -> list[dict]:
    """3 sentences per language × 4 languages = 12 training tasks.

    The four languages exercise different writing systems and
    word-order families:
      en: SVO,  Latin script
      es: SVO,  Latin + diacritics
      zh: SVO,  Han ideographs, no tense morphology
      ja: SOV,  Han + kana, particles + aspectual -た

    Same-meaning sentences across languages share their
    expected_meaning dict (modulo tense for zh, which doesn't mark
    it morphologically)."""
    return [
        # English
        {"text": "The cat sat on the mat.", "language": "en",
         "expected_meaning": {"event": "sit", "agent": "cat",
                              "location": "mat", "tense": "past"}},
        {"text": "Mary loves John.", "language": "en",
         "expected_meaning": {"event": "love", "agent": "Mary",
                              "patient": "John", "tense": "present"}},
        {"text": "Who broke the vase?", "language": "en",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                              "patient": "vase", "tense": "past",
                              "speech_act": "question"}},
        # Spanish
        {"text": "El gato se sentó en la alfombra.", "language": "es",
         "expected_meaning": {"event": "sit", "agent": "cat",
                              "location": "mat", "tense": "past"}},
        {"text": "María ama a Juan.", "language": "es",
         "expected_meaning": {"event": "love", "agent": "Mary",
                              "patient": "John", "tense": "present"}},
        {"text": "¿Quién rompió el jarrón?", "language": "es",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                              "patient": "vase", "tense": "past",
                              "speech_act": "question"}},
        # Mandarin (tense not marked morphologically; expected dict
        # omits tense for zh.)
        {"text": "猫坐在垫子上。", "language": "zh",
         "expected_meaning": {"event": "sit", "agent": "cat",
                              "location": "mat"}},
        {"text": "玛丽爱约翰。", "language": "zh",
         "expected_meaning": {"event": "love", "agent": "Mary",
                              "patient": "John"}},
        {"text": "谁打破了花瓶？", "language": "zh",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                              "patient": "vase",
                              "speech_act": "question"}},
        # Japanese (SOV)
        {"text": "猫がマットの上に座った。", "language": "ja",
         "expected_meaning": {"event": "sit", "agent": "cat",
                              "location": "mat", "tense": "past"}},
        {"text": "メアリーはジョンを愛している。", "language": "ja",
         "expected_meaning": {"event": "love", "agent": "Mary",
                              "patient": "John", "tense": "present"}},
        {"text": "誰が花瓶を割った？", "language": "ja",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                              "patient": "vase", "tense": "past",
                              "speech_act": "question"}},
    ]


def heldout_bank() -> list[dict]:
    """4 NEW sentences in the four known languages — same event/agent/
    patient structure, novel content (dog chases ball). Teacher is
    disabled for this pass; the substrate parses from its grounded
    grammar+lexicon alone. Cross-language semantic equivalence is the
    headline check: all four produce the same frame (modulo zh tense)."""
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


def short_text(t: str, n: int = 40) -> str:
    if len(t) <= n:
        return t
    return t[:n - 3] + "..."


def select_teacher(name: str):
    if name == "claude":
        return teacher_via_claude
    return teacher_stub


def main(argv: list[str]) -> int:
    teacher_name = "stub"
    for arg in argv[1:]:
        if arg in ("--claude", "claude"):
            teacher_name = "claude"
        elif arg in ("--stub", "stub"):
            teacher_name = "stub"
    teacher = select_teacher(teacher_name)
    print(f"teacher = {teacher_name}")
    print()

    s = _native.Substrate()
    training = training_bank()
    held = heldout_bank()

    world = LanguageWorld(s, training, teacher)
    print("=" * 72)
    print("Pass 1 (training) — substrate cold, every language asks the teacher")
    print("=" * 72)
    log1 = world.run()
    summ1 = LanguageWorld.summary(log1)
    print(f"Tasks: {summ1['tasks']}  Matched: {summ1['matched']}  "
          f"Teacher calls: {summ1['teacher_calls']}")
    print(f"Per-language teacher calls: {summ1['per_language_calls']}")
    print(f"Per-language matched:       {summ1['per_language_matched']}")
    print()

    print(f"Language nodes:       {len(s.nodes('Language'))}")
    print(f"Grammar nodes:        {len(s.nodes('Grammar'))}")
    print(f"Lexicon nodes:        {len(s.nodes('Lexicon'))}")
    print(f"LexEntry nodes:       {len(s.nodes('LexEntry'))}")
    print(f"Production nodes:     {len(s.nodes('Production'))}")
    print(f"SemanticFrame nodes:  {len(s.nodes('SemanticFrame'))}")
    print(f"Concept nodes:        {len(s.nodes('Concept'))}")
    print()

    print("Per-task (pass 1):")
    for i, e in enumerate(log1, 1):
        ok = "OK " if e["matched"] else "MIS"
        cov = e["lexicon_coverage"]
        print(f"  {i:2}. [{ok}] {e['language']} teach={e['teacher_calls']} "
              f"cov={cov[0]}/{cov[1]}  '{short_text(e['text'], 30)}'")
        print(f"        → {e['frame']}")

    print()
    print("=" * 72)
    print("Pass 2 (re-training) — same sentences, grammar/lexicon grounded")
    print("=" * 72)
    log2 = world.run()
    summ2 = LanguageWorld.summary(log2)
    print(f"Tasks: {summ2['tasks']}  Matched: {summ2['matched']}  "
          f"Teacher calls: {summ2['teacher_calls']}")
    print(f"Per-language teacher calls: {summ2['per_language_calls']}")
    print()

    print("Cumulative learning:")
    print(f"  pass 1 teacher calls: {summ1['teacher_calls']}")
    print(f"  pass 2 teacher calls: {summ2['teacher_calls']}")
    if summ1["teacher_calls"]:
        reduction_pct = (1 - summ2["teacher_calls"]
                         / max(1, summ1["teacher_calls"])) * 100
        print(f"  reduction:            "
              f"{summ1['teacher_calls'] - summ2['teacher_calls']} "
              f"({reduction_pct:.0f}%)")
    print()

    print("=" * 72)
    print("Pass 3 (held-out, TEACHER DISABLED) — NEW sentences, known languages")
    print("=" * 72)
    world_ho = LanguageWorld(s, held, teacher, teacher_disabled=True)
    log3 = world_ho.run()
    summ3 = LanguageWorld.summary(log3)
    print(f"Tasks: {summ3['tasks']}  Strict-matched: {summ3['matched']}  "
          f"Structural-matched: {summ3['structural_matched']}  "
          f"Teacher calls: {summ3['teacher_calls']}")
    print(f"Per-language strict:     {summ3['per_language_matched']}")
    print(f"Per-language structural: {summ3['per_language_structural']}")
    print()
    for i, e in enumerate(log3, 1):
        strict = "S+" if e["matched"] else "S-"
        struct = "T+" if e.get("structural_match") else "T-"
        cov = e["lexicon_coverage"]
        print(f"  {i:2}. [{strict}{struct}] {e['language']} cov={cov[0]}/{cov[1]} "
              f" '{short_text(e['text'], 32)}'")
        print(f"        expected={e['expected']}")
        print(f"        frame   ={e['frame']}")
        if e.get("inferred"):
            inf = ", ".join(
                f"{surf}→{cand} (w={w:.2f})"
                for _, surf, cand, w in e["inferred"]
            )
            print(f"        inferred={inf}")

    print()
    print("=" * 72)
    print("Cross-language semantic equivalence")
    print("=" * 72)
    print("Same-meaning sentences across en/es/zh/ja should produce the SAME frame:")
    by_meaning: dict[str, list[dict]] = {}
    for e in log1:
        key = (e["expected"].get("event", "?"),
               e["expected"].get("agent", "?"),
               e["expected"].get("patient") or e["expected"].get("location", "-"))
        by_meaning.setdefault(repr(key), []).append(e)
    for key, group in by_meaning.items():
        if len(group) < 2:
            continue
        print(f"\n  Concept {key}:")
        for e in group:
            print(f"    [{e['language']}] '{short_text(e['text'], 38)}'")
            print(f"        → {e['frame']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
