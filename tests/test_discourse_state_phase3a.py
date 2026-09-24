"""Phase 3A: graph-resident discourse state and goal lifecycle."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from domains.discourse_state import (
    close_expectation,
    ensure_discourse_state,
    open_goal,
    record_event,
    transition_goal,
)


def _agent():
    return WorldAdapter(seeds=())


def test_state_is_idempotent_and_events_are_not_turn_bound():
    agent = _agent()
    state = ensure_discourse_state(agent, conversation_id="c1")
    assert ensure_discourse_state(agent, conversation_id="c1") == state
    event = record_event(agent, state, kind="observation", topic="weather",
                         interaction_mode="stream", payload={"source": "sensor"})
    attrs = agent.s.node(state)["attrs"]
    assert attrs["schema"] == "discourse_state.v1"
    assert attrs["current_topic"] == "weather"
    assert attrs["event_index"] == 1
    assert agent.s.node(event)["attrs"]["interaction_mode"] == "stream"


def test_goal_lifecycle_keeps_origin_and_closes_without_orphan():
    agent = _agent()
    state = ensure_discourse_state(agent)
    origin = record_event(agent, state, kind="request", expectation="action")
    evidence = agent.s.add_node("Evidence", {"schema": "evidence.v1", "kind": "capability"})
    goal = open_goal(agent, state, kind="act_or_clarify", origin_event=origin,
                     evidence=evidence, next_action="select")
    selected = record_event(agent, state, kind="selection")
    transition_goal(agent, goal, "selected", event=selected, next_action="execute")
    executing = record_event(agent, state, kind="execution")
    transition_goal(agent, goal, "executing", event=executing)
    resolved = record_event(agent, state, kind="action_result")
    transition_goal(agent, goal, "resolved", event=resolved,
                    outcome="action_completed")
    assert agent.s.node(goal)["attrs"]["status"] == "resolved"
    assert list(agent.inner.neighbours(state, "has_active_goal")) == []
    assert list(agent.inner.neighbours(state, "has_closed_goal")) == [goal]
    assert list(agent.inner.neighbours(goal, "originated_in")) == [origin]
    assert list(agent.inner.neighbours(goal, "supported_by")) == [evidence]


def test_invalid_lifecycle_transition_fails_without_mutation():
    agent = _agent()
    state = ensure_discourse_state(agent)
    origin = record_event(agent, state, kind="question")
    goal = open_goal(agent, state, kind="answer_or_learn", origin_event=origin)
    with pytest.raises(ValueError, match="invalid goal lifecycle"):
        transition_goal(agent, goal, "resolved")
    assert agent.s.node(goal)["attrs"]["status"] == "proposed"
    assert list(agent.inner.neighbours(state, "has_active_goal")) == [goal]


def test_defer_and_error_close_expectation_without_forcing_reply():
    agent = _agent()
    state = ensure_discourse_state(agent)
    request = record_event(agent, state, kind="request", expectation="answer")
    defer = record_event(agent, state, kind="epistemic_limit")
    close_expectation(agent, state, event=defer, disposition="deferred",
                      residual="missing_referent")
    attrs = agent.s.node(state)["attrs"]
    assert attrs["pending_expectation"] is None
    assert attrs["expectation_disposition"] == "deferred"
    assert attrs["expectation_closed_by"] == defer
    assert attrs["unresolved_residuals"] == ["missing_referent"]
    assert request != defer
