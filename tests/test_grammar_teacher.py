"""Grammar teacher — small in-memory dictionary covering function words
wordnet doesn't ship.

Tests verify the lookups + the chain behaviour (grammar handles function
words, falls through to wiki/dict for content), and that the agent
absorbs grammar payloads through the same learn_from_teacher path.
"""
from __future__ import annotations

import pytest

from domains.grammar_teacher import (GrammarTeacher, entry_to_answer,
                                       entry_to_payload, is_function_word,
                                       lookup)
from substrate.world_adapter import WorldAdapter


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("word,expected_category", [
    ("your", "pronoun"),
    ("Your", "pronoun"),
    ("YOUR", "pronoun"),
    ("the", "determiner"),
    ("is", "verb"),
    ("am", "verb"),
    ("and", "conjunction"),
    ("in", "preposition"),
    ("not", "adverb"),
])
def test_lookup_finds_common_function_words(word, expected_category):
    e = lookup(word)
    assert e is not None
    category, definition = e
    assert category == expected_category
    assert len(definition) > 0


def test_lookup_misses_content_words():
    # the grammar teacher shouldn't shadow the dictionary
    assert lookup("photosynthesis") is None
    assert lookup("entropy") is None
    assert lookup("xenobordism") is None


def test_is_function_word_probe():
    assert is_function_word("your") is True
    assert is_function_word("YOUR") is True
    assert is_function_word("photosynthesis") is False


# ---------------------------------------------------------------------------
# entry → payload
# ---------------------------------------------------------------------------

def test_entry_to_answer_human_readable():
    a = entry_to_answer("your", "pronoun",
                         "second-person possessive determiner")
    assert a.startswith("(pronoun)")
    assert "possessive" in a


def test_entry_to_payload_has_learn_phrase():
    p = entry_to_payload("your", "pronoun",
                          "second-person possessive determiner")
    assert "answer" in p
    assert p["learn"][0]["phrase"] == "your"
    assert p["learn"][0]["microtheory"] == "grammar"


# ---------------------------------------------------------------------------
# teacher callable
# ---------------------------------------------------------------------------

def test_teacher_hits_function_word():
    t = GrammarTeacher()
    payload = t("your")
    assert payload is not None
    assert "(pronoun)" in payload["answer"]
    assert t.hits == 1
    assert t.last_category == "pronoun"


def test_teacher_handles_interrogative_wrapping():
    # extract_subject reused — "what is your" → "your"
    t = GrammarTeacher()
    payload = t("what is your?")
    assert payload is not None
    assert "(pronoun)" in payload["answer"]


def test_teacher_misses_content_word_returns_none_without_fallback():
    t = GrammarTeacher()
    assert t("photosynthesis") is None
    assert t.misses == 1


def test_teacher_falls_through_to_fallback_on_miss():
    fallback_calls: list = []

    def fb(q):
        fallback_calls.append(q)
        return {"answer": "from fallback", "learn": []}

    t = GrammarTeacher(fallback=fb)
    p = t("photosynthesis")
    assert p == {"answer": "from fallback", "learn": []}
    assert fallback_calls == ["photosynthesis"]


def test_teacher_does_not_consult_fallback_on_hit():
    fallback_calls: list = []
    t = GrammarTeacher(fallback=lambda q: fallback_calls.append(q))
    t("your")
    assert fallback_calls == []


# ---------------------------------------------------------------------------
# chain — grammar first, then dictionary
# ---------------------------------------------------------------------------

def test_chain_grammar_then_dictionary_picks_grammar_for_function_words():
    from domains.dict_teacher import DictionaryTeacher, is_available
    if not is_available():
        pytest.skip("wordnet not installed")

    dict_t = DictionaryTeacher()
    chain = GrammarTeacher(fallback=dict_t)
    p = chain("your")
    assert p is not None
    assert "pronoun" in p["answer"]
    assert chain.hits == 1
    assert dict_t.hits == 0     # dictionary never consulted


def test_chain_falls_through_to_dictionary_for_content_words():
    from domains.dict_teacher import DictionaryTeacher, is_available
    if not is_available():
        pytest.skip("wordnet not installed")

    dict_t = DictionaryTeacher()
    chain = GrammarTeacher(fallback=dict_t)
    p = chain("entropy")
    assert p is not None
    assert chain.misses == 1
    assert dict_t.hits == 1


# ---------------------------------------------------------------------------
# agent absorbs grammar via the same learn_from_teacher path
# ---------------------------------------------------------------------------

def test_agent_grounds_your_via_grammar_teacher():
    a = WorldAdapter()
    a.set_self_teacher(GrammarTeacher())
    learned = a.ground_unknowns("I am your creator")
    assert "your" in learned
    forms = {s.get("form") for s in a.taught_signs()}
    assert "your" in forms
    assert "grammar" in a.microtheory_names()


def test_function_words_no_longer_queue_as_inquiries_when_chain_grounds_them():
    """The whole point: with grammar in the chain, 'your' grounds and
    doesn't end up in the inquiry queue. The agent doesn't ask the user
    what 'your' means — it just knows."""
    from domains.dict_teacher import DictionaryTeacher, is_available
    if not is_available():
        pytest.skip("wordnet not installed")

    a = WorldAdapter()
    a.set_self_teacher(GrammarTeacher(fallback=DictionaryTeacher()))
    a.ground_unknowns("I am your creator, xenobordism arrives")
    # Inquire goals are graph nodes (CommunicativeGoal); the form each asks
    # about is denormalised onto the goal's inquires_about_form attr.
    forms: list = []
    for gid in a._inquire_goals():
        form = a.s.node(gid)["attrs"].get("inquires_about_form")
        f = a._inquiry_form_from_meaning(a._inquiry_meaning(form))
        if f:
            forms.append(f)
    assert "your" not in forms
    # xenobordism still queues — that's a real gap
    assert "xenobordism" in forms
