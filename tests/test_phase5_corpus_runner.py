from __future__ import annotations

from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase5_corpus_runner import (
    PROTOCOL_ID,
    learning_observation_contract,
    production_recurrence_diagnostic,
    run_phase5_recurrence_measurement,
)


def test_fixed_74_event_corpus_has_no_phase5_learning_observation_contract():
    corpus = load_corpus()
    evidence = learning_observation_contract(corpus)

    assert len(corpus["events"]) == 74
    assert evidence["status"] == "unavailable"
    assert evidence["observation_count"] == 0
    assert set(evidence["required_fields"]) == {
        "gap_identity", "learning_stage", "verification_status",
    }


def test_measurement_does_not_promote_a_single_runtime_gap_to_recurrence():
    corpus = load_corpus()
    event = next(item for item in corpus["events"] if item["id"] == "question_unknown")
    report = run_phase5_recurrence_measurement({"events": [event]})

    assert report["protocol_id"] == PROTOCOL_ID
    assert report["corpus"]["event_count"] == 1
    assert report["recurrence"]["status"] == "unavailable"
    assert report["recurrence"]["measured_recurrence_identity_count"] == 0
    assert report["production_recurrence"]["status"] == "unavailable"
    assert report["production_recurrence"]["claim_permitted"] is False
    assert "two observed SelfConcern" in report["recurrence"]["reason"]


def test_native_recurrence_without_learning_observations_is_insufficient_evidence():
    diagnostic = production_recurrence_diagnostic(
        {"status": "unavailable"},
        {
            "status": "measured",
            "reason": "native recurrence was observed",
        },
    )

    assert diagnostic["status"] == "unavailable"
    assert diagnostic["claim_permitted"] is False
    assert diagnostic["missing_evidence"] == ["learning_observation_contract"]
    assert "learning observations" in diagnostic["reason"]


def test_report_keeps_native_identity_and_event_provenance_separate():
    corpus = load_corpus()
    event = next(item for item in corpus["events"] if item["id"] == "question_unknown")
    report = run_phase5_recurrence_measurement({"events": [event]})

    for observation in report["gap_observations"]:
        assert observation["event_id"] == "question_unknown"
        assert observation["gap_identity"]
        assert observation["gap_identity"] != observation["event_id"]
        assert observation["self_concern_node_id"] is not None
        assert observation["self_concern_node_ids"]
    for identity in report["recurrence"]["identities"]:
        assert identity["identity_source"] == "SelfConcern.attrs.gap_identity"
        assert identity["event_ids"] == ["question_unknown"]
        assert identity["observation_count"] == 1
