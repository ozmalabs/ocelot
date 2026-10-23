"""The P20 runner joins working development arms and keeps holdout sealed."""
import pytest
import copy

from evaluation.process_mastery.analyze_linear_p20_v1 import analyze
from evaluation.process_mastery.linear_p20_v1 import allocation, run


def _synthetic_attested_payload(payload):
    """Give analyzer unit tests a positive-control provenance fixture.

    This changes only an in-memory test payload. It does not attest the loaded
    runtime or create evaluation evidence.
    """
    runtime = payload["provenance"]["runtime_attestation"]
    provenance = payload["provenance"]
    runtime.update({"status": "ATTESTED", "native_symbols_bound": True,
        "build_sources_match": True,
        "wrapper_sha256": provenance["wrapper_sha256"],
        "loaded_extension_sha256": provenance["loaded_extension_sha256"],
        "build_receipt_sha256": provenance["build_receipt_sha256"],
        "issues": []})
    return payload


def test_development_runner_includes_target_social_and_structural_panels():
    result = run("development", target_streams_per_pair=1,
                 social_streams_per_arm=1, social_controls_per_kind=1)
    assert result["status"] == "development_only"
    assert result["heldout_accessed"] is False
    attestation_status = result["provenance"]["runtime_attestation"]["status"]
    assert attestation_status in {"ATTESTED", "DEVELOPMENT_ONLY"}
    if attestation_status != "ATTESTED":
        rejected = analyze(result)
        assert rejected["status"] == "FAIL"
        assert "runtime_provenance_unattested" in rejected["failures"]
    assert result["allocation_sha256"]
    assert result["allocation_plan"]["primary"]["minimum_gain"] == 0.20
    assert result["target_learning"]["domain_pairs"] == [
        "heat_to_thermal", "lever_to_latch"]
    assert {row["arm"] for row in result["target_learning"]["records"]} == {
        "fresh", "mapped_source", "mismatched_source"}
    assert {row["arm"] for row in result["social_acquisition"]["records"]} == {
        "observation", "demonstration", "instruction", "reward_only"}
    assert len(result["explanation_rebuild"]["records"]) == 2
    assert all(row["fidelity_match"] and row["counterexample_rejected"]
               and not row["receiver_source_leakage"]
               for row in result["explanation_rebuild"]["records"])
    assert len(result["structural_controls"]) == 4
    assert result["structural_status"] == "PASS"


def test_heldout_panel_is_closed_before_standalone_freeze():
    with pytest.raises(RuntimeError, match="requires --preregistration"):
        run("heldout")


def test_heldout_allocation_is_fixed_and_disjoint_from_development():
    dev = allocation("development", target_streams_per_pair=8,
                     social_streams_per_arm=8, social_controls_per_kind=25,
                     explanation_streams=8)
    heldout = allocation("heldout")
    assert len(heldout["target"]) == 400
    assert len(heldout["social"]) == 800
    assert len(heldout["controls"]) == 100
    assert len(heldout["explanations"]) == 200
    assert not ({row["stream_id"] for row in dev["target"]}
                & {row["stream_id"] for row in heldout["target"]})
    assert not ({row["stream_id"] for row in dev["social"]}
                & {row["stream_id"] for row in heldout["social"]})
    assert not ({row["control_id"] for row in dev["controls"]}
                & {row["control_id"] for row in heldout["controls"]})
    assert not (set(dev["explanations"]) & set(heldout["explanations"]))


def test_development_analyzer_rejects_missing_arm_and_false_control():
    payload = _synthetic_attested_payload(run("development",
        target_streams_per_pair=1, social_streams_per_arm=1,
        social_controls_per_kind=1))
    result = analyze(payload)
    assert result["status"] == "PASS"
    assert result["primary_status"] == "NOT_ESTIMATED"
    changed = copy.deepcopy(payload)
    changed["social_acquisition"]["records"].pop()
    changed["structural_controls"][0]["false_candidate_count"] = 1
    changed["explanation_rebuild"]["records"][0]["fidelity_match"] = False
    changed["provenance"]["runtime_attestation"]["status"] = "MISMATCH"
    rejected = analyze(changed)
    assert rejected["status"] == "FAIL"
    assert any("social_allocation_mismatch" in item for item in rejected["failures"])
    assert any("control_failure" in item for item in rejected["failures"])
    assert any("explanation_failure" in item for item in rejected["failures"])
    assert "runtime_provenance_unattested" in rejected["failures"]
