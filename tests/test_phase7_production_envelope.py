"""Focused tests for the bounded Phase 7 production-shaped envelope."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from evaluation.phase7_production_envelope import (  # noqa: E402
    PROFILE_EVENT_IDS,
    SCHEMA,
    measure_production_envelope,
)


@pytest.fixture(scope="module")
def report():
    return measure_production_envelope()


def test_production_envelope_has_structural_graph_and_resource_evidence(report):
    assert report["schema"] == SCHEMA
    assert report["event_count"] == len(PROFILE_EVENT_IDS)
    assert len(report["observations"]) == len(PROFILE_EVENT_IDS)
    assert report["errors"] == []
    assert report["graph_growth"]["nodes"] > 0
    assert report["graph_growth"]["discourse_events"] == len(PROFILE_EVENT_IDS)
    # This is an observation gate, not a disguised pass condition.  The
    # current cold communication workload records the bound explicitly; the
    # Phase 7 exit remains yellow while the measured value is false.
    assert report["resource_assertions"]["rss_measured"] is True
    assert isinstance(report["resource_assertions"]["rss_growth_bounded"], bool)
    assert report["resource_assertions"]["steady_state_rss_growth_bounded"] is True
    assert report["cold_start_rss_growth_bytes"] > report[
        "steady_state_rss_growth_bytes"]
    assert report["surface_text_used_as_semantics"] is False
    assert report["turn_boundary_required"] is False


def test_production_envelope_preserves_typed_non_turn_and_overlap_evidence(report):
    rows = {row["id"]: row for row in report["observations"]}
    overlap = rows["overlap_signal"]
    assert overlap["interaction_mode"] == "non_turn"
    assert overlap["interaction_relation"] == "overlap"
    assert overlap["literal_form"] == "fragment"
    assert overlap["event_payload_relation"] == "overlap"
    assert overlap["event_payload_literal_form"] == "fragment"
    assert overlap["cognitive_disposition"] == "defer"


def test_production_envelope_replay_is_structurally_deterministic(report):
    assert report["replay_equal"] is True
    assert report["replay_difference"] is None


def test_production_envelope_exposes_boot_and_event_cost_without_semantic_use(report):
    assert report["boot_elapsed_ms"] >= 0.0
    assert len(report["rss_samples"]) == len(PROFILE_EVENT_IDS)
    assert all(sample["elapsed_ms"] >= 0.0
               and sample["rss_delta_bytes"] >= 0
               for sample in report["rss_samples"])
    assert all("graph_delta" in sample for sample in report["rss_samples"])
    assert report["surface_text_used_as_semantics"] is False
