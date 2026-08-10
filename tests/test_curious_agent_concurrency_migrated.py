"""CuriousAgent concurrency — migrated to WorldAdapter (no CuriousAgent).

1:1 coverage of tests/test_curious_agent_concurrency.py.

Key mapping:
  CuriousAgent()          -> WorldAdapter()
  a.mind_graph.node(a.agent_root).attrs[key] = val  ->
      a.inner.set_attr(a.agent, key, val)
  a.mind_graph.node(a.agent_root).attrs[key]         ->
      a.s.node(a.agent)["attrs"][key]

All concurrency infrastructure (start_worker_pool / start_async_runner /
submit_work / submit_async / start_memory_consolidation / stop_concurrency /
concurrency_state) was added as additive methods to WorldAdapter via
substrate/world_adapter.py. master_tick now returns a "concurrency" key
(dict or None) in addition to the existing tick / reflexes_fired /
thread_ran / thread_captured keys.

Architecture rule: apply-closures received by the master run on the master's
thread, so they are the I/O boundary at which substrate mutations are
permitted. The closures call a.inner.set_attr / a.s.node — pure mechanical
graph mutation, no decisions.
"""
from __future__ import annotations

import asyncio
import threading
import time

import pytest

from substrate.world_adapter import WorldAdapter


@pytest.fixture
def wa():
    a = WorldAdapter()
    yield a
    a.stop_concurrency()


# --- Opt-in lifecycle ----------------------------------------------------


def test_concurrency_off_by_default():
    """bench: test_concurrency_off_by_default"""
    a = WorldAdapter()
    assert a.concurrency_state() == {"active": False}
    # master_tick still works exactly as before; concurrency field is None.
    result = a.master_tick()
    assert result["concurrency"] is None
    a.stop_concurrency()


def test_start_worker_pool_idempotent_by_name(wa):
    """bench: test_start_worker_pool_idempotent_by_name"""
    p1 = wa.start_worker_pool(n=2, name="cpu")
    p2 = wa.start_worker_pool(n=2, name="cpu")
    assert p1 is p2
    state = wa.concurrency_state()
    assert state["active"]
    assert len(state["pools"]) == 1
    assert state["pools"][0]["name"] == "cpu"
    assert state["pools"][0]["n_workers"] == 2


def test_start_async_runner_idempotent_by_name(wa):
    """bench: test_start_async_runner_idempotent_by_name"""
    r1 = wa.start_async_runner(m=4, name="io")
    r2 = wa.start_async_runner(m=4, name="io")
    assert r1 is r2
    state = wa.concurrency_state()
    assert len(state["runners"]) == 1
    assert state["runners"][0]["name"] == "io"


def test_default_pool_and_runner_lazy_init(wa):
    """bench: test_default_pool_and_runner_lazy_init
    submit_work / submit_async create default pool/runner on first use."""
    assert getattr(wa, "_default_worker_pool", None) is None
    wa.submit_work(lambda _: None)
    assert wa._default_worker_pool is not None
    wa.submit_async(_noop_coro)
    assert wa._default_async_runner is not None


async def _noop_coro(_):
    return None


# --- Work + drain via master_tick ----------------------------------------


def test_worker_apply_closure_lands_on_master_thread(wa):
    """bench: test_worker_apply_closure_lands_on_master_thread
    Workers compute in parallel; apply-closures land on master's thread.
    Verify by recording the thread id at apply time: it must match the test
    thread (the main thread running master_tick). Mutation is via the
    substrate API (inner.set_attr / s.node) rather than mind_graph dict."""
    main_tid = threading.get_ident()
    worker_thread_ids: list[int] = []
    apply_thread_ids: list[int] = []

    def task(payload):
        worker_thread_ids.append(threading.get_ident())

        def apply(a):
            apply_thread_ids.append(threading.get_ident())
            # Master is the only writer — safe to mutate the graph here.
            # Bump a counter on the agent node as a witness.
            cur = a.s.node(a.agent)["attrs"].get("worker_applies", 0)
            a.inner.set_attr(a.agent, "worker_applies", int(cur) + 1)
        return apply

    for _ in range(8):
        wa.submit_work(task)

    # Spin master_tick until the queue drains.
    deadline = time.perf_counter() + 2.0
    while len(apply_thread_ids) < 8 and time.perf_counter() < deadline:
        wa.master_tick()
        time.sleep(0.01)

    assert len(worker_thread_ids) == 8
    assert len(apply_thread_ids) == 8
    # Workers ran off-master.
    assert all(tid != main_tid for tid in worker_thread_ids)
    # Applies ran on master.
    assert all(tid == main_tid for tid in apply_thread_ids)
    # The mutation landed.
    assert wa.s.node(wa.agent)["attrs"]["worker_applies"] == 8


def test_async_apply_closure_lands_on_master_thread(wa):
    """bench: test_async_apply_closure_lands_on_master_thread"""
    main_tid = threading.get_ident()
    coro_thread_ids: list[int] = []
    apply_thread_ids: list[int] = []

    async def coro(payload):
        coro_thread_ids.append(threading.get_ident())
        await asyncio.sleep(0.005)

        def apply(a):
            apply_thread_ids.append(threading.get_ident())
            cur = a.s.node(a.agent)["attrs"].get("async_applies", 0)
            a.inner.set_attr(a.agent, "async_applies", int(cur) + 1)
        return apply

    for _ in range(4):
        wa.submit_async(coro)

    deadline = time.perf_counter() + 2.0
    while len(apply_thread_ids) < 4 and time.perf_counter() < deadline:
        wa.master_tick()
        time.sleep(0.01)

    assert len(coro_thread_ids) == 4
    assert len(apply_thread_ids) == 4
    assert all(tid != main_tid for tid in coro_thread_ids)
    assert all(tid == main_tid for tid in apply_thread_ids)
    assert wa.s.node(wa.agent)["attrs"]["async_applies"] == 4


# --- Concurrent execution: not serial ---------------------------------


def test_workers_run_in_parallel(wa):
    """bench: test_workers_run_in_parallel
    4 sleepy tasks across 4 workers should complete in roughly the duration
    of one task — not 4x longer."""
    wa.start_worker_pool(n=4, name="cpu")

    def sleepy(_):
        time.sleep(0.10)
        return None

    t0 = time.perf_counter()
    for _ in range(4):
        wa.submit_work(sleepy)
    # Drain via master ticks.
    deadline = time.perf_counter() + 2.0
    while wa._default_worker_pool.pending() > 0 and time.perf_counter() < deadline:
        wa.master_tick()
        time.sleep(0.005)
    elapsed = time.perf_counter() - t0
    # Concurrent should finish in well under 0.30s. Serial would be ~0.40s.
    assert elapsed < 0.30, f"workers should be parallel; took {elapsed:.3f}s"


# --- Errors don't crash the master ---


def test_failing_task_does_not_crash_master_tick(wa):
    """bench: test_failing_task_does_not_crash_master_tick
    A worker that raises lands an error on the Result; master_tick records it
    under concurrency[errored] but proceeds normally."""
    def boom(_):
        raise ValueError("intentional")

    wa.submit_work(boom)
    # Drain.
    seen_errors = 0
    deadline = time.perf_counter() + 2.0
    while seen_errors == 0 and time.perf_counter() < deadline:
        result = wa.master_tick()
        if result["concurrency"] is not None:
            seen_errors += result["concurrency"]["errored"]
        time.sleep(0.01)
    assert seen_errors == 1
    # Master is still ticking normally.
    assert wa.master_tick()["tick"] > 0


# --- Memory consolidation runner ---


def test_memory_consolidation_fires_on_its_own_clock(wa):
    """bench: test_memory_consolidation_fires_on_its_own_clock
    The memory-consolidation runner schedules itself on the async runner's
    clock; each fire produces an apply closure the master runs on the next
    tick. Verify the closure ran on master."""
    main_tid = threading.get_ident()
    apply_thread_ids: list[int] = []

    def custom_consolidate():
        def apply(a):
            apply_thread_ids.append(threading.get_ident())
            cur = a.s.node(a.agent)["attrs"].get("consolidations", 0)
            a.inner.set_attr(a.agent, "consolidations", int(cur) + 1)
        return apply

    wa.start_memory_consolidation(period_s=0.05, consolidate_fn=custom_consolidate)

    # Tick master for ~0.3s — expect several consolidations.
    deadline = time.perf_counter() + 0.30
    while time.perf_counter() < deadline:
        wa.master_tick()
        time.sleep(0.01)

    consolidations = wa.s.node(wa.agent)["attrs"].get("consolidations", 0)
    assert consolidations >= 2, f"expected ≥2 consolidations; got {consolidations}"
    assert all(tid == main_tid for tid in apply_thread_ids)


# --- Multiple pools coexist ---


def test_multiple_named_pools_coexist(wa):
    """bench: test_multiple_named_pools_coexist"""
    cpu = wa.start_worker_pool(n=2, name="cpu")
    io_compute = wa.start_worker_pool(n=2, name="io_compute")
    assert cpu is not io_compute
    state = wa.concurrency_state()
    assert {p["name"] for p in state["pools"]} == {"cpu", "io_compute"}

    # Tasks routed directly to each pool.
    landed = []

    def task_for(label):
        def fn(_):
            def apply(_a):
                landed.append(label)
            return apply
        return fn

    cpu.submit(task_for("cpu_a"))
    io_compute.submit(task_for("io_b"))
    deadline = time.perf_counter() + 2.0
    while len(landed) < 2 and time.perf_counter() < deadline:
        wa.master_tick()
        time.sleep(0.01)
    assert sorted(landed) == ["cpu_a", "io_b"]
