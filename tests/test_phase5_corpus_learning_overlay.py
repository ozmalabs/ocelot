"""Phase 5O: explicit corpus learning overlay and native recurrence readback."""
from __future__ import annotations

from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase5_corpus_learning_overlay import (
    OVERLAY, PROTOCOL_ID, overlay_corpus, run_overlay,
)
from evaluation.phase5_corpus_runner import learning_observation_contract


def test_overlay_is_explicit_and_does_not_mutate_base_corpus():
    base = load_corpus()
    overlay = overlay_corpus(base)
    assert overlay["protocol_id"] == PROTOCOL_ID
    assert len(OVERLAY) == 6
    assert len(overlay["events"]) == len(OVERLAY)
    assert all("learning_observation" in event for event in overlay["events"])
    assert all("learning_observation" not in event for event in base["events"])


def test_learning_contract_reads_nested_explicit_overlay_metadata():
    evidence = learning_observation_contract(overlay_corpus())
    assert evidence["status"] == "measured"
    assert evidence["observation_count"] == len(OVERLAY)
    assert evidence["evidence_source"] == "explicit_event_learning_observation"
    assert evidence["event_ids"] == [item["event_id"] for item in OVERLAY]


def test_overlay_reuses_live_ingress_and_native_recurrence_authority():
    report = run_overlay()
    assert report["overlay_protocol_id"] == PROTOCOL_ID
    assert report["base_corpus_unchanged"] is True
    assert report["learning_observation_evidence"]["status"] == "measured"
    assert report["production_recurrence"]["claim_permitted"] is True
    assert report["recurrence"]["measured_recurrence_identity_count"] == 3
    overlay_identities = [
        item for item in report["recurrence"]["identities"]
        if "opaque-corpus-" in item["gap_identity"]
    ]
    assert len(overlay_identities) == 3
    assert all(item["recurrence"]["recurrence_count"] == 2.0
               for item in overlay_identities)
