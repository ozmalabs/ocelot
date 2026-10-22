from evaluation.process_mastery.p22_four_arm_development import (
    run_p22_four_arm_development,
)


def test_four_arm_development_uses_same_training_world_and_no_approval_side_effects():
    result = run_p22_four_arm_development(family="d4", training_draws=(250,))
    assert result["status"] == "DEVELOPMENT_ONLY"
    assert result["split"] == "training"
    assert result["common_worlds"]
    assert set(result["arms"]) == {
        "unchanged", "adaptive_only", "invention_only", "full"}
    expected_id = "p22:d4-v2:train:0250"
    for arm, data in result["arms"].items():
        assert [row["world_id"] for row in data["training_tasks"]] == [expected_id]
        assert all(row["split"] == "training" for row in data["training_tasks"])
        assert data["approval_count"] == 0
        assert data["world_receipt_count"] == 0
    assert result["arms"]["adaptive_only"]["training_tasks"][0][
        "curriculum_status"] == "completed"
    assert result["arms"]["full"]["training_tasks"][0][
        "curriculum_status"] == "completed"
    assert result["approvals_created"] == 0
    assert result["world_receipts_created"] == 0
    assert result["efficacy_established"] is False
