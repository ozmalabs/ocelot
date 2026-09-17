"""Pre-launch failures remain signed and never recreate fork/Pipe fallbacks."""
from __future__ import annotations

import pytest

from evaluation.p0a.canonical import ProtocolError, object_hash, sign
from evaluation.p0a.entrypoint import evaluation_mode
from evaluation.p0a.launch_failure import LaunchFailureRecord
from evaluation.p0a.manifest import ManifestVerifier
from evaluation.p0a.receipt_log import ReceiptLog
from evaluation.p0a.sandbox import StagedEntrypoint
from conftest import (DIGESTS, NOW, PRIVATE, PUBLIC, EXPORT_AUTHORITY_KEYS, fake_sandbox, manifest,
                      native_graph_export, native_graph_export_attestation, staged_receipt_log)


def test_malformed_manifest_is_signed_before_any_staged_worker(tmp_path):
    body = manifest(); body.pop("signature")
    log = ReceiptLog(tmp_path / "receipts", manifest_hash=object_hash(manifest()), broker_image_digest=DIGESTS["broker_image_digest"],
                     input_digest=DIGESTS["input_snapshot_digest"], signer=PRIVATE, writer_public_key=PUBLIC, now_ms=lambda: NOW)
    record = LaunchFailureRecord(tmp_path / "authority", signer=PRIVATE, signer_public_key=PUBLIC,
                                 signer_key_id="receipt-log-writer", now_ms=lambda: NOW)
    with pytest.raises(ProtocolError, match="manifest rejected"):
        with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), manifest=body,
                             expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC}, receipt_log=log,
                             native_graph_export=b"unreached", launch_failure_record=record, now_ms=lambda: NOW):
            pytest.fail("rejected manifest yielded")
    assert record.read()["reason_code"] == "manifest_malformed"


def test_missing_sandbox_is_receipted_not_replaced_with_local_execution(tmp_path):
    body = manifest(); log, control = staged_receipt_log(tmp_path, body)
    export = native_graph_export(run_id=body["run_id"])
    with pytest.raises(ProtocolError, match="sandbox isolation"):
        with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), manifest=body,
                             expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC}, receipt_log=log,
                             native_graph_export=export, native_graph_export_attestation=native_graph_export_attestation(export, run_id=body["run_id"]),
                             native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW, control_root=control):
            pytest.fail("missing sandbox yielded")
    assert log.last_receipt["reason_code"] == "sandbox_policy_unavailable"


def test_invalid_staged_entrypoint_fails_before_fake_worker_start(tmp_path):
    body = manifest(); log, control = staged_receipt_log(tmp_path, body)
    launcher = fake_sandbox(tmp_path); launcher.spec = launcher.spec.__class__(
        launcher.spec.runtime_root, launcher.spec.agent_root, launcher.spec.input_root, launcher.spec.command,
        launcher.spec.work_root, launcher.spec.seccomp_policy,
        StagedEntrypoint("ambient value", "run", "sha256:" + "a" * 64))
    export = native_graph_export(run_id=body["run_id"])
    with pytest.raises(ProtocolError, match="sandbox isolation policy"):
        with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), manifest=body,
                             expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC}, receipt_log=log,
                             native_graph_export=export, native_graph_export_attestation=native_graph_export_attestation(export, run_id=body["run_id"]),
                             native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW,
                             agent_spec=launcher.spec, sandbox_launcher=launcher, control_root=control):
            pytest.fail("invalid staged entrypoint yielded")
    assert launcher.process is None and log.last_receipt["reason_code"] == "sandbox_policy_unavailable"
