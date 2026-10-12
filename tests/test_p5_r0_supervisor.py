from __future__ import annotations

import pytest

from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.supervisor import validate_supervisor_evidence


def _evidence(status="verified_supervisor_observation"):
    value = {
        "schema": "P5R0SupervisorEvidenceV1",
        "run_id": digest("run"),
        "lock_digest": digest("lock"),
        "closure_digest": digest("closure"),
        "supervisor_digest": digest("supervisor"),
        "worker_invocations": 1,
        "worker_exit": 0,
        "observed": True,
        "timed_out": False,
        "oom": False,
        "process_group_killed": True,
        "cleanup_verified": True,
        "attestation_status": status,
        "evidence_digest": "",
    }
    value["evidence_digest"] = digest({key: value[key] for key in value if key != "evidence_digest"})
    return value


def test_supervisor_observation_is_closed_and_bound():
    value = _evidence()
    assert validate_supervisor_evidence(value, run_id=value["run_id"], lock_digest=value["lock_digest"], closure_digest=value["closure_digest"]) == value


def test_supervisor_observation_tampering_and_attestation_claim_fail_closed():
    value = _evidence()
    value["worker_exit"] = 1
    with pytest.raises(P5R0Error):
        validate_supervisor_evidence(value)
    value = _evidence("verified_confidential_space")
    with pytest.raises(P5R0Error):
        validate_supervisor_evidence(value)
