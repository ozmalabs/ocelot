"""Verifier-owned credential evidence for the R18R13 IAM readiness boundary.

This module contains no cloud client and never accepts raw tokens.  The public
factory composes only the exact Confidential Space adapter receipt, the sealed
source-bounded capability receipt, and the reviewed IAM executor's successful
credential verification.  The resulting object cannot be constructed by a
caller because its constructor requires a module-private seal.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes

from services.p5_r0_evaluator.attestation_binding import VerifiedAttestationBinding
from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.confidential_space import ConfidentialSpaceAdapter
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import ReviewedIAMExecutorAdapter
from services.p5_r0_evaluator.deploy.signed_environment_process import (
    CapabilityReceipt,
    _receipt_commitment,
    validate_attested_activation,
    _is_registered_capability_receipt,
)

_EVIDENCE_SEAL = object()
_EVIDENCE_SCHEMA = "P5R0VerifiedCredentialReadinessEvidenceV1"
_EVIDENCE_FIELDS = {
    "packet_digest",
    "signed_environment_evidence_digest",
    "provider",
    "image_digest",
    "audience",
    "principal",
    "target_resource",
    "authority_binding_digest",
    "service_account",
    "attestation_binding_digest",
    "capability_binding_digest",
    "source_token_digest",
    "capability_token_digest",
    "attestation_expires_at",
    "source_expires_at",
    "expires_at",
    "seal_digest",
}
# Strong identity registration is deliberate: retaining each issued instance
# prevents id reuse from turning a stale or forged object into valid evidence.
# The immutable field snapshot additionally detects post-issuance mutation even
# when an attacker recomputes the public seal digest.
_EVIDENCE_REGISTRY: dict[int, tuple["VerifiedCredentialReadinessEvidence", tuple[Any, ...], str]] = {}


class CredentialEvidenceError(ValueError):
    """Credential evidence was not produced by all required verifier gates."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CredentialEvidenceError(message)


def _digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and len(value) == 71 and value.startswith("sha256:") and all(c in "0123456789abcdef" for c in value[7:]), f"{label} is not a digest")
    return value


@dataclass(frozen=True, init=False)
class VerifiedCredentialReadinessEvidence:
    """Immutable, redacted evidence owned by the verifier boundary.

    No JWT, access token, key material, or caller-supplied mapping is retained.
    Only commitments and bounded expiry facts from verified objects are stored.
    """

    packet_digest: str
    signed_environment_evidence_digest: str
    provider: str
    image_digest: str
    audience: str
    principal: str
    target_resource: str
    authority_binding_digest: str
    service_account: str
    attestation_binding_digest: str
    capability_binding_digest: str
    source_token_digest: str
    capability_token_digest: str
    attestation_expires_at: int
    source_expires_at: int
    expires_at: int
    seal_digest: str

    def __init__(self, **values: Any) -> None:
        if values.pop("_seal", None) is not _EVIDENCE_SEAL or set(values) != _EVIDENCE_FIELDS:
            raise TypeError("verified credential evidence is verifier-created")
        for field in self.__dataclass_fields__:
            object.__setattr__(self, field, values[field])

    @property
    def schema(self) -> str:
        return _EVIDENCE_SCHEMA


def _evidence_snapshot(value: "VerifiedCredentialReadinessEvidence") -> tuple[Any, ...]:
    return tuple(getattr(value, field) for field in value.__dataclass_fields__)


def _is_registered_credential_evidence(value: Any) -> bool:
    if type(value) is not VerifiedCredentialReadinessEvidence:
        return False
    entry = _EVIDENCE_REGISTRY.get(id(value))
    if entry is None or entry[0] is not value:
        return False
    current = _evidence_snapshot(value)
    current_values = dict(zip(value.__dataclass_fields__, current))
    return current == entry[1] and _commitment(current_values) == entry[2]


def _register_credential_evidence(value: VerifiedCredentialReadinessEvidence) -> VerifiedCredentialReadinessEvidence:
    _EVIDENCE_REGISTRY[id(value)] = (value, _evidence_snapshot(value), value.seal_digest)
    return value


def _active_credential_contract(*, evidence_digest: str) -> dict[str, str]:
    """Load the verifier-owned contract for the active boundary artifacts."""
    try:
        from services.p5_r0_evaluator.deploy.rs069r18r13_iam_boundary import _active_credential_contract as load_contract
        return load_contract(evidence_digest=evidence_digest)
    except Exception as exc:
        raise CredentialEvidenceError("active IAM boundary credential contract is unavailable") from exc


def _commitment(values: Mapping[str, Any]) -> str:
    return digest({"schema": _EVIDENCE_SCHEMA, **{field: values[field] for field in _EVIDENCE_FIELDS if field != "seal_digest"}})


def build_verified_credential_readiness_evidence(
    *,
    adapter: ConfidentialSpaceAdapter,
    executor: ReviewedIAMExecutorAdapter,
    capability_receipt: CapabilityReceipt,
    now: int,
) -> VerifiedCredentialReadinessEvidence:
    """Build evidence only after adapter, capability, and IAM verifier gates.

    The active packet/artifact contract is loaded internally; callers cannot
    provide alternate commitments for any readiness field.
    """
    _require(type(adapter) is ConfidentialSpaceAdapter, "Confidential Space adapter is required")
    _require(type(executor) is ReviewedIAMExecutorAdapter, "reviewed IAM executor adapter is required")
    _require(type(capability_receipt) is CapabilityReceipt, "sealed capability receipt is required")
    _require(_is_registered_capability_receipt(capability_receipt), "capability receipt is not verifier-issued")
    _require(type(now) is int, "credential evidence clock is invalid")
    credential = executor.credential
    _require(credential is not None, "reviewed IAM credential is missing")
    contract = _active_credential_contract(evidence_digest=credential.evidence_digest)
    for name, value in contract.items():
        _require(isinstance(value, str) and value, f"credential evidence {name} is missing")
    _digest(contract["packet_digest"], "packet digest")
    _digest(contract["evidence_digest"], "signed-environment evidence digest")
    _digest(contract["authority_binding_digest"], "authority binding digest")
    _digest(contract["capability_binding_digest"], "capability binding digest")

    try:
        activation = validate_attested_activation(adapter)
    except Exception as exc:
        raise CredentialEvidenceError("Confidential Space attestation binding was not verifier-validated") from exc
    binding = adapter.attestation_binding
    _require(type(binding) is VerifiedAttestationBinding, "sealed attestation binding is missing")
    config = adapter.config
    _require(config.wip_provider == contract["provider"] and config.image_digest == contract["image_digest"] and config.attestation_audience == contract["audience"], "Confidential Space provider/image/audience binding drift")
    _require(config.capability_service_account == contract["service_account"], "Confidential Space capability account binding drift")
    _require(activation.provider == contract["provider"] and activation.image_digest == contract["image_digest"], "attested activation binding drift")
    _require(activation.binding_digest == binding.binding_digest, "attested activation does not use the current sealed binding")

    receipt = capability_receipt
    _require(receipt.seal_digest == _receipt_commitment({field: getattr(receipt, field) for field in receipt.__dataclass_fields__}), "capability receipt seal digest drift")
    _digest(receipt.source_token_digest, "capability source token digest")
    _digest(receipt.token_digest, "capability token digest")
    _digest(receipt.capability_binding_digest, "capability binding digest")
    _require(receipt.capability_binding_digest == contract["capability_binding_digest"], "capability binding digest drift")
    _require(receipt.service_account == contract["service_account"], "capability service account drift")
    _require(receipt.source_token_digest == activation.federated_token_digest, "capability source does not match attested STS token")
    _require(type(receipt.expires_at) is int and type(receipt.source_expires_at) is int, "capability expiry is invalid")
    _require(receipt.expires_at > now + 30 and receipt.expires_at <= receipt.source_expires_at <= now + 3600, "capability receipt is expired or not source-bounded")
    _require(receipt.expires_at <= activation.expires_at and receipt.source_expires_at <= activation.expires_at, "capability receipt exceeds attestation lifetime")

    try:
        executor.validate_credential_binding({"packet_digest": contract["packet_digest"], "evidence_digest": contract["evidence_digest"]})
    except Exception as exc:
        raise CredentialEvidenceError("reviewed IAM credential verifier did not validate the source") from exc
    credential = executor.credential
    _require(credential is not None, "reviewed IAM credential is missing")
    _require(credential.packet_digest == contract["packet_digest"] and credential.evidence_digest == contract["evidence_digest"], "IAM credential packet/evidence binding drift")
    _require(credential.provider == contract["provider"] and credential.image_digest == contract["image_digest"] and credential.audience == contract["audience"], "IAM credential provider/image/audience drift")
    _require(credential.authority_binding_digest == contract["authority_binding_digest"], "IAM credential authority binding drift")
    _require(credential.target_service_account == contract["service_account"], "IAM credential account drift")
    _require(getattr(credential, "principal", None) == contract["principal"] and getattr(credential, "target_resource", None) == contract["target_resource"], "IAM credential capability binding drift")
    _require(type(credential.expires_at) is int and credential.expires_at == receipt.expires_at, "IAM credential expiry does not match capability receipt")

    values = {
        "packet_digest": contract["packet_digest"],
        "signed_environment_evidence_digest": contract["evidence_digest"],
        "provider": contract["provider"],
        "image_digest": contract["image_digest"],
        "audience": contract["audience"],
        "principal": contract["principal"],
        "target_resource": contract["target_resource"],
        "authority_binding_digest": contract["authority_binding_digest"],
        "service_account": contract["service_account"],
        "attestation_binding_digest": binding.binding_digest,
        "capability_binding_digest": receipt.capability_binding_digest,
        "source_token_digest": receipt.source_token_digest,
        "capability_token_digest": receipt.token_digest,
        "attestation_expires_at": activation.expires_at,
        "source_expires_at": receipt.source_expires_at,
        "expires_at": receipt.expires_at,
    }
    values["seal_digest"] = _commitment(values)
    return _register_credential_evidence(VerifiedCredentialReadinessEvidence(**values, _seal=_EVIDENCE_SEAL))


__all__ = ["CredentialEvidenceError", "VerifiedCredentialReadinessEvidence", "build_verified_credential_readiness_evidence"]



# Persisted evidence is a canonical signed envelope, not an object-identity
# registry entry.  The trusted public key is supplied by the verifier boundary;
# a key embedded in an artifact is never trusted merely because it verifies.
def _evidence_public_dict(value: VerifiedCredentialReadinessEvidence) -> dict[str, Any]:
    _require(_is_registered_credential_evidence(value), "credential evidence is not verifier-issued")
    return {"schema": _EVIDENCE_SCHEMA, **{field: getattr(value, field) for field in value.__dataclass_fields__}}


def build_signed_credential_evidence_artifact(*, evidence: VerifiedCredentialReadinessEvidence, signature: str, public_key: str) -> dict[str, Any]:
    """Wrap redacted evidence in a canonical verifier-signed artifact."""
    _require(isinstance(signature, str) and bool(signature), "credential evidence signature is missing")
    _require(isinstance(public_key, str) and bool(public_key), "credential evidence public key is missing")
    payload = _evidence_public_dict(evidence)
    value = {"schema": "P5R0SignedCredentialReadinessEvidenceV1", "evidence": payload, "signature": signature, "public_key": public_key}
    value["artifact_digest"] = digest(value)
    return value


def load_signed_credential_evidence(path: Path | str, *, trusted_public_key: str) -> VerifiedCredentialReadinessEvidence:
    """Canonical-load and cryptographically verify persisted redacted evidence."""
    import base64
    from pathlib import Path
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from evaluation.p0a.canonical import parse_canonical
        artifact = parse_canonical(Path(path).read_bytes())
        _require(artifact.get("schema") == "P5R0SignedCredentialReadinessEvidenceV1", "credential evidence artifact schema drift")
        _require(artifact.get("artifact_digest") == digest({key: item for key, item in artifact.items() if key != "artifact_digest"}), "credential evidence artifact digest drift")
        _require(artifact.get("public_key") == trusted_public_key, "credential evidence signer is not trusted")
        evidence = artifact.get("evidence")
        _require(isinstance(evidence, Mapping) and evidence.get("schema") == _EVIDENCE_SCHEMA, "credential evidence payload is malformed")
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted_public_key, validate=True))
        key.verify(base64.b64decode(artifact["signature"], validate=True), canonical_bytes(dict(evidence)))
        values = {field: evidence[field] for field in VerifiedCredentialReadinessEvidence.__dataclass_fields__}
        _require(values["seal_digest"] == _commitment(values), "credential evidence seal digest drift")
        return _register_credential_evidence(VerifiedCredentialReadinessEvidence(**values, _seal=_EVIDENCE_SEAL))
    except CredentialEvidenceError:
        raise
    except Exception as exc:
        raise CredentialEvidenceError("persisted credential evidence signature is invalid") from exc


__all__ = ["CredentialEvidenceError", "VerifiedCredentialReadinessEvidence", "build_verified_credential_readiness_evidence", "build_signed_credential_evidence_artifact", "load_signed_credential_evidence"]
