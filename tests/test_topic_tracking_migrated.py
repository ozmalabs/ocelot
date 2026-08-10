"""LLM-like conversation: multi-word topics + topic tracking (graph-native).

Three failures fixed, each graph-native (the routing/tracking DECISION is a seed
RULE; the adapter only writes parse facts + renders the minted goal):

  1. MULTI-WORD TOPIC CAPTURE -- "what do you know about the three body problem?"
     routes to the FULL noun phrase "three body problem" (not the head "problem"),
     minting Goal{kind:answer_topic, concept:"three body problem"}. The self-heal
     grounds the WHOLE phrase via domains.topic_grounding.ground_topic.

  2. TOPIC TRACKING + FOLLOW-UP RESOLUTION -- after answering about a topic the
     adapter records it as the conversation's current topic (agent -current_topic->
     CurrentTopic). An ANAPHORIC follow-up ("tell me more about it", "how big is
     it") resolves `it`/`that`/`they` to that tracked topic
     (seeds/conversation_topic_tracking.json::resolve_anaphor_to_current_topic); an
     ELLIPTICAL topic shift ("what about volcanoes?") shifts to the new topic
     (::resolve_elliptical_shift_to_topic).

  3. REGRESSION -- a genuinely self-referential question ("What are you?") and a
     manner self-question ("How do you learn?") mint NO answer_topic goal.

Grounding is monkeypatched (a deterministic offline stand-in for the wiki/web
source) so these tests never touch the network.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# A deterministic, OFFLINE stand-in for domains.topic_grounding.ground_topic: it
# grounds the WHOLE phrase it is handed (memoising under taught_<phrase> exactly
# as the real grounder does), and records every phrase it was asked to ground so
# a test can assert the FULL noun phrase flowed through (never per-word).
_FAKE_ANSWERS = {
    "moon": "the moon is Earth's natural satellite",
    "volcanoes": "a volcano is a rupture in a planet's crust",
    "three body problem": "the three body problem is a physics problem of three "
                          "masses under mutual gravitation",
}


def _install_fake_grounder(monkeypatch):
    seen: list[str] = []
    import domains.topic_grounding as _tg

    def fake_ground_topic(ag, phrase, **kw):
        p = str(phrase)
        seen.append(p)
        ans = _FAKE_ANSWERS.get(p.lower(), f"{p} is a topic")
        return ag.learn_from_teacher(
            p, {"answer": ans, "learn": [{"phrase": p, "answer": ans}]})

    monkeypatch.setattr(_tg, "ground_topic", fake_ground_topic)
    return seen


def _answer_topic_goals(a, concept=None):
    out = []
    for g in a.inner.neighbours(a.agent, "has_goal"):
        if not a.inner.has_node(g):
            continue
        ga = a.s.node(g)["attrs"]
        if ga.get("kind") == "answer_topic" and (concept is None or ga.get("concept") == concept):
            out.append(g)
    return out


def _current_topic(a):
    for n in a.inner.neighbours(a.agent, "current_topic"):
        if a.inner.has_node(n):
            return a.s.node(n)["attrs"].get("name")
    return None


def test_multiword_topic_capture(agent, monkeypatch):
    seen = _install_fake_grounder(monkeypatch)
    reply = agent.converse("What do you know about the three body problem?",
                           speech_act="question")

    # The graph routed to the FULL noun phrase, not the single head "problem".
    assert _answer_topic_goals(agent, "three body problem"), (
        "the reflexive question must route to the FULL noun phrase "
        "(Goal{kind:answer_topic, concept:'three body problem'}), not the head 'problem'")
    assert not _answer_topic_goals(agent, "problem"), "must NOT capture only 'problem'"
    # The whole phrase (not per-word) was handed to the phrase grounder.
    assert "three body problem" in seen, (
        "the FULL phrase must flow to ground_topic, not per-word fragments")
    assert "problem" not in seen, "must not ground the bare word 'problem'"
    # The reply is about the phrase, not a generic dictionary sense of 'problem'.
    assert "three body problem" in reply.lower()


def test_topic_tracking_anaphor_it_resolves_to_current_topic(agent, monkeypatch):
    _install_fake_grounder(monkeypatch)
    agent.converse("What do you know about the moon?", speech_act="question")
    assert _current_topic(agent) == "moon", "answering a topic records it as current"

    reply = agent.converse("Tell me more about it.", speech_act="question")
    # `it` resolved to the tracked topic (the moon), not a self-answer.
    assert _answer_topic_goals(agent, "moon"), (
        "the anaphoric follow-up 'it' must resolve to the tracked topic 'moon' "
        "(mint Goal{kind:answer_topic, concept:'moon'})")
    assert ("moon" in reply.lower() or "satellite" in reply.lower())
    assert "i am jabberwock" not in reply.lower(), "must not misroute to a self-answer"


def test_topic_tracking_how_big_is_it_resolves_to_current_topic(agent, monkeypatch):
    _install_fake_grounder(monkeypatch)
    agent.converse("What do you know about the moon?", speech_act="question")
    reply = agent.converse("How big is it?", speech_act="question")
    assert _answer_topic_goals(agent, "moon"), (
        "'how big is it' -> `it` resolves to the tracked topic 'moon'")
    assert ("moon" in reply.lower() or "satellite" in reply.lower())


def test_elliptical_topic_shift(agent, monkeypatch):
    _install_fake_grounder(monkeypatch)
    agent.converse("What do you know about the moon?", speech_act="question")
    reply = agent.converse("What about volcanoes?", speech_act="question")
    assert _answer_topic_goals(agent, "volcanoes"), (
        "an elliptical topic shift 'what about volcanoes?' must answer about volcanoes")
    assert _current_topic(agent) == "volcanoes", "the current topic shifts to volcanoes"
    assert "volcano" in reply.lower()


def test_self_referential_mints_no_topic_goal(agent, monkeypatch):
    _install_fake_grounder(monkeypatch)
    reply = agent.converse("What are you?", speech_act="question")
    assert not _answer_topic_goals(agent), (
        "a self-referential question has no external topic -> no answer_topic goal")
    assert "couldn't find it through the sources" not in reply.lower()


def test_manner_self_question_mints_no_topic_goal(agent, monkeypatch):
    _install_fake_grounder(monkeypatch)
    agent.converse("How do you learn?", speech_act="question")
    assert not _answer_topic_goals(agent), (
        "a manner self-question has no external object/oblique nominal -> no goal")
