from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from typing import Any


class CanonicalError(ValueError):
    """An input is not a canonical protocol object."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _normalise(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        raise CanonicalError("floats are not protocol values")
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise CanonicalError("strings must be NFC")
        return value
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalError("object keys must be strings")
        return {key: _normalise(value[key]) for key in sorted(value)}
    raise CanonicalError(f"unsupported protocol value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(_normalise(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def parse_canonical(raw: bytes | str) -> dict[str, Any]:
    raw_bytes = raw.encode("utf-8") if isinstance(raw, str) else raw
    try:
        value = json.loads(raw_bytes.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanonicalError("invalid JSON") from exc
    if not isinstance(value, dict) or canonical_bytes(value) != raw_bytes:
        raise CanonicalError("JSON is not a canonical object")
    return value


def digest(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def signing_digest(value: dict[str, Any], *excluded: str) -> bytes:
    excluded_set = {"signature", *excluded}
    unsigned = {key: item for key, item in value.items() if key not in excluded_set}
    return hashlib.sha256(canonical_bytes(unsigned)).digest()


def b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def b64decode(value: str) -> bytes:
    if not isinstance(value, str):
        raise CanonicalError("base64 value")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise CanonicalError("invalid base64url") from exc
