"""Dedicated Confidential Space workload entrypoint.

Cloud Run keeps its existing ``app`` entrypoint.  This module is intentionally
separate so the Confidential Space image has an explicit, reviewable process
entrypoint whose only startup path is the locked adapter.
"""

from __future__ import annotations

import os
from typing import Any, Callable

from .canonical import canonical_bytes, digest
from .confidential_space import (
    CONFIDENTIAL_SPACE_SMOKE_PAYLOAD_DIGEST,
    CONFIDENTIAL_SPACE_SMOKE_RUN_ID,
    CONFIDENTIAL_SPACE_SMOKE_TASK_ID,
    ConfidentialSpaceAdapter,
    ConfidentialSpaceError,
    create_locked_bootstrap,
    create_timing_bridge_attestor,
)


MAX_REQUEST_BODY_BYTES = 1_048_576


def _smoke_failure_detail(error: BaseException) -> str:
    message = str(error).lower().replace("_", " ")
    if isinstance(error, TypeError):
        frames = __import__("traceback").extract_tb(error.__traceback__)
        frame = frames[-1]
        caller = frames[-2] if len(frames) > 1 else frame
        return "type_error_{}_{}_caller_{}_{}".format(
            frame.filename.rsplit("/", 1)[-1], frame.lineno,
            caller.filename.rsplit("/", 1)[-1], caller.lineno,
        )
    if "kms public key type error line " in message:
        return "kms_public_key_type_error_" + message.split("kms public key type error line ", 1)[1].replace(" ", "_")
    for marker, category in (
        ("permission denied", "kms_public_key_permission_denied"),
        ("authentication failed", "kms_public_key_authentication_failed"),
        ("transport failed", "kms_public_key_transport_failed"),
        ("deadline exceeded", "kms_public_key_deadline_exceeded"),
        ("attribute error", "kms_public_key_attribute_error"),
        ("type error", "kms_public_key_type_error"),
        ("invalid argument", "kms_public_key_invalid_argument"),
        ("value error", "kms_public_key_value_error"),
        ("unknown client error", "kms_public_key_unknown_client_error"),
        ("public key does not match", "kms_public_key_mismatch"),
        ("public key unavailable", "kms_public_key_unavailable"),
        ("not ec_sign_ed25519", "kms_algorithm_mismatch"),
        ("mismatch", "claim_or_policy_mismatch"),
        ("signature", "signature_failure"),
        ("launcher", "launcher_failure"),
        ("sts", "sts_failure"),
        ("federated", "federated_token_failure"),
        ("timing", "timing_failure"),
        ("kms", "kms_failure"),
        ("gcs", "gcs_failure"),
    ):
        if marker in message:
            return category
    return type(error).__name__


def create_service(*, timing_attestor_factory=None, timing_recorder_factory=None) -> ConfidentialSpaceAdapter:
    """Construct policy-only state; bridge auth is deferred until activation."""
    if timing_attestor_factory is None and timing_recorder_factory is None:
        timing_attestor_factory = create_timing_bridge_attestor
    return create_locked_bootstrap(
        timing_attestor_factory=timing_attestor_factory,
        timing_recorder_factory=timing_recorder_factory,
    )


def run_startup_smoke(adapter: ConfidentialSpaceAdapter, *, emit: Callable[[str], Any] = print) -> dict[str, Any]:
    """Run the locked, one-shot diagnostic bridge smoke and emit redacted JSON.

    This is intentionally not part of WSGI dispatch.  The smoke image is
    committed to this path by the attestation/WIP policy, and any dependency
    or record failure stops startup after emitting only public digests.
    """
    if getattr(adapter, "_diagnostic_smoke_ran", False):
        raise ConfidentialSpaceError("diagnostic smoke is one-shot")
    adapter._diagnostic_smoke_ran = True
    timing: dict[str, Any] | None = None
    try:
        if adapter.config.confidential_space_smoke is not True:
            raise ConfidentialSpaceError("diagnostic smoke policy is not enabled")
        active_service = adapter.activate_attested_service()
        attestor = getattr(active_service, "timing_attestor", None)
        if (getattr(active_service, "timing_certified", False) is not True
                or getattr(attestor, "independent", False) is not True
                or not callable(getattr(attestor, "record", None))):
            raise ConfidentialSpaceError("independent timing attestor is unavailable")
        record = attestor.record(
            run_id=CONFIDENTIAL_SPACE_SMOKE_RUN_ID,
            task_id=CONFIDENTIAL_SPACE_SMOKE_TASK_ID,
            event="task_issued",
            payload_digest=CONFIDENTIAL_SPACE_SMOKE_PAYLOAD_DIGEST,
        )
        if (not isinstance(record, dict)
                or record.get("schema") not in {"P5R0IndependentTimingAttestationV2", "P5R0IndependentTimingAttestationV3"}
                or type(record.get("sequence")) is not int
                or record["sequence"] != 1):
            raise ConfidentialSpaceError("timing smoke record is invalid")
        timing = {
            "record_digest": digest(record),
            "schema": record["schema"],
            "sequence": record["sequence"],
        }
        result = {
            "schema": "P5R0ConfidentialSpaceSmokeV1",
            "status": "passed",
            "startup_evidence_digest": digest(adapter.startup_evidence),
            "startup_status": adapter.startup_evidence["status"],
            "bootstrap_failure": adapter.startup_evidence.get("last_failure"),
            "timing_record_digest": timing["record_digest"],
            "timing_schema": timing["schema"],
            "timing_sequence": timing["sequence"],
        }
    except Exception as exc:
        result = {
            "schema": "P5R0ConfidentialSpaceSmokeV1",
            "status": "failed",
            "startup_evidence_digest": digest(adapter.startup_evidence),
            "startup_status": adapter.startup_evidence["status"],
            "bootstrap_failure": adapter.startup_evidence.get("last_failure"),
            "failure_type": type(exc).__name__,
            "failure_detail": _smoke_failure_detail(exc),
            "timing_record_digest": None,
            "timing_schema": None,
            "timing_sequence": None,
        }
        emit(canonical_bytes(result).decode("utf-8"))
        raise ConfidentialSpaceError("diagnostic smoke failed closed") from None
    emit(canonical_bytes(result).decode("utf-8"))
    return result


# Importing this entrypoint parses only the public locked policy.  Metadata,
# STS, GCS, KMS, truth, and evaluator state are all deferred to activation.
service = create_service()
if os.environ.get("P5R0_CONFIDENTIAL_SPACE_SMOKE") == "1":
    run_startup_smoke(service)


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
