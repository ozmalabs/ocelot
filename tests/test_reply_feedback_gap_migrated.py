"""Plan P2 (2026-10-10): the agent files its own bad replies as concerns.

seeds/reply_feedback_gap.json (scripts/gen_reply_feedback_gap.py):
  * act mismatch: a produced reply that scored inappropriate in production
    (WorldAdapter._record_reply_quality datum), not the error floor;
  * the interlocutor's next turn: a held repair / rejection cue, or the same
    question asked again;
  * one SelfConcern{kind:'reply_quality'} per recurring class, about the turn
    whose reply drew the evidence (never the feedback turn).
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter, _CONVERSATION_ERROR_SURFACE   # noqa: E402
from substrate.boot_all import load_all_seeds                                   # noqa: E402

GOAL_TAKE = "I took on the goal to play the video games, but I have no attached world/faculty to carry it out here."


@pytest.fixture(scope="module")
def booted():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    assert list(a.s.nodes("ReplyFeedbackPolicy")), "reply_feedback_gap loads on a full boot"
    return a


@pytest.fixture()
def agent(booted):
    # each test gets its own fresh boot: concerns are graph state
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _turn(a, text, reply, prev=None):
    """An interlocutor turn as the production path leaves it: received,
    interpreted (minimal), replied to, outcome + ReplyQuality datum recorded."""
    S, I = a.s, a.inner
    m = S.add_node("Message", {"from": "interlocutor", "text": text})
    I.add_edge_unchecked(a.agent, "received", m)
    if prev is not None:
        I.add_edge_unchecked(m, "follows_turn", prev)
    I.set_attr(m, "comp_reply_text", reply)
    a.record_turn_outcome(m, "reply_released" if reply != _CONVERSATION_ERROR_SURFACE else "explicit_error")
    return m


def _concerns(a):
    return [(n, a.s.node(n)["attrs"]) for n in a.s.nodes("SelfConcern")
            if a.s.node(n)["attrs"].get("kind") == "reply_quality"]


def _about(a, sc):
    return list(a.inner.neighbours(sc, "about_message"))


def test_production_datum_is_written(agent):
    m = _turn(agent, "I like to play video games too!", GOAL_TAKE)
    at = agent.s.node(m)["attrs"]
    assert at["reply_quality_score"] == 0.0
    assert at["reply_quality_reason"] == "statement->goal_take"
    assert at["reply_quality_reply_class"] == "goal_take"


def test_recurring_act_mismatch_files_one_concern_about_the_first_turn(agent):
    a = agent
    m1 = _turn(a, "I like to play video games too!", GOAL_TAKE)
    a.comprehend(); a.comprehend()
    assert not _concerns(a), "one bad reply is not yet a recurring class"
    _turn(a, "I like to go hiking on weekends.", GOAL_TAKE.replace("play the video games", "go hiking"))
    for _ in range(3):
        a.comprehend()
    cs = _concerns(a)
    assert len(cs) == 1, cs
    sc, at = cs[0]
    assert at["sig_signal"] == "act_mismatch" and at["sig_reason"] == "statement->goal_take"
    assert at["status"] == "noted" and at["source"] == "implicit"
    assert _about(a, sc) == [m1]


def test_error_floor_is_left_to_unanswered_gap(agent):
    a = agent
    for t in ("I like movies.", "I like TV."):
        _turn(a, t, _CONVERSATION_ERROR_SURFACE)
    for _ in range(3):
        a.comprehend()
    assert not _concerns(a)


def test_next_turn_repair_is_evidence_about_the_previous_reply(agent):
    a = agent
    q1 = _turn(a, "What do you like to do for fun?", "got it")
    r1 = _turn(a, "What?", "got it", prev=q1)
    q2 = _turn(a, "Do you have any pets?", "got it", prev=r1)
    _turn(a, "Huh?", "got it", prev=q2)
    for _ in range(4):
        a.comprehend()
    cs = [c for c in _concerns(a) if c[1]["sig_signal"] == "repair"]
    assert len(cs) == 1, _concerns(a)
    assert cs[0][1]["sig_reason"] == "question->receipt"
    assert _about(a, cs[0][0]) == [q1], "the concern names the turn whose reply was repaired"
    assert r1 in a.inner.neighbours(q1, "drew_feedback")


def test_repeated_question_is_evidence(agent):
    a = agent
    q1 = _turn(a, "What is your favorite band?", "got it")
    q1b = _turn(a, "What is your favorite band?", "got it", prev=q1)
    q2 = _turn(a, "Where do you live?", "got it", prev=q1b)
    _turn(a, "where do you live", "got it", prev=q2)          # no '?': not counted as a question
    _turn(a, "Where do you live?", "got it", prev=q2)
    for _ in range(4):
        a.comprehend()
    cs = [c for c in _concerns(a) if c[1]["sig_signal"] == "repeat"]
    assert len(cs) == 1, _concerns(a)
    assert _about(a, cs[0][0]) == [q1]


def test_reply_quality_is_a_self_promotable_experiment_kind():
    import json
    pol = json.load(open(os.path.join(ROOT, "seeds", "self_promotion.json")))["nodes"][0]["attrs"]
    assert "reply_quality" in pol["eligible_kinds"]
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import jabberwock_daemon as jd
    rel, pipeline = jd._promote_relations_for_concern("reply_quality", ["reply", "turn"], "REPLY")
    assert pipeline == "experiment" and ["replay", "TURN", "in", "CONVERSATION"] in rel
