"""Graph-decided cognitive tasks executed by native workers."""
from __future__ import annotations

import json
import os
import time

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREA_SEED = os.path.join(ROOT, "seeds", "cognitive_areas.json")
SCHEDULER_SEED = os.path.join(ROOT, "seeds", "cognitive_scheduler.json")


def _fresh():
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(json.load(open(AREA_SEED)), agent.agent)
    agent.inner.load_seed_manifest(json.load(open(SCHEDULER_SEED)), agent.agent)
    area = agent.s.add_node("CognitiveArea", {
        "name": "test", "status": "active", "input_epoch": 1,
        "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
        "last_residual_epoch": -1,
    })
    return agent, area


def _task(agent, area, logical_time, payload, kind="abs_diff_energy"):
    task = agent.s.add_node("CognitiveTask", {
        "status": "requested",
        "kind": kind,
        "payload": payload,
        "input_epoch": 1,
        "logical_time": logical_time,
        "area": "test",
        "order": 2,
        "salience": 1.0,
        "effort": 1,
    })
    agent.inner.add_edge_unchecked(area, "has_task", task)
    return task


def _result(agent, task):
    results = list(agent.inner.neighbours(task, "has_result"))
    assert len(results) == 1
    return agent.s.node(results[0])["attrs"]


def test_requested_tasks_execute_and_fold_in_logical_order():
    agent, area = _fresh()
    late = _task(agent, area, 20, [1, 5, 2])
    early = _task(agent, area, 10, [0, 2, 3])
    summary = agent.inner.run_cognitive_tasks(4)
    assert summary["requested"] == summary["completed"] == 2
    assert agent.s.node(early)["attrs"]["status"] == "done"
    assert agent.s.node(late)["attrs"]["status"] == "done"
    assert _result(agent, early)["output"] == 3.0
    assert _result(agent, late)["output"] == 7.0


def test_worker_count_does_not_change_results():
    outputs = []
    for workers in (1, 2, 4):
        agent, area = _fresh()
        agent.inner.set_attr(area, "desired_workers", workers)
        tasks = [_task(agent, area, i, [i, i + 3, i + 1]) for i in range(8)]
        agent.inner.run_cognitive_tasks(workers)
        outputs.append([_result(agent, task)["output"] for task in tasks])
    assert outputs[0] == outputs[1] == outputs[2]


def test_omitted_worker_count_uses_runtime_capacity_under_graph_limit():
    agent, area = _fresh()
    available = (
        len(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else (os.cpu_count() or 1)
    )
    desired = min(available, 3)
    agent.inner.set_attr(area, "desired_workers", desired)
    for i in range(desired):
        _task(agent, area, i, [i], kind="identity")

    summary = agent.inner.run_cognitive_tasks()

    assert summary["workers_used"] == desired


def test_unknown_kernel_fails_as_graph_state_not_runtime_crash():
    agent, area = _fresh()
    task = _task(agent, area, 1, [1], kind="not_a_kernel")
    summary = agent.inner.run_cognitive_tasks(2)
    assert summary["failed"] == 1
    assert agent.s.node(task)["attrs"]["status"] == "failed"
    assert "unknown native cognitive kernel" in _result(agent, task)["error"]


def test_area_metadata_round_trips_only_when_explicit():
    agent, _ = _fresh()
    agent.inner.add_rule({
        "name": "area_rule",
        "area": "vision",
        "order": 3,
        "latency_class": "soft_realtime",
        "match": [],
        "where": None,
        "effects": [],
    })
    exported = agent.inner.export_rules()
    rule = exported[-1]
    assert (rule["area"], rule["order"], rule["latency_class"]) == (
        "vision", 3, "soft_realtime")

    legacy = WorldAdapter(seeds=())
    legacy.inner.add_rule({
        "name": "legacy_rule", "match": [], "where": None, "effects": [],
    })
    old = legacy.inner.export_rules()[-1]
    assert "area" not in old and "order" not in old and "latency_class" not in old


def test_area_schedule_is_read_only_shadow_data():
    agent, _ = _fresh()
    agent.inner.add_rule({
        "name": "sensory", "area": "sensory", "order": 1,
        "match": [["a", "input", "b"]], "where": None,
        "effects": [["add_edge", "a", "feature", "b", {}]],
    })
    agent.inner.add_rule({
        "name": "attention", "area": "attention", "order": 2,
        "match": [["a", "feature", "b"]], "where": None, "effects": [],
    })
    schedule = agent.inner.area_schedule()
    names = [area["area"] for area in schedule["areas"]]
    assert names[-2:] == ["sensory", "attention"]
    assert schedule["dependencies"], "writer→reader dependency was not derived"


def test_native_workers_speed_up_real_cpu_cognition():
    timings = {}
    expected = None
    payload = [float((i * 17) % 31) for i in range(900)]
    for workers in (1, 4):
        agent, area = _fresh()
        agent.inner.set_attr(area, "desired_workers", workers)
        tasks = [
            _task(agent, area, i, payload, kind="dft_energy")
            for i in range(6)
        ]
        summary = agent.inner.run_cognitive_tasks(workers)
        timings[workers] = summary["wall_micros"]
        outputs = [_result(agent, task)["output"] for task in tasks]
        if expected is None:
            expected = outputs
        else:
            assert outputs == expected
    assert timings[4] < timings[1] * 0.9, timings


def test_pending_task_becomes_requested_only_after_dependencies_settle():
    agent, area = _fresh()
    dependency = _task(agent, area, 1, [1], kind="identity")
    child = agent.s.add_node("CognitiveTask", {
        "status": "pending", "kind": "identity", "payload": [2],
        "input_epoch": 1, "logical_time": 2, "area": "test",
        "order": 2, "salience": 1.0,
    })
    agent.inner.add_edge_unchecked(area, "has_task", child)
    agent.inner.add_edge_unchecked(child, "depends_on", dependency)
    agent.tick()
    assert agent.s.node(child)["attrs"]["status"] == "pending"
    agent.inner.run_cognitive_tasks(1)
    agent.tick()
    assert agent.s.node(child)["attrs"]["status"] == "requested"


def test_runtime_publishes_area_load_and_graph_feedback_expands_workers():
    agent, area = _fresh()
    for i in range(4):
        _task(agent, area, i, [i, i + 1], kind="identity")
    agent.inner.run_cognitive_tasks(3)
    loads = list(agent.inner.neighbours(area, "has_area_load"))
    assert len(loads) == 1
    attrs = agent.s.node(loads[0])["attrs"]
    assert attrs["capacity_workers"] == 3 and attrs["completed"] == 4

    # Add queued work after the clean completion; feedback may expand only up
    # to the measured capacity supplied by the runtime.
    queued = agent.s.add_node("CognitiveTask", {
        "status": "pending", "kind": "identity", "payload": [1],
        "input_epoch": 1, "logical_time": 9, "area": "test",
        "order": 1, "salience": 2.0,
    })
    agent.inner.add_edge_unchecked(area, "has_task", queued)
    agent.inner.set_attr(loads[0], "queued", 1)
    agent.tick()
    assert 1 <= agent.s.node(area)["attrs"]["desired_workers"] <= 3
    assert agent.s.node(area)["attrs"]["effort"] == 2.0


def test_completed_material_advances_only_its_area_clock():
    agent, area = _fresh()
    task = _task(agent, area, 1, [1, 2], kind="identity")
    before = agent.s.node(area)["attrs"]["logical_tick"]
    agent.inner.run_cognitive_tasks(1)
    agent.tick()
    assert agent.s.node(task)["attrs"]["clock_accounted"] == 1.0
    assert agent.s.node(area)["attrs"]["logical_tick"] == before + 1


def test_autonomous_pure_compute_does_not_hold_graph_mutex():
    agent, area = _fresh()
    agent.inner.set_attr(area, "desired_workers", 1)
    payload = [float((i * 13) % 29) for i in range(2600)]
    task = _task(agent, area, 1, payload, kind="dft_energy")
    agent.s.start_agent(tick_rate_hz=500, n_threads_per_runner=1)
    try:
        deadline = time.perf_counter() + 2.0
        while (agent.s.node(task)["attrs"].get("status") != "running"
               and time.perf_counter() < deadline):
            time.sleep(0.001)
        assert agent.s.node(task)["attrs"].get("status") == "running"
        started = time.perf_counter()
        agent.s.add_node("ObservationProbe", {"during_compute": 1})
        write_ms = (time.perf_counter() - started) * 1000
        assert write_ms < 20.0, (
            f"graph write blocked behind pure compute: {write_ms:.1f}ms")
        while (agent.s.node(task)["attrs"].get("status") == "running"
               and time.perf_counter() < deadline):
            time.sleep(0.002)
        assert agent.s.node(task)["attrs"].get("status") == "done"
    finally:
        agent.s.stop_agent()
