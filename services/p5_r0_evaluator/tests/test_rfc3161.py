from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.rfc3161 import (
    DEFAULT_POLICY_OID,
    FREETSA_CA_PEM_SHA256,
    FREETSA_ENDPOINT,
    FREETSA_POLICY_OID,
    FREETSA_TSA_CERTIFICATE_SHA256,
    RFC3161Config,
    RFC3161_ENDPOINT,
    RFC3161EvidenceError,
    RFC3161TimingEvidenceAdapter,
    build_timestamp_query,
    validate_rfc3161_proof,
    validate_rfc3161_evidence,
)


def _der(tag: int, value: bytes) -> bytes:
    size = len(value)
    length = bytes([size]) if size < 128 else bytes([0x81, size])
    return bytes([tag]) + length + value


def _integer(value: int) -> bytes:
    return _der(0x02, value.to_bytes(1, "big"))


def _oid(value: str) -> bytes:
    parts = [int(part) for part in value.split(".")]
    raw = bytearray([40 * parts[0] + parts[1]])
    for number in parts[2:]:
        encoded = [number & 0x7F]
        number >>= 7
        while number:
            encoded.append(0x80 | (number & 0x7F))
            number >>= 7
        raw.extend(reversed(encoded))
    return _der(0x06, bytes(raw))


def _timestamp_response(payload_digest: str, *, policy: str = DEFAULT_POLICY_OID, status: int = 0, gen_time: str = "20250101000000Z", imprint: bytes | None = None) -> bytes:
    imprint = imprint if imprint is not None else bytes.fromhex(payload_digest[7:])
    algorithm = _der(0x30, _oid("2.16.840.1.101.3.4.2.1") + _der(0x05, b""))
    message_imprint = _der(0x30, algorithm + _der(0x04, imprint))
    tst_info = _der(0x30, _integer(1) + _oid(policy) + message_imprint + _integer(1) + _der(0x18, gen_time.encode()))
    encap = _der(0x30, _oid("1.2.840.113549.1.9.16.1.4") + _der(0xA0, _der(0x04, tst_info)))
    signed_data = _der(0x30, _integer(3) + _der(0x31, b"") + encap + _der(0x31, b""))
    token = _der(0x30, _oid("1.2.840.113549.1.7.2") + _der(0xA0, signed_data))
    status_info = _der(0x30, _integer(status))
    return _der(0x30, status_info + token)


class _Response:
    status = 200
    headers = {"Content-Type": "application/timestamp-reply"}

    def __init__(self, body: bytes, url: str = RFC3161_ENDPOINT):
        self.body = body
        self.url = url

    def read(self, limit: int) -> bytes:
        return self.body

    def geturl(self) -> str:
        return self.url


class _Opener:
    def __init__(self, response: _Response):
        self.response = response
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return self.response


def _config(**changes) -> RFC3161Config:
    values = {
        "tsa_ca_pem": b"fixed test CA",
        "tsa_ca_pem_sha256": digest(b"fixed test CA"),
        "tsa_certificate_sha256": digest(b"fixed test TSA certificate"),
    }
    values.update(changes)
    return RFC3161Config(**values)


def _adapter(response: bytes, **config_changes):
    opener = _Opener(_Response(response))
    config = _config(**config_changes)
    adapter = RFC3161TimingEvidenceAdapter(
        config,
        opener=opener,
        verifier=lambda token, pinned_config: pinned_config.tsa_certificate_sha256,
        clock=lambda: datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp(),
    )
    return adapter, opener


def test_query_is_sha256_digest_only_and_uses_fixed_endpoint():
    payload_digest = digest(b"private payload that must never cross the boundary")
    query = build_timestamp_query(payload_digest)
    assert payload_digest.encode() not in query
    assert b"private payload" not in query
    assert query.startswith(b"0")
    config = _config()
    assert config.endpoint == RFC3161_ENDPOINT
    with pytest.raises(RFC3161EvidenceError, match="allowlisted"):
        RFC3161Config(endpoint="https://attacker.invalid", tsa_ca_pem=b"x", tsa_ca_pem_sha256=digest(b"x"), tsa_certificate_sha256=digest(b"cert"))


def test_freetsa_is_explicitly_allowlisted_with_its_own_policy_oid():
    config = _config(endpoint=FREETSA_ENDPOINT, policy_oid=FREETSA_POLICY_OID)
    assert config.endpoint == FREETSA_ENDPOINT
    assert config.policy_oid == FREETSA_POLICY_OID
    assert FREETSA_CA_PEM_SHA256.startswith("sha256:")
    assert FREETSA_TSA_CERTIFICATE_SHA256.startswith("sha256:")


def test_freetsa_requires_the_same_certificate_pins():
    with pytest.raises(RFC3161EvidenceError, match="CA pin"):
        RFC3161Config(endpoint=FREETSA_ENDPOINT, policy_oid=FREETSA_POLICY_OID, tsa_ca_pem=b"x", tsa_ca_pem_sha256="", tsa_certificate_sha256=digest(b"cert"))


def test_valid_mock_response_is_verified_and_only_digests_are_returned():
    payload_digest = digest(b"payload")
    raw_response = _timestamp_response(payload_digest)
    adapter, opener = _adapter(raw_response)
    evidence = adapter.record(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)
    assert evidence["schema"] == "P5R0RFC3161TimingEvidenceV1"
    assert evidence["message_imprint"] == payload_digest
    assert evidence["status"] == "granted"
    assert evidence["policy_oid"] == DEFAULT_POLICY_OID
    assert evidence["bridge_required"] is True
    assert evidence["bridge_target"] == "P5R0IndependentTimingAttestationV2"
    assert evidence["token_digest"].startswith("sha256:")
    assert evidence["token_digest"] != evidence["response_digest"]
    assert "private" not in str(evidence)
    assert opener.requests[0][0].data == build_timestamp_query(payload_digest)


def test_record_with_proof_round_trips_through_pinned_verifier_without_changing_public_evidence():
    payload_digest = digest(b"payload")
    adapter, _ = _adapter(_timestamp_response(payload_digest))
    recorded = adapter.record_with_proof(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)
    assert set(recorded.proof) == {"schema", "response_b64"}
    rebuilt = adapter.verify_proof(
        recorded.proof,
        run_id="run", task_id="task", event="task_issued",
        payload_digest=payload_digest, sequence=1, previous_digest=None,
    )
    assert rebuilt == recorded.evidence
    assert "response_b64" not in recorded.evidence


@pytest.mark.parametrize("proof", [
    {"schema": "P5R0RFC3161ProofV1", "response_b64": "not canonical!"},
    {"schema": "P5R0RFC3161ProofV1", "response_b64": ""},
    {"schema": "P5R0RFC3161ProofV1", "response_b64": "eA", "unexpected": True},
])
def test_proof_envelope_material_is_strictly_bounded_and_canonical(proof):
    from services.p5_r0_evaluator.rfc3161 import RFC3161EvidenceError
    with pytest.raises(RFC3161EvidenceError):
        validate_rfc3161_proof(proof)


def test_evaluator_side_proof_verification_rejects_payload_mismatch():
    payload_digest = digest(b"payload")
    adapter, _ = _adapter(_timestamp_response(payload_digest))
    recorded = adapter.record_with_proof(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)
    with pytest.raises(Exception, match="imprint"):
        adapter.verify_proof(
            recorded.proof,
            run_id="run", task_id="task", event="task_issued",
            payload_digest=digest(b"different"), sequence=1, previous_digest=None,
        )


    payload_digest = digest(b"payload")
    adapter, _ = _adapter(_timestamp_response(payload_digest))
    first = adapter.record(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)
    second = adapter.record(run_id="run", task_id="task", event="result_received", payload_digest=payload_digest)
    assert first["sequence"] == 1 and first["previous_digest"] is None
    assert second["sequence"] == 2 and second["previous_digest"] == digest(first)
    with pytest.raises(RFC3161EvidenceError, match="chain"):
        validate_rfc3161_evidence(second, run_id="run", task_id="task", event="result_received", payload_digest=payload_digest, previous_digest=None, last_sequence=1)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"imprint": b"x" * 32}, "imprint"),
        ({"policy": "1.2.3.4"}, "policy"),
        ({"status": 2}, "granted"),
    ],
)
def test_wrong_imprint_policy_or_status_fails_closed(kwargs, match):
    payload_digest = digest(b"payload")
    adapter, _ = _adapter(_timestamp_response(payload_digest, **kwargs))
    with pytest.raises(RFC3161EvidenceError, match=match):
        adapter.record(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)


def test_missing_ca_pin_is_rejected_before_network():
    with pytest.raises(RFC3161EvidenceError, match="CA pin"):
        RFC3161Config(tsa_ca_pem=b"fixed", tsa_ca_pem_sha256="", tsa_certificate_sha256=digest(b"cert"))


@pytest.mark.parametrize("response", [b"not DER", b"", b"x" * 300])
def test_malformed_or_oversize_response_fails_closed(response):
    adapter, _ = _adapter(response, max_response_bytes=256)
    with pytest.raises(RFC3161EvidenceError):
        adapter.record(run_id="run", task_id="task", event="task_issued", payload_digest=digest(b"payload"))


def test_redirect_is_rejected_and_response_is_not_leaked():
    payload_digest = digest(b"secret payload")
    opener = _Opener(_Response(_timestamp_response(payload_digest), RFC3161_ENDPOINT + "/redirect"))
    adapter = RFC3161TimingEvidenceAdapter(_config(), opener=opener, verifier=lambda token, config: config.tsa_certificate_sha256, clock=lambda: datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
    with pytest.raises(RFC3161EvidenceError) as failure:
        adapter.record(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)
    assert "secret payload" not in str(failure.value)
    assert "sha256:" not in str(failure.value)


def test_adapter_never_claims_existing_v2_timing_certification():
    adapter, _ = _adapter(_timestamp_response(digest(b"payload")))
    assert adapter.independent is False
    assert adapter.bridge_required is True



def test_gen_time_is_bounded_without_becoming_local_timing_evidence():
    payload_digest = digest(b"payload")
    adapter, _ = _adapter(_timestamp_response(payload_digest, gen_time="20240101000000Z"), max_gen_time_age_seconds=1)
    with pytest.raises(RFC3161EvidenceError, match="gen_time"):
        adapter.record(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)


def test_tsa_certificate_identity_pin_mismatch_fails_closed():
    payload_digest = digest(b"payload")
    opener = _Opener(_Response(_timestamp_response(payload_digest)))
    config = _config()
    adapter = RFC3161TimingEvidenceAdapter(
        config,
        opener=opener,
        verifier=lambda token, pinned_config: digest(b"different certificate"),
        clock=lambda: datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp(),
    )
    with pytest.raises(RFC3161EvidenceError, match="certificate pin"):
        adapter.record(run_id="run", task_id="task", event="task_issued", payload_digest=payload_digest)
