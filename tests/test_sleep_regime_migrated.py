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


def _sample(agent, epoch, *, task=0.0, external=0.0, urgency=0.0):
    sample = agent.s.add_node("NetworkModeSample", {
        "epoch": float(epoch), "exteroceptive_load": float(external),
        "task_demand": float(task), "interoceptive_urgency": float(urgency),
        "uncertainty": 0.0, "idle_duration": 8.0, "status": "raw",
    })
    _edge(agent, agent.agent, "has_network_mode_sample", sample)


def _staged_fresh(*, refill=0.0):
    agent = WorldAdapter(seeds=(
        "affective_state_core", "dual_process_core", "default_mode_core",
        "episodic_working_memory_core", "consolidation_scheduler",
        "thinking_budget", "sleep_regime",
    ))
    for kind, enabled in (("ConsolidationSchedulerPolicy", 1.0),
                          ("SleepRegimePolicy", 1.0),
                          ("ThinkingBudget", 1.0)):
        nodes = _nodes(agent, kind)
        assert len(nodes) == 1
        agent.s.set_attr(nodes[0], "enabled", enabled)
    budget = _nodes(agent, "ThinkingBudget")[0]
    agent.s.set_attr(budget, "capacity", 16.0)
    agent.s.set_attr(budget, "remaining", 16.0)
    agent.s.set_attr(budget, "refill_per_epoch", float(refill))
    agent.s.set_attr(_nodes(agent, "SleepRegimePolicy")[0], "decay_half_life", 1.0)
    context = agent.s.add_node("MemoryContext", {"context_key": "staged-sleep"})
    schema = agent.s.add_node("MemorySchema", {"name": "staged-route"})
    event = agent.s.add_node("EpisodicEvent", {
        "event_key": "staged-event", "cue_key": "staged-cue", "epoch": 0.0,
        "salience": 0.8, "surprise": 0.5, "value": 0.5,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "observed state",
    })
    _edge(agent, agent.agent, "experienced_event", event)
    _edge(agent, event, "in_context", context)
    _edge(agent, event, "instantiates_schema", schema)
    agent.tick()
    return agent


def _advance(agent, epoch, *, task=0.0, external=0.0, urgency=0.0):
    _sample(agent, epoch, task=task, external=external, urgency=urgency)
    agent.tick()


def _receipt_stages(agent, cycle):
    receipts = list(agent.inner.neighbours(cycle, "has_sleep_stage_receipt"))
    return [agent.s.node(node)["attrs"]["stage"] for node in receipts]


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


def test_stage_order():
    agent = _staged_fresh()
    budget = _nodes(agent, "ThinkingBudget")[0]
    _advance(agent, 1)
    cycles = _nodes(agent, "MemoryCycle")
    assert len(cycles) == 1
    cycle = cycles[0]
    assert _receipt_stages(agent, cycle) == ["replay"]
    replay_receipt = next(r for r in agent.inner.neighbours(cycle, "has_sleep_stage_receipt")
                          if agent.s.node(r)["attrs"]["stage"] == "replay")
    assert agent.s.node(replay_receipt)["attrs"]["shared_budget_debit"] == 1.0

    for epoch, expected in ((2, ["replay", "consolidate"]),
                            (3, ["replay", "consolidate", "decay"]),
                            (4, ["replay", "consolidate", "decay", "library"]),
                            (5, ["replay", "consolidate", "decay", "library", "recombine"])):
        _advance(agent, epoch)
        assert _receipt_stages(agent, cycle) == expected
    assert agent.s.node(cycle)["attrs"]["sleep_stage_cursor"] == "complete"
    receipts = list(agent.inner.neighbours(cycle, "has_sleep_stage_receipt"))
    for receipt, prior in zip(receipts[1:], receipts[:-1]):
        assert list(agent.inner.neighbours(receipt, "follows_stage_receipt")) == [prior]
    assert sum(agent.s.node(r)["attrs"]["shared_budget_debit"] for r in receipts) == 5.0
    assert all(agent.s.node(r)["attrs"]["shared_budget_debit"] == 1.0 for r in receipts)


def test_sleep_regime_disabled_by_default():
    agent = WorldAdapter(seeds=(
        "affective_state_core", "dual_process_core", "default_mode_core",
        "episodic_working_memory_core", "consolidation_scheduler",
        "thinking_budget", "sleep_regime",
    ))
    assert agent.s.node(_nodes(agent, "SleepRegimePolicy")[0])["attrs"]["enabled"] == 0.0
    assert _nodes(agent, "SleepStageReceipt") == []


def test_decay_once_per_epoch():
    agent = _staged_fresh()
    for epoch in range(1, 4):
        _advance(agent, epoch)
    support = _nodes(agent, "SemanticSupport")[0]
    cycle = _nodes(agent, "MemoryCycle")[0]
    assert agent.s.node(support)["attrs"]["sleep_freshness_epoch"] == 3.0
    assert agent.s.node(support)["attrs"]["sleep_freshness"] == 256.0
    assert agent.s.node(support)["attrs"]["sleep_decay_count"] == 1.0
    assert agent.s.node(support)["attrs"]["uncertainty"] == 0.5
    assert "decay" in _receipt_stages(agent, cycle)
    event = next(n for n in _nodes(agent, "EpisodicEvent")
                 if agent.s.node(n)["attrs"].get("event_key") == "staged-event")
    assert agent.s.node(event)["attrs"]["observation_status"] == "observed"
    before = agent.s.node(_nodes(agent, "ThinkingBudget")[0])["attrs"]["remaining"]
    agent.tick()
    assert agent.s.node(support)["attrs"]["sleep_freshness_epoch"] == 3.0
    assert agent.s.node(_nodes(agent, "ThinkingBudget")[0])["attrs"]["remaining"] == before


def test_generator_reproduces_committed_seed_exactly():
    import subprocess
    import sys
    seed = ROOT / "seeds" / "sleep_regime.json"
    before = seed.read_bytes()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_sleep_regime_seed.py")],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    assert seed.read_bytes() == before


def test_recombination_advisory():
    agent = _staged_fresh()
    for epoch in range(1, 6):
        _advance(agent, epoch)
    proposals = _nodes(agent, "SleepRecombinationProposal")
    assert len(proposals) == 1
    attrs = agent.s.node(proposals[0])["attrs"]
    assert attrs["status"] == "advisory"
    assert attrs["observation_status"] == "not_observed"
    assert _nodes(agent, "ProcessSchema") == []
    cycle = _nodes(agent, "MemoryCycle")[0]
    library_receipt = next(r for r in agent.inner.neighbours(cycle, "has_sleep_stage_receipt")
                           if agent.s.node(r)["attrs"]["stage"] == "library")
    assert agent.s.node(library_receipt)["attrs"]["status"] == "deferred"


def test_save_load_resume(tmp_path):
    agent = _staged_fresh()
    _advance(agent, 1)
    _advance(agent, 2, task=0.9)  # foreground demand leaves cursor at consolidate
    cycle = _nodes(agent, "MemoryCycle")[0]
    assert agent.s.node(cycle)["attrs"]["sleep_stage_cursor"] == "consolidate"
    checkpoint = tmp_path / "sleep-resume.json"
    budget = _nodes(agent, "ThinkingBudget")[0]
    before_resume = agent.s.node(budget)["attrs"]["remaining"]
    agent.save(checkpoint)
    resumed = WorldAdapter.load(checkpoint)

    _advance(resumed, 3)
    resumed_cycle = _nodes(resumed, "MemoryCycle")[0]
    assert resumed.s.node(resumed_cycle)["attrs"]["sleep_stage_cursor"] == "decay"
    assert _receipt_stages(resumed, resumed_cycle) == ["replay", "consolidate"]
    resumed_budget = _nodes(resumed, "ThinkingBudget")[0]
    after_resume = resumed.s.node(resumed_budget)["attrs"]["remaining"]
    assert after_resume == before_resume - 1.0
    resumed.tick()
    assert resumed.s.node(resumed_budget)["attrs"]["remaining"] == after_resume


def test_stage_defers_without_budget_and_resumes_after_funding():
    agent = _staged_fresh()
    _advance(agent, 1)
    cycle = _nodes(agent, "MemoryCycle")[0]
    budget = _nodes(agent, "ThinkingBudget")[0]
    agent.s.set_attr(budget, "remaining", 0.0)
    _advance(agent, 2)
    assert agent.s.node(cycle)["attrs"]["sleep_stage_cursor"] == "consolidate"
    assert _receipt_stages(agent, cycle) == ["replay"]

    agent.s.set_attr(budget, "remaining", 1.0)
    _advance(agent, 3)
    assert agent.s.node(cycle)["attrs"]["sleep_stage_cursor"] == "decay"
    assert _receipt_stages(agent, cycle) == ["replay", "consolidate"]


def test_external_demand_and_urgency_interrupt_before_stage():
    for field in ("external", "urgency"):
        agent = _staged_fresh()
        _advance(agent, 1)
        cycle = _nodes(agent, "MemoryCycle")[0]
        kwargs = {field: 0.9}
        _advance(agent, 2, **kwargs)
        assert agent.s.node(cycle)["attrs"]["sleep_stage_cursor"] == "consolidate"
        assert _receipt_stages(agent, cycle) == ["replay"]


def test_stale_model_cancels_pending_cycle():
    agent = _staged_fresh()
    _advance(agent, 1)
    cycle = _nodes(agent, "MemoryCycle")[0]
    policy = _nodes(agent, "SleepRegimePolicy")[0]
    agent.s.set_attr(policy, "model_epoch", 1.0)
    _advance(agent, 2)
    assert agent.s.node(cycle)["attrs"]["sleep_stage_cursor"] == "canceled"
    assert agent.s.node(cycle)["attrs"]["sleep_cancel_reason"] == "stale_model_epoch"
    assert _receipt_stages(agent, cycle) == ["replay"]


def test_256_epoch_growth_bounded():
    agent = _staged_fresh(refill=2.0)
    initial_nodes = len(agent.s.nodes())
    for epoch in range(1, 257):
        _advance(agent, epoch)
        assert len(_nodes(agent, "MemoryCycle")) <= 4
        # Four retained complete cycles plus the boundary cycle being pruned.
        assert len(_nodes(agent, "SleepStageReceipt")) <= 25
        assert len(_nodes(agent, "SleepRecombinationProposal")) <= 4
    assert len(agent.s.nodes()) <= initial_nodes + 60
