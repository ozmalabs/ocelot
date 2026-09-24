"""Phase 6T: same-event identical releases are idempotent at the gate."""
from __future__ import annotations

from domains.production_gate import release_if_gated
from substrate.world_adapter import WorldAdapter


def test_same_turn_duplicate_release_with_distinct_commitments_is_collapsed():
    agent = WorldAdapter(seeds=())
    inbound = agent.s.add_node("Message", {"message_id": "phase6t"})
    agent._last_turn_inbound = inbound
    frame = {"event": "inform", "agent": "agent", "patient": "route",
             "intent": "inform"}
    gate = {"recoverable": True, "coverage": 1.0,
            "mode": "legacy_structural_readback"}
    first = agent.s.add_node("Committed", {"utterance": "route"})
    second = agent.s.add_node("Committed", {"utterance": "route"})
    assert release_if_gated(agent, frame, "route", gate, first) == "route"
    assert release_if_gated(agent, frame, "route", gate, second) == "route"
    receipts = list(agent.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    assert agent.s.node(receipts[0])["attrs"]["turn_message_id"] == int(inbound.value)


def test_competing_semantic_events_are_not_collapsed_by_turn_id():
    agent = WorldAdapter(seeds=())
    inbound = agent.s.add_node("Message", {"message_id": "phase6t-competing"})
    agent._last_turn_inbound = inbound
    gate = {"recoverable": True, "coverage": 1.0,
            "mode": "legacy_structural_readback"}
    for event in ("inform", "answer_topic"):
        frame = {"event": event, "agent": "agent", "patient": "route",
                 "intent": "inform"}
        committed = agent.s.add_node("Committed", {"utterance": "route"})
        assert release_if_gated(agent, frame, "route", gate, committed)
    assert len(agent.s.nodes("ProductionGateReceipt")) == 2
