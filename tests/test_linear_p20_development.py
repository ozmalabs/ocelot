"""The P20 runner joins working development arms and keeps holdout sealed."""
import pytest
import copy

from evaluation.process_mastery.analyze_linear_p20_v1 import analyze
from evaluation.process_mastery.linear_p20_v1 import run


def test_development_runner_includes_target_social_and_structural_panels():
    result = run("development", target_streams_per_pair=1,
                 social_streams_per_arm=1, social_controls_per_kind=1)
    assert result["status"] == "development_only"
    assert result["heldout_accessed"] is False
    assert result["target_learning"]["domain_pairs"] == [
        "heat_to_thermal", "lever_to_latch"]
    assert {row["arm"] for row in result["target_learning"]["records"]} == {
        "fresh", "mapped_source", "mismatched_source"}
    assert {row["arm"] for row in result["social_acquisition"]["records"]} == {
        "observation", "demonstration", "instruction", "reward_only"}
    assert len(result["structural_controls"]) == 4
    assert result["structural_status"] == "PASS"


def test_heldout_panel_is_closed_before_standalone_freeze():
    with pytest.raises(RuntimeError, match="standalone preregistration freeze"):
        run("heldout")


def test_development_analyzer_rejects_missing_arm_and_false_control():
    payload = run("development", target_streams_per_pair=1,
                  social_streams_per_arm=1, social_controls_per_kind=1)
    result = analyze(payload)
    assert result["status"] == "PASS"
    assert result["primary_status"] == "NOT_ESTIMATED"
    changed = copy.deepcopy(payload)
    changed["social_acquisition"]["records"].pop()
    changed["structural_controls"][0]["false_candidate_count"] = 1
    rejected = analyze(changed)
    assert rejected["status"] == "FAIL"
    assert any("social_allocation_mismatch" in item for item in rejected["failures"])
    assert any("control_failure" in item for item in rejected["failures"])
