"""Regression gate for V2's installed world affordances and matched inputs."""
from evaluation.process_mastery.linear_p10_v2 import _run_task


def test_v2_installs_same_loopover_primitives_in_both_graph_arms():
    greedy = _run_task("loopover3", 0, "greedy", "development")
    discovered = _run_task("loopover3", 0, "discovered_strategy", "development")
    assert greedy["world_access_sha256"] == discovered["world_access_sha256"]
    for row in (greedy, discovered):
        audit = row["input_audit"]
        assert audit["primitive_affordances_installed"] is True
        assert audit["held_schema_count"] == 12
        assert audit["answer_fields_absent"] is True
        assert audit["trace_replays_to_reported_state"] is True


def test_v2_tool_goal_uses_graph_processes_and_reaches_observed_goal():
    for arm in ("greedy", "discovered_strategy"):
        row = _run_task("tool_goal", 400, arm, "development")
        assert row["status"] == "COMPLETED"
        assert row["outcome"] == "solved"
        assert row["input_audit"]["primitive_affordances_installed"] is True
        assert row["input_audit"]["trace_replays_to_reported_state"] is True
