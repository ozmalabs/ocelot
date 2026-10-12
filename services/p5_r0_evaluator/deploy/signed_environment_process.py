"""Local gate for the DISPATCH-050 signed-environment boundary.

This module is deliberately a validator and result consumer, not an execution
client.  It composes the frozen RS-065 request with the RS-067/068 authority
contracts, validates a real ``ConfidentialSpaceAdapter`` activation, checks the
reviewed KMS binding, and validates a future signed response.  It never calls
GCP, KMS, GCS, IAM, STS, FreeTSA, a signer, or a task runner; it never creates a
signature, credential, key, or runsheet entry.

The eventual apply/execute implementation must live behind the external
Confidential Space/IaC boundary represented by these validators.  Local tests
may validate malformed result shapes, but no local object is accepted as
attestation evidence merely because it contains a boolean such as
``attested=true``.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical
from evaluation.p5_r0.diagnostic_generator import build_diagnostic_artifacts
from services.p5_r0_evaluator.attestation_binding import VerifiedAttestationBinding, _is_registered_attestation_binding
from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.confidential_space import (
    DEFAULT_ATTESTATION_ISSUER,
    ConfidentialSpaceAdapter,
    FederatedAccessToken,
    LockedBootstrapConfig,
)
from services.p5_r0_evaluator.deploy.authority_binding import (
    validate_candidate_binding,
    validate_contract as validate_rs067_contract,
)
from services.p5_r0_evaluator.deploy.authority_binding_proposal import (
    validate_proposal as validate_rs068_proposal,
    validate_request_template as validate_rs068_template,
)
from services.p5_r0_evaluator.deploy.kms_lock_signing import (
    LockSigningReport,
    load_and_validate_request,
    validate_contract as validate_rs065_contract,
    validate_signed_response,
    validate_unsigned_request,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REQUEST = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json"
DEFAULT_RS067 = Path(__file__).with_name("p5-r0-authority-binding-contract.json")
DEFAULT_RS068_TEMPLATE = Path(__file__).with_name("rs-068-authority-binding-request.json")
DEFAULT_RS068_PROPOSAL = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_RUN_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,62}$")
_SERVICE_ACCOUNT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}@[a-z][a-z0-9-]{4,29}\.iam\.gserviceaccount\.com$")
_PROVIDER_RE = re.compile(
    r"^//iam\.googleapis\.com/projects/(?P<number>[0-9]+)/locations/global/"
    r"workloadIdentityPools/(?P<pool>[a-z0-9-]+)/providers/(?P<provider>[a-z0-9-]+)$"
)

# These are the facts that cannot be supplied by a local caller.  They are
# intentionally returned as review prerequisites rather than inferred.
EXTERNAL_PREREQUISITES = (
    "fresh reviewed candidate image digest and Confidential Space deployment binding",
    "fresh canonical WIP provider, claim mapping/condition, and STS audience observation",
    "existing evaluator KMS key version and Ed25519 public-key observation from the signed environment",
    "self-custodied P5R0PublicAuthorityV4 metadata bound to that exact KMS public key/version",
    "real launcher JWT with nonce, iat, exp, issuer, TEE, Secure Boot, AMD SEV, debug, workload, image, project, zone, and smoke claims",
    "STS exchange and IAM Credentials token-creator grant for the exact capability service account",
    "fresh least-privilege capability IAM observation with broad grants and public principals absent",
    "explicit child approval for the exact operation and unchanged request/authority digests",
)
FIRST_SAFE_APPLY_BOUNDARY = (
    "After the reviewed IaC definition has applied the exact image/provider/IAM bindings and "
    "freshly re-observed them, execute one Confidential Space launcher/STS bootstrap. "
    "Stop before KMS signing, GCS upload, deployment, VM/task execution, or any later operation "
    "unless the bootstrap returns a real attestation and only short-lived explicit credentials."
)


class SignedEnvironmentProcessError(ValueError):
    """A DISPATCH-050 input or external result is not admissible."""


@dataclass(frozen=True)
class SignedEnvironmentRequirements:
    request_digest: str
    unsigned_lock_digest: str
    rs065_contract_digest: str
    rs067_contract_digest: str
    rs068_proposal_digest: str | None
    status: str = "blocked_pending_external_signed_environment_prerequisites"


@dataclass(frozen=True)
class AttestedActivation:
    """Redacted activation receipt; no JWT, claims, nonce, or token is retained."""

    binding_digest: str
    claims_digest: str
    attestation_token_digest: str
    federated_token_digest: str
    issued_at: int
    expires_at: int
    image_digest: str
    provider: str


_CAPABILITY_RECEIPT_SEAL = object()
_CAPABILITY_RECEIPT_SCHEMA = "P5R0SourceBoundShortLivedCapabilityReceiptV1"
_CAPABILITY_RECEIPT_FIELDS = (
    "token_digest",
    "source_token_digest",
    "capability_binding_digest",
    "expires_at",
    "source_expires_at",
    "service_account",
)
# A private seal prevents normal construction; this registry prevents
# object.__new__, copies, and recomputed commitments from becoming receipts.
# Each entry also retains an immutable issuance snapshot, so a legitimate
# receipt mutated with object.__setattr__ cannot be resealed into a new one.
_CAPABILITY_RECEIPT_REGISTRY: dict[int, tuple["CapabilityReceipt", tuple[Any, ...], str]] = {}


def _receipt_commitment(values: Mapping[str, Any]) -> str:
    return digest({"schema": _CAPABILITY_RECEIPT_SCHEMA, **{field: values[field] for field in _CAPABILITY_RECEIPT_FIELDS}})


def _receipt_snapshot(value: "CapabilityReceipt") -> tuple[Any, ...]:
    return tuple(getattr(value, field) for field in (*_CAPABILITY_RECEIPT_FIELDS, "seal_digest"))


def _is_registered_capability_receipt(value: Any) -> bool:
    if type(value) is not CapabilityReceipt:
        return False
    entry = _CAPABILITY_RECEIPT_REGISTRY.get(id(value))
    if entry is None or entry[0] is not value:
        return False
    current = _receipt_snapshot(value)
    current_values = dict(zip(_CAPABILITY_RECEIPT_FIELDS, current))
    return current == entry[1] and _receipt_commitment(current_values) == entry[2]


def _register_capability_receipt(value: "CapabilityReceipt") -> "CapabilityReceipt":
    _CAPABILITY_RECEIPT_REGISTRY[id(value)] = (value, _receipt_snapshot(value), value.seal_digest)
    return value


@dataclass(frozen=True, init=False)
class CapabilityReceipt:
    """Redacted, verifier-owned proof of an explicit short-lived capability."""

    token_digest: str
    source_token_digest: str
    capability_binding_digest: str
    expires_at: int
    source_expires_at: int
    service_account: str
    seal_digest: str

    def __init__(self, **values: Any) -> None:
        if values.pop("_seal", None) is not _CAPABILITY_RECEIPT_SEAL or set(values) != set(self.__dataclass_fields__) or values.get("seal_digest") != _receipt_commitment(values):
            raise TypeError("capability receipt is verifier-created")
        for field in self.__dataclass_fields__:
            object.__setattr__(self, field, values[field])

    @property
    def schema(self) -> str:
        return _CAPABILITY_RECEIPT_SCHEMA


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SignedEnvironmentProcessError(message)


def _digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} must be a sha256 digest")
    return value


def _load_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical(Path(path).read_bytes())
    except Exception as exc:
        raise SignedEnvironmentProcessError(f"{label} is not canonical JSON") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def validate_local_contracts(
    *,
    request: Path = DEFAULT_REQUEST,
    rs067_contract: Path = DEFAULT_RS067,
    rs068_template: Path = DEFAULT_RS068_TEMPLATE,
    rs068_proposal: Path = DEFAULT_RS068_PROPOSAL,
) -> SignedEnvironmentRequirements:
    """Validate only checked-in review artifacts and preserve their blocked state."""
    request_path = Path(request)
    proposal_path = Path(rs068_proposal)
    if not request_path.is_file() or not proposal_path.is_file():
        try:
            generated_request = build_diagnostic_artifacts()["lock_signing_request"]
            request_report = validate_unsigned_request(generated_request)
            rs067 = validate_rs067_contract(rs067_contract)
            validate_rs068_template(rs068_template)
        except Exception as exc:
            raise SignedEnvironmentProcessError("DISPATCH-050 local contract validation failed") from exc
        _require(rs067["signature_present"] is False and rs067["production_promotable"] is False, "RS-067 contract is promoted")
        return SignedEnvironmentRequirements(
            request_digest=request_report.request_digest,
            unsigned_lock_digest=request_report.unsigned_lock_digest,
            rs065_contract_digest=digest(_load_canonical(DEFAULT_RS067.parent / "p5-r0-kms-lock-signing-contract.json", "RS-065 contract")),
            rs067_contract_digest=digest(_load_canonical(rs067_contract, "RS-067 contract")),
            rs068_proposal_digest=None,
            status="blocked_pending_local_review_inputs",
        )
    try:
        request_report = load_and_validate_request(request)
        rs065 = validate_rs065_contract()
        rs067 = validate_rs067_contract(rs067_contract)
        validate_rs068_template(rs068_template)
        rs068 = validate_rs068_proposal(rs068_proposal, request, Path(__file__).with_name("rs-068-wip-policy-remediation.json"))
    except Exception as exc:
        if isinstance(exc, SignedEnvironmentProcessError):
            raise
        raise SignedEnvironmentProcessError("DISPATCH-050 local contract validation failed") from exc
    _require(request_report.signature_present is False and request_report.production_promotable is False, "unsigned request crossed the signing boundary")
    _require(rs065["signature_present"] is False and rs065["production_promotable"] is False, "RS-065 contract is promoted")
    _require(rs067["signature_present"] is False and rs067["production_promotable"] is False, "RS-067 contract is promoted")
    _require(rs068["signature_present"] is False and rs068["production_promotable"] is False, "RS-068 proposal is promoted")
    return SignedEnvironmentRequirements(
        request_digest=request_report.request_digest,
        unsigned_lock_digest=request_report.unsigned_lock_digest,
        rs065_contract_digest=digest(_load_canonical(DEFAULT_RS067.parent / "p5-r0-kms-lock-signing-contract.json", "RS-065 contract")),
        rs067_contract_digest=digest(_load_canonical(rs067_contract, "RS-067 contract")),
        rs068_proposal_digest=digest(_load_canonical(rs068_proposal, "RS-068 proposal")),
    )


def _validate_fixed_claims(claims: Mapping[str, Any], config: LockedBootstrapConfig) -> None:
    expected = {
        "image_digest": config.image_digest,
        "project_number": config.project_number,
        "project_id": config.project_id,
        "zone": config.zone,
        "debug_state": config.debug_state,
        "tee": config.tee,
        "hardware_model": config.hardware_model,
        "secure_boot": config.secure_boot,
        "workload": config.workload,
        "smoke": "1" if config.confidential_space_smoke else "0",
    }
    _require(isinstance(claims, Mapping) and set(claims) == set(expected), "attestation fixed-claim evidence is not closed")
    _require(dict(claims) == expected, "attestation fixed claims are stale or unresolved")


def validate_attested_activation(adapter: ConfidentialSpaceAdapter) -> AttestedActivation:
    """Accept only activation performed by the real adapter gate.

    A mapping, a caller boolean, or a manually built ``VerifiedAttestation`` is
    not accepted.  The adapter's sealed binding and redacted startup evidence
    are the only admissible local receipt of the launcher/JWT/STS chain.
    """
    _require(isinstance(adapter, ConfidentialSpaceAdapter), "Confidential Space adapter is required")
    _require(adapter.attested is True, "Confidential Space attestation has not activated")
    binding = adapter.attestation_binding
    _require(isinstance(binding, VerifiedAttestationBinding), "sealed attestation binding is missing")
    evidence = adapter.startup_evidence
    _require(_is_registered_attestation_binding(binding), "sealed attestation binding is not adapter-issued")
    _require(isinstance(evidence, Mapping), "startup attestation evidence is missing")
    _require(set(evidence) == {"schema", "status", "policy_digest", "claim_paths_digest", "attestation_claims_digest", "wip_policy_digest", "attestation", "federation", "capabilities"}, "startup evidence fields are not closed")
    config = adapter.config
    _require(evidence["schema"] == "P5R0StartupAttestationEvidenceV1" and evidence["status"] == "attested", "startup evidence is not an attested activation")
    _require(evidence["policy_digest"] == config.policy_digest and evidence["claim_paths_digest"] == config.claim_paths_digest and evidence["attestation_claims_digest"] == config.attestation_claims_digest and evidence["wip_policy_digest"] == config.wip_policy_digest, "startup policy binding is stale")
    attestation = evidence["attestation"]
    _require(isinstance(attestation, Mapping) and set(attestation) == {"verified", "binding_digest", "token_digest", "claims_digest", "nonce_digest", "audience", "issuer", "issued_at", "expires_at", "fixed_claims"}, "attestation evidence is not closed")
    _require(attestation["verified"] is True and attestation["binding_digest"] == binding.binding_digest, "attestation was not verified by the adapter")
    _digest(attestation["binding_digest"], "attestation binding digest")
    _digest(attestation["token_digest"], "attestation token digest")
    _digest(attestation["claims_digest"], "attestation claims digest")
    _digest(attestation["nonce_digest"], "attestation nonce digest")
    _require(attestation["audience"] == config.attestation_audience and attestation["issuer"] == DEFAULT_ATTESTATION_ISSUER, "attestation audience or issuer binding is stale")
    _require(type(attestation["issued_at"]) is int and type(attestation["expires_at"]) is int and attestation["expires_at"] > config.clock() and attestation["issued_at"] <= config.clock() + 30 and attestation["expires_at"] - attestation["issued_at"] <= 3600, "attestation time evidence is missing or stale")
    _validate_fixed_claims(attestation["fixed_claims"], config)
    federation = evidence["federation"]
    _require(isinstance(federation, Mapping) and set(federation) == {"exchanged", "provider", "access_token_digest", "expires_at"}, "STS evidence is not closed")
    _require(federation["exchanged"] is True and federation["provider"] == config.wip_provider, "STS provider binding is stale")
    _digest(federation["access_token_digest"], "federated access-token digest")
    _require(type(federation["expires_at"]) is int and federation["expires_at"] > config.clock() + 30 and federation["expires_at"] <= config.clock() + 3600, "federated credential is not short-lived")
    _require(evidence["capabilities"] == "constructed_after_attestation", "capabilities were not constructed after attestation")
    _require(binding.image_digest == config.image_digest and binding.provider == config.wip_provider and binding.project_id == config.project_id and binding.project_number == config.project_number and binding.zone == config.zone and binding.secure_boot is config.secure_boot and binding.hardware_model == config.hardware_model and binding.tee == config.tee and binding.workload == config.workload, "sealed attestation binding is stale")
    return AttestedActivation(
        binding_digest=binding.binding_digest,
        claims_digest=attestation["claims_digest"],
        attestation_token_digest=attestation["token_digest"],
        federated_token_digest=federation["access_token_digest"],
        issued_at=attestation["issued_at"],
        expires_at=attestation["expires_at"],
        image_digest=config.image_digest,
        provider=config.wip_provider,
    )


def _expected_principal(config: LockedBootstrapConfig) -> str:
    match = _PROVIDER_RE.fullmatch(config.wip_provider)
    _require(match is not None, "WIP provider is not canonical")
    return f"principalSet://iam.googleapis.com/projects/{match.group('number')}/locations/global/workloadIdentityPools/{match.group('pool')}/attribute.image_digest/{config.image_digest}"


def validate_kms_binding(authority: Mapping[str, Any], kms: Mapping[str, Any], config: LockedBootstrapConfig) -> dict[str, Any]:
    """Verify KMS public key/version/authority binding before any future sign."""
    _require(isinstance(authority, Mapping) and authority.get("schema") == "P5R0PublicAuthorityV4", "KMS authority must be P5R0PublicAuthorityV4")
    _require(dict(authority) == dict(config.authority), "KMS authority is not the configured self-custodied authority")
    _require(isinstance(authority.get("authority_id"), str) and authority["authority_id"].startswith("self-custodied/"), "KMS authority is not self-custodied")
    _require(isinstance(kms, Mapping) and kms.get("key_version") == config.kms_key_version, "KMS key version is stale")
    transport = authority.get("transport_attestation")
    _require(isinstance(transport, Mapping) and transport.get("provider") == config.wip_provider and transport.get("audience") == config.attestation_audience and transport.get("event") == "confidential_space_attestation", "KMS transport binding is stale")
    environment = {
        "provider": config.wip_provider,
        "audience": config.attestation_audience,
        "event": "confidential_space_attestation",
        "claims": {
            "project_number": config.project_number,
            "project_id": config.project_id,
            "zone": config.zone,
            "workload": config.workload,
            "issuer": config.expected_issuer or DEFAULT_ATTESTATION_ISSUER,
            "image_digest": config.image_digest,
            "debug_state": config.debug_state,
            "tee": config.tee,
            "hardware_model": config.hardware_model,
            "secure_boot": config.secure_boot,
            "smoke": config.confidential_space_smoke,
        },
        "claim_paths": dict(config.claim_paths),
    }
    try:
        report = validate_candidate_binding(authority, kms, environment)
    except Exception as exc:
        raise SignedEnvironmentProcessError("KMS public key or authority binding failed") from exc
    return dict(report)


_CAPABILITY_BINDING_SEAL = object()
_CAPABILITY_BINDING_REGISTRY: dict[int, tuple["VerifiedCapabilityBinding", bytes, str]] = {}


@dataclass(frozen=True, init=False)
class VerifiedCapabilityBinding:
    """Verifier-issued immutable snapshot of one read-only IAM observation.

    The remote IAM facts are not accepted as a caller mapping at a gate.  The
    verifier stores a canonical snapshot and retains object identity plus the
    original commitment, so object mutation/reseal and copied lookalikes fail.
    """

    snapshot: bytes
    binding_digest: str

    def __init__(self, **values: Any) -> None:
        _require(values.pop("_seal", None) is _CAPABILITY_BINDING_SEAL, "capability binding is verifier-created")
        _require(set(values) == {"snapshot", "binding_digest"}, "capability binding fields are closed")
        _require(isinstance(values["snapshot"], bytes), "capability binding snapshot is invalid")
        _digest(values["binding_digest"], "capability binding digest")
        object.__setattr__(self, "snapshot", values["snapshot"])
        object.__setattr__(self, "binding_digest", values["binding_digest"])

    def as_public_dict(self) -> dict[str, Any]:
        _require(_is_registered_capability_binding(self), "capability binding is not verifier-issued")
        value = parse_canonical(self.snapshot)
        _require(isinstance(value, dict), "capability binding snapshot is not an object")
        return value


def _capability_snapshot(value: VerifiedCapabilityBinding) -> tuple[bytes, str]:
    return value.snapshot, value.binding_digest


def _is_registered_capability_binding(value: Any) -> bool:
    if type(value) is not VerifiedCapabilityBinding:
        return False
    entry = _CAPABILITY_BINDING_REGISTRY.get(id(value))
    return entry is not None and entry[0] is value and _capability_snapshot(value) == entry[1] and digest(parse_canonical(value.snapshot)) == entry[2]


def _validate_capability_binding_mapping(binding: Mapping[str, Any], config: LockedBootstrapConfig) -> dict[str, Any]:
    fields = {"schema", "status", "provider", "image_digest", "project_number", "project_id", "zone", "principal", "service_account", "bucket", "prefix", "run_id", "iam", "observation"}
    _require(isinstance(binding, Mapping) and set(binding) == fields, "capability binding fields are not closed")
    _require(binding["schema"] == "P5R0SignedEnvironmentCapabilityBindingV1" and binding["status"] == "verified_external_precondition", "capability binding is not a verified external precondition")
    _require(binding["provider"] == config.wip_provider and binding["image_digest"] == config.image_digest and binding["project_number"] == config.project_number and binding["project_id"] == config.project_id and binding["zone"] == config.zone, "capability binding is stale")
    _require(binding["principal"] == _expected_principal(config), "WIF principal is stale or unresolved")
    _require(isinstance(binding["service_account"], str) and _SERVICE_ACCOUNT_RE.fullmatch(binding["service_account"]) and binding["service_account"] == config.capability_service_account, "capability service account is not exact")
    _require(isinstance(binding["bucket"], str) and binding["bucket"] == config.bucket and isinstance(binding["prefix"], str) and binding["prefix"] == config.prefix and isinstance(binding["run_id"], str) and _RUN_ID_RE.fullmatch(binding["run_id"]) is not None, "capability destination is stale or unresolved")
    iam = binding["iam"]
    _require(isinstance(iam, Mapping) and set(iam) == {"narrow_writer_verified", "broad_grant_absent", "token_creator_verified", "public_principals_absent"}, "capability IAM evidence is not closed")
    _require(all(iam[name] is True for name in iam), "least-privilege capability IAM is not verified")
    observation = binding["observation"]
    _require(isinstance(observation, Mapping) and set(observation) == {"fresh", "source", "state_digest", "cloud_operations"}, "capability observation is not closed")
    _require(observation["fresh"] is True and observation["source"] == "reviewed_iac_remote_observation" and observation["cloud_operations"] == [], "capability observation is not fresh/read-only")
    _digest(observation["state_digest"], "capability state digest")
    return {"schema": binding["schema"], "status": binding["status"], "provider": binding["provider"], "principal": binding["principal"], "service_account": binding["service_account"], "state_digest": observation["state_digest"], "token_creator_verified": True}


def _issue_verified_capability_binding(binding: Mapping[str, Any], config: LockedBootstrapConfig) -> VerifiedCapabilityBinding:
    """Seal a binding only at the verifier/read-only-observation boundary."""
    _validate_capability_binding_mapping(binding, config)
    snapshot = canonical_bytes(dict(binding))
    sealed = VerifiedCapabilityBinding(snapshot=snapshot, binding_digest=digest(dict(binding)), _seal=_CAPABILITY_BINDING_SEAL)
    _CAPABILITY_BINDING_REGISTRY[id(sealed)] = (sealed, _capability_snapshot(sealed), sealed.binding_digest)
    return sealed


def validate_capability_binding(binding: VerifiedCapabilityBinding, config: LockedBootstrapConfig) -> dict[str, Any]:
    """Accept only a verifier-issued immutable IAM observation snapshot."""
    _require(_is_registered_capability_binding(binding), "capability binding is not verifier-issued")
    return _validate_capability_binding_mapping(binding.as_public_dict(), config)


def validate_short_lived_capability(
    source: FederatedAccessToken,
    capability: FederatedAccessToken,
    *,
    source_token_digest: str,
    capability_binding_digest: str,
    service_account: str,
    now: int,
) -> CapabilityReceipt:
    """Allow only an explicit bearer token bounded by a validated source/binding receipt."""
    _require(isinstance(source, FederatedAccessToken) and isinstance(capability, FederatedAccessToken), "explicit federated credentials are required")
    _require(source_token_digest == digest(source.access_token), "capability source provenance does not match")
    _digest(capability_binding_digest, "capability binding digest")
    _require(source.token_type == "Bearer" and capability.token_type == "Bearer" and bool(source.access_token) and bool(capability.access_token), "capability credentials must be bearer tokens")
    _require(type(source.expires_at) is int and type(capability.expires_at) is int and source.expires_at > now + 30, "federated source credential is expired")
    _require(capability.expires_at > now + 30 and capability.expires_at <= source.expires_at and capability.expires_at <= now + 3600, "capability credential is not short-lived or source-bounded")
    _require(isinstance(service_account, str) and _SERVICE_ACCOUNT_RE.fullmatch(service_account) is not None, "capability service account is invalid")
    values = {
        "token_digest": digest(capability.access_token),
        "source_token_digest": source_token_digest,
        "capability_binding_digest": capability_binding_digest,
        "expires_at": capability.expires_at,
        "source_expires_at": source.expires_at,
        "service_account": service_account,
    }
    values["seal_digest"] = _receipt_commitment(values)
    return _register_capability_receipt(CapabilityReceipt(**values, _seal=_CAPABILITY_RECEIPT_SEAL))


def activate_after_external_preflight(
    adapter: ConfidentialSpaceAdapter,
    *,
    authority: Mapping[str, Any],
    kms: Mapping[str, Any],
    capability_binding: VerifiedCapabilityBinding,
    service: bool = True,
):
    """Cross the first execution boundary only after fresh external checks.

    Credential bootstrap requests capability construction only; it must not
    invoke the evaluator service factory or expose a client-shaped capability
    to a downstream executor.
    """
    _require(isinstance(adapter, ConfidentialSpaceAdapter), "Confidential Space adapter is required")
    validate_kms_binding(authority, kms, adapter.config)
    validate_capability_binding(capability_binding, adapter.config)
    if service:
        return adapter.activate_attested_service()
    return adapter.activate_attested_capabilities()


def validate_signed_lock_result(
    request: Mapping[str, Any],
    response: Mapping[str, Any],
    *,
    adapter: ConfidentialSpaceAdapter | None = None,
) -> LockSigningReport:
    """Consume, but never create, the future signed response."""
    validate_attested_activation(adapter)
    _require(isinstance(request, Mapping) and isinstance(response, Mapping), "signed response requires canonical request and response objects")
    try:
        report = validate_signed_response(request, response)
    except Exception as exc:
        if isinstance(exc, SignedEnvironmentProcessError):
            raise
        raise SignedEnvironmentProcessError("signed response failed exact-lock/KMS/authority validation") from exc
    _require(report.unsigned_lock_digest == request["unsigned_lock_digest"], "signed response changed the unsigned lock digest")
    try:
        validate_kms_binding(response["authority"], response["kms"], adapter.config)
    except (KeyError, TypeError) as exc:
        raise SignedEnvironmentProcessError("signed response authority/KMS binding is not exact") from exc
    _require(report.signature_present is True and report.production_promotable is False, "signed response crossed the diagnostic boundary")
    return report


def process_summary(requirements: SignedEnvironmentRequirements | None = None) -> dict[str, Any]:
    """Return a redacted review summary suitable for local CI output."""
    return {
        "schema": "P5R0DISPATCH050SignedEnvironmentProcessV1",
        "status": requirements.status if requirements is not None else "blocked_pending_external_signed_environment_prerequisites",
        "request_digest": requirements.request_digest if requirements is not None else None,
        "unsigned_lock_digest": requirements.unsigned_lock_digest if requirements is not None else None,
        "signature_created": False,
        "credentials_created": False,
        "cloud_operations": [],
        "external_prerequisites": list(EXTERNAL_PREREQUISITES),
        "first_safe_apply_boundary": FIRST_SAFE_APPLY_BOUNDARY,
    }


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local-only DISPATCH-050 signed-environment process")
    parser.add_argument("command", choices=("validate",))
    args = parser.parse_args(argv)
    try:
        requirements = validate_local_contracts()
    except (SignedEnvironmentProcessError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(process_summary(requirements), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = [
    "DEFAULT_REQUEST", "EXTERNAL_PREREQUISITES", "FIRST_SAFE_APPLY_BOUNDARY",
    "AttestedActivation", "CapabilityReceipt", "VerifiedCapabilityBinding", "SignedEnvironmentProcessError",
    "SignedEnvironmentRequirements", "activate_after_external_preflight", "process_summary", "validate_attested_activation",
    "validate_capability_binding", "validate_kms_binding", "validate_local_contracts", "validate_short_lived_capability",
    "validate_signed_lock_result",
]
