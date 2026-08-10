"""Dictionary teacher — cheapest link in the impasse-resolver chain.

WordNet via NLTK. Tests skip cleanly if the corpus isn't installed (CI
without it shouldn't hard-fail), but require it on developer machines.
"""
from __future__ import annotations

import pytest

from domains.dict_teacher import (DictionaryTeacher, Entry, entry_to_answer,
                                  entry_to_payload, is_available, lookup)


pytestmark = pytest.mark.skipif(
    not is_available(), reason="NLTK WordNet corpus not installed")


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

def test_lookup_finds_common_noun():
    e = lookup("photosynthesis")
    assert e is not None
    assert e.pos == "n"
    assert "radiant energy" in e.definition.lower() \
           or "light" in e.definition.lower()


def test_lookup_handles_multiword_via_underscore_keying():
    # WordNet uses 'black_hole'; the teacher hands in 'black hole'.
    e = lookup("black hole")
    assert e is not None
    assert "gravitational" in e.definition.lower() \
           or "matter" in e.definition.lower()


def test_lookup_case_insensitive():
    assert lookup("ENTROPY") is not None
    assert lookup("Entropy") is not None


def test_lookup_miss_returns_none():
    assert lookup("xenobordism") is None
    assert lookup("zzzzzzzz") is None


def test_lookup_prefers_noun_sense_first():
    # 'rock' has both noun and verb senses; the teacher returns noun first.
    e = lookup("rock")
    assert e is not None
    assert e.pos == "n"


def test_lookup_reports_multi_sense_count():
    e = lookup("entropy")
    assert e is not None
    assert e.sense_count >= 2


# ---------------------------------------------------------------------------
# entry → answer / payload
# ---------------------------------------------------------------------------

def test_entry_to_answer_is_human_readable():
    e = lookup("entropy")
    a = entry_to_answer(e)
    assert a.startswith("(noun)")
    assert "+1 other senses" in a or "+2 other senses" in a \
           or "+3 other senses" in a   # plurality of senses
    # readable, not a dump
    assert "<class" not in a


def test_entry_to_payload_has_learn_phrase():
    e = lookup("photosynthesis")
    p = entry_to_payload(e, subject="photosynthesis")
    assert "answer" in p
    assert "(noun)" in p["answer"]
    assert p["learn"][0]["phrase"] == "photosynthesis"
    assert p["learn"][0]["microtheory"] == "dictionary"


# ---------------------------------------------------------------------------
# teacher callable
# ---------------------------------------------------------------------------

def test_teacher_hits_common_word():
    t = DictionaryTeacher()
    payload = t("what is photosynthesis?")
    assert payload is not None
    assert "(noun)" in payload["answer"]
    assert t.hits == 1
    assert t.misses == 0


def test_teacher_strips_interrogative_prefixes():
    t = DictionaryTeacher()
    # extract_subject handles "what is the X" → "X"
    payload = t("What is the entropy?")
    assert payload is not None
    assert "(noun)" in payload["answer"]


def test_teacher_miss_returns_none():
    t = DictionaryTeacher()
    payload = t("what is xenobordism?")
    assert payload is None
    assert t.misses == 1


def test_teacher_falls_through_to_fallback_on_miss():
    fallback_called: list[str] = []

    def fb(q):
        fallback_called.append(q)
        return {"answer": "wiki answer", "learn": []}

    t = DictionaryTeacher(fallback=fb)
    p = t("what is xenobordism?")
    assert p == {"answer": "wiki answer", "learn": []}
    assert fallback_called == ["what is xenobordism?"]


def test_teacher_does_not_call_fallback_on_hit():
    fallback_calls: list[str] = []
    t = DictionaryTeacher(fallback=lambda q: fallback_calls.append(q))
    p = t("what is entropy?")
    assert p is not None
    assert fallback_calls == []


def test_chain_dict_then_wiki_visits_dict_first():
    """The chain pattern: dict first (cheap), wiki only on miss."""
    from tests.test_wiki_teacher import (PHOTOSYNTHESIS, _synthetic_library)
    from domains.wiki_teacher import WikiTeacher

    wiki = WikiTeacher(library=_synthetic_library(
        {"photosynthesis": PHOTOSYNTHESIS}))
    chain = DictionaryTeacher(fallback=wiki)

    p = chain("what is photosynthesis?")
    assert p is not None
    assert chain.hits == 1
    assert wiki.hits == 0      # dict answered, wiki never consulted


def test_chain_falls_through_to_wiki_on_dict_miss():
    """A modern proper noun WordNet doesn't ship with (built 1985–2006);
    wiki has it. The chain should consult dict, miss, fall through to
    wiki, hit."""
    from domains.wiki_library import Article
    from tests.test_wiki_teacher import _synthetic_library
    from domains.wiki_teacher import WikiTeacher

    ZIG = Article(
        identifier=1, title="Zig (programming language)",
        url="https://en.wikipedia.org/wiki/Zig_(programming_language)",
        description="systems programming language",
        abstract=("Zig is an imperative, general-purpose, statically typed, "
                  "compiled systems programming language designed by Andrew "
                  "Kelley. It is intended for maintaining and improving on "
                  "existing C and C++ codebases."),
        sections=[], links=[])
    wiki = WikiTeacher(library=_synthetic_library(
        {"zig (programming language)": ZIG, "zig": ZIG}))
    chain = DictionaryTeacher(fallback=wiki)

    # 'zig' as a verb is in wordnet ('move with sharp angular movements')…
    # so we use a phrasing that puts the full name as subject.
    p = chain("Zig (programming language)")
    assert p is not None
    assert "Andrew Kelley" in p["answer"] or "compiled" in p["answer"]
    assert chain.misses == 1
    assert wiki.hits == 1


# ---------------------------------------------------------------------------
# agent absorbs the payload — migrated to the seed-booted WorldAdapter in
# tests/test_dict_teacher_migrated.py (this file keeps only the pure
# DictionaryTeacher class tests, which the teacher class itself owns).
# ---------------------------------------------------------------------------
