from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import threading
from typing import Any, Protocol

from .canonical import b64decode, digest, signing_digest


class TimingAttestationError(ValueError):
    pass


@dataclass(frozen=True)
class TimingAuthorityConfig:
    """Public, externally reviewed identity of the independent timing ledger."""

    authority_id: str
    key_id: str
    ledger_id: str
    public_key_digest: str

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value for value in (self.authority_id, self.key_id, self.ledger_id)):
            raise TimingAttestationError("timing authority identity")
        _digest_value(self.public_key_digest, "timing public key")

    def validate(self, value: dict[str, Any], *, run_id: str, task_id: str, event: str,
                 payload_digest: str, previous_digest: str | None = None,
                 last_sequence: int | None = None) -> dict[str, Any]:
        return validate_attestation(
            value, run_id=run_id, task_id=task_id, event=event,
            payload_digest=payload_digest, expected_authority_id=self.authority_id,
            expected_key_id=self.key_id,
            expected_public_key_digest=self.public_key_digest,
            expected_ledger_id=self.ledger_id, previous_digest=previous_digest,
            last_sequence=last_sequence,
        )


class ExternallyKeyedTimingAttestor:
    """Adapter for an independently operated recorder.

    The recorder is deliberately injected.  This module never creates a cloud
    client, reads ambient credentials, or signs timing records locally.
    """

    independent = True

    def __init__(self, authority: TimingAuthorityConfig, recorder: Any):
        if recorder is None or not callable(getattr(recorder, "record", None)):
            raise TimingAttestationError("external timing recorder is required")
        self.authority = authority
        self.recorder = recorder
        self._chains: dict[str, tuple[int, str | None]] = {}
        self._lock = threading.Lock()

    def record(self, *, run_id: str, task_id: str, event: str, payload_digest: str) -> dict[str, Any]:
        with self._lock:
            last_sequence, previous = self._chains.get(run_id, (0, None))
            value = self.recorder.record(run_id=run_id, task_id=task_id, event=event, payload_digest=payload_digest)
            if not isinstance(value, dict):
                raise TimingAttestationError("external timing recorder returned invalid record")
            value = self.authority.validate(
                value, run_id=run_id, task_id=task_id, event=event,
                payload_digest=payload_digest, previous_digest=previous,
                last_sequence=last_sequence,
            )
            self._chains[run_id] = (value["sequence"], digest(value))
            return value


class TimingAttestor(Protocol):
    """Independent event/seed ledger, not a caller-submitted timestamp."""
    def record(self, *, run_id: str, task_id: str, event: str, payload_digest: str) -> dict[str, Any]: ...


def _digest_value(value: Any, name: str) -> None:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise TimingAttestationError(f"{name} digest")
    try:
        int(value[7:], 16)
    except ValueError as exc:
        raise TimingAttestationError(f"{name} digest") from exc


def validate_attestation(
    value: dict[str, Any], *, run_id: str, task_id: str, event: str,
    payload_digest: str, expected_authority_id: str | None = None,
    expected_key_id: str | None = None, expected_public_key_digest: str | None = None,
    expected_ledger_id: str | None = None, previous_digest: str | None = None,
    last_sequence: int | None = None,
) -> dict[str, Any]:
    """Validate a service timing record or a signed independent V2 record.

    V1 is retained as a diagnostic compatibility format. Only V2 records with
    an independently pinned authority are eligible for certification.
    """
    if not isinstance(value, dict):
        raise TimingAttestationError("timing attestation schema")
    schema = value.get("schema")
    if schema == "P5R0TimingAttestationV1":
        fields = {"schema", "run_id", "task_id", "event", "sequence", "seed_digest", "payload_digest", "observed_at", "authority_id", "signature"}
        if set(value) != fields:
            raise TimingAttestationError("timing attestation schema")
        for key in ("run_id", "task_id", "event", "observed_at", "authority_id", "signature"):
            if not isinstance(value.get(key), str) or not value[key]:
                raise TimingAttestationError("timing metadata")
    elif schema == "P5R0IndependentTimingAttestationV2":
        fields = {"schema", "ledger_id", "run_id", "task_id", "event", "sequence", "previous_digest", "seed_digest", "payload_digest", "observed_at", "authority_id", "key_id", "public_key", "public_key_digest", "signature"}
        if set(value) != fields or value.get("event") not in {"task_issued", "result_received"}:
            raise TimingAttestationError("independent timing attestation schema")
        for key in ("ledger_id", "run_id", "task_id", "event", "authority_id", "key_id", "public_key", "public_key_digest", "signature"):
            if not isinstance(value.get(key), str) or not value[key]:
                raise TimingAttestationError("independent timing metadata")
        if value.get("previous_digest") is not None:
            _digest_value(value["previous_digest"], "previous")
        try:
            raw_key = b64decode(value["public_key"])
            if len(raw_key) != 32 or digest(value["public_key"]) != value["public_key_digest"]:
                raise ValueError("key binding")
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            Ed25519PublicKey.from_public_bytes(raw_key).verify(b64decode(value["signature"]), signing_digest(value))
        except Exception as exc:
            raise TimingAttestationError("independent timing signature") from exc
        if expected_key_id is not None and value["key_id"] != expected_key_id:
            raise TimingAttestationError("independent timing key mismatch")
        if expected_public_key_digest is not None and value["public_key_digest"] != expected_public_key_digest:
            raise TimingAttestationError("independent timing public key mismatch")
        if expected_ledger_id is not None and value["ledger_id"] != expected_ledger_id:
            raise TimingAttestationError("independent timing ledger mismatch")
        if last_sequence is not None and value["sequence"] != last_sequence + 1:
            raise TimingAttestationError("independent timing sequence")
        if previous_digest is not None and value["previous_digest"] != previous_digest:
            raise TimingAttestationError("independent timing chain")
    else:
        raise TimingAttestationError("timing attestation schema")
    if value.get("run_id") != run_id or value.get("task_id") != task_id or value.get("event") != event or value.get("payload_digest") != payload_digest:
        raise TimingAttestationError("timing attestation binding")
    if type(value.get("sequence")) is not int or value["sequence"] < 1:
        raise TimingAttestationError("timing sequence")
    for key in ("seed_digest", "payload_digest"):
        _digest_value(value.get(key), key)
    try:
        parsed = datetime.fromisoformat(value["observed_at"].replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None or not value["observed_at"].endswith("Z"):
            raise ValueError("UTC required")
    except Exception as exc:
        raise TimingAttestationError("timing observed_at") from exc
    if expected_authority_id is not None and value.get("authority_id") != expected_authority_id:
        raise TimingAttestationError("timing authority mismatch")
    return value


def timing_digest(attestation: dict[str, Any] | None) -> str | None:
    return digest(attestation) if attestation is not None else None


TIME_BUCKETS = ("<100ms", "<1s", "<10s", "<100s", "timeout")


def coarse_wall_bucket(duration_ms: int) -> str:
    """Reduce a server-observed wall interval; raw timing is never persisted."""
    if duration_ms >= 100_000:
        return "timeout"
    if duration_ms < 100:
        return "<100ms"
    if duration_ms < 1_000:
        return "<1s"
    if duration_ms < 10_000:
        return "<10s"
    return "<100s"
