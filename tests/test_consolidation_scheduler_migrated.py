"""Execution gates for consolidation_scheduler (P1.B1)."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "consolidation_scheduler.json"
GENERATOR = ROOT / "scripts" / "gen_consolidation_scheduler_seed.py"

for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

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


def _attrs(agent, node):
    return agent.s.node(node)["attrs"]


def _fresh(*, enabled=False):
    agent = WorldAdapter(seeds=(
        "affective_state_core",
        "dual_process_core",
        "default_mode_core",
        "episodic_working_memory_core",
        "consolidation_scheduler",
    ))
    policies = _nodes(agent, "ConsolidationSchedulerPolicy")
    assert len(policies) == 1
    if enabled:
        agent.s.set_attr(policies[0], "enabled", 1.0)
    return agent


def _sample(agent, epoch, *, external=0.0, task=0.0, urgency=0.0,
            uncertainty=0.0, idle=8.0):
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


def _experience(
    agent,
    *,
    event_key,
    cue_key,
    context_key="doom-room",
    schema_name="safe_route",
    epoch=1.0,
    salience=0.5,
    surprise=0.5,
    value=0.5,
):
    context = agent.s.add_node("MemoryContext", {"context_key": context_key})
    schema = agent.s.add_node("MemorySchema", {"name": schema_name})
    event = agent.s.add_node(
        "EpisodicEvent",
        {
            "event_key": event_key,
            "cue_key": cue_key,
            "epoch": float(epoch),
            "salience": float(salience),
            "surprise": float(surprise),
            "value": float(value),
            "observation_status": "observed",
            "provenance_kind": "perceived",
            "state_kind": "world_state",
            "state_summary": "experienced world state",
        },
    )
    _edge(agent, agent.agent, "experienced_event", event)
    _edge(agent, event, "in_context", context)
    _edge(agent, event, "instantiates_schema", schema)
    return event, context, schema


def _gate(agent, operation, epoch, *, content=None, slot=None, task="doom", priority=0.5):
    gate = agent.s.add_node(
        "WorkingMemoryGate",
        {
            "status": "pending",
            "operation": operation,
            "epoch": float(epoch),
            "task_context_key": task,
            "priority": float(priority),
        },
    )
    _edge(agent, agent.agent, "has_working_memory_gate", gate)
    if content is not None:
        _edge(agent, gate, "targets_content", content)
    if slot is not None:
        _edge(agent, gate, "targets_slot", slot)
    return gate


def test_generator_reproduces_committed_seed_exactly():
    before = SEED.read_bytes()
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert SEED.read_bytes() == before


def test_disabled_policy_produces_no_memory_cycle():
    agent = _fresh(enabled=False)
    _experience(agent, event_key="ev1", cue_key="c1")
    _sample(agent, 1, idle=8.0)

    agent.tick()

    assert _nodes(agent, "MemoryCycle") == []
    assert list(agent.inner.neighbours(agent.agent, "has_memory_clock")) == []


def test_idle_samples_mint_cooldown_paced_offline_cycles_and_semantic_support():
    agent = _fresh(enabled=True)
    # Disable DMN episode context minting so we measure consolidation_scheduler cleanly,
    # or leave DMN enabled (both share NetworkModeState).
    _experience(
        agent,
        event_key="routine",
        cue_key="corridor",
        schema_name="safe_route",
        salience=0.4,
        surprise=0.1,
        value=0.3,
    )
    _experience(
        agent,
        event_key="surprising",
        cue_key="secret-door",
        schema_name="secret_route",
        salience=0.7,
        surprise=1.0,
        value=0.8,
    )
    agent.tick()
    episodes = _nodes(agent, "Episode")
    assert len(episodes) == 2

    minted_cycle_epochs = []
    for epoch in range(1, 17):
        _sample(agent, epoch, idle=8.0, task=0.0, external=0.0)
        agent.tick()
        for cyc in _nodes(agent, "MemoryCycle"):
            c_attrs = _attrs(agent, cyc)
            if c_attrs["epoch"] == float(epoch):
                minted_cycle_epochs.append(epoch)
                assert c_attrs["status"] == "completed"
                assert c_attrs["mode"] == "offline"
                assert c_attrs["source"] == "consolidation_scheduler"
                replays = list(agent.inner.neighbours(cyc, "selected_replay"))
                assert len(replays) == 1

    # With cooldown_epochs == 4.0, cycles mint at epochs 1, 5, 9, 13 (4 total in 1..16).
    assert minted_cycle_epochs == [1, 5, 9, 13]
    total_replays = sum(_attrs(agent, ep)["replay_count"] for ep in episodes)
    assert total_replays == 4.0

    supports = _nodes(agent, "SemanticSupport")
    assert len(supports) >= 1
    assert sum(_attrs(agent, s)["support_count"] for s in supports) == 4.0


def test_high_task_demand_suppresses_offline_cycles():
    agent = _fresh(enabled=True)
    _experience(agent, event_key="ev1", cue_key="c1")
    agent.tick()

    for epoch in range(1, 17):
        _sample(agent, epoch, idle=8.0, task=0.9, external=0.0)
        agent.tick()

    assert _nodes(agent, "MemoryCycle") == []
    assert _nodes(agent, "ReplayTrace") == []


def test_long_64_epoch_stream_keeps_cycles_and_total_nodes_bounded():
    agent = _fresh(enabled=True)
    _experience(agent, event_key="ev1", cue_key="c1", schema_name="route_a")
    _experience(agent, event_key="ev2", cue_key="c2", schema_name="route_b")
    agent.tick()

    for epoch in range(1, 65):
        _sample(agent, epoch, idle=8.0, task=0.0, external=0.0)
        agent.tick()
        # retention_epochs (4.0) / cooldown_epochs (4.0) + 1 == 2
        assert len(_nodes(agent, "MemoryCycle")) <= 2
        assert len(_nodes(agent, "ReplayTrace")) <= 2

    assert len(_nodes(agent, "MemoryCycle")) <= 2
    assert len(agent.s.nodes()) < 50


def test_bound_memory_clock_expires_unmaintained_working_memory_slot():
    agent = _fresh(enabled=True)
    mode = _nodes(agent, "NetworkModeState")[0]

    content = agent.s.add_node("Concept", {"name": "temporary-target"})
    _gate(agent, "input", 1, content=content)
    _sample(agent, 1, idle=8.0)
    agent.tick()

    assert list(agent.inner.neighbours(agent.agent, "has_memory_clock")) == [mode]
    slots = _nodes(agent, "WorkingMemorySlot")
    assert len(slots) == 1
    slot = slots[0]
    assert _attrs(agent, slot)["status"] == "active"

    expires_epoch = _attrs(agent, slot)["expires_epoch"]
    _sample(agent, expires_epoch, idle=8.0)
    agent.tick()

    assert _attrs(agent, slot)["status"] == "expired"
    assert _attrs(agent, slot)["terminal_reason"] == "maintenance_lapsed"
    assert list(agent.inner.neighbours(slot, "holds_content")) == []
