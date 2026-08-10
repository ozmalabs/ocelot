"""Exact phase-plan boundary for the asynchronous-core migration."""
from __future__ import annotations

import inspect
import time

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402


def test_master_legacy_trace_preserves_fold_before_host_boundaries():
    agent = WorldAdapter(seeds=())
    node = agent.s.add_node("ClockProbe", {
        "clocked": 1, "level": 9, "next_level": 3,
    })
    report = agent.inner.run_cycle("master_legacy", trace=True)
    assert agent.s.node(node)["attrs"]["level"] == 3
    phases = [event[1] for event in report["trace"]]
    assert phases == [
        "clock_fold", "reflex_boundary", "thread_boundary",
        "result_fold_boundary",
    ]
    assert report["clock_commits"] == 1


def test_cognitive_legacy_reports_reflex_boundary_without_firing_host_callback():
    agent = WorldAdapter(seeds=())
    report = agent.inner.run_cycle("cognitive_legacy", trace=True)
    assert report["needs_reflex_dispatch"] is True
    assert [event[1] for event in report["trace"]][-1] == "reflex_boundary"


def test_world_adapter_entrypoints_are_cycle_plan_wrappers():
    assert "run_cycle(\"default\"" in inspect.getsource(WorldAdapter.tick)
    assert "run_cycle(\"cognitive_legacy\"" in inspect.getsource(WorldAdapter.cognitive_tick)
    assert "run_cycle(\"master_legacy\"" in inspect.getsource(WorldAdapter.master_tick)
    assert "run_rules(" not in inspect.getsource(WorldAdapter.cognitive_tick)
    assert "fold_clock_edge(" not in inspect.getsource(WorldAdapter.master_tick)


def test_unknown_cycle_plan_fails_closed():
    agent = WorldAdapter(seeds=())
    with pytest.raises(ValueError, match="unknown cycle plan"):
        agent.inner.run_cycle("not-a-plan")


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _soft_probe(agent):
    probe = agent.s.add_node("DefaultCycleProbe", {"ran": 0})
    root = agent.s.add_node("DefaultCycleRoot", {})
    _edge(agent, root, "has_default_cycle_probe", probe)
    agent.inner.add_rule({
        "name": "test_default_cycle_soft_probe",
        "area": "planning",
        "order": 0,
        "latency_class": "soft_realtime",
        "match": [["root", "has_default_cycle_probe", "probe"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr",
                  "node": {"type": "Var", "name": "probe"},
                  "key": "ran"},
            "b": {"type": "Lit", "value": 0},
        },
        "effects": [["set_attr", "probe", "ran", 1]],
    })
    return probe


def test_default_cycle_preserves_legacy_settlement_without_dual_process_core():
    agent = WorldAdapter(seeds=())
    probe = _soft_probe(agent)

    assert agent.tick() > 0
    assert agent.s.node(probe)["attrs"]["ran"] == 1


def test_default_cycle_gates_soft_rules_when_dual_process_core_is_enabled():
    agent = WorldAdapter(
        seeds=("affective_state_core", "dual_process_core"))
    probe = _soft_probe(agent)

    agent.tick()

    assert agent.s.node(probe)["attrs"]["ran"] == 0


def test_background_agent_uses_same_dual_process_gate_as_default_cycle():
    agent = WorldAdapter(
        seeds=("affective_state_core", "dual_process_core"))
    probe = _soft_probe(agent)
    agent.s.start_agent(tick_rate_hz=200.0)
    try:
        time.sleep(0.04)
    finally:
        agent.s.stop_agent()
    assert agent.s.node(probe)["attrs"]["ran"] == 0

    request = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "test", "epoch": 1,
    })
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "name": "background_planning", "area": "planning", "enabled": 1,
    })
    _edge(agent, request, "recruits_task_set", task_set)
    agent.s.start_agent(tick_rate_hz=200.0)
    try:
        deadline = time.monotonic() + 0.5
        while (agent.s.node(probe)["attrs"]["ran"] == 0
               and time.monotonic() < deadline):
            time.sleep(0.005)
    finally:
        agent.s.stop_agent()

    assert agent.s.node(request)["attrs"]["status"] == "serviced"
    assert agent.s.node(probe)["attrs"]["ran"] == 1


def test_concurrent_same_area_requests_receive_isolated_admission_tokens():
    agent = WorldAdapter(
        seeds=("affective_state_core", "dual_process_core"))
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "name": "shared_planning", "area": "planning", "enabled": 1,
    })
    overlap = agent.s.add_node("AdmissionOverlapProbe", {"seen": 0})
    root = agent.s.add_node("AdmissionOverlapRoot", {})
    _edge(agent, root, "has_admission_overlap_probe", overlap)

    requests = []
    probes = []
    for epoch in (1, 2):
        request = agent.s.add_node("SystemTwoEscalation", {
            "status": "requested", "reason": "test", "epoch": epoch,
        })
        probe = agent.s.add_node("PerRequestProbe", {"ran": 0})
        _edge(agent, request, "recruits_task_set", task_set)
        _edge(agent, request, "has_request_probe", probe)
        requests.append(request)
        probes.append(probe)

    agent.inner.add_rule({
        "name": "test_per_request_admitted_work",
        "area": "planning", "order": 0,
        "latency_class": "soft_realtime",
        "match": [["request", "has_request_probe", "probe"]],
        "where": {"type": "And", "items": [
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "request"},
                   "key": "status"},
             "b": {"type": "Lit", "value": "admitted"}},
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "probe"},
                   "key": "ran"},
             "b": {"type": "Lit", "value": 0}},
        ]},
        "effects": [["set_attr", "probe", "ran", 1]],
    })
    agent.inner.add_rule({
        "name": "test_no_two_requests_admitted_together",
        "area": "planning", "order": 0,
        "latency_class": "soft_realtime",
        "match": [
            ["root", "has_admission_overlap_probe", "overlap"],
            ["left", "has_request_probe", "left_probe"],
            ["right", "has_request_probe", "right_probe"],
        ],
        "where": {"type": "And", "items": [
            {"type": "Not",
             "arg": {"type": "Eq",
                     "a": {"type": "Var", "name": "left"},
                     "b": {"type": "Var", "name": "right"}}},
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "left"},
                   "key": "status"},
             "b": {"type": "Lit", "value": "admitted"}},
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "right"},
                   "key": "status"},
             "b": {"type": "Lit", "value": "admitted"}},
        ]},
        "effects": [["set_attr", "overlap", "seen", 1]],
    })

    report = agent.dual_process_tick()

    assert report["system_two_escalations"] == 2
    assert all(agent.s.node(p)["attrs"]["ran"] == 1 for p in probes)
    assert all(agent.s.node(r)["attrs"]["status"] == "serviced"
               for r in requests)
    assert agent.s.node(overlap)["attrs"]["seen"] == 0


def test_graph_opt_in_allows_same_area_contexts_to_settle_in_parallel():
    agent = WorldAdapter(
        seeds=("affective_state_core", "dual_process_core"))
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "area": "planning", "enabled": 1,
    })
    root = agent.s.add_node("AdmissionOverlapRoot", {})
    overlap = agent.s.add_node("AdmissionOverlapProbe", {"seen": 0})
    _edge(agent, root, "has_admission_overlap_probe", overlap)
    requests = []
    for epoch in (1, 2):
        request = agent.s.add_node("SystemTwoEscalation", {
            "status": "requested", "reason": "test", "epoch": epoch,
            "parallel_contexts": 1,
        })
        probe = agent.s.add_node("PerRequestProbe", {})
        _edge(agent, request, "recruits_task_set", task_set)
        _edge(agent, request, "has_request_probe", probe)
        requests.append(request)
    agent.inner.add_rule({
        "name": "test_graph_authored_parallel_admission",
        "area": "planning", "order": 0,
        "latency_class": "soft_realtime",
        "match": [
            ["root", "has_admission_overlap_probe", "overlap"],
            ["left", "has_request_probe", "left_probe"],
            ["right", "has_request_probe", "right_probe"],
        ],
        "where": {"type": "And", "items": [
            {"type": "Not", "arg": {"type": "Eq",
             "a": {"type": "Var", "name": "left"},
             "b": {"type": "Var", "name": "right"}}},
            {"type": "Eq",
             "a": {"type": "Attr", "node": {"type": "Var", "name": "left"},
                   "key": "status"},
             "b": {"type": "Lit", "value": "admitted"}},
            {"type": "Eq",
             "a": {"type": "Attr", "node": {"type": "Var", "name": "right"},
                   "key": "status"},
             "b": {"type": "Lit", "value": "admitted"}},
        ]},
        "effects": [["set_attr", "overlap", "seen", 1]],
    })

    report = agent.dual_process_tick()

    assert report["system_two_escalations"] == 2
    assert agent.s.node(overlap)["attrs"]["seen"] == 1
    assert all(agent.s.node(request)["attrs"]["status"] == "serviced"
               for request in requests)
