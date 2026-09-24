"""Phase 6T: native partial-event defer prevents forced release."""
from __future__ import annotations

from evaluation.phase6_production_manifest import EXPLICIT_ERROR
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_typed_overlap_fragment_defers_without_repair_receipt():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Thanks, I—", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "overlap", "literal_form": "fragment"},
    )
    assert reply == EXPLICIT_ERROR
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    interpretation = agent.s.node(attrs["communication_interpretation_id"])["attrs"]
    assert interpretation["cognitive_disposition"] == "defer"
    assert attrs["communication_route"] == "defer"
    assert not [node for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("status") == "released"]
