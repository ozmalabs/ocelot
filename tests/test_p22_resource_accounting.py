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
        before = snapshot_native_resources(agent)
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
