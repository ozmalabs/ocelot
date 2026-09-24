"""Phase 1: one auditable interpretation per live conversational turn.

The test checks cognitive state, not reply wording. Native speech-act output
and front-end comprehension are allowed to disagree; the disagreement must be
recorded so a later graph rule can learn from it rather than losing it in the
adapter's locals.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def _agent():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent._donkey = {"n": 0}
    return agent


def _interpretation(agent, text):
    messages = [
        n for n in agent.s.nodes("Message")
        if agent.s.node(n)["attrs"].get("text") == text
        and agent.s.node(n)["attrs"].get("from") != "agent"
    ]
    assert messages
    message = messages[-1]
    interpretations = agent.inner.neighbours(message, "has_interpretation")
    assert len(interpretations) == 1
    return message, interpretations[0]


def test_instruction_interpretation_is_graph_resident_and_selected():
    agent = _agent()
    agent.converse("report your organisation", "statement")
    message, interpretation = _interpretation(agent, "report your organisation")
    attrs = agent.s.node(interpretation)["attrs"]

    assert attrs["schema"] == "communication_interpretation.v1"
    assert attrs["evidence_schema"] == "communication_evidence.v1"
    assert attrs["evidence_provider"] == "language_adapter"
    assert attrs["event_kind"] == "utterance"
    assert attrs["interaction_mode"] == "turn_compatible"
    assert attrs["status"] == "selected"
    assert attrs["kind"] == "instruction"
    assert attrs["dispatch_path"] == "instruction"
    assert attrs["literal_mood"] == "imperative"
    assert attrs["communicative_force_hypothesis"] == "request_action_or_account"
    assert attrs["cognitive_goal_hypothesis"] == "act_or_answer"
    assert attrs["grounding_status"] == "candidate_grounded"
    assert attrs["predicate"] == "report"
    assert agent.s.node(message)["attrs"]["turn_interpretation_kind"] == "instruction"
    assert interpretation in agent.inner.neighbours(agent.agent, "holds_interpretation")
    assert message in agent.inner.neighbours(interpretation, "interprets")


def test_frontier_repair_interpretation_preserves_gap_evidence():
    agent = _agent()
    agent.converse("quorplezap the door", "statement")
    message, interpretation = _interpretation(agent, "quorplezap the door")
    attrs = agent.s.node(interpretation)["attrs"]

    assert attrs["kind"] == "statement"
    assert attrs["dispatch_path"] == "statement"
    assert attrs["gap_count"] >= 1
    assert attrs["communicative_force_hypothesis"] == "assertion_or_report"
    assert attrs["grounding_status"] == "unresolved"
    assert agent.s.node(message)["attrs"]["turn_interpretation_conflict"] in (0, 1)


def test_native_and_comprehension_conflicts_are_recorded_not_erased():
    agent = _agent()
    # The enumerate instruction is pragmatically promoted to a question by
    # comprehension, while the native surface classifier can retain the
    # instruction reading. The important Phase 1 property is the audit record.
    agent.converse("name one of your rules", "statement")
    _message, interpretation = _interpretation(agent, "name one of your rules")
    attrs = agent.s.node(interpretation)["attrs"]

    assert attrs["kind"] == "question"
    assert attrs["dispatch_path"] == "satisfiable"
    assert attrs["native_kind"] in {"", "instruction", "question", "statement"}
    assert attrs["conflict_resolution"] in {"agreement", "selected_comprehension"}


def test_turn_api_can_record_a_non_turn_interaction_mode():
    agent = _agent()
    agent.converse(
        "the sky is blue",
        "statement",
        context={"interaction_mode": "streaming_observation"},
    )
    _message, interpretation = _interpretation(agent, "the sky is blue")
    attrs = agent.s.node(interpretation)["attrs"]

    assert attrs["schema"] == "communication_interpretation.v1"
    assert attrs["interaction_mode"] == "streaming_observation"
    assert attrs["event_kind"] == "utterance"


def test_polite_action_request_keeps_action_evidence_after_politeness_strip():
    agent = _agent()
    agent.converse("Please open the north gate.", "statement")
    _message, interpretation = _interpretation(agent, "Please open the north gate.")
    attrs = agent.s.node(interpretation)["attrs"]

    assert attrs["kind"] == "instruction"
    assert attrs["dispatch_path"] == "instruction"
    assert attrs["communicative_force"] == "request_action"
    assert attrs["cognitive_goal"] == "act_or_clarify"
    assert attrs["evidence_force"] == "action_request"
