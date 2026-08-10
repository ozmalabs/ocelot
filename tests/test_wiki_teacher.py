"""Wikipedia teacher — lookup-as-teacher tests.

Most tests use a synthetic library (no real parquet dependency) so the
suite stays fast + portable. The end-to-end test against the real on-disk
snapshot is opt-in via WIKI_DATA_DIR env var.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from domains.wiki_library import Article, WikipediaLibrary
from domains.wiki_teacher import (WikiTeacher, article_to_payload,
                                  extract_subject)
from substrate.world_adapter import WorldAdapter


# ---------------------------------------------------------------------------
# subject extraction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,expected", [
    ("what is photosynthesis?", "photosynthesis"),
    ("What is the Eiffel Tower?", "Eiffel Tower"),
    ("tell me about quantum entanglement", "quantum entanglement"),
    ("Who is Ada Lovelace?", "Ada Lovelace"),
    ("define entropy.", "entropy"),
    ("explain the krebs cycle", "krebs cycle"),
    ("photosynthesis", "photosynthesis"),       # bare phrase passes through
    ("how does a transformer work?", "transformer work"),
])
def test_extract_subject(q, expected):
    assert extract_subject(q) == expected


# ---------------------------------------------------------------------------
# synthetic library — a stand-in WikipediaLibrary that holds a fixed corpus
# ---------------------------------------------------------------------------

def _synthetic_library(articles: dict[str, Article]) -> WikipediaLibrary:
    """Return a WikipediaLibrary-compatible duck whose article() returns
    fixed canned data — no parquet, no sqlite required."""
    lib = MagicMock(spec=WikipediaLibrary)

    def lookup(title: str) -> Article | None:
        return articles.get(title.lower())
    lib.article.side_effect = lookup
    return lib


PHOTOSYNTHESIS = Article(
    identifier=22483,
    title="Photosynthesis",
    url="https://en.wikipedia.org/wiki/Photosynthesis",
    abstract=(
        "Photosynthesis is a biological process by which most autotrophs, "
        "including plants and algae, convert light energy into chemical "
        "energy stored in glucose. It takes place in chloroplasts using the "
        "green pigment chlorophyll."),
    description="biochemical process used by plants",
    sections=[],
    links=["Chloroplast", "Chlorophyll", "Calvin cycle", "Light reactions"],
)

EIFFEL = Article(
    identifier=9233,
    title="Eiffel Tower",
    url="https://en.wikipedia.org/wiki/Eiffel_Tower",
    abstract=(
        "The Eiffel Tower is a wrought-iron lattice tower in Paris, France. "
        "Designed by Gustave Eiffel for the 1889 World's Fair, it remained "
        "the tallest man-made structure for 41 years."),
    description="tower in Paris",
    sections=[],
    links=["Paris", "Gustave Eiffel", "1889 World's Fair"],
)


# ---------------------------------------------------------------------------
# article → payload
# ---------------------------------------------------------------------------

def test_article_to_payload_shape():
    p = article_to_payload(PHOTOSYNTHESIS, subject="photosynthesis")
    assert isinstance(p, dict)
    assert "answer" in p and "learn" in p
    assert "biological process" in p["answer"]
    assert isinstance(p["learn"], list) and len(p["learn"]) == 1
    L = p["learn"][0]
    assert L["phrase"] == "photosynthesis"
    assert L["microtheory"] == "wikipedia"
    assert L["binding_pattern"] == "predicate_of_subject"


def test_article_to_payload_includes_related_when_asked():
    p = article_to_payload(PHOTOSYNTHESIS, subject="photosynthesis",
                            include_related=3)
    phrases = [L["phrase"] for L in p["learn"]]
    assert phrases[0] == "photosynthesis"
    assert "chloroplast" in phrases
    assert "chlorophyll" in phrases
    assert len(p["learn"]) == 1 + 3


def test_article_to_payload_long_abstract_truncated():
    long_art = Article(
        identifier=1, title="Long", url="", description="",
        abstract=("A very long abstract. " * 100).strip())
    p = article_to_payload(long_art, subject="long")
    assert p["answer"].endswith("…")
    assert len(p["answer"]) < 400


# ---------------------------------------------------------------------------
# the teacher callable
# ---------------------------------------------------------------------------

def test_teacher_hits_and_returns_payload():
    lib = _synthetic_library({"photosynthesis": PHOTOSYNTHESIS})
    t = WikiTeacher(library=lib)
    payload = t("what is photosynthesis?")
    assert payload is not None
    assert "biological process" in payload["answer"]
    assert t.hits == 1
    assert t.misses == 0
    assert t.last_subject == "photosynthesis"
    assert t.last_title == "Photosynthesis"


def test_teacher_tries_title_case_variant():
    # The agent might ask "what is the eiffel tower" (lowercase); the library
    # honours case-insensitive lookup via title_norm, but variant generation
    # is still the teacher's job for the on-disk path.
    lib = _synthetic_library({"eiffel tower": EIFFEL})
    t = WikiTeacher(library=lib)
    payload = t("What is the Eiffel Tower?")
    assert payload is not None
    assert "Paris" in payload["answer"]


def test_teacher_miss_returns_none():
    lib = _synthetic_library({})           # empty corpus
    t = WikiTeacher(library=lib)
    payload = t("what is xenobordism?")
    assert payload is None
    assert t.misses == 1
    assert t.hits == 0


def test_teacher_falls_through_to_fallback_on_miss():
    lib = _synthetic_library({})
    fallback_called = []

    def fallback(q):
        fallback_called.append(q)
        return {"answer": "fallback answer", "learn": []}

    t = WikiTeacher(library=lib, fallback=fallback)
    payload = t("what is xenobordism?")
    assert payload == {"answer": "fallback answer", "learn": []}
    assert fallback_called == ["what is xenobordism?"]


def test_teacher_does_not_call_fallback_on_hit():
    lib = _synthetic_library({"photosynthesis": PHOTOSYNTHESIS})
    fallback_calls = []
    t = WikiTeacher(library=lib,
                    fallback=lambda q: fallback_calls.append(q))
    payload = t("what is photosynthesis?")
    assert payload is not None
    assert "biological process" in payload["answer"]
    assert fallback_calls == []


# ---------------------------------------------------------------------------
# end-to-end: agent absorbs a wiki teach via the same path as the LLM teacher
# ---------------------------------------------------------------------------

def test_agent_absorbs_wiki_payload_via_learn_from_teacher():
    """The agent's existing learn_from_teacher absorbs wiki payloads — same
    Frame + Sign + Concept install path the LLM teacher uses. The wiki
    teacher is wire-compatible by construction."""
    lib = _synthetic_library({"photosynthesis": PHOTOSYNTHESIS})
    t = WikiTeacher(library=lib)

    a = WorldAdapter()
    payload = t("what is photosynthesis?")
    assert payload is not None
    # Same call site the autonomous self-teacher reflex uses.
    a.learn_from_teacher("what is photosynthesis?", payload)

    # the lexicon now has the phrase
    forms = {s.get("form") for s in a.taught_signs()}
    assert "photosynthesis" in forms
    # and the wikipedia Mt is in scope
    assert "wikipedia" in a.microtheory_names()


def test_agent_uses_wiki_teacher_through_self_teacher_reflex():
    """Wire the wiki teacher in as the agent's self-teacher and verify the
    full autonomous loop (impasse → teacher → absorb) fires. This proves
    wire compatibility with the existing reflex layer."""
    lib = _synthetic_library({"photosynthesis": PHOTOSYNTHESIS,
                              "eiffel tower": EIFFEL})
    teacher = WikiTeacher(library=lib)

    a = WorldAdapter()
    a.set_self_teacher(teacher)

    # Force an impasse — the reasoner does this when it doesn't recognise.
    a.impasse(reason="render_gap", question="what is photosynthesis?")

    # One master tick spawns the teacher thread; drain it.
    a.master_tick()
    a.drain_all_taught_threads(timeout=2.0)

    forms = {s.get("form") for s in a.taught_signs()}
    assert "photosynthesis" in forms
    assert teacher.hits == 1


# ---------------------------------------------------------------------------
# real on-disk parquet path — opt-in
# ---------------------------------------------------------------------------

_REAL_DATA = Path(os.environ.get(
    "WIKI_DATA_DIR", "/home/matt/ozma/data/wikipedia"))
_REAL_AVAILABLE = (_REAL_DATA / "title_index.sqlite").exists()


@pytest.mark.skipif(not _REAL_AVAILABLE,
                    reason="no on-disk wikipedia snapshot (set WIKI_DATA_DIR)")
def test_real_snapshot_lookup_for_a_household_topic():
    """End-to-end against the actual parquet+sqlite. Photosynthesis is a
    safe canonical topic — high-traffic en.wiki article, present in every
    namespace-0 dump."""
    lib = WikipediaLibrary(data_dir=_REAL_DATA)
    try:
        art = lib.article("Photosynthesis")
    except Exception as e:
        pytest.skip(f"index in use: {e}")   # indexer holding the db
    if art is None:
        pytest.skip("Photosynthesis not yet indexed in this snapshot")
    assert art.title.lower() == "photosynthesis"
    assert "light" in art.abstract.lower()  # safe lexical anchor
