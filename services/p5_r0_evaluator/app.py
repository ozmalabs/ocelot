from __future__ import annotations

from typing import Any

from .canonical import canonical_bytes
from .confidential_space import ConfidentialSpaceAdapter, create_locked_bootstrap


MAX_REQUEST_BODY_BYTES = 1_048_576


def create_service(*, timing_recorder_factory=None) -> ConfidentialSpaceAdapter:
    """Return a locked adapter; production timing is injected only at activation."""
    return create_locked_bootstrap(timing_recorder_factory=timing_recorder_factory)


# Importing the WSGI app parses policy only. It does not create ADC clients,
# fetch GCS objects, load truth, or initialize KMS until attestation succeeds.
service = create_service()


def application(environ: dict[str, Any], start_response: Any):
    try:
        declared = environ.get("CONTENT_LENGTH")
        if declared is None or declared == "":
            length = MAX_REQUEST_BODY_BYTES + 1
        else:
            try:
                length = int(declared)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid content length") from exc
            if length < 0:
                raise ValueError("invalid content length")
            if length > MAX_REQUEST_BODY_BYTES:
                payload = canonical_bytes({"schema": "P5R0ErrorV1", "error": "request body too large"})
                start_response("413 ERROR", [("content-type", "application/json"), ("cache-control", "no-store"), ("content-length", str(len(payload)))])
                return [payload]
        body = environ["wsgi.input"].read(length)
        if len(body) > MAX_REQUEST_BODY_BYTES:
            payload = canonical_bytes({"schema": "P5R0ErrorV1", "error": "request body too large"})
            start_response("413 ERROR", [("content-type", "application/json"), ("cache-control", "no-store"), ("content-length", str(len(payload)))])
            return [payload]
        headers = {key[5:].lower().replace("_", "-"): value for key, value in environ.items() if key.startswith("HTTP_")}
        status, response_headers, payload = service.dispatch(environ["REQUEST_METHOD"], environ["PATH_INFO"], body, headers)
    except ValueError:
        payload = canonical_bytes({"schema": "P5R0ErrorV1", "error": "invalid content length"})
        status, response_headers = 400, {"content-type": "application/json", "cache-control": "no-store"}
    except Exception:
        status, response_headers, payload = 503, {"content-type": "application/json", "cache-control": "no-store"}, b'{"error":"service initialization failure; fail closed","schema":"P5R0ErrorV1"}'
    start_response(f"{status} {'OK' if status < 400 else 'ERROR'}", [(key, value) for key, value in response_headers.items()] + [("content-length", str(len(payload)))])
    return [payload]
