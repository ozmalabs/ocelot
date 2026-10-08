"""Phase 6A: production release must carry cognitive evidence."""
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
from domains.production_gate import (  # noqa: E402
    legacy_readback_gate,
    release_if_gated,
)


def _agent():
    return WorldAdapter(seeds=())


def _frame():
    return {"event": "is", "agent": "dog", "patient": "mammal",
            "tense": "present", "intent": "inform"}


def test_release_requires_selected_semantics_parseback_and_commitment():
    wa = _agent()
    committed = wa.s.add_node("Committed", {"utterance": "The dog is a mammal"})
    gate = {"recoverable": True, "coverage": 1.0,
            "mode": "grounded_comprehension"}

    surface = release_if_gated(wa, _frame(), "The dog is a mammal", gate, committed)

    assert surface == "The dog is a mammal"
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "released"
    assert attrs["semantic_event"] == "is"
    assert attrs["parse_back_mode"] == "grounded_comprehension"
    assert committed in list(wa.inner.neighbours(receipts[0], "releases"))


def test_parseback_gate_checks_every_item_in_a_list_semantic_role():
    frame = {"event": "organised", "patient": ["north area", "south area"]}
    complete = legacy_readback_gate(
        frame, "Organised into north area and south area.",
        evidence_keys=("event", "patient"))
    incomplete = legacy_readback_gate(
        frame, "Organised into north area.",
        evidence_keys=("event", "patient"))

    assert complete["recoverable"] is True
    assert complete["coverage"] == 1.0
    assert incomplete["recoverable"] is False
    assert incomplete["missing"] == ["south area"]


def test_release_receipt_preserves_each_list_semantic_content_item():
    wa = _agent()
    frame = {"event": "organised", "agent": "I",
             "patient": ["north area", "south area"], "intent": "inform"}
    committed = wa.s.add_node("SelectedAnswer", {"faculty": "self_organisation"})
    gate = {"recoverable": True, "coverage": 1.0, "mode": "list_readback"}

    assert release_if_gated(
        wa, frame, "I am organised into north area and south area.",
        gate, committed)

    receipt = next(iter(wa.s.nodes("ProductionGateReceipt")))
    assert wa.s.node(receipt)["attrs"]["semantic_content"] == [
        "I", "north area", "south area"]
    assert wa.s.node(receipt)["attrs"]["semantic_event"] == "organised"


def test_repeated_release_for_same_commitment_is_idempotent():
    wa = _agent()
    committed = wa.s.add_node("Committed", {"utterance": "The dog is a mammal"})
    gate = {"recoverable": True, "coverage": 1.0,
            "mode": "grounded_comprehension"}
    assert release_if_gated(wa, _frame(), "The dog is a mammal", gate, committed)
    assert release_if_gated(wa, _frame(), "The dog is a mammal", gate, committed)
    assert len(wa.s.nodes("ProductionGateReceipt")) == 1


@pytest.mark.parametrize("frame, gate, committed", [
    ({}, {"recoverable": True}, True),
    (_frame(), {"recoverable": False}, True),
    (_frame(), {"recoverable": True}, None),
])
def test_release_withholds_when_any_cognitive_evidence_is_missing(frame, gate, committed):
    wa = _agent()
    assert release_if_gated(wa, frame, "The dog is a mammal", gate, committed) is None
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["withhold_reasons"]
    assert not list(wa.inner.neighbours(receipts[0], "releases"))


def test_forbidden_fallback_surface_is_withheld_even_with_other_evidence():
    wa = _agent()
    committed = wa.s.add_node("Committed", {"utterance": "noted"})
    gate = {"recoverable": True, "coverage": 1.0, "mode": "recognizer"}

    assert release_if_gated(wa, _frame(), "noted", gate, committed) is None
    receipt = list(wa.s.nodes("ProductionGateReceipt"))[0]
    attrs = wa.s.node(receipt)["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["withhold_reasons"] == ["forbidden_fallback_surface"]
    assert not list(wa.inner.neighbours(receipt, "releases"))


def test_diagnostic_error_surface_is_not_counted_as_a_semantic_release():
    wa = _agent()
    committed = wa.s.add_node("Committed", {"utterance": "answer response"})
    gate = {"recoverable": True, "coverage": 1.0, "mode": "test"}

    assert release_if_gated(
        wa, _frame(),
        "ERROR: no communicative response could be generated.",
        gate, committed,
    ) is None
    receipt = list(wa.s.nodes("ProductionGateReceipt"))[0]
    attrs = wa.s.node(receipt)["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["withhold_reasons"] == [
        "diagnostic_error_surface_not_a_release"]
    assert not list(wa.inner.neighbours(receipt, "releases"))


def test_realized_frame_reply_leaves_release_receipt():
    wa = _agent()
    reply = wa._realize_frame_reply(_frame())

    assert reply
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["surface"] == reply
    assert attrs["recoverable"] is True
    assert attrs["coverage"] == 1.0
    assert attrs["parse_back_mode"] in {"grounded_comprehension", "recognizer"}


def test_question_response_cannot_splice_answer_act_and_surface_messages(
        monkeypatch):
    wa = _agent()
    inbound = wa.s.add_node("Message", {
        "from": "user", "text": "Which item?", "adjacency_replied_act": "answer",
    })
    interpretation = wa.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "interaction_mode": "turn_compatible",
    })
    wa.inner.set_attr(
        inbound, "communication_interpretation_id", int(interpretation.value))
    answer_act = wa.s.add_node("SpeechActConcept", {"name": "answer"})
    answer_only = wa.s.add_node("Message", {
        "from": "agent", "text": "",
    })
    surface_only = wa.s.add_node("Message", {
        "from": "agent", "text": "The grounded answer.",
    })
    for message in (answer_only, surface_only):
        wa.inner.add_edge_unchecked(message, "responds_to", inbound)
        wa.inner.add_edge_unchecked(wa.agent, "sent", message)
    wa.inner.add_edge_unchecked(answer_only, "has_speech_act", answer_act)

    monkeypatch.setattr(wa, "_relation_has_causal_evidence", lambda _mid: True)
    release_calls = []
    from domains import production_gate
    monkeypatch.setattr(
        production_gate, "release_if_gated",
        lambda *args, **kwargs: release_calls.append((args, kwargs)) or "released")

    assert wa._release_question_response_reply(
        inbound, "The grounded answer.") is None
    assert release_calls == []


def test_rule_history_reply_requires_exact_selected_evidence_edge(monkeypatch):
    wa = _agent()
    inbound = wa.s.add_node("Message", {
        "from": "user", "text": "Which rule fired last?",
        "adjacency_replied_act": "answer",
    })
    interpretation = wa.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "interaction_mode": "turn_compatible",
        "arbitration_basis": "grounded_rule_firing_history",
        "cognitive_disposition": "answer",
        "selected_rule_name": "selected_rule_42",
    })
    wa.inner.set_attr(
        inbound, "communication_interpretation_id", int(interpretation.value))
    history = wa.s.add_node("RuleFiringHistory", {
        "schema": "rule_firing_history.v1",
        "last_rule_name": "selected_rule_42",
        "last_inbound_message_id": 123,
    })
    evidence = wa.s.add_node("RuleFiringAnswerEvidence", {
        "schema": "rule_firing_answer_evidence.v1",
        "status": "supported",
        "rule_name": "selected_rule_42",
        "source_message_id": 123,
    })
    wa.inner.add_edge_unchecked(
        interpretation, "has_rule_firing_answer_evidence", evidence)
    wa.inner.add_edge_unchecked(evidence, "supported_by", history)
    answer_act = wa.s.add_node("SpeechActConcept", {"name": "answer"})
    candidate = "The last rule to make progress was: selected_rule_42."
    reply = wa.s.add_node("Message", {
        "from": "agent", "text": candidate,
        "rule_firing_history_answer": 1.0,
    })
    wa.inner.add_edge_unchecked(reply, "responds_to", inbound)
    wa.inner.add_edge_unchecked(reply, "has_speech_act", answer_act)
    wa.inner.add_edge_unchecked(reply, "grounded_by_rule_firing_history", history)
    wa.inner.add_edge_unchecked(wa.agent, "sent", reply)

    monkeypatch.setattr(wa, "_relation_has_causal_evidence", lambda _mid: True)
    release_calls = []
    from domains import production_gate
    monkeypatch.setattr(
        production_gate, "release_if_gated",
        lambda *args, **kwargs: release_calls.append((args, kwargs)) or "released")

    # A linked answer and history are insufficient when the exact selected
    # RuleFiringAnswerEvidence is not the one the surface realizes.
    assert wa._release_question_response_reply(inbound, candidate) is None
    assert release_calls == []


def test_output_null_repair_attempts_leave_withheld_receipts(monkeypatch):
    wa = _agent()

    def never_recover(*args, **kwargs):
        return {"recoverable": False, "coverage": 0.0,
                "missing": ["dog", "mammal"], "recovered": [],
                "intended": ["dog", "mammal"], "mode": "test"}

    from domains import self_target_monitor
    monkeypatch.setattr(self_target_monitor, "score_self_target", never_recover)

    assert wa._realize_frame_reply(_frame()) is None
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 2
    assert all(wa.s.node(node)["attrs"]["status"] == "withheld"
               for node in receipts)
    assert all("parse_back_not_recoverable" in wa.s.node(node)["attrs"]["withhold_reasons"]
               for node in receipts)


@pytest.mark.parametrize(
    ("text", "speech_act", "expected_event"),
    [
        ("Please open the north gate.", "statement", "open"),
        # With no antecedent for ``it``, cognition must preserve the
        # unresolved-reference repair state rather than releasing an action.
        ("Move it now.", "statement", "repair"),
        ("Quorplezap the door.", "request", "repair"),
        ("look left then quorplezap the door", "statement", "repair"),
    ],
)
def test_conversation_action_and_repair_surfaces_release_graph_receipts(
        text, speech_act, expected_event):
    """Action/repair coverage must come from the bridge's graph commitment."""
    from substrate.boot_all import load_all_seeds

    wa = _agent()
    # This is an end-to-end graph-action/repair integration, not an empty
    # substrate fallback test. Install the same cognitive/production seed
    # graph that owns the disposition and receipt before asserting its release.
    load_all_seeds(wa)
    reply = wa.converse(text, speech_act=speech_act,
                        context={"interaction_mode": "turn_compatible"})

    assert reply
    assert reply != "noted"
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    released = [wa.s.node(node)["attrs"] for node in receipts
                if wa.s.node(node)["attrs"].get("status") == "released"]
    assert len(released) == 1
    assert released[0]["parse_back_mode"] == "conversation_action_graph"
    assert released[0]["surface"] == reply
    assert released[0]["semantic_event"] == expected_event
    trace = wa.reply_turn_trace(wa.last_turn_inbound_id())
    assert trace["reply"] == reply
    assert trace["production_release"]["semantic_event"] == expected_event
    if expected_event == "open":
        inbound = wa._last_turn_inbound
        assert any(
            wa.s.node(goal)["attrs"].get("kind") == "instruction"
            and wa.s.node(goal)["attrs"].get("object") == "north gate"
            and inbound in wa.inner.neighbours(goal, "comprehends")
            for goal in wa.inner.neighbours(wa.agent, "has_goal")
            if wa.s.has_node(goal)
        )
    if "quorplezap" in text.lower():
        inbound = wa._last_turn_inbound
        interpretation = wa.s.node(
            wa.s.node(inbound)["attrs"]["communication_interpretation_id"]
        )["attrs"]
        assert interpretation["cognitive_disposition"] == "repair"
        assert interpretation["arbitration_basis"] == \
            "typed_unresolved_action_dependency"
        assert interpretation["language_repair_focus"].lower() == "quorplezap"
        if " then " in text.lower():
            assert interpretation["language_sequence_relation"] == "sequential"
            assert interpretation["language_sequence_status"] == \
                "unresolved_action_head"
        else:
            assert interpretation["language_repair_evidence"] == \
                "unresolved_action_head"
        assert "quorplezap" in reply.lower()


def test_unrelated_topic_path_does_not_gain_action_receipt():
    wa = _agent()
    wa.converse("How are you organised?", speech_act="question",
                context={"interaction_mode": "turn_compatible"})

    assert not any(
        wa.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_action_graph"
        for node in wa.s.nodes("ProductionGateReceipt")
    )


def test_native_instruction_gap_report_releases_its_graph_message_through_gate():
    from substrate.boot_all import load_all_seeds

    wa = _agent()
    load_all_seeds(wa)
    surface = wa.converse("Inspect the lower sensor.", speech_act="instruction")
    inbound = wa._last_turn_inbound
    inbound_attrs = wa.s.node(inbound)["attrs"]

    assert inbound_attrs["instruction_gap_noted"] == 1.0
    assert inbound_attrs["self_improvement_route"] == "filed_concern"
    assert inbound_attrs["communication_route"] == "instruction_gap_report_graph"
    matching = [receipt for receipt in wa.s.nodes("ProductionGateReceipt")
                if wa.s.node(receipt)["attrs"].get("turn_message_id")
                == int(inbound.value)
                and wa.s.node(receipt)["attrs"].get("surface") == surface]
    assert len(matching) == 1
    receipt = matching[0]
    attrs = wa.s.node(receipt)["attrs"]
    assert attrs["status"] == "released"
    assert attrs["semantic_event"] == "gap"
    assert attrs["semantic_intent"] == "inform"
    assert attrs["parse_back_mode"] == "conversation_instruction_graph"
    released = list(wa.inner.neighbours(receipt, "releases"))
    assert len(released) == 1
    assert inbound in wa.responds_to(released[0])
    assert wa.s.node(released[0])["attrs"]["text"] == surface
