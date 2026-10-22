from copy import deepcopy

import pytest

from evaluation.process_mastery.p22_resource_accounting import (
    compare_resource_snapshots, snapshot_native_resources,
)
from tests.test_open_process_search import _agent as _p19_agent


def test_native_snapshot_retains_failed_and_pending_search_and_budget_usage():
    agent, _domain = _p19_agent(attempts=32)
    try:
        budget = agent.nodes("ThinkingBudget")[0]
        agent.s.set_attr(budget, "remaining", 73.0)
        for status in ("failed", "timed_out", "pending"):
            attempt = agent.s.add_node("OpenProcessSearchAttempt", {"status": status})
            agent.s.add_edge(agent.ag, "has_open_process_search_attempt", attempt, {})

        snapshot = snapshot_native_resources(agent)
        counts = {(row["type"], row["status"]): row["count"]
                  for row in snapshot["status_counts"]}
        assert snapshot["thinking_budget_capacity"] == 100.0
        assert snapshot["thinking_budget_remaining"] == 73.0
        assert snapshot["thinking_budget_spent"] == 27.0
        assert snapshot["resource_counts"]["search_attempts"] == 3
        assert counts[("OpenProcessSearchAttempt", "failed")] == 1
        assert counts[("OpenProcessSearchAttempt", "timed_out")] == 1
        assert counts[("OpenProcessSearchAttempt", "pending")] == 1
        assert snapshot["serialized_graph_bytes"] > 0
    finally:
        del agent


def test_resource_comparison_checks_digest_and_keeps_each_arm_vector():
    agent, _domain = _p19_agent(attempts=32)
    try:
        legacy = snapshot_native_resources(agent)
        missing_runtime = compare_resource_snapshots(
            {"unchanged": legacy, "full": deepcopy(legacy)})
        assert not missing_runtime["all_resource_dimensions_match"]
        assert "native_rule_steps" in missing_runtime["unavailable_dimensions"]

        before = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 0, "native_model_calls": 0})
        after = deepcopy(before)
        result = compare_resource_snapshots({"unchanged": before, "full": after})
        assert result["all_resource_dimensions_match"]
        assert result["failure_statuses_retained"]
        assert result["arms"]["full"]["thinking_budget_spent"] == 0.0

        after["resource_counts"]["search_attempts"] += 1
        with pytest.raises(ValueError, match="digest does not verify"):
            compare_resource_snapshots({"unchanged": before, "full": after})
    finally:
        del agent


def test_resource_snapshot_counts_training_exposure_and_native_work():
    agent, _domain = _p19_agent(attempts=32)
    try:
        evidence = agent.s.add_node("ProcessCurriculumEvidence", {"split": "training"})
        heldout = agent.s.add_node("ProcessCurriculumEvidence", {"split": "heldout"})
        outcome = agent.s.add_node("ProcessCurriculumOutcome", {"split": "training"})
        task = agent.s.add_node("SolveTask", {
            "split": "training", "steps": 3, "moves": 5.5})
        attempt = agent.s.add_node("OpenProcessSearchAttempt", {"work_cost": 4.0})
        approved = agent.s.add_node("ThinkingBudgetRequest", {
            "status": "approved", "cost": 2.0})
        denied = agent.s.add_node("ThinkingBudgetRequest", {
            "status": "denied", "cost": 1.5})
        snapshot = snapshot_native_resources(agent)
        resources = snapshot["cumulative_resources"]
        assert resources["training_evidence_exposures"] == 1
        assert resources["training_outcomes"] == 1
        assert resources["training_task_exposures"] == 1
        assert resources["native_solver_steps"] == 3.0
        assert resources["native_solver_primitive_work"] == 5.5
        assert resources["search_declared_primitive_work"] == 4.0
        assert resources["budget_requested"] == 3.5
        assert resources["budget_approved"] == 2.0
        assert resources["budget_denied_cost"] == 1.5
        assert snapshot["snapshot_sha256"]
    finally:
        del agent


def test_runtime_rule_steps_are_digest_bound_and_comparison_detects_mismatch():
    agent, _domain = _p19_agent(attempts=32)
    try:
        low = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 120, "native_model_calls": 0})
        high = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 121, "native_model_calls": 0})
        result = compare_resource_snapshots({"low": low, "high": high})
        assert not result["all_resource_dimensions_match"]
        assert result["matched"]["native_rule_steps"] is False
        assert result["matched"]["native_model_calls"] is True
        with pytest.raises(ValueError, match="native_rule_steps"):
            snapshot_native_resources(agent,
                runtime_counters={"native_rule_steps": True})
    finally:
        del agent
