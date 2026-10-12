"""Authenticated WSGI boundary for the independent timing bridge service.

The module deliberately contains no deployment, cloud, IAM, or key-custody
logic.  A production process injects a fully constructed
:class:`TimingBridgeService` and an application authenticator through
``application.inject(...)`` or uses ``create_application`` directly.
"""

from __future__ import annotations

from threading import Lock
from typing import Any, Callable

from .canonical import canonical_bytes, parse_canonical
from .rfc3161 import validate_rfc3161_proof
from .timing_bridge import MAX_BRIDGE_REQUEST_BYTES
from .timing_bridge_service import BRIDGE_RECORD_SCHEMA, BRIDGE_RESPONSE_SCHEMA, TimingBridgeServiceError


MAX_REQUEST_BODY_BYTES = MAX_BRIDGE_REQUEST_BYTES
_ERROR_SCHEMA = "P5R0ErrorV1"
_ENVELOPE_FIELDS = frozenset({"schema", "record", "proof"})
_V3_FIELDS = frozenset(
    {
        "schema",
        "ledger_id",
        "run_id",
        "task_id",
        "event",
        "sequence",
        "previous_digest",
        "seed_digest",
        "payload_digest",
        "observed_at",
        "authority_id",
        "key_id",
        "public_key",
        "public_key_digest",
        "rfc3161_evidence_digest",
        "signature",
    }
)


def _payload(error: str) -> bytes:
    return canonical_bytes({"error": error, "schema": _ERROR_SCHEMA})


def _respond(start_response: Any, status: int, payload: bytes, *, allow: str | None = None) -> list[bytes]:
    headers = [
        ("content-type", "application/json"),
        ("cache-control", "no-store"),
        ("content-length", str(len(payload))),
    ]
    if allow is not None:
        headers.append(("allow", allow))
    start_response(f"{status} {'OK' if status < 400 else 'ERROR'}", headers)
    return [payload]


def _error(start_response: Any, status: int, category: str, *, allow: str | None = None) -> list[bytes]:
    return _respond(start_response, status, _payload(category), allow=allow)


def _headers(environ: dict[str, Any]) -> dict[str, Any]:
    result = {
        key[5:].lower().replace("_", "-"): value
        for key, value in environ.items()
        if key.startswith("HTTP_")
    }
    for key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
        if key in environ:
            result[key.lower().replace("_", "-")] = environ[key]
    return result


def _content_length(environ: dict[str, Any]) -> int:
    declared = environ.get("CONTENT_LENGTH")
    if declared is None or declared == "":
        # Never read an unbounded WSGI input stream.
        return MAX_REQUEST_BODY_BYTES + 1
    try:
        length = int(declared)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid content length") from exc
    if length < 0:
        raise ValueError("invalid content length")
    return length


def _validate_service(service: Any) -> None:
    if not callable(getattr(service, "handle", None)):
        raise ValueError("timing bridge service is required")
    if getattr(service, "production_ready", None) is not True:
        raise ValueError("production-ready timing bridge service is required")
    ledger = getattr(service, "ledger", None)
    if getattr(ledger, "durable", None) is not True:
        raise ValueError("durable timing bridge ledger is required")


def create_application(service: Any, authenticator: Callable[[dict[str, Any]], Any]) -> Callable[..., list[bytes]]:
    """Create the production timing bridge WSGI application.

    The factory intentionally refuses test-mode services and non-durable
    ledgers.  Authentication is supplied by the deployment and receives only
    normalized request headers; this module does not create credentials.
    """
    _validate_service(service)
    if not callable(authenticator):
        raise ValueError("timing bridge authenticator is required")
    return _TimingBridgeApplication(service, authenticator)


class _TimingBridgeApplication:
    def __init__(self, service: Any, authenticator: Callable[[dict[str, Any]], Any]):
        self._service = service
        self._authenticator = authenticator

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method = environ.get("REQUEST_METHOD")
        path = environ.get("PATH_INFO")
        if method != "POST":
            return _error(start_response, 405, "method not allowed", allow="POST")
        if path != "/v1/timing":
            return _error(start_response, 404, "not found")

        content_type = environ.get("CONTENT_TYPE")
        if not isinstance(content_type, str) or content_type.lower().split(";", 1)[0].strip() != "application/json":
            return _error(start_response, 415, "unsupported media type")

        try:
            length = _content_length(environ)
        except ValueError:
            return _error(start_response, 400, "invalid request")
        if length > MAX_REQUEST_BODY_BYTES:
            return _error(start_response, 413, "request body too large")

        try:
            stream = environ["wsgi.input"]
            body = stream.read(length)
        except Exception:
            return _error(start_response, 400, "invalid request")
        if not isinstance(body, bytes) or len(body) > MAX_REQUEST_BODY_BYTES:
            return _error(start_response, 413, "request body too large")

        try:
            parse_canonical(body)
        except Exception:
            return _error(start_response, 400, "invalid canonical JSON")

        try:
            authenticated = self._authenticator(_headers(environ))
            if authenticated is None or authenticated is False:
                raise PermissionError("authentication failed")
        except Exception:
            return _error(start_response, 401, "unauthorized")

        try:
            record = self._service.handle(body)
        except TimingBridgeServiceError:
            return _error(start_response, 422, "timing request rejected")
        except Exception:
            return _error(start_response, 503, "service unavailable")

        if (
            not isinstance(record, dict)
            or set(record) != _ENVELOPE_FIELDS
            or record.get("schema") != BRIDGE_RESPONSE_SCHEMA
            or not isinstance(record.get("record"), dict)
            or set(record["record"]) != _V3_FIELDS
            or record["record"].get("schema") != BRIDGE_RECORD_SCHEMA
            or not isinstance(record["record"].get("signature"), str)
            or not record["record"]["signature"]
            or not isinstance(record.get("proof"), dict)
        ):
            return _error(start_response, 503, "service unavailable")
        try:
            validate_rfc3161_proof(record["proof"])
            response = canonical_bytes(record)
        except Exception:
            return _error(start_response, 503, "service unavailable")
        return _respond(start_response, 200, response)


class _LockedApplication:
    """Fail-closed module entrypoint until a production app is injected."""

    def __init__(self):
        self._lock = Lock()
        self._delegate: Callable[..., list[bytes]] | None = None

    def inject(self, service: Any, authenticator: Callable[[dict[str, Any]], Any]) -> Callable[..., list[bytes]]:
        delegate = create_application(service, authenticator)
        with self._lock:
            if self._delegate is not None:
                raise RuntimeError("timing bridge application already injected")
            self._delegate = delegate
        return delegate

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        with self._lock:
            delegate = self._delegate
        if delegate is None:
            return _error(start_response, 503, "service unavailable")
        return delegate(environ, start_response)


# A WSGI server may import this object before deployment wiring runs.  It
# remains fail-closed rather than constructing an unauthenticated service.
application = _LockedApplication()


def inject_application(service: Any, authenticator: Callable[[dict[str, Any]], Any]) -> Callable[..., list[bytes]]:
    """Inject the production app behind the module-level fail-closed entrypoint."""
    return application.inject(service, authenticator)


__all__ = ["MAX_REQUEST_BODY_BYTES", "application", "create_application", "inject_application"]
