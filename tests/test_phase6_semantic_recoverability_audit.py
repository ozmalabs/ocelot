import json

from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase6_semantic_recoverability_audit import audit_semantic_recoverability


def test_semantic_audit_uses_runtime_fields_and_excludes_surface_text():
    report = {
        "protocol_id": "test",
        "observations": [{
            "id": "case-a", "observed_state": "error",
            "observed_force": "assertion_or_correction",
            "grounding_status": "unresolved", "reply": "ERROR: no communicative response could be generated.",
            "grounding_evidence_path": "", "production_gate_receipts": [],
        }],
    }
    result = audit_semantic_recoverability(report, {"events": [{
        "id": "case-a", "expected_state": "defer", "communicative_force": "assertion",
        "grounding_status": "grounded",
    }]})
    assert result["status"] == "measured"
    assert result["dimension_counts"] == {"grounding_recall": 1, "state": 1}
    assert result["surface_text_used_as_evidence"] is False
    assert "reply" not in json.dumps(result)


def test_semantic_audit_compares_fine_grained_force_at_neutral_runtime_boundary():
    result = audit_semantic_recoverability(
        {"protocol_id": "test", "observations": [
            {"id": "offer", "observed_state": "act",
             "observed_force": "social_action", "grounding_status": "grounded"},
            {"id": "refusal", "observed_state": "error",
             "observed_force": "repair_or_defer", "grounding_status": "grounded"},
            {"id": "correction", "observed_state": "defer",
             "observed_force": "assertion_or_correction", "grounding_status": "grounded"},
        ]},
        {"events": [
            {"id": "offer", "expected_state": "act", "communicative_force": "offer",
             "grounding_status": "grounded"},
            {"id": "refusal", "expected_state": "error", "communicative_force": "refusal",
             "grounding_status": "grounded"},
            {"id": "correction", "expected_state": "defer", "communicative_force": "correction",
             "grounding_status": "grounded"},
        ]},
    )
    assert result["mismatch_count"] == 0


def test_current_phase2j_report_audit_is_complete_and_fail_closed():
    report = json.loads(open("evaluation/reports/phase8_corpus_report_20260923_phase2j.json").read())
    result = audit_semantic_recoverability(report, load_corpus())
    assert result["status"] == "measured"
    assert result["event_count"] == 74
    assert result["observed_event_count"] == 74
    assert result["surface_text_used_as_evidence"] is False
    assert result["mismatch_count"] > 0
