import json
import subprocess
import sys

import pytest

from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.rs050_contract import (
    RS050_CLAIM_BOUNDARY,
    contract_digest,
    validate_authenticated_rs050_evidence,
    validate_rs050_evidence,
)


def _identity():
    value = {
        "schema": "P5R0SupervisorIdentityV1",
        "supervisor_id": "fixture-only-supervisor",
        "authority_key_digest": digest("fixture-only-key"),
        "authentication_method": "external_signature",
        "identity_digest": "",
    }
    value["identity_digest"] = digest({key: value[key] for key in value if key != "identity_digest"})
    return value


def _evidence(count=2):
    run_id, lock_digest, closure_digest, profile = map(digest, ("run", "lock", "closure", "profile"))
    identity = _identity()
    invocations = []
    for sequence in range(1, count + 1):
        invocation = {
            "schema": "P5R0RS050InvocationV1",
            "run_id": run_id,
            "lock_digest": lock_digest,
            "closure_digest": closure_digest,
            "supervisor_digest": identity["identity_digest"],
            "task_id": digest(f"task-{sequence}"),
            "sequence": sequence,
            "worker_exit": 0,
            "timed_out": False,
            "oom": False,
            "process_group_killed": False,
            "cleanup_verified": True,
            "observed": True,
            "resource_profile_digest": profile,
            "resource_observation_digest": digest({"sequence": sequence, "status": "complete"}),
            "evidence_digest": "",
        }
        invocation["evidence_digest"] = digest({key: invocation[key] for key in invocation if key != "evidence_digest"})
        invocations.append(invocation)
    supervisor_evidence = {
        "schema": "P5R0SupervisorEvidenceV1",
        "run_id": run_id,
        "lock_digest": lock_digest,
        "closure_digest": closure_digest,
        "supervisor_digest": identity["identity_digest"],
        "worker_invocations": count,
        "worker_exit": 0,
        "observed": True,
        "timed_out": False,
        "oom": False,
        "process_group_killed": False,
        "cleanup_verified": True,
        "attestation_status": "verified_supervisor_observation",
        "evidence_digest": "",
    }
    supervisor_evidence["evidence_digest"] = digest({key: supervisor_evidence[key] for key in supervisor_evidence if key != "evidence_digest"})
    value = {
        "schema": "P5R0RS050EvidenceV1",
        "run_id": run_id,
        "lock_digest": lock_digest,
        "closure_digest": closure_digest,
        "resource_profile_digest": profile,
        "supervisor_identity": identity,
        "supervisor_evidence": supervisor_evidence,
        "worker_invocations": count,
        "invocations": invocations,
        "claim_boundary": RS050_CLAIM_BOUNDARY,
        "contract_digest": contract_digest(),
        "evidence_digest": "",
    }
    value["evidence_digest"] = digest({key: value[key] for key in value if key != "evidence_digest"})
    return value


class _TrustedFixtureSupervisor:
    trusted = True
    independent = True

    def validate_execution_evidence(self, evidence):
        return evidence["attestation_status"] == "verified_supervisor_observation"

    def validate_bounded_compute_claim(self, claim):
        return claim["schema"] == "P5R0RS050ResourceClaimV1"


def test_rs050_contract_is_closed_and_not_promotable_by_digest_alone():
    report = validate_rs050_evidence(_evidence())
    assert report["authenticated"] is False
    assert report["promotable"] is False
    assert report["worker_invocations"] == 2


def test_rs050_external_supervisor_seam_is_required_for_authentication():
    with pytest.raises(P5R0Error, match="trust boundary"):
        validate_authenticated_rs050_evidence(_evidence(), object())
    report = validate_authenticated_rs050_evidence(_evidence(), _TrustedFixtureSupervisor())
    assert report["authenticated"] is True
    assert report["promotable"] is True


@pytest.mark.parametrize("change", [
    ("sequence", 0),
    ("task_id", digest("duplicate")),
    ("timed_out", True),
    ("oom", True),
    ("cleanup_verified", False),
])
def test_rs050_lifecycle_and_binding_invariants_fail_closed(change):
    value = _evidence()
    key, replacement = change
    if key == "task_id":
        value["invocations"][1][key] = replacement
    else:
        value["invocations"][0][key] = replacement
    with pytest.raises(P5R0Error):
        validate_rs050_evidence(value)


def test_rs050_digest_tampering_and_cli_validation(tmp_path):
    value = _evidence()
    value["invocations"][0]["worker_exit"] = 1
    with pytest.raises(P5R0Error):
        validate_rs050_evidence(value)
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(_evidence()), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "evaluation.p5_r0.rs050_contract", "--evidence", str(path)],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report["promotable"] is False
    assert report["authenticated"] is False
