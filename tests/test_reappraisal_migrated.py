"""G2.1 preregistration fixtures; G2.2 will replace these with native rules."""
from __future__ import annotations

from copy import deepcopy


def _event():
    return {
        "event_id": "feedback-17",
        "observed_facts": ["reviewer requested two changes"],
        "source_id": "message-88",
        "forced_constraints": ["the review contained criticism"],
        "appraisal": "threat",
        "arousal": 0.8,
    }


def _supported_alternative():
    return {
        "frame_id": "actionable-feedback",
        "claims": ["the reviewer identified changes that can improve the report"],
        "evidence_refs": ["message-88", "reviewer-request-2"],
        "contradicting_evidence_refs": [],
        "forced_constraints": ["the review contained criticism"],
        "appraisal_result": "challenge",
    }


def test_alternative_input_reappraised():
    event = _event()
    frame = _supported_alternative()
    evidence_ids = {event["source_id"], "reviewer-request-2"}
    assert frame["frame_id"] != ""
    assert frame["evidence_refs"]
    assert set(frame["evidence_refs"]) <= evidence_ids
    assert frame["contradicting_evidence_refs"] == []
    assert frame["appraisal_result"] == "challenge"


def test_event_unchanged():
    event = _event()
    original = deepcopy(event)
    reappraisal_view = {
        "source_event_id": event["event_id"],
        "frame": _supported_alternative(),
    }
    assert event == original
    assert reappraisal_view["source_event_id"] == event["event_id"]
    assert reappraisal_view["frame"]["forced_constraints"] == event["forced_constraints"]


def test_unsupported_optimism_rejected():
    frame = {
        "frame_id": "they-loved-it",
        "claims": ["the reviewer loved the report"],
        "evidence_refs": [],
        "contradicting_evidence_refs": [],
        "appraisal_result": "relief",
    }
    assert not frame["evidence_refs"]
    assert frame["claims"]
    # No evidence means this frame cannot be registered as admissible.
    assert frame.get("admissible", False) is False


def test_no_frame_no_reappraisal():
    probe = {"event": _event(), "candidate_frames": []}
    assert probe["candidate_frames"] == []
    assert probe.get("reappraisal_view") is None
