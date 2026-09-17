import os
import shutil
import subprocess
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.canonical import b64encode, canonical_bytes, parse_canonical, sign
from evaluation.p4.evaluator import P4R0Evaluator
from evaluation.p4.receipts import P4ReceiptLog
from evaluation.p4.runner import _native_request
from evaluation.p4.tests.helpers import local_lock, staged_spec

ROOT = Path(__file__).resolve().parents[3]
RUST = ROOT / "runners" / "dsl"


def _worker() -> Path:
    cargo = shutil.which("cargo")
    if cargo is None:
        pytest.skip("cargo unavailable")
    completed = subprocess.run([cargo, "build", "--offline", "--manifest-path", str(RUST / "Cargo.toml"), "--bin", "p4_native_readiness_worker"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=180)
    if completed.returncode:
        pytest.fail(completed.stderr.decode("utf-8", "replace"))
    target = Path(os.environ.get("CARGO_TARGET_DIR", RUST / "target"))
    if not target.is_absolute():
        target = RUST / target
    return target / "debug" / "p4_native_readiness_worker"


def _request(tmp_path):
    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    lock = local_lock(tmp_path, spec, evaluator_signer=signer)
    receipts = P4ReceiptLog(tmp_path / "receipts", signer)
    evaluator = P4R0Evaluator(b"seed", {"root": 1}, lock, receipts)
    return _native_request(lock, evaluator, receipts, "p4-r0", evaluator.pre_run_graph_snapshot_digest), signer, spec


def _run_unit_harness(worker: Path, request: dict, trust_artifact: Path):
    """Explicit unit-only host harness; it never invokes run_local readiness."""
    env = {"PATH": os.environ.get("PATH", ""), "P4_UNIT_HARNESS": "1", "P4_UNIT_TRUST_ARTIFACT": str(trust_artifact)}
    return subprocess.run([str(worker)], input=canonical_bytes(request), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=3, env=env)


def test_real_evaluator_transport_reaches_native_complete_and_rejects_adversarial_outcomes(tmp_path):
    worker = _worker()
    request, signer, spec = _request(tmp_path)
    valid = _run_unit_harness(worker, request, spec.trusted_evaluator_artifact())
    assert valid.returncode == 0
    assert parse_canonical(valid.stdout) == {"schema": "P4NativeReadinessReplyV1", "status": "complete"}

    signed = parse_canonical(request["outcomes"][0])
    forged = dict(signed)
    forged["signature"] = ("A" if forged["signature"][0] != "A" else "B") + forged["signature"][1:]
    forged_request = dict(request)
    forged_request["outcomes"] = [canonical_bytes(forged).decode("ascii")]
    assert _run_unit_harness(worker, forged_request, spec.trusted_evaluator_artifact()).returncode != 0

    altered = dict(signed)
    altered["reservation_digest"] = "sha256:" + "f" * 64
    altered["signature"] = sign(altered, signer)
    altered_request = dict(request)
    altered_request["outcomes"] = [canonical_bytes(altered).decode("ascii")]
    assert _run_unit_harness(worker, altered_request, spec.trusted_evaluator_artifact()).returncode != 0

    wrong_key = dict(signed)
    wrong_key["key_id"] = "p4-r0-forged-key"
    wrong_key["signature"] = sign(wrong_key, signer)
    wrong_key_request = dict(request)
    wrong_key_request["outcomes"] = [canonical_bytes(wrong_key).decode("ascii")]
    assert _run_unit_harness(worker, wrong_key_request, spec.trusted_evaluator_artifact()).returncode != 0

    replay_request = dict(request)
    replay_request["outcomes"] = [request["outcomes"][0], request["outcomes"][0]]
    assert _run_unit_harness(worker, replay_request, spec.trusted_evaluator_artifact()).returncode != 0


def test_self_consistent_attacker_key_request_cannot_bypass_staged_authority(tmp_path):
    worker = _worker()
    request, _, spec = _request(tmp_path)
    attacker = Ed25519PrivateKey.generate()
    attacker_key = b64encode(attacker.public_key().public_bytes_raw())
    signed = parse_canonical(request["outcomes"][0])
    signed["authority_id"] = "attacker"
    signed["key_id"] = "attacker-key"
    signed["authority_public_key"] = attacker_key
    signed["lock_digest"] = "sha256:" + "e" * 64
    signed["signature"] = sign(signed, attacker)
    attacker_request = dict(request)
    # Legacy caller-controlled authority fields are rejected by the closed request schema.
    attacker_request.update({"authority_id": "attacker", "key_id": "attacker-key", "authority_public_key": attacker_key, "lock_digest": "sha256:" + "e" * 64})
    attacker_request["outcomes"] = [canonical_bytes(signed).decode("ascii")]
    assert _run_unit_harness(worker, attacker_request, spec.trusted_evaluator_artifact()).returncode != 0


def test_staged_authority_artifact_tamper_is_rejected_by_worker(tmp_path):
    worker = _worker()
    request, _, spec = _request(tmp_path)
    spec.trusted_evaluator_artifact().write_text("{}")
    assert _run_unit_harness(worker, request, spec.trusted_evaluator_artifact()).returncode != 0



@pytest.mark.parametrize("arm", ["graph_planner", "reactive_no_plan", "no_causal_model", "search_budget_matched"])
def test_native_arm_trace_controls_reach_completion(tmp_path, arm):
    worker = _worker()
    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    lock = local_lock(tmp_path, spec, evaluator_signer=signer)
    receipts = P4ReceiptLog(tmp_path / "receipts", signer)
    evaluator = P4R0Evaluator(b"seed", {"root": 1}, lock, receipts)
    request = _native_request(lock, evaluator, receipts, "p4-r0", evaluator.pre_run_graph_snapshot_digest, arm_id=arm)
    completed = _run_unit_harness(worker, request, spec.trusted_evaluator_artifact())
    assert completed.returncode == 0
    assert parse_canonical(completed.stdout)["status"] == "complete"


def test_native_reset_memory_arm_fails_closed_after_intervention(tmp_path):
    worker = _worker()
    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    lock = local_lock(tmp_path, spec, evaluator_signer=signer)
    receipts = P4ReceiptLog(tmp_path / "receipts", signer)
    evaluator = P4R0Evaluator(b"seed", {"root": 1}, lock, receipts)
    request = _native_request(lock, evaluator, receipts, "p4-r0", evaluator.pre_run_graph_snapshot_digest, arm_id="reset_memory")
    assert _run_unit_harness(worker, request, spec.trusted_evaluator_artifact()).returncode != 0



def test_native_rejects_label_scramble_and_transition_confounds(tmp_path):
    worker = _worker()
    request, _, spec = _request(tmp_path)
    scrambled = dict(request)
    selection = dict(request["runtime_selection"])
    selection["arm_id"] = "reactive_no_plan"
    scrambled["runtime_selection"] = selection
    assert _run_unit_harness(worker, scrambled, spec.trusted_evaluator_artifact()).returncode != 0

    mismatched = dict(request)
    mismatched["actions"] = ["reverse", "inspect", "advance"]
    assert _run_unit_harness(worker, mismatched, spec.trusted_evaluator_artifact()).returncode != 0

    unavailable = dict(request)
    unavailable["actions"] = ["inspect", "delete", "advance"]
    assert _run_unit_harness(worker, unavailable, spec.trusted_evaluator_artifact()).returncode != 0
