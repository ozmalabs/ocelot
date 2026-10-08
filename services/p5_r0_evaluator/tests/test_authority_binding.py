from copy import deepcopy

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, digest
from services.p5_r0_evaluator.deploy.authority_binding import (
    DEFAULT_CONTRACT,
    AuthorityBindingValidationError,
    _cli,
    validate_candidate_binding,
    validate_contract,
)


CLAIM_PATHS = {
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
}


def _candidate():
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    provider = "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/pool/providers/evaluator"
    audience = "https://sts.googleapis.com"
    authority = {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": "test-authority",
        "key_id": "test-evaluator-key",
        "public_key": public,
        "public_key_digest": digest(public),
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
            "project_id": "ocelot1",
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
        "claim_paths": CLAIM_PATHS,
    }
    key_version = "projects/ocelot1/locations/us-east1/keyRings/p5/cryptoKeys/evaluator/cryptoKeyVersions/1"
    binding = {
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
        "public_key_digest": digest(public),
        "authority_binding": {**binding, "binding_digest": digest(binding)},
    }
    approval_body = {
        "schema": "P5R0ConfidentialSpaceApprovalV1",
        "environment": "Confidential Space",
        "approval_source": "confidential_space_attestation",
        "approved": True,
        "attestation_verified": True,
        "project_authority": "self_custodied",
        "local_execution": False,
    }
    approval = {**approval_body, "approval_digest": digest(approval_body)}
    return authority, kms, environment, approval


def test_checked_in_contract_is_canonical_marker_only_and_blocked():
    report = validate_contract(DEFAULT_CONTRACT)
    assert report["status"] == "blocked_pending_reviewed_authority_and_confidential_space_approval"
    assert report["authority_metadata_present"] is False
    assert report["approval_present"] is False
    assert report["signature_present"] is False
    assert report["production_promotable"] is False


def test_candidate_binds_authority_kms_and_signed_environment_without_signing():
    authority, kms, environment, approval = _candidate()
    report = validate_candidate_binding(authority, kms, environment, approval)
    assert report["authority_id"] == "test-authority"
    assert report["key_id"] == "test-evaluator-key"
    assert report["approval_present"] is True
    assert report["signature_present"] is False
    assert report["production_promotable"] is False


def test_wrong_kms_key_fails_closed():
    authority, kms, environment, approval = _candidate()
    wrong = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    tampered = deepcopy(kms)
    tampered["public_key"] = b64encode(wrong)
    tampered["public_key_digest"] = digest(tampered["public_key"])
    with pytest.raises(AuthorityBindingValidationError, match="does not match authority"):
        validate_candidate_binding(authority, tampered, environment, approval)


def test_provider_as_audience_confusion_fails_closed():
    authority, kms, environment, approval = _candidate()
    tampered = deepcopy(environment)
    tampered["audience"] = tampered["provider"]
    with pytest.raises(AuthorityBindingValidationError, match="separate from the provider"):
        validate_candidate_binding(authority, kms, tampered, approval)


def test_provider_project_mismatch_fails_closed():
    authority, kms, environment, approval = _candidate()
    tampered = deepcopy(environment)
    tampered["provider"] = tampered["provider"].replace("141633828616", "999999999999")
    authority["transport_attestation"]["provider"] = tampered["provider"]
    with pytest.raises(AuthorityBindingValidationError, match="does not match project claim"):
        validate_candidate_binding(authority, kms, tampered, approval)


def test_missing_transport_field_fails_closed():
    authority, kms, environment, approval = _candidate()
    tampered = deepcopy(authority)
    del tampered["transport_attestation"]["event"]
    with pytest.raises(AuthorityBindingValidationError, match="transport metadata is not closed"):
        validate_candidate_binding(tampered, kms, environment, approval)


def test_self_authored_or_local_approval_fails_closed():
    authority, kms, environment, approval = _candidate()
    tampered = deepcopy(approval)
    tampered["approval_source"] = "local_self_authored"
    tampered["local_execution"] = True
    tampered["approval_digest"] = digest({key: value for key, value in tampered.items() if key != "approval_digest"})
    with pytest.raises(AuthorityBindingValidationError, match="not signed-environment authority"):
        validate_candidate_binding(authority, kms, environment, tampered)


def test_missing_approval_is_review_only_and_never_promotable():
    authority, kms, environment, _ = _candidate()
    report = validate_candidate_binding(authority, kms, environment)
    assert report["approval_present"] is False
    assert report["production_promotable"] is False


def test_cli_validation_is_repository_only(capsys):
    assert _cli(["validate"]) == 0
    output = capsys.readouterr().out
    assert "blocked_pending_reviewed_authority_and_confidential_space_approval" in output
    assert '"signature_present":false' in output
