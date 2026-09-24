"""Phase 6 production boundary for unresolved world questions."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from evaluation.phase6_production_manifest import EXPLICIT_ERROR  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


@pytest.mark.parametrize(
    "signal",
    [
        "Will it rain today?",
        "What did the monitor report?",
        "Which gate is open?",
    ],
)
def test_unresolved_world_question_returns_explicit_error_and_withheld_receipt(signal):
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        signal,
        speech_act="question",
        context={"interaction_mode": "non_turn"},
    )

    assert reply == EXPLICIT_ERROR
    assert reply != "noted"
    receipts = [
        node for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_information_graph"
    ]
    assert len(receipts) == 1
    attrs = agent.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["semantic_event"] == "request_information"
    assert attrs["semantic_intent"] == "defer"
    assert attrs["recoverable"] is False
    assert "parse_back_not_recoverable" in attrs["withhold_reasons"]


def test_grounded_information_answer_does_not_use_unresolved_world_bridge():
    agent = WorldAdapter(seeds=())
    agent._persist_held_answer("sensor status", "nominal")

    reply = agent.converse(
        "What is the sensor status?",
        speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )

    assert reply == "nominal"
    assert not any(
        agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_world_graph"
        for node in agent.s.nodes("ProductionGateReceipt")
    )


def test_unrelated_surface_cannot_invoke_unresolved_world_bridge():
    agent = WorldAdapter(seeds=())
    inbound = agent.receive_utterance("What did the monitor report?", speech_act="question")
    assert agent._release_unresolved_information_reply(
        inbound, None, "arbitrary reply"
    ) is None
    assert not list(agent.s.nodes("ProductionGateReceipt"))
