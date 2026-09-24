"""Focused Phase 2T overlay tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from evaluation.proposition_event_commitment_measurement import (
    FIXTURE,
    PHASE0,
    load_cases,
    measure_cases,
)


def test_overlay_is_keyed_by_existing_phase0_ids_without_editing_corpus():
    before = PHASE0.read_bytes()
    payload = load_cases()
    phase0_ids = {event["id"] for event in json.loads(before)["events"]}
    overlay_ids = {
        step["event_id"]
        for case in payload["cases"]
        for step in case["steps"]
    }
    assert overlay_ids <= phase0_ids
    assert PHASE0.read_bytes() == before


def test_phase2t_reads_all_required_stages_and_fails_closed():
    report = measure_cases()
    assert report["schema"] == "proposition_event_commitment_measurement.v1"
    assert report["case_count"] == 7
    assert report["event_identity_count"] == 9
    assert report["proposition_materialization_accuracy"] == 1.0
    assert report["commitment_status_accuracy"] == 1.0
    assert report["consequence_projection_accuracy"] == 1.0
    assert report["proposition_provenance_complete_count"] == 5
    assert report["consequence_provenance_complete_count"] == 1
    assert report["fail_closed_negative_count"] == 4
    assert report["reply_evidence_used"] is False
    assert report["external_truth_claim"] is False

    rows = {row["id"]: row for row in report["rows"]}
    assert rows["accepted_supported"]["proposition"]["uptake_applied"] == "accept"
    assert rows["accepted_supported"]["consequence_provenance"] is True
    assert rows["accepted_then_retracted"]["commitment_status"] == "retracted"
    assert rows["accepted_then_retracted"]["consequence_supported"] is False
    assert rows["conflicting_evidence_id"]["steps"][1]["bridge_supported"] is False
    assert rows["conflicting_evidence_id"]["steps"][1]["proposition_count_delta"] == 0


def test_fixture_is_standalone_and_has_no_surface_reply_evidence():
    assert FIXTURE.exists()
    payload = load_cases()
    serialized = json.dumps(payload)
    assert "reply" not in serialized
    surface_negative = next(
        case for case in payload["cases"] if case["category"] == "unsupported")
    assert "text" in surface_negative["steps"][0]["proposition"]
    assert all(
        "text" not in step.get("proposition", {})
        for case in payload["cases"]
        if case["category"] != "unsupported"
        for step in case["steps"]
        if "proposition" in step
    )
