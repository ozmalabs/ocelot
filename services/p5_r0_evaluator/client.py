"""Fail-closed HTTP client for the P5 evaluator control plane.

This module is an external-I/O adapter only. It does not create credentials,
locks, manifests, truth, worker evidence, authority keys, or evaluator
results. Callers must inject an OIDC token provider and supply all committed
P5 digests explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .canonical import b64decode, canonical_bytes, digest, parse_canonical, signing_digest
from .schemas import SchemaError, next_task as validate_next_task, run_start as validate_run_start
from .schemas import task_envelope, task_response, task_result

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover - the production image pins cryptography.
    Ed25519PublicKey = None  # type: ignore[assignment,misc]


MAX_CLIENT_REQUEST_BYTES = 1_048_576
MAX_CLIENT_RESPONSE_BYTES = 1_048_576
_RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
_AUTHORITY_FIELDS = frozenset({
    "schema", "authority_id", "key_id", "public_key", "public_key_digest",
    "transport_attestation",
})


class EvaluatorClientError(RuntimeError):
    """The client refused an invalid transport, protocol, or response."""


class EvaluatorHTTPError(EvaluatorClientError):
    """The evaluator returned a non-success HTTP status."""

    def __init__(self, status: int, response: Mapping[str, Any] | None = None):
        self.status = status
        self.response = dict(response) if response is not None else None
        super().__init__(f"evaluator HTTP status {status}")


class EvaluatorImpasse(EvaluatorClientError):
    """The evaluator returned its explicit signed/no-go impasse result."""

    def __init__(self, response: Mapping[str, Any]):
        self.response = dict(response)
        super().__init__("evaluator returned impasse")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        raise EvaluatorClientError("evaluator redirects are forbidden")


def _validate_authority(authority: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(authority, Mapping) or set(authority) != _AUTHORITY_FIELDS:
        raise EvaluatorClientError("authority metadata is not closed")
    if authority.get("schema") not in {"P5R0AuthorityV3", "P5R0PublicAuthorityV4"}:
        raise EvaluatorClientError("authority schema is invalid")
    for key in ("authority_id", "key_id", "public_key", "public_key_digest"):
        if not isinstance(authority.get(key), str) or not authority[key]:
            raise EvaluatorClientError("authority metadata is invalid")
    if authority["public_key_digest"] != digest(authority["public_key"]):
        raise EvaluatorClientError("authority public-key binding is invalid")
    transport = authority["transport_attestation"]
    if not isinstance(transport, Mapping) or set(transport) != {"schema", "provider", "audience", "event"}:
        raise EvaluatorClientError("authority transport metadata is invalid")
    if transport.get("schema") != "P5R0AuthorityTransportV1":
        raise EvaluatorClientError("authority transport schema is invalid")
    return dict(authority)


def _digest_id(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise EvaluatorClientError(f"{name} is invalid")
    try:
        int(value[7:], 16)
    except ValueError as exc:
        raise EvaluatorClientError(f"{name} is invalid") from exc
    return value


@dataclass(frozen=True)
class EvaluatorClientConfig:
    """Explicit non-secret client configuration.

    ``token_provider`` must return the caller's already-authorized OIDC token.
    It is never loaded from ADC, metadata, a service-account key, or this
    module's environment.
    """

    endpoint: str
    authority: Mapping[str, Any]
    token_provider: Callable[[], str] = field(repr=False, compare=False)
    timeout_seconds: float = 5.0
    max_response_bytes: int = MAX_CLIENT_RESPONSE_BYTES
    max_attempts: int = 3
    retry_delay_seconds: float = 0.0
    clock_ms: Callable[[], int] = field(default=lambda: int(time.time() * 1000), repr=False, compare=False)
    sleeper: Callable[[float], None] = field(default=time.sleep, repr=False, compare=False)
    opener: Any | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        parsed = urlsplit(self.endpoint)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise EvaluatorClientError("evaluator endpoint must be HTTPS")
        if parsed.query or parsed.fragment:
            raise EvaluatorClientError("evaluator endpoint must not contain query or fragment")
        if not callable(self.token_provider):
            raise EvaluatorClientError("explicit token provider is required")
        _validate_authority(self.authority)
        if not 0 < self.timeout_seconds <= 30:
            raise EvaluatorClientError("evaluator timeout is invalid")
        if type(self.max_response_bytes) is not int or not 0 < self.max_response_bytes <= MAX_CLIENT_RESPONSE_BYTES:
            raise EvaluatorClientError("evaluator response bound is invalid")
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 5:
            raise EvaluatorClientError("evaluator attempt bound is invalid")
        if not 0 <= self.retry_delay_seconds <= 10:
            raise EvaluatorClientError("evaluator retry delay is invalid")
        if self.opener is None:
            object.__setattr__(self, "opener", build_opener(_NoRedirect()))


class P5EvaluatorClient:
    """Canonical, bounded client for the normal P5 HTTP control plane."""

    def __init__(self, config: EvaluatorClientConfig):
        if not isinstance(config, EvaluatorClientConfig):
            raise EvaluatorClientError("client configuration is required")
        self.config = config
        self.authority = _validate_authority(config.authority)

    def _url(self, *parts: str) -> str:
        encoded = []
        for part in parts:
            if not isinstance(part, str) or not part:
                raise EvaluatorClientError("evaluator path component is invalid")
            encoded.append(quote(part, safe=":"))
        return self.config.endpoint.rstrip("/") + "/" + "/".join(encoded)

    def _token(self) -> str:
        token = self.config.token_provider()
        if not isinstance(token, str) or not token or any(ord(char) < 0x20 or ord(char) == 0x7F for char in token):
            raise EvaluatorClientError("token provider returned an invalid token")
        return token

    def _request(self, method: str, url: str, body: bytes | None = None) -> dict[str, Any]:
        if body is not None and len(body) > MAX_CLIENT_REQUEST_BYTES:
            raise EvaluatorClientError("evaluator request is too large")
        if method == "GET" and body is not None:
            raise EvaluatorClientError("GET request must not have a body")
        last_error: BaseException | None = None
        for attempt in range(self.config.max_attempts):
            token = self._token()
            headers = {
                "Accept": "application/json",
                # Cloud Run may reserve Authorization for platform IAM.
                "X-P5-Authorization": f"Bearer {token}",
            }
            if body is not None:
                headers["Content-Type"] = "application/json"
            request = Request(
                url,
                data=body,
                method=method,
                headers=headers,
            )
            try:
                response = self.config.opener.open(request, timeout=self.config.timeout_seconds)
                status = int(getattr(response, "status", 200))
                headers = getattr(response, "headers", None)
                content_type = headers.get("Content-Type") if headers is not None else None
                if not isinstance(content_type, str) or content_type.lower().split(";", 1)[0].strip() != "application/json":
                    raise EvaluatorClientError("evaluator response content type is invalid")
                raw = response.read(self.config.max_response_bytes + 1)
                if not isinstance(raw, bytes) or len(raw) > self.config.max_response_bytes:
                    raise EvaluatorClientError("evaluator response is too large")
                if status in _RETRYABLE_STATUSES and attempt + 1 < self.config.max_attempts:
                    self.config.sleeper(self.config.retry_delay_seconds)
                    continue
                if not 200 <= status < 300:
                    try:
                        parsed_error = parse_canonical(raw)
                    except Exception:
                        parsed_error = None
                    raise EvaluatorHTTPError(status, parsed_error)
                return parse_canonical(raw)
            except HTTPError as exc:
                last_error = exc
                if exc.code in _RETRYABLE_STATUSES and attempt + 1 < self.config.max_attempts:
                    self.config.sleeper(self.config.retry_delay_seconds)
                    continue
                raise EvaluatorHTTPError(exc.code) from exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt + 1 < self.config.max_attempts:
                    self.config.sleeper(self.config.retry_delay_seconds)
                    continue
                raise EvaluatorClientError("evaluator request failed") from exc
            except (EvaluatorClientError, ValueError):
                raise
        raise EvaluatorClientError("evaluator request failed") from last_error

    def start_run(self, *, lock_digest: str, manifest_digest: str, worker_contract_digest: str, idempotency_key: str, execution_mode: str = "diagnostic_only") -> dict[str, Any]:
        request = {
            "schema": "P5R0RunStartRequestV1",
            "lock_digest": _digest_id(lock_digest, "lock_digest"),
            "manifest_digest": _digest_id(manifest_digest, "manifest_digest"),
            "worker_contract_digest": _digest_id(worker_contract_digest, "worker_contract_digest"),
            "idempotency_key": idempotency_key,
            "execution_mode": execution_mode,
        }
        try:
            validate_run_start(request)
        except SchemaError as exc:
            raise EvaluatorClientError("run-start request is invalid") from exc
        return self._request("POST", self._url("v1", "runs"), canonical_bytes(request))

    def issue_time_seed(self, *, run_id: str, namespace: str, idempotency_key: str) -> dict[str, Any]:
        _digest_id(run_id, "run_id")
        if not isinstance(namespace, str) or not namespace or not isinstance(idempotency_key, str) or not idempotency_key:
            raise EvaluatorClientError("time-seed request is invalid")
        request = {"schema": "P5R0TimeSeedRequestV1", "run_id": run_id, "namespace": namespace, "idempotency_key": idempotency_key}
        return self._request("POST", self._url("v1", "runs", run_id, "time-seed"), canonical_bytes(request))

    def next_task(self, *, run_id: str, expected_sequence: int, idempotency_key: str) -> dict[str, Any]:
        _digest_id(run_id, "run_id")
        request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": expected_sequence, "idempotency_key": idempotency_key}
        try:
            validate_next_task(request)
        except SchemaError as exc:
            raise EvaluatorClientError("next-task request is invalid") from exc
        response = self._request("POST", self._url("v1", "runs", run_id, "tasks", "next"), canonical_bytes(request))
        try:
            checked = task_response(response)
            envelope = task_envelope(checked["task_envelope"])
        except SchemaError as exc:
            raise EvaluatorClientError("task response is invalid") from exc
        if checked["run_id"] != run_id or envelope["run_id"] != run_id:
            raise EvaluatorClientError("task response run binding is invalid")
        if envelope["sequence"] != expected_sequence:
            raise EvaluatorClientError("task response sequence is invalid")
        if envelope["authority_id"] != self.authority["authority_id"] or envelope["key_id"] != self.authority["key_id"] or envelope["public_key_digest"] != self.authority["public_key_digest"]:
            raise EvaluatorClientError("task response authority is invalid")
        if digest(envelope["task"]) != envelope["task_digest"]:
            raise EvaluatorClientError("task response digest is invalid")
        if self.config.clock_ms() >= envelope["expires_at_ms"]:
            raise EvaluatorClientError("task response is expired")
        if Ed25519PublicKey is None:
            raise EvaluatorClientError("Ed25519 verification is unavailable")
        try:
            Ed25519PublicKey.from_public_bytes(b64decode(self.authority["public_key"])).verify(
                b64decode(envelope["signature"]), signing_digest(envelope)
            )
        except Exception as exc:
            raise EvaluatorClientError("task response signature is invalid") from exc
        return checked

    def submit_result(self, *, run_id: str, task_id: str, result: Mapping[str, Any]) -> dict[str, Any]:
        _digest_id(run_id, "run_id")
        _digest_id(task_id, "task_id")
        try:
            checked = task_result(dict(result), run_id, task_id)
        except SchemaError as exc:
            raise EvaluatorClientError("task result request is invalid") from exc
        return self._request(
            "POST", self._url("v1", "runs", run_id, "tasks", task_id, "result"), canonical_bytes(checked)
        )

    def get_result(self, *, run_id: str) -> dict[str, Any]:
        _digest_id(run_id, "run_id")
        response = self._request("GET", self._url("v1", "runs", run_id, "result"))
        if response.get("schema") != "P5R0RunResultResponseV1" or response.get("run_id") != run_id:
            raise EvaluatorClientError("result response is invalid")
        if response.get("status") == "impasse" or response.get("disposition") == "impasse":
            raise EvaluatorImpasse(response)
        return response


__all__ = [
    "EvaluatorClientConfig",
    "EvaluatorClientError",
    "EvaluatorHTTPError",
    "EvaluatorImpasse",
    "P5EvaluatorClient",
]
