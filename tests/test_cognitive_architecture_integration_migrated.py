"""Cross-faculty contracts for the graph-native cognitive architecture.

These tests provide only synthetic observations, clocks, gate commands and
receipts at the adapter boundary.  All cognition under test is seed-held graph
data executed by the Rust rule engine.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _add(agent, node_type, attrs, edge_type=None):
    node = agent.s.add_node(node_type, attrs)
    if edge_type is not None:
        _edge(agent, agent.agent, edge_type, node)
    return node


def _nodes(agent, node_type):
    return [
        node
        for node in agent.s.nodes()
        if agent.s.node(node)["type"] == node_type
    ]


def _attrs(agent, node):
    return agent.s.node(node)["attrs"]


def test_full_core_boot_is_quiescent_without_world_input():
    agent = WorldAdapter()
    before = len(agent.s.nodes())

    assert agent.tick() == 0
    assert agent.tick() == 0
    assert len(agent.s.nodes()) == before


def test_only_grounded_event_binds_and_replay_does_not_launder_observation():
    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    context = _add(agent, "MemoryContext", {"context_key": "doom-room"})
    schema = _add(agent, "MemorySchema", {"name": "door_affordance"})

    grounded = _add(
        agent,
        "EpisodicEvent",
        {
            "event_key": "door-opened",
            "cue_key": "door",
            "epoch": 1.0,
            "salience": 0.8,
            "surprise": 0.9,
            "value": 0.7,
            "provenance_kind": "perceived",
            "observation_status": "observed",
        },
        "experienced_event",
    )
    imagined = _add(
        agent,
        "EpisodicEvent",
        {
            "event_key": "imagined-door",
            "cue_key": "door",
            "epoch": 1.0,
            "salience": 1.0,
            "surprise": 1.0,
            "value": 1.0,
            # A contradictory status must fail closed rather than allowing an
            # imagined event to become autobiographical evidence.
            "provenance_kind": "imagined",
            "observation_status": "observed",
        },
        "experienced_event",
    )
    for event in (grounded, imagined):
        _edge(agent, event, "in_context", context)
        _edge(agent, event, "instantiates_schema", schema)

    agent.tick()

    episodes = _nodes(agent, "Episode")
    assert len(episodes) == 1
    assert list(agent.inner.neighbours(episodes[0], "bound_event")) == [
        grounded
    ]

    cycle = _add(
        agent,
        "MemoryCycle",
        {"status": "pending", "mode": "wake", "epoch": 2.0},
        "has_memory_cycle",
    )
    agent.tick()

    replay = list(agent.inner.neighbours(cycle, "selected_replay"))[0]
    assert _attrs(agent, replay)["provenance_kind"] == "replayed"
    assert _attrs(agent, replay)["observation_status"] == "not_observed"
    support = _nodes(agent, "SemanticSupport")[0]
    assert _attrs(agent, support)["observation_status"] == "not_observed"


def test_memory_recall_reconstructs_nonobserved_world_model_belief():
    agent = WorldAdapter(
        seeds=("episodic_working_memory_core", "generative_world_model")
    )
    context = _add(agent, "MemoryContext", {"context_key": "doom-room"})
    schema = _add(agent, "MemorySchema", {"name": "door_affordance"})
    event = _add(
        agent,
        "EpisodicEvent",
        {
            "event_key": "door-opened",
            "cue_key": "door",
            "state_kind": "corridor",
            "state_summary": "the door opened",
            "epoch": 1.0,
            "salience": 0.8,
            "surprise": 0.7,
            "value": 0.6,
            "provenance_kind": "perceived",
            "observation_status": "observed",
        },
        "experienced_event",
    )
    _edge(agent, event, "in_context", context)
    _edge(agent, event, "instantiates_schema", schema)
    agent.tick()

    request = _add(
        agent,
        "MemoryRetrievalRequest",
        {"status": "pending", "cue_key": "door", "epoch": 3.0},
        "has_memory_retrieval_request",
    )
    agent.tick()

    recall = list(agent.inner.neighbours(request, "has_recall_candidate"))[0]
    beliefs = list(agent.inner.neighbours(
        recall, "has_reconstructed_belief"
    ))
    assert len(beliefs) == 1
    belief = beliefs[0]
    assert _attrs(agent, belief)["state_kind"] == "corridor"
    assert _attrs(agent, belief)["state_summary"] == "the door opened"
    assert _attrs(agent, belief)["provenance_kind"] == "remembered"
    assert _attrs(agent, belief)["observation_status"] == "not_observed"


def test_dead_end_rollout_terminalizes_and_completes_without_clock_advance():
    agent = WorldAdapter(seeds=("generative_world_model",))
    observation = _add(
        agent,
        "WorldModelObservation",
        {
            "belief_status": "new",
            "prediction_comparison_status": "uncompared",
            "provenance_kind": "perceived",
            "state_kind": "corridor",
            "state_summary": "corridor",
            "epoch": 1.0,
            "confidence": 0.9,
            "uncertainty": 0.1,
        },
        "has_world_model_observation",
    )
    agent.tick()
    belief = _nodes(agent, "BeliefState")[0]
    action = _add(
        agent,
        "WorldModelAction",
        {"action_kind": "forward", "branch_rank": 1.0},
        "has_world_model_action",
    )
    transition = _add(
        agent,
        "TransitionHypothesis",
        {
            "source_state_kind": "corridor",
            "action_kind": "forward",
            "successor_state_kind": "dead_end",
            "successor_summary": "a dead end",
            "predicted_observation_kind": "wall",
            "predicted_observation_value": 0.0,
            "predicted_outcome_kind": "blocked",
            "predicted_outcome_value": -0.2,
            "confidence": 0.8,
            "uncertainty": 0.2,
            "model_rank": 1.0,
            "revision_count": 0.0,
        },
        "has_transition_hypothesis",
    )
    clock = _add(agent, "WorldModelClock", {"epoch": 1.0})
    request = _add(
        agent,
        "SimulationRequest",
        {
            "status": "active",
            "request_kind": "dead_end_probe",
            "provenance_kind": "imagined",
            "observation_status": "not_observed",
            "input_epoch": 1.0,
            "deadline_epoch": 10.0,
            "horizon": 4.0,
            "budget": 6.0,
            "maximum_branching": 1.0,
        },
        "has_simulation_request",
    )
    _edge(agent, request, "has_source_belief", belief)
    _edge(agent, request, "considers_action", action)
    _edge(agent, request, "validated_by_clock", clock)

    agent.tick()

    assert observation and transition
    assert _attrs(agent, request)["status"] == "completed"
    states = _nodes(agent, "PredictedBeliefState")
    assert len(states) == 1
    assert _attrs(agent, states[0])["expansion_status"] == "terminal"
    assert _attrs(agent, states[0])["terminal_reason"] == (
        "no_applicable_transition"
    )
    assert agent.tick() == 0


def test_default_mode_trajectory_is_revised_only_by_grounded_outcome():
    agent = WorldAdapter(
        seeds=(
            "affective_state_core",
            "dual_process_core",
            "generative_world_model",
            "default_mode_core",
        )
    )
    _add(
        agent,
        "WorldModelObservation",
        {
            "belief_status": "new",
            "prediction_comparison_status": "uncompared",
            "provenance_kind": "perceived",
            "state_kind": "corridor",
            "state_summary": "door ahead",
            "epoch": 10.0,
            "confidence": 0.9,
            "uncertainty": 0.1,
        },
        "has_world_model_observation",
    )
    action = _add(
        agent,
        "WorldModelAction",
        {"action_kind": "forward", "branch_rank": 1.0},
        "has_world_model_action",
    )
    transition = _add(
        agent,
        "TransitionHypothesis",
        {
            "source_state_kind": "corridor",
            "action_kind": "forward",
            "successor_state_kind": "corridor",
            "successor_summary": "advance through corridor",
            "predicted_observation_kind": "corridor_progress",
            "predicted_observation_value": 0.4,
            "predicted_outcome_kind": "progress",
            "predicted_outcome_value": 0.4,
            "confidence": 0.8,
            "uncertainty": 0.2,
            "model_rank": 1.0,
            "revision_count": 0.0,
        },
        "has_transition_hypothesis",
    )
    _add(
        agent,
        "Goal",
        {"status": "unresolved", "name": "reach safety"},
        "has_goal",
    )
    _add(
        agent,
        "NetworkModeSample",
        {
            "epoch": 10.0,
            "exteroceptive_load": 0.0,
            "task_demand": 0.0,
            "interoceptive_urgency": 0.0,
            "uncertainty": 0.2,
            "idle_duration": 8.0,
            "status": "raw",
        },
        "has_network_mode_sample",
    )

    agent.tick()

    contexts = _nodes(agent, "InternallyGeneratedContext")
    assert len(contexts) == 1
    trajectories = list(agent.inner.neighbours(
        contexts[0], "has_prediction_trajectory"
    ))
    assert trajectories
    predictions = _nodes(agent, "PredictedOutcome")
    assert predictions
    assert all(
        _attrs(agent, prediction)["observation_status"] == "not_observed"
        for prediction in predictions
    )
    old_confidence = _attrs(agent, transition)["confidence"]

    grounded = _add(
        agent,
        "WorldModelObservation",
        {
            "belief_status": "integrated",
            "prediction_comparison_status": "uncompared",
            "provenance_kind": "perceived",
            "state_kind": "action_outcome",
            "state_summary": "grounded receipt",
            "epoch": 11.0,
            "confidence": 1.0,
            "uncertainty": 0.0,
            "observed_outcome_value": 1.0,
        },
        "has_world_model_observation",
    )
    _edge(agent, grounded, "confirms_prediction", predictions[0])
    agent.tick()

    errors = _nodes(agent, "WorldModelPredictionError")
    assert len(errors) == 1
    assert _attrs(agent, errors[0])["status"] == "integrated"
    assert _attrs(agent, transition)["revision_count"] == 1.0
    assert _attrs(agent, transition)["confidence"] != old_confidence
    assert agent.tick() == 0
    assert _attrs(agent, transition)["revision_count"] == 1.0
    assert action


def test_default_mode_admits_only_one_context_from_simultaneous_sources():
    agent = WorldAdapter(
        seeds=(
            "affective_state_core",
            "dual_process_core",
            "generative_world_model",
            "default_mode_core",
        )
    )
    for name in ("find exit", "find ammunition"):
        _add(
            agent,
            "Goal",
            {"status": "unresolved", "name": name},
            "has_goal",
        )
    _add(
        agent,
        "NetworkModeSample",
        {
            "epoch": 10.0,
            "exteroceptive_load": 0.0,
            "task_demand": 0.0,
            "interoceptive_urgency": 0.0,
            "uncertainty": 0.2,
            "idle_duration": 8.0,
            "status": "raw",
        },
        "has_network_mode_sample",
    )

    agent.tick()

    active = [
        context
        for context in _nodes(agent, "InternallyGeneratedContext")
        if _attrs(agent, context)["status"] == "active"
    ]
    assert len(active) == 1
    assert len(list(agent.inner.neighbours(
        active[0], "generated_from_goal"
    ))) == 1


def test_verified_action_outcome_updates_credit_and_forward_model_together():
    agent = WorldAdapter(seeds=("adaptive_control_core",))
    context = _add(agent, "AdaptiveContext", {"name": "doom"})
    state = _add(agent, "BeliefState", {"name": "corridor"})
    action = _add(
        agent, "MotorCommand", {"name": "turn", "command_value": 2.0}
    )
    controller = _add(agent, "Controller", {"name": "habit"})
    attention = _add(agent, "AttentionChoice", {"name": "door"})
    model = _add(
        agent,
        "ForwardModel",
        {
            "predicted_consequence": 2.0,
            "confidence": 0.6,
            "expected_noise": 0.1,
            "last_calibration_epoch": -1.0,
        },
    )
    decision = _add(
        agent,
        "AdaptiveDecision",
        {
            "status": "committed",
            "epoch": 10.0,
            "prediction_authored": 0,
            "trace_authored": 0,
            "sensorimotor_prediction_authored": 0,
            "reliable": 0,
            "option_evidence_used": 0,
        },
        "has_adaptive_decision",
    )
    for edge_type, target in (
        ("in_adaptive_context", context),
        ("selected_state", state),
        ("selected_action", action),
        ("selected_controller", controller),
        ("selected_attention", attention),
        ("uses_forward_model", model),
    ):
        _edge(agent, decision, edge_type, target)
    agent.tick()

    prediction = _nodes(agent, "OutcomePrediction")[0]
    outcome = _add(
        agent,
        "AdaptiveOutcome",
        {
            "status": "verified",
            "error_evaluated": 0,
            "epoch": 11.0,
            "observed_value": 1.0,
            "next_value": 0.0,
            "expected_noise": 0.1,
            "volatility": 0.2,
            "model_ignorance": 0.1,
        },
        "has_adaptive_outcome",
    )
    _edge(agent, outcome, "evaluates_prediction", prediction)
    _edge(agent, outcome, "in_adaptive_context", context)
    consequence = _add(
        agent,
        "SensoryConsequence",
        {
            "status": "observed",
            "receipt_verified": 1,
            "calibration_applied": 0,
            "epoch": 11.0,
            "signal_value": 2.5,
        },
    )
    _edge(agent, consequence, "reports_decision", decision)
    agent.tick()

    assert _attrs(agent, outcome)["prediction_error"] == pytest.approx(1.0)
    assert len(_nodes(agent, "CreditAssignment")) == 1
    assert _attrs(
        agent, _nodes(agent, "ControllerValue")[0]
    )["experience_count"] == 1.0
    residual = _nodes(agent, "SensorimotorResidual")[0]
    assert _attrs(agent, residual)["residual"] == pytest.approx(0.5)
    assert _attrs(agent, residual)["attribution"] == (
        "self_generated_receipt_backed"
    )
    assert _attrs(agent, model)["predicted_consequence"] == pytest.approx(
        2.125
    )
    assert agent.tick() == 0


def test_working_memory_output_can_win_functional_broadcast_and_route():
    agent = WorldAdapter(
        seeds=("episodic_working_memory_core", "adaptive_control_core")
    )
    consumer = _add(
        agent,
        "BroadcastConsumer",
        {"name": "planning"},
        "has_broadcast_consumer",
    )
    content = _add(agent, "Concept", {"name": "open-door-action"})
    input_gate = _add(
        agent,
        "WorkingMemoryGate",
        {
            "status": "pending",
            "operation": "input",
            "epoch": 1.0,
            "task_context_key": "doom",
            "priority": 0.9,
        },
        "has_working_memory_gate",
    )
    _edge(agent, input_gate, "targets_content", content)
    agent.tick()
    slot = list(agent.inner.neighbours(input_gate, "created_slot"))[0]

    output_gate = _add(
        agent,
        "WorkingMemoryGate",
        {
            "status": "pending",
            "operation": "output",
            "epoch": 2.0,
            "task_context_key": "doom",
            "priority": 0.9,
        },
        "has_working_memory_gate",
    )
    _edge(agent, output_gate, "targets_slot", slot)
    agent.tick()

    output = list(agent.inner.neighbours(
        output_gate, "has_working_memory_output"
    ))[0]
    broadcasts = [
        broadcast
        for broadcast in _nodes(agent, "FunctionalBroadcast")
        if list(agent.inner.neighbours(
            broadcast, "broadcasts_content"
        )) == [content]
    ]
    assert len(broadcasts) == 1
    assert list(agent.inner.neighbours(
        broadcasts[0], "available_to_consumer"
    )) == [consumer]
    assert _attrs(agent, broadcasts[0])["provenance_kind"] == (
        "working_memory_retrieval"
    )


def test_exact_tie_refuses_broadcast_instead_of_using_graph_order():
    agent = WorldAdapter(seeds=("adaptive_control_core",))
    candidates = []
    for index in range(2):
        content = _add(agent, "BroadcastContent", {"index": index})
        candidate = _add(
            agent,
            "BroadcastCandidate",
            {
                "epoch": 1.0,
                "status": "pending",
                "salience": 0.5,
                "urgency": 0.2,
                "confidence": 1.0,
                "precision": 1.0,
                "ttl": 2.0,
                "priority": 0.0,
                "source_kind": "integration_test",
                "provenance_kind": "perceived",
            },
            "has_broadcast_candidate",
        )
        _edge(agent, candidate, "about_content", content)
        candidates.append(candidate)

    agent.tick()

    assert _nodes(agent, "FunctionalBroadcast") == []
    ties = _nodes(agent, "BroadcastTie")
    assert len(ties) == 1
    assert _attrs(agent, ties[0])["reason"] == "exact_priority_tie"
    assert {
        _attrs(agent, candidate)["status"] for candidate in candidates
    } == {"refused_exact_tie"}
    assert agent.tick() == 0


def test_simultaneous_working_memory_inputs_respect_capacity():
    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    policy = _nodes(agent, "WorkingMemoryPolicy")[0]
    agent.inner.set_attr(policy, "maximum_slots", 2.0)

    gates = []
    for index in range(4):
        content = _add(agent, "Concept", {"name": f"item-{index}"})
        gate = _add(
            agent,
            "WorkingMemoryGate",
            {
                "status": "pending",
                "operation": "input",
                "epoch": 1.0,
                "task_context_key": "doom",
                "priority": float(index),
            },
            "has_working_memory_gate",
        )
        _edge(agent, gate, "targets_content", content)
        gates.append(gate)

    agent.tick()

    active = [
        slot
        for slot in _nodes(agent, "WorkingMemorySlot")
        if _attrs(agent, slot)["status"] == "active"
    ]
    assert len(active) == 2
    assert sum(
        _attrs(agent, gate)["status"] == "processed" for gate in gates
    ) == 4
    assert len(_nodes(agent, "WorkingMemoryGateResult")) == 4
