"""Phase 6 production boundary for graph-authored question responses."""
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


def _receipts(agent):
    return [
        node for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_question_response_graph"
    ]


def test_question_response_without_grounded_content_exposes_explicit_error():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "Did the sensor report it?", speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )

    assert reply == EXPLICIT_ERROR
    assert not _receipts(agent)
    inbound_attrs = agent.s.node(agent._last_turn_inbound)["attrs"]
    assert inbound_attrs["adjacency_replied_act"] == "answer"
    interpretation = inbound_attrs["communication_interpretation_id"]
    assert agent.s.node(interpretation)["attrs"]["interaction_mode"] == "turn_compatible"


def test_question_response_requires_both_graph_commitments():
    agent = WorldAdapter(seeds=())
    inbound = agent.receive_utterance(
        "Did the sensor report it?", speech_act="question")

    assert agent._release_question_response_reply(
        inbound, "arbitrary reply") is None
    assert not _receipts(agent)


def test_question_response_surface_mismatch_is_not_released():
    agent = WorldAdapter(seeds=())
    agent.converse(
        "Did the sensor report it?", speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )
    inbound = agent._last_turn_inbound

    assert agent._release_question_response_reply(inbound, "fabricated") is None
    receipts = _receipts(agent)
    assert len(receipts) == 1
    withheld = agent.s.node(receipts[0])["attrs"]
    assert withheld["status"] == "withheld"
    assert "parse_back_not_recoverable" in withheld["withhold_reasons"]


def test_non_response_question_does_not_use_response_bridge():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "What is beyond the wall?", speech_act="question",
        context={"interaction_mode": "non_turn"},
    )

    assert reply == EXPLICIT_ERROR
    assert not _receipts(agent)
