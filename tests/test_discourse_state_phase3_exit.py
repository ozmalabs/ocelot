"""Phase 3 exit gate: mixed discourse, common ground, and native lifecycle."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import load_seeds_into
from substrate.world_adapter import WorldAdapter
from domains.discourse_state import (
    close_expectation,
    ensure_common_ground,
    ensure_discourse_state,
    open_goal,
    record_event,
    transition_goal,
)


def _agent_with_discourse_seed():
    agent = WorldAdapter(seeds=())
    load_seeds_into(agent.s, agent.agent, ["conversation_discourse_state"])
    return agent


def test_phase3_ten_event_mixed_act_dialogue_tracks_addressee_and_common_ground():
    agent = _agent_with_discourse_seed()
    people = agent.attach_chat_world("user")
    addressee = people["interlocutor"]
    state = ensure_discourse_state(agent, conversation_id="ten-event",
                                   addressee=addressee)
    ground = ensure_common_ground(agent, state, addressee=addressee)

    origin = record_event(agent, state, kind="request", speaker=addressee,
                          addressee=agent.agent, topic="calendar",
                          expectation="action", payload={"common_ground_delta": "calendar_request"})
    record_event(agent, state, kind="selection", speaker=agent.agent,
                 addressee=addressee)
    record_event(agent, state, kind="execution", speaker=agent.agent,
                 addressee=addressee)
    result = record_event(agent, state, kind="action_result",
                          speaker=agent.agent, addressee=addressee,
                          payload={"common_ground_delta": "calendar_checked"})
    record_event(agent, state, kind="assertion", speaker=addressee,
                 addressee=agent.agent, topic="calendar",
                 payload={"common_ground_delta": "calendar_shared"})

    answer_origin = record_event(agent, state, kind="question",
                                 speaker=addressee, addressee=agent.agent,
                                 topic="location", expectation="answer")
    record_event(agent, state, kind="selection", speaker=agent.agent,
                 addressee=addressee)
    record_event(agent, state, kind="execution", speaker=agent.agent,
                 addressee=addressee)
    answer_result = record_event(agent, state, kind="action_result",
                                 speaker=agent.agent, addressee=addressee,
                                 payload={"common_ground_delta": "location_shared"})
    repair = record_event(agent, state, kind="epistemic_limit",
                          speaker=agent.agent, addressee=addressee)
    close_expectation(agent, state, event=repair, disposition="deferred",
                      residual="location_unresolved")

    assert agent.s.node(state)["attrs"]["event_index"] == 10
    assert agent.s.node(ground)["attrs"]["revision"] == 2
    assert agent.s.node(ground)["attrs"]["claims"] == [
        "calendar_checked", "location_shared"
    ]
    agent_ground = next(item for item in agent.inner.neighbours(
        state, "has_common_ground")
                        if agent.s.node(item)["attrs"].get("scope_key") ==
                        "addressee:%s" % agent.agent)
    assert agent.s.node(agent_ground)["attrs"]["claims"] == [
        "calendar_request", "calendar_shared"
    ]
    assert list(agent.inner.neighbours(state, "for_addressee")) == [addressee]
    assert list(agent.inner.neighbours(origin, "to_addressee")) == [agent.agent]
    assert list(agent.inner.neighbours(answer_result, "contributes_to_common_ground")) == [ground]
    assert answer_origin != result


def test_phase3_native_rules_execute_mixed_act_goal_lifecycle():
    agent = _agent_with_discourse_seed()
    addressee = agent.attach_chat_world("user")["interlocutor"]
    state = ensure_discourse_state(agent, conversation_id="native", addressee=addressee)
    origin = record_event(agent, state, kind="request", speaker=addressee,
                          addressee=agent.agent, expectation="action")
    goal = open_goal(agent, state, kind="act_or_clarify", origin_event=origin)
    record_event(agent, state, kind="selection", speaker=agent.agent,
                 addressee=addressee, goal=goal)
    record_event(agent, state, kind="execution", speaker=agent.agent,
                 addressee=addressee, goal=goal)
    result = record_event(agent, state, kind="action_result",
                          speaker=agent.agent, addressee=addressee,
                          goal=goal)

    steps = agent.inner.run_rules(max_steps=20)
    attrs = agent.s.node(goal)["attrs"]
    assert steps >= 1
    assert attrs["lifecycle_status"] == "resolved"
    assert attrs["status"] == "resolved"
    assert attrs["outcome"] == "native_event_result"
    assert list(agent.inner.neighbours(goal, "transitioned_by")) == [
        list(agent.inner.neighbours(state, "has_event"))[1],
        list(agent.inner.neighbours(state, "has_event"))[2],
        result,
    ]
    assert goal in list(agent.inner.neighbours(state, "has_closed_goal"))


def test_phase3_fixture_is_exactly_ten_mixed_events():
    fixture_path = (Path(__file__).parent / "fixtures" / "conversational_manifold"
                    / "phase3_mixed_act_dialogue.json")
    fixture = json.loads(fixture_path.read_text())
    kinds = [event["kind"] for event in fixture["events"]]
    assert fixture["event_count"] == len(kinds) == 10
    assert {"request", "assertion", "question", "epistemic_limit"}.issubset(kinds)


def test_phase3_common_ground_stress_interleaves_goals_and_nonreply_events():
    """Common ground and goals advance over events, not manufactured turns."""
    agent = _agent_with_discourse_seed()
    first = agent.attach_chat_world("user")
    second = agent.attach_chat_world("observer")
    state = ensure_discourse_state(agent, conversation_id="stress",
                                   addressee=first["interlocutor"])
    ground = ensure_common_ground(agent, state, addressee=first["interlocutor"])

    origin_a = record_event(
        agent, state, kind="request", speaker=first["interlocutor"],
        addressee=agent.agent, expectation="action",
        interaction_mode="asynchronous",
        payload={"common_ground_delta": "schedule_request"},
    )
    observation = record_event(
        agent, state, kind="observation", speaker=second["interlocutor"],
        addressee=agent.agent, interaction_mode="stream",
        payload={"common_ground_delta": "availability_observed"},
    )
    assertion = record_event(
        agent, state, kind="assertion", speaker=first["interlocutor"],
        addressee=second["interlocutor"], interaction_mode="event",
        payload={"common_ground_delta": "constraint_shared"},
    )
    origin_b = record_event(
        agent, state, kind="request", speaker=second["interlocutor"],
        addressee=agent.agent, expectation="action",
        interaction_mode="asynchronous",
        payload={"common_ground_delta": "verification_request"},
    )
    goal_a = open_goal(agent, state, kind="schedule", origin_event=origin_a,
                       addressee=first["interlocutor"])
    goal_b = open_goal(agent, state, kind="verify", origin_event=origin_b,
                       addressee=second["interlocutor"])

    select_a = record_event(agent, state, kind="selection",
                            addressee=first["interlocutor"],
                            interaction_mode="native")
    execute_a = record_event(agent, state, kind="execution",
                             addressee=first["interlocutor"],
                             interaction_mode="native")
    result_a = record_event(agent, state, kind="action_result",
                            addressee=first["interlocutor"],
                            interaction_mode="native",
                            payload={"common_ground_delta": "schedule_verified"})
    select_b = record_event(agent, state, kind="selection",
                            addressee=second["interlocutor"],
                            interaction_mode="native")
    execute_b = record_event(agent, state, kind="execution",
                             addressee=second["interlocutor"],
                             interaction_mode="native")
    result_b = record_event(agent, state, kind="action_result",
                            addressee=second["interlocutor"],
                            interaction_mode="native",
                            payload={"common_ground_delta": "constraint_verified"})

    transition_goal(agent, goal_a, "selected", event=select_a)
    transition_goal(agent, goal_a, "executing", event=execute_a)
    transition_goal(agent, goal_a, "resolved", event=result_a,
                    outcome="schedule_verified")
    transition_goal(agent, goal_b, "selected", event=select_b)
    transition_goal(agent, goal_b, "executing", event=execute_b)
    transition_goal(agent, goal_b, "resolved", event=result_b,
                    outcome="constraint_verified")

    grounds = list(agent.inner.neighbours(state, "has_common_ground"))
    scoped_claims = {
        agent.s.node(item)["attrs"].get("scope_key"):
        agent.s.node(item)["attrs"].get("claims") or []
        for item in grounds
    }
    assert scoped_claims["addressee:%s" % agent.agent] == [
        "schedule_request", "availability_observed", "verification_request",
    ]
    assert scoped_claims["addressee:%s" % second["interlocutor"]] == [
        "constraint_shared", "constraint_verified",
    ]
    assert scoped_claims["addressee:%s" % first["interlocutor"]] == [
        "schedule_verified",
    ]
    all_participants = set().union(*(
        set(agent.s.node(item)["attrs"].get("participants") or [])
        for item in grounds))
    assert all_participants == {
        agent.agent, first["interlocutor"], second["interlocutor"],
    }
    assert list(agent.inner.neighbours(observation, "to_addressee")) == [agent.agent]
    assert list(agent.inner.neighbours(assertion, "to_addressee")) == [second["interlocutor"]]
    assert agent.s.node(goal_a)["attrs"]["status"] == "resolved"
    assert agent.s.node(goal_b)["attrs"]["status"] == "resolved"
    assert list(agent.inner.neighbours(state, "has_active_goal")) == []
    assert set(agent.inner.neighbours(state, "has_closed_goal")) == {goal_a, goal_b}
    assert all(agent.s.node(event)["attrs"]["kind"] != "reply"
               for event in agent.inner.neighbours(state, "has_event"))


def test_phase3_common_ground_stress_fixture_is_non_turn_event_corpus():
    fixture_path = (Path(__file__).parent / "fixtures" / "conversational_manifold"
                    / "phase3_common_ground_stress.json")
    fixture = json.loads(fixture_path.read_text())
    assert fixture["event_count"] == len(fixture["events"]) == 10
    assert fixture["reply_event_count"] == 0
    assert {event["mode"] for event in fixture["events"]} == {
        "asynchronous", "stream", "event", "native",
    }
