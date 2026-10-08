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


def test_exhausted_standalone_unknown_topic_releases_native_repair_not_answer():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "What is a blorf?",
        speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    assert "blorf" in reply.lower()
    assert "what is a blorf" not in reply.lower()
    assert reply.endswith("?")
    interpretation = agent.s.node(
        agent.s.node(agent._last_turn_inbound)["attrs"][
            "communication_interpretation_id"])["attrs"]
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == (
        "failed_standalone_topic_retrieval")
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id")
        == agent._last_turn_inbound.value
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["semantic_event"] == "repair"
    assert receipts[0]["semantic_intent"] == "request"
    assert not any(
        agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_information_graph"
        for node in agent.s.nodes("ProductionGateReceipt")
    )


def test_failed_continuing_topic_request_does_not_use_standalone_repair_rule():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "What is a blorf?",
        speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"},
    )

    assert reply == "ERROR: no communicative response could be generated."
    interpretation = agent.s.node(
        agent.s.node(agent._last_turn_inbound)["attrs"][
            "communication_interpretation_id"])["attrs"]
    assert interpretation["cognitive_disposition"] is None
    assert interpretation["arbitration_basis"] != (
        "failed_standalone_topic_retrieval")
    assert not any(
        agent.s.node(node)["attrs"].get("status") == "released"
        and agent.s.node(node)["attrs"].get("semantic_event") == "repair"
        and agent.s.node(node)["attrs"].get("turn_message_id")
        == agent._last_turn_inbound.value
        for node in agent.s.nodes("ProductionGateReceipt")
    )


@pytest.mark.parametrize("signal", [
    "Will it rain today?",
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


def test_non_turn_blocked_world_question_closes_without_reply_slot():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "What is beyond the wall?", speech_act="question",
        context={"interaction_mode": "non_turn"},
    )

    assert reply == ""
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    assert agent.s.node(interpretation)["attrs"][
        "cognitive_disposition"] == "blocked"
    assert agent.s.node(inbound)["attrs"]["turn_reply_surface"] == ""


def test_event_bound_reported_content_answers_with_source_attribution():
    """Recall an utterance without upgrading its proposition to world fact."""
    agent = WorldAdapter()
    from substrate.boot_all import load_all_seeds
    report = load_all_seeds(
        agent, seed_ids=["communication_reported_content_recall"])
    assert report["selection_complete"]
    assert "communication_reported_content_recall" in report["order"]

    agent.converse(
        "The monitor reports a fault.", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )
    source_message = agent._last_turn_inbound
    source_event = agent.s.node(source_message)["attrs"]["discourse_event_id"]

    reply = agent.converse(
        "What did the monitor report?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"},
    )
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    interpretation = attrs["communication_interpretation_id"]
    interpretation_attrs = agent.s.node(interpretation)["attrs"]

    assert reply == "Earlier, you said: The monitor reports a fault."
    assert interpretation_attrs["cognitive_disposition"] == "answer"
    assert interpretation_attrs["arbitration_basis"] == (
        "event_bound_reported_content_recall")
    assert interpretation_attrs["grounding_status"] == "unresolved"
    assert interpretation_attrs["reported_content_epistemic_status"] == (
        "attributed_source_utterance")
    assert interpretation_attrs["grounding_status"] == "unresolved"
    assert interpretation_attrs["reported_content_evidence_path"].startswith(
        "ReportedContentEvidence:")
    assert "epistemic_status=attributed_source_utterance" in (
        interpretation_attrs["reported_content_evidence_path"])
    evidence = list(agent.inner.neighbours(
        interpretation, "has_reported_content_evidence"))
    assert len(evidence) == 1
    evidence = evidence[0]
    assert source_event in agent.inner.neighbours(
        evidence, "from_source_event")
    assert source_message in agent.inner.neighbours(
        evidence, "from_source_message")
    assert inbound in agent.inner.neighbours(evidence, "for_request")
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["parse_back_mode"] == (
        "conversation_reported_content_graph")


def test_async_reported_content_release_matches_the_sync_graph_proof():
    """Daemon release uses the same event/source check and receipt boundary."""
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter()
    load_all_seeds(
        agent, seed_ids=["communication_reported_content_recall"])
    context = {"interaction_mode": "turn_compatible",
               "interaction_relation": "response"}
    source = agent.ingest_turn(
        "The monitor reports a fault.", speech_act="statement",
        context=context)
    agent.comprehend()
    agent.release_graph_selected_response(source)
    source_event = agent.s.node(source)["attrs"]["discourse_event_id"]

    query = agent.ingest_turn(
        "What did the monitor report?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"})
    agent.comprehend()
    reply = agent.release_graph_selected_response(query)

    assert reply == "Earlier, you said: The monitor reports a fault."
    attrs = agent.s.node(query)["attrs"]
    interpretation = attrs["communication_interpretation_id"]
    evidence = agent.inner.neighbours(
        interpretation, "has_reported_content_evidence")
    assert len(evidence) == 1
    evidence = evidence[0]
    assert source_event in agent.inner.neighbours(
        evidence, "from_source_event")
    assert query in agent.inner.neighbours(evidence, "for_request")
    assert agent.s.node(interpretation)["attrs"]["grounding_status"] == "unresolved"
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("turn_message_id")
                == int(query.value)]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["parse_back_mode"] == (
        "conversation_reported_content_graph")


def test_reported_content_readback_rejects_tampered_relation_evidence():
    """Production rechecks evidence against the source parse before release."""
    from substrate.boot_all import load_all_seeds

    class TamperedEvidenceAdapter(WorldAdapter):
        def _release_reported_content_recall(self, inbound):
            interpretation = self.s.node(inbound)["attrs"][
                "communication_interpretation_id"]
            evidence = self.inner.neighbours(
                interpretation, "has_reported_content_evidence")[0]
            self.inner.set_attr(evidence, "content", "forged content")
            return super()._release_reported_content_recall(inbound)

    agent = TamperedEvidenceAdapter()
    load_all_seeds(
        agent, seed_ids=["communication_reported_content_recall"])
    agent.converse(
        "The monitor reports a fault.", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    reply = agent.converse(
        "What did the monitor report?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"},
    )

    assert reply == "ERROR: no communicative response could be generated."
    assert not any(
        agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_reported_content_graph"
        and agent.s.node(node)["attrs"].get("status") == "released"
        for node in agent.s.nodes("ProductionGateReceipt"))


@pytest.mark.parametrize(
    "source,query_relation",
    [
        ("The monitor detected a fault.", "What did the monitor report?"),
        ("The sensor reports a fault.", "What did the monitor report?"),
    ],
)
def test_reported_content_recall_requires_matching_event_relation_and_subject(
        source, query_relation):
    """A nearby claim with a different predicate or subject is not an answer."""
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter()
    load_all_seeds(
        agent, seed_ids=["communication_reported_content_recall"])
    agent.converse(
        source, speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )
    reply = agent.converse(
        query_relation, speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"},
    )

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    assert reply == "ERROR: no communicative response could be generated."
    assert agent.s.nodes("ReportedContentEvidence") == []
    assert agent.s.node(interpretation)["attrs"].get(
        "arbitration_basis") != "event_bound_reported_content_recall"
    assert not any(agent.s.node(node)["attrs"].get("parse_back_mode")
                   == "conversation_reported_content_graph"
                   and agent.s.node(node)["attrs"].get("status") == "released"
                   for node in agent.s.nodes("ProductionGateReceipt"))


def test_weather_question_without_a_world_provider_is_not_grounded_by_form():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "What is the weather?", speech_act="question",
        context={"interaction_mode": "turn_compatible"},
    )

    assert reply == "ERROR: no communicative response could be generated."
    assert not any(
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
    # The object referent is now selected from the typed action relation and
    # can be graph-grounded independently; that does not grant access
    # authority or release an answer.
    assert attrs["grounding_status"] == "candidate_grounded"
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_information_graph"
    ]
    assert receipts
    assert all(item["status"] == "withheld" for item in receipts)


def test_turn_compatible_route_recommendation_without_authority_is_graph_blocked():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Should we use the north route?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})

    assert "guide that decision" in reply.lower()
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["authority_status"] == "missing"
    assert attrs["grounding_status"] in {
        "candidate_grounded", "authority_missing"}
    assert attrs["cognitive_disposition"] == "blocked"
    assert attrs["cognitive_goal"] == "blocked"
    assert attrs["arbitration_basis"] == "missing_permission_authority"
    assert attrs["language_authority_request_kind"] == \
        "decision_recommendation"
    replies = [node for node in agent.agent_outbound_messages()
               if inbound in agent.responds_to(node)]
    assert any(
        str(agent.s.node(act)["attrs"].get("name") or "") == "clarification"
        for reply_node in replies
        for act in agent.inner.neighbours(reply_node, "has_speech_act")
        if agent.s.has_node(act))
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id")
        == int(inbound.value)
    ]
    assert any(item["status"] == "released"
               and item["semantic_event"] == "repair"
               for item in receipts)


def test_unanswered_learning_request_asks_for_grounding_context_not_weather():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Will it rain today?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "turn_compatible"})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "learn"
    assert "information" in reply.lower() and "answer" in reply.lower()
    assert "rain" not in reply.lower()
    replies = [node for node in agent.agent_outbound_messages()
               if inbound in agent.responds_to(node)]
    assert any(
        str(agent.s.node(act)["attrs"].get("name") or "") == "clarification"
        for reply_node in replies
        for act in agent.inner.neighbours(reply_node, "has_speech_act")
        if agent.s.has_node(act))


def test_selected_uncertainty_learning_request_asks_for_context_not_answer():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "I am not sure which reading is correct.", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "learn"
    requests = [
        node for node in agent.s.nodes("InformationLearningRequest")
        if inbound in agent.inner.neighbours(node, "for_event")
    ]
    assert len(requests) == 1
    request_attrs = agent.s.node(requests[0])["attrs"]
    assert request_attrs["source_policy"] == "unselected"
    assert request_attrs["answer_authority"] == "none"
    assert "information" in reply.lower() and "answer" in reply.lower()
    assert "reading" not in reply.lower()
    assert agent.reply_turn_trace(int(inbound.value)).get(
        "answer_commitment") is None
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id") == int(inbound.value)
    ]
    assert any(item["status"] == "released"
               and item["semantic_event"] == "repair"
               for item in receipts)


def test_missing_world_information_request_clarifies_without_claiming_answer():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "How far is the valley?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "blocked"
    assert attrs["arbitration_basis"] == "missing_world_information_request"
    assert "information" in reply.lower() and "answer" in reply.lower()
    assert "valley" not in reply.lower()
    assert attrs.get("answer_commitment") is None
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id") == int(inbound.value)
    ]
    assert any(item["status"] == "released"
               and item["semantic_event"] == "repair"
               for item in receipts)


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
        context={"interaction_mode": "non_turn"}) == ""
    reply = agent.converse(
        "Why did it close?", speech_act="question",
        context={"interaction_mode": "turn_compatible"})
    assert reply == (
        "What event or evidence would help establish what caused it to close?")
    assert reply != "The gate is open.", (
        "a topic summary must not be substituted for missing causal evidence")
    inbound = agent._last_turn_inbound
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert all("Donald Henry Pleasence" not in str(
        agent.s.node(node)["attrs"].get("surface") or "")
        for node in agent.s.nodes("ProductionGateReceipt"))
    assert any(receipt.get("parse_back_mode") == "conversation_action_graph"
               and receipt.get("status") == "released"
               and receipt.get("surface") == reply
               for receipt in receipts)


def test_native_causal_repair_asks_for_missing_event_evidence():
    """A graph-selected continuation repair asks for evidence, not a fact."""
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent._persist_held_answer("gate", "The gate is open.")
    agent.converse(
        "Which gate is open?", speech_act="question",
        context={"interaction_mode": "non_turn"})
    agent.converse(
        "What is beyond the wall?", speech_act="question",
        context={"interaction_mode": "non_turn"})

    reply = agent.converse(
        "Why did it close?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "continuation"})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    assert agent.s.node(interpretation)["attrs"].get(
        "arbitration_basis") == "missing_causal_relation_with_anaphor"
    assert reply == (
        "What event or evidence would help establish what caused it to close?")
    assert "the gate is open" not in reply.lower()
    receipts = [agent.s.node(node)["attrs"] for node in agent.s.nodes(
        "ProductionGateReceipt") if agent.s.node(node)["attrs"].get(
            "parse_back_mode") == "conversation_action_graph"]
    assert any(receipt.get("status") == "released"
               and receipt.get("surface") == reply
               for receipt in receipts)
    agent.comprehend()
    agent.comprehend()
    causal_replies = [node for node in agent.agent_outbound_messages()
                      if inbound in agent.responds_to(node)
                      and agent.s.node(node)["attrs"].get(
                          "native_causal_repair_reply") == 1.0]
    assert len(causal_replies) == 1, (
        "re-entering the native fixpoint must not duplicate the repair pair")


@pytest.mark.parametrize(
    ("text", "relation"),
    [("I could—", "overlap"),
     ("That happened after the reset.", "continuation")],
)
def test_native_defer_without_response_slot_closes_silently(text, relation):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        text, speech_act=WorldAdapter.classify_speech_act(text),
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": relation})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "defer"
    assert reply == ""
    assert agent.reply_turn_trace(inbound) is None or not any(
        agent.s.node(node)["attrs"].get("status") == "released"
        and agent.s.node(node)["attrs"].get("turn_message_id") == int(inbound.value)
        for node in agent.s.nodes("ProductionGateReceipt"))


def test_full_corpus_context_releases_native_causal_repair_before_generic_askback():
    """A bounded scheduler must settle the specific graph repair first."""
    from evaluation.conversational_manifold_phase0 import load_corpus
    from evaluation.phase8_corpus_runner import _runtime_context, _speech_act

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    target = "question_followup"
    for event in load_corpus()["events"]:
        for held in (event.get("setup") or {}).get("held_answers") or []:
            agent._persist_held_answer(
                str(held["topic"]), str(held["answer"]))
        reply = agent.converse(
            event["signal"], speech_act=_speech_act(event),
            context=_runtime_context(event))
        if event["id"] != target:
            continue

        inbound = agent._last_turn_inbound
        attrs = agent.s.node(inbound)["attrs"]
        assert reply == (
            "What event or evidence would help establish what caused it to close?")
        assert attrs.get("communication_route") == \
            "causal_evidence_repair_graph"
        receipts = [agent.s.node(node)["attrs"]
                    for node in agent.s.nodes("ProductionGateReceipt")
                    if agent.s.node(node)["attrs"].get(
                        "turn_message_id") == int(inbound.value)]
        assert len(receipts) == 1
        assert receipts[0]["status"] == "released"
        assert receipts[0]["surface"] == reply
        assert receipts[0]["parse_back_mode"] == "conversation_action_graph"
        assert not any("Might I ask which it" in str(
            receipt.get("surface") or "") for receipt in receipts)
        event_id = attrs.get("discourse_event_id")
        partial_sources = [agent.s.node(node)["attrs"]
                           for node in agent.s.nodes("Phase4PartialEvidence")
                           if agent.s.node(node)["attrs"].get(
                               "communication_event_id") == event_id]
        assert partial_sources
        assert all(source.get("phase4_dimensions_present") == ["grounding"]
                   for source in partial_sources)
        return
    pytest.fail(f"corpus does not contain event {target!r}")
