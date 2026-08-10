"""substrate awareness, migrated — the entity is aware of its substrate via the
WorldAdapter (no CuriousAgent). What each tick costs in compute, how much memory
it's using vs its ceiling, and a persistent long-term store (an mmap-backed
file). The information lives on the AGENT NODE as graph-resident scalar attrs, so
the agent's own DSL Terms can read it (Attr(Var("agent"), "<name>")) — no special
machinery, no hidden Python state.

Covers tests/test_substrate_awareness one-for-one: per-tick cost, pass-through
signal, memory footprint, memory pressure, compute pressure, the mmap store, and
the store surviving a fresh agent. All of it is mechanical I/O bookkeeping that
the adapter is permitted to do; making the information AVAILABLE is the point.
"""
from __future__ import annotations

import time

from substrate.world_adapter import WorldAdapter


def test_agent_sees_its_per_tick_compute_cost():
    wa = WorldAdapter()

    def work(_):
        time.sleep(0.01)

    wa.measure_tick(work)
    assert wa.agent_attr("tick_count") == 1
    # the tick cost lands on the agent node as a number (ms)
    assert wa.agent_attr("last_tick_cost_ms") >= 9.0
    assert wa.agent_attr("total_tick_cost_ms") >= 9.0

    wa.measure_tick(work)
    assert wa.agent_attr("tick_count") == 2
    # total accumulates across ticks; the agent can see how much it's burned
    assert wa.agent_attr("total_tick_cost_ms") >= wa.agent_attr("last_tick_cost_ms")


def test_measure_tick_returns_the_works_signal():
    # whatever the work emits passes through — measure_tick is non-intrusive
    wa = WorldAdapter()
    signal = wa.measure_tick(lambda _: "carry-through")
    assert signal == "carry-through"


def test_agent_sees_its_memory_footprint():
    wa = WorldAdapter()
    bytes_used = wa.refresh_memory_stats()
    assert bytes_used is not None and bytes_used > 0
    # the agent can also read it off its own node (graph-resident — what the
    # agent's DSL Terms would see via Attr(Var("agent"), "memory_bytes"))
    assert wa.agent_attr("memory_bytes") == bytes_used


def test_agent_sees_pressure_against_its_memory_limit():
    wa = WorldAdapter()
    wa.refresh_memory_stats()
    bytes_used = wa.agent_attr("memory_bytes")
    wa.set_memory_limit(bytes_used * 2)
    # used/limit ratio is computed on stored attrs — exactly 0.5 here
    assert wa.memory_pressure() == 0.5
    # the limit itself is graph-resident, the agent can see its own ceiling
    assert wa.agent_attr("memory_limit_bytes") == bytes_used * 2


def test_agent_sees_pressure_against_its_overall_compute_limit():
    wa = WorldAdapter()

    def work(_):
        time.sleep(0.01)

    wa.measure_tick(work)
    wa.measure_tick(work)
    spent = wa.agent_attr("total_tick_cost_ms")
    wa.set_compute_limit(spent * 4)        # we've used a quarter of the budget
    assert wa.compute_pressure() == 0.25
    # the limit itself is graph-resident on the agent node — the agent's DSL can
    # read it the same way it reads any other Attr
    assert wa.agent_attr("compute_limit_ms") == spent * 4


def test_agent_uses_an_mmap_long_term_store(tmp_path):
    wa = WorldAdapter()
    path = str(tmp_path / "long_term.bin")
    wa.open_long_term_storage(path, size=4096)
    # writes persist into the mmap'd file
    assert wa.storage_write(0, b"hello, substrate") == 16
    assert wa.storage_read(0, 16) == b"hello, substrate"
    # ...and offsets work as expected
    wa.storage_write(1024, b"chunk@1k")
    assert wa.storage_read(1024, 8) == b"chunk@1k"
    # the agent can see WHERE its store is and HOW BIG it is, graph-resident
    assert wa.agent_attr("storage_path") == path
    assert wa.agent_attr("storage_bytes") == 4096


def test_long_term_store_survives_a_fresh_agent(tmp_path):
    # the file outlives the process; a new agent can re-attach and read what the
    # old one wrote (this is what "long-term" means)
    path = str(tmp_path / "carryover.bin")
    wa = WorldAdapter()
    wa.open_long_term_storage(path, size=1024)
    wa.storage_write(0, b"persist-me")
    # ...new agent, same file
    wb = WorldAdapter()
    wb.open_long_term_storage(path)            # size omitted; file already exists
    assert wb.storage_read(0, 10) == b"persist-me"
