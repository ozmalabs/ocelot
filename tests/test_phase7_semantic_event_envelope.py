"""Focused Phase 7K tests for the neutral semantic-event envelope."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from evaluation.phase7_semantic_event_envelope import (  # noqa: E402
    SCHEMA,
    SEQUENCE,
    measure_with_replay,
)


@pytest.fixture(scope="module")
def report():
    return measure_with_replay()


def test_phase7k_schema_and_resource_observations(report):
    assert report["schema"] == SCHEMA
    assert report["sequence_length"] == 3
    assert report["graph_growth"]["nodes"] > 0
    assert report["graph_growth"]["edges"] > 0
    assert report["latency_ms"] >= 0.0
    assert report["resource_assertions"]["rss_measured"]
    assert report["resource_assertions"]["rss_growth_bounded"]
    assert len(SEQUENCE) == 3


def test_phase7k_cognitive_readback_and_fail_closed_malformed_case(report):
    rows = {row["id"]: row for row in report["rows"]}
    assert rows["challenged_proposition"]["supported"] is True
    assert rows["accepted_typed_consequence"]["supported"] is True
    assert rows["accepted_typed_consequence"]["consequence_supported"] is True
    assert rows["malformed_evidence"]["supported"] is False
    assert rows["malformed_evidence"]["proposition_count_delta"] == 0
    assert rows["malformed_evidence"]["evidence_count_delta"] == 0
    assert report["malformed_proposition_failed_closed"] is True

    propositions = {row["evidence_id"]: row for row in report["readback"]["propositions"]}
    assert propositions["phase7k-challenged"]["commitment_status"] == "challenged"
    accepted = propositions["phase7k-accepted-drop"]
    assert accepted["commitment_status"] == "accepted"
    assert accepted["uptake_applied"] == "accept"
    assert accepted["consequences"] == [{
        "source": "accepted_common_ground_projection",
        "predicate": "drop",
        "originated_in": True,
    }]


def test_phase7k_is_non_turn_and_keeps_authority_boundaries(report):
    assert report["no_message_created"] is True
    assert report["no_turn_created"] is True
    assert report["no_reply_created"] is True
    assert report["python_materialization"]["surface_parser_invoked"] is False
    assert report["python_materialization"]["reply_selection"] is False
    authority = report["native_authority"]
    assert authority["lifecycle_status_read_from_graph"] is True
    assert authority["lifecycle_seed"] == "proposition_commitment_lifecycle"
    assert any(name.startswith("pcl_")
               for name in authority["native_rule_names_loaded"])
    assert report["readback"]["common_ground"]
    assert {row["scope_key"] for row in report["readback"]["common_ground"]} == {"shared"}


def test_phase7k_fresh_graph_replay_is_deterministic(report):
    assert report["replay_equal"] is True
    assert report["replay_difference"] is None
