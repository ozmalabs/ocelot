"""Phase 6 social surfaces require graph commitment and semantic readback."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402


@pytest.mark.parametrize(
    ("event_id", "signal", "speech_act"),
    [
        ("social_greeting", "Hello.", "greeting"),
        ("social_thanks", "Thank you.", "thanks"),
        # The fixed Phase 8 social adapter presents all five substantive
        # social events to the social adjacency faculty as ``greeting``;
        # preserve that existing arbitration contract here.
        ("social_goodbye", "I am leaving now.", "greeting"),
        ("social_question", "Good morning, are we ready?", "greeting"),
        ("social_address", "Operator, please listen.", "greeting"),
    ],
)
def test_substantive_social_event_releases_existing_graph_commitment(
        event_id, signal, speech_act):
    wa = WorldAdapter(seeds=())
    reply = wa.converse(
        signal, speech_act=speech_act,
        context={"interaction_mode": "turn_compatible"},
    )

    assert reply
    assert reply != "noted"
    receipt_nodes = [
        node for node in wa.s.nodes("ProductionGateReceipt")
        if wa.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_social_graph"
    ]
    assert len(receipt_nodes) == 1, event_id
    receipt = wa.s.node(receipt_nodes[0])["attrs"]
    assert receipt["status"] == "released"
    assert receipt["surface"] == reply
    assert receipt["semantic_intent"] == "coordinate_socially"
    assert receipt["recoverable"] is True

    inbound = wa._last_turn_inbound
    outbound = list(wa.inner.neighbours(receipt_nodes[0], "releases"))
    assert outbound
    assert inbound in wa.responds_to(outbound[0])


def test_social_surface_cannot_release_without_semantic_act_match():
    wa = WorldAdapter(seeds=())
    inbound = wa.receive_utterance("Hello.", speech_act="greeting")
    wa.enable_replies()
    wa.comprehend()
    reply_mid = next(
        node for node in wa.agent_outbound_messages()
        if inbound in wa.responds_to(node)
    )

    assert wa._release_social_reply(inbound, reply_mid, "arbitrary reply") is None
    assert list(wa.s.nodes("ProductionGateReceipt")) == []
