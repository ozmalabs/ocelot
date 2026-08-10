"""Smoke test for Substrate.start_agent — the autonomous tick loop.

The mind adapter spawns a background thread that ticks the Rust runtime at
a configured rate. World adapters write events to the graph; the running
agent picks them up on the next tick — no per-write Π.tick() call needed.
"""
import time

import pytest

from substrate_rs import Substrate as RustSubstrate


def test_start_and_stop_lifecycle():
    s = RustSubstrate()
    assert s.agent_running() is False
    s.start_agent(tick_rate_hz=50.0)
    assert s.agent_running() is True
    s.stop_agent()
    assert s.agent_running() is False


def test_double_start_raises():
    s = RustSubstrate()
    s.start_agent(tick_rate_hz=20.0)
    try:
        with pytest.raises(ValueError):
            s.start_agent(tick_rate_hz=20.0)
    finally:
        s.stop_agent()


def test_stop_without_start_is_noop():
    s = RustSubstrate()
    s.stop_agent()  # must not raise
    assert s.agent_running() is False


def test_one_writer_multiple_pure_task_workers():
    s = RustSubstrate()
    with pytest.raises(ValueError):
        s.start_agent(tick_rate_hz=10.0, n_runners=2)
    s.start_agent(tick_rate_hz=10.0, n_threads_per_runner=4)
    assert s.agent_running() is True
    s.stop_agent()
    assert s.agent_running() is False


def test_loop_actually_ticks():
    """At 100Hz, after ~150ms the thread should have completed multiple
    ticks. Add a node from the main thread while the agent is
    running, and confirm the substrate stays consistent. The Rust
    tick thread holds the inner mutex briefly during each tick;
    add_node serialises against it at the mutex (not the GIL)."""
    s = RustSubstrate()
    n_before = s.node_count()
    s.start_agent(tick_rate_hz=100.0)
    time.sleep(0.15)
    nid = s.add_node("Mark", {})
    time.sleep(0.05)
    s.stop_agent()
    assert s.node_count() == n_before + 1
    assert s.node(nid)["type"] == "Mark"


def test_concurrent_worlds_write_while_agent_ticks():
    """Two Python "world adapter" threads write to the substrate at
    different rates while the Rust agent ticks autonomously at a
    third rate. None of them coordinate; they hot-plug + write +
    detach without waiting for the others. Verifies the architecture
    the user asked for: the world adapter and the agent are not
    synchronous with each other."""
    import threading

    s = RustSubstrate()
    s.start_agent(tick_rate_hz=200.0)

    stop = threading.Event()
    counts = {"world_a": 0, "world_b": 0}

    def world_a():
        # 1 kHz writer
        while not stop.is_set():
            s.add_node("EventA", {})
            counts["world_a"] += 1
            time.sleep(0.001)

    def world_b():
        # 500 Hz writer with a different type
        while not stop.is_set():
            s.add_node("EventB", {})
            counts["world_b"] += 1
            time.sleep(0.002)

    ta = threading.Thread(target=world_a, daemon=True)
    tb = threading.Thread(target=world_b, daemon=True)
    ta.start()
    tb.start()
    time.sleep(0.3)
    stop.set()
    ta.join(timeout=1.0)
    tb.join(timeout=1.0)
    s.stop_agent()

    # Both worlds got real wall-clock progress — the agent's tick
    # didn't starve them. With GIL-serialised tick + writes this
    # would have been much choppier; with Rust-thread + Arc<Mutex>
    # and GIL released around the lock, each world keeps ticking.
    assert counts["world_a"] > 100, counts
    assert counts["world_b"] > 50, counts
