"""Phase 4: audience selection and grammar-owned frame realization."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from domains import audience_driven_production as audience
from domains import conversation_action


def test_frame_reply_uses_audience_selection_and_grammar(monkeypatch):
    wa = WorldAdapter(seeds=())
    calls = []
    original = audience.select_utterance

    def counted(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(result)
        return result

    monkeypatch.setattr(audience, "select_utterance", counted)
    frame = {"event": "is", "agent": "dog", "patient": "mammal",
             "tense": "present", "intent": "inform"}
    reply = wa._realize_frame_reply(
        frame, {"id": "user", "observed": False, "known_concepts": []})

    assert reply
    assert "dog" in reply.lower() and "mammal" in reply.lower()
    assert len(calls) == 1
    trace = wa._last_frame_realization
    assert trace["selection"] is calls[0]
    assert trace["result"]["backbone"]
    assert any(item.get("function_word") for item in
               trace["result"]["produce"]["phonological_word"]["words"])


def test_goal_utterance_for_and_action_bridge_share_frame_path():
    wa = WorldAdapter(seeds=())
    frame = {"event": "is", "agent": "dog", "patient": "mammal",
             "tense": "present", "intent": "inform"}

    direct = wa._realize_frame_reply(frame)
    via_utterance = wa.utterance_for(frame)
    via_action = conversation_action.realize_frame_reply(wa, frame)

    assert direct and via_utterance and via_action
    assert "dog" in via_utterance.lower()
    assert "mammal" in via_action.lower()
