"""P20 social development panel exercises each source adapter and sink."""
from evaluation.process_mastery.social_sequence_development import (
    ARMS, run_development_panel,
)


def test_all_social_source_arms_run_through_native_verification_and_sink():
    result = run_development_panel(streams_per_arm=1)
    assert result["status"] == "development_only"
    assert result["arms"] == list(ARMS)
    assert len(result["records"]) == 4
    by_arm = {row["arm"]: row for row in result["records"]}
    for arm in ("observation", "demonstration", "instruction"):
        row = by_arm[arm]
        assert row["outcome"] == "verified_and_executed"
        assert row["verification_status"] == "VERIFIED"
        assert row["solved"] is True
        assert row["own_actions"] == 2
        assert row["budget_debits"] == 2
    assert by_arm["observation"]["source_evidence_types"] == ["ObservedInteractionTrace"]
    assert by_arm["demonstration"]["source_evidence_types"] == ["ProcessDemonstration"]
    assert by_arm["instruction"]["source_evidence_types"] == ["ParsedProcessInstruction"]
    assert by_arm["instruction"]["source_graph_nodes"] > 0
    assert by_arm["instruction"]["visible_observations"] == 2
    assert by_arm["instruction"]["source_world_actions"] == 0
    assert by_arm["instruction"]["target_primitive_actions"] == 2
    assert by_arm["instruction"]["native_rule_steps"] > 0
    assert by_arm["instruction"]["graph_bytes"] > 0
    reward = by_arm["reward_only"]
    assert reward["outcome"] == "abstained_underidentified"
    assert reward["verification_status"] == "not_applicable"
    assert reward["own_actions"] == 0
    assert reward["budget_debits"] == 1
