"""Phase 9 — master + N workers + M async runners.

The concurrency layer is the engineering instantiation of the converged
biology research: Baars' Global Workspace, Posner-Petersen executive
attention, ACT-R modules + central production, Friston multi-timescale.

Posture: master is the single writer; workers + async runners compute
in isolation; their results return as `apply(agent)` closures the
master runs on its own thread. Same shape as ACT-R's "modules compute
in parallel, decision cycle is serial".

Tests cover both the primitive surface and the ACT-R-shape integration
where a "master" object drains the result queue per tick.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from domains.concurrency import (
    AsyncRunner,
    ConcurrencyLayer,
    MemoryConsolidationRunner,
    Result,
    WorkerPool,
)


# --- WorkerPool ----------------------------------------------------------


def test_worker_pool_runs_task_and_returns_value():
    pool = WorkerPool(n_workers=2, name="t")
    try:
        tid = pool.submit(lambda x: x * x, payload=7)
        # Spin briefly for the worker to pick it up.
        for _ in range(50):
            results = pool.drain()
            if results:
                break
            time.sleep(0.01)
        assert len(results) == 1
        r = results[0]
        assert r.task_id == tid
        assert r.value == 49
        assert r.error is None
        assert r.apply is None
        assert r.wall_ms >= 0.0
    finally:
        pool.stop()


def test_worker_pool_routes_callable_return_to_apply():
    """If a task returns a 1-arg callable, it's treated as an
    apply(agent) closure — the master-commit path."""
    pool = WorkerPool(n_workers=2, name="t2")
    try:
        def task(payload):
            squared = payload * payload

            def apply(agent):
                agent.append(("worker_committed", squared))
            return apply

        tid = pool.submit(task, payload=5)
        for _ in range(50):
            results = pool.drain()
            if results:
                break
            time.sleep(0.01)
        r = results[0]
        assert r.task_id == tid
        assert r.apply is not None  # callable detected
        assert r.value is None
        agent = []
        r.apply(agent)
        assert agent == [("worker_committed", 25)]
    finally:
        pool.stop()


def test_worker_pool_captures_exceptions():
    """A raising worker doesn't crash the pool — the error lands on
    Result.error and the pool keeps running."""
    pool = WorkerPool(n_workers=1, name="t3")
    try:
        def bad(_):
            raise ValueError("intentional")
        bad_tid = pool.submit(bad, payload=None)
        # Schedule a good one after — the pool's first worker should
        # process the bad one, then continue.
        good_tid = pool.submit(lambda _: 42, payload=None)
        seen: dict = {}
        for _ in range(100):
            for r in pool.drain():
                seen[r.task_id] = r
            if len(seen) == 2:
                break
            time.sleep(0.01)
        assert isinstance(seen[bad_tid].error, ValueError)
        assert seen[good_tid].value == 42
    finally:
        pool.stop()


def test_worker_pool_n_workers_run_truly_concurrently():
    """N workers should process roughly N tasks in parallel — wall
    time for N sleepy tasks ≈ task_duration, not N×task_duration."""
    n = 4
    pool = WorkerPool(n_workers=n, name="t4")
    try:
        def sleepy(_):
            time.sleep(0.10)
            return None
        t0 = time.perf_counter()
        for _ in range(n):
            pool.submit(sleepy, payload=None)
        # Wait until all results land (poll briefly).
        got = 0
        deadline = time.perf_counter() + 2.0
        while got < n and time.perf_counter() < deadline:
            got += len(pool.drain())
            time.sleep(0.01)
        elapsed = time.perf_counter() - t0
        assert got == n
        # If workers were serial, this would take ~0.40s; concurrent
        # should be <0.25s with plenty of slack for scheduler jitter.
        assert elapsed < 0.30, f"expected concurrent execution; took {elapsed:.3f}s"
    finally:
        pool.stop()


# --- AsyncRunner --------------------------------------------------------


def test_async_runner_executes_coroutine():
    runner = AsyncRunner(max_concurrent=4, name="ar")
    try:
        async def coro(payload):
            await asyncio.sleep(0.01)
            return payload + 1
        tid = runner.submit(coro, payload=10)
        results: list[Result] = []
        for _ in range(50):
            results.extend(runner.drain())
            if results:
                break
            time.sleep(0.01)
        assert len(results) == 1
        assert results[0].task_id == tid
        assert results[0].value == 11
    finally:
        runner.stop()


def test_async_runner_caps_concurrency():
    """With max_concurrent=2, four 0.1s sleeps should serialise in
    pairs — wall time ~0.2s, not ~0.1s and not ~0.4s."""
    runner = AsyncRunner(max_concurrent=2, name="cap")
    try:
        async def coro(_):
            await asyncio.sleep(0.10)
            return None
        t0 = time.perf_counter()
        for _ in range(4):
            runner.submit(coro, payload=None)
        got = 0
        while got < 4 and time.perf_counter() - t0 < 2.0:
            got += len(runner.drain())
            time.sleep(0.01)
        elapsed = time.perf_counter() - t0
        assert got == 4
        # Two batches of 2 → ~0.2s, with jitter give it some slack.
        assert 0.15 < elapsed < 0.40, (
            f"semaphore should serialise in pairs; took {elapsed:.3f}s"
        )
    finally:
        runner.stop()


def test_async_runner_classifies_apply_closure():
    runner = AsyncRunner(max_concurrent=4, name="ar2")
    try:
        async def coro(payload):
            def apply(agent):
                agent.append(payload)
            return apply
        runner.submit(coro, payload="from_async")
        results: list[Result] = []
        for _ in range(50):
            results.extend(runner.drain())
            if results:
                break
            time.sleep(0.01)
        assert results[0].apply is not None
        agent = []
        results[0].apply(agent)
        assert agent == ["from_async"]
    finally:
        runner.stop()


def test_async_runner_captures_exceptions():
    runner = AsyncRunner(max_concurrent=1, name="ar3")
    try:
        async def boom(_):
            raise RuntimeError("intentional")
        runner.submit(boom, payload=None)
        results: list[Result] = []
        for _ in range(50):
            results.extend(runner.drain())
            if results:
                break
            time.sleep(0.01)
        assert isinstance(results[0].error, RuntimeError)
    finally:
        runner.stop()


def test_async_runner_stop_joins_thread_and_rejects_new_work():
    runner = AsyncRunner(max_concurrent=1, name="stop")
    runner.stop()
    assert not runner._thread.is_alive()

    async def never_submitted(_):
        return None

    with pytest.raises(RuntimeError, match="stopped"):
        runner.submit(never_submitted)


# --- ConcurrencyLayer (master integration) -------------------------------


def test_concurrency_layer_drains_pools_and_runners_per_tick():
    """The master calls `layer.tick(agent)`; the layer drains every
    pool and runner and applies each apply-closure on the caller's
    thread. This is the actual ACT-R-shape: concurrent compute,
    serial commit."""
    pool = WorkerPool(n_workers=2, name="lp")
    runner = AsyncRunner(max_concurrent=2, name="lr")
    layer = ConcurrencyLayer(max_results_per_tick=32)
    layer.add_pool(pool)
    layer.add_runner(runner)
    agent: list = []
    try:
        def worker_task(p):
            return lambda a: a.append(("worker", p))

        async def async_task(p):
            return lambda a: a.append(("async", p))

        pool.submit(worker_task, payload="A")
        pool.submit(worker_task, payload="B")
        runner.submit(async_task, payload="C")

        # Spin the master tick until all three land.
        deadline = time.perf_counter() + 2.0
        while len(agent) < 3 and time.perf_counter() < deadline:
            layer.tick(agent)
            time.sleep(0.01)
        assert len(agent) == 3
        kinds = sorted(a[0] for a in agent)
        assert kinds == ["async", "worker", "worker"]
    finally:
        layer.stop_all()


def test_concurrency_layer_reports_apply_error_ignored_counts():
    pool = WorkerPool(n_workers=1, name="lc")
    layer = ConcurrencyLayer()
    layer.add_pool(pool)
    try:
        pool.submit(lambda _: lambda a: a.append("ok"), payload=None)  # apply
        pool.submit(lambda _: 42, payload=None)                         # value (ignored)
        pool.submit(lambda _: (_ for _ in ()).throw(ValueError("x")),   # error
                    payload=None)
        agent: list = []
        deadline = time.perf_counter() + 2.0
        applied = errored = ignored = 0
        while applied + errored + ignored < 3 and time.perf_counter() < deadline:
            stats = layer.tick(agent)
            applied += stats["applied"]
            errored += stats["errored"]
            ignored += stats["ignored"]
            time.sleep(0.01)
        assert applied == 1
        assert errored == 1
        assert ignored == 1
        assert agent == ["ok"]
        # Recent-results history retained for inspection.
        assert len(layer.recent_results) == 3
    finally:
        layer.stop_all()


# --- Memory consolidation runner ----------------------------------------


def test_memory_consolidation_runner_fires_periodically():
    """The CLS-shape background process: periodic offline replay
    delivers apply closures to the master. Verify it fires at the
    expected cadence and stops cleanly."""
    runner = AsyncRunner(max_concurrent=2, name="mc")
    fire_count = [0]

    def consolidate():
        fire_count[0] += 1

        def apply(agent):
            agent.append(("consolidated", fire_count[0]))
        return apply

    mcr = MemoryConsolidationRunner(
        runner=runner,
        consolidate_fn=consolidate,
        period_s=0.05,  # 50ms — fast for the test
    )
    mcr.start()
    agent: list = []
    # Drain for ~0.3s — expect ~5 consolidations.
    deadline = time.perf_counter() + 0.30
    while time.perf_counter() < deadline:
        for r in runner.drain():
            if r.apply:
                r.apply(agent)
        time.sleep(0.01)
    mcr.stop()
    runner.stop()
    n_committed = sum(1 for a in agent if isinstance(a, tuple) and a[0] == "consolidated")
    # Conservative bound — jitter on CI can vary. Expect 2-10.
    assert 2 <= n_committed <= 10, f"expected ~5 consolidations, got {n_committed}"
