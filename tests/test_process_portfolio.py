"""P15.02: graph-owned funding and deterministic native portfolio partitions."""
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

from substrate.boot_core import CORE_SEEDS  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _nodes(agent, node_type):
    return [nid for nid in agent.s.nodes()
            if agent.s.node(nid)["type"] == node_type]


def _fresh(*, workers=4, budget=100.0):
    seeds = tuple(dict.fromkeys(
        CORE_SEEDS + ("thinking_budget", "cognitive_areas", "process_portfolio")))
    agent = WorldAdapter(seeds=seeds)
    policy = _nodes(agent, "ProcessPortfolioPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    agent.s.set_attr(policy, "max_workers", float(workers))
    area = next(n for n in _nodes(agent, "CognitiveArea")
                if agent.s.node(n)["attrs"].get("name") == "process_portfolio")
    agent.s.set_attr(area, "desired_workers", workers)
    pool = _nodes(agent, "ThinkingBudget")[0]
    mode = _nodes(agent, "NetworkModeState")[0]
    epoch = agent.s.node(mode)["attrs"]["epoch"]
    agent.s.set_attr(pool, "enabled", 1.0)
    agent.s.set_attr(pool, "capacity", budget)
    agent.s.set_attr(pool, "remaining", budget)
    agent.s.set_attr(pool, "refill_per_epoch", 0.0)
    agent.s.set_attr(pool, "last_refill_epoch", epoch)
    return agent, pool


def _batch(agent, key, status="proposed"):
    mode = _nodes(agent, "NetworkModeState")[0]
    epoch = agent.s.node(mode)["attrs"]["epoch"]
    batch = agent.s.add_node("ProcessPortfolioBatch", {
        "batch_key": key, "source_epoch": epoch,
        "deadline_epoch": epoch + 1, "status": status,
    })
    _edge(agent, agent.agent, "has_portfolio_batch", batch)
    return batch


def _unit(agent, batch, *, key, logical_time, vector, cost=2.0, status="proposed"):
    mode = _nodes(agent, "NetworkModeState")[0]
    epoch = agent.s.node(mode)["attrs"]["epoch"]
    unit = agent.s.add_node("ProcessPortfolioWorkUnit", {
        "task_key": key, "partition": logical_time % 4,
        "generation": 1, "logical_time": logical_time,
        "source_epoch": epoch, "deadline_epoch": epoch + 1,
        "evidence_vector": vector, "cost": cost, "status": status,
    })
    _edge(agent, batch, "has_work_unit", unit)
    return unit


def _execute(agent, workers):
    return agent.inner.run_cycle("area_parallel", 100_000, False, False, workers)


def _semantic_records(agent):
    return sorted(
        (agent.s.node(n)["attrs"].get("task_key"),
         agent.s.node(n)["attrs"].get("partition"),
         agent.s.node(n)["attrs"].get("result"),
         agent.s.node(n)["attrs"].get("status"),
         agent.s.node(n)["attrs"].get("work_units"))
        for n in _nodes(agent, "ProcessPortfolioReceipt"))


def test_serial_parallel_same_effects():
    outputs = []
    for workers in (1, 4):
        agent, pool = _fresh(workers=workers)
        batch = _batch(agent, "g1:serial-parallel")
        for i in range(8):
            _unit(agent, batch, key=f"g1:task:{i:02}", logical_time=i,
                  vector=[float(i), 1.0, float(i % 3)])
        _execute(agent, workers)
        outputs.append(_semantic_records(agent))
        assert agent.s.node(pool)["attrs"]["remaining"] == pytest.approx(84.0)
    assert outputs[0] == outputs[1]


def test_fold_order_deterministic():
    snapshots = []
    for order in (list(range(10)), list(reversed(range(10)))):
        agent, _pool = _fresh(workers=4)
        batch = _batch(agent, "g1:fold")
        for i in order:
            _unit(agent, batch, key=f"g1:ordered:{i:02}", logical_time=i,
                  vector=[float(i), float(2 * i)])
        _execute(agent, 4)
        snapshots.append(_semantic_records(agent))
    assert snapshots[0] == snapshots[1]
    assert [r[0] for r in snapshots[0]] == [f"g1:ordered:{i:02}" for i in range(10)]


def test_parallel_budget_no_overspend():
    agent, pool = _fresh(workers=4, budget=6.0)
    batch = _batch(agent, "g1:over-budget")
    first = _unit(agent, batch, key="g1:funded", logical_time=1,
                  vector=[2.0, 3.0], cost=4.0)
    second = _unit(agent, batch, key="g1:denied", logical_time=2,
                   vector=[7.0], cost=4.0)
    _execute(agent, 4)
    assert agent.s.node(first)["attrs"]["status"] == "denied"
    assert agent.s.node(second)["attrs"]["status"] == "denied"
    assert not agent.inner.neighbours(second, "has_native_task")
    assert not agent.inner.neighbours(first, "has_native_task")
    assert agent.s.node(pool)["attrs"]["remaining"] == pytest.approx(6.0)
    assert sorted(r[3] for r in _semantic_records(agent)) == ["denied", "denied"]


def test_batches_reserve_shared_budget_without_same_settlement_overspend():
    agent, pool = _fresh(workers=2, budget=5.0)
    first_batch = _batch(agent, "a-first")
    first = _unit(agent, first_batch, key="a:first", logical_time=1,
                  vector=[1.0, 2.0], cost=3.0)
    second_batch = _batch(agent, "b-second")
    second = _unit(agent, second_batch, key="b:second", logical_time=2,
                   vector=[3.0, 4.0], cost=3.0)
    _execute(agent, 2)
    assert agent.s.node(first)["attrs"]["status"] == "completed"
    assert agent.s.node(pool)["attrs"]["remaining"] == pytest.approx(2.0)
    assert agent.s.node(second)["attrs"]["status"] in {"proposed", "denied"}
    assert not agent.inner.neighbours(second, "has_native_task")
    assert sum(agent.s.node(n)["attrs"]["status"] == "approved"
               for n in _nodes(agent, "ThinkingBudgetRequest")) == 1


def test_cancel_preserves_receipts():
    agent, pool = _fresh(workers=2)
    done_batch = _batch(agent, "g1:done-batch")
    completed = _unit(agent, done_batch, key="g1:done", logical_time=1, vector=[2.0, 2.0])
    _execute(agent, 2)
    old_receipts = list(agent.inner.neighbours(completed, "has_receipt"))
    assert len(old_receipts) == 1

    canceled_batch = _batch(agent, "g1:cancel-batch", status="cancel_requested")
    canceled = _unit(agent, canceled_batch, key="g1:cancel", logical_time=2,
                     vector=[100.0], cost=3.0, status="cancel_requested")
    _execute(agent, 2)
    assert agent.s.node(canceled)["attrs"]["status"] == "cancelled"
    assert not agent.inner.neighbours(canceled_batch, "funded_by")
    assert list(agent.inner.neighbours(completed, "has_receipt")) == old_receipts
    assert len(agent.inner.neighbours(canceled, "has_receipt")) == 1


def test_disabled_policy_does_not_fund_or_execute():
    agent, _pool = _fresh()
    policy = _nodes(agent, "ProcessPortfolioPolicy")[0]
    agent.s.set_attr(policy, "enabled", 0.0)
    batch = _batch(agent, "g1:disabled-batch")
    unit = _unit(agent, batch, key="g1:disabled", logical_time=1, vector=[1.0])
    _execute(agent, 4)
    assert agent.s.node(unit)["attrs"]["status"] == "proposed"
    assert not agent.inner.neighbours(batch, "funded_by")
    assert not agent.inner.neighbours(unit, "has_native_task")


def test_policy_worker_cap_is_graph_owned():
    agent, _pool = _fresh(workers=4)
    policy = _nodes(agent, "ProcessPortfolioPolicy")[0]
    area = next(n for n in _nodes(agent, "CognitiveArea")
                if agent.s.node(n)["attrs"].get("name") == "process_portfolio")
    agent.s.set_attr(policy, "max_workers", 2.0)
    batch = _batch(agent, "g1:worker-cap")
    for i in range(4):
        _unit(agent, batch, key=f"g1:worker-cap:{i}", logical_time=i,
              vector=[float(i), 1.0])
    summary = _execute(agent, 4)
    assert agent.s.node(area)["attrs"]["desired_workers"] == 2.0
    assert summary["task_workers_used"] == 2


def test_portfolio_generator_matches_committed_seed():
    from scripts.gen_process_portfolio_seed import OUT, build

    expected = json.dumps(build(), indent=2) + "\n"
    assert OUT.read_text(encoding="utf-8") == expected
