from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from services.p5_r0_evaluator.auth import StaticTokenVerifier
from services.p5_r0_evaluator.canonical import b64decode, b64encode, canonical_bytes, digest, parse_canonical, signing_digest
from services.p5_r0_evaluator.interfaces import Principal
from services.p5_r0_evaluator.service import EvaluatorService, ServiceError
from services.p5_r0_evaluator.store import MemoryStore


class FakeSigner:
    def __init__(self):
        self.key = Ed25519PrivateKey.generate()
        public = b64encode(self.key.public_key().public_bytes_raw())
        self.authority = {"schema": "P5R0AuthorityV3", "authority_id": "test-authority", "key_id": "test-key", "public_key": public, "public_key_digest": digest(public), "transport_attestation": {"provider": "test", "event": "fixed"}}

    def sign_digest(self, value: bytes) -> str:
        return b64encode(self.key.sign(value))


class FakeEngine:
    def issue(self, **kwargs):
        return {"schema": "P5R0WorkerTaskV3", "case_token": digest(kwargs["case"]["case_id"]), "task_nonce": kwargs["nonce"], "observation": {"x": 1}, "legal_actions": ["a", "b"], "protocol_budget": {"max_steps": 1, "frame_bytes": 65536, "wall_seconds": 3}, "episode_step": 0, "reset_policy": "fresh_case", "arm": kwargs["arm"], "persistent_projection": {}, "control": None}

    def evaluate(self, **kwargs):
        return {"schema": "P5R0EvaluatorOutcomeV3", "outcome": "complete_correct"}

    def restore(self):
        return digest("restored")


class FakeTiming:
    def __init__(self):
        self.events = []

    def record(self, *, run_id, task_id, event, payload_digest):
        self.events.append(event)
        return {"schema": "P5R0TimingAttestationV1", "run_id": run_id, "task_id": task_id, "event": event, "sequence": len(self.events), "seed_digest": digest({"seed": len(self.events)}), "payload_digest": payload_digest, "observed_at": f"2025-01-01T00:00:0{len(self.events)}Z", "authority_id": "third-party-clock", "signature": "third-party-signature"}


class FakeEngineFactory:
    def create(self, manifest, private_store):
        return FakeEngine()


def _fixture():
    signer = FakeSigner()
    row = {"schema": "P5R0CaseManifestV2", "case_id": "case-1", "ordinal": 0}
    index_digest = digest([row])
    truth_digest = digest({"case-1": {"opaque": True}})
    cases = [{"case_id": "case-1"}]
    store_digest = digest({"case_index_digest": index_digest, "truth_digest": truth_digest, "cases": cases})
    private_store = {"schema": "P5R0CaseStoreV2", "case_index_digest": index_digest, "truth_digest": truth_digest, "cases": cases, "store_digest": store_digest}
    manifest = {"schema": "P5R0ManifestV2", "case_index": [row], "index_digest": index_digest, "truth_digest": truth_digest, "store_digest": store_digest, "split_digest": digest("split"), "manifest_digest": ""}
    manifest["manifest_digest"] = digest({k: v for k, v in manifest.items() if k != "manifest_digest"})
    worker_contract = {"task_schema": "P5R0WorkerTaskV3", "reply_schema": "P5R0WorkerReplyV3", "digest": digest({"task_schema": "P5R0WorkerTaskV3", "reply_schema": "P5R0WorkerReplyV3"})}
    lock = {"schema": "P5R0LocalLockV3", "classification": "local_readiness_only", "non_release": True, "authority": signer.authority, "authority_digest": digest(signer.authority), "authority_transport_digest": digest(signer.authority["transport_attestation"]), "manifest_digest": manifest["manifest_digest"], "case_index_digest": index_digest, "truth_digest": truth_digest, "store_digest": store_digest, "policy": {"schema": "P5R0GatePolicyV3"}, "worker_contract": worker_contract, "lock_digest": "", "signature": ""}
    lock["lock_digest"] = digest({k: v for k, v in lock.items() if k not in {"lock_digest", "signature"}})
    lock["signature"] = signer.sign_digest(signing_digest(lock, "lock_digest"))
    objects = {f"locks/{lock['lock_digest']}.json": lock, f"manifests/{manifest['manifest_digest']}.json": manifest, f"truth/{store_digest}.json": private_store}
    return signer, lock, manifest, MemoryStore(objects)


def _service(timing=None):
    signer, lock, manifest, store = _fixture()
    verifier = StaticTokenVerifier({"token": Principal("runner")})
    return EvaluatorService(store=store, signer=signer, verifier=verifier, engine_factory=FakeEngineFactory(), timing_attestor=timing), signer, lock, manifest


def _headers():
    return {"authorization": "Bearer token"}


def test_canonical_input_rejects_noncanonical_and_duplicate_keys():
    import pytest
    with pytest.raises(ValueError):
        parse_canonical(b'{"b":1,"a":1}')
    with pytest.raises(ValueError):
        parse_canonical(b'{"a":1,"a":1}')


def test_start_task_result_is_signed_and_replay_safe():
    service, signer, lock, manifest = _service()
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "start-1"}
    status, _, raw = service.dispatch("POST", "/v1/runs", canonical_bytes(start), _headers())
    assert status == 200
    started = parse_canonical(raw)
    next_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "next-1"}
    status, _, raw = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/next", canonical_bytes(next_request), _headers())
    assert status == 200
    task_response = parse_canonical(raw)
    envelope = task_response["task_envelope"]
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    Ed25519PublicKey.from_public_bytes(b64decode(signer.authority["public_key"])).verify(b64decode(envelope["signature"]), signing_digest(envelope))
    result = {"schema": "P5R0TaskResultRequestV1", "run_id": started["run_id"], "task_id": task_response["task_id"], "sequence": 1, "task_digest": task_response["task_digest"], "reply": {"schema": "P5R0WorkerReplyV3", "action": 0}, "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None}, "worker_invocation": "unknown", "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False}, "idempotency_key": "result-1"}
    status, _, raw = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/{task_response['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 200
    submitted = parse_canonical(raw)
    assert submitted["outcome"] == "complete_correct" and submitted["receipt"]["schema"] == "P5R0ReceiptV3"
    status, _, duplicate = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/{task_response['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 200 and duplicate == raw
    result["reply"]["action"] = 1
    status, _, _ = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/{task_response['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 409


def test_missing_identity_fails_closed():
    service, _, lock, manifest = _service()
    request = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "start-1"}
    status, _, _ = service.dispatch("POST", "/v1/runs", canonical_bytes(request), {})
    assert status == 401



def test_third_party_seed_ledger_is_explicit_and_bound_to_events():
    timing = FakeTiming()
    service, _, lock, manifest = _service(timing)
    request = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "timed-start"}
    status, _, raw = service.dispatch("POST", "/v1/runs", canonical_bytes(request), _headers())
    assert status == 200
    run = parse_canonical(raw)
    next_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "timed-next"}
    status, _, raw = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/next", canonical_bytes(next_request), _headers())
    assert status == 200
    state = parse_canonical(service.store.get(f"runs/{run['run_id']}/state.json").data)
    assert timing.events == ["task_issued"]
    assert state["issued"]["timing_attestation"]["seed_digest"].startswith("sha256:")



def test_compute_class_protocol_uses_kms_signature_and_private_commitments():
    service, signer, lock, manifest = _service()
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "compute-start"}
    status, _, raw = service.dispatch("POST", "/v1/runs", canonical_bytes(start), _headers())
    assert status == 200
    run = parse_canonical(raw)
    next_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "compute-next"}
    status, _, raw = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/next", canonical_bytes(next_request), _headers())
    assert status == 200
    task = parse_canonical(raw)
    seed_request = {"schema": "P5ComputeClassSeedRequestV1", "run_id": run["run_id"], "task_id": task["task_id"], "sequence": 1, "idempotency_key": "seed-1"}
    status, _, raw = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/{task['task_id']}/seed", canonical_bytes(seed_request), _headers())
    assert status == 200
    seed = parse_canonical(raw)
    common = {"run_id": run["run_id"], "task_id": task["task_id"], "sequence": 1, "seed_digest": seed["seed_digest"], "image_digest": digest("image"), "runtime_digest": digest("runtime"), "resource_profile_digest": digest("resources")}
    result = {"schema": "P5R0TaskResultRequestV1", "run_id": run["run_id"], "task_id": task["task_id"], "sequence": 1, "task_digest": task["task_digest"], "reply": {"schema": "P5R0WorkerReplyV3", "action": 0}, "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None}, "worker_invocation": "unknown", "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": common["runtime_digest"], "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False}, "idempotency_key": "compute-result"}
    status, _, raw = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/{task['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 200
    submitted_result = parse_canonical(raw)
    observation_request = {"schema": "P5ComputeClassObservationRequestV1", "run_id": run["run_id"], "task_id": task["task_id"], "sequence": 1, "task_digest": task["task_digest"], "seed_digest": seed["seed_digest"], "image_digest": common["image_digest"], "runtime_digest": common["runtime_digest"], "resource_profile_digest": common["resource_profile_digest"], "result_digest": digest(result), "idempotency_key": "observation-1"}
    status, _, raw = service.dispatch("POST", f"/v1/runs/{run['run_id']}/compute-class/observation", canonical_bytes(observation_request), _headers())
    assert status == 200
    observation = parse_canonical(raw)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    Ed25519PublicKey.from_public_bytes(b64decode(signer.authority["public_key"])).verify(b64decode(observation["signature"]), signing_digest(observation, "observation_digest"))
    assert observation["schema"] == "P5ComputeClassObservationV2"
    assert observation["result_digest"] == submitted_result["result_digest"] == digest(result)
    assert observation["issued_at_ms"] <= observation["received_at_ms"]
    assert observation["wall_vs_cpu"] == "provider_wall_transport_interval_not_worker_cpu"
    state = parse_canonical(service.store.get(f"runs/{run['run_id']}/state.json").data)
    assert "'seed':" not in str(state) and "wall_duration_ms" not in str(state)
    status, _, duplicate = service.dispatch("POST", f"/v1/runs/{run['run_id']}/compute-class/observation", canonical_bytes(observation_request), _headers())
    assert status == 200 and duplicate == raw


def test_server_timestamps_and_expiry_fail_closed():
    signer, lock, manifest, store = _fixture()
    now = [1000]
    service = EvaluatorService(store=store, signer=signer, verifier=StaticTokenVerifier({"token": Principal("runner")}), engine_factory=FakeEngineFactory(), clock_ms=lambda: now[0], task_ttl_ms=10)
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "expiry-start"}
    _, _, raw = service.dispatch("POST", "/v1/runs", canonical_bytes(start), _headers())
    run = parse_canonical(raw)
    next_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "expiry-next"}
    _, _, raw = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/next", canonical_bytes(next_request), _headers())
    task = parse_canonical(raw)
    assert task["issued_at_ms"] == 1000 and task["expires_at_ms"] == 1010
    now[0] = 1010
    expired_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "expiry-next-2"}
    status, _, _ = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/next", canonical_bytes(expired_request), _headers())
    assert status == 409
    seed_request = {"schema": "P5ComputeClassSeedRequestV1", "run_id": run["run_id"], "task_id": task["task_id"], "sequence": 1, "idempotency_key": "expiry-seed"}
    status, _, _ = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/{task['task_id']}/seed", canonical_bytes(seed_request), _headers())
    assert status == 409



def test_kms_ed25519_uses_raw_data_and_verifies_locally():
    from cryptography.hazmat.primitives import serialization
    from services.p5_r0_evaluator.signing import KMSConfigurationError, KMSEd25519Signer

    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
    raw_public = key.public_key().public_bytes_raw()
    public_b64 = b64encode(raw_public)
    authority = {"schema": "P5R0AuthorityV3", "authority_id": "kms-test", "key_id": "kms-key", "public_key": public_b64, "public_key_digest": digest(public_b64), "transport_attestation": {"provider": "test", "event": "fixed"}}

    class PublicResponse:
        pem = public
        algorithm = "EC_SIGN_ED25519"

    class SignatureResponse:
        def __init__(self, signature):
            self.signature = signature

    class Client:
        def get_public_key(self, *, request):
            assert request == {"name": "projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1"}
            return PublicResponse()

        def asymmetric_sign(self, *, request):
            assert request["name"].endswith("/1")
            assert request["data"] == message
            assert "digest" not in request
            return SignatureResponse(key.sign(request["data"]))

    message = signing_digest({"payload": "protocol"})
    with pytest.raises(KMSConfigurationError, match="explicit federated KMS client"):
        KMSEd25519Signer("projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1", authority)

    signer = KMSEd25519Signer("projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1", authority, Client())
    signature = b64decode(signer.sign_digest(message))
    key.public_key().verify(signature, message)

    class BadClient(Client):
        def asymmetric_sign(self, *, request):
            return SignatureResponse(Ed25519PrivateKey.generate().sign(request["data"]))

    bad = KMSEd25519Signer("projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1", authority, BadClient())
    try:
        bad.sign_digest(message)
    except KMSConfigurationError as exc:
        assert "invalid Ed25519 signature" in str(exc)
    else:
        raise AssertionError("invalid KMS signature was accepted")



def test_terminal_seal_is_signed_and_tamper_rejected_on_result_read():
    service, _, lock, manifest = _service()
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "seal-start"}
    status, _, raw = service.dispatch("POST", "/v1/runs", canonical_bytes(start), _headers())
    assert status == 200
    run = parse_canonical(raw)
    for sequence in range(1, 4):
        next_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": sequence, "idempotency_key": f"seal-next-{sequence}"}
        status, _, raw = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/next", canonical_bytes(next_request), _headers())
        assert status == 200
        task = parse_canonical(raw)
        result = {"schema": "P5R0TaskResultRequestV1", "run_id": run["run_id"], "task_id": task["task_id"], "sequence": sequence, "task_digest": task["task_digest"], "reply": {"schema": "P5R0WorkerReplyV3", "action": 0}, "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None}, "worker_invocation": "unknown", "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False}, "idempotency_key": f"seal-result-{sequence}"}
        status, _, _ = service.dispatch("POST", f"/v1/runs/{run['run_id']}/tasks/{task['task_id']}/result", canonical_bytes(result), _headers())
        assert status == 200
    status, _, raw = service.dispatch("GET", f"/v1/runs/{run['run_id']}/result", b"", _headers())
    assert status == 200
    served = parse_canonical(raw)
    seal = served["result_seal"]
    assert seal["schema"] == "P5R0ResultSealV4" and seal["external_authority_verified"] is False
    seal["chain_digest"] = digest("forged-chain")
    with pytest.raises(ServiceError, match="receipt binding"):
        service._verify_result_seal(parse_canonical(service.store.get(f"runs/{run['run_id']}/state.json").data), seal)



def test_service_requires_adapter_binding_and_never_accepts_forged_dict():
    signer, _, _, store = _fixture()
    verifier = StaticTokenVerifier({"token": Principal("runner")})
    service = EvaluatorService(store=store, signer=signer, verifier=verifier)
    assert service.attestation_binding is None
    assert service.bounded_compute_ready is False
    assert service.bounded_compute_certified is False
    with pytest.raises(ValueError, match="adapter-created"):
        EvaluatorService(store=store, signer=signer, verifier=verifier, verified_attestation_binding={})
