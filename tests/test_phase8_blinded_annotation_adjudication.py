from __future__ import annotations

import pytest

from evaluation.phase8_blinded_annotation_adjudication import (
    ADJUDICATION_SCHEMA,
    audit_blinded_annotations,
    make_adjudication_template,
    make_rater_template,
)
from evaluation.phase8_blinded_annotation_packet import (
    BEHAVIOR_DIMENSIONS, PACKET_SCHEMA,
)


def _packet():
    return {
        "schema": PACKET_SCHEMA,
        "protocol_id": "test-protocol",
        "annotation_rows": [
            {"case_code": "case_001", "response_code": alias,
             "scores": {name: None for name in BEHAVIOR_DIMENSIONS},
             "evidence_notes": {name: "" for name in BEHAVIOR_DIMENSIONS}}
            for alias in ("A", "B")
        ],
    }


def _rated(packet, rater_id, *, special=None):
    form = make_rater_template(packet, rater_id)
    for row in form["annotation_rows"]:
        row_key = (row["case_code"], row["response_code"])
        row["scores"] = {name: 1.0 for name in BEHAVIOR_DIMENSIONS}
        row["evidence_notes"] = {name: "" for name in BEHAVIOR_DIMENSIONS}
        if special and row_key == special[0]:
            dimension, score, note = special[1:]
            row["scores"][dimension] = score
            row["evidence_notes"][dimension] = note
    return form


def test_unanimous_dual_ratings_report_agreement_without_scoring_systems():
    packet = _packet()
    a, b = _rated(packet, "rater-a"), _rated(packet, "rater-b")

    report = audit_blinded_annotations(packet, a, b)

    assert report["status"] == "consensus_complete"
    assert report["annotation_row_count"] == 2
    assert report["disputed_row_count"] == 0
    assert report["agreement"]["all_dimensions_exact_agreement"][
        "exact_agreement"] == 1.0
    assert report["score_interpretation_performed"] is False
    assert report["system_aliases_unblinded"] is False
    assert all(row["status"] == "unanimous"
               for row in report["consensus_rows"])


def test_disagreements_stay_unscored_until_independent_adjudication():
    packet = _packet()
    a = _rated(packet, "rater-a")
    b = _rated(packet, "rater-b", special=(
        ("case_001", "B"), "repair", 0.5, "Target is not actionable."))
    initial = audit_blinded_annotations(packet, a, b)

    assert initial["status"] == "awaiting_adjudication"
    assert initial["disputed_row_count"] == 1
    assert initial["unresolved_row_count"] == 1
    disputed = next(row for row in initial["consensus_rows"]
                    if row["status"] == "awaiting_adjudication")
    assert disputed["scores"] is None

    adjudication = make_adjudication_template(packet, initial, "adjudicator-c")
    assert adjudication["schema"] == ADJUDICATION_SCHEMA
    assert len(adjudication["rows"]) == 1
    adjudication["rows"][0]["final_scores"] = {
        name: 1.0 for name in BEHAVIOR_DIMENSIONS
    }
    adjudication["rows"][0]["final_evidence_notes"] = {
        name: "" for name in BEHAVIOR_DIMENSIONS
    }
    adjudication["rows"][0]["resolution_note"] = (
        "On blind review, the repair is supported by the event evidence.")

    final = audit_blinded_annotations(packet, a, b,
                                      adjudication=adjudication)
    assert final["status"] == "consensus_complete"
    assert final["unresolved_row_count"] == 0
    assert final["adjudicator_id"] == "adjudicator-c"
    assert disputed["case_code"] == final["consensus_rows"][1]["case_code"]
    assert final["consensus_rows"][1]["status"] == "adjudicated"


def test_packet_binding_and_required_notes_are_enforced():
    packet = _packet()
    a, b = _rated(packet, "rater-a"), _rated(packet, "rater-b")
    a["annotation_rows"][0]["scores"]["grounding"] = 0
    with pytest.raises(ValueError, match="note required"):
        audit_blinded_annotations(packet, a, b)

    a = _rated(packet, "rater-a")
    a["packet_sha256"] = "wrong packet"
    with pytest.raises(ValueError, match="packet digest mismatch"):
        audit_blinded_annotations(packet, a, b)


def test_raters_and_adjudicator_must_be_independent_and_boolean_is_not_a_score():
    packet = _packet()
    a = _rated(packet, "same-id")
    b = _rated(packet, "same-id")
    with pytest.raises(ValueError, match="distinct blinded IDs"):
        audit_blinded_annotations(packet, a, b)

    a, b = _rated(packet, "rater-a"), _rated(packet, "rater-b")
    a["annotation_rows"][0]["scores"]["action"] = True
    with pytest.raises(ValueError, match="invalid action score"):
        audit_blinded_annotations(packet, a, b)
