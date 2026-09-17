from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from evaluation.p0a.canonical import canonical_bytes, object_hash
from evaluation.p2.lock import ARTIFACT_NAMES
from evaluation.p2.receipts import ReceiptFailureLog, ReceiptLog
from evaluation.p2.podman import PodmanSpec
from evaluation.p2.protocol import P2ProtocolError
from evaluation.p2.runner import P2Runner
from p2_fixtures import LOCK_PUBLIC, PRIVATE, PUBLIC, release_lock, signed
from test_p2_protocol import envelope


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, source: str, executable=False) -> Path:
    path.write_text(source)
    path.chmod(0o700 if executable else 0o400)
    return path


def _runner(tmp_path: Path, *, lock=None, envelope_key=PUBLIC, trusted_lock_keys=None) -> P2Runner:
    stage = tmp_path / "stage"
    agent, inputs, work, metadata = stage / "agent", stage / "input", stage / "work", stage / "metadata"
    for directory in (agent, inputs, work, metadata):
        directory.mkdir(parents=True)
    worker = _write(agent / "worker", "#!/bin/sh\nexit 0\n", executable=True)
    seccomp = _write(stage / "seccomp.json", "{}")
    sealed = _write(inputs / "sealed-input.json", canonical_bytes(envelope()).decode("utf-8"))
    input_digest = _digest(sealed)
    evaluator_reply = json.dumps({"accepted": False, "classification": "worker_mismatch",
        "metrics": {"brier_milli": 1000, "ece_milli": 0, "feasibility_milli": 1000,
        "minimality_milli": 1000, "safety_milli": 1000, "abstention_milli": 0},
        "verified_input_digest": input_digest, "reconstruction_digest": "sha256:" + "e" * 64})
    evaluator = _write(stage / "evaluator", f"#!/bin/sh\ncat >/dev/null\nprintf '%s' '{evaluator_reply}'\n", executable=True)
    worker_reply = json.dumps({"verified_input_digest": input_digest})
    probe_reply = json.dumps({"schema": "P2NativeRuntimeProbeReplyV1", "status": "ready", "abi": "p2-native-v1"})
    bypass_reply = json.dumps({"schema": "P2BypassProbeReportV1", "status": "contained", "attempts": {name: "blocked" for name in ("agent_write", "callback", "evaluator_path", "host_protocol", "id_only_route", "input_write", "network", "shell", "undeclared_binary")}})
    python_bypass_reply = json.dumps({"schema": "P2PythonBypassProbeReportV1", "status": "contained", "attempts": {**{name: "blocked" for name in ("agent_write", "callback", "evaluator_path", "host_protocol", "id_only_route", "input_write", "network", "shell", "undeclared_binary")}, "python_execution": "executed_no_effect"}})
    podman = _write(stage / "podman", f"#!/bin/sh\ncase \"$1\" in\ninfo) echo true ;;\nimage) echo \"$5\" ;;\nrun) payload=$(cat); case \"$*\" in *p2_python_bypass_probe*) echo '{python_bypass_reply}' ;; *) case \"$payload\" in '') echo '{bypass_reply}' ;; *P2NativeRuntimeProbeV1*) echo '{probe_reply}' ;; *) echo '{worker_reply}' ;; esac ;; esac ;;\nesac\n", executable=True)
    runtime_closure = _write(metadata / "runtime_closure.json", canonical_bytes({"schema": "P2NativeRuntimeClosureV1", "binary_digest": _digest(worker), "interpreter": "/lib64/ld-linux-x86-64.so.2", "files": [{"path": "/lib64/ld-linux-x86-64.so.2", "digest": "sha256:" + "a" * 64, "elf_class": 2, "elf_machine": 62}], "support_files": [{"path": "/etc/ld.so.cache", "digest": "sha256:" + "b" * 64}]}).decode("utf-8"))
    staged = {"native_worker_binary": worker, "native_evaluator_binary": evaluator,
              "seccomp_policy": seccomp, "sealed_input": sealed, "runtime_closure": runtime_closure}
    for name in set(ARTIFACT_NAMES) - set(staged) - {"p2_image", "p2_bypass_image", "p2_python_bypass_image"}:
        staged[name] = _write(metadata / f"{name}.json", json.dumps({"artifact": name}))
    p2_image, bypass_image, python_bypass_image = "sha256:" + "3" * 64, "sha256:" + "4" * 64, "sha256:" + "5" * 64
    staged.update({"p2_image": p2_image, "p2_bypass_image": bypass_image, "p2_python_bypass_image": python_bypass_image})
    artifacts = {name: staged[name] if name in {"p2_image", "p2_bypass_image", "p2_python_bypass_image"} else _digest(staged[name]) for name in ARTIFACT_NAMES}
    configured = release_lock(artifacts) if lock is None else lock
    spec = PodmanSpec(p2_image, worker, agent, inputs, seccomp, artifacts["seccomp_policy"], work, stage, podman_path=str(podman))
    replay = tmp_path / "replay"
    replay.mkdir()
    return P2Runner(evaluator_binary=evaluator, evaluation_lock=configured, envelope_key=envelope_key,
        replay_root=replay, receipt_log=ReceiptLog(tmp_path / "receipts", PRIVATE),
        failure_log=ReceiptFailureLog(tmp_path / "receipt-failures", PRIVATE), worker_spec=spec,
        trusted_lock_keys=trusted_lock_keys or {"ed25519:p2-release-test": LOCK_PUBLIC}, release_artifacts=staged)


def test_unified_runner_scores_worker_mismatch_then_receipts_replay_denial(tmp_path):
    runner = _runner(tmp_path)
    first = runner.score(envelope())
    assert first["classification"] == "worker_mismatch"
    assert first["success_credit"] == 0 and first["result_seal"] == first["receipt_hash"]
    assert first["verified_input_digest"] == runner.evaluation_lock["artifacts"]["sealed_input"]
    second = runner.score(envelope())
    assert second["classification"] == "replay_denied"
    record = json.loads((tmp_path / "receipts" / "000001.json").read_text())
    evidence = record["hostile_bypass_evidence"]
    assert record["outcome"]["hostile_bypass_evidence_hash"] == object_hash(evidence)
    assert evidence["native_attempts"]["network"] == {"attempted": True, "result": "blocked"}
    assert evidence["python_attempts"]["python_execution"] == {"attempted": True, "result": "executed_no_effect"}
    assert all(commitment["before"] == commitment["after"] for commitment in evidence["evaluator_mounts"].values())
    assert ReceiptLog(tmp_path / "receipts", PRIVATE).sequence == 2


def test_valid_but_separately_supplied_envelope_is_denied_before_worker_launch(tmp_path):
    runner = _runner(tmp_path)
    separately_signed = copy.deepcopy(envelope())
    separately_signed["run_id"] = "other-run"
    separately_signed = signed(separately_signed)
    response = runner.score(separately_signed)
    assert response["classification"] == "protocol_error"
    assert not list((tmp_path / "replay").glob("*.claim"))
    receipt = ReceiptLog(tmp_path / "receipts", PRIVATE)
    assert receipt.sequence == 1
    record = json.loads((tmp_path / "receipts" / "000001.json").read_text())
    locked_digest = _digest(Path(runner.release_artifacts["sealed_input"]))
    assert response["verified_input_digest"] == locked_digest
    assert record["input_digest"] == locked_digest
    assert record["submitted_input_evidence_hash"] == object_hash(separately_signed)
    assert record["submitted_input_evidence_hash"] != record["input_digest"]


def test_primary_receipt_append_failure_emits_signed_failure_seal_and_survives_restart(tmp_path, monkeypatch):
    runner = _runner(tmp_path)
    monkeypatch.setattr(runner.receipts, "append", lambda _receipt: (_ for _ in ()).throw(OSError("read-only")))
    response = runner.score(envelope())
    assert response["classification"] == "receipt_persistence_failed"
    assert response["success_credit"] == 0 and response["brokered"] is False
    assert response["result_seal"] == response["failure_record_hash"]
    assert not list((tmp_path / "replay").glob("*.claim"))
    restarted = ReceiptFailureLog(tmp_path / "receipt-failures", PRIVATE)
    assert restarted.sequence == 1 and restarted.previous == response["failure_record_hash"]


def _assert_unverified_receipt(root: Path, response, submitted) -> None:
    record = json.loads((root / "receipts" / "000001.json").read_text())
    assert response["verified_input_digest"] is None
    assert record["lock_status"] == "unverified"
    assert all(record[name] is None for name in ("lock_digest", "input_digest", "worker_image_digest", "evaluator_binary_digest"))
    assert record["submitted_input_evidence_hash"] == object_hash(submitted)


def test_receipt_preflight_failure_blocks_worker_and_emits_unverified_receipt(tmp_path, monkeypatch):
    runner = _runner(tmp_path)
    submitted = envelope()
    monkeypatch.setattr(runner.receipts, "preflight", lambda: (_ for _ in ()).throw(P2ProtocolError("receipt append preflight")))
    response = runner.score(submitted)
    assert response["classification"] == "protocol_error"
    assert not list((tmp_path / "replay").glob("*.claim"))
    _assert_unverified_receipt(tmp_path, response, submitted)


def test_malformed_invalid_and_tampered_release_locks_emit_unverified_receipts(tmp_path):
    malformed = _runner(tmp_path / "malformed-lock", lock={"lock_schema": "broken"})
    submitted = envelope()
    response = malformed.score(submitted)
    assert response["classification"] == "protocol_error"
    _assert_unverified_receipt(tmp_path / "malformed-lock", response, submitted)

    wrong_key = Ed25519PrivateKey.from_private_bytes(bytes([9]) * 32).public_key()
    invalid = _runner(tmp_path / "wrong-trust", trusted_lock_keys={"ed25519:p2-release-test": wrong_key})
    submitted = envelope()
    response = invalid.score(submitted)
    assert response["classification"] == "protocol_error"
    _assert_unverified_receipt(tmp_path / "wrong-trust", response, submitted)

    tampered = _runner(tmp_path / "tampered-lock")
    tampered.evaluation_lock["artifacts"]["runtime_closure"] = "sha256:" + "f" * 64
    submitted = envelope()
    response = tampered.score(submitted)
    assert response["classification"] == "protocol_error"
    _assert_unverified_receipt(tmp_path / "tampered-lock", response, submitted)


def test_verified_lock_artifact_substitution_retains_locked_input_digest(tmp_path):
    runner = _runner(tmp_path)
    runtime_closure = Path(runner.release_artifacts["runtime_closure"])
    runtime_closure.chmod(0o600)
    runtime_closure.write_text("substituted")
    submitted = envelope()
    response = runner.score(submitted)
    record = json.loads((tmp_path / "receipts" / "000001.json").read_text())
    assert response["classification"] == "protocol_error"
    assert record["lock_status"] == "verified"
    assert record["input_digest"] == runner.evaluation_lock["artifacts"]["sealed_input"]
    assert record["submitted_input_evidence_hash"] == object_hash(submitted)


def test_every_staged_artifact_substitution_fails_closed(tmp_path):
    for artifact in ARTIFACT_NAMES:
        runner = _runner(tmp_path / artifact)
        staged = runner.release_artifacts[artifact]
        if artifact in {"p2_image", "p2_bypass_image", "p2_python_bypass_image"}:
            runner.release_artifacts[artifact] = "sha256:" + "f" * 64
        else:
            target = Path(staged)
            target.chmod(0o600)
            target.write_text("substituted")
        assert runner.score(envelope())["classification"] == "protocol_error", artifact
        record = json.loads((tmp_path / artifact / "receipts" / "000001.json").read_text())
        assert record["lock_status"] == "verified"
        assert record["input_digest"] == runner.evaluation_lock["artifacts"]["sealed_input"]

    wrong_key = Ed25519PrivateKey.from_private_bytes(bytes([8]) * 32).public_key()
    runner = _runner(tmp_path, envelope_key=wrong_key)
    assert runner.score(envelope())["classification"] == "protocol_error"
    record = json.loads((tmp_path / "receipts" / "000001.json").read_text())
    assert record["lock_status"] == "verified"
