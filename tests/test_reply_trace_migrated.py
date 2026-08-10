"""Reply trace read + human flag -> SelfConcern (web UI support)."""
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


def test_adapter_reply_marked_not_agent(agent):
    reply = agent.converse("Can you navigate 3D spaces?", speech_act="question")
    assert reply
    tid = agent.last_turn_inbound_id()
    meta = agent.last_turn_reply_meta()
    assert meta.get("reply_from") == "agent"
    trace = agent.reply_turn_trace(tid)
    assert trace.get("reply_from") == "agent"
    assert "navigate" in reply.lower() or "spatial" in reply.lower() or "yes" in reply.lower()
    assert "no body" not in reply.lower()


def test_reply_turn_trace_after_converse(agent):
    agent.converse("Can you dance?", speech_act="question")
    tid = agent.last_turn_inbound_id()
    assert tid is not None
    import substrate_rs as srs
    agent.inner.set_attr(srs.NodeID(tid), "comp_reply_text",
                         "No — I can't dance. I have no body.")
    trace = agent.reply_turn_trace(tid)
    assert trace is not None
    assert trace["turn_id"] == tid
    assert "dance" in trace["question"].lower()
    assert trace["reply"]
    assert trace["parse"].get("comp_kind") == "question"


def test_flag_reply_mints_concern(agent):
    agent.converse("Can you dance?", speech_act="question")
    tid = agent.last_turn_inbound_id()
    import substrate_rs as srs
    mid = srs.NodeID(tid)
    note = "Should honestly decline capability, not say 'I don't hold that'."
    agent._ensure_comprehension_seeds()
    agent.inner.set_attr(mid, "reply_flag_note", note)
    agent.inner.set_attr(mid, "reply_flag_pending", 1.0)
    agent.comprehend()
    trace = agent.reply_turn_trace(tid)
    assert trace["concerns"], "flag rule must mint a SelfConcern"
    fix = [c for c in trace["concerns"] if c.get("kind") == "reply_fix"]
    assert fix and fix[0]["content"] == note
