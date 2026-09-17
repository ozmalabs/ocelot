"""Verified manifest registration; only an external launcher may create a run."""
from __future__ import annotations

from dataclasses import dataclass
import time
import uuid
from typing import Any

from .canonical import ProtocolError, object_hash, verify_signature

_MANIFEST_FIELDS = frozenset({
    "schema", "run_id", "evaluation", "issuer", "key_id", "issued_at_unix_ms",
    "expires_at_unix_ms", "control_plane_digest", "broker_image_digest",
    "agent_build_digest", "input_snapshot_digest", "seed_snapshot_digest",
    "enabled_methods", "limits", "revocation_generation", "signature",
})
_DIGEST_FIELDS = ("control_plane_digest", "broker_image_digest", "agent_build_digest",
                  "input_snapshot_digest", "seed_snapshot_digest")


@dataclass(frozen=True)
class VerifiedManifest:
    body: dict[str, Any]
    manifest_hash: str
    local_harness_only: bool = True

    @property
    def run_id(self) -> str:
        return self.body["run_id"]

    @property
    def enabled_methods(self) -> frozenset[str]:
        return frozenset(self.body["enabled_methods"])


class ManifestVerifier:
    """Verification-only authority; its private key is intentionally not a run input."""

    def __init__(self, keys: dict[str, Any], *, now_ms=None):
        self._keys = dict(keys)
        self._now_ms = now_ms or (lambda: int(time.time() * 1000))
        self._runs: set[str] = set()

    def verify(self, manifest: dict[str, Any], *, expected_digests: dict[str, str] | None = None,
               allow_fixture_methods: bool = False) -> VerifiedManifest:
        if set(manifest) != _MANIFEST_FIELDS:
            raise ProtocolError("manifest fields are not exact")
        if manifest.get("schema") != "EvaluationManifestV1" or manifest.get("evaluation") is not True:
            raise ProtocolError("not an evaluation manifest")
        if not isinstance(manifest.get("run_id"), str):
            raise ProtocolError("invalid run_id")
        try:
            uuid.UUID(manifest["run_id"], version=4)
        except (ValueError, AttributeError) as exc:
            raise ProtocolError("run_id must be UUIDv4") from exc
        key = self._keys.get(manifest.get("key_id"))
        if key is None:
            raise ProtocolError("unknown manifest key")
        verify_signature(manifest, key)
        if not isinstance(manifest["enabled_methods"], list) or any(
                not isinstance(method, str) for method in manifest["enabled_methods"]):
            raise ProtocolError("invalid enabled_methods")
        if manifest["enabled_methods"] and not allow_fixture_methods:
            raise ProtocolError("P0-A manifests enable no methods")
        if not isinstance(manifest["issued_at_unix_ms"], int) or not isinstance(manifest["expires_at_unix_ms"], int):
            raise ProtocolError("manifest times must be integers")
        if manifest["expires_at_unix_ms"] < self._now_ms():
            raise ProtocolError("manifest expired")
        if manifest["expires_at_unix_ms"] < manifest["issued_at_unix_ms"]:
            raise ProtocolError("manifest time range invalid")
        for field in _DIGEST_FIELDS:
            value = manifest[field]
            if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
                raise ProtocolError(f"invalid {field}")
            if expected_digests and expected_digests.get(field) != value:
                raise ProtocolError(f"{field} mismatch")
        if not isinstance(manifest["limits"], dict) or set(manifest["limits"]) != {
                "wall_ms", "cpu_ms", "memory_bytes", "max_requests", "max_receipts"}:
            raise ProtocolError("invalid limits")
        if any(type(value) is not int or value < 0 for value in manifest["limits"].values()):
            raise ProtocolError("invalid limits")
        if type(manifest["revocation_generation"]) is not int or manifest["revocation_generation"] < 0:
            raise ProtocolError("invalid revocation generation")
        if manifest["run_id"] in self._runs:
            raise ProtocolError("run_id already registered")
        self._runs.add(manifest["run_id"])
        return VerifiedManifest(dict(manifest), object_hash(manifest))


def make_attestation(manifest: VerifiedManifest, *, endpoint: str, started_at_unix_ms: int,
                     signer, key_id: str) -> dict[str, Any]:
    """Create the launcher-signed local-only attestation record."""
    from .canonical import sign
    body = {
        "schema": "EvaluationAttestationV1", "run_id": manifest.run_id,
        "manifest_hash": manifest.manifest_hash,
        "verified_control_plane_digest": manifest.body["control_plane_digest"],
        "verified_agent_build_digest": manifest.body["agent_build_digest"],
        "verified_input_snapshot_digest": manifest.body["input_snapshot_digest"],
        "broker_endpoint": endpoint, "started_at_unix_ms": started_at_unix_ms,
        "local_harness_only": True, "key_id": key_id,
    }
    body["signature"] = sign(body, signer)
    return body
