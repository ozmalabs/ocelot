"""Active cognition checks in on surprise or approximate evidence-time."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.gen_cognitive_supervision_seed import manifest
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]


def _edge(agent, src, edge_type, tgt):
    agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _fixture(span=4):
    agent = WorldAdapter(seeds=("cognitive_supervision",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": span,
        "cognitive_continuation_authority": 1,
        "cognitive_checkin_terminal": 0,
    })
    plan = agent.s.add_node("LearningPlan", {"status": "active"})
    step = agent.s.add_node("LearningPlanStep", {
        "status": "active", "last_receipt_seq": 0,
        "context_evidence_units": 0, "evidence_spent_units": 0,
    })
    instance = agent.s.add_node("Node", {
        "status": "active", "success_count": 0, "failure_count": 0,
    })
    goal = agent.s.add_node("Goal", {
        "status": "active", "progress_units": 0, "resolved_units": 0,
    })
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "plans_learning_capability", instance)
    _edge(agent, step, "pursues_goal", goal)
    agent.tick()
    process = list(agent.s.nodes("CognitiveProcess"))[0]
    return agent, episode, plan, step, instance, process


def _advance(agent, step, instance, *, epoch, effort, success, failure,
             context=0):
    process = list(agent.s.nodes("CognitiveProcess"))[0]
    goal = agent.inner.neighbours(process, "pursues_goal")[0]
    policy = agent.inner.neighbours(
        process, "governed_by_cognitive_supervision_policy"
    )[0]
    # The native outer-cycle boundary advances this once before settlement.
    agent.inner.set_attr(policy, "cognitive_epoch", epoch - 1)
    for node, key, value in (
        (step, "last_receipt_seq", epoch),
        (step, "evidence_spent_units", effort),
        (step, "context_evidence_units", context),
        (instance, "success_count", success),
        (instance, "failure_count", failure),
        (goal, "progress_units", success),
    ):
        agent.inner.set_attr(node, key, value)
    agent.tick()


def test_supervision_seed_regenerates_and_cognition_is_integer_only():
    committed = json.loads(
        (ROOT / "seeds" / "cognitive_supervision.json").read_text()
    )
    generated = manifest()
    assert generated == committed

    def visit(value):
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(generated)


def test_supervisory_lease_publishes_graph_owned_async_cycle_budget_provenance():
    agent, _, _, step, instance, process = _fixture(span=4)
    budget = list(agent.s.nodes("AsyncDaemonCycleBudget"))
    assert len(budget) == 1
    budget = budget[0]
    attrs = agent.s.node(budget)["attrs"]
    assert attrs["quantum_units"] == 4
    assert attrs["observed_lease_generation"] == 0
    first = agent.inner.neighbours(
        budget, "has_daemon_cycle_budget_adjustment"
    )
    assert len(first) == 1
    assert agent.s.node(first[0])["attrs"]["reason"] == (
        "supervisory_lease_renewal"
    )

    _advance(agent, step, instance, epoch=4, effort=4, success=1, failure=0)
    attrs = agent.s.node(budget)["attrs"]
    assert attrs["observed_lease_generation"] == 1
    assert attrs["adjustment_count"] == 2
    adjustments = agent.inner.neighbours(
        budget, "has_daemon_cycle_budget_adjustment"
    )
    assert len(adjustments) == 2
    assert all(agent.inner.neighbours(
        adjustment, "adjusts_for_cognitive_process"
    ) == [process] for adjustment in adjustments)


def test_productive_window_checks_in_then_explicitly_continues():
    agent, episode, _, step, instance, process = _fixture(span=4)
    _advance(
        agent, step, instance,
        epoch=4, effort=4, success=1, failure=2,
    )

    checkin = list(agent.s.nodes("CognitiveCheckIn"))[0]
    attrs = agent.s.node(checkin)["attrs"]
    assert attrs["reason"] == "approximate_time"
    assert attrs["status"] == "continued"
    assert attrs["causal_yield_units"] == 1
    assert attrs["effort_units"] == 4
    assert agent.s.node(process)["attrs"]["next_checkin_epoch"] == 8
    assert agent.s.node(process)["attrs"]["lease_generation"] == 1
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 1
    profile = agent.inner.neighbours(
        checkin, "has_efficiency_pareto_profile"
    )[0]
    assert agent.s.node(profile)["attrs"]["scalarized"] == 0
    assert agent.s.node(profile)["attrs"]["dimension_count"] == 1
    escalation = list(agent.s.nodes("SystemTwoEscalation"))[0]
    assert agent.s.node(escalation)["attrs"]["parallel_contexts"] == 1


def test_cognitive_supervision_rules_refresh_on_checkpoint_resume():
    from scripts import jabberwock_daemon as daemon

    assert "cognitive_supervision" in daemon._REFRESHABLE_SEEDS


def test_unproductive_window_is_dominated_and_cannot_continue():
    agent, episode, plan, step, instance, process = _fixture(span=4)
    _advance(
        agent, step, instance,
        epoch=4, effort=4, success=0, failure=1,
    )

    checkin = list(agent.s.nodes("CognitiveCheckIn"))[0]
    assert agent.s.node(checkin)["attrs"]["status"] == "replan_required"
    assert agent.s.node(process)["attrs"]["status"] == "replan_required"
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 0
    residuals = agent.inner.neighbours(step, "has_learning_plan_residual")
    assert len(residuals) == 1
    assert agent.s.node(residuals[0])["attrs"]["kind"] == (
        "inefficient_cognitive_process_window"
    )
    current = agent.inner.neighbours(
        agent.inner.neighbours(checkin, "has_efficiency_pareto_profile")[0],
        "has_incumbent_pareto_candidate",
    )[0]
    assert agent.inner.neighbours(current, "is_dominated_by_pareto_candidate") == []


def test_surprise_preempts_approximate_checkin_time():
    agent, episode, _, step, instance, process = _fixture(span=4)
    signal = agent.s.add_node("CognitiveProcessSignal", {
        "kind": "embodiment_integrity",
        "observed_units": 1,
        "expected_lower_units": 0,
        "expected_upper_units": 0,
        "supervision_processed": 0,
    })
    _edge(agent, process, "observes_process_signal", signal)
    _advance(
        agent, step, instance,
        epoch=1, effort=1, success=0, failure=0,
    )

    checkin = list(agent.s.nodes("CognitiveCheckIn"))[0]
    attrs = agent.s.node(checkin)["attrs"]
    assert attrs["epoch"] == 1
    assert attrs["reason"] == "outside_expected_bounds"
    assert attrs["status"] == "replan_required"
    assert agent.inner.neighbours(
        checkin, "triggered_by_process_signal"
    ) == [signal]
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 0


def test_checkin_time_is_situated_not_a_global_magic_interval():
    short = _fixture(span=3)
    long = _fixture(span=7)
    assert short[0].s.node(short[-1])["attrs"]["next_checkin_epoch"] == 3
    assert long[0].s.node(long[-1])["attrs"]["next_checkin_epoch"] == 7

    _advance(short[0], short[3], short[4],
             epoch=2, effort=2, success=0, failure=0)
    assert list(short[0].s.nodes("CognitiveCheckIn")) == []


def test_cognitive_clock_checks_in_even_when_no_receipt_arrives():
    agent, episode, _, _, _, process = _fixture(span=3)
    policy = agent.inner.neighbours(
        process, "governed_by_cognitive_supervision_policy"
    )[0]
    agent.inner.set_attr(policy, "cognitive_epoch", 2)
    agent.tick()

    checkin = list(agent.s.nodes("CognitiveCheckIn"))[0]
    assert agent.s.node(checkin)["attrs"]["reason"] == "approximate_time"
    assert agent.s.node(checkin)["attrs"]["status"] == "replan_required"
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 0


def test_signal_inside_expected_envelope_does_not_preempt_lease():
    agent, _, _, step, instance, process = _fixture(span=4)
    signal = agent.s.add_node("CognitiveProcessSignal", {
        "kind": "load",
        "observed_units": 2,
        "expected_lower_units": 1,
        "expected_upper_units": 3,
        "supervision_processed": 0,
    })
    _edge(agent, process, "observes_process_signal", signal)
    _advance(
        agent, step, instance,
        epoch=1, effort=1, success=0, failure=1,
    )
    assert list(agent.s.nodes("CognitiveCheckIn")) == []
    assert agent.s.node(process)["attrs"]["continuation_authority"] == 1


def test_previous_window_dominates_same_yield_at_twice_the_effort():
    agent, episode, _, step, instance, process = _fixture(span=4)
    _advance(
        agent, step, instance,
        epoch=4, effort=2, success=1, failure=0,
    )
    first_reference = agent.inner.neighbours(
        process, "has_reference_efficiency_window"
    )[0]
    assert agent.s.node(first_reference)["attrs"]["effort_units"] == 2

    _advance(
        agent, step, instance,
        epoch=8, effort=6, success=2, failure=0,
    )
    checkins = sorted(
        agent.s.nodes("CognitiveCheckIn"),
        key=lambda node: agent.s.node(node)["attrs"]["epoch"],
    )
    second = checkins[-1]
    assert agent.s.node(second)["attrs"]["status"] == "replan_required"
    profile = agent.inner.neighbours(
        second, "has_efficiency_pareto_profile"
    )[0]
    current = agent.inner.neighbours(
        profile, "has_incumbent_pareto_candidate"
    )[0]
    dominators = agent.inner.neighbours(
        current, "is_dominated_by_pareto_candidate"
    )
    assert any(
        agent.s.node(candidate)["attrs"]["kind"]
        == "previous_cognitive_efficiency_window"
        for candidate in dominators
    )
    assert agent.s.node(process)["attrs"]["continuation_authority"] == 0
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 0


def test_deep_subgoal_progress_renews_root_process_without_root_progress():
    agent, _, _, step, instance, process = _fixture(span=4)
    root = agent.inner.neighbours(process, "pursues_goal")[0]
    child = agent.s.add_node("Goal", {
        "progress_units": 0, "resolved_units": 0,
    })
    grandchild = agent.s.add_node("Goal", {
        "progress_units": 0, "resolved_units": 0,
    })
    _edge(agent, root, "has_subgoal", child)
    _edge(agent, child, "has_subgoal", grandchild)
    agent.tick()

    assert set(agent.inner.neighbours(process, "supervises_goal")) == {
        root, child, grandchild,
    }
    agent.inner.set_attr(grandchild, "progress_units", 1)
    _advance(
        agent, step, instance,
        epoch=4, effort=4, success=0, failure=0,
    )

    checkin = list(agent.s.nodes("CognitiveCheckIn"))[0]
    assert agent.s.node(checkin)["attrs"]["status"] == "continued"
    assert agent.s.node(checkin)["attrs"]["goal_progress_units"] == 1
    profile = agent.inner.neighbours(
        checkin, "has_efficiency_pareto_profile"
    )[0]
    assert agent.s.node(profile)["attrs"]["dimension_count"] == 3
    for candidate in agent.inner.neighbours(profile, "has_pareto_candidate"):
        assert len(agent.inner.neighbours(candidate, "has_pareto_value")) == 3


def test_embodied_bridge_publishes_structural_surprise_not_normal_failure():
    agent = WorldAdapter(seeds=("embodied_development",))
    runtime = agent.s.add_node("HumanoidEpisode", {
        "structural_interrupt_required": 0,
    })
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "latest_development_receipt_seq": 1,
    })
    process = agent.s.add_node("CognitiveProcess", {
        "status": "monitoring",
    })
    receipt = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
        "development_receipt_seq": 1,
        "embodiment_destroyed": 0,
        "cognitive_surprise_published": 0,
    })
    _edge(agent, runtime, "projects_embodied_development", episode)
    _edge(agent, episode, "has_cognitive_process", process)
    _edge(agent, episode, "has_embodied_development_receipt", receipt)

    agent.tick()
    assert agent.inner.neighbours(
        process, "observes_process_signal"
    ) == []

    agent.inner.set_attr(runtime, "structural_interrupt_required", 1)
    agent.tick()
    signals = agent.inner.neighbours(process, "observes_process_signal")
    assert len(signals) == 1
    signal = signals[0]
    assert agent.s.node(signal)["attrs"]["kind"] == (
        "structural_body_envelope"
    )
    assert agent.inner.neighbours(
        signal, "grounded_in_causal_receipt"
    ) == [receipt]


def test_humanoid_adapter_honours_withdrawn_graph_authority():
    from scripts.jabberwock_humanoid_walk import (
        _cognitive_continuation_authorised,
    )

    agent, development, _, _, _, process = _fixture(span=4)
    runtime = agent.s.add_node("HumanoidEpisode", {
        "cognitive_continuation_authority": 1,
    })
    assert _cognitive_continuation_authorised(
        agent, runtime, development
    )
    agent.inner.set_attr(process, "continuation_authority", 0)
    assert not _cognitive_continuation_authorised(
        agent, runtime, development
    )
    agent.inner.set_attr(process, "continuation_authority", 1.0)
    assert not _cognitive_continuation_authorised(
        agent, runtime, development
    )
    agent.inner.set_attr(runtime, "cognitive_continuation_authority", 0)
    assert not _cognitive_continuation_authorised(agent, runtime, None)

    source = (ROOT / "scripts" / "jabberwock_humanoid_walk.py").read_text()
    gate = source.index("if not _cognitive_continuation_authorised(")
    enact = source.index("token, trial, decision = _request_action", gate)
    assert gate < enact
