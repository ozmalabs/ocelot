"""Phase 6: receipt mismatch causes remain observable, not auto-selected."""
from __future__ import annotations

from evaluation.phase6_receipt_mismatch_audit import audit_receipt_mismatches


def _event(case_id: str, force: str = "request_action"):
    return {"id": case_id, "communicative_force": force,
            "expected_state": "act", "cognitive_goal": "act",
            "grounding_status": "grounded", "signal": case_id,
            "literal_form": "imperative"}


def _receipt(event: str, *, mode: str = "native", intent: str = "act"):
    return {"status": "released", "attrs": {
        "status": "released", "recoverable": True,
        "semantic_content": ["agent", "object"],
        "semantic_event": event, "semantic_intent": intent,
        "parse_back_mode": mode, "turn_message_id": 11,
    }}


def test_audit_distinguishes_duplicate_and_competing_releases():
    corpus = {"events": [
        _event("duplicate"), _event("competing"),
        _event("force", force="assertion"),
    ]}
    report = {"observations": [
        {"id": "duplicate", "production_gate_receipts": [
            _receipt("open"), _receipt("open")]},
        {"id": "competing", "production_gate_receipts": [
            _receipt("open"), _receipt("answer_topic", mode="conversation")]},
        {"id": "force", "production_gate_receipts": [
            _receipt("open", intent="act")]},
    ]}
    result = audit_receipt_mismatches(report, corpus)
    by_id = {item["id"]: item for item in result["mismatches"]}
    assert by_id["duplicate"]["cause"] == "duplicate_semantic_release"
    assert by_id["competing"]["cause"] == "competing_semantic_releases"
    assert by_id["force"]["cause"] == "semantic_field_mismatch"
    assert all(item["receipt_selection_performed"] is False
               for item in result["mismatches"])
    assert result["surface_text_used_as_evidence"] is False
