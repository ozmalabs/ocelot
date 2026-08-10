"""test_first_person_routing_migrated -- BLIND-SPOT CLOSURE R6 (bare
first-person routing, "Who am I?" / "What do I want?").

Today `domains/comprehend_text.py`'s reflexive gate (`_has_self_cue`) only
recognises SECOND-person self-cues ("you"/"your"/"yourself"/"yours"/"me"); a
bare first-person subject question has none, so `comp.reflexive` stays False
and the turn falls through to the non-reflexive "know" dispatch, which treats
the composed relation's topic nominal ("I") as an external WORLD CONCEPT to
look up -- "I don't hold that." The interlocutor_model reflective reader
already answers this shape ("You are <name>." / the tracked wants list) but
was unreachable from a bare first-person question.

THE CLOSURE (seeds/first_person_routing.json::
route_first_person_question_to_interlocutor): the graph's OWN existing
first-person resolution (seeds/intent.json::rule_first_person_resolves_to_
speaker -- every Mention with text in {i,me,my,mine} already resolves,
refers_to, the turn's Intent.speaker for EVERY message) is joined against the
"know" dispatch's own echoed concept (world_adapter's comp_know_concept,
a mechanical echo of comp.dispatch["concept"], not a new decision). When a
Mention's text equals that echoed concept AND the SAME mention resolves to
the turn's own speaker, the turn IS about the speaker -- Goal{kind:
answer_interlocutor_meta} is minted and world_adapter._answer_interlocutor_
meta_reply renders it via the SAME reflect()/_surface_self_state backend
every other meta reader uses. No Python pronoun list, no comprehend_text.py
edit.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    return a


def _has_rule(a, name):
    return any(r.get("name") == name for r in a.inner.export_rules())


# --------------------------------------------------------------------------- #
#  THE CLOSURE: a bare first-person question answers from the PARTY model.
# --------------------------------------------------------------------------- #
def test_bare_first_person_identity_question_answers_from_party(agent):
    a = agent
    assert _has_rule(a, "route_first_person_question_to_interlocutor")
    a.converse("Hi, I am Uma.", speech_act="statement")
    a.converse("I want to learn about volcanoes.", speech_act="statement")
    reply = a.converse("Who am I?", speech_act="question")
    assert "uma" in reply.lower(), reply
    assert "i don't hold that" not in reply.lower(), reply
    mid = a._last_turn_inbound
    at = a.s.node(mid)["attrs"]
    assert at.get("comp_dispatch_path") == "know", at
    assert at.get("comp_know_concept") == "i", at


def test_bare_first_person_want_question_answers_from_party(agent):
    a = agent
    a.converse("Hi, I am Uma.", speech_act="statement")
    a.converse("I want to learn about volcanoes.", speech_act="statement")
    reply = a.converse("What do I want?", speech_act="question")
    assert "volcano" in reply.lower(), reply
    assert "i don't hold that" not in reply.lower(), reply


def test_bare_first_person_question_mints_exactly_one_goal(agent):
    a = agent
    a.converse("Hi, I am Uma.", speech_act="statement")
    reply = a.converse("Who am I?", speech_act="question")
    mid = a._last_turn_inbound
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_interlocutor_meta"
             and mid in list(a.inner.neighbours(g, "comprehends"))]
    assert len(goals) == 1, goals
    # the goal fulfiller's answer is what converse() actually returned (the
    # SAME "benign redundant floor Message, correctly out-precedenced"
    # pattern the pre-existing answer_topic path already exhibits -- see
    # world_adapter.converse's read-off precedence docstring; a spurious
    # honest-floor Message may also be minted in the same fixpoint pass, but
    # it is never what the turn returns).
    assert "uma" in reply.lower(), reply


def test_unknown_party_bare_first_person_is_honest_not_a_world_lookup(agent):
    """No self-identification yet -- the reader's own honest "not known"
    branch answers, never the old "I don't hold that" world-concept miss."""
    a = agent
    reply = a.converse("Who am I?", speech_act="question")
    assert "i don't hold that" not in reply.lower(), reply


# --------------------------------------------------------------------------- #
#  PARITY: every existing self/meta/topic route stays byte-unchanged.
# --------------------------------------------------------------------------- #
def test_agent_directed_identity_question_unchanged(agent):
    a = agent
    reply = a.converse("Who are you?", speech_act="question")
    assert "jabberwock" in reply.lower(), reply
    mid = a._last_turn_inbound
    at = a.s.node(mid)["attrs"]
    assert at.get("comp_dispatch_path") != "know", at
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_interlocutor_meta"]
    assert goals == []


def test_agent_directed_what_are_you_unchanged(agent):
    a = agent
    reply = a.converse("What are you?", speech_act="question")
    assert "jabberwock" in reply.lower(), reply


def test_existing_meta_lexicon_interlocutor_route_unaffected(agent):
    """"What do you know about me?" already reaches interlocutor_model via
    the OLD table/keyword meta route (it contains "me", a second-person
    self-cue) -- must stay on that path (fastpath/meta), never additionally
    (or instead) claimed by the new "know"-path rule."""
    a = agent
    a.converse("Hi, I am Uma.", speech_act="statement")
    reply = a.converse("What do you know about me?", speech_act="question")
    assert "uma" in reply.lower(), reply
    mid = a._last_turn_inbound
    at = a.s.node(mid)["attrs"]
    assert at.get("comp_dispatch_path") != "know", at
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_interlocutor_meta"]
    assert goals == [], "the old meta-lexicon route already claimed this turn"


def test_external_know_question_unaffected(agent):
    a = agent
    reply = a.converse("What is an airplane?", speech_act="question")
    mid = a._last_turn_inbound
    at = a.s.node(mid)["attrs"]
    # whatever the front end resolved, it must not be hijacked to the
    # interlocutor reader: no first-person mention resolves to "airplane".
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_interlocutor_meta"]
    assert goals == [], (reply, at)


def test_first_person_statement_kind_unaffected(agent):
    """A first-person STATEMENT (not a question) never matches comp_kind==
    'question', so the new rule cannot fire on it -- byte-unchanged."""
    a = agent
    a.converse("I like volcanoes.", speech_act="statement")
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_interlocutor_meta"]
    assert goals == []


# --------------------------------------------------------------------------- #
#  CLOSURE PROOF (agent-in-control): the routing decision is graph data --
#  ablating the rule reverts to the OLD (broken) behaviour, proving the
#  decision genuinely lives in the graph, not in comprehend_text.py.
# --------------------------------------------------------------------------- #
def test_ablating_the_rule_reverts_to_the_old_misroute(agent):
    a = agent
    a.converse("Hi, I am Uma.", speech_act="statement")
    idx = None
    for i, r in enumerate(a.inner.export_rules()):
        if isinstance(r, dict) and r.get("active", True) and \
                r.get("name") == "route_first_person_question_to_interlocutor":
            idx = i
            break
    assert idx is not None, "the routing decision must be a live, named, removable rule"
    assert a.inner.remove_rule(idx) is True

    reply = a.converse("Who am I?", speech_act="question")
    # with the rule gone, the turn falls back through to the OLD
    # (pre-closure) "know" dispatch honest floor -- proving the fix's
    # decision genuinely lived in the ablated rule, not in Python.
    assert "uma" not in reply.lower(), (
        "ablating the rule must revert the routing, not just weaken it", reply)
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_interlocutor_meta"]
    assert goals == []
