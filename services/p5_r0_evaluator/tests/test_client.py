import json
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest, signing_digest
from services.p5_r0_evaluator.client import (
    EvaluatorClientConfig,
    EvaluatorClientError,
    EvaluatorHTTPError,
    EvaluatorImpasse,
    P5EvaluatorClient,
)


class Response:
    def __init__(self, status, value, content_type="application/json"):
        self.status = status
        self.body = canonical_bytes(value)
        self.headers = {"Content-Type": content_type}

    def read(self, limit):
        return self.body[:limit]


class Opener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


def _authority():
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": "receipt-authority",
        "key_id": "receipt-key",
        "public_key": public,
        "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1",
            "provider": "provider",
            "audience": "https://sts.googleapis.com",
            "event": "confidential_space_attestation",
        },
    }
    return key, authority


def _client(opener, authority, *, token="caller-token", now=1_000, attempts=3):
    config = EvaluatorClientConfig(
        endpoint="https://evaluator.example.test",
        authority=authority,
        token_provider=lambda: token,
        max_attempts=attempts,
        clock_ms=lambda: now,
        opener=opener,
    )
    return P5EvaluatorClient(config)


def _task_response(key, authority, *, run_id=None, task_id=None, expires_at=2_000, signature_key=None):
    run_id = run_id or digest("run")
    task_id = task_id or digest("task")
    task = {"schema": "P5R0WorkerTaskV3", "case_token": digest("case")}
    envelope = {
        "schema": "P5R0TaskEnvelopeV1",
        "run_id": run_id,
        "task_id": task_id,
        "sequence": 1,
        "task_digest": digest(task),
        "task": task,
        "issued_at_ms": 900,
        "expires_at_ms": expires_at,
        "authority_id": authority["authority_id"],
        "key_id": authority["key_id"],
        "public_key_digest": authority["public_key_digest"],
        "signature": "",
    }
    signer = signature_key or key
    envelope["signature"] = b64encode(signer.sign(signing_digest(envelope)))
    return {
        "schema": "P5R0NextTaskResponseV1",
        "run_id": run_id,
        "task_id": task_id,
        "sequence": 1,
        "phase": "primary",
        "case_id": "case-1",
        "side": "primary",
        "pair_id": None,
        "task_digest": digest(task),
        "task": task,
        "task_envelope": envelope,
        "authority": authority,
        "issued_at_ms": 900,
        "expires_at_ms": expires_at,
    }


def test_start_retries_with_identical_canonical_bytes_and_idempotency():
    _, authority = _authority()
    opener = Opener([
        Response(503, {"schema": "P5R0ErrorV1", "error": "temporary"}),
        Response(200, {"schema": "P5R0RunStartResponseV1", "run_id": digest("run"), "status": "ready"}),
    ])
    client = _client(opener, authority, attempts=2)
    result = client.start_run(
        lock_digest=digest("lock"),
        manifest_digest=digest("manifest"),
        worker_contract_digest=digest("worker"),
        idempotency_key="start-1",
    )
    assert result["status"] == "ready"
    assert len(opener.requests) == 2
    assert opener.requests[0][0].data == opener.requests[1][0].data
    assert opener.requests[0][0].get_header("X-p5-authorization") == "Bearer caller-token"
    assert json.loads(opener.requests[0][0].data)["idempotency_key"] == "start-1"


def test_retry_exhaustion_surfaces_http_error_without_success():
    _, authority = _authority()
    opener = Opener([Response(503, {"schema": "P5R0ErrorV1", "error": "temporary"})])
    client = _client(opener, authority, attempts=1)
    with pytest.raises(EvaluatorHTTPError) as caught:
        client.start_run(
            lock_digest=digest("lock"), manifest_digest=digest("manifest"),
            worker_contract_digest=digest("worker"), idempotency_key="start-1",
        )
    assert caught.value.status == 503


def test_next_task_verifies_authority_digest_signature_and_expiry():
    key, authority = _authority()
    run_id = digest("run")
    response = _task_response(key, authority, run_id=run_id)
    opener = Opener([Response(200, response)])
    client = _client(opener, authority)
    checked = client.next_task(run_id=run_id, expected_sequence=1, idempotency_key="next-1")
    assert checked["task_envelope"]["task_digest"] == digest(checked["task"])

    bad = dict(response)
    bad["task_envelope"] = dict(response["task_envelope"])
    bad["task_envelope"]["signature"] = b64encode(b"bad")
    with pytest.raises(EvaluatorClientError, match="signature"):
        _client(Opener([Response(200, bad)]), authority).next_task(
            run_id=run_id, expected_sequence=1, idempotency_key="next-2"
        )

    expired = _task_response(key, authority, run_id=run_id, expires_at=1_000)
    with pytest.raises(EvaluatorClientError, match="expired"):
        _client(Opener([Response(200, expired)]), authority).next_task(
            run_id=run_id, expected_sequence=1, idempotency_key="next-3"
        )


def test_next_task_rejects_authority_mismatch():
    key, authority = _authority()
    other_key, other_authority = _authority()
    response = _task_response(other_key, other_authority, signature_key=other_key)
    with pytest.raises(EvaluatorClientError, match="authority"):
        _client(Opener([Response(200, response)]), authority).next_task(
            run_id=response["run_id"], expected_sequence=1, idempotency_key="next-1"
        )


def test_result_impasse_is_explicit_not_success():
    _, authority = _authority()
    run_id = digest("run")
    response = {
        "schema": "P5R0RunResultResponseV1",
        "run_id": run_id,
        "status": "impasse",
        "disposition": "impasse",
        "result_seal": {"schema": "P5R0ResultSealV4"},
    }
    with pytest.raises(EvaluatorImpasse) as caught:
        _client(Opener([Response(200, response)]), authority).get_result(run_id=run_id)
    assert caught.value.response["disposition"] == "impasse"


def test_client_refuses_missing_token_and_invalid_response_content_type():
    _, authority = _authority()
    with pytest.raises(EvaluatorClientError, match="token"):
        _client(Opener([]), authority, token="").start_run(
            lock_digest=digest("lock"), manifest_digest=digest("manifest"),
            worker_contract_digest=digest("worker"), idempotency_key="start-1",
        )
    opener = Opener([Response(200, {"schema": "P5R0RunStartResponseV1"}, content_type="text/plain")])
    with pytest.raises(EvaluatorClientError, match="content type"):
        _client(opener, authority).start_run(
            lock_digest=digest("lock"), manifest_digest=digest("manifest"),
            worker_contract_digest=digest("worker"), idempotency_key="start-1",
        )


def test_client_refuses_non_https_endpoint_and_invalid_digest():
    _, authority = _authority()
    with pytest.raises(EvaluatorClientError, match="HTTPS"):
        EvaluatorClientConfig("http://evaluator.example.test", authority, lambda: "token")
    with pytest.raises(EvaluatorClientError, match="lock_digest"):
        _client(Opener([]), authority).start_run(
            lock_digest="not-a-digest", manifest_digest=digest("manifest"),
            worker_contract_digest=digest("worker"), idempotency_key="start-1",
        )
