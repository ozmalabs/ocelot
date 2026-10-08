"""Opt-in HTTPS seam for an independently operated RFC3161 timing bridge.

This module is deliberately only a client seam.  It does not construct or
provision the bridge endpoint, access credentials, RFC3161 tokens, or signing
keys.  The remote endpoint is expected to validate RFC3161 evidence and return
one canonical, bounded ``P5R0RFC3161TimingBridgeEnvelopeV1`` containing a
signed ``P5R0IndependentTimingAttestationV3`` record and its internal proof.
The evaluator verifies that proof locally before accepting the V3 record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .canonical import canonical_bytes, digest, parse_canonical
from .rfc3161 import RFC3161Config, RFC3161TimingEvidenceAdapter
from .timing import TimingAttestationError, TimingAuthorityConfig


MAX_BRIDGE_RESPONSE_BYTES = 512 * 1024
MAX_BRIDGE_REQUEST_BYTES = 4096


class TimingBridgeError(ValueError):
    """A bridge configuration, transport, or signed-record response failed closed."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        raise TimingBridgeError("timing bridge redirects are forbidden")


@dataclass(frozen=True)
class TimingBridgeConfig:
    """Public bridge policy; no default endpoint is supplied or provisioned."""

    endpoint: str
    authority: TimingAuthorityConfig
    rfc3161_config: RFC3161Config
    timeout_seconds: float = 5.0
    max_response_bytes: int = MAX_BRIDGE_RESPONSE_BYTES
    # A header value or zero-argument provider is injected by the evaluator
    # deployment.  Keep it out of reprs and never include it in errors/logs.
    authorization_header: str | Callable[[], str] | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.endpoint, str) or not self.endpoint:
            raise TimingBridgeError("timing bridge endpoint is required")
        parsed = urlsplit(self.endpoint)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise TimingBridgeError("timing bridge endpoint must be HTTPS")
        if parsed.query or parsed.fragment:
            raise TimingBridgeError("timing bridge endpoint must not contain query or fragment")
        if not isinstance(self.authority, TimingAuthorityConfig):
            raise TimingBridgeError("timing bridge authority is required")
        if not isinstance(self.rfc3161_config, RFC3161Config):
            raise TimingBridgeError("pinned RFC3161 configuration is required")
        if not isinstance(self.timeout_seconds, (int, float)) or not 0 < self.timeout_seconds <= 10:
            raise TimingBridgeError("timing bridge timeout")
        if type(self.max_response_bytes) is not int or not 0 < self.max_response_bytes <= MAX_BRIDGE_RESPONSE_BYTES:
            raise TimingBridgeError("timing bridge response bound")
        if self.authorization_header is not None and not isinstance(self.authorization_header, str) and not callable(self.authorization_header):
            raise TimingBridgeError("timing bridge authorization header is invalid")

    def authorization_value(self) -> str | None:
        """Return the injected bearer header without exposing it in diagnostics."""
        value = self.authorization_header() if callable(self.authorization_header) else self.authorization_header
        if value is None:
            return None
        if not isinstance(value, str) or not value.startswith("Bearer ") or not value[7:]:
            raise TimingBridgeError("timing bridge authorization header is invalid")
        if any(ord(char) < 0x20 or ord(char) == 0x7f for char in value):
            raise TimingBridgeError("timing bridge authorization header is invalid")
        return value


# Descriptive alias for callers that use the RFC3161 terminology.
RFC3161TimingBridgeConfig = TimingBridgeConfig


class HTTPSRFC3161TimingBridgeClient:
    """Validate signed V3 records returned by a fixed, bounded HTTPS bridge.

    Requests contain only public run/task/event identifiers and the already
    committed payload digest.  The client never accepts caller-selected URLs,
    redirects, non-canonical JSON, raw evidence, or raw timestamp tokens.
    """

    independent = True
    bridge_required = False

    def __init__(self, config: TimingBridgeConfig, *, opener: Any | None = None, rfc3161_adapter: RFC3161TimingEvidenceAdapter | None = None):
        if not isinstance(config, TimingBridgeConfig):
            raise TimingBridgeError("timing bridge configuration is required")
        if rfc3161_adapter is not None and not callable(getattr(rfc3161_adapter, "verify_proof", None)):
            raise TimingBridgeError("RFC3161 proof verifier is invalid")
        if rfc3161_adapter is not None and getattr(rfc3161_adapter, "config", None) != config.rfc3161_config:
            raise TimingBridgeError("RFC3161 proof verifier configuration mismatch")
        self.config = config
        self.authority = config.authority
        self._rfc3161 = rfc3161_adapter or RFC3161TimingEvidenceAdapter(config.rfc3161_config)
        self._opener = opener or build_opener(_NoRedirect())
        self._chains: dict[str, tuple[int, str | None]] = {}
        self._lock = threading.Lock()

    def _request_body(self, *, run_id: str, task_id: str, event: str, payload_digest: str) -> bytes:
        value = {
            "schema": "P5R0RFC3161TimingBridgeRequestV1",
            "run_id": run_id,
            "task_id": task_id,
            "event": event,
            "payload_digest": payload_digest,
        }
        raw = canonical_bytes(value)
        if len(raw) > MAX_BRIDGE_REQUEST_BYTES:
            raise TimingBridgeError("timing bridge request bound")
        return raw

    def _post(self, body: bytes) -> dict[str, Any]:
        try:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            authorization = self.config.authorization_value()
            if authorization is not None:
                headers["Authorization"] = authorization
            request = Request(
                self.config.endpoint,
                data=body,
                method="POST",
                headers=headers,
            )
            response = self._opener.open(request, timeout=self.config.timeout_seconds)
            if getattr(response, "status", 200) != 200:
                raise TimingBridgeError("timing bridge HTTP status")
            geturl = getattr(response, "geturl", None)
            if callable(geturl) and geturl() != self.config.endpoint:
                raise TimingBridgeError("timing bridge redirect")
            headers = getattr(response, "headers", None)
            content_type = headers.get("Content-Type") if headers is not None else None
            if not isinstance(content_type, str) or content_type.lower().split(";", 1)[0].strip() != "application/json":
                raise TimingBridgeError("timing bridge content type")
            raw = response.read(self.config.max_response_bytes + 1)
            if not isinstance(raw, bytes) or len(raw) > self.config.max_response_bytes:
                raise TimingBridgeError("timing bridge response too large")
            return parse_canonical(raw)
        except TimingBridgeError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise TimingBridgeError("timing bridge request failed") from exc
        except Exception as exc:
            raise TimingBridgeError("timing bridge request failed") from exc

    def restore_chain(self, *, run_id: str, sequence: int, previous_digest: str | None) -> None:
        """Restore the bridge validation head from durable evaluator state."""
        if not isinstance(run_id, str) or not run_id:
            raise TimingBridgeError("timing bridge run identity")
        if type(sequence) is not int or sequence < 0:
            raise TimingBridgeError("timing bridge chain sequence")
        if previous_digest is not None:
            if not isinstance(previous_digest, str) or len(previous_digest) != 71 or not previous_digest.startswith("sha256:"):
                raise TimingBridgeError("timing bridge previous digest")
            try:
                int(previous_digest[7:], 16)
            except ValueError as exc:
                raise TimingBridgeError("timing bridge previous digest") from exc
        with self._lock:
            current = self._chains.get(run_id)
            expected = (sequence, previous_digest)
            if current is not None and current != expected:
                raise TimingBridgeError("timing bridge chain head conflict")
            self._chains[run_id] = expected

    def record(self, *, run_id: str, task_id: str, event: str, payload_digest: str) -> dict[str, Any]:
        if not all(isinstance(value, str) and value for value in (run_id, task_id, event)):
            raise TimingBridgeError("timing bridge event metadata")
        if event not in {"task_issued", "result_received"}:
            raise TimingBridgeError("timing bridge event metadata")
        if not isinstance(payload_digest, str) or not payload_digest.startswith("sha256:") or len(payload_digest) != 71:
            raise TimingBridgeError("timing bridge payload digest")
        try:
            int(payload_digest[7:], 16)
        except ValueError as exc:
            raise TimingBridgeError("timing bridge payload digest") from exc
        with self._lock:
            last_sequence, previous = self._chains.get(run_id, (0, None))
            envelope = self._post(self._request_body(run_id=run_id, task_id=task_id, event=event, payload_digest=payload_digest))
            if not isinstance(envelope, dict) or set(envelope) != {"schema", "record", "proof"} or envelope.get("schema") != "P5R0RFC3161TimingBridgeEnvelopeV1":
                raise TimingBridgeError("timing bridge proof envelope schema")
            record = envelope.get("record")
            proof = envelope.get("proof")
            if not isinstance(record, dict) or not isinstance(proof, dict):
                raise TimingBridgeError("timing bridge proof envelope schema")
            try:
                evidence = self._rfc3161.verify_proof(
                    proof,
                    run_id=run_id,
                    task_id=task_id,
                    event=event,
                    payload_digest=payload_digest,
                    sequence=last_sequence + 1,
                    previous_digest=previous,
                )
            except Exception as exc:
                raise TimingBridgeError("timing bridge RFC3161 proof invalid") from exc
            evidence_digest = digest(evidence)
            if not isinstance(record, dict) or record.get("rfc3161_evidence_digest") != evidence_digest:
                raise TimingBridgeError("timing bridge evidence binding")
            try:
                if record.get("schema") != "P5R0IndependentTimingAttestationV3":
                    raise TimingAttestationError("timing bridge requires V3")
                record = self.authority.validate(
                    record,
                    run_id=run_id,
                    task_id=task_id,
                    event=event,
                    payload_digest=payload_digest,
                    previous_digest=previous,
                    last_sequence=last_sequence,
                )
            except Exception as exc:
                raise TimingBridgeError("timing bridge signed record invalid") from exc
            self._chains[run_id] = (record["sequence"], digest(record))
            return record


# Names kept intentionally explicit, with a compatibility alias for callers
# that call the seam a recorder rather than a client.
RFC3161TimingBridgeClient = HTTPSRFC3161TimingBridgeClient
IndependentTimingBridgeClient = HTTPSRFC3161TimingBridgeClient


__all__ = [
    "MAX_BRIDGE_REQUEST_BYTES",
    "MAX_BRIDGE_RESPONSE_BYTES",
    "TimingBridgeError",
    "TimingBridgeConfig",
    "RFC3161TimingBridgeConfig",
    "HTTPSRFC3161TimingBridgeClient",
    "RFC3161TimingBridgeClient",
    "IndependentTimingBridgeClient",
]
