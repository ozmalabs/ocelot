"""Self-integration — the agent grows its OWN capability.
(Migrated from test_self_integration.py — CuriousAgent replaced by WorldAdapter.)

A teacher supplies a definition of a new word in the vocabulary the agent
already grounds (here a fixed spec; the live demo uses a spawned-Agent teacher).
The agent ingests it into a DSL Term, grounds the concept + sign, and then
comprehends and answers questions using it. The point: a new concept costs ZERO
concept-specific code — the meaning is the teacher's, the grounding/use the
agent's. This is "the entity grows itself", not "Claude adds a capability".
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def test_agent_self_grounds_and_uses_a_taught_concept():
    a = WorldAdapter()
    # 'trip' := value mod 3 == 0  — supplied by a teacher, grounded by the agent
    a.ground_from_spec("trip", ["Eq", ["Mod", "value", 3], 0])
    assert a.evaluate_word("trip", 12) is True
    assert a.evaluate_word("trip", 7) is False
    # the agent comprehends a question and answers with its own grounded meaning
    assert a.answer_predicate("is 12 trip?") is True
    assert a.answer_predicate("is 7 trip?") is False


def test_a_second_concept_is_also_zero_code():
    a = WorldAdapter()
    a.ground_from_spec("biggish", ["Gt", "value", 100])      # value > 100
    assert a.answer_predicate("is 250 biggish?") is True
    assert a.answer_predicate("is 5 biggish?") is False


def test_agent_asks_for_unknown_words_and_grounds_them():
    # the agent DRIVES its own learning: it sees what it doesn't know and asks
    teacher_defs = {"septal": ["Eq", ["Mod", "value", 7], 0]}     # multiple of 7

    def teacher(form):
        return teacher_defs.get(form)

    a = WorldAdapter()
    assert "septal" in a.discover_unknown_words("is 14 septal?")
    # one call: discover→ask→ground→answer
    assert a.answer_predicate("is 14 septal?", teacher=teacher) is True
    assert a.answer_predicate("is 15 septal?", teacher=teacher) is False
    # the concept stays grounded; no further asking needed
    assert a.answer_predicate("is 49 septal?") is True
    assert a.discover_unknown_words("is 49 septal?") == []        # now known


def test_grounded_meaning_is_graph_resident():
    # the new capability lives in the mind-graph as a Concept Term-tree the agent
    # can introspect — not in Python
    a = WorldAdapter()
    a.ground_from_spec("trip", ["Eq", ["Mod", "value", 3], 0])
    assert a.word_meaning("trip") is not None                # an evaluable Term
