from __future__ import annotations

"""Opaque, redacted binding between verified startup and future worker evidence.

This module deliberately does not contain a public constructor/factory.  The
adapter is the only production code that can call ``_build_verified...``.  The
private seal also prevents a dict, dataclass replacement, or caller metadata
from being accepted as a verified binding by the service.
"""

from dataclasses import dataclass
from typing import Any, Mapping

from .canonical import digest


class AttestationBindingError(ValueError):
    """The verified startup/token/policy binding is invalid."""


_BINDING_SEAL = object()
_BINDING_SCHEMA = "P5R0VerifiedAttestationBindingV1"
_BINDING_REGISTRY: dict[int, tuple["VerifiedAttestationBinding", tuple[Any, ...]]] = {}


@dataclass(frozen=True, init=False)
class VerifiedAttestationBinding:
    """Redacted, immutable evidence of one verified attestation activation.

    Raw attestation claims, nonce, subject token, and federated access token
    are intentionally not retained.  The private constructor seal means that
    service callers cannot manufacture this type from a public dict.
    """

    token_digest: str
    federated_token_digest: str
    claims_digest: str
    image_digest: str
    project_number: str
    project_id: str
    zone: str
    hardware_model: str
    secure_boot: bool
    tee: str
    workload: str
    policy_digest: str
    claim_paths_digest: str
    attestation_claims_digest: str
    wip_policy_digest: str
    provider: str
    binding_digest: str

    def __init__(self, **values: Any) -> None:
        seal = values.pop("_seal", None)
        if seal is not _BINDING_SEAL:
            raise TypeError("verified attestation binding is adapter-created")
        fields = tuple(self.__dataclass_fields__)
        if set(values) != set(fields):
            raise TypeError("verified attestation binding fields are closed")
        for field in fields:
            object.__setattr__(self, field, values[field])

    @property
    def schema(self) -> str:
        return _BINDING_SCHEMA

    @property
    def secureboot(self) -> bool:
        return self.secure_boot

    @property
    def access_token_digest(self) -> str:
        """Compatibility name matching startup federation evidence."""
        return self.federated_token_digest

    @property
    def attestation_token_digest(self) -> str:
        return self.token_digest

    def as_public_dict(self) -> dict[str, Any]:
        """Return only the non-secret commitment fields."""
        if not _is_registered_attestation_binding(self):
            raise AttestationBindingError("verified attestation binding is not adapter-issued")
        return {"schema": _BINDING_SCHEMA, **{
            field: getattr(self, field) for field in self.__dataclass_fields__
        }}


def _binding_snapshot(value: VerifiedAttestationBinding) -> tuple[Any, ...]:
    return tuple(getattr(value, field) for field in value.__dataclass_fields__)


def _is_registered_attestation_binding(value: Any) -> bool:
    if type(value) is not VerifiedAttestationBinding:
        return False
    entry = _BINDING_REGISTRY.get(id(value))
    return entry is not None and entry[0] is value and _binding_snapshot(value) == entry[1]


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise AttestationBindingError(f"{name} is not a digest")
    if any(char not in "0123456789abcdef" for char in value[7:]):
        raise AttestationBindingError(f"{name} is not a digest")
    return value


def _claim(claims: Mapping[str, Any], path: str) -> Any:
    current: Any = claims
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise AttestationBindingError(f"attestation claim {path} is missing")
        current = current[part]
    return current


def _build_verified_attestation_binding(attestation: Any, token: Any, policy: Any) -> VerifiedAttestationBinding:
    """Build a binding from the adapter's verified objects and locked policy.

    Imports are intentionally local to avoid making this module own the
    attestation types or creating a circular import.  Exact type checks keep
    arbitrary lookalike dictionaries/objects out of the adapter boundary.
    """
    from .confidential_space import FederatedAccessToken, LockedBootstrapConfig, VerifiedAttestation

    if not isinstance(attestation, VerifiedAttestation):
        raise AttestationBindingError("binding requires a verified attestation")
    if not isinstance(token, FederatedAccessToken):
        raise AttestationBindingError("binding requires a federated access token")
    if not isinstance(policy, LockedBootstrapConfig):
        raise AttestationBindingError("binding requires locked bootstrap policy")
    if not isinstance(attestation.claims, dict) or not attestation.claims:
        raise AttestationBindingError("verified claims are invalid")
    if not isinstance(attestation.subject_token, str) or not attestation.subject_token:
        raise AttestationBindingError("attestation token is invalid")
    if token.token_type != "Bearer" or not token.access_token:
        raise AttestationBindingError("federated token is invalid")
    if token.expires_at <= int(policy.clock()):
        raise AttestationBindingError("federated token is expired")

    expected = {
        "image_digest": policy.image_digest,
        "project_number": policy.project_number,
        "project_id": policy.project_id,
        "zone": policy.zone,
        "debug_state": policy.debug_state,
        "tee": policy.tee,
        "hardware_model": policy.hardware_model,
        "secure_boot": policy.secure_boot,
        "workload": policy.workload,
    }
    for name, expected_value in expected.items():
        if _claim(attestation.claims, policy.claim_paths[name]) != expected_value:
            raise AttestationBindingError(f"attestation {name} mismatch")

    claims_digest = digest(attestation.claims)
    values = {
        "token_digest": digest(attestation.subject_token),
        "federated_token_digest": digest(token.access_token),
        "claims_digest": claims_digest,
        "image_digest": policy.image_digest,
        "project_number": policy.project_number,
        "project_id": policy.project_id,
        "zone": policy.zone,
        "hardware_model": policy.hardware_model,
        "secure_boot": policy.secure_boot,
        "tee": policy.tee,
        "workload": policy.workload,
        "policy_digest": policy.policy_digest,
        "claim_paths_digest": policy.claim_paths_digest,
        "attestation_claims_digest": policy.attestation_claims_digest,
        "wip_policy_digest": policy.wip_policy_digest,
        "provider": policy.wip_provider,
    }
    for name in ("claims_digest", "policy_digest", "claim_paths_digest", "attestation_claims_digest", "wip_policy_digest"):
        _digest(values[name], name)
    values["binding_digest"] = digest({"schema": _BINDING_SCHEMA, **values})
    binding = VerifiedAttestationBinding(**values, _seal=_BINDING_SEAL)
    _BINDING_REGISTRY[id(binding)] = (binding, _binding_snapshot(binding))
    return binding


__all__ = ["AttestationBindingError", "VerifiedAttestationBinding"]
