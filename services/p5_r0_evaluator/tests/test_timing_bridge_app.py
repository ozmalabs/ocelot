from io import BytesIO
import json

import pytest

from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest, parse_canonical
from services.p5_r0_evaluator.timing_bridge_service import TimingBridgeServiceError
from services.p5_r0_evaluator.timing_bridge_app import _LockedApplication, application, create_application


class _DurableLedger:
    durable = True


class _Service:
    production_ready = True

    def __init__(self, result=None, error=None):
        self.ledger = _DurableLedger()
        self.result = result or _envelope()
        self.error = error
        self.calls = []

    def handle(self, body):
        self.calls.append(body)
        if self.error is not None:
            raise self.error
        return self.result


def _record():
    return {
        "schema": "P5R0IndependentTimingAttestationV3",
        "ledger_id": "ledger",
        "run_id": "run",
        "task_id": "task",
        "event": "task_issued",
        "sequence": 1,
        "previous_digest": None,
        "seed_digest": digest("evidence"),
        "payload_digest": digest("payload"),
        "observed_at": "2025-01-01T00:00:00.000000Z",
        "authority_id": "authority",
        "key_id": "key",
        "public_key": "public-key",
        "public_key_digest": digest("public-key"),
        "rfc3161_evidence_digest": digest("evidence"),
        "signature": "signed-record",
    }


def _envelope():
    return {
        "schema": "P5R0RFC3161TimingBridgeEnvelopeV1",
        "record": _record(),
        "proof": {"schema": "P5R0RFC3161ProofV1", "response_b64": b64encode(b"proof")},
    }


def _request():
    return canonical_bytes(
        {
            "event": "task_issued",
            "payload_digest": digest("payload"),
            "run_id": "run",
            "schema": "P5R0RFC3161TimingBridgeRequestV1",
            "task_id": "task",
        }
    )


def _call(app, body=None, *, method="POST", path="/v1/timing", content_type="application/json", content_length=None, headers=None, stream=None):
    body = _request() if body is None else body
    captured = {}
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)) if content_length is None else str(content_length),
        "wsgi.input": BytesIO(body) if stream is None else stream,
    }
    environ.update({f"HTTP_{key.upper().replace('-', '_')}": value for key, value in (headers or {}).items()})

    def start_response(status, response_headers):
        captured["status"] = status
        captured["headers"] = dict(response_headers)

    chunks = app(environ, start_response)
    captured["body"] = b"".join(chunks)
    return captured


def _status(response):
    return int(response["status"].split()[0])


def test_locked_default_is_generic_503_until_injected():
    response = _call(application)
    assert _status(response) == 503
    assert parse_canonical(response["body"]) == {"error": "service unavailable", "schema": "P5R0ErrorV1"}
    assert b"traceback" not in response["body"]


def test_authentication_failure_returns_generic_401_and_never_calls_service():
    service = _Service()

    def authenticate(headers):
        assert headers["x-p5-authorization"] == "bad-token"
        raise RuntimeError("secret token should not be returned")

    response = _call(create_application(service, authenticate), headers={"X-P5-Authorization": "bad-token"})
    assert _status(response) == 401
    assert parse_canonical(response["body"])["error"] == "unauthorized"
    assert b"secret" not in response["body"] and service.calls == []


@pytest.mark.parametrize(
    ("method", "path", "content_type", "expected"),
    [
        ("GET", "/v1/timing", "application/json", 405),
        ("POST", "/v1/other", "application/json", 404),
        ("POST", "/v1/timing", "text/plain", 415),
        ("POST", "/v1/timing", None, 415),
    ],
)
def test_method_path_and_content_type_are_strict(method, path, content_type, expected):
    service = _Service()
    response = _call(create_application(service, lambda headers: True), method=method, path=path, content_type=content_type)
    assert _status(response) == expected
    assert parse_canonical(response["body"])["schema"] == "P5R0ErrorV1"
    assert service.calls == []


def test_body_size_is_bounded_without_unbounded_reads():
    service = _Service()
    app = create_application(service, lambda headers: True)
    response = _call(app, content_length=4097)
    assert _status(response) == 413
    assert service.calls == []

    class _GreedyStream:
        def read(self, length):
            assert length == 4096
            return b"x" * 4097

    response = _call(app, stream=_GreedyStream(), content_length=4096)
    assert _status(response) == 413
    assert service.calls == []


def test_noncanonical_json_is_rejected_before_authentication():
    service = _Service()
    authenticated = []

    def authenticate(headers):
        authenticated.append(True)
        return True

    body = json.dumps(parse_canonical(_request()), separators=(", ", ": ")).encode()
    response = _call(create_application(service, authenticate), body=body)
    assert _status(response) == 400
    assert parse_canonical(response["body"])["error"] == "invalid canonical JSON"
    assert authenticated == [] and service.calls == []


def test_service_error_is_redacted_to_generic_category():
    service = _Service(error=TimingBridgeServiceError("raw RFC3161 token and timestamp"))
    response = _call(create_application(service, lambda headers: True))
    assert _status(response) == 422
    assert parse_canonical(response["body"]) == {"error": "timing request rejected", "schema": "P5R0ErrorV1"}
    assert b"RFC3161" not in response["body"] and b"timestamp" not in response["body"]


def test_valid_request_is_canonical_proof_envelope_pass_through():
    service = _Service()
    seen_headers = []

    def authenticate(headers):
        seen_headers.append(headers)
        return True

    body = _request()
    response = _call(create_application(service, authenticate), body=body, headers={"X-P5-Authorization": "valid"})
    assert _status(response) == 200
    assert response["headers"]["content-type"] == "application/json"
    assert response["body"] == canonical_bytes(_envelope())
    assert service.calls == [body]
    assert seen_headers[0]["x-p5-authorization"] == "valid"


def test_factory_rejects_non_production_or_non_durable_service():
    service = _Service()
    service.production_ready = False
    with pytest.raises(ValueError, match="production-ready"):
        create_application(service, lambda headers: True)

    service.production_ready = True
    service.ledger.durable = False
    with pytest.raises(ValueError, match="durable"):
        create_application(service, lambda headers: True)



def test_locked_application_injection_is_one_time():
    locked = _LockedApplication()
    service = _Service()
    locked.inject(service, lambda headers: True)
    with pytest.raises(RuntimeError, match="already injected"):
        locked.inject(service, lambda headers: True)
