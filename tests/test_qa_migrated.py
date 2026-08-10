"""Factual question-answering (definitional slice), migrated — the agent answers
'what is X?' from a KNOWN FACT, on the seed-booted WorldAdapter, no CuriousAgent.

This is the tractable, graph-native slice of answer_within: a fact the agent
knows is a persistent Term.Relation subgraph tagged `knows_fact`; answering 'what
is X?' is a graph retrieval (the fact whose subject leaf is X) + a render via the
graph engine. Integrated into the conversation loop: a question's adjacency pair
is `answer`, and converse() fills that answer with the retrieved fact.

(The full answer_within — Frame recognition + capability dispatch + the math
kernels in reason.py — is a much heavier faculty and stays on the legacy path;
this covers definitional retrieval, the common case.)
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _agent():
    wa = WorldAdapter()
    for w in ("is_a", "uses", "graph", "structure", "process", "data"):
        wa.learn_sign(w, w)
    wa.learn_sign("hello", "greeting")
    wa.learn_sign("noted", "acknowledgment")
    wa.learn_fact({"is_a": {"left": "graph", "right": "structure"}})
    wa.learn_fact({"uses": {"left": "process", "right": "data"}})
    return wa


# --- the faculty --------------------------------------------------------

def test_known_fact_is_graph_resident():
    wa = _agent()
    facts = list(wa.inner.neighbours(wa.agent, "knows_fact"))
    assert len(facts) == 2
    assert all(wa.s.node(f)["type"] == "Term.Relation" for f in facts)


def test_answer_about_renders_the_fact():
    wa = _agent()
    assert wa.answer_about("graph") == "graph is_a structure"
    assert wa.answer_about("process") == "process uses data"


def test_answer_about_unknown_subject_is_none():
    assert _agent().answer_about("unicorn") is None


def test_answer_question_extracts_the_subject():
    wa = _agent()
    assert wa.answer_question("what is a graph?") == "graph is_a structure"
    assert wa.answer_question("what is process") == "process uses data"
    assert wa.answer_question("what's a graph?") == "graph is_a structure"


# --- integrated into the conversation loop ------------------------------

def test_question_turn_answers_from_a_fact():
    wa = _agent()
    assert wa.converse("what is a graph", "question") == "graph is_a structure"


def test_unknown_question_yields_no_answer():
    """No known fact -> an HONEST 'I don't know ...' statement, never silence: the
    conversational surface never returns None (it names the focus it can't answer)."""
    reply = _agent().converse("what is xyz", "question")
    assert isinstance(reply, str) and "xyz" in reply and reply.lower().startswith("i don't")


def test_mixed_conversation():
    """Greeting, statement, and question each handled on the one loop."""
    wa = _agent()
    assert wa.converse("hello", "greeting") == "hello"
    assert wa.converse("the sky is blue", "statement") == "noted"
    assert wa.converse("what is a graph", "question") == "graph is_a structure"
