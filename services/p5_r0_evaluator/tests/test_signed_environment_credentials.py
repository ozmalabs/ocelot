from __future__ import annotations

from dataclasses import replace

import pytest

from services.p5_r0_evaluator.canonical import b64encode, digest
from services.p5_r0_evaluator.confidential_space import Capabilities, ConfidentialSpaceAdapter, FederatedAccessToken, LauncherTokenSource
from services.p5_r0_evaluator.deploy.signed_environment_credentials import (
    CredentialOnlyCapabilityFactory,
    CredentialProcessError,
    _issue_verified_child_approval,
    VerifiedCredentialChildApproval,
    bootstrap_credentials,
    build_execution_request,
    validate_child_approval,
    validate_execution_request,
    validate_receipt,
)
from services.p5_r0_evaluator.deploy.signed_environment_process import _issue_verified_capability_binding, validate_short_lived_capability
from services.p5_r0_evaluator.tests.test_confidential_space import FakeSource, FakeVerifier, _claims, _config

from services.p5_r0_evaluator.deploy.track_a_bootstrap_runner import CANONICAL_PACKET_PATH


PACKET_DIGEST = digest("canonical-approval-016-packet")
PACKET_PATH = CANONICAL_PACKET_PATH


def _build_request(config, kms, capability_binding):
    return build_execution_request(
        config=config, kms=kms, capability_binding=capability_binding,
        packet_digest=PACKET_DIGEST, packet_path=PACKET_PATH,
    )

def _reviewed_inputs(config):
    # The test config does not retain its signing key, so use a fresh authority
    # key and bind the exact public value into both config and the KMS report.
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": "self-custodied/ocelot-proof/evaluator",
        "key_id": "evaluator-key-v4",
        "public_key": public,
        "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1",
            "provider": config.wip_provider,
            "audience": config.attestation_audience,
            "event": "confidential_space_attestation",
        },
    }
    config = replace(config, authority=authority, capability_service_account="p5-r0-gcs-only@project.iam.gserviceaccount.com")
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
        "public_key": public,
        "public_key_digest": authority["public_key_digest"],
        "authority_binding": binding,
    }
    capability_binding = {
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
    return config, authority, kms, _issue_verified_capability_binding(capability_binding, config)


def _approval(request):
    return _issue_verified_child_approval(request, issued_at=1_000, expires_at=1_200)


def _adapter(config, *, binding_digest, effective_expiry=1_150, source=None):
    def impersonate(source):
        assert source.access_token == "federated-source"
        return FederatedAccessToken("iam-effective-token", effective_expiry)

    factory = CredentialOnlyCapabilityFactory(
        config,
        capability_binding_digest=binding_digest,
        impersonation_factory=impersonate,
    )
    return ConfidentialSpaceAdapter(
        config,
        source=source or FakeSource(),
        verifier=FakeVerifier(_claims(config)),
        sts=type("STS", (), {"exchange": lambda self, **_: FederatedAccessToken("federated-source", 1_200)})(),
        capability_factory=factory,
        service_factory=lambda capabilities: object(),
    )



class _LauncherSocket:
    def __init__(self, response):
        self.response = response
        self.sent = b""
        self.closed = False

    def settimeout(self, value):
        assert value == 5

    def connect(self, path):
        assert path == "/run/container_launcher/teeserver.sock"

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        value, self.response = self.response, b""
        return value[:size] if value else b""

    def close(self):
        self.closed = True


def test_bootstrap_uses_shared_launcher_socket_protocol():
    config, _ = _config()
    config, authority, kms, capability_binding = _reviewed_inputs(config)
    request = _build_request(config, kms, capability_binding)
    approval = _approval(request)
    assert approval.as_public_dict()["packet_digest"] == PACKET_DIGEST
    assert approval.as_public_dict()["packet_path"] == PACKET_PATH
    socket = _LauncherSocket(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 17\r\n\r\n"
        b'{"token":"h.p.s"}'
    )
    source = LauncherTokenSource(socket_factory=lambda *_: socket)
    adapter = _adapter(config, binding_digest=capability_binding.binding_digest, source=source)
    receipt = bootstrap_credentials(
        adapter=adapter, authority=authority, kms=kms,
        capability_binding=capability_binding,
        request=request.as_public_dict(), child_approval=approval,
    )
    sent = socket.sent.decode("ascii")
    assert "POST /v1/token HTTP/1.1" in sent
    assert '"audience":"https://sts.googleapis.com"' in sent
    assert '"nonces":["nonce-1234"]' in sent
    assert receipt.as_public_dict()["attestation_token_digest"] == digest("h.p.s")
    assert "h.p.s" not in str(receipt.as_public_dict())


def test_bootstrap_uses_adapter_evidence_and_emits_only_redacted_receipt():
    config, _ = _config()
    config, authority, kms, capability_binding = _reviewed_inputs(config)
    request = _build_request(config, kms, capability_binding)
    approval = _approval(request)
    adapter = _adapter(config, binding_digest=capability_binding.binding_digest)

    receipt = bootstrap_credentials(
        adapter=adapter, authority=authority, kms=kms,
        capability_binding=capability_binding,
        request=request.as_public_dict(), child_approval=approval,
    )

    public = receipt.as_public_dict()
    assert validate_receipt(receipt, now=1_000)["nonce_digest"].startswith("sha256:")
    assert public["schema"] == "P5R0CredentialBootstrapReceiptV2"
    assert public["provider"] == config.wip_provider
    assert public["image_digest"] == config.image_digest
    assert public["project_number"] == config.project_number
    assert public["zone"] == config.zone
    assert public["tee"] == "CONFIDENTIAL_SPACE"
    assert public["hardware_model"] == "GCP_AMD_SEV"
    assert public["secure_boot"] is True
    assert public["debug_state"] == "disabled-since-boot"
    assert public["workload"] == "evaluator"
    assert public["smoke"] == "0"
    assert public["cloud_operations"] == []
    assert public["credentials_exported"] is False
    assert public["contains_key_material"] is False
    assert "federated-source" not in str(public)
    assert "iam-effective-token" not in str(public)
    assert "attestation-token" not in str(public)

    with pytest.raises(CredentialProcessError, match="packet digest"):
        validate_receipt(receipt, now=1_000, packet_digest=digest("wrong-packet"))

    # Adapter activation and receipt issuance are rerunnable/idempotent; the
    # second call does not fetch another launcher token or derive another token.
    second = bootstrap_credentials(
        adapter=adapter, authority=authority, kms=kms,
        capability_binding=capability_binding,
        request=request.as_public_dict(), child_approval=approval,
    )
    assert second.receipt_digest == receipt.receipt_digest
    assert len(adapter.gate.source.calls) == 1


def test_bootstrap_rejects_request_or_kms_binding_drift_before_launcher():
    config, _ = _config()
    config, authority, kms, capability_binding = _reviewed_inputs(config)
    request = _build_request(config, kms, capability_binding)
    approval = _approval(request)
    adapter = _adapter(config, binding_digest=capability_binding.binding_digest)

    changed = request.as_public_dict()
    changed["zone"] = "us-east1-b"
    with pytest.raises(CredentialProcessError, match="request digest"):
        bootstrap_credentials(
            adapter=adapter, authority=authority, kms=kms,
            capability_binding=capability_binding, request=changed,
            child_approval=approval,
        )
    assert adapter.gate.source.calls == []

    stale_kms = dict(kms)
    stale_kms["key_version"] = "projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/2"
    with pytest.raises(Exception, match="key version"):
        _build_request(config, stale_kms, capability_binding)


def test_child_approval_is_external_and_never_treated_as_applied():
    config, _ = _config()
    config, _, kms, capability_binding = _reviewed_inputs(config)
    request = _build_request(config, kms, capability_binding)
    approval = _approval(request)
    assert validate_child_approval(approval, request=request, now=1_000)["parent_approval_id"] == "P5-MASTER-001/APPROVAL-013"
    object.__setattr__(approval, "request_digest", digest("attacker-request"))
    with pytest.raises(CredentialProcessError, match="verifier-issued"):
        validate_child_approval(approval, request=request, now=1_000)
    approval = _approval(request)
    object.__setattr__(approval, "packet_path", "/tmp/altered-packet.json")
    with pytest.raises(CredentialProcessError, match="verifier-issued"):
        validate_child_approval(approval, request=request, now=1_000)


def test_credential_only_factory_rejects_source_overrun():
    config, _ = _config()
    config, _, _, capability_binding = _reviewed_inputs(config)
    factory = CredentialOnlyCapabilityFactory(
        config,
        capability_binding_digest=capability_binding.binding_digest,
        impersonation_factory=lambda _: FederatedAccessToken("too-long", 1_201),
    )
    with pytest.raises(Exception, match="source-bounded"):
        factory.build(FederatedAccessToken("source", 1_200))



def test_non_credential_factory_is_rejected_before_launcher_activation():
    config, _ = _config()
    config, authority, kms, capability_binding = _reviewed_inputs(config)
    request = _build_request(config, kms, capability_binding)
    approval = _approval(request)
    source = FakeSource()

    class WrongFactory:
        def build(self, token):
            raise AssertionError("ordinary capability factory must not be called")

    adapter = ConfidentialSpaceAdapter(
        config,
        source=source,
        verifier=FakeVerifier(_claims(config)),
        sts=type("STS", (), {"exchange": lambda self, **_: FederatedAccessToken("federated-source", 1_200)})(),
        capability_factory=WrongFactory(),
        service_factory=lambda capabilities: object(),
    )
    with pytest.raises(CredentialProcessError, match="credential-only capability factory"):
        bootstrap_credentials(
            adapter=adapter, authority=authority, kms=kms,
            capability_binding=capability_binding,
            request=request.as_public_dict(), child_approval=approval,
        )
    assert source.calls == []



def test_receipt_is_rebound_to_live_source_and_target():
    config, _ = _config()
    config, authority, kms, capability_binding = _reviewed_inputs(config)
    request = _build_request(config, kms, capability_binding)
    approval = _approval(request)
    adapter = _adapter(config, binding_digest=capability_binding.binding_digest)
    bootstrap_credentials(
        adapter=adapter, authority=authority, kms=kms,
        capability_binding=capability_binding,
        request=request.as_public_dict(), child_approval=approval,
    )
    forged = validate_short_lived_capability(
        FederatedAccessToken("other-source", 1_200),
        FederatedAccessToken("other-effective", 1_150),
        source_token_digest=digest("other-source"),
        capability_binding_digest=capability_binding.binding_digest,
        service_account=config.capability_service_account,
        now=1_000,
    )
    adapter.capability_factory._receipt = forged
    with pytest.raises(CredentialProcessError, match="live STS activation"):
        bootstrap_credentials(
            adapter=adapter, authority=authority, kms=kms,
            capability_binding=capability_binding,
            request=request.as_public_dict(), child_approval=approval,
        )



def test_self_digested_child_approval_mapping_is_not_verifier_evidence():
    config, _ = _config()
    config, _, kms, capability_binding = _reviewed_inputs(config)
    request = _build_request(config, kms, capability_binding)
    forged = {
        "schema": "P5R0SignedEnvironmentCredentialChildApprovalV1",
        "approval_id": "attacker-approved",
        "operation_id": "bootstrap_signed_environment_credentials",
        "scope": ["bootstrap_signed_environment_credentials"],
        "status": "approved_single_operation_pending_apply",
        "request_digest": request.request_digest,
        "approval_source": "confidential_space_attestation",
        "attestation_verified": True,
        "local_execution": False,
        "cloud_operations": [],
    }
    forged["approval_digest"] = digest(forged)
    with pytest.raises(CredentialProcessError, match="verifier-issued"):
        validate_child_approval(forged, request=request, now=1_000)  # type: ignore[arg-type]


def test_capability_snapshot_reseal_and_mapping_are_rejected():
    config, _ = _config()
    config, _, kms, capability_binding = _reviewed_inputs(config)
    mapping = capability_binding.as_public_dict()
    object.__setattr__(capability_binding, "binding_digest", digest("attacker-binding"))
    with pytest.raises(Exception, match="verifier-issued"):
        _build_request(config, kms, capability_binding)
    with pytest.raises(Exception, match="verifier-issued"):
        _build_request(config, kms, mapping)  # type: ignore[arg-type]


def test_credential_only_factory_matches_capabilities_contract_without_service_handoff():
    config, _ = _config()
    config, _, kms, capability_binding = _reviewed_inputs(config)
    called = []
    adapter = _adapter(config, binding_digest=capability_binding.binding_digest)
    adapter.service_factory = lambda _capabilities: called.append(True) or (_ for _ in ()).throw(AssertionError("service factory must not run during credential bootstrap"))
    capabilities = adapter.activate_attested_capabilities()
    assert isinstance(capabilities, Capabilities)
    assert capabilities.credentials_expires_at == 1_150
    assert called == []
