from __future__ import annotations

from dataclasses import replace

import pytest

from services.p5_r0_evaluator.canonical import b64encode, digest
from services.p5_r0_evaluator.confidential_space import (
    CapabilityFactory,
    ConfidentialSpaceAdapter,
    FederatedAccessToken,
    STSError,
)
from services.p5_r0_evaluator.deploy.signed_environment_process import (
    _issue_verified_capability_binding,
    SignedEnvironmentProcessError,
    validate_attested_activation,
    validate_capability_binding,
    validate_kms_binding,
    validate_local_contracts,
    validate_short_lived_capability,
    validate_signed_lock_result,
)
from services.p5_r0_evaluator.tests.test_confidential_space import (
    FakeGCSClient,
    FakeKMSClient,
    FakeSource,
    FakeVerifier,
    _claims,
    _config,
)


def test_locked_policy_cannot_select_non_amd_or_insecure_posture():
    config, _ = _config()
    with pytest.raises(ValueError, match="AMD_SEV"):
        replace(config, hardware_model="GCP_INTEL_TDX")
    with pytest.raises(ValueError, match="Secure Boot"):
        replace(config, secure_boot=False)


def test_local_contracts_remain_blocked_and_unsigned():
    report = validate_local_contracts()
    assert report.status == "blocked_pending_external_signed_environment_prerequisites"
    assert report.request_digest.startswith("sha256:")
    assert report.unsigned_lock_digest == "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"


def test_local_contracts_are_rerunnable_when_ignored_review_artifacts_are_absent(tmp_path):
    report = validate_local_contracts(request=tmp_path / "missing-request.json", rs068_proposal=tmp_path / "missing-proposal.json")
    assert report.status == "blocked_pending_local_review_inputs"
    assert report.rs068_proposal_digest is None
    assert report.unsigned_lock_digest.startswith("sha256:")


def test_kms_binding_requires_exact_public_key_version_and_self_custodied_authority():
    config, key = _config()
    public_key = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": "self-custodied/project/evaluator",
        "key_id": "evaluator-key",
        "public_key": public_key,
        "public_key_digest": digest(public_key),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1",
            "provider": config.wip_provider,
            "audience": config.attestation_audience,
            "event": "confidential_space_attestation",
        },
    }
    config = replace(config, authority=authority)
    binding = {
        "schema": "P5R0KMSAuthorityBindingV1",
        "authority_id": authority["authority_id"],
        "key_id": authority["key_id"],
        "kms_key_version": config.kms_key_version,
        "public_key_digest": authority["public_key_digest"],
        "purpose": "p5-r0-production-authority",
    }
    binding["binding_digest"] = digest(binding)
    kms = {
        "key_version": config.kms_key_version,
        "public_key": public_key,
        "public_key_digest": authority["public_key_digest"],
        "authority_binding": binding,
    }
    report = validate_kms_binding(authority, kms, config)
    assert report["kms_key_version"] == config.kms_key_version
    stale = dict(kms)
    stale["key_version"] = "projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/2"
    with pytest.raises(SignedEnvironmentProcessError, match="key version"):
        validate_kms_binding(authority, stale, config)


def test_capability_binding_requires_fresh_exact_external_state():
    config, _ = _config()
    config = replace(config, capability_service_account="p5-evaluator@project.iam.gserviceaccount.com")
    binding = {
        "schema": "P5R0SignedEnvironmentCapabilityBindingV1",
        "status": "verified_external_precondition",
        "provider": config.wip_provider,
        "image_digest": config.image_digest,
        "project_number": config.project_number,
        "project_id": config.project_id,
        "zone": config.zone,
        "principal": "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/attribute.image_digest/" + config.image_digest,
        "service_account": config.capability_service_account,
        "bucket": config.bucket,
        "prefix": config.prefix,
        "run_id": "dispatch-050-run",
        "iam": {
            "narrow_writer_verified": True,
            "broad_grant_absent": True,
            "token_creator_verified": True,
            "public_principals_absent": True,
        },
        "observation": {
            "fresh": True,
            "source": "reviewed_iac_remote_observation",
            "state_digest": "sha256:" + "d" * 64,
            "cloud_operations": [],
        },
    }
    verified = _issue_verified_capability_binding(binding, config)
    result = validate_capability_binding(verified, config)
    assert result["token_creator_verified"] is True

    stale = {**verified.as_public_dict(), "image_digest": "sha256:" + "e" * 64}
    with pytest.raises(SignedEnvironmentProcessError, match="verifier-issued"):
        validate_capability_binding(stale, config)  # type: ignore[arg-type]

    unresolved = {**verified.as_public_dict(), "observation": {**verified.as_public_dict()["observation"], "state_digest": None}}
    with pytest.raises(SignedEnvironmentProcessError, match="verifier-issued"):
        validate_capability_binding(unresolved, config)  # type: ignore[arg-type]


def test_short_lived_capability_rejects_adc_keys_and_source_overrun():
    source = FederatedAccessToken("source-token", 1_000 + 600)
    capability = FederatedAccessToken("capability-token", 1_000 + 300)
    receipt = validate_short_lived_capability(
        source, capability,
        source_token_digest=digest(source.access_token),
        capability_binding_digest=digest("binding"),
        service_account="p5-evaluator@project.iam.gserviceaccount.com",
        now=1_000,
    )
    assert receipt.token_digest.startswith("sha256:")
    with pytest.raises(SignedEnvironmentProcessError, match="explicit federated"):
        validate_short_lived_capability({"token": "adc"}, capability, source_token_digest="sha256:" + "0" * 64, capability_binding_digest="sha256:" + "1" * 64, service_account="p5-evaluator@project.iam.gserviceaccount.com", now=1_000)
    with pytest.raises(SignedEnvironmentProcessError, match="source-bounded"):
        validate_short_lived_capability(source, FederatedAccessToken("too-long", 1_000 + 601), source_token_digest=digest(source.access_token), capability_binding_digest=digest("binding"), service_account="p5-evaluator@project.iam.gserviceaccount.com", now=1_000)
    with pytest.raises(SignedEnvironmentProcessError, match="short-lived"):
        validate_short_lived_capability(source, FederatedAccessToken("expired", 1_030), source_token_digest=digest(source.access_token), capability_binding_digest=digest("binding"), service_account="p5-evaluator@project.iam.gserviceaccount.com", now=1_000)


def test_activation_rejects_federated_credential_longer_than_attestation():
    config, signing_key = _config()
    adapter = ConfidentialSpaceAdapter(
        config,
        source=FakeSource(),
        verifier=FakeVerifier(_claims(config)),
        sts=type("OverlongSTS", (), {"exchange": lambda self, **_kwargs: FederatedAccessToken("federated", 2_001)})(),
        capability_factory=CapabilityFactory(
            config,
            storage_client_factory=lambda _token: FakeGCSClient(),
            kms_client_factory=lambda _token: FakeKMSClient(signing_key),
        ),
        service_factory=lambda _capabilities: object(),
    )
    with pytest.raises(STSError, match="attestation lifetime"):
        adapter.activate_attested_service()
    assert adapter.attested is False


def test_attestation_receipt_requires_real_adapter_evidence_and_smoke_claim():
    config, signing_key = _config()
    adapter = ConfidentialSpaceAdapter(
        config,
        source=FakeSource(),
        verifier=FakeVerifier(_claims(config)),
        sts=type("BoundedSTS", (), {"exchange": lambda self, **_kwargs: FederatedAccessToken("federated", 1_200)})(),
        capability_factory=CapabilityFactory(
            config,
            storage_client_factory=lambda _token: FakeGCSClient(),
            kms_client_factory=lambda _token: FakeKMSClient(signing_key),
        ),
        service_factory=lambda _capabilities: object(),
    )
    adapter.activate_attested_service()
    receipt = validate_attested_activation(adapter)
    assert receipt.image_digest == config.image_digest
    assert receipt.provider == config.wip_provider
    assert receipt.expires_at == 2_000

    adapter._startup_evidence["attestation"]["fixed_claims"].pop("smoke")
    with pytest.raises(SignedEnvironmentProcessError, match="fixed-claim"):
        validate_attested_activation(adapter)

    forged = dict(adapter.startup_evidence)
    forged["attestation"] = dict(forged["attestation"])
    forged["attestation"]["fixed_claims"] = dict(forged["attestation"]["fixed_claims"])
    forged["attestation"]["fixed_claims"].pop("smoke", None)
    adapter.startup_evidence  # receipt remains owned by the adapter; forged mappings are not accepted
    with pytest.raises(SignedEnvironmentProcessError, match="adapter"):
        validate_attested_activation(forged)  # type: ignore[arg-type]


def test_signed_result_is_consumed_only_and_rejects_caller_boolean():
    with pytest.raises(SignedEnvironmentProcessError, match="adapter"):
        validate_signed_lock_result({"attested": True}, {"signature": "caller"})



def test_attestation_binding_mutation_or_forged_mapping_cannot_promote_activation():
    config, signing_key = _config()
    adapter = ConfidentialSpaceAdapter(
        config,
        source=FakeSource(),
        verifier=FakeVerifier(_claims(config)),
        sts=type("BoundedSTS", (), {"exchange": lambda self, **_: FederatedAccessToken("federated", 1_200)})(),
        capability_factory=CapabilityFactory(
            config,
            storage_client_factory=lambda _token: FakeGCSClient(),
            kms_client_factory=lambda _token: FakeKMSClient(signing_key),
        ),
        service_factory=lambda _capabilities: object(),
    )
    adapter.activate_attested_service()
    binding = adapter.attestation_binding
    assert binding is not None
    object.__setattr__(binding, "image_digest", "sha256:" + "f" * 64)
    with pytest.raises(SignedEnvironmentProcessError, match="adapter-issued"):
        validate_attested_activation(adapter)
    with pytest.raises(SignedEnvironmentProcessError, match="adapter"):
        validate_attested_activation({"attested": True})  # type: ignore[arg-type]
