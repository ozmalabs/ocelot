from evaluation.proposition_commitment_measurement import measure_cases


def test_proposition_overlay_measures_commitment_without_changing_corpus():
    report = measure_cases()
    assert report["schema"] == "proposition_commitment_measurement.v1"
    assert report["case_count"] == 4
    assert report["commitment_status_accuracy"] == 1.0
    assert report["consequence_projection_accuracy"] == 1.0
    assert report["supported_consequence_count"] == 1
    assert report["provenance_complete_count"] == 4
    negated = next(row for row in report["rows"] if row["id"] == "negated_drop_fail_closed")
    assert negated["commitment_status"] == "accepted"
    assert negated["consequence_supported"] is False
