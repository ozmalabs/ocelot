"""Tests for P2.A5 (`thinking_budget` seed and P1 requester integration).

Covers:
1. Refill is capped at `capacity`.
2. Refill happens at most once per epoch, including across an epoch jump (`20 -> 22`)
   and repeated ticks within the same epoch.
3. A requester with `cost = 4` and `remaining = 6` succeeds once (`remaining == 2`)
   and a second request with `cost = 4` is denied with a `ThinkingBudgetDenial`
   (deduped to at most one denial per `(requester_kind, epoch)`).
4. Both direct `ThinkingBudgetRequest` nodes and the P1 bridge requesters
   (`impasse_simulation_bridge`, `consolidation_scheduler`) honour `ThinkingBudget`
   when `enabled == 1.0`, and behave identically to their P1 tests when
   `ThinkingBudget.enabled == 0.0`.
5. `tb_fund_from_horizon` derives `capacity = Min(capacity_ceiling, future_manifold_projection_budget * funding_gain)`
   when `agent -governs_horizon-> ManifoldPolicy` is present.
6. `scripts/gen_thinking_budget_seed.py` reproduces `seeds/thinking_budget.json`.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

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


def _fresh(*extra_seeds):
    seeds = tuple(dict.fromkeys(CORE_SEEDS + ("thinking_budget",) + extra_seeds))
    return WorldAdapter(seeds=seeds)


def test_refill_is_capped_at_capacity_and_runs_once_per_epoch():
    agent = _fresh()
    budget = _nodes(agent, "ThinkingBudget")[0]
    mode = _nodes(agent, "NetworkModeState")[0]

    agent.s.set_attr(budget, "enabled", 1.0)
    agent.s.set_attr(budget, "capacity", 16.0)
    agent.s.set_attr(budget, "remaining", 15.0)
    agent.s.set_attr(budget, "refill_per_epoch", 2.0)
    agent.s.set_attr(budget, "last_refill_epoch", 0.0)

    agent.s.set_attr(mode, "epoch", 1.0)
    agent.tick()
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(16.0)
    assert agent.s.node(budget)["attrs"]["last_refill_epoch"] == pytest.approx(1.0)

    # Extra ticks within the same epoch must not refill again even if remaining drops
    agent.s.set_attr(budget, "remaining", 10.0)
    agent.tick()
    agent.tick()
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(10.0)


def test_refill_once_per_epoch_across_epoch_jump_99_assertion():
    """Mirrors `test_default_mode_core_migrated.py:208-226`: after an epoch jump
    (`20 -> 22`), refill fires once at epoch 20 (`98 -> 99`) and once at epoch 22 (`98 -> 99`),
    never accumulating per intermediate skipped epoch or per repeated tick."""
    agent = _fresh()
    budget = _nodes(agent, "ThinkingBudget")[0]
    mode = _nodes(agent, "NetworkModeState")[0]

    agent.s.set_attr(budget, "enabled", 1.0)
    agent.s.set_attr(budget, "capacity", 100.0)
    agent.s.set_attr(budget, "remaining", 98.0)
    agent.s.set_attr(budget, "refill_per_epoch", 1.0)
    agent.s.set_attr(budget, "last_refill_epoch", 0.0)

    agent.s.set_attr(mode, "epoch", 20.0)
    agent.tick()
    agent.tick()
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(99.0)

    # Reset remaining to 98.0 and jump from epoch 20 to epoch 22 -> refills once to 99.0
    agent.s.set_attr(budget, "remaining", 98.0)
    agent.s.set_attr(mode, "epoch", 22.0)
    agent.tick()
    agent.tick()
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(99.0)


def test_requester_with_cost_4_and_remaining_6_succeeds_once_then_denied():
    agent = _fresh()
    budget = _nodes(agent, "ThinkingBudget")[0]
    mode = _nodes(agent, "NetworkModeState")[0]

    agent.s.set_attr(mode, "epoch", 5.0)
    agent.s.set_attr(budget, "enabled", 1.0)
    agent.s.set_attr(budget, "capacity", 16.0)
    agent.s.set_attr(budget, "remaining", 6.0)
    agent.s.set_attr(budget, "last_refill_epoch", 5.0)

    req1 = agent.s.add_node(
        "ThinkingBudgetRequest",
        {"status": "pending", "cost": 4.0, "requester_kind": "deliberation_probe"},
    )
    _edge(agent, req1, "draws_on_thinking_budget", budget)
    agent.tick()

    assert agent.s.node(req1)["attrs"]["status"] == "approved"
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(2.0)
    assert _nodes(agent, "ThinkingBudgetDenial") == []

    # Second request with cost 4.0 at remaining 2.0 is denied and records one ThinkingBudgetDenial
    req2 = agent.s.add_node(
        "ThinkingBudgetRequest",
        {"status": "pending", "cost": 4.0, "requester_kind": "deliberation_probe"},
    )
    _edge(agent, req2, "draws_on_thinking_budget", budget)
    agent.tick()

    assert agent.s.node(req2)["attrs"]["status"] == "denied"
    assert agent.s.node(req2)["attrs"]["terminal_reason"] == "budget_exhausted"
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(2.0)

    denials = _nodes(agent, "ThinkingBudgetDenial")
    assert len(denials) == 1
    d_attrs = agent.s.node(denials[0])["attrs"]
    assert d_attrs["reason"] == "budget_exhausted"
    assert d_attrs["requester_kind"] == "deliberation_probe"
    assert d_attrs["epoch"] == pytest.approx(5.0)

    # A third exhausted request of the same kind in the same epoch does not duplicate the denial node
    req3 = agent.s.add_node(
        "ThinkingBudgetRequest",
        {"status": "pending", "cost": 4.0, "requester_kind": "deliberation_probe"},
    )
    _edge(agent, req3, "draws_on_thinking_budget", budget)
    agent.tick()
    assert agent.s.node(req3)["attrs"]["status"] == "denied"
    assert len(_nodes(agent, "ThinkingBudgetDenial")) == 1


def test_p1_impasse_and_consolidation_requesters_obey_enabled_budget_and_preserve_disabled_behaviour():
    agent = _fresh(
        "dual_process_core",
        "impasse_simulation_bridge",
        "consolidation_scheduler",
    )
    budget = _nodes(agent, "ThinkingBudget")[0]
    mode = _nodes(agent, "NetworkModeState")[0]
    isb_pol = _nodes(agent, "ImpasseSimulationPolicy")[0]
    csch_pol = _nodes(agent, "ConsolidationSchedulerPolicy")[0]

    agent.s.set_attr(isb_pol, "enabled", 1.0)
    agent.s.set_attr(isb_pol, "cost", 4.0)
    agent.s.set_attr(csch_pol, "enabled", 1.0)
    agent.s.set_attr(csch_pol, "cost", 4.0)

    # Seed perceived belief + episode so both P1 bridges have valid inputs
    belief = agent.s.add_node(
        "BeliefState",
        {
            "status": "current",
            "provenance_kind": "perceived",
            "observation_status": "observed",
            "state_kind": "corridor",
            "state_summary": "corridor",
            "epoch": 1.0,
            "confidence": 0.9,
            "uncertainty": 0.1,
        },
    )
    _edge(agent, agent.agent, "has_belief_state", belief)
    ep = agent.s.add_node(
        "Episode",
        {
            "status": "active",
            "epoch": 1.0,
            "last_replayed_epoch": -100.0,
            "salience": 0.8,
            "surprise": 0.7,
            "value": 0.6,
            "replay_priority": 0.9,
            "replay_count": 0.0,
            "consolidated": 0.0,
            "provenance_kind": "perceived",
            "observation_status": "observed",
        },
    )
    _edge(agent, agent.agent, "recorded_episode", ep)

    # 1. With ThinkingBudget disabled (default enabled=0.0), both bridges fire without debiting remaining
    agent.s.set_attr(budget, "enabled", 0.0)
    agent.s.set_attr(budget, "remaining", 2.0)
    agent.s.set_attr(mode, "epoch", 2.0)
    agent.s.set_attr(mode, "default_mode_weight", 0.8)
    agent.s.set_attr(mode, "task_demand", 0.0)
    agent.tick()
    assert len(_nodes(agent, "MemoryCycle")) == 1
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(2.0)

    # 2. Enable ThinkingBudget with remaining = 6.0 and cost = 4.0 at epoch 10.0:
    # First requester in load order (impasse_simulation_bridge) succeeds (remaining: 6 -> 2),
    # second requester (consolidation_scheduler) is blocked and emits ThinkingBudgetDenial!
    agent.s.set_attr(budget, "enabled", 1.0)
    agent.s.set_attr(budget, "remaining", 6.0)
    agent.s.set_attr(budget, "last_refill_epoch", 10.0)
    agent.s.set_attr(mode, "epoch", 10.0)
    agent.s.set_attr(mode, "default_mode_weight", 0.8)
    agent.s.set_attr(mode, "task_demand", 0.0)

    ctx = agent.s.add_node("DualProcessContext", {"status": "escalated", "epoch": 10.0})
    esc = agent.s.add_node(
        "SystemTwoEscalation",
        {"status": "open", "reason": "near_conflict", "epoch": 10.0},
    )
    _edge(agent, agent.agent, "has_dual_process_context", ctx)
    _edge(agent, ctx, "has_system_two_escalation", esc)

    agent.tick()

    assert len(_nodes(agent, "SimulationRequest")) == 1
    assert len(_nodes(agent, "MemoryCycle")) == 1
    assert agent.s.node(_nodes(agent, "MemoryCycle")[0])["attrs"]["epoch"] == pytest.approx(2.0)
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(2.0)
    denials = _nodes(agent, "ThinkingBudgetDenial")
    assert len(denials) == 1
    assert agent.s.node(denials[0])["attrs"]["requester_kind"] == "consolidation"


def test_fund_from_horizon_updates_capacity_from_manifold_policy():
    agent = _fresh()
    budget = _nodes(agent, "ThinkingBudget")[0]
    agent.s.set_attr(budget, "enabled", 1.0)

    mpol = agent.s.add_node(
        "ManifoldPolicy",
        {"future_manifold_projection_budget": 12.0},
    )
    _edge(agent, agent.agent, "governs_horizon", mpol)

    agent.tick()
    assert agent.s.node(budget)["attrs"]["capacity"] == pytest.approx(24.0)

    # Respects capacity_ceiling = 64.0
    agent.s.set_attr(mpol, "future_manifold_projection_budget", 50.0)
    agent.tick()
    assert agent.s.node(budget)["attrs"]["capacity"] == pytest.approx(64.0)


def test_thinking_budget_generator_matches_committed_seed():
    from scripts.gen_thinking_budget_seed import OUT, build

    expected = json.dumps(build(), indent=2) + "\n"
    assert OUT.read_text(encoding="utf-8") == expected
