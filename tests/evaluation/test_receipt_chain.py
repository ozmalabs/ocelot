import json

import pytest
from evaluation.p0a.canonical import ProtocolError, canonical_bytes, object_hash
from evaluation.p0a.receipt_log import ReceiptLog
from conftest import DIGESTS, PRIVATE, PUBLIC, broker, grant, raw, request


def reopen(tmp_path, target):
    return ReceiptLog(tmp_path, manifest_hash=target.manifest.manifest_hash,
        broker_image_digest=DIGESTS["broker_image_digest"], input_digest=DIGESTS["input_snapshot_digest"],
        signer=PRIVATE, writer_public_key=PUBLIC, now_ms=lambda: 1000)


def test_receipt_tamper_deletion_fork_or_head_change_blocks_restart(tmp_path):
    target = broker(tmp_path); req = request(target.manifest.run_id)
    assert target.submit_action(raw(req), raw(grant(req))).phase == "accepted"
    path = tmp_path / "receipts.ndjson"; path.write_text(path.read_text().replace("accepted", "denied"))
    with pytest.raises(ProtocolError): reopen(tmp_path, target)


def test_recomputed_receipt_hash_and_head_still_require_writer_signature(tmp_path):
    target = broker(tmp_path); req = request(target.manifest.run_id)
    assert target.submit_action(raw(req), raw(grant(req))).phase == "accepted"
    path = tmp_path / "receipts.ndjson"
    receipt = json.loads(path.read_text())
    receipt["outcome"] = "denied"
    receipt["receipt_hash"] = object_hash(receipt, "receipt_hash", "writer_signature")
    path.write_bytes(canonical_bytes(receipt) + b"\n")
    (tmp_path / "head.json").write_bytes(canonical_bytes({"sequence": 1, "head": receipt["receipt_hash"]}))
    with pytest.raises(ProtocolError): reopen(tmp_path, target)


def test_receipt_head_mismatch_and_missing_writer_impasse_without_effect(tmp_path):
    target = broker(tmp_path); req = request(target.manifest.run_id)
    (tmp_path / "head.json").write_text('{"head":"sha256:fork","sequence":1}')
    with pytest.raises(ProtocolError): reopen(tmp_path, target)
    target.receipt_log = None
    assert target.submit_action(raw(req), raw(grant(req))).phase == "impasse"
    assert target.state["counter"] == 0
