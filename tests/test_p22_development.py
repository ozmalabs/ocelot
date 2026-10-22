from evaluation.process_mastery.p22_development import (
    run_p22_training_proposal_probe,
)


def test_v2_native_training_proposals_are_qualified_and_scored_nonactionably():
    cases = {
        "d4": ((1, 7), 16),
        "loopover": ((1, 3), 0),
    }
    for family, (training_draws, expected_successes) in cases.items():
        result = run_p22_training_proposal_probe(
            family=family, training_draws=training_draws,
            validation_draws=tuple(range(200)))
        assert result["status"] == "COMPLETED"
        assert result["training_goals_match"]
        assert len(set(result["training_world_ids"])) == 2
        assert len(result["validation_world_ids"]) == 200
        assert result["candidate_count"] > 0
        assert result["approval_count"] == 0
        assert result["world_receipt_count"] == 0
        assert result["resource_snapshot"]["resource_counts"][
            "improvement_proposals"] > 0
        assert result["resource_snapshot"]["cumulative_resources"][
            "training_task_exposures"] == 2
        assert all(row["status"] == "unapproved_candidate"
                   and row["proposal_count"] > 0
                   and row["panel"]["status"] == "nonactionable_validation_panel_scored"
                   and row["panel"]["world_count"] == 200
                   and row["panel"]["approval_created"] is False
                   and row["panel"]["world_receipts_created"] is False
                   for row in result["candidates"])
        assert sum(row["qualification_count"] > 0 for row in result["candidates"]) == 1
        assert sum(row["qualification_count"] == 0 for row in result["candidates"]) == 1
        qualified = next(row for row in result["candidates"]
                         if row["qualification_count"] > 0)
        assert len(qualified["qualifications"]) == 1
        qualification = qualified["qualifications"][0]
        assert qualification["status"] == "qualified_for_candidate_specific_approval"
        assert qualification["declared_trial_count"] == 2.0
        assert len(set(qualification["attempt_ids"])) == 2
        assert len(set(qualification["task_ids"])) == 2
        assert len(set(qualification["training_trial_keys"])) == 2
        assert all(row["panel"]["successes"] == expected_successes
                   for row in result["candidates"])
