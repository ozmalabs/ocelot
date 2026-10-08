from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.deploy.authority_binding_proposal import (
    REVIEW_AUTHORITY_ID,
    REVIEW_AUDIENCE,
    REVIEW_KEY_ID,
    REVIEW_KMS_KEY_VERSION,
    REVIEW_PROVIDER,
    REVIEW_PUBLIC_KEY_DIGEST,
)
from services.p5_r0_evaluator.deploy.rs069r18r11_operation_3 import (
    ACCEPTANCE_CONTRACT,
    APPROVAL_ID,
    APPROVAL_SCHEMA,
    DEFAULT_DEPENDENCY_LEDGER,
    DEFAULT_LEDGER,
    DEFAULT_PLAN,
    DEFAULT_REQUEST,
    LATER_OPERATION_IDS,
    OPERATION_ID,
    RS069Operation3Blocked,
    _load_r18r10_dependency,
    execute_operation_3,
    validate_operation_3_bindings,
)
from services.p5_r0_evaluator.deploy.rs069_change_plan import load_plan

ROOT = Path(__file__).resolve().parents[3]


def _binding() -> dict:
    public = "bZEShuBoboR54KanOSdEyfDB6EnjnFaultXu7uof9e4"
    provider = REVIEW_PROVIDER
    audience = REVIEW_AUDIENCE
    authority = {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": REVIEW_AUTHORITY_ID,
        "key_id": REVIEW_KEY_ID,
        "public_key": public,
        "public_key_digest": REVIEW_PUBLIC_KEY_DIGEST,
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1",
            "provider": provider,
            "audience": audience,
            "event": "confidential_space_attestation",
        },
    }
    environment = {
        "provider": provider,
        "audience": audience,
        "event": "confidential_space_attestation",
        "claims": {
            "project_number": "141633828616",
            "project_id": "ocelot-proof",
            "zone": "us-east1-b",
            "workload": "evaluator",
            "issuer": "https://confidentialcomputing.googleapis.com",
            "image_digest": "sha256:" + "a" * 64,
            "debug_state": "disabled-since-boot",
            "tee": "CONFIDENTIAL_SPACE",
            "hardware_model": "GCP_AMD_SEV",
            "secure_boot": True,
            "smoke": False,
        },
        "claim_paths": {
            "audience": "aud",
            "nonce": "eat_nonce",
            "issued_at": "iat",
            "expires_at": "exp",
            "issuer": "iss",
            "subject": "sub",
            "image_digest": "submods.container.image_digest",
            "project_number": "submods.gce.project_number",
            "project_id": "submods.gce.project_id",
            "zone": "submods.gce.zone",
            "debug_state": "dbgstat",
            "tee": "swname",
            "hardware_model": "hwmodel",
            "secure_boot": "secboot",
            "workload": "submods.container.env.P5R0_EXPECTED_WORKLOAD",
            "smoke": "submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
        },
    }
    key_version = REVIEW_KMS_KEY_VERSION
    body = {
        "schema": "P5R0KMSAuthorityBindingV1",
        "authority_id": authority["authority_id"],
        "key_id": authority["key_id"],
        "kms_key_version": key_version,
        "public_key_digest": authority["public_key_digest"],
        "purpose": "p5-r0-production-authority",
    }
    kms = {
        "key_version": key_version,
        "public_key": public,
        "public_key_digest": authority["public_key_digest"],
        "authority_binding": {**body, "binding_digest": digest(body)},
    }
    artifact = {
        "schema": "P5R0RS069R18R11BindingInputsV1",
        "classification": "diagnostic_unsigned_non_release",
        "authority": authority,
        "kms": kms,
        "environment": environment,
    }
    return {**artifact, "artifact_digest": sha256(artifact)}


def _approval(plan: dict, binding: dict, dependency: dict, request: dict) -> dict:
    artifact = {
        "schema": APPROVAL_SCHEMA,
        "acceptance_contract": ACCEPTANCE_CONTRACT,
        "approval_id": APPROVAL_ID,
        "status": "approved_single_operation_pending_apply",
        "operation_id": OPERATION_ID,
        "operation_order": 3,
        "scope": [OPERATION_ID],
        "attempt_id": "rs069r18r11-op3-20260919-a1b2c3d4",
        "plan_digest": sha256(plan),
        "dependency_ledger_head_digest": dependency["ledger_head_digest"],
        "binding_artifact_digest": binding["artifact_digest"],
        "authority_binding_digest": binding["kms"]["authority_binding"]["binding_digest"],
        "request_digest": request["request_digest"],
        "unsigned_lock_digest": request["unsigned_lock_digest"],
        "attestation": {"status": "deferred", "deferred_to": "RS-080", "asserted": False},
        "later_operations": [{"id": item, "enabled": False} for item in LATER_OPERATION_IDS],
        "master_approved": True,
        "user_approved": True,
        "approved": True,
        "enabled": True,
    }
    return {**artifact, "artifact_digest": sha256(artifact)}


def _artifacts():
    plan = load_plan(DEFAULT_PLAN)
    request = parse_canonical(DEFAULT_REQUEST.read_bytes())
    binding = _binding()
    dependency = _load_r18r10_dependency(DEFAULT_DEPENDENCY_LEDGER)
    approval = _approval(plan, binding, dependency, request)
    return plan, request, binding, approval, dependency


def _write_canonical(path: Path, value: dict) -> None:
    path.write_bytes(canonical_bytes(value))


def test_default_attempt_fails_closed_without_creating_r18r11_artifacts(tmp_path):
    with pytest.raises(RS069Operation3Blocked, match="binding artifact is unavailable"):
        execute_operation_3(repository_root=ROOT, apply_enabled=True, ledger_path=tmp_path / DEFAULT_LEDGER.name)
    assert not (tmp_path / DEFAULT_LEDGER.name).exists()


def test_valid_review_packet_writes_only_distinct_local_review_ledger(tmp_path):
    plan, request, binding, approval, _ = _artifacts()
    _write_canonical(tmp_path / "plan.json", plan)
    _write_canonical(tmp_path / "request.json", request)
    _write_canonical(tmp_path / "binding.json", binding)
    _write_canonical(tmp_path / "approval.json", approval)
    ledger = tmp_path / DEFAULT_LEDGER.name
    before_r18r10 = DEFAULT_DEPENDENCY_LEDGER.read_bytes()

    result = execute_operation_3(
        repository_root=ROOT,
        plan_path=tmp_path / "plan.json",
        request_path=tmp_path / "request.json",
        binding_path=tmp_path / "binding.json",
        approval_path=tmp_path / "approval.json",
        ledger_path=ledger,
        dependency_ledger_path=DEFAULT_DEPENDENCY_LEDGER,
        apply_enabled=True,
    )

    assert result["status"] == "verified_repository_binding_review_only"
    assert result["cloud_operations"] == []
    assert result["mutations_performed"] is False
    assert result["production_promotable"] is False
    assert result["later_operations_enabled"] is False
    records = [parse_canonical(line) for line in ledger.read_bytes().splitlines()]
    assert [record["kind"] for record in records] == ["run_started", "dependency_verified", "binding_verified", "run_stopped"]
    assert all(record["cloud_operations"] == [] and record["mutations_performed"] is False for record in records)
    assert records[-1]["later_operations_skipped"] == list(LATER_OPERATION_IDS)
    assert DEFAULT_DEPENDENCY_LEDGER.read_bytes() == before_r18r10


def test_changed_request_or_binding_digest_fails_before_new_ledger(tmp_path):
    plan, request, binding, approval, dependency = _artifacts()
    tampered_request = deepcopy(request)
    tampered_request["unsigned_lock"]["classification"] = "changed"
    with pytest.raises(RS069Operation3Blocked, match="unsigned lock request validation failed"):
        validate_operation_3_bindings(plan=plan, request=tampered_request, binding=binding, approval=approval, dependency=dependency)

    tampered_binding = deepcopy(binding)
    tampered_binding["kms"]["authority_binding"]["binding_digest"] = "sha256:" + "0" * 64
    tampered_binding["artifact_digest"] = sha256({key: value for key, value in tampered_binding.items() if key != "artifact_digest"})
    with pytest.raises(RS069Operation3Blocked, match="authority/KMS binding validation failed"):
        validate_operation_3_bindings(plan=plan, request=request, binding=tampered_binding, approval=approval, dependency=dependency)
    assert not list(tmp_path.iterdir())


def test_widened_scope_or_attestation_is_rejected():
    plan, request, binding, approval, dependency = _artifacts()
    widened = deepcopy(approval)
    widened["scope"] = [OPERATION_ID, LATER_OPERATION_IDS[0]]
    widened["artifact_digest"] = sha256({key: value for key, value in widened.items() if key != "artifact_digest"})
    with pytest.raises(RS069Operation3Blocked, match="approval scope drift"):
        validate_operation_3_bindings(plan=plan, request=request, binding=binding, approval=widened, dependency=dependency)

    forged = deepcopy(approval)
    forged["attestation"] = {"status": "verified", "deferred_to": None, "asserted": True}
    forged["artifact_digest"] = sha256({key: value for key, value in forged.items() if key != "artifact_digest"})
    with pytest.raises(RS069Operation3Blocked, match="must not fabricate attestation"):
        validate_operation_3_bindings(plan=plan, request=request, binding=binding, approval=forged, dependency=dependency)


def test_r18r10_dependency_is_exact_and_read_only():
    dependency = _load_r18r10_dependency(DEFAULT_DEPENDENCY_LEDGER)
    assert dependency["poststate_digest"] == "sha256:9a7fcde1498606c60ab06e83a91eb3ba1712f8da6cdb554ca4cb02f3c2060ff7"
    assert DEFAULT_LEDGER != DEFAULT_DEPENDENCY_LEDGER
    assert not DEFAULT_LEDGER.exists()



def test_noncanonical_reviewed_kms_version_is_rejected():
    plan, request, binding, approval, dependency = _artifacts()
    drifted = deepcopy(binding)
    drifted["kms"]["key_version"] = drifted["kms"]["key_version"].replace("cryptoKeyVersions/1", "cryptoKeyVersions/2")
    drifted["kms"]["authority_binding"]["kms_key_version"] = drifted["kms"]["key_version"]
    binding_body = {key: value for key, value in drifted["kms"]["authority_binding"].items() if key != "binding_digest"}
    drifted["kms"]["authority_binding"]["binding_digest"] = sha256(binding_body)
    drifted["artifact_digest"] = sha256({key: value for key, value in drifted.items() if key != "artifact_digest"})
    with pytest.raises(RS069Operation3Blocked, match="reviewed authority/KMS commitments drift"):
        validate_operation_3_bindings(plan=plan, request=request, binding=drifted, approval=approval, dependency=dependency)
