"""Phase 6 bounded production coverage for grounded information answers."""
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
from substrate.boot_all import load_all_seeds  # noqa: E402


def _grounded_agent():
    agent = WorldAdapter(seeds=())
    agent._persist_held_answer("sensor status", "nominal")
    return agent


def test_info_status_releases_only_graph_grounded_answer():
    agent = _grounded_agent()
    reply = agent.converse(
        "What is the sensor status?",
        speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )

    assert reply == "nominal"
    receipts = [
        node for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_information_graph"
    ]
    assert len(receipts) == 1
    attrs = agent.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "released"
    assert attrs["surface"] == reply
    assert attrs["semantic_event"] == "answer_topic"
    assert attrs["semantic_intent"] == "inform"
    assert attrs["coverage"] == 1.0
    released = list(agent.inner.neighbours(receipts[0], "releases"))
    assert released
    assert agent._last_turn_inbound in list(
        agent.inner.neighbours(released[0], "comprehends"))


def test_information_surface_mismatch_is_withheld_and_returns_error():
    agent = _grounded_agent()
    agent.converse(
        "What is the sensor status?",
        speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )
    inbound = agent._last_turn_inbound

    assert agent._release_information_reply(inbound, "fabricated") is None
    receipts = [
        node for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_information_graph"
    ]
    assert len(receipts) == 2
    attrs = agent.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "released"
    withheld = agent.s.node(receipts[1])["attrs"]
    assert withheld["status"] == "withheld"
    assert "parse_back_not_recoverable" in withheld["withhold_reasons"]


def test_unresolved_info_unknown_is_not_promoted_to_release():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "What is a blorf?",
        speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )

    assert reply == "ERROR: no communicative response could be generated."
    withheld = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_information_graph"
    ]
    assert withheld
    assert all(item["status"] == "withheld" for item in withheld)
    assert not any(
        agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_information_graph"
        for node in agent.s.nodes("ProductionGateReceipt")
    )


@pytest.mark.parametrize("signal", [
    "Will it rain today?",
    "What is beyond the wall?",
    "Where did you learn that?",
])
def test_unresolved_information_families_use_error_and_withheld_receipt(signal):
    agent = WorldAdapter(seeds=())
    reply = agent.converse(signal, speech_act="question",
                           context={"interaction_mode": "non_turn"})

    assert reply == "ERROR: no communicative response could be generated."
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_information_graph"
    ]
    assert receipts
    assert all(item["status"] == "withheld" for item in receipts)


def test_grounded_weather_question_is_not_downgraded_to_unresolved_error():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "What is the weather?", speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )

    assert reply
    assert reply != "ERROR: no communicative response could be generated."
    assert any(
        agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_information_graph"
        and agent.s.node(node)["attrs"].get("status") == "released"
        for node in agent.s.nodes("ProductionGateReceipt")
    )


def test_permission_request_without_authority_is_blocked_fail_closed():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Can I access the sealed room?", speech_act="question",
        context={"interaction_mode": "non_turn"})

    assert reply == "ERROR: no communicative response could be generated."
    interpretations = list(agent.s.nodes("CommunicationInterpretation"))
    assert interpretations
    attrs = agent.s.node(interpretations[-1])["attrs"]
    assert attrs["authority_status"] == "missing"
    assert attrs["grounding_status"] == "authority_missing"
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_information_graph"
    ]
    assert receipts
    assert all(item["status"] == "withheld" for item in receipts)


def test_declarative_ability_offer_is_not_reclassified_as_permission_request():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "I can check the gate.", speech_act="statement",
        context={"interaction_mode": "non_turn"})
    assert reply
    interpretation = list(agent.s.nodes("CommunicationInterpretation"))[-1]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs.get("authority_status") != "missing"




def test_anaphoric_relation_without_causal_evidence_cannot_release_lexical_answer():
    """A pronoun's topic binding does not answer a new causal relation."""
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent._persist_held_answer("gate", "The gate is open.")
    assert agent.converse(
        "Which gate is open?", speech_act="question",
        context={"interaction_mode": "non_turn"}) == "The gate is open."
    assert agent.converse(
        "What is beyond the wall?", speech_act="question",
        context={"interaction_mode": "non_turn"}) == (
            "ERROR: no communicative response could be generated.")
    reply = agent.converse(
        "Why did it close?", speech_act="question",
        context={"interaction_mode": "turn_compatible"})
    assert reply == "ERROR: no communicative response could be generated."
    assert all("Donald Henry Pleasence" not in str(
        agent.s.node(node)["attrs"].get("surface") or "")
        for node in agent.s.nodes("ProductionGateReceipt"))
    assert any(
        agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_information_graph"
        and agent.s.node(node)["attrs"].get("status") == "withheld"
        for node in agent.s.nodes("ProductionGateReceipt"))
