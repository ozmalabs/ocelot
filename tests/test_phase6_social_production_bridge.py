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


def test_standalone_farewell_uses_typed_social_adjacency_and_receipt():
    from substrate.boot_all import load_all_seeds

    signal = "I am leaving now."
    assert WorldAdapter.classify_speech_act(signal) == "farewell"
    assert WorldAdapter.classify_speech_act(
        "I am leaving early to collect the equipment.") == "statement"
    assert WorldAdapter.classify_speech_act("I am leaving now?") == "question"

    wa = WorldAdapter()
    report = load_all_seeds(
        wa, seed_ids=["communication_social_reply"])
    assert report["selection_complete"]
    reply = wa.converse(
        signal,
        speech_act=wa.classify_speech_act(signal),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    inbound = wa._last_turn_inbound
    interpretation = wa.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = wa.s.node(interpretation)["attrs"]
    assert reply == "goodbye"
    assert attrs["evidence_force"] == "social_action"
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["arbitration_basis"] == "standalone_social_farewell"
    receipts = [wa.s.node(node)["attrs"] for node in
                wa.s.nodes("ProductionGateReceipt")
                if wa.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["parse_back_mode"] == "conversation_social_graph"


def test_graph_typed_action_offer_uses_acceptance_adjacency_and_receipt():
    from substrate.boot_all import load_all_seeds

    wa = WorldAdapter()
    load_all_seeds(wa, seed_ids=["communication_social_reply"])
    wa.s.add_node("Concept", {
        "name": "can", "definition": "modal indicating ability or permission",
    })
    wa.s.add_node("Concept", {
        "name": "sensor", "definition": "device that detects a physical quantity",
    })
    signal = "I can inspect the sensor."
    reply = wa.converse(
        signal, speech_act=wa.classify_speech_act(signal),
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    inbound = wa._last_turn_inbound
    interpretation = wa.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = wa.s.node(interpretation)["attrs"]
    assert reply == "that would be helpful"
    assert attrs["evidence_communicative_act"] == "ability_action_offer"
    assert attrs["language_communicative_act_evidence"] == (
        "first_person_ability_action_offer")
    assert attrs["offer_target_status"] == "concept_available"
    assert attrs["grounding_status"] == "candidate_grounded"
    assert attrs["grounding_evidence_path"] == (
        "CommunicationInterpretation -> "
        "typed_ability_action_offer.target -> Concept.referent")
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["arbitration_basis"] == "typed_ability_action_offer"
    assert [wa.s.node(act)["attrs"].get("name") for act in
            wa.inner.neighbours(inbound, "has_speech_act")] == ["offer"]
    responses = [node for node in wa.agent_outbound_messages()
                 if inbound in wa.responds_to(node)]
    assert len(responses) == 1
    assert [wa.s.node(act)["attrs"].get("name") for act in
            wa.inner.neighbours(responses[0], "has_speech_act")] == [
                "acceptance"]
    receipts = [wa.s.node(node)["attrs"] for node in
                wa.s.nodes("ProductionGateReceipt")
                if wa.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["parse_back_mode"] == "conversation_social_graph"


def test_daemon_releases_graph_selected_typed_offer_acceptance():
    from substrate.boot_all import load_all_seeds

    wa = WorldAdapter()
    load_all_seeds(wa)
    inbound = wa.ingest_turn(
        "I can inspect the sensor.", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )
    wa.tick()
    wa.comprehend()
    reply = wa.release_graph_selected_response(inbound)

    assert reply == "that would be helpful"
    assert wa.graph_turn_reply(inbound) == reply
    attrs = wa.s.node(inbound)["attrs"]
    interpretation = wa.s.node(attrs["communication_interpretation_id"])["attrs"]
    assert interpretation["arbitration_basis"] == "typed_ability_action_offer"
    assert interpretation["grounding_status"] == "candidate_grounded"
    assert interpretation["grounding_evidence_path"] == (
        "CommunicationInterpretation -> "
        "typed_ability_action_offer.target -> Concept.referent")
    receipts = [wa.s.node(node)["attrs"] for node in
                wa.s.nodes("ProductionGateReceipt")
                if wa.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["semantic_intent"] == "coordinate_socially"
    assert receipts[0]["parse_back_mode"] == "conversation_social_graph"
    assert wa.s.node(inbound)["attrs"].get("action_execution_goal_id") is None


def test_unresolved_action_offer_is_repaired_without_acceptance_reply():
    from substrate.boot_all import load_all_seeds

    wa = WorldAdapter()
    load_all_seeds(wa, seed_ids=["communication_social_reply"])
    wa.s.add_node("Concept", {
        "name": "can", "definition": "modal indicating ability or permission",
    })
    signal = "I can inspect the sensor."
    reply = wa.converse(
        signal, speech_act=wa.classify_speech_act(signal),
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    inbound = wa._last_turn_inbound
    interpretation = wa.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = wa.s.node(interpretation)["attrs"]
    assert attrs["evidence_communicative_act"] == "ability_action_offer"
    assert attrs["offer_target_status"] == "unresolved"
    assert attrs["evidence_force"] == "social_action"
    assert attrs["cognitive_disposition"] == "repair"
    assert attrs["arbitration_basis"] == "unresolved_ability_offer_target"
    assert attrs["grounding_status"] == "unresolved"
    assert [wa.s.node(act)["attrs"].get("name") for act in
            wa.inner.neighbours(inbound, "has_speech_act")] == ["offer"]
    assert reply != "thank you; please do"
    assert wa.s.node(inbound)["attrs"]["communication_route"] == \
        "unresolved_offer_repair_graph"
    repair_receipts = [wa.s.node(node)["attrs"] for node in
                       wa.s.nodes("ProductionGateReceipt")
                       if wa.s.node(node)["attrs"].get("turn_message_id")
                       == int(inbound.value)]
    assert len(repair_receipts) == 1
    assert repair_receipts[0]["status"] == "released"
    assert repair_receipts[0]["parse_back_mode"] == \
        "conversation_action_graph"
    assert not any(
        wa.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_social_graph"
        and wa.s.node(node)["attrs"].get("status") == "released"
        for node in wa.s.nodes("ProductionGateReceipt"))
    assert reply


def test_non_turn_incomplete_action_offer_has_no_reply_slot():
    from substrate.boot_all import load_all_seeds

    wa = WorldAdapter()
    load_all_seeds(wa)
    signal = "I can check, if that helps."
    reply = wa.converse(
        signal, speech_act=wa.classify_speech_act(signal),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    inbound = wa._last_turn_inbound
    interpretation = wa.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = wa.s.node(interpretation)["attrs"]
    assert attrs["evidence_communicative_act"] == "ability_action_offer"
    assert attrs["offer_target_status"] == "missing"
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["arbitration_basis"] == "incomplete_ability_offer_deferred"
    assert reply == ""
    assert wa.graph_turn_reply_expectation(inbound) == {
        "status": "not_expected", "expected_response_acts": [],
        "reason": "native_non_turn_defer"}
    assert wa.graph_turn_reply(inbound) is None
    assert not any(
        wa.s.node(node)["attrs"].get("status") == "released"
        and wa.s.node(node)["attrs"].get("turn_message_id") == int(inbound.value)
        for node in wa.s.nodes("ProductionGateReceipt"))
    assert not any(
        inbound in wa.responds_to(node)
        and wa.s.node(node)["attrs"].get("text") == "that would be helpful"
        and not wa.s.node(node)["attrs"].get("turn_reply_suppressed")
        for node in wa.agent_outbound_messages())


def test_typed_nonunderstanding_report_releases_a_clarification():
    from domains.comprehend_text import comprehend_text
    from substrate.boot_all import load_all_seeds

    wa = WorldAdapter(seeds=())
    load_all_seeds(wa)
    signal = "I did not understand that."
    reply = wa.converse(
        signal, speech_act=wa.classify_speech_act(signal),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "response"},
    )

    inbound = wa._last_turn_inbound
    interpretation = wa.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = wa.s.node(interpretation)["attrs"]
    assert attrs["evidence_force"] == "repair_or_defer"
    assert attrs["evidence_communicative_act"] == "nonunderstanding_report"
    assert attrs["language_repair_evidence"] == "nonunderstanding_report"
    assert attrs["cognitive_disposition"] == "repair"
    assert attrs["arbitration_basis"] == "typed_nonunderstanding_report"
    assert wa.s.node(inbound)["attrs"]["communication_route"] == \
        "nonunderstanding_repair_graph"
    assert reply == "What part was unclear?"
    clarification = [node for node in wa.agent_outbound_messages()
                     if inbound in wa.responds_to(node)]
    selected = [node for node in clarification
                if wa.s.node(node)["attrs"].get(
                    "native_action_reply_plan") == "repair"]
    assert len(selected) == 1
    assert [wa.s.node(act)["attrs"].get("name") for act in
            wa.inner.neighbours(selected[0], "has_speech_act")] == [
                "clarification"]
    receipts = [wa.s.node(node)["attrs"] for node in
                wa.s.nodes("ProductionGateReceipt")
                if wa.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["parse_back_mode"] == "conversation_action_graph"

    # The typed act requires both parsed first-person agency and negated
    # understanding; nearby assertions must not inherit it.
    for control in ("They did not understand that.",
                    "I did understand that."):
        parsed = comprehend_text(wa, control, kind="statement")
        control_evidence = (parsed.dispatch or {}).get(
            "language_evidence") or {}
        assert control_evidence.get("communicative_act") != \
            "nonunderstanding_report"
