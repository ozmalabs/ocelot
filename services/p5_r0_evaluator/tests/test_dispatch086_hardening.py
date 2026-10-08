import dataclasses
import dataclasses
import json
import os
from pathlib import Path

import pytest

from services.p5_r0_evaluator.canonical import canonical_bytes, digest
from services.p5_r0_evaluator.deploy import iam_predecessor
from services.p5_r0_evaluator.deploy import reviewed_iam_backend as boundary
from services.p5_r0_evaluator.deploy.reviewed_iam_backend import (
    ReviewedIAMError,
    SubprocessGcloudRunner,
    _issue_verified_signature_verifier,
    build_signed_credential_transport_artifact,
    issue_verifier_credential_transport,
    load_signed_credential_transport_artifact,
    verify_transport_bytes,
)

# Import the existing offline ledger/credential fixtures without duplicating
# protected packet or prestate artifacts.
from services.p5_r0_evaluator.tests.test_dispatch085_hardening import _ledger
from services.p5_r0_evaluator.tests.test_reviewed_iam_backend import _prerequisites


BYTES = b"fresh-verifier-owned-token"


def test_actual_fd_bytes_are_verified_before_runner(monkeypatch, tmp_path: Path):
    prerequisites = _prerequisites()
    token_path = tmp_path / "token"
    token_path.write_bytes(BYTES)
    fd = os.open(token_path, os.O_RDONLY)
    transport = issue_verifier_credential_transport(
        evidence_digest=prerequisites["credential"].evidence_digest,
        target_service_account=prerequisites["credential"].target_service_account,
        expires_at=prerequisites["credential"].expires_at,
        token_fd=fd,
        packet_digest=prerequisites["credential"].packet_digest,
    )
    credential = dataclasses.replace(prerequisites["credential"], transport=transport)
    # Same descriptor identity, changed contents: metadata/signature alone must
    # not permit the effectful call.
    os.lseek(fd, 0, os.SEEK_SET)
    tamper_fd = os.open(token_path, os.O_WRONLY)
    try:
        os.write(tamper_fd, b"tampered-verifier-token")
    finally:
        os.close(tamper_fd)
    monkeypatch.setattr("services.p5_r0_evaluator.deploy.reviewed_iam_backend.subprocess.run", lambda *_a, **_k: pytest.fail("gcloud must not run"))
    try:
        with pytest.raises(ReviewedIAMError, match="bytes do not match|descriptor"):
            SubprocessGcloudRunner().run(boundary.allowlisted_argv("project_describe"), credential=credential)
    finally:
        os.close(fd)


def test_fd_eof_and_oversize_are_rejected_at_issuance(tmp_path: Path):
    empty = os.open(tmp_path / "empty", os.O_CREAT | os.O_RDONLY, 0o600)
    try:
        with pytest.raises(ReviewedIAMError, match="EOF"):
            issue_verifier_credential_transport(evidence_digest="sha256:" + "e" * 64, target_service_account="x@example.com", expires_at=2_000_000_000, token_fd=empty)
    finally:
        os.close(empty)
    oversized_path = tmp_path / "oversized"
    oversized_path.write_bytes(b"x" * (64 * 1024 + 1))
    oversized = os.open(oversized_path, os.O_RDONLY)
    try:
        with pytest.raises(ReviewedIAMError, match="oversized"):
            issue_verifier_credential_transport(evidence_digest="sha256:" + "e" * 64, target_service_account="x@example.com", expires_at=2_000_000_000, token_fd=oversized)
    finally:
        os.close(oversized)


def test_transport_artifact_reissues_fresh_fd_without_persisting_bytes(tmp_path: Path):
    token_path = tmp_path / "token"
    token_path.write_bytes(BYTES)
    old_fd = os.open(token_path, os.O_RDONLY)
    transport = issue_verifier_credential_transport(evidence_digest="sha256:" + "e" * 64, target_service_account="x@example.com", expires_at=2_000_000_000, token_fd=old_fd, packet_digest="sha256:" + "b" * 64)
    artifact = build_signed_credential_transport_artifact(transport)
    assert BYTES.decode() not in json.dumps(artifact)
    artifact_path = tmp_path / "transport.json"
    artifact_path.write_bytes(canonical_bytes(artifact))
    new_fds: list[int] = []

    def source(public):
        fresh = os.open(token_path, os.O_RDONLY)
        new_fds.append(fresh)
        return fresh

    try:
        fresh = load_signed_credential_transport_artifact(artifact_path, trusted_public_key=transport.verifier_public_key, signed_environment_source=source)
        assert fresh.token_fd != transport.token_fd
        assert fresh.packet_digest == transport.packet_digest
        assert fresh.expires_at == transport.expires_at
        assert verify_transport_bytes(fresh, BYTES)
    finally:
        os.close(old_fd)
        for fd in new_fds:
            os.close(fd)


def _signed_ledger(path: Path):
    _ledger(path)
    verifier = _issue_verified_signature_verifier()
    records = [json.loads(line) for line in path.read_text().splitlines()]
    root = iam_predecessor.issue_signed_iam_ledger_root(
        records=[records[0], records[1], records[2], {}],
        signer=boundary._sign_ledger_root_payload,
        public_key=verifier.public_key,
    )
    records[3]["ledger_root"] = root
    records[3]["event_digest"] = digest({key: value for key, value in records[3].items() if key != "event_digest"})
    path.write_bytes(b"".join(canonical_bytes(item) + b"\n" for item in records))
    return verifier


def test_signed_ledger_root_binds_consumer_expectations(tmp_path: Path):
    ledger = tmp_path / "signed.jsonl"
    verifier = _signed_ledger(ledger)
    predecessor = iam_predecessor.load_verified_iam_predecessor(
        ledger_path=ledger,
        operation_id="provision_gcs_only_iam_boundary",
        attempt_id="dispatch082-iam-20260920-a7f4c2d9",
        packet_digest="sha256:" + "b" * 64,
        prestate_digest="sha256:" + "d" * 64,
        evidence_digest="sha256:" + "e" * 64,
        trusted_verifier=iam_predecessor.VerifiedIAMLedgerRootVerifier(public_key=verifier.public_key),
    )
    assert predecessor.status == "verified"
    with pytest.raises(iam_predecessor.IAMPredecessorError, match="packet binding"):
        iam_predecessor.load_verified_iam_predecessor(
            ledger_path=ledger,
            operation_id="provision_gcs_only_iam_boundary",
            attempt_id="dispatch082-iam-20260920-a7f4c2d9",
            packet_digest="sha256:" + "c" * 64,
            prestate_digest="sha256:" + "d" * 64,
            evidence_digest="sha256:" + "e" * 64,
            trusted_verifier=iam_predecessor.VerifiedIAMLedgerRootVerifier(public_key=verifier.public_key),
        )


def test_recomputed_self_hashed_ledger_without_trusted_root_is_rejected(tmp_path: Path):
    ledger = tmp_path / "unsigned.jsonl"
    _ledger(ledger)
    with pytest.raises(iam_predecessor.IAMPredecessorError, match="trusted IAM ledger root|verifier"):
        iam_predecessor.load_verified_iam_predecessor(
            ledger_path=ledger,
            operation_id="provision_gcs_only_iam_boundary",
            attempt_id="dispatch082-iam-20260920-a7f4c2d9",
            packet_digest="sha256:" + "b" * 64,
            prestate_digest="sha256:" + "d" * 64,
            evidence_digest="sha256:" + "e" * 64,
        )



def test_transport_rehydration_rejects_reuse_of_registered_stale_fd(tmp_path: Path):
    token_path = tmp_path / "token"
    token_path.write_bytes(BYTES)
    old_fd = os.open(token_path, os.O_RDONLY)
    transport = issue_verifier_credential_transport(evidence_digest="sha256:" + "e" * 64, target_service_account="x@example.com", expires_at=2_000_000_000, token_fd=old_fd)
    artifact_path = tmp_path / "transport.json"
    artifact_path.write_bytes(canonical_bytes(build_signed_credential_transport_artifact(transport)))
    try:
        with pytest.raises(ReviewedIAMError, match="stale transport fd"):
            load_signed_credential_transport_artifact(
                artifact_path,
                trusted_public_key=transport.verifier_public_key,
                signed_environment_source=lambda _public: old_fd,
            )
    finally:
        os.close(old_fd)
