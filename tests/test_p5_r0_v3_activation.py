from pathlib import Path
import json
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p5_r0.domain_cards import authority_from_private
from evaluation.p5_r0.evidence import seal_result, verify_result_seal
from evaluation.p5_r0.native import closure_spec_v3
from evaluation.p5_r0.preregister import preregister
from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.receipts import ReceiptChain
from evaluation.p5_r0.repair import V3_PARENT_LOCK_DIGEST, preregister_repair
from evaluation.p5_r0.runner import run_readiness_gate


def _v3(tmp_path):
    key = Ed25519PrivateKey.generate()
    authority = authority_from_private(key, "external-v3-authority", "external-v3-key")
    authority["transport_attestation"] = {"schema": "external", "nonce": "activation-test"}
    parent = {"lock_digest": V3_PARENT_LOCK_DIGEST, "manifest_digest": digest("parent-manifest"), "case_index_digest": digest("parent-index"), "truth_digest": digest("parent-truth"), "store_digest": digest("parent-store"), "split_commitment": {"contrast_matrix": []}}
    profile = tmp_path / "seccomp.json"
    profile.write_text(json.dumps({"defaultAction": "SCMP_ACT_ERRNO", "syscalls": [{"action": "SCMP_ACT_ALLOW", "names": ["read"]}]}))
    image = "sha256:" + "a" * 64
    closure = closure_spec_v3(image_digest=image, image_ref="local:v3@" + image, entrypoint="/runtime/p5_r0_worker", profile=profile, paths={"worker": Path(__file__), "runtime": Path("/usr/bin/crun")}, allowed_syscalls=["read"])
    artifact = preregister_repair(tmp_path / "v3-lock.json", parent_lock=parent, signer=key, trusted_authority=authority, closure=closure)
    return artifact, key, authority


def test_v2_is_rejected_for_production_and_is_immutable(tmp_path):
    key = Ed25519PrivateKey.generate(); authority = authority_from_private(key); authority["transport_attestation"] = {"schema": "external"}
    artifact = preregister(tmp_path / "v2-lock.json", signer=key, trusted_authority=authority)
    lock_path = tmp_path / "v2-lock.json"; before = lock_path.read_bytes(); mode = lock_path.stat().st_mode
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"], trusted_authority=authority, receipt_signer=key)
    assert result["outcome"] == "local_readiness_only/no_go"
    assert lock_path.read_bytes() == before and lock_path.stat().st_mode == mode


def test_v3_preflight_is_first_and_seal_reload_verifies(tmp_path):
    artifact, key, authority = _v3(tmp_path)
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"], trusted_authority=authority, receipt_signer=key, require_native=False)
    assert result["schema"] == "P5R0ResultSealV3" and result["disposition"] == "impasse"
    assert result["record_count"] == 0 and result["control_count"] == 0
    chain = ReceiptChain.reload(tmp_path / "receipts", key.public_key(), authority_id=authority["authority_id"], key_id=authority["key_id"])
    assert chain.records[0]["payload"]["kind"] == "impasse"
    sealed = seal_result(result, tmp_path / "result.json")
    assert verify_result_seal(tmp_path / "result.json")["seal_digest"] == sealed["seal_digest"]


def test_v3_key_or_chain_tamper_is_rejected(tmp_path):
    artifact, key, authority = _v3(tmp_path)
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"], trusted_authority=authority, receipt_signer=key, require_native=False)
    out = tmp_path / "result.json"; seal_result(result, out)
    raw = json.loads(out.read_text()); raw["receipt_key_id"] = "tampered"; out.chmod(0o600); out.write_text(json.dumps(raw)); out.chmod(0o400)
    with pytest.raises(P5R0Error): verify_result_seal(out)
    receipt = tmp_path / "receipts" / "000001.json"; original = receipt.read_bytes(); receipt.chmod(0o600); receipt.write_bytes(original.replace(b"containment_failure", b"rollback_impasse")); receipt.chmod(0o400)
    with pytest.raises(P5R0Error): ReceiptChain.reload(tmp_path / "receipts", key.public_key(), authority_id=authority["authority_id"], key_id=authority["key_id"])


def test_missing_authority_is_no_go_before_native(monkeypatch, tmp_path):
    artifact, key, _authority = _v3(tmp_path)
    called = []
    monkeypatch.setattr("evaluation.p5_r0.runner._invoke_native_case", lambda **_: called.append(True))
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"], require_native=True)
    assert result["outcome"] == "local_readiness_only/no_go" and not called


def test_v3_native_fallback_is_rejected_before_worker_execution(monkeypatch, tmp_path):
    artifact, key, authority = _v3(tmp_path)
    called = []
    monkeypatch.setattr("evaluation.p5_r0.runner._invoke_native_case", lambda **_: called.append(True))
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"], trusted_authority=authority, receipt_signer=key, require_native=False)
    assert result["outcome"] == "local_readiness_only/no_go"
    assert result["record_count"] == 0 and result["control_count"] == 0 and not called
    assert "V3 native worker is mandatory" in result["gate_reasons"][0]



def test_v3_no_go_cannot_be_resealed_as_go(tmp_path):
    artifact, key, authority = _v3(tmp_path)
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"], trusted_authority=authority, receipt_signer=key, require_native=False)
    result["outcome"] = result["disposition"] = "local_readiness_only/go"; result["gate_reasons"] = []
    with pytest.raises(P5R0Error): seal_result(result, tmp_path / "forged.json")


def test_v3_projection_rejects_nested_private_fields(tmp_path):
    artifact = preregister(tmp_path / "v2.json")
    from evaluation.p5_r0.fixture_generator import make_task_v3, private_store_for
    from evaluation.p5_r0.native_worker import validate_task
    task = make_task_v3(private_store_for(artifact["bundle"])["cases"][0], task_nonce="privacy", persistent_projection={"truth": "secret"})
    with pytest.raises(P5R0Error): validate_task(task)


def test_v3_output_collision_is_rejected(tmp_path):
    artifact, key, authority = _v3(tmp_path)
    with pytest.raises(P5R0Error):
        preregister_repair(tmp_path / "v3-lock.json", parent_lock={"lock_digest": V3_PARENT_LOCK_DIGEST}, signer=key, trusted_authority=authority)



def test_v3_impasse_no_go_is_sealable_and_reloadable(tmp_path):
    artifact, _key, _authority = _v3(tmp_path)
    result = run_readiness_gate(artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"], require_native=True)
    assert result["disposition"] == "impasse" and result["outcome"] == "local_readiness_only/no_go"
    seal_result(result, tmp_path / "impasse.json")
    assert verify_result_seal(tmp_path / "impasse.json")["schema"] == "P5R0ResultSealV3"



def test_v3_readiness_requires_explicit_durable_private_store(tmp_path):
    artifact, key, authority = _v3(tmp_path)
    result = run_readiness_gate(
        artifact["bundle"], receipts_root=tmp_path / "receipts", lock=artifact["lock"],
        trusted_authority=authority, receipt_signer=key, require_native=True,
    )
    assert result["disposition"] == "impasse"
    assert "durable private store" in result["gate_reasons"][0]
