"""Signed, local-test-only prerequisite attestations for P3-R0.

These records are intentionally not release custody claims.  They bind a
locally provisioned P0, P1, or P2 test result into an immutable P3 lock and
are accepted only from an explicitly trusted local test key.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, sha256
from .protocol import P3ProtocolError, is_digest, validate_signed

_PHASE_SCHEMA = {
    "p0": "P0PhaseGoAttestationV1",
    "p1": "P1PhaseGoAttestationV1",
    "p2": "P2PhaseGoAttestationV1",
}
_REQUIRED = {"schema", "phase", "decision", "custody", "evidence_digest", "key_id", "signature"}


def local_attestation_digest(value: Mapping[str, Any]) -> str:
    """Digest the complete signed artifact, not an unauthenticated claim."""
    if not isinstance(value, Mapping):
        raise P3ProtocolError("local go object")
    return sha256(canonical_bytes(dict(value)))


def validate_local_phase_go(value: Mapping[str, Any], *, phase: str,
                            trusted_keys: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one signed local prerequisite without granting release status."""
    schema = _PHASE_SCHEMA.get(phase)
    if schema is None or not isinstance(value, Mapping) or set(value) != _REQUIRED:
        raise P3ProtocolError("local go schema")
    parsed = validate_signed(value, trusted_keys=trusted_keys, schema=schema)
    if (parsed["phase"] != phase or parsed["decision"] != "go"
            or parsed["custody"] != "local-test" or not is_digest(parsed["evidence_digest"])):
        raise P3ProtocolError("local go content")
    return parsed
