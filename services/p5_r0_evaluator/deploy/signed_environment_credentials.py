"""Review-only Confidential Space/WIF credential bootstrap boundary.

This module is the smallest executable boundary between reviewed external
inputs and the existing ConfidentialSpaceAdapter.  It does not apply IAM,
create cloud resources, sign, upload, or execute diagnostics.  The adapter
remains the sole owner of launcher-token verification and the only source of
attestation evidence; this module only composes its redacted receipt with
reviewed KMS/capability bindings.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import time
from typing import Any, Callable, Mapping

from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.confidential_space import (
    Capabilities,
    ConfidentialSpaceAdapter,
    FederatedAccessToken,
    LockedBootstrapConfig,
)
from services.p5_r0_evaluator.deploy.signed_environment_process import (
    CapabilityReceipt,
    VerifiedCapabilityBinding,
    _is_registered_capability_receipt,
    activate_after_external_preflight,
    validate_attested_activation,
    validate_capability_binding,
    validate_kms_binding,
    validate_short_lived_capability,
)

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SERVICE_ACCOUNT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}@[a-z][a-z0-9-]{4,29}\.iam\.gserviceaccount\.com$")
_PROVIDER_RE = re.compile(r"^//iam\.googleapis\.com/projects/(?P<number>[0-9]+)/locations/global/workloadIdentityPools/(?P<pool>[a-z0-9-]+)/providers/(?P<provider>[a-z0-9-]+)$")
_OPERATION_ID = "bootstrap_signed_environment_credentials"
_FORBIDDEN = (
    "cloud_mutation",
    "credential_export",
    "kms_signing",
    "gcs_upload",
    "diagnostic_execution",
)


class CredentialProcessError(ValueError):
    """A reviewed credential process input or result is not admissible."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CredentialProcessError(message)


def _is_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} must be a sha256 digest")
    return value


def _closed_digest(value: Mapping[str, Any], field: str) -> str:
    _is_digest(value.get(field), field)
    return digest({key: item for key, item in value.items() if key != field})


def _expected_claims(config: LockedBootstrapConfig) -> dict[str, Any]:
    return {
        "provider": config.wip_provider,
        "audience": config.attestation_audience,
        "image_digest": config.image_digest,
        "project_number": config.project_number,
        "project_id": config.project_id,
        "zone": config.zone,
        "tee": config.tee,
        "hardware_model": config.hardware_model,
        "secure_boot": config.secure_boot,
        "debug_state": config.debug_state,
        "workload": config.workload,
        "smoke": "1" if config.confidential_space_smoke else "0",
    }


def _expected_principal(config: LockedBootstrapConfig) -> str:
    match = _PROVIDER_RE.fullmatch(config.wip_provider)
    _require(match is not None, "WIP provider is not canonical")
    return f"principalSet://iam.googleapis.com/projects/{match.group('number')}/locations/global/workloadIdentityPools/{match.group('pool')}/attribute.image_digest/{config.image_digest}"


@dataclass(frozen=True)
class CredentialExecutionRequest:
    """Canonical, non-executable request for one credential bootstrap."""

    schema: str
    operation_id: str
    scope: tuple[str, ...]
    status: str
    provider: str
    audience: str
    image_digest: str
    project_number: str
    project_id: str
    zone: str
    tee: str
    hardware_model: str
    secure_boot: bool
    debug_state: str
    workload: str
    smoke: str
    kms_key_version: str
    authority_binding_digest: str
    capability_binding_digest: str
    principal: str
    service_account: str
    bucket: str
    prefix: str
    run_id: str
    forbidden_operations: tuple[str, ...]
    cloud_operations: tuple[str, ...]
    mutations_performed: bool
    local_signatures_created: bool
    packet_digest: str
    packet_path: str
    request_digest: str

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "operation_id": self.operation_id,
            "scope": list(self.scope),
            "status": self.status,
            "provider": self.provider,
            "audience": self.audience,
            "image_digest": self.image_digest,
            "project_number": self.project_number,
            "project_id": self.project_id,
            "zone": self.zone,
            "tee": self.tee,
            "hardware_model": self.hardware_model,
            "secure_boot": self.secure_boot,
            "debug_state": self.debug_state,
            "workload": self.workload,
            "smoke": self.smoke,
            "kms_key_version": self.kms_key_version,
            "authority_binding_digest": self.authority_binding_digest,
            "capability_binding_digest": self.capability_binding_digest,
            "principal": self.principal,
            "service_account": self.service_account,
            "bucket": self.bucket,
            "prefix": self.prefix,
            "run_id": self.run_id,
            "forbidden_operations": list(self.forbidden_operations),
            "cloud_operations": list(self.cloud_operations),
            "mutations_performed": self.mutations_performed,
            "local_signatures_created": self.local_signatures_created,
            "packet_digest": self.packet_digest,
            "packet_path": self.packet_path,
            "request_digest": self.request_digest,
        }




_APPROVAL_SEAL = object()
_APPROVAL_REGISTRY: dict[int, tuple["VerifiedCredentialChildApproval", tuple[Any, ...]]] = {}
_APPROVAL_FIELDS = (
    "schema", "approval_id", "operation_id", "scope", "status", "packet_digest", "packet_path", "request_digest",
    "parent_approval_id", "verifier_id", "issued_at", "expires_at", "approval_digest",
)


@dataclass(frozen=True, init=False)
class VerifiedCredentialChildApproval:
    """Verifier-issued one-operation approval bound to one exact request.

    Approval mappings are deliberately not accepted.  The registry snapshot
    prevents object copying or mutation/reseal from becoming an approval.
    """

    schema: str
    approval_id: str
    operation_id: str
    scope: tuple[str, ...]
    status: str
    packet_digest: str
    packet_path: str
    request_digest: str
    parent_approval_id: str
    verifier_id: str
    issued_at: int
    expires_at: int
    approval_digest: str

    def __init__(self, **values: Any) -> None:
        _require(values.pop("_seal", None) is _APPROVAL_SEAL, "credential child approval is verifier-created")
        _require(set(values) == set(_APPROVAL_FIELDS), "credential child approval fields are closed")
        for field in _APPROVAL_FIELDS:
            object.__setattr__(self, field, tuple(values[field]) if field == "scope" else values[field])

    def as_public_dict(self) -> dict[str, Any]:
        _require(_is_registered_approval(self), "credential child approval is not verifier-issued")
        return {field: (list(getattr(self, field)) if field == "scope" else getattr(self, field)) for field in _APPROVAL_FIELDS}


def _approval_snapshot(value: VerifiedCredentialChildApproval) -> tuple[Any, ...]:
    return tuple(getattr(value, field) for field in _APPROVAL_FIELDS)


def _is_registered_approval(value: Any) -> bool:
    return type(value) is VerifiedCredentialChildApproval and id(value) in _APPROVAL_REGISTRY and _APPROVAL_REGISTRY[id(value)][0] is value and _approval_snapshot(value) == _APPROVAL_REGISTRY[id(value)][1]


def _issue_verified_child_approval(request: CredentialExecutionRequest, *, issued_at: int, expires_at: int) -> VerifiedCredentialChildApproval:
    """Verifier-side fixture/receipt issuance; production receives this object."""
    _require(type(issued_at) is int and type(expires_at) is int and expires_at > issued_at, "credential approval lifetime is invalid")
    values: dict[str, Any] = {
        "schema": "P5R0SignedEnvironmentCredentialChildApprovalV3",
        "approval_id": "P5-MASTER-001/APPROVAL-013-CREDENTIALS",
        "operation_id": _OPERATION_ID,
        "scope": [_OPERATION_ID],
        "status": "approved_single_operation_pending_apply",
        "packet_digest": request.packet_digest,
        "packet_path": request.packet_path,
        "request_digest": request.request_digest,
        "parent_approval_id": "P5-MASTER-001/APPROVAL-013",
        "verifier_id": "confidential-space-verifier",
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    values["approval_digest"] = digest(values)
    approval = VerifiedCredentialChildApproval(**values, _seal=_APPROVAL_SEAL)
    _APPROVAL_REGISTRY[id(approval)] = (approval, _approval_snapshot(approval))
    return approval


def build_execution_request(*, config: LockedBootstrapConfig, kms: Mapping[str, Any], capability_binding: VerifiedCapabilityBinding, packet_digest: str, packet_path: str) -> CredentialExecutionRequest:
    """Build a review artifact; this never means that the request was applied."""
    _is_digest(packet_digest, "canonical packet digest")
    _require(isinstance(packet_path, str) and packet_path.startswith("/"), "canonical packet path is invalid")
    report = validate_kms_binding(config.authority, kms, config)
    validate_capability_binding(capability_binding, config)
    binding = kms["authority_binding"]
    public_binding = capability_binding.as_public_dict()
    values: dict[str, Any] = {
        "schema": "P5R0SignedEnvironmentCredentialExecutionRequestV2",
        "operation_id": _OPERATION_ID,
        "scope": [_OPERATION_ID],
        "status": "blocked_pending_external_signed_environment",
        **_expected_claims(config),
        "kms_key_version": report["kms_key_version"],
        "authority_binding_digest": binding["binding_digest"],
        "capability_binding_digest": capability_binding.binding_digest,
        "principal": public_binding["principal"],
        "service_account": public_binding["service_account"],
        "bucket": public_binding["bucket"],
        "prefix": public_binding["prefix"],
        "run_id": public_binding["run_id"],
        "forbidden_operations": list(_FORBIDDEN),
        "cloud_operations": [],
        "mutations_performed": False,
        "local_signatures_created": False,
        "packet_digest": packet_digest,
        "packet_path": packet_path,
    }
    values["request_digest"] = digest(values)
    return _request_from_mapping(values)


def _request_from_mapping(value: Mapping[str, Any]) -> CredentialExecutionRequest:
    expected = {
        "schema", "operation_id", "scope", "status", "provider", "audience",
        "image_digest", "project_number", "project_id", "zone", "tee",
        "hardware_model", "secure_boot", "debug_state", "workload", "smoke",
        "kms_key_version", "authority_binding_digest", "capability_binding_digest",
        "principal", "service_account", "bucket", "prefix", "run_id", "forbidden_operations",
        "cloud_operations", "mutations_performed", "local_signatures_created", "packet_digest", "packet_path",
        "request_digest",
    }
    _require(set(value) == expected, "credential execution request is not closed")
    _require(value["schema"] == "P5R0SignedEnvironmentCredentialExecutionRequestV2", "credential execution request schema drift")
    _require(value["operation_id"] == _OPERATION_ID and value["scope"] == [_OPERATION_ID], "credential execution scope drift")
    _require(value["status"] == "blocked_pending_external_signed_environment", "credential execution request must remain blocked")
    _require(value["forbidden_operations"] == list(_FORBIDDEN) and value["cloud_operations"] == [], "credential request operation boundary drift")
    _require(value["mutations_performed"] is False and value["local_signatures_created"] is False, "credential request crossed a local apply boundary")
    _is_digest(value["image_digest"], "image digest")
    _is_digest(value["authority_binding_digest"], "authority binding digest")
    _is_digest(value["capability_binding_digest"], "capability binding digest")
    _is_digest(value["packet_digest"], "canonical packet digest")
    _require(isinstance(value["packet_path"], str) and value["packet_path"].startswith("/"), "canonical packet path is invalid")
    _require(isinstance(value["principal"], str) and value["principal"].startswith("principalSet://"), "credential request WIF principal is invalid")
    _require(isinstance(value["service_account"], str) and _SERVICE_ACCOUNT_RE.fullmatch(value["service_account"]) is not None, "credential request service account is invalid")
    _require(value["request_digest"] == _closed_digest(value, "request_digest"), "credential request digest mismatch")
    _require(isinstance(value["scope"], list) and all(isinstance(item, str) for item in value["scope"]), "credential scope is malformed")
    return CredentialExecutionRequest(
        schema=value["schema"], operation_id=value["operation_id"], scope=tuple(value["scope"]),
        status=value["status"], provider=value["provider"], audience=value["audience"],
        image_digest=value["image_digest"], project_number=value["project_number"],
        project_id=value["project_id"], zone=value["zone"], tee=value["tee"],
        hardware_model=value["hardware_model"], secure_boot=value["secure_boot"],
        debug_state=value["debug_state"], workload=value["workload"], smoke=value["smoke"],
        kms_key_version=value["kms_key_version"], authority_binding_digest=value["authority_binding_digest"],
        capability_binding_digest=value["capability_binding_digest"], principal=value["principal"],
        service_account=value["service_account"], bucket=value["bucket"], prefix=value["prefix"], run_id=value["run_id"],
        forbidden_operations=tuple(value["forbidden_operations"]), cloud_operations=tuple(value["cloud_operations"]),
        mutations_performed=value["mutations_performed"], local_signatures_created=value["local_signatures_created"],
        packet_digest=value["packet_digest"], packet_path=value["packet_path"], request_digest=value["request_digest"],
    )


def validate_execution_request(request: Mapping[str, Any], *, config: LockedBootstrapConfig, kms: Mapping[str, Any], capability_binding: VerifiedCapabilityBinding, packet_digest: str, packet_path: str) -> CredentialExecutionRequest:
    checked = _request_from_mapping(request)
    expected = build_execution_request(config=config, kms=kms, capability_binding=capability_binding, packet_digest=packet_digest, packet_path=packet_path)
    _require(checked == expected, "credential execution request is not bound to the exact reviewed environment")
    return checked


def validate_child_approval(approval: VerifiedCredentialChildApproval, *, request: CredentialExecutionRequest, now: int | None = None) -> dict[str, Any]:
    """Validate only a verifier-issued, parent-bound one-operation approval."""
    _require(_is_registered_approval(approval), "credential child approval is not verifier-issued")
    public = approval.as_public_dict()
    _require(public["schema"] == "P5R0SignedEnvironmentCredentialChildApprovalV3", "credential child approval schema drift")
    _require(public["operation_id"] == _OPERATION_ID and public["scope"] == [_OPERATION_ID], "credential child approval scope drift")
    _is_digest(public["packet_digest"], "canonical packet digest")
    _require(isinstance(public["packet_path"], str) and public["packet_path"].startswith("/"), "canonical packet path is invalid")
    _require(public["packet_digest"] == request.packet_digest and public["packet_path"] == request.packet_path, "credential child approval packet binding drift")
    _require(public["status"] == "approved_single_operation_pending_apply", "credential child approval is not ready")
    _require(public["request_digest"] == request.request_digest, "credential child approval request binding drift")
    _require(public["parent_approval_id"] == "P5-MASTER-001/APPROVAL-013" and public["verifier_id"] == "confidential-space-verifier", "credential child approval provenance is not verified")
    _require(type(public["issued_at"]) is int and type(public["expires_at"]) is int, "credential child approval lifetime is invalid")
    clock = int(time.time()) if now is None else now
    _require(type(clock) is int and public["issued_at"] <= clock + 30 and public["expires_at"] > clock, "credential child approval is expired")
    _require(public["approval_digest"] == _closed_digest(public, "approval_digest"), "credential child approval digest mismatch")
    return public


class _CredentialOnlyUnavailable:
    """Contract placeholder; credential bootstrap cannot expose evaluator clients."""

    def __getattr__(self, name: str) -> Any:
        raise CredentialProcessError(f"credential-only capability has no evaluator {name}")


class CredentialOnlyCapabilityFactory:
    """Satisfy the adapter capability contract without GCS/KMS clients."""

    def __init__(self, config: LockedBootstrapConfig, *, capability_binding_digest: str, impersonation_factory: Callable[[FederatedAccessToken], FederatedAccessToken] | None = None):
        _is_digest(capability_binding_digest, "capability binding digest")
        _require(config.capability_service_account is not None and _SERVICE_ACCOUNT_RE.fullmatch(config.capability_service_account) is not None, "credential service account is required")
        self.config = config
        self.capability_binding_digest = capability_binding_digest
        self.impersonation_factory = impersonation_factory
        self._receipt: CapabilityReceipt | None = None

    @property
    def capability_receipt(self) -> CapabilityReceipt | None:
        return self._receipt

    def _impersonate(self, source: FederatedAccessToken) -> FederatedAccessToken:
        if self.impersonation_factory is not None:
            result = self.impersonation_factory(source)
        else:
            from services.p5_r0_evaluator.timing_bridge_auth import IAMCredentialsAccessTokenFactory, IAMCredentialsError
            try:
                result = IAMCredentialsAccessTokenFactory(self.config.capability_service_account or "", source)()
            except IAMCredentialsError as exc:
                raise CredentialProcessError("reviewed IAM credential derivation failed") from exc
        _require(isinstance(result, FederatedAccessToken), "IAM credential derivation returned an invalid token")
        return result

    def build(self, source: FederatedAccessToken) -> Capabilities:
        _require(isinstance(source, FederatedAccessToken), "explicit STS source credential is required")
        _require(source.token_type == "Bearer" and bool(source.access_token), "explicit STS source credential is invalid")
        _require(type(source.expires_at) is int and source.expires_at > int(self.config.clock()) + 30, "federated source credential is expired")
        effective = self._impersonate(source)
        self._receipt = validate_short_lived_capability(
            source, effective,
            source_token_digest=digest(source.access_token),
            capability_binding_digest=self.capability_binding_digest,
            service_account=self.config.capability_service_account or "",
            now=int(self.config.clock()),
        )
        # Return the adapter's declared Capabilities contract, but populate it
        # with fail-closed placeholders.  Bootstrap uses capability-only
        # activation, so these can never become evaluator clients or signers.
        return Capabilities(
            store=_CredentialOnlyUnavailable(),
            signer=_CredentialOnlyUnavailable(),
            timing_attestor=_CredentialOnlyUnavailable(),
            credentials_expires_at=effective.expires_at,
        )


_RECEIPT_SEAL = object()
_RECEIPT_REGISTRY: dict[int, tuple["CredentialBootstrapReceipt", tuple[Any, ...]]] = {}
_RECEIPT_FIELDS = (
    "request_digest", "packet_digest", "packet_path", "approval_digest", "provider", "audience", "image_digest",
    "project_number", "project_id", "zone", "tee", "hardware_model", "secure_boot",
    "debug_state", "workload", "smoke", "attestation_binding_digest",
    "attestation_claims_digest", "attestation_token_digest", "nonce_digest",
    "attestation_issued_at", "attestation_expires_at", "federated_token_digest",
    "capability_receipt_digest", "capability_binding_digest", "kms_key_version",
    "kms_public_key_digest", "authority_id", "key_id", "kms_authority_binding_digest", "source_expires_at",
    "expires_at", "cloud_operations", "credentials_exported", "contains_key_material",
)


@dataclass(frozen=True, init=False)
class CredentialBootstrapReceipt:
    """Verifier-owned redacted receipt; raw JWTs and access tokens are absent."""

    schema: str
    request_digest: str
    packet_digest: str
    packet_path: str
    approval_digest: str
    provider: str
    audience: str
    image_digest: str
    project_number: str
    project_id: str
    zone: str
    tee: str
    hardware_model: str
    secure_boot: bool
    debug_state: str
    workload: str
    smoke: str
    attestation_binding_digest: str
    attestation_claims_digest: str
    attestation_token_digest: str
    nonce_digest: str
    attestation_issued_at: int
    attestation_expires_at: int
    federated_token_digest: str
    capability_receipt_digest: str
    capability_binding_digest: str
    kms_key_version: str
    kms_public_key_digest: str
    authority_id: str
    key_id: str
    kms_authority_binding_digest: str
    source_expires_at: int
    expires_at: int
    cloud_operations: tuple[str, ...]
    credentials_exported: bool
    contains_key_material: bool
    receipt_digest: str

    def __init__(self, **values: Any) -> None:
        _require(values.pop("_seal", None) is _RECEIPT_SEAL, "credential bootstrap receipt is verifier-created")
        _require(set(values) == set(self.__dataclass_fields__), "credential bootstrap receipt is not closed")
        for field in self.__dataclass_fields__:
            value = values[field]
            object.__setattr__(self, field, tuple(value) if field == "cloud_operations" else value)

    def as_public_dict(self) -> dict[str, Any]:
        _require(_is_registered_receipt(self), "credential bootstrap receipt is not verifier-issued")
        return {"schema": self.schema, **{field: (list(getattr(self, field)) if field == "cloud_operations" else getattr(self, field)) for field in self.__dataclass_fields__}}


def _receipt_digest(values: Mapping[str, Any]) -> str:
    return digest({"schema": "P5R0CredentialBootstrapReceiptV2", **{field: values[field] for field in _RECEIPT_FIELDS}})


def _is_registered_receipt(value: Any) -> bool:
    return type(value) is CredentialBootstrapReceipt and id(value) in _RECEIPT_REGISTRY and _RECEIPT_REGISTRY[id(value)][0] is value and tuple(getattr(value, field) for field in value.__dataclass_fields__) == _RECEIPT_REGISTRY[id(value)][1]


def _build_receipt(*, request: CredentialExecutionRequest, approval: Mapping[str, Any], config: LockedBootstrapConfig, kms: Mapping[str, Any], adapter: ConfidentialSpaceAdapter, activation: Any, capability_receipt: CapabilityReceipt) -> CredentialBootstrapReceipt:
    _require(_is_registered_capability_receipt(capability_receipt), "capability receipt is not verifier-issued")
    binding = kms["authority_binding"]
    values: dict[str, Any] = {
        "schema": "P5R0CredentialBootstrapReceiptV2",
        "request_digest": request.request_digest,
        "packet_digest": request.packet_digest,
        "packet_path": request.packet_path,
        "approval_digest": approval["approval_digest"],
        **_expected_claims(config),
        "attestation_binding_digest": activation.binding_digest,
        "attestation_claims_digest": activation.claims_digest,
        "attestation_token_digest": activation.attestation_token_digest,
        "nonce_digest": adapter.startup_evidence["attestation"]["nonce_digest"],
        "attestation_issued_at": activation.issued_at,
        "attestation_expires_at": activation.expires_at,
        "federated_token_digest": activation.federated_token_digest,
        "capability_receipt_digest": capability_receipt.seal_digest,
        "capability_binding_digest": capability_receipt.capability_binding_digest,
        "kms_key_version": kms["key_version"],
        "kms_public_key_digest": kms["public_key_digest"],
        "authority_id": binding["authority_id"],
        "key_id": binding["key_id"],
        "kms_authority_binding_digest": binding["binding_digest"],
        "source_expires_at": capability_receipt.source_expires_at,
        "expires_at": capability_receipt.expires_at,
        "cloud_operations": (),
        "credentials_exported": False,
        "contains_key_material": False,
    }
    values["receipt_digest"] = _receipt_digest({**values, "cloud_operations": []})
    values["_seal"] = _RECEIPT_SEAL
    receipt = CredentialBootstrapReceipt(**values)
    _RECEIPT_REGISTRY[id(receipt)] = (receipt, tuple(getattr(receipt, field) for field in receipt.__dataclass_fields__))
    return receipt


def validate_receipt(
    receipt: CredentialBootstrapReceipt,
    *,
    now: int,
    packet_digest: str | None = None,
    packet_path: str | None = None,
    request_digest: str | None = None,
    approval_digest: str | None = None,
) -> dict[str, Any]:
    """Validate only a live receipt and, when supplied, its exact bindings."""
    _require(type(now) is int, "receipt clock is invalid")
    _require(_is_registered_receipt(receipt), "credential bootstrap receipt is not verifier-issued")
    public = receipt.as_public_dict()
    _require(receipt.receipt_digest == _receipt_digest(public), "credential bootstrap receipt digest drift")
    _require(type(public["packet_path"]) is str and public["packet_path"].startswith("/"), "canonical packet path is invalid")
    if packet_digest is not None:
        _require(public["packet_digest"] == packet_digest, "credential bootstrap receipt packet digest drift")
    if packet_path is not None:
        _require(public["packet_path"] == packet_path, "credential bootstrap receipt packet path drift")
    if request_digest is not None:
        _require(public["request_digest"] == request_digest, "credential bootstrap receipt request digest drift")
    if approval_digest is not None:
        _require(public["approval_digest"] == approval_digest, "credential bootstrap receipt approval digest drift")
    for field in (
        "request_digest", "packet_digest", "approval_digest", "image_digest", "kms_authority_binding_digest",
        "attestation_binding_digest", "attestation_claims_digest", "attestation_token_digest",
        "nonce_digest", "federated_token_digest", "capability_receipt_digest",
        "capability_binding_digest", "kms_public_key_digest", "kms_authority_binding_digest",
    ):
        _is_digest(public[field], field)
    _require(isinstance(public["kms_key_version"], str) and public["kms_key_version"], "KMS key version is missing")
    _require(isinstance(public["authority_id"], str) and public["authority_id"].startswith("self-custodied/"), "KMS authority identity is invalid")
    _require(isinstance(public["key_id"], str) and public["key_id"], "KMS key identity is missing")
    _require(public["cloud_operations"] == [] and public["credentials_exported"] is False and public["contains_key_material"] is False, "credential receipt crossed the operation boundary")
    _require(type(public["attestation_issued_at"]) is int and type(public["attestation_expires_at"]) is int, "attestation time evidence is invalid")
    _require(public["attestation_expires_at"] > now and public["attestation_issued_at"] <= now + 30 and public["attestation_expires_at"] - public["attestation_issued_at"] <= 3600, "attestation time evidence is stale")
    _require(type(public["source_expires_at"]) is int and type(public["expires_at"]) is int and public["expires_at"] > now + 30 and public["expires_at"] <= public["source_expires_at"] <= public["attestation_expires_at"], "credential expiry is not source-bounded")
    return public


def bootstrap_credentials(*, adapter: ConfidentialSpaceAdapter, authority: Mapping[str, Any], kms: Mapping[str, Any], capability_binding: VerifiedCapabilityBinding, request: Mapping[str, Any], child_approval: VerifiedCredentialChildApproval) -> CredentialBootstrapReceipt:
    """Run one rerunnable, fail-closed credential bootstrap.

    The adapter performs the real launcher socket/JWT/STS sequence. This
    function only validates external read-only prerequisites before activation
    and emits a sealed redacted receipt afterward.
    """
    _require(type(adapter) is ConfidentialSpaceAdapter, "Confidential Space adapter is required")
    factory = adapter.capability_factory
    _require(isinstance(factory, CredentialOnlyCapabilityFactory), "credential-only capability factory is required")
    _require(isinstance(capability_binding, VerifiedCapabilityBinding), "capability binding is verifier-issued")
    checked_request = validate_execution_request(
        request, config=adapter.config, kms=kms, capability_binding=capability_binding,
        packet_digest=request.get("packet_digest"), packet_path=request.get("packet_path"),
    )
    _require(factory.capability_binding_digest == capability_binding.binding_digest, "capability binding digest drift")
    checked_approval = validate_child_approval(child_approval, request=checked_request, now=int(adapter.config.clock()))
    validate_kms_binding(authority, kms, adapter.config)
    _require(kms["authority_binding"]["binding_digest"] == checked_request.authority_binding_digest, "KMS authority binding digest drift")
    # The capability binding validator is intentionally called by the existing
    # preflight function; its returned state is read-only and never applied.
    activate_after_external_preflight(adapter, authority=authority, kms=kms, capability_binding=capability_binding, service=False)
    activation = validate_attested_activation(adapter)
    capability_receipt = factory.capability_receipt
    _require(capability_receipt is not None, "source-bounded capability receipt is missing")
    _require(capability_receipt.source_token_digest == activation.federated_token_digest, "capability source does not match the live STS activation")
    _require(capability_receipt.service_account == adapter.config.capability_service_account, "capability service account provenance drift")
    _require(capability_receipt.capability_binding_digest == factory.capability_binding_digest == capability_binding.binding_digest, "capability binding provenance drift")
    _require(capability_receipt.expires_at <= activation.expires_at and capability_receipt.source_expires_at <= activation.expires_at, "credential lifetime exceeds attestation")
    return _build_receipt(request=checked_request, approval=checked_approval, config=adapter.config, kms=kms, adapter=adapter, activation=activation, capability_receipt=capability_receipt)


__all__ = [
    "CredentialBootstrapReceipt", "CredentialExecutionRequest", "CredentialOnlyCapabilityFactory", "VerifiedCredentialChildApproval",
    "CredentialProcessError", "bootstrap_credentials", "build_execution_request",
    "validate_child_approval", "validate_execution_request", "validate_receipt",
]
