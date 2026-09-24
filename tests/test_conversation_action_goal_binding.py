"""Focused provenance tests for conversation-action Goal minting."""
from __future__ import annotations

from domains import conversation_action as ca
from domains.comprehend_text import Comprehension
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def _agent():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    return agent


def test_mint_goal_binds_origin_message_and_is_idempotent():
    agent = _agent()
    inbound = agent.receive_utterance("Open the gate.", speech_act="instruction")

    goal = ca._mint_goal(agent, "instruction", "open", "gate", inbound=inbound)
    ca._bind_goal_to_inbound(agent, goal, inbound)

    assert list(agent.inner.neighbours(goal, "comprehends")) == [inbound]
    assert agent.s.node(goal)["attrs"]["origin_turn_id"] == int(inbound.value)


def test_action_path_binds_goal_without_creating_an_extra_goal():
    agent = _agent()
    inbound = agent.receive_utterance("Open the gate.", speech_act="instruction")
    comp = Comprehension(
        raw="Open the gate.",
        kind="instruction",
        dispatch={"predicate": "open", "object": "gate"},
    )
    before = len(list(agent.s.nodes("Goal")))

    result = ca.act_on_instruction(agent, comp, inbound)

    goal = result["goal"]
    assert len(list(agent.s.nodes("Goal"))) == before + 1
    assert list(agent.inner.neighbours(goal, "comprehends")) == [inbound]
    assert agent.s.node(goal)["attrs"]["origin_turn_id"] == int(inbound.value)


def test_mint_goal_without_inbound_remains_unbound():
    agent = _agent()

    goal = ca._mint_goal(agent, "instruction", "open", "gate")

    assert list(agent.inner.neighbours(goal, "comprehends")) == []
    assert "origin_turn_id" not in agent.s.node(goal)["attrs"]
