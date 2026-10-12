"""Repository-only RS-067 authority/transport binding validator.

This module validates a proposed self-custodied authority binding for the
selected evaluator KMS key candidate.  It never calls KMS, Confidential
Space, STS, GCS, FreeTSA, gcloud, a VM, or a task runner, and it never creates
an authority, approval, or signature.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from services.p5_r0_evaluator.canonical import b64decode, digest, parse_canonical

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover - the repository test environment pins cryptography.
    Ed25519PublicKey = None  # type: ignore[assignment,misc]


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = Path(__file__).with_name("p5-r0-authority-binding-contract.json")
_AUTHORITY_FIELDS = {"schema", "authority_id", "key_id", "public_key", "public_key_digest", "transport_attestation"}
_TRANSPORT_FIELDS = {"schema", "provider", "audience", "event"}
_KMS_FIELDS = {"key_version", "public_key", "public_key_digest", "authority_binding"}
_KMS_BINDING_FIELDS = {"schema", "authority_id", "key_id", "kms_key_version", "public_key_digest", "purpose", "binding_digest"}
_APPROVAL_FIELDS = {"schema", "environment", "approval_source", "approved", "attestation_verified", "project_authority", "local_execution", "approval_digest"}
_CLAIM_FIELDS = {"project_number", "project_id", "zone", "workload", "issuer", "image_digest", "debug_state", "tee", "hardware_model", "secure_boot", "smoke"}
_CLAIM_PATHS = {
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
_KEY_VERSION_RE = re.compile(
    r"^projects/[a-z][a-z0-9-]*/locations/[a-z0-9-]+/keyRings/[A-Za-z0-9_-]+/cryptoKeys/[A-Za-z0-9_-]+/cryptoKeyVersions/[1-9][0-9]*$"
)
_PROVIDER_RE = re.compile(
    r"^//iam\.googleapis\.com/projects/(?P<number>[0-9]+)/locations/global/workloadIdentityPools/(?P<pool>[a-z0-9-]+)/providers/(?P<provider>[a-z0-9-]+)$"
)
_PROJECT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
_ZONE_RE = re.compile(r"^[a-z][a-z0-9-]+$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED_PREFIX = "REQUIRED_INPUT:"


class AuthorityBindingValidationError(ValueError):
    """An RS-067 contract or candidate binding is not admissible."""


class AuthorityBindingBlockedError(AuthorityBindingValidationError):
    """The repository contract is structurally valid but lacks reviewed inputs."""


class AuthorityBindingReport(dict):
    """Small dict-compatible report for local review and tests."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuthorityBindingValidationError(message)


def _load_canonical(path: Path) -> dict[str, Any]:
    try:
        return parse_canonical(path.read_bytes())
    except Exception as exc:
        raise AuthorityBindingValidationError(f"contract is not canonical JSON: {path}") from exc


def _marker(value: Any, label: str) -> None:
    _require(isinstance(value, str) and value.startswith(_REQUIRED_PREFIX) and len(value) > len(_REQUIRED_PREFIX), f"{label} must remain a required-input marker")


def _validate_public_key(value: Any, label: str) -> bytes:
    _require(isinstance(value, str) and value, f"{label} is missing")
    try:
        raw = b64decode(value)
    except Exception as exc:
        raise AuthorityBindingValidationError(f"{label} is not canonical base64url") from exc
    _require(raw and __import__("base64").urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") == value, f"{label} is not canonical base64url")
    _require(len(raw) == 32, f"{label} must contain 32 Ed25519 bytes")
    try:
        Ed25519PublicKey.from_public_bytes(raw)
    except Exception as exc:
        raise AuthorityBindingValidationError(f"{label} is not an Ed25519 public key") from exc
    return raw


def _validate_authority(authority: Mapping[str, Any], *, markers: bool = False) -> dict[str, Any]:
    _require(isinstance(authority, Mapping) and set(authority) == _AUTHORITY_FIELDS, "authority metadata is not closed")
    _require(authority.get("schema") == "P5R0PublicAuthorityV4", "authority schema must be P5R0PublicAuthorityV4")
    for name in ("authority_id", "key_id", "public_key", "public_key_digest"):
        if markers:
            _marker(authority.get(name), f"authority.{name}")
        else:
            _require(isinstance(authority.get(name), str) and authority[name], f"authority.{name} is missing")
    transport = authority.get("transport_attestation")
    _require(isinstance(transport, Mapping) and set(transport) == _TRANSPORT_FIELDS, "authority transport metadata is not closed")
    _require(transport.get("schema") == "P5R0AuthorityTransportV1", "authority transport schema must be P5R0AuthorityTransportV1")
    for name in ("provider", "audience", "event"):
        if markers:
            _marker(transport.get(name), f"authority.transport_attestation.{name}")
        else:
            _require(isinstance(transport.get(name), str) and transport[name], f"authority transport {name} is missing")
    if not markers:
        public = _validate_public_key(authority["public_key"], "authority.public_key")
        _require(authority["public_key_digest"] == digest(authority["public_key"]), "authority public-key digest mismatch")
        return {**dict(authority), "_public_key_bytes": public}
    return dict(authority)


def _validate_marked_contract(contract: Mapping[str, Any]) -> None:
    expected = {
        "schema", "classification", "status", "custody_model", "evidence", "authority_binding",
        "signed_environment", "approval_requirements", "signature_state", "boundaries", "commands",
    }
    _require(set(contract) == expected, "RS-067 contract fields are not closed")
    _require(contract["schema"] == "P5R0SignedEnvironmentAuthorityBindingContractV1", "RS-067 contract schema drift")
    _require(contract["classification"] == "repository_definition_only", "RS-067 contract classification drift")
    _require(contract["status"] == "blocked_pending_reviewed_authority_and_confidential_space_approval", "RS-067 contract must remain blocked")
    _require(contract["custody_model"] == "self_custodied_diagnostic", "authority custody model drift")

    evidence = contract["evidence"]
    _require(isinstance(evidence, Mapping) and set(evidence) == {"rs_063", "rs_065", "rs_066"}, "RS-067 evidence references are not closed")
    _require(evidence["rs_065"] == {
        "request_digest": "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d",
        "unsigned_lock_digest": "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df",
        "authority_binding_digest": None,
        "signature": None,
    }, "RS-065 evidence binding drift")
    _require(evidence["rs_066"] == {"state": "BLOCKED", "authority_id": None, "key_id": None, "kms_key_version": None, "public_key": None, "public_key_digest": None, "transport_attestation": None}, "RS-066 must remain blocked and value-free")
    _require(isinstance(evidence["rs_063"], Mapping) and set(evidence["rs_063"]) == {"state", "approval_present", "production_values_present"}, "RS-063 evidence reference is not closed")
    _require(evidence["rs_063"] == {"state": "PASS_REVIEW", "approval_present": False, "production_values_present": False}, "RS-063 evidence boundary drift")

    binding = contract["authority_binding"]
    _require(isinstance(binding, Mapping) and set(binding) == {"authority_metadata", "required_authority", "kms"}, "authority binding section is not closed")
    _require(binding["authority_metadata"] is None, "actual authority metadata must remain null")
    _validate_authority(binding["required_authority"], markers=True)
    kms = binding["kms"]
    _require(isinstance(kms, Mapping) and set(kms) == {"key_version", "public_key", "public_key_digest", "authority_binding"}, "KMS binding input is not closed")
    _marker(kms["key_version"], "kms.key_version")
    _require(kms["public_key"] is None and kms["authority_binding"] is None, "unreviewed KMS values must remain null")
    _marker(kms["public_key_digest"], "kms.public_key_digest")

    environment = contract["signed_environment"]
    _require(isinstance(environment, Mapping) and set(environment) == {"provider", "audience", "event", "claims", "claim_paths"}, "signed-environment binding is not closed")
    for name in ("provider", "audience", "event"):
        _marker(environment[name], f"signed_environment.{name}")
    transport = binding["required_authority"]["transport_attestation"]
    _require(transport["provider"] == environment["provider"] and transport["audience"] == environment["audience"] and transport["event"] == environment["event"], "authority transport and environment binding drift")
    claims = environment["claims"]
    _require(isinstance(claims, Mapping) and set(claims) == _CLAIM_FIELDS, "signed-environment claims are not closed")
    for name, value in claims.items():
        _marker(value, f"signed_environment.claims.{name}")
    _require(environment["claim_paths"] == _CLAIM_PATHS, "signed-environment claim paths drift")

    _require(contract["approval_requirements"] == {
        "schema": "P5R0ConfidentialSpaceApprovalV1",
        "environment": "Confidential Space",
        "approval_source": "confidential_space_attestation",
        "approved": True,
        "attestation_verified": True,
        "project_authority": "self_custodied",
        "local_execution": False,
        "actual_approval": None,
    }, "signed-environment approval requirements drift")
    _require(contract["signature_state"] == {"signature": None, "signature_present": False, "production_promotable": False}, "signature state must remain unsigned")
    _require(contract["boundaries"] == {"kms_call_performed": False, "authority_created": False, "approval_created": False, "cloud_operations": [], "local_execution_forbidden": True, "production_promotion_allowed": False}, "RS-067 no-go boundaries drift")
    _require(isinstance(contract["commands"], list) and all(isinstance(command, str) and command.startswith("python3 -m") for command in contract["commands"]), "RS-067 commands must be local Python validation commands")


def validate_contract(path: Path = DEFAULT_CONTRACT) -> AuthorityBindingReport:
    """Validate the marker-only checked-in RS-067 contract."""
    contract = _load_canonical(Path(path))
    _validate_marked_contract(contract)
    return AuthorityBindingReport({"schema": contract["schema"], "status": contract["status"], "authority_metadata_present": False, "approval_present": False, "signature_present": False, "production_promotable": False})


def _validate_environment(environment: Mapping[str, Any], authority: Mapping[str, Any]) -> None:
    _require(isinstance(environment, Mapping) and set(environment) == {"provider", "audience", "event", "claims", "claim_paths"}, "signed-environment claims are not closed")
    provider = environment["provider"]
    audience = environment["audience"]
    _require(isinstance(provider, str) and _PROVIDER_RE.fullmatch(provider) is not None, "WIP provider is not canonical")
    _require(isinstance(audience, str) and audience.startswith("https://") and audience != provider, "WIP token audience must be separate from the provider resource")
    transport = authority["transport_attestation"]
    _require(transport["provider"] == provider and transport["audience"] == audience and transport["event"] == environment["event"], "authority transport does not match signed environment")
    claims = environment["claims"]
    _require(isinstance(claims, Mapping) and set(claims) == _CLAIM_FIELDS, "signed-environment claims are not closed")
    _require(isinstance(claims["project_number"], str) and claims["project_number"].isdigit(), "project_number claim is invalid")
    provider_match = _PROVIDER_RE.fullmatch(provider)
    _require(provider_match is not None and provider_match.group("number") == claims["project_number"], "WIP provider project does not match project claim")
    _require(isinstance(claims["project_id"], str) and _PROJECT_ID_RE.fullmatch(claims["project_id"]), "project_id claim is invalid")
    _require(isinstance(claims["zone"], str) and _ZONE_RE.fullmatch(claims["zone"]), "zone claim is invalid")
    _require(claims["workload"] == "evaluator", "workload claim is not evaluator")
    _require(claims["issuer"] == "https://confidentialcomputing.googleapis.com", "attestation issuer claim drift")
    for name in ("image_digest",):
        _require(isinstance(claims[name], str) and _DIGEST_RE.fullmatch(claims[name]), f"{name} claim is invalid")
    for name in ("debug_state", "tee", "hardware_model"):
        _require(isinstance(claims[name], str) and claims[name], f"{name} claim is missing")
    _require(claims["secure_boot"] is True and claims["smoke"] is False, "signed-environment secure-boot or smoke claim drift")
    _require(environment["claim_paths"] == _CLAIM_PATHS, "signed-environment claim paths drift")


def _validate_approval(approval: Mapping[str, Any] | None) -> bool:
    if approval is None:
        return False
    _require(isinstance(approval, Mapping) and set(approval) == _APPROVAL_FIELDS, "Confidential Space approval is not closed")
    _require(approval["schema"] == "P5R0ConfidentialSpaceApprovalV1", "approval schema drift")
    _require(approval["environment"] == "Confidential Space" and approval["approval_source"] == "confidential_space_attestation", "approval is not signed-environment authority")
    _require(approval["approved"] is True and approval["attestation_verified"] is True and approval["local_execution"] is False, "approval is absent or locally authored")
    _require(approval["project_authority"] == "self_custodied", "approval custody model drift")
    _require(approval["approval_digest"] == digest({key: value for key, value in approval.items() if key != "approval_digest"}), "approval digest mismatch")
    return True


def validate_candidate_binding(authority: Mapping[str, Any], kms: Mapping[str, Any], environment: Mapping[str, Any], approval: Mapping[str, Any] | None = None) -> AuthorityBindingReport:
    """Validate supplied review inputs without calling or creating anything."""
    checked_authority = _validate_authority(authority)
    _validate_environment(environment, checked_authority)
    _require(isinstance(kms, Mapping) and set(kms) == _KMS_FIELDS, "KMS binding fields are not closed")
    _require(isinstance(kms["key_version"], str) and _KEY_VERSION_RE.fullmatch(kms["key_version"]) is not None, "KMS key version is invalid")
    kms_public = _validate_public_key(kms["public_key"], "KMS public key")
    _require(kms["public_key_digest"] == digest(kms["public_key"]), "KMS public-key digest mismatch")
    _require(kms["public_key"] == authority["public_key"] and kms_public == checked_authority["_public_key_bytes"], "KMS public key does not match authority")
    binding = kms["authority_binding"]
    _require(isinstance(binding, Mapping) and set(binding) == _KMS_BINDING_FIELDS, "KMS authority binding is not closed")
    _require(binding["schema"] == "P5R0KMSAuthorityBindingV1", "KMS authority binding schema drift")
    _require(binding["authority_id"] == authority["authority_id"] and binding["key_id"] == authority["key_id"], "authority identifier binding mismatch")
    _require(binding["kms_key_version"] == kms["key_version"] and binding["public_key_digest"] == kms["public_key_digest"], "KMS version or public-key binding mismatch")
    _require(binding["purpose"] == "p5-r0-production-authority", "KMS binding purpose drift")
    _require(binding["binding_digest"] == digest({key: value for key, value in binding.items() if key != "binding_digest"}), "KMS authority binding digest mismatch")
    approval_present = _validate_approval(approval)
    return AuthorityBindingReport({"schema": "P5R0SignedEnvironmentAuthorityBindingReportV1", "authority_id": authority["authority_id"], "key_id": authority["key_id"], "kms_key_version": kms["key_version"], "approval_present": approval_present, "signature_present": False, "production_promotable": False})


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local-only RS-067 authority binding contract")
    parser.add_argument("command", choices=("validate",))
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate_contract(args.contract), sort_keys=True, separators=(",", ":")))
    except AuthorityBindingValidationError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = ["AuthorityBindingBlockedError", "AuthorityBindingReport", "AuthorityBindingValidationError", "DEFAULT_CONTRACT", "validate_candidate_binding", "validate_contract"]
