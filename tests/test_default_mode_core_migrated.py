"""Focused tests for graph-native intrinsic/default-mode control."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import CORE_SEEDS
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


def _fresh():
    # WorldAdapter's explicit seed tuple is a mechanical manifest list rather
    # than the registry's dependency resolver, so name the declared closure.
    return WorldAdapter(seeds=(
        "affective_state_core", "dual_process_core", "default_mode_core",
    ))


def _sample(agent, epoch, *, external=0.0, task=0.0, urgency=0.0,
            uncertainty=0.0, idle=5.0):
    sample = agent.s.add_node("NetworkModeSample", {
        "epoch": float(epoch),
        "exteroceptive_load": float(external),
        "task_demand": float(task),
        "interoceptive_urgency": float(urgency),
        "uncertainty": float(uncertainty),
        "idle_duration": float(idle),
        "status": "raw",
    })
    _edge(agent, agent.agent, "has_network_mode_sample", sample)
    return sample


def test_default_core_installs_dormant_mode_without_runaway_activity():
    assert "default_mode_core" in CORE_SEEDS
    agent = WorldAdapter()

    assert len(_nodes(agent, "NetworkModeState")) == 1
    before = len(agent.s.nodes())
    assert agent.tick() == 0
    assert agent.tick() == 0
    assert len(agent.s.nodes()) == before
    assert _nodes(agent, "InternallyGeneratedContext") == []


def test_mode_sample_updates_continuous_overlapping_network_weights():
    agent = _fresh()
    _sample(
        agent, 1, external=0.35, task=0.4, urgency=0.2,
        uncertainty=0.6, idle=3.0,
    )

    assert agent.tick() > 0
    mode = agent.s.node(_nodes(agent, "NetworkModeState")[0])["attrs"]

    assert mode["epoch"] == 1.0
    assert mode["exteroceptive_load"] == pytest.approx(0.35)
    assert mode["task_demand"] == pytest.approx(0.4)
    assert mode["interoceptive_urgency"] == pytest.approx(0.2)
    assert mode["uncertainty"] == pytest.approx(0.6)
    assert mode["idle_duration"] == pytest.approx(3.0)
    assert mode["external_attention_weight"] == pytest.approx(0.4)
    assert mode["executive_control_weight"] == pytest.approx(0.7)
    assert mode["salience_weight"] == pytest.approx(0.35)
    assert 0.0 < mode["default_mode_weight"] < 1.0
    # More than one network can carry weight at once: no exclusive mode switch.
    assert mode["executive_control_weight"] > 0.0
    assert mode["default_mode_weight"] > 0.0


def test_low_demand_mints_one_bounded_prospective_context_with_provenance():
    agent = _fresh()
    goal = agent.s.add_node("Goal", {
        "status": "unresolved", "name": "find_a_safe_route",
    })
    _edge(agent, agent.agent, "has_goal", goal)
    _sample(agent, 10, uncertainty=0.3, idle=8.0)

    agent.tick()

    contexts = _nodes(agent, "InternallyGeneratedContext")
    assert len(contexts) == 1
    context = contexts[0]
    context_attrs = agent.s.node(context)["attrs"]
    assert context_attrs["status"] == "active"
    assert context_attrs["source_kind"] == "unresolved_goal"
    assert context_attrs["deadline_epoch"] == 14.0
    assert context_attrs["budget_remaining"] == 2.0
    assert list(agent.inner.neighbours(context, "generated_from_goal")) == [goal]

    scenario = _nodes(agent, "ImaginedScenario")
    prediction = _nodes(agent, "PredictedState")
    request = _nodes(agent, "SystemTwoEscalation")
    assert len(scenario) == len(prediction) == len(request) == 1
    assert agent.s.node(scenario[0])["attrs"]["provenance_kind"] == "imagined"
    assert agent.s.node(scenario[0])["attrs"]["observation_status"] == "not_observed"
    assert agent.s.node(prediction[0])["attrs"]["provenance_kind"] == "predicted"
    assert agent.s.node(prediction[0])["attrs"]["observation_status"] == "not_observed"
    assert agent.s.node(request[0])["attrs"]["task_kind"] == "prospective_simulation"
    assert agent.s.node(request[0])["attrs"]["input_epoch"] == 10.0
    task_sets = list(agent.inner.neighbours(request[0], "recruits_task_set"))
    assert {
        agent.s.node(task_set)["attrs"]["area"] for task_set in task_sets
    } == {"default_mode_prospection", "world_model_simulation"}
    assert _nodes(agent, "Observation") == []

    # A fixed-point re-tick at the same epoch cannot mint or spend again.
    count = len(agent.s.nodes())
    assert agent.tick() == 0
    assert len(agent.s.nodes()) == count
    assert agent.s.node(context)["attrs"]["budget_remaining"] == 2.0


def test_default_mode_projection_uses_scoped_native_task_fold():
    agent = _fresh()
    goal = agent.s.add_node("Goal", {
        "status": "unresolved", "name": "find_a_safe_route",
    })
    _edge(agent, agent.agent, "has_goal", goal)
    _sample(agent, 10, uncertainty=0.3, idle=8.0)

    report = agent.dual_process_tick(trace=True)

    assert report["tasks_requested"] == 1
    assert report["tasks_completed"] == 1
    assert report["tasks_stale"] == 0
    assert report["task_workers_used"] == 1
    assert report["system_two_escalations"] == 1
    context = _nodes(agent, "InternallyGeneratedContext")[0]
    task = _nodes(agent, "CognitiveTask")[0]
    result = _nodes(agent, "TaskResult")[0]
    assert agent.s.node(task)["attrs"]["kind"] == "default_mode_projection"
    assert agent.s.node(task)["attrs"]["execution_class"] == "system_two"
    assert agent.s.node(task)["attrs"]["status"] == "done"
    assert list(agent.inner.neighbours(task, "about_context")) == [context]
    assert agent.s.node(result)["attrs"]["status"] == "done"
    assert agent.s.node(result)["attrs"]["source_epoch"] == 10
    scenario = _nodes(agent, "ImaginedScenario")[0]
    assert agent.s.node(scenario)["attrs"]["simulation_output"] == (
        4.0, 2.0, 0.7
    )


def test_consolidated_episode_can_seed_replay_when_no_goal_is_available():
    agent = _fresh()
    episode = agent.s.add_node("Episode", {
        "consolidated": True, "kind": "navigation", "salience": 1.0,
    })
    _edge(agent, agent.agent, "recorded_episode", episode)
    _sample(agent, 3, idle=6.0)

    agent.tick()

    context = _nodes(agent, "InternallyGeneratedContext")
    assert len(context) == 1
    assert agent.s.node(context[0])["attrs"]["source_kind"] == "episodic_memory"
    assert list(agent.inner.neighbours(context[0], "replays_episode")) == [episode]
    request = _nodes(agent, "SystemTwoEscalation")
    assert len(request) == 1
    assert agent.s.node(request[0])["attrs"]["task_kind"] == "episodic_replay"


def test_salient_external_input_interrupts_and_terminal_nodes_are_pruned():
    agent = _fresh()
    goal = agent.s.add_node("Goal", {"status": "pending"})
    _edge(agent, agent.agent, "has_goal", goal)
    _sample(agent, 1, idle=8.0)
    agent.tick()
    context = _nodes(agent, "InternallyGeneratedContext")[0]
    request = _nodes(agent, "SystemTwoEscalation")[0]

    _sample(agent, 2, external=0.9, idle=0.0)
    agent.tick()

    assert agent.s.node(context)["attrs"]["status"] == "interrupted"
    assert agent.s.node(context)["attrs"]["terminal_reason"] == (
        "salient_external_demand"
    )
    assert agent.s.node(request)["attrs"]["status"] == "cancelled"
    assert agent.s.node(request)["attrs"]["terminal_reason"] == (
        "salient_external_demand"
    )

    # retention_epochs=2: at epoch 4, context and all transient descendants go.
    _sample(agent, 4, external=0.9, idle=0.0)
    agent.tick()
    assert _nodes(agent, "InternallyGeneratedContext") == []
    assert _nodes(agent, "SystemTwoEscalation") == []
    assert _nodes(agent, "ImaginedScenario") == []
    assert _nodes(agent, "PredictedState") == []


def test_context_deadline_is_independent_of_its_resource_budget():
    agent = _fresh()
    policy = _nodes(agent, "DefaultModePolicy")[0]
    agent.inner.set_attr(policy, "context_budget", 100.0)
    agent.inner.set_attr(policy, "maximum_context_epochs", 2.0)
    goal = agent.s.add_node("Goal", {"status": "unresolved"})
    _edge(agent, agent.agent, "has_goal", goal)
    _sample(agent, 20, idle=8.0)
    agent.tick()
    context = _nodes(agent, "InternallyGeneratedContext")[0]

    _sample(agent, 22, idle=8.0)
    agent.tick()

    attrs = agent.s.node(context)["attrs"]
    assert attrs["status"] == "expired"
    assert attrs["terminal_reason"] == "deadline"
    assert attrs["budget_remaining"] == 99.0


def test_long_idle_stream_remains_bounded_by_budget_cooldown_and_cleanup():
    agent = _fresh()
    goal = agent.s.add_node("Goal", {"status": "unresolved"})
    _edge(agent, agent.agent, "has_goal", goal)

    maximum_transients = 0
    for epoch in range(1, 65):
        _sample(agent, epoch, idle=8.0)
        agent.tick()
        transient_count = sum(
            len(_nodes(agent, typ))
            for typ in (
                "NetworkModeSample",
                "InternallyGeneratedContext",
                "SystemTwoEscalation",
                "ImaginedScenario",
                "PredictedState",
            )
        )
        maximum_transients = max(maximum_transients, transient_count)

    # One newest sample plus at most one retained terminal context family and
    # one active family. The exact ceiling is intentionally asserted tightly.
    assert maximum_transients <= 9
    assert len(_nodes(agent, "NetworkModeSample")) == 1
    assert len(_nodes(agent, "InternallyGeneratedContext")) <= 2
    assert len(agent.s.nodes()) < 30
