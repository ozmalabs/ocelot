"""The daemon executes graph-selected host work, never tick-counter policy."""
from __future__ import annotations

import inspect
import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from substrate.world_adapter import WorldAdapter  # noqa: E402
import jabberwock_daemon as daemon  # noqa: E402


def _supervised_experiment():
    agent = WorldAdapter(seeds=())
    assert daemon._ensure_supervisory_scheduler(agent) > 0
    agent.s.add_node("Experiment", {"status": "requested"})
    agent.tick()
    requests = list(agent.s.nodes("HostActionRequest"))
    assert len(requests) == 1
    return agent, requests[0]


def test_requested_experiment_becomes_graph_selected_host_action_with_integer_coordinates():
    agent, request = _supervised_experiment()
    attrs = agent.s.node(request)["attrs"]
    assert attrs["action"] == "dispatch"
    assert attrs["status"] == "requested"
    for key in ("urgency", "residual", "estimated_cost", "deadline", "priority"):
        assert type(attrs[key]) is int

    tasks = list(agent.inner.neighbours(request, "scheduled_as"))
    assert len(tasks) == 1
    task = agent.s.node(tasks[0])["attrs"]
    assert task["kind"] == "host_action"
    assert task["status"] == "host_requested"
    assert all(type(task[key]) is int for key in
               ("urgency", "residual", "estimated_cost", "deadline", "priority"))


def test_embodied_trial_enters_the_same_graph_selected_host_action_queue():
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    source = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "status": "requested", "supervision_priority": 3,
    })
    agent.tick()
    requests = [node for node in agent.s.nodes("HostActionRequest")
                if agent.s.node(node)["attrs"].get("action") == "embodied_trial"]
    assert len(requests) == 1
    attrs = agent.s.node(requests[0])["attrs"]
    assert attrs["status"] == "requested"
    assert attrs["source"] == source
    assert attrs["priority"] == 3


def test_host_executor_uses_selected_label_and_writes_receipt(monkeypatch):
    agent, request = _supervised_experiment()
    calls = []
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"dispatch": lambda: calls.append("dispatch")},
    )
    state = daemon.DaemonState(agent, "test")
    state.runs_dir = "/tmp/unused"

    assert daemon._execute_host_action_requests(state) == 1
    assert calls == ["dispatch"]
    assert agent.s.node(request)["attrs"]["status"] == "done"
    tasks = list(agent.inner.neighbours(request, "scheduled_as"))
    assert agent.s.node(tasks[0])["attrs"]["status"] == "done"
    receipts = list(agent.inner.neighbours(request, "has_receipt"))
    assert len(receipts) == 1
    receipt = agent.s.node(receipts[0])["attrs"]
    assert receipt["action"] == "dispatch" and receipt["status"] == "done"
    assert all(type(receipt[key]) is int for key in
               ("urgency", "residual", "estimated_cost", "deadline", "logical_time"))


def test_completed_action_rearms_supervision_for_a_new_source():
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    first_source = agent.s.add_node("StandingConcern", {"status": "pending"})
    agent.tick()
    first = [n for n in agent.s.nodes("HostActionRequest")
             if agent.s.node(n)["attrs"].get("action") == "concern"]
    assert len(first) == 1
    first_task = list(agent.inner.neighbours(first[0], "scheduled_as"))[0]

    agent.s.set_attr(first_source, "status", "processed")
    agent.s.set_attr(first[0], "status", "done")
    agent.s.set_attr(first_task, "status", "done")
    second_source = agent.s.add_node("StandingConcern", {"status": "pending"})
    agent.tick()

    requests = [n for n in agent.s.nodes("HostActionRequest")
                if agent.s.node(n)["attrs"].get("action") == "concern"]
    assert len(requests) == 2
    latest = max(requests, key=lambda n: n.value)
    attrs = agent.s.node(latest)["attrs"]
    assert attrs["source"] == second_source
    assert attrs["status"] == "requested"


def test_tick_loop_has_no_modulo_cognitive_policy():
    source = inspect.getsource(daemon.tick_loop)
    assert " % " not in source
    assert "_execute_host_action_requests" in source


def test_bounded_quantum_is_not_itself_a_daemon_continuation_signal():
    """A rewrite allowance is not evidence and may not self-spin planning."""
    source = inspect.getsource(daemon.tick_loop)
    assert "if completed:" in source
    assert "completed or progressed" not in source
    assert "if completed or (quantum" not in source


def test_graph_authored_cycle_quantum_still_admits_host_work(monkeypatch):
    """A graph-owned quantum does not prevent its selected host action."""
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    budget = agent.s.add_node("AsyncDaemonCycleBudget", {
        "status": "active", "quantum_units": 1,
        "integer_native": 1, "output_authority": 0,
    })
    agent.s.add_node("Experiment", {"status": "requested"})
    original_tick = agent.tick
    observed_quanta = []

    def bounded_tick(*, max_steps=100_000):
        observed_quanta.append(max_steps)
        original_tick(max_steps=max_steps)
        return max_steps

    monkeypatch.setattr(agent, "tick", bounded_tick)
    state = daemon.DaemonState(agent, "test")
    state.runs_dir = "/tmp/unused"
    stop = threading.Event()
    calls = []
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {
            "dispatch": lambda: (calls.append("dispatch"), stop.set()),
        },
    )
    daemon.tick_loop(state, stop, 1000, 0, state.runs_dir)

    assert calls == ["dispatch"]
    assert len(observed_quanta) == 1
    assert set(observed_quanta) == {1}
    attrs = agent.s.node(budget)["attrs"]
    assert attrs["last_consumed_quantum_units"] == 1
    assert attrs["last_consumed_rewrite_steps"] <= 1


def test_legacy_cadence_values_cannot_change_graph_request_selection(monkeypatch):
    """A requested experiment dispatches even when a legacy value is enormous.

    The comparison run with zero makes the compatibility claim explicit: the
    number only reaches deprecation logging and cannot gate graph work.
    """
    results = []
    for legacy_value in (0, 999_999):
        agent = WorldAdapter(seeds=())
        daemon._ensure_supervisory_scheduler(agent)
        agent.s.add_node("Experiment", {"status": "requested"})
        state = daemon.DaemonState(agent, "test")
        state.runs_dir = "/tmp/unused"
        stop = threading.Event()
        calls = []
        monkeypatch.setattr(
            daemon, "_host_action_handlers",
            lambda _state, _world: {
                "dispatch": lambda: (calls.append("dispatch"), stop.set()),
            },
        )
        daemon.tick_loop(state, stop, 1000, legacy_value, state.runs_dir)
        results.append(calls)
    assert results == [["dispatch"], ["dispatch"]]


def _pending_host_action(agent, action: str, priority: int):
    request = agent.s.add_node("HostActionRequest", {
        "action": action, "status": "pending",
        "urgency": priority, "residual": priority,
        "estimated_cost": 1, "deadline": 0, "priority": priority,
    })
    task = agent.s.add_node("CognitiveTask", {
        "kind": "host_action", "action": action, "area": "supervision",
        "status": "pending", "urgency": priority, "residual": priority,
        "estimated_cost": 1, "deadline": 0, "priority": priority,
        "input_epoch": 0, "logical_time": 0,
    })
    agent.inner.add_edge_unchecked(request, "scheduled_as", task)
    return request, task


def test_graph_priority_releases_higher_value_demand_before_lower_value_demand():
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    low, low_task = _pending_host_action(agent, "fetch", 2)
    high, high_task = _pending_host_action(agent, "teacher", 9)

    agent.tick()
    assert agent.s.node(high)["attrs"]["status"] == "requested"
    assert agent.s.node(high_task)["attrs"]["status"] == "host_requested"
    assert agent.s.node(low)["attrs"]["status"] == "pending"
    assert agent.s.node(low_task)["attrs"]["status"] == "pending"

    # A receipt/executor completion is the external event that releases the
    # next graph-selected task; there is no host counter in this transition.
    agent.s.set_attr(high, "status", "done")
    agent.s.set_attr(high_task, "status", "done")
    agent.tick()
    assert agent.s.node(low)["attrs"]["status"] == "requested"
    assert agent.s.node(low_task)["attrs"]["status"] == "host_requested"


def test_cross_action_graph_priority_beats_bridge_rule_order_then_releases_loser():
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    agent.s.add_node("StandingConcern", {
        "status": "pending", "supervision_priority": 2,
    })
    teacher_source = agent.s.add_node("TeacherRequest", {
        "status": "requested", "teacher_tier": "dictionary",
        "supervision_priority": 9,
    })

    agent.tick()
    requests = {agent.s.node(n)["attrs"]["action"]: n
                for n in agent.s.nodes("HostActionRequest")}
    assert set(requests) == {"concern", "teacher"}
    teacher = requests["teacher"]
    concern = requests["concern"]
    assert agent.s.node(teacher)["attrs"]["status"] == "requested"
    assert agent.s.node(concern)["attrs"]["status"] == "pending"

    teacher_task = list(agent.inner.neighbours(teacher, "scheduled_as"))[0]
    # The mechanical teacher handler settles its exact source before the
    # daemon writes the HostActionReceipt; model that external result here.
    agent.s.set_attr(teacher_source, "status", "completed")
    agent.s.set_attr(teacher, "status", "done")
    agent.s.set_attr(teacher_task, "status", "done")
    agent.tick()
    assert agent.s.node(concern)["attrs"]["status"] == "requested"


def test_equal_neutral_demands_release_exactly_one_graph_selected_action():
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    _pending_host_action(agent, "fetch", 1)
    _pending_host_action(agent, "detail", 1)
    agent.tick()
    statuses = [agent.s.node(n)["attrs"]["status"]
                for n in agent.s.nodes("HostActionRequest")]
    assert statuses.count("requested") == 1
    assert statuses.count("pending") == 1


def test_completion_receipt_releases_a_request_previously_held_by_backpressure(monkeypatch):
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    first, _ = _pending_host_action(agent, "teacher", 2)
    second, second_task = _pending_host_action(agent, "search", 1)
    agent.tick()
    assert agent.s.node(first)["attrs"]["status"] == "requested"
    assert agent.s.node(second)["attrs"]["status"] == "pending"

    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"teacher": lambda: None, "search": lambda: None},
    )
    state = daemon.DaemonState(agent, "test")
    assert daemon._execute_host_action_requests(state) == 1
    assert list(agent.inner.neighbours(first, "has_receipt"))

    agent.tick()
    assert agent.s.node(second)["attrs"]["status"] == "requested"
    assert agent.s.node(second_task)["attrs"]["status"] == "host_requested"


def test_teacher_action_carries_exact_selected_source_identity():
    agent = WorldAdapter(seeds=())
    daemon._ensure_supervisory_scheduler(agent)
    first = agent.s.add_node("TeacherRequest", {
        "status": "requested", "teacher_tier": "dictionary",
        "supervision_priority": 2,
    })
    selected = agent.s.add_node("TeacherRequest", {
        "status": "requested", "teacher_tier": "wikipedia",
        "supervision_priority": 9,
    })
    agent.tick()
    action = list(agent.s.nodes("HostActionRequest"))
    assert len(action) == 1
    attrs = agent.s.node(action[0])["attrs"]
    assert attrs["action"] == "teacher"
    assert attrs["source_type"] == "TeacherRequest"
    assert attrs["source"] == selected
    assert attrs["source"] != first


def test_default_library_attachment_enables_structured_teacher_when_llm_allowed(monkeypatch):
    import domains.libraries as libraries

    seen = {}

    def attach(adapter, *, enable_llm, log):
        seen["adapter"] = adapter
        seen["enable_llm"] = enable_llm
        return {"teachers": ["dictionary", "wiki"], "teacher": "llm", "skipped": []}

    monkeypatch.setattr(libraries, "attach_libraries", attach)
    agent = WorldAdapter(seeds=())
    report = daemon._attach_default_libraries(agent, enable_llm=True)
    assert seen == {"adapter": agent, "enable_llm": True}
    assert report["teachers"] == ["dictionary", "wiki"]
