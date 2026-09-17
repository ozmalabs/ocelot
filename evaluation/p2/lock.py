"""Cryptographically bound P2 release-lock attestation."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from evaluation.p0a.canonical import b64decode, b64encode, object_hash, sign, verify_signature
from .protocol import P2ProtocolError

ARTIFACT_NAMES = (
    "native_worker_binary", "native_evaluator_binary", "p2_image", "p2_bypass_image", "p2_python_bypass_image",
    "seccomp_policy", "sealed_input", "task_generator", "scoring_schema", "runtime_closure",
    "action_vocabulary", "native_rule", "native_seed", "outcome_vocabulary", "split_commitment",
)
_IMAGE_ARTIFACTS = frozenset({"p2_image", "p2_bypass_image", "p2_python_bypass_image"})
_THRESHOLDS = {
    "held_out_brier_min_milli": 750,
    "held_out_ece_max_milli": 100,
    "held_out_feasible_minimal_min_milli": 700,
    "required_controls": True,
    "required_safety_protocol_reconstruction_milli": 1000,
}
_REQUIRED = frozenset({
    "lock_schema", "key_id", "public_key", "evaluator_key_id", "evaluator_public_key",
    "receipt_key_id", "receipt_public_key", "artifacts", "thresholds", "content_hash", "signature",
})


def is_digest(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 71 and value.startswith("sha256:")
            and all(char in "0123456789abcdef" for char in value[7:]) and set(value[7:]) != {"0"})


def public_key_bytes(key: Any) -> bytes:
    public = key.public_key() if hasattr(key, "public_key") else key
    if not isinstance(public, Ed25519PublicKey):
        raise P2ProtocolError("P2 Ed25519 public key required")
    return public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def public_key_encoding(key: Any) -> str:
    return b64encode(public_key_bytes(key))


def public_key_from_encoding(value: Any) -> Ed25519PublicKey:
    if not isinstance(value, str):
        raise P2ProtocolError("P2 public key encoding")
    try:
        return Ed25519PublicKey.from_public_bytes(b64decode(value))
    except Exception as exc:
        raise P2ProtocolError("P2 public key encoding") from exc


def canonical_content_hash(lock: Mapping[str, Any]) -> str:
    return object_hash(dict(lock), "content_hash")


def make_release_lock(*, signing_key: Ed25519PrivateKey, key_id: str,
                      evaluator_key: Any, evaluator_key_id: str,
                      receipt_key: Any, receipt_key_id: str,
                      artifacts: Mapping[str, str]) -> dict[str, Any]:
    """Create a signed canonical lock; production staging supplies measured digests."""
    body = {
        "lock_schema": "P2ReleaseLockV2", "key_id": key_id,
        "public_key": public_key_encoding(signing_key),
        "evaluator_key_id": evaluator_key_id, "evaluator_public_key": public_key_encoding(evaluator_key),
        "receipt_key_id": receipt_key_id, "receipt_public_key": public_key_encoding(receipt_key),
        "artifacts": dict(artifacts), "thresholds": dict(_THRESHOLDS),
    }
    body["content_hash"] = canonical_content_hash(body)
    body["signature"] = sign(body, signing_key)
    return body


def validate_lock(lock: Mapping[str, Any], trusted_keys: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Verify the trusted signer, canonical content hash, and complete artifact manifest."""
    if not isinstance(lock, Mapping) or set(lock) != _REQUIRED or lock.get("lock_schema") != "P2ReleaseLockV2":
        raise P2ProtocolError("P2 lock schema")
    if not isinstance(lock.get("key_id"), str) or not isinstance(lock.get("evaluator_key_id"), str) or not isinstance(lock.get("receipt_key_id"), str):
        raise P2ProtocolError("P2 lock key id")
    if not isinstance(trusted_keys, Mapping) or lock["key_id"] not in trusted_keys:
        raise P2ProtocolError("P2 untrusted lock key")
    trusted = trusted_keys[lock["key_id"]]
    if public_key_encoding(trusted) != lock["public_key"]:
        raise P2ProtocolError("P2 lock key substitution")
    # Parse every encoded identity even when it is not the lock signer.
    public_key_from_encoding(lock["evaluator_public_key"])
    public_key_from_encoding(lock["receipt_public_key"])
    artifacts = lock.get("artifacts")
    if not isinstance(artifacts, Mapping) or set(artifacts) != set(ARTIFACT_NAMES) or any(not is_digest(artifacts.get(name)) for name in ARTIFACT_NAMES):
        raise P2ProtocolError("P2 lock artifact manifest")
    if lock.get("thresholds") != _THRESHOLDS:
        raise P2ProtocolError("P2 lock thresholds")
    if lock.get("content_hash") != canonical_content_hash(lock):
        raise P2ProtocolError("P2 lock content hash")
    try:
        verify_signature(dict(lock), trusted)
    except Exception as exc:
        raise P2ProtocolError("P2 lock signature") from exc
    return dict(lock)
