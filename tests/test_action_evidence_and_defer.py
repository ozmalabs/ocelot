"""Neutral action/condition evidence reaches cognition and Goal lifecycle."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from domains.comprehend_text import comprehend_text  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


@pytest.mark.parametrize("text, expected", [
    ("Check the pressure.", ("check", "pressure")),
    ("Open the hatch and check the gauge.", ("open", "hatch")),
])
def test_instruction_adapter_emits_neutral_action_evidence(text, expected):
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, text, kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_predicate"].lower() == expected[0]
    assert evidence["action_target"].lower() == expected[1]


def test_temporal_focus_emits_deferred_condition_evidence():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "When ready, close the hatch.",
                          kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_predicate"].lower() == "close"
    assert evidence["action_target"].lower() == "hatch"
    assert evidence["deferred_condition"] is True


def test_deferred_instruction_goal_is_not_immediate_execution():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "When ready, close the hatch.", speech_act="instruction",
        context={"interaction_mode": "non_turn"})
    assert reply
    goals = [agent.s.node(node)["attrs"] for node in agent.s.nodes("Goal")
             if agent.s.node(node)["attrs"].get("predicate") == "close"]
    assert goals
    assert any(goal.get("status") == "deferred" for goal in goals)


def test_graph_semantic_knowledge_deficit_enters_repair_lifecycle():
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "I need more information.", speech_act="statement",
        context={"interaction_mode": "non_turn"})
    assert reply
    assert reply != "ERROR: no communicative response could be generated."
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    assert attrs["comp_dispatch_path"] == "frontier"
    assert attrs["comp_intent"] == "repair:knowledge_deficit"
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")]
    assert any(item.get("parse_back_mode") == "conversation_action_graph"
               and item.get("status") == "released" for item in receipts)


def test_world_support_gap_remains_explicit_blocked_boundary():
    from domains.comprehend_text import comprehend_text
    from domains.conversation_action import is_ask_back

    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "What is beyond the wall?", kind="question")
    assert comp.dispatch["language_evidence"]["world_support"] == "missing"
    assert is_ask_back(comp) is False


def test_world_support_evidence_survives_selected_interpretation():
    agent = WorldAdapter(seeds=())
    agent.converse("What is beyond the wall?", speech_act="question")
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"])
    assert interpretation["attrs"]["language_world_support"] == "missing"
