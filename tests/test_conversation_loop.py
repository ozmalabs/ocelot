"""test_conversation_loop — the COMPLETE conversational turn on the live converse
loop: the jabberwock ANSWERS a question, ACTS on an instruction (a conversation
drives a goal -> it does something it chose), and ASKS BACK on a comprehension
gap (a repair first-pair-part), instead of the old answer-or-acknowledge only.

The pieces already existed (comprehend_text, the self-model reflect, the self-
built describe faculty, the adjacency-pair repair vocabulary); this gates that
`WorldAdapter.converse` now WIRES them into one path via
`domains/conversation_action.py`. Every assertion drives the REAL converse loop.
donkey=0 throughout — the CONTENT is the agent's own faculties, not host prose.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import conversation_action as ca


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("I heard you.", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


@pytest.fixture(scope="module")
def agent():
    return _agent()


def _goals(a, kind):
    return [g for g in a.s.nodes("Goal")
            if a.inner.has_node(g) and a.s.node(g)["attrs"].get("kind") == kind]


# ---------------------------------------------------------------------------
# REGRESSION — the existing converse behaviour is untouched.
# ---------------------------------------------------------------------------

def test_greeting_round_trip(agent):
    assert agent.converse("hello", "greeting") == "hello"


def test_statement_acknowledged(agent):
    assert agent.converse("the sky is blue", "statement") == \
        "ERROR: no communicative response could be generated."


def test_answer_is_terminal(agent):
    # A received answer has no second-pair-part. The dead-end is explicit and
    # diagnostic, never disguised as a dismissive register acknowledgement.
    reply = agent.converse("it is blue", "answer")
    assert reply == "ERROR: no communicative response could be generated."


# ---------------------------------------------------------------------------
# QUESTION — still answers in prose (unchanged path).
# ---------------------------------------------------------------------------

def test_question_still_answers(agent):
    ans = agent.converse("How are you organised?", "question")
    assert isinstance(ans, str) and "organis" in ans.lower()
    assert ans.strip().lower() not in ("noted", "acknowledgment")


def test_world_question_still_answers(agent):
    ans = agent.converse("Tell me about the rule hop_descend_gradient.", "question")
    assert isinstance(ans, str) and "hop_descend_gradient" in ans


# ---------------------------------------------------------------------------
# ACT — an instruction drives a goal -> the agent DOES something (self-report).
# ---------------------------------------------------------------------------

def test_act_self_report_mints_goal_and_produces(agent):
    before = len(_goals(agent, "report_self"))
    reply = agent.converse("report your organisation", "statement")
    assert isinstance(reply, str) and "organis" in reply.lower()
    assert reply.strip().lower() not in ("noted", "acknowledgment")
    # the ACTION happened: a report_self Goal was minted (graph evidence).
    assert len(_goals(agent, "report_self")) == before + 1


def test_act_tell_about_yourself(agent):
    reply = agent.converse("tell me about yourself", "question")
    assert isinstance(reply, str) and reply.strip()
    assert reply.strip().lower() not in ("noted", "acknowledgment")


# ---------------------------------------------------------------------------
# ACT — describe an ATTACHED scene via the self-built describe faculty.
# ---------------------------------------------------------------------------

def test_act_describe_scene(agent):
    ca.attach_scene(agent, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False}])
    reply = agent.converse("describe what you see", "statement")
    assert isinstance(reply, str) and reply.strip()
    assert reply.strip().lower() not in ("noted", "acknowledgment")
    # the agent's OWN authored rule minted a describe_scene Goal + produced text.
    assert _goals(agent, "describe_scene")
    assert len(reply.split()) >= 3          # produced multiple utterances, not a canned token


# ---------------------------------------------------------------------------
# ASK-BACK — a comprehension gap -> the agent ASKS, not acknowledges.
# ---------------------------------------------------------------------------

def test_ask_back_on_gap(agent):
    reply = agent.converse("quorplezap the door", "statement")
    assert isinstance(reply, str)
    assert "quorplezap" in reply            # quotes the real trouble source
    assert reply.rstrip().endswith("?")     # it ASKED
    assert reply.strip().lower() not in ("noted", "acknowledgment")


def test_ask_back_is_not_a_fabricated_answer(agent):
    # discriminative: the gap is NOT answered with invented content — the reply
    # is a repair question, and a clarification first-pair-part is recorded.
    reply = agent.converse("flar the glorp", "statement")
    assert reply.rstrip().endswith("?") and "flar" in reply
    clar = [m for m in agent.s.nodes("Message")
            if agent.s.node(m)["attrs"].get("from") == "agent"
            and agent.s.node(m)["attrs"].get("trouble_source")]
    assert clar, "expected a recorded clarification (repair) first-pair-part"


# ---------------------------------------------------------------------------
# The three behaviours are DISCRIMINATED, and it stays donkey=0.
# ---------------------------------------------------------------------------

def test_three_behaviours_discriminated(agent):
    q = agent.converse("How are you organised?", "question")          # ANSWER
    act = agent.converse("report your organisation", "statement")     # ACT
    ask = agent.converse("blorptangle the widget", "statement")       # ASK-BACK
    assert "organis" in q.lower()
    assert act and act.strip().lower() not in ("noted",)
    assert ask.rstrip().endswith("?") and "blorptangle" in ask
    # ask-back is not an answer; answer is not a question.
    assert not q.rstrip().endswith("?")


def test_donkey_zero(agent):
    # every turn above ran without a single self-teacher (LLM) call.
    assert agent._donkey["n"] == 0
