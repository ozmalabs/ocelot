from pathlib import Path

from evaluation.p5_r0.preregister import preregister
from evaluation.p5_r0.protocol import is_digest
from evaluation.p5_r0.runner import run_readiness_gate
from evaluation.p5_r0.scoring import evaluate_gate
from evaluation.p5_r0.split import contrast_matrix


def test_local_run_emits_locked_pair_receipts_and_never_native_go(tmp_path):
    artifact = preregister(tmp_path / "lock.json")
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", require_native=False)
    assert result["record_count"] == 144
    assert result["control_count"] == 11
    assert len(result["contrast_evidence"]) == 90
    assert result["receipts"] == 144 + 11 + (90 * 2) + 2
    assert result["disposition"] == "local_readiness_only/no_go"
    assert "native_closure" in result["gate_reasons"]
    assert "mechanics_distinctness" in result["gate_reasons"]
    assert all(is_digest(row["receipt_hash"]) for row in result["records"])
    assert all(is_digest(row["receipt_hash"]) for row in result["controls"])
    assert all(is_digest(row["left_receipt_hash"]) and is_digest(row["right_receipt_hash"]) for row in result["contrast_evidence"])


def test_gate_rejects_synthetic_summary_flags_without_verified_chain():
    policy = {
        "expected_primary_records": 1,
        "expected_cases": 1,
        "required_control_ids": ["control"],
        "contrast_matrix": [],
        "native_controls_required": False,
        "external_authority_required": False,
        "mechanics_contrast_required": False,
        "session_state_required": False,
    }
    result = evaluate_gate({
        "run_id": "sha256:" + "0" * 64,
        "records": [{"case_id": "case", "case_digest": "sha256:" + "1" * 64, "domain_token": "domain", "split": "held_out", "arm": "cold_reset", "ordinal": 0, "outcome": "complete_correct", "receipt_hash": "sha256:" + "2" * 64}],
        "case_index": [{"case_id": "case", "case_digest": "sha256:" + "1" * 64, "domain_token": "domain", "split": "held_out"}],
        "controls": [{"control_id": "control", "receipt_hash": "sha256:" + "3" * 64}],
        "native_verified": True,
        "native_controls_verified": True,
        "mechanics_contrasts_verified": True,
        "chain_verified": True,
        "controls_passed": True,
        "held_out_complete": True,
        "rollback_exact": True,
        "score_report": {},
    }, policy)
    assert result["disposition"] == "local_readiness_only/no_go"
    assert "receipt_evidence" in result["reasons"]
    assert "receipt_chain" in result["reasons"]


def test_contrast_matrix_is_explicit_and_one_factor_locked():
    matrix = contrast_matrix()
    assert [row["pair_id"] for row in matrix] == ["T01_T02_memory", "T02_T03_causal", "T04_D01_memory", "D02_H01_action_effect", "H01_H02_memory"]
    assert all(row["relation"] in {"invariant", "non_invariant"} for row in matrix)
    assert all(row["arms"] == ["cold_reset", "frozen_transfer", "warm_adaptive"] for row in matrix)
