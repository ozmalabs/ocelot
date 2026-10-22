"""P13 sleep lifecycle contract gates, starting from the existing scheduler."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import pytest
pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _nodes(agent, kind):
    return [nid for nid in agent.s.nodes()
            if agent.s.node(nid)["type"] == kind]


def _fresh(*, enabled=True):
    agent = WorldAdapter(seeds=(
        "affective_state_core", "dual_process_core", "default_mode_core",
        "episodic_working_memory_core", "consolidation_scheduler",
    ))
    policies = _nodes(agent, "ConsolidationSchedulerPolicy")
    assert len(policies) == 1
    agent.s.set_attr(policies[0], "enabled", 1.0 if enabled else 0.0)
    context = agent.s.add_node("MemoryContext", {"context_key": "sleep-test"})
    schema = agent.s.add_node("MemorySchema", {"name": "verified-route"})
    episode = agent.s.add_node("EpisodicEvent", {
        "event_key": "sleep-event", "cue_key": "sleep-cue", "epoch": 0.0,
        "salience": 0.8, "surprise": 0.5, "value": 0.5,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "observed state",
    })
    _edge(agent, agent.agent, "experienced_event", episode)
    _edge(agent, episode, "in_context", context)
    _edge(agent, episode, "instantiates_schema", schema)
    return agent, episode


def _sample(agent, epoch, *, task=0.0):
    sample = agent.s.add_node("NetworkModeSample", {
        "epoch": float(epoch), "exteroceptive_load": 0.0,
        "task_demand": float(task), "interoceptive_urgency": 0.0,
        "uncertainty": 0.0, "idle_duration": 8.0, "status": "raw",
    })
    _edge(agent, agent.agent, "has_network_mode_sample", sample)


def test_one_owner_per_cycle():
    agent, _ = _fresh()
    agent.tick()
    _sample(agent, 1)
    agent.tick()

    cycles = _nodes(agent, "MemoryCycle")
    assert len(cycles) == 1
    assert agent.s.node(cycles[0])["attrs"]["source"] == "consolidation_scheduler"
    assert len(list(agent.inner.neighbours(cycles[0], "selected_replay"))) == 1


def test_replay_not_duplicated():
    agent, episode = _fresh()
    agent.tick()
    episode = _nodes(agent, "Episode")[0]
    _sample(agent, 1)
    agent.tick()
    cycle = _nodes(agent, "MemoryCycle")[0]
    assert agent.s.node(episode)["attrs"]["replay_count"] == 1.0

    # A repeated graph tick cannot turn the completed cycle into a second replay.
    agent.tick()
    assert agent.s.node(episode)["attrs"]["replay_count"] == 1.0
    assert len(list(agent.inner.neighbours(cycle, "selected_replay"))) == 1


def test_foreground_interrupts_before_offline_entry():
    agent, _ = _fresh()
    agent.tick()
    _sample(agent, 1, task=0.9)
    agent.tick()

    assert _nodes(agent, "MemoryCycle") == []
    assert _nodes(agent, "ReplayTrace") == []


def test_repeat_same_cycle_no_double_debit():
    # Current scheduler baseline has one admission debit; repeated ticks with
    # the same epoch cannot replay or debit that completed cycle again. True
    # checkpoint resume awaits the staged lifecycle in P13.02.
    agent = WorldAdapter(seeds=(
        "affective_state_core", "dual_process_core", "default_mode_core",
        "episodic_working_memory_core", "consolidation_scheduler",
        "thinking_budget",
    ))
    policy = _nodes(agent, "ConsolidationSchedulerPolicy")[0]
    budget = _nodes(agent, "ThinkingBudget")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    agent.s.set_attr(budget, "enabled", 1.0)
    agent.s.set_attr(budget, "remaining", 5.0)
    agent.s.set_attr(budget, "capacity", 5.0)
    agent.s.set_attr(budget, "last_refill_epoch", 1.0)
    context = agent.s.add_node("MemoryContext", {"context_key": "budget-sleep"})
    schema = agent.s.add_node("MemorySchema", {"name": "budget-route"})
    episode = agent.s.add_node("EpisodicEvent", {
        "event_key": "budget-event", "cue_key": "budget-cue", "epoch": 0.0,
        "salience": 0.8, "surprise": 0.5, "value": 0.5,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "observed state",
    })
    _edge(agent, agent.agent, "experienced_event", episode)
    _edge(agent, episode, "in_context", context)
    _edge(agent, episode, "instantiates_schema", schema)
    agent.tick()
    _sample(agent, 1)
    agent.tick()
    remaining = agent.s.node(budget)["attrs"]["remaining"]
    count = len(_nodes(agent, "MemoryCycle"))

    agent.tick()
    agent.tick()
    assert len(_nodes(agent, "MemoryCycle")) == count
    assert agent.s.node(budget)["attrs"]["remaining"] == remaining
