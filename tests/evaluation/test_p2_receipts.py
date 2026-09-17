from __future__ import annotations

import json

import pytest

from evaluation.p0a.canonical import canonical_bytes, object_hash, sign
from evaluation.p2.protocol import P2ProtocolError
from evaluation.p2.receipts import ReceiptFailureLog, ReceiptLog
from p2_fixtures import PRIVATE


def digest(char: str) -> str:
    return "sha256:" + char * 64


def terminal():
    return {"lock_status": "verified", "lock_digest": digest("1"), "input_digest": digest("2"),
            "proposal_digest": digest("3"), "reconstruction_digest": digest("4"),
            "worker_image_digest": digest("5"), "evaluator_binary_digest": digest("6"),
            "outcome": {"classification": "protocol_error", "brokered": False},
            "scoring_vector": {"brier_milli": 0}}


def hostile_bypass_evidence():
    native_routes = ("agent_write", "callback", "evaluator_path", "host_protocol", "id_only_route",
                     "input_write", "network", "shell", "undeclared_binary")
    return {"schema": "P2HostileBypassEvidenceV2", "status": "contained",
            "native_attempts": {route: {"attempted": True, "result": "blocked"} for route in native_routes},
            "python_attempts": {route: {"attempted": True,
                                          "result": "executed_no_effect" if route == "python_execution" else "blocked"}
                                for route in (*native_routes, "python_execution")},
            "evaluator_mounts": {"agent": {"before": digest("a"), "after": digest("a")},
                                 "input": {"before": digest("b"), "after": digest("b")}}}


def terminal_with_hostile_bypass_evidence():
    receipt = terminal()
    evidence = hostile_bypass_evidence()
    receipt["hostile_bypass_evidence"] = evidence
    receipt["outcome"].update({"hostile_bypass_evidence_hash": object_hash(evidence),
                               "hostile_bypass_status": "contained"})
    return receipt


def unverified_terminal():
    receipt = terminal()
    receipt.update({"lock_status": "unverified", "lock_digest": None, "input_digest": None,
                    "worker_image_digest": None, "evaluator_binary_digest": None,
                    "submitted_input_evidence_hash": digest("7")})
    return receipt


def test_receipt_chain_is_exclusive_and_survives_verified_restart(tmp_path):
    first = ReceiptLog(tmp_path, PRIVATE).append(terminal())
    second = ReceiptLog(tmp_path, PRIVATE).append(terminal())
    restarted = ReceiptLog(tmp_path, PRIVATE)
    assert second["previous_receipt_hash"] == first["receipt_hash"]
    assert restarted.sequence == 2 and restarted.previous == second["receipt_hash"]


def test_receipt_reload_verifies_full_canonical_hostile_bypass_evidence(tmp_path):
    entry = ReceiptLog(tmp_path, PRIVATE).append(terminal_with_hostile_bypass_evidence())
    restarted = ReceiptLog(tmp_path, PRIVATE)
    assert restarted.sequence == 1 and restarted.previous == entry["receipt_hash"]
    assert entry["hostile_bypass_evidence"]["native_attempts"]["network"] == {"attempted": True, "result": "blocked"}
    assert entry["hostile_bypass_evidence"]["python_attempts"]["python_execution"] == {"attempted": True, "result": "executed_no_effect"}
    assert entry["hostile_bypass_evidence"]["evaluator_mounts"]["agent"]["before"] == entry["hostile_bypass_evidence"]["evaluator_mounts"]["agent"]["after"]


def test_receipt_reload_rejects_tampered_hostile_bypass_evidence(tmp_path):
    ReceiptLog(tmp_path, PRIVATE).append(terminal_with_hostile_bypass_evidence())
    target = tmp_path / "000001.json"
    body = json.loads(target.read_text())
    body["hostile_bypass_evidence"]["native_attempts"]["network"]["result"] = "succeeded"
    target.chmod(0o600)
    target.write_bytes(canonical_bytes(body))
    target.chmod(0o400)
    with pytest.raises(P2ProtocolError, match="hostile bypass route result"):
        ReceiptLog(tmp_path, PRIVATE)


def test_legacy_verified_receipt_reloads_and_preserves_append_safety(tmp_path):
    current = ReceiptLog(tmp_path, PRIVATE).append(terminal())
    legacy = {key: value for key, value in current.items()
              if key not in {"lock_status", "receipt_hash", "signature"}}
    legacy["receipt_hash"] = object_hash(legacy)
    legacy["signature"] = sign(legacy, PRIVATE, "receipt_hash")
    target = tmp_path / "000001.json"
    target.chmod(0o600)
    target.write_bytes(canonical_bytes(legacy))
    target.chmod(0o400)

    restarted = ReceiptLog(tmp_path, PRIVATE)
    appended = restarted.append(terminal())

    assert restarted.sequence == 2
    assert appended["previous_receipt_hash"] == legacy["receipt_hash"]


def test_unverified_receipt_chain_preserves_null_authority_and_submission_evidence(tmp_path):
    entry = ReceiptLog(tmp_path, PRIVATE).append(unverified_terminal())
    restarted = ReceiptLog(tmp_path, PRIVATE)
    assert entry["lock_status"] == "unverified"
    assert entry["input_digest"] is None
    assert entry["submitted_input_evidence_hash"] == digest("7")
    assert restarted.sequence == 1 and restarted.previous == entry["receipt_hash"]


def test_receipt_restart_rejects_tampering_and_terminal_placeholders(tmp_path):
    with pytest.raises(P2ProtocolError, match="terminal receipt"):
        ReceiptLog(tmp_path, PRIVATE).append({})
    ReceiptLog(tmp_path, PRIVATE).append(terminal())
    target = tmp_path / "000001.json"
    target.chmod(0o600)
    target.write_text("{}")
    with pytest.raises(P2ProtocolError):
        ReceiptLog(tmp_path, PRIVATE)


def test_failure_receipt_reload_preserves_unverified_chain_and_rejects_tampering(tmp_path):
    first = ReceiptFailureLog(tmp_path, PRIVATE).append(
        unverified_terminal(), attempted_classification="protocol_error", failure_code="OSError")
    restarted = ReceiptFailureLog(tmp_path, PRIVATE)
    second = restarted.append(
        terminal(), attempted_classification="protocol_error", failure_code="OSError")

    assert restarted.sequence == 2
    assert second["previous_failure_hash"] == first["failure_hash"]
    assert first["lock_status"] == "unverified"
    assert first["input_digest"] is None

    target = tmp_path / "000002.json"
    tampered = json.loads(target.read_text())
    tampered["failure_code"] = "tampered"
    target.chmod(0o600)
    target.write_bytes(canonical_bytes(tampered))
    target.chmod(0o400)
    with pytest.raises(P2ProtocolError):
        ReceiptFailureLog(tmp_path, PRIVATE)


def test_receipt_append_retries_short_writes_before_exposing_a_seal(tmp_path, monkeypatch):
    import evaluation.p2.receipts as receipt_module
    original_write = receipt_module.os.write
    calls = 0

    def short_once(fd, payload):
        nonlocal calls
        calls += 1
        if calls == 1 and len(payload) > 1:
            return original_write(fd, payload[:len(payload) // 2])
        return original_write(fd, payload)

    monkeypatch.setattr(receipt_module.os, "write", short_once)
    entry = ReceiptLog(tmp_path, PRIVATE).append(terminal())
    restarted = ReceiptLog(tmp_path, PRIVATE)
    assert restarted.sequence == 1 and restarted.previous == entry["receipt_hash"]
