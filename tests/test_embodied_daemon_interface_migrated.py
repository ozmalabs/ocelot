"""Mechanical daemon boundary for graph-owned embodied learning."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import jabberwock_daemon as daemon  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def test_embodied_status_is_read_only_and_preserves_graph_provenance():
    agent = WorldAdapter(seeds=())
    session = agent.s.add_node("EmbodiedLearningSession", {
        "status": "active", "trial_seq": 2, "integer_native": 1,
    })
    goal = agent.s.add_node("Goal", {
        "kind": "supported_orientation_change", "status": "active",
        "order_n": 1,
    })
    frontier = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "name": "rolling", "status": "active",
    })
    request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "status": "requested", "attempt_ordinal": 2,
    })
    mission = agent.s.add_node("EmbodiedInstructionGoalProposal", {
        "status": "accepted", "predicate": "develop",
    })
    _edge(agent, session, "has_active_embodied_goal", goal)
    _edge(agent, session, "has_developmental_frontier", frontier)
    _edge(agent, session, "has_grounded_external_trial_request", request)
    before = agent.inner.graph_to_dict()

    status = daemon.embodied_learning_status(agent)

    assert status["read_only"] and not status["requires_cognition"]
    assert status["sessions"][0]["id"] == session.value
    assert status["sessions"][0]["goals"][0]["id"] == goal.value
    assert status["sessions"][0]["frontiers"][0]["id"] == frontier.value
    assert status["sessions"][0]["external_requests"][0]["id"] == request.value
    assert status["missions"][0]["id"] == mission.value
    assert agent.inner.graph_to_dict() == before


def test_graph_selected_embodied_host_action_calls_only_attached_transducer():
    agent = WorldAdapter(seeds=())
    state = daemon.DaemonState(agent, "test")
    calls = []
    source = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "status": "requested", "integer_native": 1,
    })
    state.embodied_trial_executor = lambda observed, selected: calls.append(
        (observed, selected))
    request = agent.s.add_node("HostActionRequest", {
        "action": "embodied_trial", "status": "requested",
        "source": source,
        "urgency": 1, "residual": 1, "estimated_cost": 1, "deadline": 0,
    })

    assert daemon._execute_host_action_requests(state) == 1
    assert calls == [(agent, source)]
    assert agent.s.node(request)["attrs"]["status"] == "done"
    receipt = agent.inner.neighbours(request, "has_receipt")[0]
    assert agent.s.node(receipt)["attrs"]["action"] == "embodied_trial"


def test_missing_embodied_world_is_an_honest_failed_receipt():
    agent = WorldAdapter(seeds=())
    state = daemon.DaemonState(agent, "test")
    request = agent.s.add_node("HostActionRequest", {
        "action": "embodied_trial", "status": "requested",
        "source": agent.s.add_node("EmbodiedExternalTrialRequest", {
            "status": "requested", "integer_native": 1,
        }),
        "urgency": 1, "residual": 1, "estimated_cost": 1, "deadline": 0,
    })

    assert daemon._execute_host_action_requests(state) == 1
    assert agent.s.node(request)["attrs"]["status"] == "failed"
    receipt = agent.inner.neighbours(request, "has_receipt")[0]
    attrs = agent.s.node(receipt)["attrs"]
    assert attrs["status"] == "failed"
    assert "no embodied trial world" in attrs["error"]
