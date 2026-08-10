"""Executable graph-native belief dynamics and counterfactual trajectories."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _nodes(agent, node_type):
    return [
        nid for nid in agent.s.nodes()
        if agent.s.node(nid)["type"] == node_type
    ]


def _add(agent, node_type, attrs, edge_type=None):
    node = agent.s.add_node(node_type, attrs)
    if edge_type is not None:
        _edge(agent, agent.agent, edge_type, node)
    return node


def _perceive(agent, epoch=1):
    observation = _add(agent, "WorldModelObservation", {
        "belief_status": "new",
        "prediction_comparison_status": "uncompared",
        "provenance_kind": "perceived",
        "state_kind": "corridor",
        "state_summary": "door ahead, cover on the left",
        "epoch": float(epoch),
        "confidence": 0.9,
        "uncertainty": 0.1,
    }, "has_world_model_observation")
    agent.tick()
    return observation, _nodes(agent, "BeliefState")[-1]


def _model_fixture(agent, source_belief, *, epoch=1, deadline=5, budget=6):
    clock = _add(agent, "WorldModelClock", {"epoch": float(epoch)})
    forward = _add(agent, "WorldModelAction", {
        "action_kind": "forward", "branch_rank": 1.0,
    }, "has_world_model_action")
    turn = _add(agent, "WorldModelAction", {
        "action_kind": "turn_left", "branch_rank": 2.0,
    }, "has_world_model_action")

    transitions = []
    for rank, source, action, successor, observation, outcome, value in (
        (1, "corridor", "forward", "junction", "junction_visible",
         "progress", 0.7),
        (2, "corridor", "turn_left", "corridor", "left_wall_visible",
         "safe_reorientation", 0.2),
        (3, "junction", "forward", "exit", "exit_visible",
         "goal_progress", 1.0),
        (4, "junction", "turn_left", "corridor", "side_route_visible",
         "safe_reorientation", 0.4),
    ):
        transition = _add(agent, "TransitionHypothesis", {
            "source_state_kind": source,
            "action_kind": action,
            "successor_state_kind": successor,
            "successor_summary": f"{action} predicts {successor}",
            "predicted_observation_kind": observation,
            "predicted_observation_value": value,
            "predicted_outcome_kind": outcome,
            "predicted_outcome_value": value,
            "confidence": 0.8,
            "uncertainty": 0.2,
            "model_rank": float(rank),
            "revision_count": 0.0,
        }, "has_transition_hypothesis")
        feature = _add(agent, "TransitionFeature", {
            "feature_key": f"affordance:{action}",
            "feature_value": successor,
            "confidence": 0.9,
        })
        _edge(agent, transition, "predicts_feature", feature)
        transitions.append(transition)

    request = _add(agent, "SimulationRequest", {
        "status": "active",
        "request_kind": "test_counterfactual",
        "provenance_kind": "imagined",
        "observation_status": "not_observed",
        "input_epoch": float(epoch),
        "deadline_epoch": float(deadline),
        "horizon": 3.0,
        "budget": float(budget),
        "maximum_branching": 2.0,
    }, "has_simulation_request")
    _edge(agent, request, "has_source_belief", source_belief)
    _edge(agent, request, "considers_action", forward)
    _edge(agent, request, "considers_action", turn)
    _edge(agent, request, "validated_by_clock", clock)
    return request, clock, transitions


def test_perception_and_recall_keep_distinct_epistemic_provenance():
    agent = WorldAdapter(seeds=("generative_world_model",))
    observation, perceived = _perceive(agent)

    assert agent.s.node(perceived)["attrs"]["provenance_kind"] == "perceived"
    assert agent.s.node(perceived)["attrs"]["observation_status"] == "observed"
    assert list(agent.inner.neighbours(
        perceived, "supported_by_observation"
    )) == [observation]

    episode = _add(agent, "Episode", {
        "state_kind": "room",
        "state_summary": "a remembered room",
        "tick": -10.0,
    })
    request = _add(agent, "MemoryRetrievalRequest", {
        "status": "completed",
        "cue_key": "room",
        "epoch": 2.0,
    })
    recall = _add(agent, "RecallCandidate", {
        "status": "requested",
        "retrieval_status": "recalled",
        "epoch": 2.0,
        "confidence": 0.65,
        "uncertainty": 0.35,
    }, "has_memory_transient")
    _edge(agent, request, "has_recall_candidate", recall)
    _edge(agent, recall, "recalls_episode", episode)
    agent.tick()

    reconstructed = list(agent.inner.neighbours(
        recall, "has_reconstructed_belief"
    ))[0]
    attrs = agent.s.node(reconstructed)["attrs"]
    assert attrs["provenance_kind"] == "remembered"
    assert attrs["observation_status"] == "not_observed"
    assert attrs["status"] == "reconstructed"
    assert agent.s.node(perceived)["attrs"]["status"] == "current"


def test_action_conditioned_rollout_is_content_bearing_and_budget_bounded():
    agent = WorldAdapter(seeds=("generative_world_model",))
    _, belief = _perceive(agent)
    request, _, _ = _model_fixture(agent, belief, budget=6)

    assert agent.tick() > 0
    assert agent.s.node(request)["attrs"]["status"] == "completed"

    trajectories = _nodes(agent, "PredictionTrajectory")
    states = _nodes(agent, "PredictedBeliefState")
    observations = _nodes(agent, "PredictedObservation")
    outcomes = _nodes(agent, "PredictedOutcome")
    features = _nodes(agent, "PredictedFeature")

    assert len(trajectories) == 2
    # The request authorizes six state nodes. Branch allocation cannot exceed
    # that graph-held resource budget.
    assert 2 <= len(states) <= 6
    assert len(observations) == len(outcomes) == len(states)
    assert len(features) == len(states)
    assert {agent.s.node(s)["attrs"]["state_kind"] for s in states} >= {
        "junction", "corridor",
    }
    assert all(
        agent.s.node(s)["attrs"]["depth"] <= 3.0 for s in states
    )
    for node in trajectories + states + observations + outcomes + features:
        attrs = agent.s.node(node)["attrs"]
        assert attrs["provenance_kind"] == "imagined"
        assert attrs["observation_status"] == "not_observed"

    count = len(agent.s.nodes())
    assert agent.tick() == 0
    assert len(agent.s.nodes()) == count


def test_perceived_prediction_error_revises_transition_once():
    agent = WorldAdapter(seeds=("generative_world_model",))
    _, belief = _perceive(agent)
    request, _, transitions = _model_fixture(agent, belief)
    agent.tick()
    assert agent.s.node(request)["attrs"]["status"] == "completed"

    prediction = _nodes(agent, "PredictedOutcome")[0]
    transition = list(agent.inner.neighbours(
        prediction, "generated_by_transition"
    ))[0]
    old_confidence = agent.s.node(transition)["attrs"]["confidence"]
    actual = _add(agent, "WorldModelObservation", {
        "belief_status": "integrated",
        "prediction_comparison_status": "uncompared",
        "provenance_kind": "perceived",
        "state_kind": "outcome",
        "state_summary": "grounded action receipt",
        "epoch": 2.0,
        "confidence": 1.0,
        "uncertainty": 0.0,
        "observed_outcome_value": (
            agent.s.node(prediction)["attrs"]["outcome_value"] + 0.8
        ),
    }, "has_world_model_observation")
    _edge(agent, actual, "confirms_prediction", prediction)

    agent.tick()

    errors = _nodes(agent, "WorldModelPredictionError")
    assert len(errors) == 1
    assert agent.s.node(errors[0])["attrs"]["status"] == "integrated"
    assert agent.s.node(errors[0])["attrs"]["magnitude"] == pytest.approx(0.8)
    revised = agent.s.node(transition)["attrs"]
    assert revised["confidence"] < old_confidence
    assert revised["uncertainty"] > 0.2
    assert revised["revision_count"] == 1.0

    agent.tick()
    assert agent.s.node(transition)["attrs"]["revision_count"] == 1.0
    assert len(_nodes(agent, "WorldModelPredictionError")) == 1
    assert transition in transitions


def test_deadline_stales_then_prunes_simulation_family():
    agent = WorldAdapter(seeds=("generative_world_model",))
    _, belief = _perceive(agent)
    request, clock, _ = _model_fixture(agent, belief, deadline=3)
    agent.tick()

    agent.inner.set_attr(clock, "epoch", 4.0)
    agent.tick()
    assert agent.s.node(request)["attrs"]["status"] == "expired"
    assert {
        agent.s.node(t)["attrs"]["status"]
        for t in _nodes(agent, "PredictionTrajectory")
    } == {"stale"}

    agent.inner.set_attr(clock, "epoch", 6.0)
    agent.tick()
    assert _nodes(agent, "SimulationRequest") == []
    assert _nodes(agent, "PredictionTrajectory") == []
    assert _nodes(agent, "PredictedBeliefState") == []
    assert _nodes(agent, "PredictedObservation") == []
    assert _nodes(agent, "PredictedOutcome") == []


def test_default_mode_uses_current_belief_for_real_trajectory_content():
    agent = WorldAdapter(seeds=(
        "affective_state_core",
        "dual_process_core",
        "generative_world_model",
        "default_mode_core",
    ))
    _, belief = _perceive(agent, epoch=10)
    _model_fixture(agent, belief, epoch=10, deadline=20, budget=6)
    # The fixture's standalone request is not part of default mode; retire it
    # after its model objects have supplied the shared transition repertoire.
    standalone = _nodes(agent, "SimulationRequest")[0]
    agent.inner.set_attr(standalone, "status", "cancelled")
    agent.inner.set_attr(standalone, "cleanup_after_epoch", 100.0)

    goal = _add(agent, "Goal", {
        "status": "unresolved", "name": "reach safety",
    }, "has_goal")
    sample = _add(agent, "NetworkModeSample", {
        "epoch": 10.0,
        "exteroceptive_load": 0.0,
        "task_demand": 0.0,
        "interoceptive_urgency": 0.0,
        "uncertainty": 0.2,
        "idle_duration": 8.0,
        "status": "raw",
    }, "has_network_mode_sample")
    assert goal and sample

    agent.tick()

    contexts = _nodes(agent, "InternallyGeneratedContext")
    assert len(contexts) == 1
    context = contexts[0]
    assert list(agent.inner.neighbours(
        context, "has_source_belief"
    )) == [belief]
    simulations = list(agent.inner.neighbours(
        context, "has_world_model_simulation"
    ))
    assert len(simulations) == 1
    assert agent.s.node(simulations[0])["attrs"]["status"] == "completed"
    trajectories = list(agent.inner.neighbours(
        context, "has_prediction_trajectory"
    ))
    assert trajectories
    assert all(
        agent.s.node(t)["attrs"]["provenance_kind"] == "imagined"
        for t in trajectories
    )
