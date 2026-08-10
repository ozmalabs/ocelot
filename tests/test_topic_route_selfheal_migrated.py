"""The 'moon bug' fix + self-healing knowledge gaps (graph-native).

Before: "What do you know about the moon?" -> "I am Jabberwock." The Python
front end (comprehend_text) sees the self-cue 'you' and routes the WHOLE turn
to a self/meta faculty, discarding the real topic.

After: the adapter writes the external object/oblique nominal onto the Message
(comp_topic + topic_pending marker -- NEVER the self-word subject), and the
graph rule route_question_to_topic (seeds/conversation_topic_route.json) DECIDES
the turn is about that external topic and mints Goal{kind:answer_topic}. The
adapter renders the answer from that decision via answer_about, and SELF-HEALS a
miss by grounding the topic through the agent's OWN self-teacher chain
(ground_unknowns) and re-answering -- the agent fixing its own knowledge gap.

A genuinely self-referential question ("What are you?") writes no comp_topic, so
the rule never fires and the self/meta path is byte-unchanged.
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


def _answer_topic_goals(a, concept=None):
    out = []
    for g in a.inner.neighbours(a.agent, "has_goal"):
        if not a.inner.has_node(g):
            continue
        ga = a.s.node(g)["attrs"]
        if ga.get("kind") == "answer_topic" and (concept is None or ga.get("concept") == concept):
            out.append(g)
    return out


def test_reflexive_topic_question_routes_to_topic_not_self(agent):
    # No teacher attached -> the topic can't be grounded, but the ROUTING must
    # still be fixed: the turn is about 'moon', not the agent's identity.
    reply = agent.converse("What do you know about the moon?", speech_act="question")
    assert _answer_topic_goals(agent, "moon"), (
        "the graph must route the reflexive question to its external topic "
        "(mint Goal{kind:answer_topic, concept:'moon'}), not to a self faculty")
    assert "moon" in reply.lower(), "the honest reply must be ABOUT the topic"
    assert "i am jabberwock" not in reply.lower(), "the self-identity misroute must be gone"


def test_self_heals_knowledge_gap_via_teacher(agent, monkeypatch):
    # The self-heal now flows through domains.topic_grounding.ground_topic (PHRASE
    # grounding: local Wikipedia library, then web) -- the per-word ground_unknowns
    # teacher chain is only the FALLBACK when that module is absent. Monkeypatch the
    # phrase grounder so the heal is deterministic and offline (it stands in for the
    # dictionary/wiki source), and assert the agent CONSULTS it on a miss and then
    # holds the answer.
    calls = {"n": 0}
    import domains.topic_grounding as _tg

    def fake_ground_topic(ag, phrase, **kw):
        calls["n"] += 1
        assert str(phrase).lower() == "moon"
        ans = "the moon is Earth's natural satellite"
        return ag.learn_from_teacher(
            phrase, {"answer": ans, "learn": [{"phrase": phrase, "answer": ans}]})

    monkeypatch.setattr(_tg, "ground_topic", fake_ground_topic)
    reply = agent.converse("What do you know about the moon?", speech_act="question")

    assert _answer_topic_goals(agent, "moon"), "routed to the topic"
    assert "natural satellite" in reply.lower(), (
        "on a miss the agent must GROUND the topic through its own phrase grounder "
        "and re-answer -- fixing its own knowledge gap")
    assert calls["n"] >= 1, "the phrase grounder (ground_topic) must have been consulted"
    # It actually LEARNED the concept (memoised, answerable without re-grounding).
    assert "taught_moon" in agent.taught_capabilities(), "the grounding must persist"


def test_genuinely_self_referential_question_is_unchanged(agent):
    reply = agent.converse("What are you?", speech_act="question")
    assert not _answer_topic_goals(agent), (
        "a self-referential question has no external topic -> route rule must NOT "
        "fire (topic_pending stays absent)")
    # The self path answered it -- not the topic-gap floor.
    assert "couldn't find it through the sources" not in reply.lower()


def test_no_external_topic_when_subject_is_self_word(agent):
    # 'how do you learn' -- reflexive, but no object/oblique topic -> no routing.
    agent.converse("How do you learn?", speech_act="question")
    assert not _answer_topic_goals(agent), (
        "a manner self-question has no external object/oblique nominal, so no "
        "answer_topic goal is minted")


def test_possessive_self_topic_is_not_grounded_externally(agent):
    # "how does YOUR collapse function work" -- the topic is the agent's OWN
    # faculty (a second-person POSSESSIVE 'your' determining a following noun).
    # The graph understands this (your -refers_to-> a second-person Concept, and
    # it has a next_mention) and DEFERS the external route -> no answer_topic
    # goal, no grounding of "your collapse". It falls to the reflexive self path.
    reply = agent.converse("How does your collapse function work?", speech_act="question")
    assert not _answer_topic_goals(agent, "collapse function") and not _answer_topic_goals(agent, "collapse"), (
        "a second-person-possessed topic ('your collapse') must NOT route to "
        "external-topic grounding -- the graph understands it is about the agent")
    assert "couldn't find it through the sources" not in (reply or "").lower(), (
        "it must not fall to the external-topic gap floor")


def test_external_topic_still_routes_with_possessive_guard(agent):
    # The possessive guard must not break the moon route ('you' is the subject,
    # 'moon' is preceded by 'the' -- no possessive determining the topic).
    agent.converse("What do you know about the moon?", speech_act="question")
    assert _answer_topic_goals(agent, "moon"), (
        "an external topic with no possessive self-reference still routes")


def test_what_is_x_made_of_routes_to_topic_not_know_tail(agent, monkeypatch):
    # "What is the moon made of?" must route to topic=moon (composition ask),
    # NOT know('moon made of') -> "I don't know moon made of."
    import domains.topic_grounding as _tg

    def fake_aspect(agent, concept, aspect, **kw):
        assert concept == "moon" and aspect == "made_of"
        ans = "The Moon's crust is mostly oxygen and silicon; its mantle is silicate rock."
        return agent.learn_from_teacher(
            f"composition of {concept}",
            {"answer": ans, "learn": [{"phrase": f"composition of {concept}", "answer": ans}]})

    monkeypatch.setattr(_tg, "ground_topic_aspect", fake_aspect)
    reply = agent.converse("What is the moon made of?", speech_act="question")
    assert _answer_topic_goals(agent, "moon"), (
        "composition question must mint Goal{kind:answer_topic, concept:'moon'}")
    assert "moon made of" not in reply.lower(), (
        "the mangled know-tail reply must be gone")
    assert "silicate" in reply.lower() or "oxygen" in reply.lower() or "crust" in reply.lower(), (
        "composition aspect must answer with material/composition content, not generic orbit prose")
    assert "i am jabberwock" not in reply.lower()


def test_embedded_wh_topic_routes_not_self_identity(agent):
    # "do you know what dancing is?" — reflexive (you), but the topic is the
    # embedded wh-clause nominal (dancing), not the agent's identity.
    reply = agent.converse("Do you know what dancing is?", speech_act="question")
    assert _answer_topic_goals(agent, "dancing"), (
        "embedded wh-clause topic must route to answer_topic, not self_identity")
    assert "i am jabberwock" not in reply.lower(), (
        "the self-identity misroute must be gone")
    assert "dancing" in reply.lower() or "dance" in reply.lower() or "couldn't find" in reply.lower(), (
        "the reply must be about dancing (or an honest topic miss), not identity")


def test_polar_capability_question_honest_reply(agent):
    reply = agent.converse("Can you dance?", speech_act="question")
    assert "i don't hold that" not in reply.lower(), (
        "a capability question must not get the knowledge-gap shrug")
    assert "can't dance" in reply.lower() or "no embodiment" in reply.lower(), (
        "the graph must honestly decline dance from held capability knowledge")
    assert "no body" not in reply.lower(), (
        "adapter must not inject the retired 'no body' floor")


def test_navigate_3d_spaces_graph_capability_reply(agent):
    reply = agent.converse("Can you navigate 3D spaces?", speech_act="question")
    meta = agent.last_turn_reply_meta()
    assert meta.get("reply_from") == "agent"
    assert "no body" not in reply.lower()
    assert "yes" in reply.lower() or "can navigate" in reply.lower(), (
        "spatial navigation is a held graph capability, not a body-dependent refusal")


def test_polar_capability_with_object_still_routes_topic(agent):
    # "can you play chess?" has an external object — topic route, not capability floor.
    reply = agent.converse("Can you play chess?", speech_act="question")
    assert _answer_topic_goals(agent, "chess"), (
        "an object-bearing polar question routes to the external topic")
    assert "chess" in reply.lower()


def test_infer_3d_from_2d_image_graph_capability_reply(agent):
    q = "Can you infer 3D spaces from a 2D image that has perspective?"
    reply = agent.converse(q, speech_act="question")
    meta = agent.last_turn_reply_meta()
    assert meta.get("reply_from") == "agent", (
        "capability question must be answered by the graph, not the adapter topic floor")
    assert "visual representation" not in reply.lower(), (
        "must not blind-lookup the 'image' topic instead of answering capability")
    assert "infer" in reply.lower() or "perspective" in reply.lower() or "spatial" in reply.lower(), (
        "reply must address spatial inference capability")


def test_polar_capability_conditional_clause_not_topic_routed(agent):
    # "if you had a body" must not hijack a capability question into grounding
    # the Wikipedia disambiguation page for "body" ("Body may refer to:").
    reply = agent.converse("Could you dance if you had a body?", speech_act="question")
    assert not _answer_topic_goals(agent, "body"), (
        "a conditional clause noun must not become an answer_topic route")
    assert "body may refer to" not in reply.lower(), (
        "the disambiguation header is the symptom of the misroute")
    assert "imagining i had" in reply.lower(), (
        "a counterfactual capability question must route to imagination")
    assert "dance" in reply.lower(), (
        "the reply must address dancing under the hypothetical")
    assert "no body" not in reply.lower() or "imagining" in reply.lower(), (
        "must not flat-refuse with only 'I have no body'")
