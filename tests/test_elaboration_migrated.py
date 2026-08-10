"""Graph-native progressive DISCLOSURE ('tell me more') -- the agent serves the
NEXT unseen chunk of detail on each continuation follow-up, with the DECISION
and the progression living in seed RULES (seeds/conversation_elaborate.json),
not Python.

The spine (all graph, no arithmetic -- a served-marker chain):

  1. request_detail_for_current_topic RULE mints DetailRequest{topic:X} when the
     conversation has a current topic X and no DetailRequest for it yet.
  2. domains.fetch_dispatch.scan_and_ingest_detail (mechanical I/O, mirrors
     scan_and_search) fulfils it: topic_detail(agent, X) -> ordered chunk list,
     ingested as a graph chain (Topic -detail_head-> c0; Topic -has_detail-> c;
     c -next_detail-> c_next).
  3. serve_next_detail_chunk RULE serves the HEAD OF THE UNSERVED RUN on each
     'tell me more' (a continuation-cue Concept resolved from a Mention),
     marking that chunk served=1.0 -- exactly one chunk per turn, in order.
  4. elaboration_exhausted RULE gives an honest floor when detail exists but is
     all served, so 'more' is never silent.
  5. A PLAIN anaphor with no continuation cue ('how big is it') is NOT deferred:
     it still routes to the summary path (conversation_topic_tracking), and
     consumes no detail chunk.

Detail + grounding are monkeypatched (deterministic offline stand-ins) so these
tests never touch the network.
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


_FAKE_DETAIL = ["First detail.", "Second detail.", "Third detail."]


def _install_fakes(monkeypatch):
    """Offline stand-ins: `topic_detail` returns a fixed 3-chunk list (no
    network); `ground_topic` memoises a summary so the summary path in
    _answer_topic_reply never reaches out to the web either."""
    import domains.topic_grounding as _tg

    monkeypatch.setattr(_tg, "topic_detail",
                        lambda ag, phrase, **kw: list(_FAKE_DETAIL))

    def fake_ground_topic(ag, phrase, **kw):
        p = str(phrase)
        ans = f"the {p} is a topic i can summarise"
        return ag.learn_from_teacher(
            p, {"answer": ans, "learn": [{"phrase": p, "answer": ans}]})

    monkeypatch.setattr(_tg, "ground_topic", fake_ground_topic)


def _current_topic(a):
    for n in a.inner.neighbours(a.agent, "current_topic"):
        if a.inner.has_node(n):
            return a.s.node(n)["attrs"].get("name")
    return None


def _answer_topic_goals(a, concept=None):
    out = []
    for g in a.inner.neighbours(a.agent, "has_goal"):
        if not a.inner.has_node(g):
            continue
        ga = a.s.node(g)["attrs"]
        if ga.get("kind") == "answer_topic" and (concept is None or ga.get("concept") == concept):
            out.append(g)
    return out


def _served_count(a, topic):
    n = 0
    for c in a.s.nodes("DetailChunk"):
        if not a.inner.has_node(c):
            continue
        ca = a.s.node(c)["attrs"]
        if ca.get("topic") == topic and ca.get("served") == 1.0:
            n += 1
    return n


def _detail_chunks(a, topic):
    return [a.s.node(c)["attrs"]
            for c in a.s.nodes("DetailChunk")
            if a.inner.has_node(c) and a.s.node(c)["attrs"].get("topic") == topic]


def _prime_moon_detail(a):
    """Converse a topic, fire the mint rule, and ingest the (faked) detail."""
    from domains.fetch_dispatch import scan_and_ingest_detail
    a.converse("What do you know about the moon?", speech_act="question")
    assert _current_topic(a) == "moon", "answering a topic records it as current"
    # current_topic is set by the adapter AFTER comprehend; one more rule pass
    # lets request_detail_for_current_topic mint the DetailRequest.
    a.comprehend()
    touched = scan_and_ingest_detail(a)
    assert touched, "the agent's rule must have minted a DetailRequest to fulfil"
    return touched


def test_detail_request_minted_and_chain_ingested(agent, monkeypatch):
    _install_fakes(monkeypatch)
    _prime_moon_detail(agent)
    chunks = _detail_chunks(agent, "moon")
    assert [c["text"] for c in chunks] == _FAKE_DETAIL, (
        "the ordered chunk list must be ingested as DetailChunk nodes")
    assert _served_count(agent, "moon") == 0, "nothing served yet"


def test_progressive_disclosure_serves_next_chunk_each_time(agent, monkeypatch):
    _install_fakes(monkeypatch)
    _prime_moon_detail(agent)

    r1 = agent.converse("Tell me more about it.", speech_act="question")
    assert r1 == "First detail.", "first 'more' serves the head chunk"
    assert _served_count(agent, "moon") == 1, "served marker advanced by one"

    r2 = agent.converse("Tell me more about it.", speech_act="question")
    assert r2 == "Second detail.", "second 'more' serves the next chunk in order"
    assert _served_count(agent, "moon") == 2

    r3 = agent.converse("Tell me more about it.", speech_act="question")
    assert r3 == "Third detail.", "third 'more' serves the last chunk"
    assert _served_count(agent, "moon") == 3

    r4 = agent.converse("Tell me more about it.", speech_act="question")
    assert r4 == "That's the main of what I hold about it.", (
        "when detail is exhausted, elaboration_exhausted fires (never silent)")
    assert _served_count(agent, "moon") == 3, "nothing left to serve"


def test_expand_synonym_also_serves(agent, monkeypatch):
    _install_fakes(monkeypatch)
    _prime_moon_detail(agent)
    # 'expand' is another continuation cue; carried on an anaphoric follow-up
    # (the supported 'more about it' shape) it serves the head chunk too.
    r = agent.converse("Can you expand on it?", speech_act="question")
    assert r == "First detail.", "'expand' is a continuation cue too"


def test_plain_anaphora_uses_summary_not_serve(agent, monkeypatch):
    _install_fakes(monkeypatch)
    _prime_moon_detail(agent)

    # A plain anaphor with NO continuation cue must NOT consume a detail chunk;
    # it routes to the summary path (resolve_anaphor_to_current_topic).
    reply = agent.converse("How big is it?", speech_act="question")
    assert _served_count(agent, "moon") == 0, (
        "a plain anaphor consumes no detail chunk (serve rule must not fire)")
    assert reply != "First detail."
    assert _answer_topic_goals(agent, "moon"), (
        "'how big is it' resolves to the tracked topic via the summary path")


def test_more_without_detail_falls_through_to_summary(agent, monkeypatch):
    """Regression: a continuation follow-up when NO detail has been ingested for
    the topic must still resolve to the summary re-answer (the anaphor-exclusion
    guard defers to the elaboration seed ONLY when detail chunks exist)."""
    _install_fakes(monkeypatch)
    agent.converse("What do you know about the moon?", speech_act="question")
    # No scan_and_ingest_detail -> no DetailChunk nodes for 'moon'.
    reply = agent.converse("Tell me more about it.", speech_act="question")
    assert reply != "That's the main of what I hold about it.", (
        "with no detail ingested, do not claim exhaustion")
    assert "moon" in reply.lower() or "satellite" in reply.lower() or "topic" in reply.lower(), (
        "falls through to the summary re-answer path")
    assert _answer_topic_goals(agent, "moon")
