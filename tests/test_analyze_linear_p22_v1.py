from evaluation.process_mastery.analyze_linear_p22_v1 import (
    _self_check_payload, analyze, self_check,
)


def test_self_check_exercises_null_timeout_unsafe_and_comparator_disagreement():
    result = self_check()
    assert result["status"] == "PASS"
    assert {"null", "timeout", "unsafe", "comparator_disagreement"}.issubset(
        set(result["cases"]))
    assert "selection_split_integrity" in result["cases"]


def test_incomplete_development_rows_are_retained_and_not_imputed():
    payload = _self_check_payload()
    removed = payload["checkpoint_rows"].pop()
    result = analyze(payload)
    assert result["status"] == "DEVELOPMENT_ONLY"
    assert result["counts"]["rows"] == len(payload["checkpoint_rows"])
    assert result["counts"]["missing_rows"] == 1
    assert any("missing_rows:1" == failure for failure in result["failures"])
    assert result["paired_effects"]["status"] == "NOT_ESTABLISHED"
    assert removed["world_id"] in payload["allocation_plan"]["world_ids_by_family"][
        removed["family"]]


def test_heldout_without_preregistration_is_rejected():
    payload = _self_check_payload()
    payload.update(split="heldout", heldout_accessed=True,
                   status="heldout_pending_analysis")
    result = analyze(payload)
    assert result["status"] == "NOT_ESTABLISHED"
    assert "heldout_requires_preregistration" in result["failures"]
    assert result["evidence_class"] == "HELDOUT_INVALID"


def test_full_vs_unchanged_mcnemar_keeps_all_paired_worlds():
    payload = _self_check_payload()
    result = analyze(payload)
    for key, comparison in result["mcnemar"].items():
        assert comparison["paired_worlds"] == 2
        assert comparison["left_only"] == 0
        assert comparison["right_only"] == 0
        assert comparison["p_two_sided"] == 1.0


def test_development_is_not_reported_as_attested_and_split_overlap_fails():
    payload = _self_check_payload()
    clean = analyze(payload)
    assert clean["provenance_status"] == "DEVELOPMENT_ONLY"

    payload["allocation_plan"]["validation_world_ids_by_family"]["d4"][0] = "d4-w0"
    result = analyze(payload)
    assert result["status"] == "DEVELOPMENT_ONLY"
    assert "split_identity_overlap:d4" in result["failures"]


def test_selection_allocation_is_required_and_disjoint():
    payload = _self_check_payload()
    del payload["allocation_plan"]["selection_world_ids_by_family"]
    missing = analyze(payload)
    assert "training_selection_or_validation_allocation_invalid" in missing["failures"]

    payload = _self_check_payload()
    payload["allocation_plan"]["selection_world_ids_by_family"]["d4"][0] = "d4-w0"
    overlap = analyze(payload)
    assert "split_identity_overlap:d4" in overlap["failures"]

    payload = _self_check_payload()
    payload["allocation_plan"]["selection_world_ids_by_family"]["loopover"][0] = "d4-w0"
    cross_family_overlap = analyze(payload)
    assert "allocation_identity_reused_across_families_or_splits" in (
        cross_family_overlap["failures"])
