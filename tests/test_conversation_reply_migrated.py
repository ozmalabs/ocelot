"""Turn-taking reply, migrated — the comprehend->respond conversational SPINE
runs as graph Rules on the seed-booted WorldAdapter, no CuriousAgent.

The reply DECISION is now a graph-resident RewriteRule (the conversation_reply
seed, authored): an inbound Message whose Intent expects a response (an adjacency
pair, from the conversation seed's expects_response graph data) and that hasn't
been responded to yet gets the agent's outbound second-pair-part Message —
carrying that speech act and a responds_to edge forming the turn spine. Fires
under run_rules() alongside the intent rules in one comprehend().

(Reply CONTENT/surface realization — answer_within for questions, produce() for
statements — is a separate heavier faculty; this covers the turn-taking spine:
which speech act the reply is, and the responds_to thread.)
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def _sa(wa, mid):
    return [wa.s.node(x)["attrs"].get("name")
            for x in wa.inner.neighbours(mid, "has_speech_act")]


def _turn(wa, text, speech_act):
    """One inbound turn: receive + comprehend; return (inbound, reply-or-None)."""
    mid = wa.receive_utterance(text, speech_act=speech_act, speaker="user")
    wa.comprehend()
    replies = [r for r in wa.outbound_messages() if mid in wa.responds_to(r)]
    return mid, (replies[0] if replies else None)


def test_greeting_gets_a_greeting_back():
    """greeting -> greeting (the mirrored adjacency pair): the agent's reply
    carries the greeting speech act and responds_to the inbound."""
    wa = WorldAdapter()
    wa.enable_replies()
    inbound, reply = _turn(wa, "hello", "greeting")
    assert reply is not None
    assert _sa(wa, reply) == ["greeting"]
    assert inbound in wa.responds_to(reply)
    assert wa.s.node(reply)["attrs"]["from"] == "agent"


def test_question_gets_an_answer_turn():
    """question -> answer: the reply's speech act is the expected second-pair-part
    (the conversation seed wires question -expects_response-> answer)."""
    wa = WorldAdapter()
    wa.enable_replies()
    _inbound, reply = _turn(wa, "what is it?", "question")
    assert reply is not None
    assert _sa(wa, reply) == ["answer"]


def test_reply_is_idempotent_at_fixed_point():
    """Comprehending again doesn't spawn a second reply to the same inbound."""
    wa = WorldAdapter()
    wa.enable_replies()
    inbound, reply = _turn(wa, "hello", "greeting")
    wa.comprehend()
    wa.comprehend()
    replies = [r for r in wa.outbound_messages() if inbound in wa.responds_to(r)]
    assert len(replies) == 1


def test_statement_gets_acknowledged():
    """statement -> acknowledgment (the conversation seed wires it): the agent
    acknowledges what it's told."""
    wa = WorldAdapter()
    wa.enable_replies()
    _inbound, reply = _turn(wa, "the sky is blue", "statement")
    assert reply is not None
    assert _sa(wa, reply) == ["acknowledgment"]


def test_no_reply_to_a_terminal_act():
    """An `answer` expects no response (terminal second-pair-part), so the reply
    rule doesn't fire — conversation doesn't loop forever."""
    wa = WorldAdapter()
    wa.enable_replies()
    _inbound, reply = _turn(wa, "it is blue", "answer")
    assert reply is None


def test_agent_messages_are_not_replied_to():
    """The reply rule only fires for inbound (from interlocutor) Messages — it
    doesn't reply to its own outbound, so no runaway self-conversation."""
    wa = WorldAdapter()
    wa.enable_replies()
    _inbound, reply = _turn(wa, "hello", "greeting")
    assert reply is not None
    # the reply itself is from the agent; comprehending again must not produce
    # a reply-to-the-reply.
    wa.comprehend()
    second_order = [r for r in wa.outbound_messages()
                    if reply in wa.responds_to(r)]
    assert second_order == []
