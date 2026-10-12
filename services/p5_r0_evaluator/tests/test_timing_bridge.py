from datetime import datetime, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest, parse_canonical, signing_digest
from services.p5_r0_evaluator.rfc3161 import RFC3161Config
from services.p5_r0_evaluator.timing import (
    TimingAttestationError,
    TimingAuthorityConfig,
    sign_independent_timing_attestation_v3,
    validate_attestation,
)
from services.p5_r0_evaluator.timing_bridge import (
    HTTPSRFC3161TimingBridgeClient,
    TimingBridgeConfig,
    TimingBridgeError,
)


class _Response:
    def __init__(self, body, url, *, status=200, content_type="application/json"):
        self._body = body
        self.status = status
        self._url = url
        self.headers = {"Content-Type": content_type}

    def geturl(self):
        return self._url

    def read(self, limit):
        return self._body[:limit]


class _Opener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _Signer:
    def __init__(self, key):
        self.key = key

    def sign_digest(self, message_digest):
        return b64encode(self.key.sign(message_digest))


class _ProofAdapter:
    def __init__(self, config, evidence):
        self.config = config
        self.evidence = evidence

    def verify_proof(self, proof, **kwargs):
        assert proof["schema"] == "P5R0RFC3161ProofV1"
        return self.evidence


def _proof_config():
    return RFC3161Config(
        tsa_ca_pem=b"fixed test CA",
        tsa_ca_pem_sha256=digest(b"fixed test CA"),
        tsa_certificate_sha256=digest(b"fixed test TSA certificate"),
    )


def _proof_evidence():
    return {"proof": "verified RFC3161 response"}


def _envelope(record):
    return {
        "schema": "P5R0RFC3161TimingBridgeEnvelopeV1",
        "record": record,
        "proof": {"schema": "P5R0RFC3161ProofV1", "response_b64": b64encode(b"proof")},
    }


def _authority(key):
    public = b64encode(key.public_key().public_bytes_raw())
    return TimingAuthorityConfig(
        authority_id="bridge-authority",
        key_id="bridge-key",
        ledger_id="bridge-ledger",
        public_key_digest=digest(public),
    ), public


def _v3(key, *, run_id="run", task_id="task", event="task_issued", sequence=1,
        previous_digest=None, payload_digest=None, rfc_digest=None):
    authority, public = _authority(key)
    value = {
        "schema": "P5R0IndependentTimingAttestationV3",
        "ledger_id": authority.ledger_id,
        "run_id": run_id,
        "task_id": task_id,
        "event": event,
        "sequence": sequence,
        "previous_digest": previous_digest,
        "seed_digest": digest("seed"),
        "payload_digest": payload_digest or digest("payload"),
        "observed_at": datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority_id": authority.authority_id,
        "key_id": authority.key_id,
        "public_key": public,
        "public_key_digest": authority.public_key_digest,
        "rfc3161_evidence_digest": rfc_digest or digest({"rfc": "evidence"}),
        "signature": "",
    }
    return sign_independent_timing_attestation_v3(value, _Signer(key)), authority


def _client(response, *, max_response_bytes=512 * 1024, endpoint="https://bridge.example.test/v1/timing", authorization_header=None):
    key = Ed25519PrivateKey.generate()
    evidence = _proof_evidence()
    record, authority = _v3(key, rfc_digest=digest(evidence))
    body = canonical_bytes(response(_envelope(record)) if callable(response) else response)
    opener = _Opener([_Response(body, endpoint)])
    rfc_config = _proof_config()
    client = HTTPSRFC3161TimingBridgeClient(
        TimingBridgeConfig(endpoint=endpoint, authority=authority, rfc3161_config=rfc_config, max_response_bytes=max_response_bytes, authorization_header=authorization_header),
        opener=opener,
        rfc3161_adapter=_ProofAdapter(rfc_config, evidence),
    )
    return client, opener, record, key, authority


def test_v3_is_closed_signed_and_requires_rfc3161_digest():
    key = Ed25519PrivateKey.generate()
    record, authority = _v3(key)
    validate_attestation(
        record, run_id="run", task_id="task", event="task_issued",
        payload_digest=record["payload_digest"], expected_authority_id=authority.authority_id,
        expected_key_id=authority.key_id, expected_ledger_id=authority.ledger_id,
        expected_public_key_digest=authority.public_key_digest, last_sequence=0,
    )
    extra = dict(record)
    extra["unexpected"] = True
    with pytest.raises(TimingAttestationError, match="schema"):
        validate_attestation(extra, run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])
    missing = dict(record)
    del missing["rfc3161_evidence_digest"]
    with pytest.raises(TimingAttestationError, match="schema"):
        validate_attestation(missing, run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])
    with pytest.raises(TimingAttestationError, match="digest mismatch"):
        validate_attestation(
            record, run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"],
            expected_rfc3161_evidence_digest=digest("different-evidence"),
        )


@pytest.mark.parametrize("field, value", [
    ("run_id", "other-run"), ("task_id", "other-task"), ("event", "result_received"),
    ("payload_digest", digest("different-payload")), ("sequence", 2),
    ("previous_digest", digest("different-previous")), ("authority_id", "attacker"),
    ("key_id", "attacker-key"), ("ledger_id", "attacker-ledger"),
    ("rfc3161_evidence_digest", digest("different-evidence")),
])
def test_v3_signature_binds_all_record_fields(field, value):
    key = Ed25519PrivateKey.generate()
    record, authority = _v3(key)
    forged = dict(record)
    forged[field] = value
    with pytest.raises(TimingAttestationError):
        validate_attestation(
            forged, run_id="run", task_id="task", event="task_issued",
            payload_digest=record["payload_digest"], expected_authority_id=authority.authority_id,
            expected_key_id=authority.key_id, expected_ledger_id=authority.ledger_id,
            expected_public_key_digest=authority.public_key_digest, last_sequence=0,
        )


def test_v3_rejects_signature_and_public_key_substitution():
    key = Ed25519PrivateKey.generate()
    record, authority = _v3(key)
    bad_signature = dict(record, signature=b64encode(b"bad"))
    with pytest.raises(TimingAttestationError, match="signature"):
        validate_attestation(bad_signature, run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])
    other = Ed25519PrivateKey.generate()
    forged_key = dict(record, public_key=b64encode(other.public_key().public_bytes_raw()))
    with pytest.raises(TimingAttestationError, match="signature"):
        validate_attestation(forged_key, run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])
    with pytest.raises(TimingAttestationError, match="authority mismatch"):
        validate_attestation(record, run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"], expected_authority_id="attacker")
    assert authority.authority_id == "bridge-authority"


def test_bridge_sends_only_public_ids_and_payload_digest_and_validates_v3():
    client, opener, record, _, _ = _client(lambda generated: generated)
    payload = record["payload_digest"]
    received = client.record(run_id="run", task_id="task", event="task_issued", payload_digest=payload)
    request, timeout = opener.requests[0]
    sent = parse_canonical(request.data)
    assert set(sent) == {"schema", "run_id", "task_id", "event", "payload_digest"}
    assert sent["payload_digest"] == payload and "timestamp" not in request.data.decode()
    assert received == record
    assert request.full_url == "https://bridge.example.test/v1/timing"
    assert timeout == 5.0


def test_bridge_sends_injected_authorization_header_without_returning_it():
    client, opener, record, _, _ = _client(lambda generated: generated, authorization_header=lambda: "Bearer id-token")
    client.record(run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])
    request, _ = opener.requests[0]
    assert request.get_header("Authorization") == "Bearer id-token"
    assert "id-token" not in repr(client.config)


    client, opener, record, _, _ = _client(lambda generated: generated["record"])
    with pytest.raises(TimingBridgeError, match="envelope"):
        client.record(run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])


def test_bridge_rejects_oversized_or_malformed_proof_material():
    client, opener, record, _, _ = _client(lambda generated: dict(generated, proof={"schema": "bad", "response_b64": "eA=="}))
    with pytest.raises(TimingBridgeError, match="proof"):
        client.record(run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])


@pytest.mark.parametrize("body", [b'{"schema":"bad"}', b'{"schema": "bad"}'])
def test_bridge_rejects_malformed_or_noncanonical_response(body):
    key = Ed25519PrivateKey.generate()
    authority, _ = _authority(key)
    endpoint = "https://bridge.example.test/v1/timing"
    opener = _Opener([_Response(body, endpoint)])
    client = HTTPSRFC3161TimingBridgeClient(TimingBridgeConfig(endpoint=endpoint, authority=authority, rfc3161_config=_proof_config()), opener=opener)
    with pytest.raises(TimingBridgeError):
        client.record(run_id="run", task_id="task", event="task_issued", payload_digest=digest("payload"))


def test_bridge_rejects_redirect_oversize_and_wrong_content_type_without_leaking_body():
    client, opener, record, _, _ = _client(lambda generated: generated)
    opener.responses[0] = _Response(canonical_bytes(_envelope(record)), "https://other.example.test/redirect")
    with pytest.raises(TimingBridgeError, match="redirect"):
        client.record(run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])

    key = Ed25519PrivateKey.generate()
    record, authority = _v3(key)
    endpoint = "https://bridge.example.test/v1/timing"
    opener = _Opener([_Response(canonical_bytes(_envelope(record)), endpoint, content_type="text/plain")])
    client = HTTPSRFC3161TimingBridgeClient(TimingBridgeConfig(endpoint=endpoint, authority=authority, rfc3161_config=_proof_config()), opener=opener, rfc3161_adapter=_ProofAdapter(_proof_config(), _proof_evidence()))
    with pytest.raises(TimingBridgeError):
        client.record(run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])

    opener = _Opener([_Response(canonical_bytes(_envelope(record)) + b"x" * 20, endpoint)])
    client = HTTPSRFC3161TimingBridgeClient(TimingBridgeConfig(endpoint=endpoint, authority=authority, rfc3161_config=_proof_config(), max_response_bytes=10), opener=opener, rfc3161_adapter=_ProofAdapter(_proof_config(), _proof_evidence()))
    with pytest.raises(TimingBridgeError, match="large"):
        client.record(run_id="run", task_id="task", event="task_issued", payload_digest=record["payload_digest"])


def test_bridge_requires_https_and_does_not_change_rfc3161_adapter_independence():
    key = Ed25519PrivateKey.generate()
    authority, _ = _authority(key)
    with pytest.raises(TimingBridgeError, match="HTTPS"):
        TimingBridgeConfig(endpoint="http://bridge.example.test/timing", authority=authority, rfc3161_config=_proof_config())
    from services.p5_r0_evaluator.rfc3161 import RFC3161TimingEvidenceAdapter
    assert RFC3161TimingEvidenceAdapter.independent is False



def test_service_accepts_v3_only_for_the_configured_independent_authority():
    from services.p5_r0_evaluator.service import EvaluatorService, ServiceError

    bridge_key = Ed25519PrivateKey.generate()
    record, authority = _v3(bridge_key)
    receipt_key = Ed25519PrivateKey.generate()
    receipt_public = b64encode(receipt_key.public_key().public_bytes_raw())

    class _Attestor:
        independent = True

        def record(self, **kwargs):
            return record

    class _Signer:
        authority = {
            "public_key_digest": digest(receipt_public),
            "authority_id": "receipt",
            "key_id": "receipt-key",
        }

    service = object.__new__(EvaluatorService)
    service.timing_attestor = _Attestor()
    service.signer = _Signer()
    service.timing_authority_id = authority.authority_id
    service.timing_key_id = authority.key_id
    service.timing_ledger_id = authority.ledger_id
    service.timing_public_key_digest = authority.public_key_digest
    state = {"run_id": "run", "timing_sequence": 0, "timing_record_digest": None}
    accepted = service._record_timing(state, task_id="task", event="task_issued", payload_digest=record["payload_digest"])
    assert accepted["schema"] == "P5R0IndependentTimingAttestationV3"
    assert state["timing_sequence"] == 1

    service.timing_authority_id = "wrong-authority"
    with pytest.raises(ServiceError, match="failed closed"):
        service._record_timing({"run_id": "run", "timing_sequence": 0, "timing_record_digest": None}, task_id="task", event="task_issued", payload_digest=record["payload_digest"])



def test_fresh_bridge_client_restores_durable_chain_head_before_recording():
    key = Ed25519PrivateKey.generate()
    evidence = _proof_evidence()
    record_one, authority = _v3(key, task_id="task-one", rfc_digest=digest(evidence))
    endpoint = "https://bridge.example.test/v1/timing"
    config = TimingBridgeConfig(endpoint=endpoint, authority=authority, rfc3161_config=_proof_config())
    client_one = HTTPSRFC3161TimingBridgeClient(
        config,
        opener=_Opener([_Response(canonical_bytes(_envelope(record_one)), endpoint)]),
        rfc3161_adapter=_ProofAdapter(_proof_config(), evidence),
    )
    first = client_one.record(run_id="run", task_id="task-one", event="task_issued", payload_digest=record_one["payload_digest"])

    record_two, _ = _v3(
        key,
        task_id="task-two",
        sequence=2,
        previous_digest=digest(first),
        payload_digest=digest("payload-two"),
        rfc_digest=digest(evidence),
    )
    client_two = HTTPSRFC3161TimingBridgeClient(
        config,
        opener=_Opener([_Response(canonical_bytes(_envelope(record_two)), endpoint)]),
        rfc3161_adapter=_ProofAdapter(_proof_config(), evidence),
    )
    client_two.restore_chain(run_id="run", sequence=1, previous_digest=digest(first))
    second = client_two.record(run_id="run", task_id="task-two", event="task_issued", payload_digest=record_two["payload_digest"])
    assert second["sequence"] == 2
    assert second["previous_digest"] == digest(first)
