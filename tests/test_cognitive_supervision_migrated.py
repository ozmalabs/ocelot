"""Active cognition checks in on surprise or approximate evidence-time."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.gen_cognitive_supervision_seed import manifest
from scripts.jabberwock_humanoid_walk import (
    _cognitive_continuation_authorised,
    _settle_cognitive_continuation_authority,
)
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


def test_unproductive_window_preserves_only_viable_future():
    agent, episode, plan, step, instance, process = _fixture(span=4)
    _advance(
        agent, step, instance,
        epoch=4, effort=4, success=0, failure=1,
    )

    checkin = list(agent.s.nodes("CognitiveCheckIn"))[0]
    assert agent.s.node(checkin)["attrs"]["status"] == "continued"
    assert agent.s.node(process)["attrs"]["status"] == "monitoring"
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 1
    assert agent.inner.neighbours(step, "has_learning_plan_residual") == []


def test_unproductive_window_replans_when_replacement_future_exists():
    agent, episode, plan, step, instance, process = _fixture(span=4)
    replacement = agent.s.add_node("LearningPlanStep", {"status": "ready"})
    _edge(agent, plan, "has_learning_plan_step", replacement)

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


def test_new_graph_selected_step_attaches_process_and_clears_terminal_latch():
    agent, episode, plan, step, instance, process = _fixture(span=4)
    _advance(
        agent, step, instance,
        epoch=4, effort=4, success=0, failure=1,
    )

    replacement_step = agent.s.add_node("LearningPlanStep", {
        "status": "active", "last_receipt_seq": 0,
        "context_evidence_units": 0, "evidence_spent_units": 0,
    })
    replacement_instance = agent.s.add_node("Node", {
        "status": "active", "success_count": 0, "failure_count": 0,
    })
    replacement_goal = agent.s.add_node("Goal", {
        "status": "active", "progress_units": 0, "resolved_units": 0,
    })
    for source, edge_type, target in (
        (plan, "has_learning_plan_step", replacement_step),
        (replacement_step, "plans_learning_capability", replacement_instance),
        (replacement_step, "pursues_goal", replacement_goal),
    ):
        _edge(agent, source, edge_type, target)

    # This is the ordinary graph planner handoff: release the held step and
    # select a valid replacement. The supervision seed must attach a fresh
    # process and clear the old check-in's terminal latch.
    agent.inner.remove_edge_unchecked(
        plan, "has_selected_learning_plan_step", step
    )
    _edge(agent, plan, "has_selected_learning_plan_step", replacement_step)
    agent.tick(max_steps=100)

    assert agent.s.node(episode)["attrs"][
        "cognitive_checkin_terminal"
    ] == 0
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 1
    replacement_processes = [
        candidate for candidate in agent.s.nodes("CognitiveProcess")
        if replacement_step in agent.inner.neighbours(
            candidate, "supervises_learning_plan_step"
        )
    ]
    assert len(replacement_processes) == 1
    replacement_attrs = agent.s.node(replacement_processes[0])["attrs"]
    assert replacement_attrs["status"] == "monitoring"
    assert replacement_attrs["continuation_authority"] == 1


def test_exhausted_frontier_reopens_timed_suspension_but_not_surprise():
    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 4,
        "latest_development_receipt_seq": 0,
        "cognitive_continuation_authority": 0,
        "cognitive_checkin_terminal": 1,
    })
    plan = agent.s.add_node("LearningPlan", {"status": "active"})
    step = agent.s.add_node("LearningPlanStep", {
        "status": "meta_suspended", "ordinal": 3,
    })
    instance = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "meta_suspended", "ordinal": 3,
    })
    process = agent.s.add_node("CognitiveProcess", {
        "status": "replan_required", "continuation_authority": 0,
        "replan_release_complete": 1,
    })
    checkin = agent.s.add_node("CognitiveCheckIn", {
        "status": "replan_required", "reason": "approximate_time",
    })
    for source, edge_type, target in (
        (episode, "has_self_directed_learning_plan", plan),
        (plan, "has_learning_plan_step", step),
        (step, "plans_learning_capability", instance),
        (episode, "has_cognitive_process", process),
        (process, "supervises_learning_plan_step", step),
        (process, "has_cognitive_checkin", checkin),
    ):
        _edge(agent, source, edge_type, target)

    agent.tick(max_steps=100)

    assert agent.s.node(process)["attrs"]["status"] == "frontier_exhausted"
    assert agent.s.node(step)["attrs"]["status"] != "meta_suspended"
    assert agent.s.node(instance)["attrs"]["status"] != "meta_suspended"

    # A structural surprise is not merely a stale preference and remains held.
    agent.inner.set_attr(step, "status", "meta_suspended")
    agent.inner.set_attr(instance, "status", "meta_suspended")
    agent.inner.set_attr(process, "status", "replan_required")
    agent.inner.set_attr(checkin, "reason", "outside_expected_bounds")
    agent.tick(max_steps=100)
    assert agent.s.node(process)["attrs"]["status"] == "replan_required"
    assert agent.s.node(step)["attrs"]["status"] == "meta_suspended"


def test_retired_process_cannot_shadow_replacement_lease_owner():
    agent = WorldAdapter(seeds=("cognitive_supervision",))
    episode = agent.s.add_node("Node", {})
    context = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {
        "evidence_spent_units": 65,
    })
    retired = agent.s.add_node("CognitiveProcess", {
        "status": "frontier_exhausted", "continuation_authority": 0,
        "replan_release_complete": 1,
    })
    current = agent.s.add_node("CognitiveProcess", {
        "status": "monitoring", "continuation_authority": 1,
        "lease_generation": 0, "renew_before_epoch": 21,
        "next_checkin_evidence_units": 86,
    })
    policy = agent.s.add_node("CognitiveSupervisionPolicy", {
        "enabled": 1, "cognitive_epoch": 14,
    })
    for source, edge_type, target in (
        (context, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (context, "has_cognitive_process", retired),
        (retired, "supervises_learning_plan_step", step),
        (context, "has_cognitive_process", current),
        (current, "supervises_learning_plan_step", step),
        (current, "governed_by_cognitive_supervision_policy", policy),
    ):
        _edge(agent, source, edge_type, target)

    assert _cognitive_continuation_authorised(
        agent, episode, context
    ) is True


def test_selected_active_lease_clears_a_stale_terminal_handoff_latch():
    agent = WorldAdapter(seeds=("cognitive_supervision",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "cognitive_checkin_terminal": 1,
        "cognitive_continuation_authority": 0,
    })
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    process = agent.s.add_node("CognitiveProcess", {
        "status": "monitoring", "continuation_authority": 1,
    })
    policy = agent.s.add_node("CognitiveSupervisionPolicy", {"enabled": 1})
    for source, edge_type, target in (
        (episode, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (episode, "has_cognitive_process", process),
        (process, "supervises_learning_plan_step", step),
        (process, "governed_by_cognitive_supervision_policy", policy),
    ):
        _edge(agent, source, edge_type, target)

    agent.tick(max_steps=100)

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["cognitive_checkin_terminal"] == 0
    assert attrs["cognitive_continuation_authority"] == 1


def test_only_the_selected_step_can_withdraw_global_continuation_authority():
    rules = {rule["name"]: rule for rule in manifest()["rules"]}

    for name in (
        "cs_hold_marginally_dominated_process_for_replanning",
        "cs_hold_zero_yield_process_for_replanning",
    ):
        assert [
            "plan", "has_selected_learning_plan_step", "step"
        ] in rules[name]["match"]


def test_productive_replan_selects_ready_alternative_after_suspended_step():
    """A real suspended cognitive step hands control back to the plan.

    The replacement is deliberately graph-authored and ready before the
    second check-in. The supervisor releases the old step; the ordinary
    developmental Pareto profile selects the alternative and the lease seed
    attaches a fresh process. No host selection or safety override is used.
    """
    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 9,
        "latest_development_receipt_seq": 0,
        "embodiment_reset_available": 1,
        "embodiment_reset_reachable": 1,
        "embodiment_reset_cost_units": 6,
        "embodied_reset_requested": 0,
        "development_effector_coverage_complete": 0,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    agent.tick(max_steps=100)

    plan = agent.inner.neighbours(
        episode, "has_self_directed_learning_plan"
    )[0]
    old_step = agent.inner.neighbours(
        plan, "has_selected_learning_plan_step"
    )[0]
    old_instance = agent.inner.neighbours(
        old_step, "plans_learning_capability"
    )[0]
    old_process = agent.inner.neighbours(
        episode, "has_cognitive_process"
    )[0]
    old_goal = agent.inner.neighbours(
        old_process, "pursues_goal"
    )[0]
    policy = agent.inner.neighbours(
        old_process, "governed_by_cognitive_supervision_policy"
    )[0]

    replacement_instance = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "graph_ready_replacement", "goal": "replacement_goal",
            "ordinal": 99, "status": "available", "attempt_count": 0,
            "success_count": 0, "failure_count": 0,
            "last_reinstantiation_failure_count": 0,
            "warm_start_overlap": 0, "optional_route": 1,
        },
    )
    replacement_step = agent.s.add_node("LearningPlanStep", {
        "name": "graph_ready_replacement", "goal": "replacement_goal",
        "ordinal": 99, "status": "ready", "evidence_budget_units": 9,
        "evidence_spent_units": 0, "context_evidence_units": 0,
        "successful_evidence_units": 0, "failed_evidence_units": 0,
        "last_receipt_seq": 0, "selection_count": 0,
        "revision_count": 0, "last_revision_receipt_seq": 0,
        "last_budget_review_receipt_seq": 0, "budget_success_baseline": 0,
        "budget_failure_baseline": 0, "deferred_generation": 0,
        "last_selected_decision_epoch": 0, "optional_route": 1,
    })
    replacement_goal = agent.s.add_node("Goal", {
        "status": "active", "progress_units": 0, "resolved_units": 0,
    })
    for source, edge_type, target in (
        (plan, "has_learning_plan_step", replacement_step),
        (replacement_step, "plans_learning_capability", replacement_instance),
        (replacement_step, "pursues_goal", replacement_goal),
    ):
        _edge(agent, source, edge_type, target)

    for node, key, value in (
        (old_step, "evidence_spent_units", 10),
        (old_instance, "success_count", 10),
        (old_instance, "failure_count", 0),
        (old_goal, "progress_units", 10),
    ):
        agent.inner.set_attr(node, key, value)
    agent.inner.set_attr(policy, "cognitive_epoch", 3)
    agent.tick(max_steps=200)

    for node, key, value in (
        (old_step, "evidence_spent_units", 19),
        (old_instance, "success_count", 10),
        (old_instance, "failure_count", 4),
        (old_goal, "progress_units", 10),
    ):
        agent.inner.set_attr(node, key, value)
    agent.inner.set_attr(policy, "cognitive_epoch", 8)
    agent.tick(max_steps=300)

    # The old step stays suspended while the distinct graph-authored
    # replacement is selected; no evidence budget or mastery is fabricated.
    assert agent.s.node(old_step)["attrs"]["status"] == "meta_suspended"
    assert agent.s.node(old_process)["attrs"]["status"] == "replan_required"
    assert agent.inner.neighbours(
        plan, "has_selected_learning_plan_step"
    ) == [replacement_step]
    assert agent.s.node(episode)["attrs"][
        "cognitive_checkin_terminal"
    ] == 0
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 1
    new_processes = [
        process for process in agent.s.nodes("CognitiveProcess")
        if replacement_step in agent.inner.neighbours(
            process, "supervises_learning_plan_step"
        )
    ]
    assert len(new_processes) == 1
    assert agent.s.node(new_processes[0])["attrs"]["status"] == "monitoring"
    assert agent.s.node(new_processes[0])["attrs"][
        "continuation_authority"
    ] == 1


def test_verified_learning_safety_context_alone_does_not_revive_held_process():
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
        epoch=1, effort=1, success=0, failure=1,
    )
    safety = agent.s.add_node("LearningSafetyContext", {
        "verified": 1, "reset_reachable": 1, "reset_cost_units": 1,
        "protective_support_available": 0,
        "protective_support_effectiveness": 0,
        "recovery_path_count": 1, "required_horizon_units": 1,
        "minimum_width_relaxation": 1,
        "information_loss_allowance": 1,
    })
    _edge(agent, episode, "has_learning_safety_context", safety)

    for _ in range(2):
        agent.tick(max_steps=100)

    assert agent.s.node(episode)["attrs"][
        "cognitive_checkin_terminal"
    ] == 1
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 0
    assert agent.s.node(process)["attrs"]["status"] == "replan_required"
    assert agent.s.node(process)["attrs"]["continuation_authority"] == 0
    assert len(list(agent.s.nodes("CognitiveProcess"))) == 1


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


def test_cognitive_clock_does_not_check_in_without_evidence_progress():
    agent, episode, _, step, _, process = _fixture(span=3)
    policy = agent.inner.neighbours(
        process, "governed_by_cognitive_supervision_policy"
    )[0]
    agent.inner.set_attr(policy, "cognitive_epoch", 2)
    agent.tick()

    assert list(agent.s.nodes("CognitiveCheckIn")) == []

    # The same lease becomes due when the graph-owned evidence counter moves,
    # regardless of how many cognitive scheduler epochs elapsed.
    agent.inner.set_attr(step, "evidence_spent_units", 3)
    agent.tick()

    checkin = list(agent.s.nodes("CognitiveCheckIn"))[0]
    assert agent.s.node(checkin)["attrs"]["reason"] == "approximate_time"
    assert agent.s.node(checkin)["attrs"]["status"] == "continued"
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 1


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


def test_dominated_productive_window_continues_when_it_is_the_only_future():
    agent, episode, _, step, instance, process = _fixture(span=4)
    _advance(
        agent, step, instance,
        epoch=4, effort=4, success=1, failure=0,
    )
    first_reference = agent.inner.neighbours(
        process, "has_reference_efficiency_window"
    )[0]
    assert agent.s.node(first_reference)["attrs"]["effort_units"] == 4

    _advance(
        agent, step, instance,
        epoch=8, effort=12, success=2, failure=0,
    )
    checkins = sorted(
        agent.s.nodes("CognitiveCheckIn"),
        key=lambda node: agent.s.node(node)["attrs"]["epoch"],
    )
    second = checkins[-1]
    assert agent.s.node(second)["attrs"]["status"] == "continued"
    profile = agent.inner.neighbours(
        second, "has_efficiency_pareto_profile"
    )[0]
    current = agent.inner.neighbours(
        profile, "has_incumbent_pareto_candidate"
    )[0]
    # The direct Pareto comparison detects dominance before the historical
    # relation needs to be materialized, but cannot discard the sole future.
    assert agent.s.node(current)["attrs"]["dominated"] == 0
    assert agent.s.node(process)["attrs"]["continuation_authority"] == 1
    assert agent.s.node(episode)["attrs"][
        "cognitive_continuation_authority"
    ] == 1


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


def test_authority_boundary_settles_changed_graph_state_without_action(
    monkeypatch,
):
    import scripts.jabberwock_humanoid_walk as walk

    agent, development, _, _, _, process = _fixture(span=4)
    runtime = agent.s.add_node("HumanoidEpisode", {
        "cognitive_continuation_authority": 1,
    })
    agent.inner.set_attr(process, "continuation_authority", 0)
    calls = []

    def output_null_tick(active_agent, *, service_system_two=False):
        assert active_agent is agent
        assert service_system_two is True
        calls.append(len(calls))
        if len(calls) == 1:
            active_agent.inner.set_attr(process, "lease_generation", 1)
        else:
            active_agent.inner.set_attr(process, "continuation_authority", 1)

    monkeypatch.setattr(walk, "_tick_agent", output_null_tick)

    authorised, cycles = _settle_cognitive_continuation_authority(
        agent, runtime, development
    )

    assert authorised is True
    assert cycles == 2
    assert calls == [0, 1]


def test_authority_boundary_stops_when_scheduler_transition_repeats(monkeypatch):
    import scripts.jabberwock_humanoid_walk as walk

    agent, development, _, _, _, process = _fixture(span=4)
    runtime = agent.s.add_node("HumanoidEpisode", {
        "cognitive_continuation_authority": 1,
    })
    agent.inner.set_attr(process, "continuation_authority", 0)
    calls = []

    def output_null_tick(active_agent, *, service_system_two=False):
        assert active_agent is agent
        assert service_system_two is True
        calls.append(len(calls))

    monkeypatch.setattr(walk, "_tick_agent", output_null_tick)

    authorised, cycles = _settle_cognitive_continuation_authority(
        agent, runtime, development
    )

    assert authorised is False
    assert cycles == 2
    assert calls == [0, 1]


def test_completed_learning_plan_hands_authority_to_motor_manifold_gate(
    monkeypatch,
):
    import scripts.jabberwock_humanoid_walk as walk

    agent, development, plan, step, _, process = _fixture(span=4)
    runtime = agent.s.add_node("HumanoidEpisode", {
        "cognitive_continuation_authority": 1,
    })
    agent.inner.set_attr(plan, "status", "completed")
    agent.inner.set_attr(step, "status", "completed")
    agent.inner.set_attr(process, "continuation_authority", 0)
    _edge(agent, plan, "has_learning_plan_step", step)

    def unexpected_tick(*args, **kwargs):
        raise AssertionError("a completed plan has no authority work to settle")

    monkeypatch.setattr(walk, "_tick_agent", unexpected_tick)

    assert _cognitive_continuation_authorised(
        agent, runtime, development
    ) is True
    authorised, cycles = _settle_cognitive_continuation_authority(
        agent, runtime, development
    )

    assert authorised is True
    assert cycles == 0
