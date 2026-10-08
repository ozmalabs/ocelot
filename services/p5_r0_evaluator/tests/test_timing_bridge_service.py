from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest
from services.p5_r0_evaluator.rfc3161 import RFC3161RecordedProof, RFC3161Config
from services.p5_r0_evaluator.rfc3161 import validate_rfc3161_evidence
from services.p5_r0_evaluator.timing import TimingAuthorityConfig
from services.p5_r0_evaluator.timing_bridge_service import (
    BRIDGE_RECORD_SCHEMA,
    InMemoryTimingBridgeLedger,
    TimingBridgeService,
    TimingBridgeServiceError,
)


class _Signer:
    def __init__(self):
        self.key = Ed25519PrivateKey.generate()
        public = b64encode(self.key.public_key().public_bytes_raw())
        self.authority = {
            "schema": "P5R0AuthorityV3",
            "authority_id": "bridge-authority",
            "key_id": "bridge-key",
            "public_key": public,
            "public_key_digest": digest(public),
        }

    def sign_digest(self, value):
        return b64encode(self.key.sign(value))


def _authority(signer):
    return TimingAuthorityConfig(
        authority_id=signer.authority["authority_id"],
        key_id=signer.authority["key_id"],
        ledger_id="bridge-ledger",
        public_key_digest=signer.authority["public_key_digest"],
    )


def _evidence(request, sequence, previous_digest=None, *, payload_digest=None):
    payload_digest = payload_digest or request["payload_digest"]
    value = {
        "schema": "P5R0RFC3161TimingEvidenceV1",
        "run_id": request["run_id"],
        "task_id": request["task_id"],
        "event": request["event"],
        "sequence": sequence,
        "ledger_id": "digicert-rfc3161",
        "previous_digest": previous_digest,
        "payload_digest": payload_digest,
        "message_imprint": payload_digest,
        "status": "granted",
        "policy_oid": "2.16.840.1.114412.7.1",
        "gen_time": "20250101000000.123Z",
        "token_digest": digest({"token": sequence}),
        "response_digest": digest({"response": sequence}),
        "tsa_certificate_sha256": digest("tsa-certificate"),
        "bridge_required": True,
        "bridge_target": "P5R0IndependentTimingAttestationV2",
    }
    validate_rfc3161_evidence(
        value,
        run_id=request["run_id"],
        task_id=request["task_id"],
        event=request["event"],
        payload_digest=payload_digest,
        previous_digest=previous_digest,
        last_sequence=sequence - 1,
    )
    return value


class _Adapter:
    def __init__(self):
        self.calls = []
        self.evidence = {}

    def record(self, **kwargs):
        self.calls.append(kwargs)
        sequence = len(self.calls)
        previous = digest(self.evidence[sequence - 1]) if sequence > 1 else None
        evidence = self.evidence.get(sequence) or _evidence(kwargs, sequence, previous)
        self.evidence[sequence] = evidence
        return evidence
    def verify_proof(self, proof, **kwargs):
        return self.evidence[kwargs["sequence"]]

    def record_with_proof(self, **kwargs):
        return RFC3161RecordedProof(
            evidence=self.record(**kwargs),
            proof={"schema": "P5R0RFC3161ProofV1", "response_b64": b64encode(b"verified-proof")},
        )


def _request(*, task_id="task-1", event="task_issued", payload="payload"):
    return {
        "schema": "P5R0RFC3161TimingBridgeRequestV1",
        "run_id": "run-1",
        "task_id": task_id,
        "event": event,
        "payload_digest": digest(payload),
    }


def _service(*, adapter=None, signer=None, authority=None, ledger=None, production_ready=False):
    signer = signer or _Signer()
    authority = authority or _authority(signer)
    return TimingBridgeService(
        adapter or _Adapter(),
        authority,
        signer,
        ledger or InMemoryTimingBridgeLedger(non_production=True),
        production_ready=production_ready,
    )


def test_legacy_digest_only_adapter_is_rejected_at_bridge_construction():
    class _LegacyAdapter:
        def record(self, **kwargs):
            return _evidence(kwargs, 1)

    with pytest.raises(TimingBridgeServiceError, match="proof"):
        _service(adapter=_LegacyAdapter())


    adapter = _Adapter()
    service = _service(adapter=adapter)
    request = _request()
    envelope = service.handle(canonical_bytes(request))
    assert set(envelope) == {"schema", "record", "proof"}
    record = envelope["record"]
    assert envelope["schema"] == "P5R0RFC3161TimingBridgeEnvelopeV1"
    assert set(record) == {
        "schema", "ledger_id", "run_id", "task_id", "event", "sequence",
        "previous_digest", "seed_digest", "payload_digest", "observed_at",
        "authority_id", "key_id", "public_key", "public_key_digest",
        "rfc3161_evidence_digest", "signature",
    }
    assert record["schema"] == BRIDGE_RECORD_SCHEMA
    assert record["observed_at"] == "2025-01-01T00:00:00.123000Z"
    assert record["seed_digest"] == record["rfc3161_evidence_digest"]
    assert record["rfc3161_evidence_digest"] == digest(adapter.evidence[1])
    assert envelope["proof"]["schema"] == "P5R0RFC3161ProofV1"
    assert "token_digest" not in record and "token_bytes" not in record
    assert adapter.calls == [{
        "run_id": "run-1", "task_id": "task-1", "event": "task_issued",
        "payload_digest": request["payload_digest"],
    }]


def test_sequence_and_previous_digest_come_from_ledger_chain():
    service = _service()
    first_request = _request()
    second_request = _request(task_id="task-2", event="result_received", payload="result")
    first = service.record(first_request)["record"]
    second = service.record(second_request)["record"]
    assert first["sequence"] == 1 and first["previous_digest"] is None
    assert second["sequence"] == 2 and second["previous_digest"] == digest(first)


def test_replay_and_event_conflict_fail_closed_before_adapter_call():
    adapter = _Adapter()
    service = _service(adapter=adapter)
    request = _request()
    service.record(request)
    with pytest.raises(TimingBridgeServiceError, match="replay"):
        service.record(dict(request))
    assert len(adapter.calls) == 1

    conflict = _request(payload="different")
    with pytest.raises(TimingBridgeServiceError, match="conflict"):
        service.record(conflict)
    assert len(adapter.calls) == 1


def test_signer_and_authority_mismatch_fails_closed():
    signer = _Signer()
    authority = TimingAuthorityConfig(
        authority_id="attacker-authority",
        key_id="bridge-key",
        ledger_id="bridge-ledger",
        public_key_digest=signer.authority["public_key_digest"],
    )
    with pytest.raises(TimingBridgeServiceError, match="signer/authority"):
        _service(signer=signer, authority=authority)


def test_production_mode_rejects_non_durable_in_memory_ledger():
    with pytest.raises(TimingBridgeServiceError, match="durable"):
        _service(production_ready=True)


def test_malformed_or_noncanonical_request_fails_closed():
    service = _service()
    with pytest.raises(TimingBridgeServiceError, match="canonical"):
        service.handle(b'{"schema":"P5R0RFC3161TimingBridgeRequestV1","run_id":"run-1","task_id":"task-1","event":"task_issued","payload_digest":"' + digest("payload").encode() + b'"}')
    malformed = _request()
    malformed.pop("payload_digest")
    with pytest.raises(TimingBridgeServiceError, match="schema"):
        service.record(malformed)
    invalid_event = _request(event="other")
    with pytest.raises(TimingBridgeServiceError, match="event"):
        service.record(invalid_event)


def test_adapter_evidence_mismatch_fails_closed_and_is_not_ledgered():
    class _TamperedAdapter(_Adapter):
        def record(self, **kwargs):
            self.calls.append(kwargs)
            return _evidence(kwargs, 1, payload_digest=digest("different"))

    adapter = _TamperedAdapter()
    service = _service(adapter=adapter)
    with pytest.raises(TimingBridgeServiceError, match="evidence mismatch"):
        service.record(_request())
    assert service.ledger.head("run-1").sequence == 0
