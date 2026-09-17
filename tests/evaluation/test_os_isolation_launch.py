"""Fail-closed P0 launcher seams; real containment probes live behind deployment gate."""
from __future__ import annotations

import pytest

from evaluation.p0a.canonical import ProtocolError, object_hash
from evaluation.p0a.entrypoint import evaluation_mode
from evaluation.p0a.manifest import ManifestVerifier
from evaluation.p0a.receipt_log import ReceiptLog
from evaluation.p0a.run_paths import RunPaths
from conftest import (DIGESTS, EXPORT_AUTHORITY_KEYS, NOW, PRIVATE, PUBLIC, manifest,
                      native_graph_export, native_graph_export_attestation)


def test_missing_sandbox_is_receipted_and_never_starts_a_worker(tmp_path):
    body = manifest()
    control = tmp_path / "control"
    paths = RunPaths.for_verified_run(control, run_id=body["run_id"], verified_manifest_hash=object_hash(body))
    log = ReceiptLog(paths.receipts_root, manifest_hash=object_hash(body), broker_image_digest=DIGESTS["broker_image_digest"],
                     input_digest=DIGESTS["input_snapshot_digest"], signer=PRIVATE, writer_public_key=PUBLIC,
                     now_ms=lambda: NOW, run_paths=paths)
    export = native_graph_export(run_id=body["run_id"])
    with pytest.raises(ProtocolError, match="sandbox isolation"):
        with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW),
                             manifest=body, expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC},
                             receipt_log=log, native_graph_export=export,
                             native_graph_export_attestation=native_graph_export_attestation(export, run_id=body["run_id"]),
                             native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW,
                             control_root=control):
            pytest.fail("isolation failure must not expose a run")
    assert log.last_receipt["reason_code"] == "sandbox_policy_unavailable"
    assert log.last_receipt["outcome"] == "impasse"
