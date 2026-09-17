"""Strict canonical JSON and Ed25519 bindings for the local P0-A protocol."""
from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class ProtocolError(ValueError):
    """An untrusted protocol object failed a structural or cryptographic check."""


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _normalise(value: Any) -> Any:
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        raise ProtocolError("floats are not valid protocol values")
    if isinstance(value, str):
        normal = unicodedata.normalize("NFC", value)
        if normal != value:
            raise ProtocolError("protocol strings must be NFC")
        return value
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ProtocolError("protocol object keys must be strings")
        return {key: _normalise(value[key]) for key in sorted(value)}
    raise ProtocolError(f"unsupported protocol value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(_normalise(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def parse_canonical(raw: bytes | str) -> dict[str, Any]:
    raw_bytes = raw.encode("utf-8") if isinstance(raw, str) else raw
    try:
        parsed = json.loads(raw_bytes.decode("utf-8"), object_pairs_hook=_pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise ProtocolError("protocol object must be a JSON object")
    if canonical_bytes(parsed) != raw_bytes:
        raise ProtocolError("protocol JSON is not canonical")
    return parsed


def sha256(value: bytes | dict[str, Any]) -> str:
    raw = canonical_bytes(value) if isinstance(value, dict) else value
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def unsigned(obj: dict[str, Any], *excluded: str) -> dict[str, Any]:
    return {key: value for key, value in obj.items() if key not in set(excluded)}


def object_hash(obj: dict[str, Any], *excluded: str) -> str:
    return sha256(unsigned(obj, "signature", *excluded))


def b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def b64decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:  # pragma: no cover - backend-specific decoder details
        raise ProtocolError("invalid base64url") from exc


def sign(obj: dict[str, Any], key: Ed25519PrivateKey, *excluded: str) -> str:
    digest = hashlib.sha256(canonical_bytes(unsigned(obj, "signature", *excluded))).digest()
    return b64encode(key.sign(digest))


def verify_signature(obj: dict[str, Any], key: Ed25519PublicKey, *excluded: str) -> None:
    signature = obj.get("signature")
    if not isinstance(signature, str):
        raise ProtocolError("missing signature")
    digest = hashlib.sha256(canonical_bytes(unsigned(obj, "signature", *excluded))).digest()
    try:
        key.verify(b64decode(signature), digest)
    except (InvalidSignature, ValueError) as exc:
        raise ProtocolError("invalid signature") from exc
