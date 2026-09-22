from pathlib import Path
from evaluation.p5_r0.preregister import preregister
from evaluation.p5_r0.protocol import digest
from evaluation.p5_r0.runner import _host_evidence, run_readiness_gate

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



def test_self_digested_supervisor_evidence_stays_unattested_without_adapter():
    run_id = digest("run")
    value = {
        "schema": "P5R0SupervisorEvidenceV1", "run_id": run_id,
        "lock_digest": digest("lock"), "closure_digest": digest("closure"),
        "supervisor_digest": digest("supervisor"), "worker_invocations": 1,
        "worker_exit": 0, "observed": True, "timed_out": False, "oom": False,
        "process_group_killed": True, "cleanup_verified": True,
        "attestation_status": "verified_supervisor_observation", "evidence_digest": "",
    }
    value["evidence_digest"] = digest({key: value[key] for key in value if key != "evidence_digest"})
    evidence = _host_evidence(
        closure={"closure_digest": value["closure_digest"], "files": {}},
        run_id=run_id, lock_digest=value["lock_digest"], native_invocations=1,
        supervisor_evidence=value,
    )
    assert evidence["host_execution_evidence"]["observed"] is False
    assert evidence["host_execution_evidence"]["evidence_status"] == "unavailable_unattested_local"
