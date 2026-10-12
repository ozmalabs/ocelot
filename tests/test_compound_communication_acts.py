from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.communication_evidence import from_semantic_frame
from domains.comprehend_text import comprehend_text
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def _acts(agent, interpretation):
    nodes = agent.inner.neighbours(
        interpretation, "has_communication_act_evidence")
    return [dict(agent.s.node(node)["attrs"]) for node in nodes]


def test_live_text_preserves_greeting_and_polar_question_as_co_acts():
    agent = WorldAdapter(seeds=())
    text = "Good morning, are we ready?"
    message = agent.add_inbound(text, speaker="user")
    comp = comprehend_text(agent, text, kind="question")

    interpretation = agent._record_communication_interpretation(
        message, comp, native_kind="question", speech_act="question")
    attrs = agent.s.node(interpretation)["attrs"]
    acts = _acts(agent, interpretation)

    # The legacy event-level summary still carries the question, while the
    # language adapter's graph evidence keeps the greeting independently true.
    assert attrs["evidence_force"] == "information_request"
    assert [(act["act_type"], act["communicative_force"])
            for act in acts] == [
                ("greeting", "social_action"),
                ("polar_question", "information_request"),
            ]
    assert [act["sequence_index"] for act in acts] == [0, 1]
    assert all(act["authority"] == "language_adapter" for act in acts)

    # The same non-exclusive evidence is available in the serialized turn
    # observation; it is not only an internal node attached during parsing.
    serialized = agent.production_turn_evidence(message)["cognitive_trace"]
    assert [item["attrs"]["act_type"] for item in
            serialized["communication_act_evidence"]] == [
                "greeting", "polar_question"]


def test_native_arbitration_repairs_unsupported_question_without_erasing_greeting():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    text = "Good morning, are we ready?"
    reply = agent.converse(text, speech_act="question")
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]

    assert attrs["cognitive_disposition"] == "repair"
    assert attrs["arbitration_basis"] == (
        "compound_polar_relation_missing_support")
    assert attrs["communicative_force"] == "request_information"
    assert attrs["parsed_predicate"] == "ready"
    assert [act["act_type"] for act in _acts(agent, interpretation)] == [
        "greeting", "polar_question"]
    assert reply != "ERROR: no communicative response could be generated."
    assert agent.s.node(inbound)["attrs"]["compound_response_components"] == [
        "greeting", "repair"]
    assert "?" in reply
    assert "ready" in reply.casefold()
    assert "good morning, are we ready" not in reply.casefold()
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert any(item.get("status") == "released"
               and item.get("semantic_event") == "repair"
               for item in receipts)
    greeting_receipts = [item for item in receipts
                         if item.get("status") == "released"
                         and item.get("semantic_event") == "greeting"]
    assert greeting_receipts
    assert reply.casefold().startswith(
        str(greeting_receipts[0].get("surface") or "").casefold())
    composition_receipt = next((node for node in
                                agent.s.nodes("ProductionGateReceipt")
                                if agent.s.node(node)["attrs"].get(
                                    "turn_message_id") == int(inbound.value)
                                and agent.s.node(node)["attrs"].get(
                                    "status") == "released"
                                and agent.s.node(node)["attrs"].get(
                                    "semantic_event")
                                == "compound_greeting_repair"
                                and agent.s.node(node)["attrs"].get(
                                    "surface") == reply
                                and agent.s.node(node)["attrs"].get(
                                    "parse_back_mode")
                                == "conversation_compound_act_composition.v1"),
                               None)
    assert composition_receipt is not None
    composition_messages = agent.inner.neighbours(
        composition_receipt, "releases")
    assert len(composition_messages) == 1
    assert agent.s.node(composition_messages[0])["attrs"][
        "composition_source"] == (
            "world_adapter_deterministic_join_of_released_components")
    component_messages = agent.inner.neighbours(
        composition_messages[0], "composes")
    assert len(component_messages) == 2


def test_language_neutral_semantic_ingress_preserves_compound_act_evidence():
    agent = WorldAdapter(seeds=())
    evidence = from_semantic_frame({
        "communicative_force": "information_request",
        "communicative_acts": [
            {"act_type": "greeting", "force": "social_action"},
            {"act_type": "polar_question",
             "force": "information_request"},
        ],
    }, provider="language_adapter:compound")
    assert evidence["evidence_force"] == "information_request"
    assert [act["act_type"] for act in
            evidence["evidence_communicative_acts"]] == [
                "greeting", "polar_question"]

    result = agent.ingest_semantic_event({
        "communicative_force": "information_request",
        "communicative_acts": [
            {"act_type": "greeting", "force": "social_action"},
            {"act_type": "polar_question",
             "force": "information_request"},
        ],
    }, provider="language_adapter:compound")
    interpretation = result["interpretation_id"]
    assert agent.s.node(interpretation)["attrs"]["evidence_force"] == \
        "information_request"
    assert [act["act_type"] for act in _acts(agent, interpretation)] == [
        "greeting", "polar_question"]


@pytest.mark.parametrize("frame", [
    {"communicative_force": "information_request", "communicative_acts": []},
    {"communicative_force": "information_request", "communicative_acts": [
        {"act_type": "greeting", "force": "unsupported"}]},
    {"communicative_force": "information_request", "communicative_acts": [
        {"act_type": "surface_phrase", "force": "social_action"}]},
])
def test_compound_act_contract_rejects_ambiguous_or_unsupported_evidence(frame):
    with pytest.raises(ValueError, match="communicative"):
        from_semantic_frame(frame, provider="invalid_adapter")
