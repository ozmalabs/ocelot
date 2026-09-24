"""The cognition rules must work from neutral adapter evidence alone.

These events deliberately omit English predicates, word order, POS, mood, and
dispatch-path labels. They model the output of a second semantic adapter.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from domains.communication_evidence import from_semantic_frame


EVENTS = [
    ("information", "information_request", "answer_or_learn", "request_information"),
    ("action", "action_request", "act_or_clarify", "request_action"),
    ("assertion", "assertion_or_correction", "update_common_ground", "assertion_or_correction"),
    ("repair", "repair_or_defer", "clarify_or_defer", "repair_or_defer"),
    ("social", "social_action", "coordinate_socially", "social_action"),
]


def test_graph_arbitration_accepts_language_neutral_evidence_provider():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    for label, evidence_force, evidence_goal, expected_force in EVENTS:
        interpretation = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "evidence_provider": "synthetic_semantic_adapter",
            "evidence_force": evidence_force,
            "evidence_goal": evidence_goal,
            "communicative_force": None,
            "cognitive_goal": None,
        })
        agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation", interpretation)
        agent.inner.run_rules()
        attrs = agent.s.node(interpretation)["attrs"]
        assert attrs["communicative_force"] == expected_force, label
        assert attrs["cognitive_goal"] == evidence_goal, label


def test_unknown_adapter_force_is_an_explicit_evidence_error():
    with pytest.raises(ValueError, match="supported neutral communicative force"):
        from_semantic_frame(
            {"speech_act": "unclassified"},
            provider="incomplete_adapter",
        )
