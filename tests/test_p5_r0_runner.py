from pathlib import Path
from evaluation.p5_r0.preregister import preregister
from evaluation.p5_r0.runner import run_readiness_gate

def test_missing_native_closure_fails_closed_and_rolls_back(tmp_path):
    bundle = preregister(tmp_path / "lock.json")["bundle"]
    result = run_readiness_gate(bundle, receipts_root=tmp_path / "receipts", require_native=True)
    assert result["disposition"] == "impasse"
    assert result["outcome"] == "local_readiness_only/no_go"
    assert result["rollback"]["exact"] is True

def test_finite_local_harness_reports_raw_records_without_composite(tmp_path):
    bundle = preregister(tmp_path / "lock.json")["bundle"]
    result = run_readiness_gate(bundle, receipts_root=tmp_path / "receipts", require_native=False)
    assert len(result["records"]) == 144
    assert result["score_report"]["has_composite_capability_score"] is False
    assert "general intelligence" in result["claim_boundary"].lower()
