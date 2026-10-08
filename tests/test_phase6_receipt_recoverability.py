from __future__ import annotations

from evaluation.phase6_receipt_recoverability import (
    EXPLICIT_OR_WITHHELD,
    MISSING,
    RECEIPT_BACKED,
    RELEASED_MISMATCH,
    classify_event,
    measure_receipt_recoverability,
)


def _event(case_id: str, force: str = "request_action", state: str = "act") -> dict:
    return {
        "id": case_id,
        "signal": case_id,
        "event_mode": "non_turn",
        "literal_form": "imperative",
        "communicative_force": force,
        "cognitive_goal": state,
        "grounding_status": "grounded",
        "interaction_relation": "standalone",
        "evidence": ["graph_path"],
        "expected_state": state,
    }


def _receipt(*, status: str = "released", intent: str = "act", event: str = "open",
             recoverable: bool = True) -> dict:
    return {
        "type": "ProductionGateReceipt",
        "status": status,
        "attrs": {
            "status": status,
            "recoverable": recoverable,
            "semantic_content": ["agent", "object"],
            "semantic_event": event,
            "semantic_intent": intent,
            "parse_back_mode": "native_graph",
        },
    }


def _report(observations: list[dict]) -> dict:
    return {"schema": "injected.phase8", "protocol_id": "test-protocol",
            "observations": observations}


def _corpus(events: list[dict]) -> dict:
    return {"schema": "communication_event_corpus.v1", "events": events}


def test_classifies_all_outcomes_and_reports_dimension_counts() -> None:
    events = [
        _event("good"),
        _event("error"),
        _event("withheld"),
        _event("mismatch"),
        _event("missing"),
    ]
    report = _report([
        {"id": "good", "production_gate_receipts": [_receipt()]},
        {"id": "error", "reply": "ERROR: no communicative response could be generated."},
        {"id": "withheld", "production_gate_receipts": [_receipt(status="withheld")]},
        {"id": "mismatch", "production_gate_receipts": [_receipt(intent="coordinate_socially")]},
        {"id": "missing", "trace_coverage": {"parse_evidence": True},
         "reply": "a plausible sentence"},
    ])

    result = measure_receipt_recoverability(report, _corpus(events))

    assert result["status"] == "measured"
    assert result["classification_counts"] == {
        RECEIPT_BACKED: 1,
        EXPLICIT_OR_WITHHELD: 2,
        RELEASED_MISMATCH: 1,
        MISSING: 1,
    }
    assert result["dimension_counts"] == {"force": 1}
    assert result["runtime_state_mismatch_count"] == 0
    assert result["reply_text_used_as_semantic_evidence"] is False
    assert result["trace_flags_used_as_semantic_evidence"] is False


def test_reply_and_trace_flags_cannot_make_a_missing_receipt_recoverable() -> None:
    event = _event("missing")
    result = measure_receipt_recoverability(
        _report([{
            "id": "missing",
            "reply": "a plausible sentence",
            "trace_coverage": {"parse_evidence": True, "reply_provenance": True},
        }]),
        _corpus([event]),
    )

    assert result["results"][0]["classification"] == MISSING
    assert result["classification_counts"][MISSING] == 1


def test_released_receipt_requires_authoritative_semantic_fields() -> None:
    event = _event("malformed")
    receipt = _receipt()
    del receipt["attrs"]["semantic_content"]
    result = measure_receipt_recoverability(
        _report([{"id": "malformed", "production_gate_receipts": [receipt]}]),
        _corpus([event]),
    )

    assert result["results"][0]["classification"] == RELEASED_MISMATCH
    assert result["dimension_counts"] == {"semantic_content": 1}


def test_explicit_error_is_an_outcome_not_semantic_evidence() -> None:
    event = _event("error")
    result = measure_receipt_recoverability(
        _report([{
            "id": "error",
            "explicit_error": "ERROR: no communicative response could be generated.",
            "reply": "not used",
            "production_gate_receipts": [_receipt(status="withheld")],
        }]),
        _corpus([event]),
    )

    row = result["results"][0]
    assert row["classification"] == EXPLICIT_OR_WITHHELD
    assert row["semantic_evidence"] is None


def test_semantic_intent_is_not_cognitive_state() -> None:
    event = _event("deferred", state="defer")
    receipt = _receipt(intent="act")
    result = measure_receipt_recoverability(
        _report([{
            "id": "deferred",
            "observed_state": "defer",
            "production_gate_receipts": [receipt],
        }]),
        _corpus([event]),
    )
    assert result["classification_counts"][RECEIPT_BACKED] == 1


def test_runtime_state_diagnostic_preserves_its_evidence_contract() -> None:
    event = _event("state")
    result = measure_receipt_recoverability(
        _report([{
            "id": "state",
            "cognitive_state": "defer",
            "cognitive_state_evidence_source": "graph_resident_goal_lifecycle",
            "cognitive_state_authority": "graph_readback",
            "cognitive_state_evidence_available": True,
            "release_state": "released",
            "production_gate_receipts": [_receipt()],
        }]),
        _corpus([event]),
    )
    diagnostic = result["runtime_state_diagnostics"][0]
    assert diagnostic["source"] == "graph_resident_goal_lifecycle"
    assert diagnostic["authority"] == "graph_readback"
    assert diagnostic["evidence_available"] is True
    assert diagnostic["release_state"] == "released"
    assert diagnostic["not_receipt_semantic_evidence"] is True
    assert result["dimension_counts"] == {}


def test_typed_response_intents_are_compatible_with_their_input_force() -> None:
    # These pairs are observed in ProductionGateReceipt fields.  They include
    # response acts (clarification, acknowledgement, refusal/defer, and gap
    # reporting), not merely a repetition of the input's speech-act label.
    compatible = [
        ("assertion", "acknowledge_receipt_without_endorsement"),
        ("acknowledgement", "acknowledge_receipt_without_endorsement"),
        ("assertion", "request"),
        ("correction", "update_common_ground"),
        ("correction", "request"),
        ("request_information", "act"),
        ("request_action", "inform"),
        ("request_action", "defer"),
        ("offer", "coordinate_socially"),
        ("offer", "request"),
        ("offer", "acknowledge_receipt_without_endorsement"),
        ("social_action", "request"),
    ]
    for force, intent in compatible:
        result = classify_event(
            _event(f"{force}-{intent}", force=force),
            {"production_gate_receipts": [_receipt(intent=intent)]},
        )
        assert result["classification"] == RECEIPT_BACKED, (force, intent, result)


def test_unrelated_social_response_does_not_match_an_action_request() -> None:
    result = classify_event(
        _event("wrong-response", force="request_action"),
        {"production_gate_receipts": [_receipt(intent="coordinate_socially")]},
    )
    assert result["classification"] == RELEASED_MISMATCH
    assert result["dimensions"] == ["force"]
