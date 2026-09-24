"""Phase 5A: graph-native canonical identity for learning gaps."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _concerns(a):
    return [a.s.node(sc)["attrs"] for sc in a.inner.neighbours(a.agent, "has_self_concern")]


def test_unresolved_gap_gets_stable_identity_with_origin_turn(agent, monkeypatch):
    import domains.topic_grounding as topic_grounding
    monkeypatch.setattr(topic_grounding, "ground_topic", lambda ag, phrase, **kw: None)

    agent.converse("What do you know about phase5a_unknown?", speech_act="question")
    agent.comprehend()
    gaps = [c for c in _concerns(agent) if c.get("content") == "phase5a_unknown"]
    assert len(gaps) == 1
    assert gaps[0]["gap_identity_schema"] == "gap_identity.v1"
    assert gaps[0]["gap_identity"].startswith("knowledge|implicit|phase5a_unknown|turn:")
    # The answer_topic goal now preserves the originating event mechanically;
    # the concern is linked to that goal, not directly to the Message.
    assert gaps[0]["gap_identity"].split("|turn:", 1)[1].isdigit()


def test_same_text_different_cognitive_kind_keeps_distinct_identities(agent):
    first = agent.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": "knowledge", "content": "same-text"
    })
    second = agent.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": "instruction", "content": "same-text"
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", first)
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", second)
    agent.comprehend()

    active = [c for c in _concerns(agent) if c.get("content") == "same-text" and c.get("status") != "retired"]
    assert len(active) == 2
    assert {c["gap_identity"] for c in active} == {
        "knowledge|implicit|same-text|turn:none",
        "instruction|implicit|same-text|turn:none",
    }
