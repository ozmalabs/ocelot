from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from services.p5_r0_evaluator.canonical import canonical_bytes, digest
from services.p5_r0_evaluator.deploy import iam_predecessor
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import CUSTOM_ROLE, EXACT_CONDITION
from services.p5_r0_evaluator.deploy.reviewed_iam_backend import (
    build_signed_iam_child_approval_artifact,
    _issue_verified_iam_child_approval,
    _issue_verified_signature_verifier,
    _sign_ledger_root_payload,
    issue_verifier_credential_transport,
    load_verified_iam_child_approval,
    verify_transport_bytes,
)


OPERATION = "provision_gcs_only_iam_boundary"
ATTEMPT = "dispatch082-iam-20260920-a7f4c2d9"
EVIDENCE = "sha256:" + "e" * 64
PACKET = "sha256:" + "b" * 64
PRESTATE = "sha256:" + "d" * 64
POSTSTATE = "sha256:" + "a" * 64


def _receipt() -> dict:
    value = {
        "schema": "P5R0APPROVAL023IAMReceiptV1",
        "operation_id": OPERATION,
        "project_id": "ocelot-proof",
        "bucket": "p5-evaluator-ocelot-proof-141633828616",
        "service_account": "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com",
        "custom_role": CUSTOM_ROLE,
        "custom_role_permissions": ["storage.objects.create", "storage.objects.get"],
        "wif_principal": "principalSet://iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/attribute.repository/ocelot",
        "condition_title": "p5_r0_r18r13_op4_exact_run",
        "condition_expression": EXACT_CONDITION,
        "private": True,
        "prestate_digest": PRESTATE,
        "poststate_digest": POSTSTATE,
        "prestate_versions": {},
        "poststate_versions": {},
        "later_operations_enabled": False,
        "credentials_exported": False,
        "keys_created": False,
    }
    return {**value, "receipt_digest": digest(value)}


def _ledger(path: Path) -> None:
    receipt = _receipt()
    common = {
        "schema": "P5R0APPROVAL023DISPATCH082IAMLedgerEventV1",
        "operation_id": OPERATION,
        "dispatch_id": "P5-MASTER-001/DISPATCH-082",
        "approval_id": "P5-MASTER-001/APPROVAL-023",
        "attempt_id": ATTEMPT,
        "packet_digest": PACKET,
        "prestate_digest": PRESTATE,
        "credential_evidence_digest": EVIDENCE,
        "child_approval_digest": "sha256:" + "c" * 64,
        "later_operations_enabled": False,
        "cloud_operations": ["iam.service_account_create"],
        "credentials_exported": False,
        "keys_created": False,
    }
    records: list[dict] = []
    for body in (
        {**common, "kind": "run_started", "mutations_performed": False},
        {**common, "kind": "prestate_verified", "prestate_digest": PRESTATE, "mutations_performed": False},
        {**common, "kind": "poststate_verified", "poststate_digest": POSTSTATE, "receipt": receipt, "mutations_performed": True},
    ):
        body["previous_event_digest"] = records[-1]["event_digest"] if records else None
        body["event_digest"] = digest(body)
        records.append(body)
    terminal = {**common, "kind": "run_stopped", "status": "verified", "verified_event_digest": records[-1]["event_digest"], "rollback_status": "not_required_verified", "receipt": receipt, "mutations_performed": True}
    terminal["previous_event_digest"] = records[-1]["event_digest"]
    terminal["event_digest"] = digest(terminal)
    records.append(terminal)
    verifier = _issue_verified_signature_verifier()
    records[-1]["ledger_root"] = iam_predecessor.issue_signed_iam_ledger_root(records=[records[0], records[1], records[2], {}], signer=_sign_ledger_root_payload, public_key=verifier.public_key)
    records[-1]["event_digest"] = digest({key: value for key, value in records[-1].items() if key != "event_digest"})
    path.write_bytes(b"".join(canonical_bytes(item) + b"\n" for item in records))
    return verifier


def test_transport_signature_binds_exact_bytes_without_retaining_them():
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"signed-token-envelope")
    try:
        transport = issue_verifier_credential_transport(
            evidence_digest=EVIDENCE,
            target_service_account="p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com",
            expires_at=2_000_000_000,
            token_fd=read_fd,
            transport_bytes=b"signed-token-envelope",
        )
        assert verify_transport_bytes(transport, b"signed-token-envelope") is True
        assert verify_transport_bytes(transport, b"tampered-token-envelope") is False
        assert not hasattr(transport, "transport_bytes")
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_persisted_iam_ledger_reloads_and_binds_terminal_receipt(tmp_path: Path):
    ledger = tmp_path / "iam.jsonl"
    verifier = _ledger(ledger)
    predecessor = iam_predecessor.load_verified_iam_predecessor(
        ledger_path=ledger, operation_id=OPERATION, attempt_id=ATTEMPT,
        evidence_digest=EVIDENCE, packet_digest=PACKET, prestate_digest=PRESTATE,
        trusted_verifier=iam_predecessor.VerifiedIAMLedgerRootVerifier(public_key=verifier.public_key),
    )
    assert predecessor.ledger_head_digest.startswith("sha256:")
    assert predecessor.receipt_digest == _receipt()["receipt_digest"]
    iam_predecessor.validate_verified_iam_predecessor(
        predecessor, operation_id=OPERATION, attempt_id=ATTEMPT,
        evidence_digest=EVIDENCE, packet_digest=PACKET, ledger_path=ledger,
        trusted_verifier=iam_predecessor.VerifiedIAMLedgerRootVerifier(public_key=verifier.public_key),
    )


def test_persisted_iam_ledger_rejects_tampered_chain_and_receipt(tmp_path: Path):
    ledger = tmp_path / "iam.jsonl"
    _ledger(ledger)
    lines = [json.loads(line) for line in ledger.read_text().splitlines()]
    lines[-1]["receipt"]["condition_expression"] = "resource.name == 'attacker'"
    ledger.write_bytes(b"".join(canonical_bytes(item) + b"\n" for item in lines))
    with pytest.raises(iam_predecessor.IAMPredecessorError):
        iam_predecessor.load_verified_iam_predecessor(
            ledger_path=ledger, operation_id=OPERATION, attempt_id=ATTEMPT,
            evidence_digest=EVIDENCE, packet_digest=PACKET, prestate_digest=PRESTATE,
        )


def test_failed_closed_or_manual_review_terminal_never_becomes_predecessor(tmp_path: Path):
    ledger = tmp_path / "iam.jsonl"
    _ledger(ledger)
    lines = [json.loads(line) for line in ledger.read_text().splitlines()]
    lines[-1]["status"] = "failed_closed"
    lines[-1]["event_digest"] = digest({key: value for key, value in lines[-1].items() if key != "event_digest"})
    ledger.write_bytes(b"".join(canonical_bytes(item) + b"\n" for item in lines))
    with pytest.raises(iam_predecessor.IAMPredecessorError):
        iam_predecessor.load_verified_iam_predecessor(
            ledger_path=ledger, operation_id=OPERATION, attempt_id=ATTEMPT,
            evidence_digest=EVIDENCE, packet_digest=PACKET, prestate_digest=PRESTATE,
        )



def test_signed_child_approval_can_be_reloaded_without_copying_a_mapping(tmp_path: Path):
    verifier = _issue_verified_signature_verifier()
    approval = _issue_verified_iam_child_approval(
        packet_digest=PACKET,
        attempt_id=ATTEMPT,
        prestate_digest=PRESTATE,
        credential_evidence_digest=EVIDENCE,
        authority_binding_digest="sha256:" + "b" * 64,
        issued_at=1_000,
        expires_at=2_000,
    )
    artifact = build_signed_iam_child_approval_artifact(approval, public_key=verifier.public_key)
    path = tmp_path / "approval.json"
    path.write_bytes(canonical_bytes(artifact))
    loaded = load_verified_iam_child_approval(path, trusted_public_key=verifier.public_key)
    assert loaded.as_public_dict() == approval.as_public_dict()
    artifact["approval"]["attempt_id"] = "forged-attempt"
    path.write_bytes(canonical_bytes(artifact))
    with pytest.raises(Exception):
        load_verified_iam_child_approval(path, trusted_public_key=verifier.public_key)
