"""Repository-only RS-065 KMS lock-signing boundary.

This module is a request/response contract, not a KMS client.  It consumes the
frozen RS-062 unsigned request, describes the existing ``Signer`` capability,
and validates a future Confidential Space response.  It never calls a signer,
KMS, gcloud, GCS, VM, deployment, FreeTSA, or task executor and never accepts
private key material.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from evaluation.p0a.canonical import b64decode, canonical_bytes, parse_canonical, sha256
from evaluation.p5_r0.diagnostic_generator import build_diagnostic_artifacts
from services.p5_r0_evaluator.canonical import digest as service_digest
from services.p5_r0_evaluator.client import EvaluatorClientError, _validate_authority
from services.p5_r0_evaluator.interfaces import Signer


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REQUEST = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json"
DEFAULT_CONTRACT = Path(__file__).with_name("p5-r0-kms-lock-signing-contract.json")
EXPECTED_OPERATION = "sign_exact_lock_digest_in_reviewed_signed_environment"
EXPECTED_BINDING_SCHEMA = "P5R0KMSAuthorityBindingV1"
_KEY_VERSION_RE = re.compile(
    r"^projects/[^/]+/locations/[^/]+/keyRings/[^/]+/cryptoKeys/[^/]+/cryptoKeyVersions/[1-9][0-9]*$"
)


class KMSLockSigningValidationError(ValueError):
    """An RS-065 request or future signed response is not admissible."""


class KMSLockSigningCapability(Signer, Protocol):
    """The existing signer capability used only by the future signed boundary."""


@dataclass(frozen=True)
class LockSigningReport:
    request_digest: str
    unsigned_lock_digest: str
    signature_present: bool
    production_promotable: bool = False


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise KMSLockSigningValidationError(message)


def _load_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical(path.read_bytes())
    except Exception as exc:
        raise KMSLockSigningValidationError(f"{label} is not canonical JSON") from exc
    return value


def _expected_request() -> dict[str, Any]:
    return build_diagnostic_artifacts()["lock_signing_request"]


def validate_unsigned_request(request: Mapping[str, Any], *, expected: Mapping[str, Any] | None = None) -> LockSigningReport:
    """Validate the exact generated request and preserve its unsigned state."""
    expected_request = dict(expected) if expected is not None else _expected_request()
    _require(dict(request) == expected_request, "request is not the exact frozen diagnostic request")
    unsigned = request["unsigned_lock"]
    _require(request["unsigned_lock_digest"] == unsigned["lock_digest"], "unsigned lock digest binding mismatch")
    _require(unsigned["signature"] is None, "unsigned lock already contains a signature")
    _require(unsigned["authority_digest"] is None and unsigned["kms_authority_binding_digest"] is None, "unsigned lock contains authority material")
    _require(request["kms"] == {
        "required": True,
        "operation": EXPECTED_OPERATION,
        "key_version": None,
        "authority_binding_digest": None,
        "signature_present": False,
    }, "KMS request is not request-only")
    _require(request["production_signature_created"] is False and request["cloud_operations"] == [], "request has release or cloud effects")
    return LockSigningReport(
        request_digest=request["request_digest"],
        unsigned_lock_digest=request["unsigned_lock_digest"],
        signature_present=False,
    )


def load_and_validate_request(path: Path = DEFAULT_REQUEST) -> LockSigningReport:
    request = _load_canonical(Path(path), "lock-signing request")
    return validate_unsigned_request(request)


def operation_descriptor(capability: Signer) -> dict[str, Any]:
    """Describe the future call without invoking the injected signer capability."""
    _require(callable(getattr(capability, "sign_digest", None)), "existing Signer capability is required")
    authority = getattr(capability, "authority", None)
    _require(isinstance(authority, Mapping), "Signer authority metadata is required")
    return {
        "interface": "services.p5_r0_evaluator.interfaces.Signer.sign_digest",
        "input": "32-byte SHA-256 digest of the exact unsigned lock",
        "output": "base64url Ed25519 signature",
        "environment": "Confidential Space",
        "approval_required": True,
        "request_only": True,
        "local_execution_forbidden": True,
        "private_key_export": False,
        "signature": None,
    }


def _validate_public_key(value: Any, label: str) -> bytes:
    _require(isinstance(value, str) and value, f"{label} is missing")
    try:
        raw = b64decode(value)
        Ed25519PublicKey.from_public_bytes(raw)
    except Exception as exc:
        raise KMSLockSigningValidationError(f"{label} is not an Ed25519 public key") from exc
    _require(len(raw) == 32, f"{label} length is invalid")
    return raw


def _validate_binding(authority: Mapping[str, Any], kms: Mapping[str, Any]) -> tuple[str, bytes]:
    _require(set(kms) == {"key_version", "public_key", "public_key_digest", "authority_binding"}, "KMS response fields are not closed")
    key_version = kms.get("key_version")
    _require(isinstance(key_version, str) and _KEY_VERSION_RE.fullmatch(key_version) is not None, "KMS key version is invalid")
    returned_public = _validate_public_key(kms.get("public_key"), "returned KMS public key")
    public_digest = service_digest(kms["public_key"])
    _require(kms.get("public_key_digest") == public_digest, "returned public-key digest mismatch")
    _require(authority.get("public_key") == kms["public_key"] and authority.get("public_key_digest") == public_digest, "returned public key does not match authority")

    binding = kms["authority_binding"]
    required = {"schema", "authority_id", "key_id", "kms_key_version", "public_key_digest", "purpose", "binding_digest"}
    _require(isinstance(binding, Mapping) and set(binding) == required, "KMS authority binding is not closed")
    _require(binding.get("schema") == EXPECTED_BINDING_SCHEMA, "KMS authority binding schema drift")
    _require(binding.get("authority_id") == authority.get("authority_id"), "authority id binding mismatch")
    _require(binding.get("key_id") == authority.get("key_id"), "authority key id binding mismatch")
    _require(binding.get("kms_key_version") == key_version, "KMS key-version binding mismatch")
    _require(binding.get("public_key_digest") == public_digest, "KMS binding public-key mismatch")
    _require(binding.get("purpose") == "p5-r0-production-authority", "KMS binding purpose is not the reviewed project authority")
    _require(binding.get("binding_digest") == sha256({key: value for key, value in binding.items() if key != "binding_digest"}), "KMS authority binding digest mismatch")
    return key_version, returned_public


def _validate_signature(signature: Any, public_key: bytes, unsigned_digest: str) -> None:
    _require(isinstance(signature, str) and signature, "signature is missing")
    try:
        raw_signature = b64decode(signature)
        _require(len(raw_signature) == 64, "Ed25519 signature length is invalid")
        Ed25519PublicKey.from_public_bytes(public_key).verify(raw_signature, bytes.fromhex(unsigned_digest[7:]))
    except KMSLockSigningValidationError:
        raise
    except Exception as exc:
        raise KMSLockSigningValidationError("Ed25519 signature does not verify the exact lock digest") from exc


def validate_signed_response(request: Mapping[str, Any], response: Mapping[str, Any]) -> LockSigningReport:
    """Validate a future signed response; this function never creates one."""
    request_report = validate_unsigned_request(request)
    required = {"schema", "status", "request_digest", "unsigned_lock_digest", "approval", "authority", "kms", "signed_lock"}
    _require(set(response) == required, "KMS response fields are not closed")
    _require(response["schema"] == "P5R0KMSLockSigningResponseV1" and response["status"] == "signed_review_only", "KMS response status is not review-only")
    _require(response["request_digest"] == request_report.request_digest, "response request digest mismatch")
    _require(response["unsigned_lock_digest"] == request_report.unsigned_lock_digest, "response lock digest mismatch")

    approval = response["approval"]
    _require(isinstance(approval, Mapping) and set(approval) == {
        "schema", "environment", "approval_source", "approved", "attestation_verified", "project_authority", "local_execution", "approval_digest"
    }, "Confidential Space approval is not closed")
    _require(approval.get("schema") == "P5R0ConfidentialSpaceApprovalV1", "approval schema drift")
    _require(approval.get("environment") == "Confidential Space" and approval.get("approval_source") == "confidential_space_attestation", "signed environment is not Confidential Space")
    _require(approval.get("approved") is True and approval.get("attestation_verified") is True and approval.get("local_execution") is False, "Confidential Space approval is absent or locally authored")
    _require(approval.get("project_authority") == "self_custodied", "project authority custody drift")
    _require(approval.get("approval_digest") == sha256({key: value for key, value in approval.items() if key != "approval_digest"}), "approval digest mismatch")

    try:
        authority = _validate_authority(response["authority"])
    except (EvaluatorClientError, TypeError) as exc:
        raise KMSLockSigningValidationError("returned authority metadata is invalid") from exc
    key_version, public_key = _validate_binding(authority, response["kms"])

    signed_lock = response["signed_lock"]
    unsigned_lock = request["unsigned_lock"]
    _require(isinstance(signed_lock, Mapping), "signed lock is missing")
    _require(set(signed_lock) == set(unsigned_lock), "signed lock fields are not closed")
    for key, value in unsigned_lock.items():
        if key != "signature":
            _require(signed_lock.get(key) == value, f"signed lock changed exact diagnostic field: {key}")
    _require(signed_lock.get("non_release") is True and signed_lock.get("classification") == "diagnostic_unsigned_kms_request", "signed lock crossed diagnostic boundary")
    _validate_signature(signed_lock.get("signature"), public_key, request_report.unsigned_lock_digest)
    return LockSigningReport(
        request_digest=request_report.request_digest,
        unsigned_lock_digest=request_report.unsigned_lock_digest,
        signature_present=True,
        production_promotable=False,
    )


def validate_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = _load_canonical(Path(path), "RS-065 contract")
    expected_fields = {"schema", "classification", "status", "request_path", "request_digest", "unsigned_lock_digest", "operation", "verification", "boundaries", "commands", "claim_boundary"}
    _require(set(contract) == expected_fields, "RS-065 contract fields are not closed")
    _require(contract["schema"] == "P5R0KMSLockSigningAdapterContractV1", "RS-065 contract schema drift")
    _require(contract["classification"] == "repository_definition_only" and contract["status"] == "blocked_pending_confidential_space_approval", "RS-065 contract must remain blocked")
    request = _load_canonical(REPOSITORY_ROOT / contract["request_path"], "RS-065 request")
    report = validate_unsigned_request(request)
    _require(contract["request_digest"] == report.request_digest and contract["unsigned_lock_digest"] == report.unsigned_lock_digest, "RS-065 request commitment drift")
    _require(contract["operation"]["interface"] == "services.p5_r0_evaluator.interfaces.Signer.sign_digest", "Signer interface drift")
    _require(contract["operation"]["signature_output"] is None and contract["operation"]["private_key_export"] is False, "RS-065 signature/private-key boundary drift")
    _require(contract["boundaries"]["local_execution_forbidden"] is True and contract["boundaries"]["production_promotion_allowed"] is False, "RS-065 local promotion boundary drift")
    return {"schema": contract["schema"], "status": contract["status"], "request_digest": report.request_digest, "unsigned_lock_digest": report.unsigned_lock_digest, "signature_present": False, "production_promotable": False}


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the repository-only RS-065 KMS lock-signing contract")
    parser.add_argument("command", choices=("validate",))
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate_contract(args.contract), sort_keys=True, separators=(",", ":")))
    except KMSLockSigningValidationError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = [
    "DEFAULT_CONTRACT", "DEFAULT_REQUEST", "KMSLockSigningCapability", "KMSLockSigningValidationError",
    "LockSigningReport", "load_and_validate_request", "operation_descriptor", "validate_contract",
    "validate_signed_response", "validate_unsigned_request",
]
