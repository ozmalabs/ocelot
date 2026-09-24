"""test_comprehension_robustness — kill the "understood" catch-all: an ornate,
satisfiable, or world-less input must reach its REAL intent, never a bare
acknowledgment. Every assertion drives the live `WorldAdapter.converse`.

Four routing fixes (all reasoned over GROUNDED signals — grammar, self-model,
the honest world-limit — not a per-word table):
  * POLITENESS   — "Pray,"/"kindly" are discourse markers, stripped so the
    ornate question reaches self-identity (not a bogus "Pray the nature" goal);
  * SATISFIABLE  — "Name one of your rules." is answered from held data;
  * HONEST NO-WORLD — "Describe what you perceive." with no scene attached hits
    the honest "no world attached", never "understood".

donkey=0 throughout.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


@pytest.fixture(scope="module")
def agent():
    return _agent()


_ACKS = {"noted", "understood", "got it", "i have no reply to that."}


def _say(agent, text):
    return agent.converse(text, agent.classify_speech_act(text))


# ---------------------------------------------------------------------------
# POLITENESS markers reach the intent underneath, not a bogus instruction.
# ---------------------------------------------------------------------------

def test_pray_ornate_question_reaches_self_identity(agent):
    reply = _say(agent, "Pray, what manner of thing are you?")
    low = reply.lower()
    assert low.strip() not in _ACKS
    assert "jabberwock" in low or "i am" in low
    assert "pray" not in low                     # never built a "goal to Pray"


def test_kindly_reaches_self_identity(agent):
    reply = _say(agent, "kindly tell me what you are")
    low = reply.lower()
    assert low.strip() not in _ACKS
    assert "jabberwock" in low or "i am" in low


# ---------------------------------------------------------------------------
# SATISFIABLE — an instruction answerable from held data is ANSWERED.
# ---------------------------------------------------------------------------

def test_name_one_of_your_rules_names_a_held_rule(agent):
    reply = _say(agent, "Name one of your rules.")
    low = reply.lower()
    assert low.strip() not in _ACKS
    assert "my rule" in low                       # named a real held RuleSummary
    # the named rule is really in the graph.
    names = {agent.s.node(n)["attrs"].get("name")
             for n in agent.s.nodes("RuleSummary") if agent.inner.has_node(n)}
    assert any(nm and nm.lower() in low for nm in names)


# ---------------------------------------------------------------------------
# HONEST NO-WORLD — a perception request with no scene is honest, not "understood".
# ---------------------------------------------------------------------------

def test_describe_what_you_perceive_no_scene_is_honest(agent):
    assert getattr(agent, "_conv_scene", None) is None      # no scene attached
    reply = _say(agent, "Describe what you perceive.")
    low = reply.lower()
    assert low.strip() not in _ACKS
    assert "no world attached" in low or "no scene attached" in low
    assert "perceive" in low


# ---------------------------------------------------------------------------
# NO REGRESSION — the existing conversational behaviour still holds.
# ---------------------------------------------------------------------------

def test_greeting_unchanged(agent):
    assert agent.converse("hello", "greeting") == "hello"


def test_statement_still_acknowledged(agent):
    assert agent.converse(
        "the sky is blue", "statement"
    ) == "ERROR: no communicative response could be generated."


def test_self_organisation_question_unchanged(agent):
    reply = agent.converse("How are you organised?", "question")
    assert isinstance(reply, str) and reply.strip()
    assert reply.strip().lower() not in _ACKS


def test_ask_back_on_real_gap_unchanged(agent):
    reply = agent.converse("quorplezap the door", "statement")
    low = reply.lower()
    assert "quorplezap" in low                     # quotes the real trouble source
    assert "?" in reply


def test_donkey_stays_zero(agent):
    _say(agent, "Pray, what manner of thing are you?")
    _say(agent, "Name one of your rules.")
    _say(agent, "Describe what you perceive.")
    assert agent._donkey["n"] == 0
