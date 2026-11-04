import json
import math
import pytest

from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointWorldAdapter,
)
from evaluation.process_mastery.p22_four_arm_development import (
    run_p22_four_arm_development,
)


def test_four_arm_development_uses_same_training_world_and_no_approval_side_effects():
    result = run_p22_four_arm_development(family="d4", training_draws=(250,))
    assert result["status"] == "DEVELOPMENT_ONLY"
    assert result["split"] == "training"
    assert result["common_worlds"]
    assert result["all_arms_terminal"]
    assert set(result["arms"]) == {
        "unchanged", "adaptive_only", "invention_only", "full"}
    expected_id = "p22:d4-v2:train:0250"
    for arm, data in result["arms"].items():
        assert [row["world_id"] for row in data["training_tasks"]] == [expected_id]
        assert all(row["split"] == "training" for row in data["training_tasks"])
        assert data["approval_count"] == 0
        assert data["world_receipt_count"] == 0
        assert data["resource_snapshot"]["runtime_counters"][
            "native_rule_steps"] > 0
        assert data["resource_snapshot"]["runtime_counters"][
            "native_model_calls"] == 0
        resources = data["resource_snapshot"]
        assert resources["runtime_counters"]["search_attempts_reserved"] == (
            resources["resource_counts"]["search_attempts"])
        assert resources["runtime_counters"]["search_attempts_reserved"] <= 64
        assert math.isfinite(data["wall_time_seconds"])
        assert data["wall_time_seconds"] > 0
        assert data["resource_snapshot"]["runtime_counters"][
            "wall_time_seconds"] == data["wall_time_seconds"]
        assert data["resource_snapshot"]["resource_measurement_coverage"][
            "wall_time_seconds"]["status"] == "MEASURED"
    assert result["arms"]["adaptive_only"]["training_tasks"][0][
        "curriculum_status"] == "completed"
    assert result["arms"]["full"]["training_tasks"][0][
        "curriculum_status"] == "completed"
    assert result["approvals_created"] == 0
    assert result["world_receipts_created"] == 0
    assert result["efficacy_established"] is False


def test_single_arm_peak_rss_is_recorded_without_claiming_a_comparison():
    result = run_p22_four_arm_development(family="d4", training_draws=(250,),
        selected_arms=("unchanged",), measure_process_peak_rss=True,
        measure_native_rule_work=True)
    assert result["search_attempt_ceiling"] == 64
    assert result["resource_comparison"] is None
    counters = result["arms"]["unchanged"]["resource_snapshot"]["runtime_counters"]
    assert counters["process_peak_rss_bytes"] > 0
    rule_work = result["arms"]["unchanged"]["resource_snapshot"]["native_rule_work"]
    assert rule_work["totals_by_metric"]["term_evaluations"] > 0


def test_isolated_arm_can_capture_measured_generation_zero_checkpoint():
    from evaluation.process_mastery.checkpoint_world_adapter import CheckpointExpression

    result = run_p22_four_arm_development(family="d4", training_draws=(250,),
        selected_arms=("unchanged",), measure_process_peak_rss=True,
        measure_native_rule_work=True, capture_checkpoints=True)
    record = result["arms"]["unchanged"]["generation_zero_checkpoint"]
    checkpoint = CheckpointExpression(**record)
    assert CheckpointWorldAdapter._checkpoint_digest_valid(checkpoint)
    snapshot = json.loads(checkpoint.resource_snapshot_json)
    assert snapshot["native_rule_work"]["rule_identity_coverage"] == "COMPLETE"
    assert snapshot["runtime_counters"]["process_peak_rss_bytes"] > 0
    assert result["arms"]["unchanged"]["approval_count"] == 0
    assert result["arms"]["unchanged"]["world_receipt_count"] == 0


def test_search_attempt_ceiling_rejects_invalid_values():
    for ceiling in (0, -1, 30_001, True, 1.5):
        with pytest.raises(ValueError, match="search attempt ceiling"):
            run_p22_four_arm_development(family="d4", training_draws=(250,),
                search_attempt_ceiling=ceiling, selected_arms=("unchanged",))


def test_unapproved_candidates_are_scored_on_disjoint_validation_views():
    result = run_p22_four_arm_development(family="d4",
        training_draws=tuple(range(250, 258)),
        validation_draws=tuple(range(350, 358)))
    assert result["common_worlds"]
    assert len(result["validation_world_ids"]) == 8
    assert set(result["training_world_ids"]).isdisjoint(result["validation_world_ids"])
    expected_validation_ids = [f"p22:d4-v2:validation:{draw:04d}"
                               for draw in range(350, 358)]
    for arm_data in result["arms"].values():
        for panel in arm_data["candidate_validation_panels"]:
            assert panel["world_ids"] == expected_validation_ids
            assert [row["world_id"] for row in panel["outcomes"]] == expected_validation_ids
            assert panel["actionable"] is False
            assert panel["approval_created"] is False
            assert panel["world_receipts_created"] is False
        assert arm_data["approval_count"] == 0
        assert arm_data["world_receipt_count"] == 0
        count = sum(panel["world_count"]
                    for panel in arm_data["candidate_validation_panels"])
        assert arm_data["resource_snapshot"]["runtime_counters"][
            "native_candidate_validation_evaluations"] == count
