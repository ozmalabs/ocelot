"""P24 matched-arm curve invariants and information-cost accounting."""
from evaluation.process_mastery.target_learning_curve_v2 import (
    ARMS, CHECKPOINTS, _auc, run_development_panel, self_check)


def test_receipt_sets_match_by_checkpoint():
    result = run_development_panel(streams_per_pair=1, stream_prefix="p24-receipts")
    streams = {row["stream_id"] for row in result["records"]}
    assert len(streams) == 2
    for stream in streams:
        rows = [row for row in result["records"] if row["stream_id"] == stream]
        assert {row["arm"] for row in rows} == set(ARMS)
        assert len({tuple(row["target_receipt_ids"]) for row in rows}) == 1
        for checkpoint in CHECKPOINTS:
            assert all(row["curve"][checkpoint]["target_interactions"] == checkpoint
                       for row in rows)


def test_target_learner_identical_across_arms():
    result = run_development_panel(streams_per_pair=1, stream_prefix="p24-paths")
    for stream in {row["stream_id"] for row in result["records"]}:
        rows = [row for row in result["records"] if row["stream_id"] == stream]
        assert len({repr(row["ordinary_evidence_signature"]) for row in rows}) == 1
        assert {row["target_actions"] for row in rows} == {2}


def test_auc_uses_same_horizon():
    all_fail = [{"target_interactions": 0, "success": 0},
                {"target_interactions": 1, "success": 0},
                {"target_interactions": 2, "success": 0}]
    all_pass = [{"target_interactions": 0, "success": 1},
                {"target_interactions": 1, "success": 1},
                {"target_interactions": 2, "success": 1}]
    assert _auc(all_fail) == 0.0
    assert _auc(all_pass) == 1.0


def test_source_and_target_costs_not_hidden():
    result = run_development_panel(streams_per_pair=1, stream_prefix="p24-costs")
    for stream in {row["stream_id"] for row in result["records"]}:
        by_arm = {row["arm"]: row for row in result["records"]
                  if row["stream_id"] == stream}
        assert {row["target_actions"] for row in by_arm.values()} == {2}
        assert by_arm["fresh"]["source_action_count"] == 0
        assert by_arm["compatible_source"]["source_action_count"] == 2
        assert by_arm["wrong_source"]["source_action_count"] == 2
        assert by_arm["same_target_map_work"]["source_action_count"] == 0
        assert by_arm["compatible_source"]["map_pair_count"] == 2
        assert by_arm["wrong_source"]["map_pair_count"] == 2
        assert by_arm["same_target_map_work"]["map_pair_count"] == 2
        assert by_arm["fresh"]["map_work_budget_debits"] == 0
        assert by_arm["compatible_source"]["map_work_budget_debits"] == 2
        assert by_arm["same_target_map_work"]["map_work_budget_debits"] == 2
        assert all(row["shared_budget_debits"] >= 2 for row in by_arm.values())


def test_all_fail_and_all_pass_streams_are_retained():
    result = self_check()
    assert result["heldout_accessed"] is False
    assert result["task_design"]["context_epochs"] == [5, 6]
    assert len(result["records"]) == 2 * 2 * len(ARMS)
    assert all(row["status"] == "complete" for row in result["records"])
    assert all(summary["all_streams_retained"] for summary in result["summary"].values())
