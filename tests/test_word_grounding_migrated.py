"""Per-word grounding, migrated to the seed-booted WorldAdapter (no
CuriousAgent).

Covers ALL of tests/test_word_grounding.py:
  • ground_unknowns — per-word lexicon growth via the registered self-teacher
    (the bare word, not a wrapped question; skip short/known tokens; survive a
    per-word teacher failure);
  • receive({assert}) — names what it learned + reports concept-bearing meanings
    (empty for gibberish);
  • the module answer_within(..., agent=wa) grounds unknowns before recognition.

The grounding faculty is graph-native: each word the teacher knows installs its
Microtheory + a lexicon Sign + a taught Concept (learn_from_teacher's `phrase`
branch). The adapter is the per-word I/O loop; the teacher decides the meaning.

`recognise_frame` returns the honest NO-MATCH (None) — the Frame layer is not
migrated, so nothing is recognised and answer_within falls through to per-word
grounding, which is exactly the behaviour this bench exercises. The whole-Frame
recognition itself is the un-migrated reason.py surface, out of scope here.
"""
from __future__ import annotations

import pytest

from domains.dict_teacher import DictionaryTeacher, is_available
from domains.reason import answer_within
from substrate.world_adapter import WorldAdapter


pytestmark = pytest.mark.skipif(
    not is_available(), reason="NLTK WordNet corpus not installed")


# ---------------------------------------------------------------------------
# ground_unknowns — direct call
# ---------------------------------------------------------------------------

def test_ground_unknowns_returns_empty_with_no_teacher():
    a = WorldAdapter()
    learnt = a.ground_unknowns("photosynthesis happens in chloroplasts")
    assert learnt == []        # no _self_teacher set; nothing to ground


def test_ground_unknowns_grows_lexicon_per_word():
    a = WorldAdapter()
    a.set_self_teacher(DictionaryTeacher())
    before = {s.get("form") for s in a.taught_signs()}
    learnt = a.ground_unknowns("photosynthesis happens in chloroplasts")
    after = {s.get("form") for s in a.taught_signs()}
    assert "photosynthesis" in learnt
    assert "chloroplasts" in learnt
    assert "photosynthesis" in after - before


def test_ground_unknowns_skips_already_known_words():
    a = WorldAdapter()
    a.set_self_teacher(DictionaryTeacher())
    a.ground_unknowns("entropy is a thing")
    teacher = a._self_teacher
    teacher.hits = 0
    teacher.misses = 0
    a.ground_unknowns("entropy entropy entropy")
    assert teacher.hits == 0
    assert teacher.misses == 0


def test_ground_unknowns_skips_short_tokens():
    a = WorldAdapter()
    teacher_calls: list = []

    def fake_teacher(form):
        teacher_calls.append(form)
        return None

    a.set_self_teacher(fake_teacher)
    a.ground_unknowns("a x photosynthesis ab")
    assert "photosynthesis" in teacher_calls
    assert "a" not in teacher_calls
    assert "x" not in teacher_calls
    assert "ab" not in teacher_calls


def test_ground_unknowns_passes_form_not_question():
    forms_seen = []

    def teacher(form):
        forms_seen.append(form)
        return None

    a = WorldAdapter()
    a.set_self_teacher(teacher)
    a.ground_unknowns("photosynthesis chloroplast")
    assert "photosynthesis" in forms_seen
    assert "chloroplast" in forms_seen
    assert "photosynthesis chloroplast" not in forms_seen


def test_ground_unknowns_survives_per_word_teacher_failure():
    def teacher(form):
        if form == "broken":
            raise RuntimeError("synthetic teacher failure")
        return None

    a = WorldAdapter()
    a.set_self_teacher(teacher)
    a.ground_unknowns("broken photosynthesis")     # should not raise


# ---------------------------------------------------------------------------
# integration — receive({assert}) names what it learned
# ---------------------------------------------------------------------------

def test_receive_assert_grows_lexicon_and_names_new_words():
    a = WorldAdapter()
    a.set_self_teacher(DictionaryTeacher())
    r = a.receive({"kind": "assert",
                   "text": "photosynthesis happens in chloroplasts"})
    assert "learned" in r
    assert "photosynthesis" in r["learned"]
    assert "meanings" in r
    assert isinstance(r["meanings"], list)


def test_receive_assert_says_nothing_recognised_when_no_grounding():
    a = WorldAdapter()
    a.set_self_teacher(DictionaryTeacher())
    r = a.receive({"kind": "assert", "text": "asdfg"})
    assert r["learned"] == []
    concept_bearing = [m for m in r["meanings"]
                       if isinstance(m, dict) and
                       any(k != "force" for k in m)]
    assert concept_bearing == []


def test_receive_assert_repeated_message_only_learns_once():
    a = WorldAdapter()
    a.set_self_teacher(DictionaryTeacher())
    r1 = a.receive({"kind": "assert", "text": "entropy is interesting"})
    assert "entropy" in r1["learned"]
    r2 = a.receive({"kind": "assert", "text": "entropy is interesting"})
    assert "entropy" not in r2["learned"]


# ---------------------------------------------------------------------------
# integration — answer_within grounds before Frame matching
# ---------------------------------------------------------------------------

def test_answer_within_grounds_unknowns_before_recogniser_runs():
    a = WorldAdapter()
    a.set_self_teacher(DictionaryTeacher())
    before = {s.get("form") for s in a.taught_signs()}
    try:
        answer_within("What is photosynthesis and entropy?",
                       bindings={}, budget_ops=100_000, agent=a)
    except Exception:
        pass
    after = {s.get("form") for s in a.taught_signs()}
    new = after - before
    assert "photosynthesis" in new
    assert "entropy" in new
