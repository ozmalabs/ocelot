"""Full conversational turn, migrated — text in -> text out on the seed-booted
WorldAdapter, with NO CuriousAgent, entirely on graph data.

`converse(text, speech_act)` runs the whole loop as graph operations:
  ingest (receive_utterance: Message + has_speech_act + sent_by)
    -> comprehend (intent Rules build the Intent + adjacency-pair expects_response;
                   the conversation_reply Rule constructs the outbound reply)
    -> emit (render the reply's speech act to surface via the graph render engine)

Every step is a seeded Term/Rule or a graph-resident render; the adapter only
translates I/O. Reply CONTENT here is the canonical surface of the expected
speech act (greeting->'hello', acknowledgment->'noted'); richer content
(answer_within for questions) is the separate reply-content faculty.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _agent():
    wa = WorldAdapter()
    # canonical surfaces for the speech acts the agent replies with
    wa.learn_sign("hello", "greeting")
    wa.learn_sign("noted", "acknowledgment")
    return wa


def test_greeting_round_trip():
    """text 'hello' (a greeting) -> the agent greets back, 'hello'."""
    assert _agent().converse("hello", "greeting") == "hello"


def test_unsupported_statement_exposes_explicit_error():
    """A statement without a selected meaning cannot emit a fixed acknowledgement."""
    assert _agent().converse("the sky is blue", "statement") == \
        "ERROR: no communicative response could be generated."


def test_terminal_act_gets_no_reply():
    """A received answer has no second-pair-part, but the conversational surface
    never hides failure behind a fixed acknowledgement, never None."""
    reply = _agent().converse("it is blue", "answer")
    assert reply == "ERROR: no communicative response could be generated."


def test_turn_spine_recorded_in_the_graph():
    """The exchange leaves a turn spine: the agent's reply responds_to the
    inbound, both Messages graph-resident."""
    wa = _agent()
    wa.converse("hello", "greeting")
    inbound = [m for m in wa.s.nodes("Message")
               if wa.s.node(m)["attrs"].get("from") == "interlocutor"]
    outbound = wa.outbound_messages()
    assert len(inbound) == 1 and len(outbound) == 1
    assert inbound[0] in wa.responds_to(outbound[0])


def test_multiple_turns_each_get_their_own_reply():
    wa = _agent()
    assert wa.converse("hello", "greeting") == "hello"
    assert wa.converse("the sky is blue", "statement") == \
        "ERROR: no communicative response could be generated."
    # two inbound, two outbound replies
    assert len([m for m in wa.s.nodes("Message")
                if wa.s.node(m)["attrs"].get("from") == "interlocutor"]) == 2
    assert len(wa.outbound_messages()) == 2
