"""Autonomous inquiry, migrated to the seed-booted WorldAdapter (no
CuriousAgent).

Covers ALL of tests/test_inquiry.py:
  • ground_unknowns queues an inquire CommunicativeGoal (a graph node) for each
    form the teacher chain can't resolve — and NOT for forms it grounds;
  • the gaps dedupe per form across turns;
  • compose_inquiry surfaces the MOST-RECENT un-asked gap as an ask-meaning Term
    (force=ask, the form on an 'of' slot), one per turn, never re-asked, None
    when nothing is pending — the recency choice is the seeded Argmax, not a
    Python comparison;
  • end-to-end through receive({assert});
  • inquire goals are graph nodes, so they ROUND-TRIP through save/load.

The gaps live as graph data (CommunicativeGoal nodes), not a Python queue; the
meaning is reconstructed from the goal's inquires_about_form attr, so no stored
subgraph is needed for persistence.
"""
from __future__ import annotations

import os
import tempfile

import pytest

from domains.dict_teacher import DictionaryTeacher, is_available
from domains.grammar_teacher import GrammarTeacher
from substrate.world_adapter import WorldAdapter


pytestmark = pytest.mark.skipif(
    not is_available(), reason="NLTK WordNet corpus not installed")


def _agent_with_dict():
    """Adapter with the grammar→dictionary teacher chain — grammar grounds
    function words, the dictionary fallback grounds content words; words neither
    knows (e.g. 'xenobordism') queue as inquire goals."""
    a = WorldAdapter()
    a.set_self_teacher(GrammarTeacher(fallback=DictionaryTeacher()))
    return a


def _inquire_forms(agent) -> list:
    """The forms the agent has open inquire goals for — read from the graph
    (CommunicativeGoal nodes), via the same meaning round-trip the asker uses."""
    out = []
    for gid in agent._inquire_goals():
        form = agent.s.node(gid)["attrs"].get("inquires_about_form")
        m = agent._inquiry_meaning(form)
        f = agent._inquiry_form_from_meaning(m)
        if f:
            out.append(f)
    return out


def _meaning_about(meaning) -> str | None:
    for k, v in meaning.items():
        if k == "force":
            continue
        if isinstance(v, dict) and "of" in v:
            return v["of"]
    return None


# --- inquire goals — graph nodes, not Python state ----------------------

def test_ground_unknowns_creates_inquire_goals_for_unresolved_forms():
    a = _agent_with_dict()
    a.ground_unknowns("entropy is related to xenobordism")
    forms = _inquire_forms(a)
    assert "xenobordism" in forms
    assert "entropy" not in forms


def test_ungrounded_words_dedupe_across_turns():
    a = _agent_with_dict()
    a.ground_unknowns("look at xenobordism")
    a.ground_unknowns("xenobordism again")
    forms = _inquire_forms(a)
    assert forms.count("xenobordism") == 1


# --- compose_inquiry — the agent asks -----------------------------------

def test_compose_inquiry_returns_none_when_nothing_pending():
    a = _agent_with_dict()
    assert a.compose_inquiry() is None


def test_compose_inquiry_returns_meaning_term_for_pending_word():
    a = _agent_with_dict()
    a.ground_unknowns("xenobordism is a thing")
    m = a.compose_inquiry()
    assert m is not None
    assert isinstance(m, dict)
    assert m.get("force") == "ask"
    found = False
    for k, v in m.items():
        if k == "force":
            continue
        if isinstance(v, dict) and v.get("of") == "xenobordism":
            found = True
            break
    assert found, m


def test_compose_inquiry_dequeues_after_asking():
    a = _agent_with_dict()
    a.ground_unknowns("xenobordism is a thing")
    a.compose_inquiry()
    assert a.compose_inquiry() is None


def test_compose_inquiry_does_not_re_ask_same_word():
    a = _agent_with_dict()
    a.ground_unknowns("xenobordism is interesting")
    assert a.compose_inquiry() is not None
    a.ground_unknowns("more about xenobordism")
    assert a.compose_inquiry() is None


def test_compose_inquiry_most_recent_gap_first():
    a = _agent_with_dict()
    a.ground_unknowns("xenobordism arrived")
    a.ground_unknowns("yiblogarithm followed")
    first = a.compose_inquiry()
    assert _meaning_about(first) == "yiblogarithm"
    second = a.compose_inquiry()
    assert _meaning_about(second) == "xenobordism"


# --- end-to-end through receive -----------------------------------------

def test_receive_assert_followed_by_compose_inquiry_yields_a_question():
    a = _agent_with_dict()
    a.receive({"kind": "assert",
               "text": "I learned that xenobordism is hard"})
    m = a.compose_inquiry()
    assert m is not None
    assert _meaning_about(m) == "xenobordism"


def test_inquire_goals_persist_across_save_load():
    a = _agent_with_dict()
    a.ground_unknowns("xenobordism is a thing")
    forms_before = _inquire_forms(a)
    assert "xenobordism" in forms_before

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False) as f:
        path = f.name
    try:
        a.save(path)
        loaded = WorldAdapter.load(path)
        forms_after = _inquire_forms(loaded)
        assert "xenobordism" in forms_after
    finally:
        os.unlink(path)
