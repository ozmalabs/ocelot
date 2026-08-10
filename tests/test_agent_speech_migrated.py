"""Speaking as goal-directed action, migrated to the seed-booted WorldAdapter
(no CuriousAgent).

A communicative `inform` goal drives an utterance: the agent speaks to advance
an unmet goal (rendering the meaning via the lexicon + the predicate-argument
render), models the addressee's uptake (their believed_concepts grow), conveys
only the new content, and falls silent once every goal is met. No addressee ->
silent, so the autopoietic loop is unchanged. Speaking competes in the unified
action choice (`_UTTER`) and a freshly taught word is immediately usable +
evaluable. Covers tests/test_agent_speech.py.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _agent_with_addressee():
    a = WorldAdapter()
    other = a.s.add_node("Agent", {"id": "other", "believed_concepts": frozenset()})
    a.set_addressee(other)
    return a, other


def _believed(a, other):
    return set(a.s.node(other)["attrs"].get("believed_concepts") or [])


def _no_preview_world():
    g = TypedGraph()
    g._insert_node("Thing", {})
    sub = Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))
    return sub, [("use",), ("attack",)]


# --- speak to satisfy, then fall silent ---------------------------------

def test_speaks_to_satisfy_then_falls_silent():
    a, other = _agent_with_addressee()
    a.add_communicative_goal("gravity")
    assert a._communicative_action() == ["gravity"]
    assert "gravity" in _believed(a, other)
    assert a._communicative_action() is None


def test_conveys_only_the_new():
    a, other = _agent_with_addressee()
    a.inner.set_attr(other, "believed_concepts", frozenset({"math"}))
    a.add_communicative_goal("math")              # already known
    a.add_communicative_goal("logic")             # unmet
    assert a._communicative_action() == ["logic"]


def test_no_addressee_is_silent():
    a = WorldAdapter()
    a.add_communicative_goal("gravity")
    assert a._communicative_action() is None


# --- competes in the unified action choice ------------------------------

def test_utterance_competes_in_the_unified_argmax():
    a, _ = _agent_with_addressee()
    a.add_communicative_goal("gravity")
    sub, actions = _no_preview_world()
    a.observe(sub)
    assert a.choose_action_or_utter(actions, lambda _x: sub) is a._UTTER


def test_world_action_chosen_when_nothing_to_say():
    a, _ = _agent_with_addressee()
    sub, actions = _no_preview_world()
    a.observe(sub)
    assert a.choose_action_or_utter(actions, lambda _x: sub) in actions


# --- structured meanings via the sign lexicon ---------------------------

def test_renders_structured_meaning_via_sign_lexicon():
    a, other = _agent_with_addressee()
    a.learn_sign("determinant", "det")
    a.add_communicative_goal({"det": {"of": "M"}})
    assert a._communicative_action() == ["determinant of M"]
    assert {"det", "M"} <= _believed(a, other)
    assert a._communicative_action() is None


def test_agent_learns_a_sign_then_speaks_with_it():
    a, _ = _agent_with_addressee()
    a.learn_sign("kernel", "kernel")
    a.add_communicative_goal({"kernel": {"of": "M"}})
    assert a._communicative_action() == ["kernel of M"]


# --- lexicon is graph-resident + lazy -----------------------------------

def test_lexicon_is_graph_resident_and_lazy():
    a = WorldAdapter()
    assert not [n for n in a.s.nodes("Sign")]      # none until needed
    a.learn_sign("widget", "widget")
    assert [n for n in a.s.nodes("Sign")]          # now in the graph


# --- teach + ground a word to an evaluable meaning ----------------------

def test_teach_and_ground_links_sign_to_evaluable_meaning():
    a, _ = _agent_with_addressee()
    assert a.word_meaning("even") is None
    a.ground_from_spec("even", ["Eq", ["Mod", "value", 2], 0], domain="number")
    assert a.word_meaning("even") is not None       # now denotes a grounded meaning
    assert a.evaluate_word("even", 4) is True
    assert a.evaluate_word("even", 3) is False
