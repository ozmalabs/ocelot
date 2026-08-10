"""ChatWorld — migrated twin of tests/test_chat_world.py.

All ten tests from the CuriousAgent-based bench are covered here on the
seed-booted WorldAdapter.  No CuriousAgent; no Python rule engine; the graph
IS the agent.

Mapping (original → migrated):
  test_attach_creates_interlocutor_and_channel
    → test_attach_creates_interlocutor_and_channel
  test_attach_sets_addressee_edge_so_speak_can_fire
    → test_attach_sets_addressee_edge_so_speak_can_fire
  test_attach_links_both_participants_to_channel
    → test_attach_links_both_participants_to_channel
  test_attach_is_idempotent
    → test_attach_is_idempotent
  test_add_inbound_creates_message_from_interlocutor
    → test_add_inbound_creates_message_from_interlocutor
  test_add_outbound_creates_message_from_agent
    → test_add_outbound_creates_message_from_agent
  test_conversation_returns_messages_in_tick_order
    → test_conversation_returns_messages_in_insertion_order
  test_last_inbound_returns_latest_user_message
    → test_last_inbound_returns_latest_user_message
  test_conversation_persists_across_save_load
    → test_conversation_persists_across_save_load
  test_addressee_persists_across_save_load
    → test_addressee_persists_across_save_load
"""
from __future__ import annotations

import os
import tempfile

from substrate.world_adapter import WorldAdapter

# Node types (mirrors the constants from domains/chat_world.py)
_INTERLOCUTOR_TYPE = "Interlocutor"
_CHANNEL_TYPE = "Channel"
_MESSAGE_TYPE = "Message"


# ---------------------------------------------------------------------------
# attach — structure
# ---------------------------------------------------------------------------

def test_attach_creates_interlocutor_and_channel():
    """attach_chat_world() creates exactly one Interlocutor and one Channel,
    and the Interlocutor carries name=="user"."""
    wa = WorldAdapter()
    ids = wa.attach_chat_world()
    assert ids["interlocutor"] is not None
    assert ids["channel"] is not None
    inter = wa.s.nodes(_INTERLOCUTOR_TYPE)
    chan = wa.s.nodes(_CHANNEL_TYPE)
    assert len(inter) == 1
    assert len(chan) == 1
    assert wa.s.node(inter[0])["attrs"]["name"] == "user"


def test_attach_sets_addressee_edge_so_speak_can_fire():
    """The addressee edge from agent to Interlocutor is present after attach,
    making the speak-as-action machinery live (the edge the seeded Terms read)."""
    wa = WorldAdapter()
    ids = wa.attach_chat_world()
    addressees = list(wa.inner.neighbours(wa.agent, "addressee"))
    assert ids["interlocutor"] in addressees


def test_attach_links_both_participants_to_channel():
    """Both the agent and the Interlocutor have participates_in edges to the
    Channel after attach."""
    wa = WorldAdapter()
    ids = wa.attach_chat_world()
    # agent participates in channel
    agent_in_channel = list(wa.inner.neighbours(wa.agent, "participates_in"))
    assert ids["channel"] in agent_in_channel
    # interlocutor participates in channel
    inter_in_channel = list(wa.inner.neighbours(ids["interlocutor"], "participates_in"))
    assert ids["channel"] in inter_in_channel


def test_attach_is_idempotent():
    """Calling attach_chat_world() twice returns the same ids and does not
    duplicate Interlocutor / Channel nodes or the addressee edge."""
    wa = WorldAdapter()
    ids1 = wa.attach_chat_world()
    ids2 = wa.attach_chat_world()
    assert ids1 == ids2
    # exactly one Interlocutor and one Channel
    assert len(wa.s.nodes(_INTERLOCUTOR_TYPE)) == 1
    assert len(wa.s.nodes(_CHANNEL_TYPE)) == 1
    # addressee edge is not duplicated
    addrs = list(wa.inner.neighbours(wa.agent, "addressee"))
    assert len(addrs) == 1


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------

def test_add_inbound_creates_message_from_interlocutor():
    """add_inbound() creates a Message with from=='interlocutor' and the correct
    text, plus a sent_by edge to the Interlocutor."""
    wa = WorldAdapter()
    ids = wa.attach_chat_world()
    mid = wa.add_inbound("I am your creator, Matt")
    n = wa.s.node(mid)
    assert n["type"] == _MESSAGE_TYPE
    assert n["attrs"]["text"] == "I am your creator, Matt"
    assert n["attrs"]["from"] == "interlocutor"
    sent_by = list(wa.inner.neighbours(mid, "sent_by"))
    assert ids["interlocutor"] in sent_by


def test_add_outbound_creates_message_from_agent():
    """add_outbound() creates a Message with from=='agent' and a sent_by edge
    to the agent root."""
    wa = WorldAdapter()
    wa.attach_chat_world()
    mid = wa.add_outbound("noted.")
    n = wa.s.node(mid)
    assert n["type"] == _MESSAGE_TYPE
    assert n["attrs"]["from"] == "agent"
    sent_by = list(wa.inner.neighbours(mid, "sent_by"))
    assert wa.agent in sent_by


# ---------------------------------------------------------------------------
# conversation history
# ---------------------------------------------------------------------------

def test_conversation_returns_messages_in_insertion_order():
    """conversation() returns all three Messages in the order they were added
    (oldest first by node-id).  The migrated version orders by node id rather
    than CuriousAgent._activity_tick — the semantics are identical when messages
    are added sequentially."""
    wa = WorldAdapter()
    wa.attach_chat_world()
    wa.add_inbound("hello")
    wa.add_outbound("hi back")
    wa.add_inbound("how are you")
    conv = wa.conversation()
    assert len(conv) == 3
    assert [m["text"] for m in conv] == ["hello", "hi back", "how are you"]
    assert [m["from"] for m in conv] == ["interlocutor", "agent", "interlocutor"]


def test_last_inbound_returns_latest_user_message():
    """last_inbound() returns the most recently added inbound message."""
    wa = WorldAdapter()
    wa.attach_chat_world()
    wa.add_inbound("first")
    wa.add_outbound("noted.")
    wa.add_inbound("second")
    last = wa.last_inbound()
    assert last["text"] == "second"


# ---------------------------------------------------------------------------
# persistence — the world structure round-trips
# ---------------------------------------------------------------------------

def test_conversation_persists_across_save_load():
    """Message nodes round-trip through save/load; conversation() still returns
    the full history after loading, and attach_chat_world() still works."""
    wa = WorldAdapter()
    wa.attach_chat_world()
    wa.add_inbound("I am Matt")
    wa.add_outbound("noted.")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False) as f:
        path = f.name
    try:
        wa.save(path)
        loaded = WorldAdapter.load(path)
        # Message nodes are in the graph — no attach needed to read them
        msg_nodes = loaded.s.nodes(_MESSAGE_TYPE)
        assert len(msg_nodes) == 2
        texts = sorted(loaded.s.node(m)["attrs"]["text"] for m in msg_nodes)
        assert texts == ["I am Matt", "noted."]

        # after attaching the chat world, conversation() still works
        loaded.attach_chat_world()
        conv = loaded.conversation()
        assert [m["text"] for m in conv] == ["I am Matt", "noted."]
    finally:
        os.unlink(path)


def test_addressee_persists_across_save_load():
    """The Interlocutor node and the addressee edge survive save/load; the
    loaded adapter can immediately resume the conversation."""
    wa = WorldAdapter()
    wa.attach_chat_world()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False) as f:
        path = f.name
    try:
        wa.save(path)
        loaded = WorldAdapter.load(path)
        # Interlocutor is present
        inter = loaded.s.nodes(_INTERLOCUTOR_TYPE)
        assert len(inter) == 1
        # addressee edge points at it
        addr = list(loaded.inner.neighbours(loaded.agent, "addressee"))
        assert inter[0] in addr
    finally:
        os.unlink(path)
