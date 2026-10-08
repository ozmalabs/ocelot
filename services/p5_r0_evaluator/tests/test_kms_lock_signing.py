from __future__ import annotations

from copy import deepcopy
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, digest
from evaluation.p5_r0.diagnostic_generator import build_diagnostic_artifacts
from services.p5_r0_evaluator.deploy.kms_lock_signing import (
    KMSLockSigningValidationError,
    _cli,
    operation_descriptor,
    validate_signed_response,
    validate_unsigned_request,
)


KEY_VERSION = "projects/example/locations/us/keyRings/diagnostic/cryptoKeys/lock/cryptoKeyVersions/7"


def _authority(key: Ed25519PrivateKey) -> dict:
    public_key = b64encode(key.public_key().public_bytes_raw())
    return {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": "project-authority",
        "key_id": "diagnostic-lock-key",
        "public_key": public_key,
        "public_key_digest": digest(public_key),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1",
            "provider": "confidential-space",
            "audience": "p5-r0",
            "event": "approved",
        },
    }


def _response(request: dict, key: Ed25519PrivateKey) -> dict:
    authority = _authority(key)
    binding = {
        "schema": "P5R0KMSAuthorityBindingV1",
        "authority_id": authority["authority_id"],
        "key_id": authority["key_id"],
        "kms_key_version": KEY_VERSION,
        "public_key_digest": authority["public_key_digest"],
        "purpose": "p5-r0-production-authority",
    }
    binding["binding_digest"] = digest(binding)
    approval = {
        "schema": "P5R0ConfidentialSpaceApprovalV1",
        "environment": "Confidential Space",
        "approval_source": "confidential_space_attestation",
        "approved": True,
        "attestation_verified": True,
        "project_authority": "self_custodied",
        "local_execution": False,
    }
    approval["approval_digest"] = digest(approval)
    signed_lock = deepcopy(request["unsigned_lock"])
    lock_bytes = bytes.fromhex(request["unsigned_lock_digest"][7:])
    signed_lock["signature"] = b64encode(key.sign(lock_bytes))
    return {
        "schema": "P5R0KMSLockSigningResponseV1",
        "status": "signed_review_only",
        "request_digest": request["request_digest"],
        "unsigned_lock_digest": request["unsigned_lock_digest"],
        "approval": approval,
        "authority": authority,
        "kms": {
            "key_version": KEY_VERSION,
            "public_key": authority["public_key"],
            "public_key_digest": authority["public_key_digest"],
            "authority_binding": binding,
        },
        "signed_lock": signed_lock,
    }


def test_checked_in_request_is_exact_and_contract_has_no_output():
    request = build_diagnostic_artifacts()["lock_signing_request"]
    report = validate_unsigned_request(request)
    assert report.signature_present is False
    assert report.production_promotable is False
    assert request["unsigned_lock_digest"] == "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"
    assert request["kms"]["key_version"] is None
    assert request["kms"]["authority_binding_digest"] is None
    assert request["unsigned_lock"]["signature"] is None


def test_operation_uses_existing_signer_without_invocation():
    class Capability:
        authority = {"not": "used to sign"}

        def sign_digest(self, _digest: bytes) -> str:
            raise AssertionError("RS-065 must not invoke a signer")

    descriptor = operation_descriptor(Capability())
    assert descriptor["interface"] == "services.p5_r0_evaluator.interfaces.Signer.sign_digest"
    assert descriptor["signature"] is None
    assert descriptor["private_key_export"] is False


def test_wrong_digest_is_rejected():
    request = build_diagnostic_artifacts()["lock_signing_request"]
    tampered = deepcopy(request)
    tampered["unsigned_lock_digest"] = "sha256:" + "0" * 64
    with pytest.raises(KMSLockSigningValidationError, match="exact frozen diagnostic request"):
        validate_unsigned_request(tampered)


def test_wrong_returned_key_is_rejected():
    request = build_diagnostic_artifacts()["lock_signing_request"]
    response = _response(request, Ed25519PrivateKey.generate())
    wrong = Ed25519PrivateKey.generate()
    response["kms"]["public_key"] = b64encode(wrong.public_key().public_bytes_raw())
    response["kms"]["public_key_digest"] = digest(response["kms"]["public_key"])
    with pytest.raises(KMSLockSigningValidationError, match="returned public key does not match authority"):
        validate_signed_response(request, response)


def test_malformed_signature_is_rejected():
    request = build_diagnostic_artifacts()["lock_signing_request"]
    response = _response(request, Ed25519PrivateKey.generate())
    response["signed_lock"]["signature"] = "not-a-valid-signature"
    with pytest.raises(KMSLockSigningValidationError, match="signature"):
        validate_signed_response(request, response)


@pytest.mark.parametrize("field,value", [("local_execution", True), ("approved", False)])
def test_attempted_local_or_unapproved_promotion_is_rejected(field: str, value: bool):
    request = build_diagnostic_artifacts()["lock_signing_request"]
    response = _response(request, Ed25519PrivateKey.generate())
    response["approval"][field] = value
    with pytest.raises(KMSLockSigningValidationError, match="approval"):
        validate_signed_response(request, response)


def test_valid_future_response_stays_review_only_and_non_release():
    request = build_diagnostic_artifacts()["lock_signing_request"]
    response = _response(request, Ed25519PrivateKey.generate())
    report = validate_signed_response(request, response)
    assert report.signature_present is True
    assert report.production_promotable is False
    assert response["signed_lock"]["non_release"] is True
    assert response["signed_lock"]["classification"] == "diagnostic_unsigned_kms_request"


def test_cli_contract_validation_is_local_only(capsys):
    assert _cli(["validate"]) == 0
    output = capsys.readouterr().out
    assert "blocked_pending_confidential_space_approval" in output
    assert '"signature_present":false' in output
