from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from services.p5_r0_evaluator.auth import StaticTokenVerifier
from services.p5_r0_evaluator.canonical import b64decode, b64encode, canonical_bytes, digest, parse_canonical, signing_digest
from services.p5_r0_evaluator.interfaces import Principal, StoreError
from services.p5_r0_evaluator.input_builder import input_builder_binding
from services.p5_r0_evaluator.service import EvaluatorService, ServiceError
from services.p5_r0_evaluator.store import MemoryStore
from services.p5_r0_evaluator.timing import sign_independent_timing_attestation_v3
from services.p5_r0_evaluator.time_seed import time_seed_algorithm_binding


class FakeSigner:
    def __init__(self):
        self.key = Ed25519PrivateKey.generate()
        public = b64encode(self.key.public_key().public_bytes_raw())
        self.authority = {"schema": "P5R0AuthorityV3", "authority_id": "test-authority", "key_id": "test-key", "public_key": public, "public_key_digest": digest(public), "transport_attestation": {"provider": "test", "event": "fixed"}}

    def sign_digest(self, value: bytes) -> str:
        return b64encode(self.key.sign(value))


class FakeEngine:
    def __init__(self):
        self.value = 0

    def issue(self, **kwargs):
        return {"schema": "P5R0WorkerTaskV3", "case_token": digest(kwargs["case"]["case_id"]), "task_nonce": kwargs["nonce"], "observation": {"x": 1}, "legal_actions": ["a", "b"], "protocol_budget": {"max_steps": 1, "frame_bytes": 65536, "wall_seconds": 3}, "episode_step": 0, "reset_policy": "fresh_case", "arm": kwargs["arm"], "persistent_projection": {}, "control": None}

    def evaluate(self, **kwargs):
        self.value += 1
        return {"schema": "P5R0EvaluatorOutcomeV3", "outcome": "complete_correct"}

    def checkpoint(self):
        return {"schema": "FakeCheckpointV1", "value": self.value}

    def restore_checkpoint(self, checkpoint):
        if checkpoint.get("schema") != "FakeCheckpointV1":
            raise ValueError("checkpoint")
        self.value = checkpoint["value"]

    def restore(self):
        return digest("restored")


class FakeTiming:
    def __init__(self):
        self.events = []

    def record(self, *, run_id, task_id, event, payload_digest):
        self.events.append(event)
        return {"schema": "P5R0TimingAttestationV1", "run_id": run_id, "task_id": task_id, "event": event, "sequence": len(self.events), "seed_digest": digest({"seed": len(self.events)}), "payload_digest": payload_digest, "observed_at": f"2025-01-01T00:00:0{len(self.events)}Z", "authority_id": "third-party-clock", "signature": "third-party-signature"}




class FakeIndependentTiming:
    independent = True

    def __init__(self):
        self.key = Ed25519PrivateKey.generate()
        self.public_key = b64encode(self.key.public_key().public_bytes_raw())
        self.authority_id = "independent-authority"
        self.key_id = "independent-key"
        self.ledger_id = "independent-ledger"
        self.public_key_digest = digest(self.public_key)
        self.events = []
        self.records = []

    def record(self, *, run_id, task_id, event, payload_digest):
        self.events.append(event)
        sequence = len(self.records) + 1
        value = {"schema": "P5R0IndependentTimingAttestationV3", "ledger_id": self.ledger_id,
                 "run_id": run_id, "task_id": task_id, "event": event, "sequence": sequence,
                 "previous_digest": digest(self.records[-1]) if self.records else None,
                 "seed_digest": digest({"seed": sequence}), "payload_digest": payload_digest,
                 "observed_at": f"2025-01-01T00:00:0{sequence}Z", "authority_id": self.authority_id,
                 "key_id": self.key_id, "public_key": self.public_key,
                 "public_key_digest": self.public_key_digest,
                 "rfc3161_evidence_digest": digest({"rfc3161": sequence}), "signature": ""}
        value = sign_independent_timing_attestation_v3(value, self)
        self.records.append(value)
        return value

    def sign_digest(self, value):
        return b64encode(self.key.sign(value))


class FakeEngineFactory:
    def create(self, manifest, private_store):
        return FakeEngine()

    def rehydrate(self, manifest, private_store, checkpoint):
        engine = FakeEngine()
        engine.restore_checkpoint(checkpoint)
        return engine


def _fixture():
    signer = FakeSigner()
    row = {"schema": "P5R0CaseManifestV2", "case_id": "case-1", "ordinal": 0}
    index_digest = digest([row])
    truth_digest = digest({"case-1": {"opaque": True}})
    cases = [{"case_id": "case-1"}]
    store_digest = digest({"case_index_digest": index_digest, "truth_digest": truth_digest, "cases": cases})
    private_store = {"schema": "P5R0CaseStoreV2", "case_index_digest": index_digest, "truth_digest": truth_digest, "cases": cases, "store_digest": store_digest}
    manifest = {"schema": "P5R0ManifestV2", "case_index": [row], "index_digest": index_digest, "truth_digest": truth_digest, "store_digest": store_digest, "split_digest": digest("split"), "input_builder_binding": input_builder_binding(), "time_seed_algorithm_binding": time_seed_algorithm_binding(), "manifest_digest": ""}
    manifest["manifest_digest"] = digest({k: v for k, v in manifest.items() if k != "manifest_digest"})
    worker_contract = {"task_schema": "P5R0WorkerTaskV3", "reply_schema": "P5R0WorkerReplyV3", "digest": digest({"task_schema": "P5R0WorkerTaskV3", "reply_schema": "P5R0WorkerReplyV3"})}
    lock = {"schema": "P5R0LocalLockV3", "classification": "local_readiness_only", "non_release": True, "authority": signer.authority, "authority_digest": digest(signer.authority), "authority_transport_digest": digest(signer.authority["transport_attestation"]), "manifest_digest": manifest["manifest_digest"], "case_index_digest": index_digest, "truth_digest": truth_digest, "store_digest": store_digest, "input_builder_binding": manifest["input_builder_binding"], "time_seed_algorithm_binding": manifest["time_seed_algorithm_binding"], "policy": {"schema": "P5R0GatePolicyV3"}, "worker_contract": worker_contract, "lock_digest": "", "signature": ""}
    lock["lock_digest"] = digest({k: v for k, v in lock.items() if k not in {"lock_digest", "signature"}})
    lock["signature"] = signer.sign_digest(signing_digest(lock, "lock_digest"))
    objects = {f"locks/{lock['lock_digest']}.json": lock, f"manifests/{manifest['manifest_digest']}.json": manifest, f"truth/{store_digest}.json": private_store}
    return signer, lock, manifest, MemoryStore(objects)


def _service(timing=None):
    signer, lock, manifest, store = _fixture()
    verifier = StaticTokenVerifier({"token": Principal("runner")})
    timing_kwargs = {}
    if getattr(timing, "independent", False):
        timing_kwargs = {"timing_authority_id": timing.authority_id, "timing_key_id": timing.key_id, "timing_ledger_id": timing.ledger_id, "timing_public_key_digest": timing.public_key_digest}
    return EvaluatorService(store=store, signer=signer, verifier=verifier, engine_factory=FakeEngineFactory(), timing_attestor=timing, **timing_kwargs), signer, lock, manifest


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





def test_timing_first_rejects_no_seed_and_legacy_v1_before_evaluation():
    timing = FakeIndependentTiming()
    service, _, lock, manifest = _service(timing)
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "timing-first-start", "execution_mode": "timing_first"}
    started = service.start(start, Principal("runner"))
    with pytest.raises(ServiceError, match="seed must be committed"):
        service.next_task(started["run_id"], {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "timing-first-next-before-seed"}, Principal("runner"))
    assert timing.events == []
    service.issue_time_seed(started["run_id"], "production-inputs", Principal("runner"))
    task = service.next_task(started["run_id"], {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "timing-first-next"}, Principal("runner"))
    legacy = {"schema": "P5R0TaskResultRequestV1", "run_id": started["run_id"], "task_id": task["task_id"], "sequence": 1, "task_digest": task["task_digest"], "reply": {"schema": "P5R0WorkerReplyV3", "action": 0}, "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None}, "worker_invocation": "unknown", "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False}, "idempotency_key": "timing-first-legacy"}
    with pytest.raises(ServiceError, match="diagnostic-only"):
        service.submit_result(started["run_id"], task["task_id"], legacy, Principal("runner"))
    state = parse_canonical(service.store.get(f"runs/{started['run_id']}/state.json").data)
    assert state["issued"]["task_id"] == task["task_id"] and state["cursor"] == 0

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



def test_repository_restart_rehydrates_checkpointed_engine():
    signer, lock, manifest, store = _fixture()

    class CheckpointEngine(FakeEngine):
        def checkpoint(self):
            return {"schema": "TestEngineCheckpointV1", "counter": 0}

    class CheckpointFactory:
        def __init__(self):
            self.rehydrated = None

        def create(self, manifest, private_store):
            return CheckpointEngine()

        def rehydrate(self, manifest, private_store, checkpoint):
            self.rehydrated = checkpoint
            return CheckpointEngine()

    verifier = StaticTokenVerifier({"token": Principal("runner")})
    factory_a = CheckpointFactory()
    first = EvaluatorService(store=store, signer=signer, verifier=verifier, engine_factory=factory_a)
    request = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "restart-start"}
    started = first.start(request, Principal("runner"))
    task = first.next_task(started["run_id"], {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "restart-next"}, Principal("runner"))

    second = EvaluatorService(store=store, signer=signer, verifier=verifier, engine_factory=factory_a)
    result = {"schema": "P5R0TaskResultRequestV1", "run_id": started["run_id"], "task_id": task["task_id"], "sequence": 1, "task_digest": task["task_digest"], "reply": {"schema": "P5R0WorkerReplyV3", "action": 0}, "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None}, "worker_invocation": "unknown", "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False}, "idempotency_key": "restart-result"}
    submitted = second.submit_result(started["run_id"], task["task_id"], result, Principal("runner"))
    assert submitted["outcome"] == "complete_correct"
    assert factory_a.rehydrated is not None
    assert factory_a.rehydrated["schema"] == "TestEngineCheckpointV1"


def test_repository_restart_without_checkpoint_fails_closed():
    service, _, lock, manifest = _service()
    request = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "legacy-start"}
    started = service.start(request, Principal("runner"))
    state_name = f"runs/{started['run_id']}/state.json"
    state_item = service.store.get(state_name)
    state = parse_canonical(state_item.data)
    state.pop("engine_checkpoint", None)
    state.pop("engine_checkpoint_digest", None)
    service.store.replace(state_name, canonical_bytes(state), state_item.generation)
    restarted = EvaluatorService(store=service.store, signer=service.signer, verifier=StaticTokenVerifier({"token": Principal("runner")}), engine_factory=service.engine_factory)
    with pytest.raises(ServiceError, match="checkpoint unavailable"):
        restarted.next_task(started["run_id"], {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "legacy-next"}, Principal("runner"))



def test_post_evaluation_persistence_failure_rehydrates_last_checkpoint_and_retries():
    signer, lock, manifest, base_store = _fixture()

    class EvidenceFailureStore(type(base_store)):
        def __init__(self):
            super().__init__()
            self.fail_evidence = True

        def create(self, name, data):
            if "/evidence/" in name and self.fail_evidence:
                raise StoreError("injected evidence persistence failure")
            return super().create(name, data)

    store = EvidenceFailureStore()
    store._objects = dict(base_store._objects)
    service = EvaluatorService(
        store=store, signer=signer, verifier=StaticTokenVerifier({"token": Principal("runner")}),
        engine_factory=FakeEngineFactory(),
    )
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "rollback-start"}
    started = parse_canonical(service.dispatch("POST", "/v1/runs", canonical_bytes(start), _headers())[2])
    next_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "rollback-next"}
    task = parse_canonical(service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/next", canonical_bytes(next_request), _headers())[2])
    result = {"schema": "P5R0TaskResultRequestV1", "run_id": started["run_id"], "task_id": task["task_id"], "sequence": 1, "task_digest": task["task_digest"], "reply": {"schema": "P5R0WorkerReplyV3", "action": 0}, "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None}, "worker_invocation": "unknown", "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False}, "idempotency_key": "rollback-result"}
    status, _, _ = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/{task['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 503
    assert service._engines[started["run_id"]].value == 0
    state = parse_canonical(store.get(f"runs/{started['run_id']}/state.json").data)
    assert state["issued"]["task_id"] == task["task_id"]
    assert state["cursor"] == 0
    assert state["engine_checkpoint"]["value"] == 0
    assert state["engine_checkpoint_digest"] == digest(state["engine_checkpoint"])

    store.fail_evidence = False
    status, _, raw = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/{task['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 200
    submitted = parse_canonical(raw)
    assert submitted["receipt"]["sequence"] == 2
    final_state = parse_canonical(store.get(f"runs/{started['run_id']}/state.json").data)
    assert final_state["cursor"] == 1 and final_state["next_sequence"] == 2 and final_state["issued"] is None
    assert final_state["engine_checkpoint"]["value"] == 1
    assert final_state["receipts"] == [
        parse_canonical(store.get(f"runs/{started['run_id']}/receipts/{sequence:06d}.json").data)["receipt_hash"]
        for sequence in (1, 2)
    ]


def test_timing_outbox_recovers_seed_after_state_failure_without_second_recorder_call():
    timing = FakeIndependentTiming()
    signer, lock, manifest, base_store = _fixture()

    class StateFailureStore(type(base_store)):
        def __init__(self):
            super().__init__()
            self.fail_state = False

        def replace(self, name, data, generation):
            if name.endswith("/state.json") and self.fail_state:
                self.fail_state = False
                raise StoreError("injected state persistence failure")
            return super().replace(name, data, generation)

    store = StateFailureStore()
    store._objects = dict(base_store._objects)
    service = EvaluatorService(store=store, signer=signer, verifier=StaticTokenVerifier({"token": Principal("runner")}), engine_factory=FakeEngineFactory(), timing_attestor=timing, timing_authority_id=timing.authority_id, timing_key_id=timing.key_id, timing_ledger_id=timing.ledger_id, timing_public_key_digest=timing.public_key_digest)
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "timing-retry-start"}
    started = service.start(start, Principal("runner"))
    store.fail_state = True
    with pytest.raises(ServiceError, match="state generation conflict"):
        service.issue_time_seed(started["run_id"], "namespace-a", Principal("runner"))
    assert timing.events == ["task_issued"]
    with pytest.raises(ServiceError, match="conflicting time-seed request reuse"):
        service.issue_time_seed(started["run_id"], "namespace-b", Principal("runner"))
    assert timing.events == ["task_issued"]

    seed = service.issue_time_seed(started["run_id"], "namespace-a", Principal("runner"))
    assert timing.events == ["task_issued"]
    state = parse_canonical(store.get(f"runs/{started['run_id']}/state.json").data)
    assert state["timing_sequence"] == 1
    assert state["timing_record_digest"] == seed["timing_record_digest"]
    assert state["time_seed_timing_record_digest"] == seed["timing_record_digest"]
    receipt = parse_canonical(store.get(f"runs/{started['run_id']}/receipts/000002.json").data)
    assert receipt["payload"]["binding"]["timing_record_digest"] == seed["timing_record_digest"]
    timing_object = parse_canonical(store.get(f"runs/{started['run_id']}/timing/000001-seed.json").data)
    assert digest(timing_object) == seed["timing_record_digest"]


def test_time_seed_rejects_diagnostic_v1_before_recorder_or_seed_artifacts():
    timing = FakeTiming()
    service, _, lock, manifest = _service(timing)
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "v1-seed-start"}
    started = service.start(start, Principal("runner"))
    with pytest.raises(ServiceError, match="independent V3 timing authority unavailable"):
        service.issue_time_seed(started["run_id"], "namespace", Principal("runner"))
    assert timing.events == []
    assert not any("timing-outbox/seed-intent.json" in name for name in service.store._objects)


def test_timing_outbox_recovers_result_after_state_failure_without_second_recorder_call():
    timing = FakeTiming()
    signer, lock, manifest, base_store = _fixture()

    class StateFailureStore(type(base_store)):
        def __init__(self):
            super().__init__()
            self.fail_state = False

        def replace(self, name, data, generation):
            if name.endswith("/state.json") and self.fail_state:
                self.fail_state = False
                raise StoreError("injected state persistence failure")
            return super().replace(name, data, generation)

    store = StateFailureStore()
    store._objects = dict(base_store._objects)
    service = EvaluatorService(store=store, signer=signer, verifier=StaticTokenVerifier({"token": Principal("runner")}), engine_factory=FakeEngineFactory(), timing_attestor=timing)
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "result-timing-start"}
    started = parse_canonical(service.dispatch("POST", "/v1/runs", canonical_bytes(start), _headers())[2])
    next_request = {"schema": "P5R0NextTaskRequestV1", "expected_sequence": 1, "idempotency_key": "result-timing-next"}
    task = parse_canonical(service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/next", canonical_bytes(next_request), _headers())[2])
    result = {"schema": "P5R0TaskResultRequestV1", "run_id": started["run_id"], "task_id": task["task_id"], "sequence": 1, "task_digest": task["task_digest"], "reply": {"schema": "P5R0WorkerReplyV3", "action": 0}, "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None}, "worker_invocation": "unknown", "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False}, "idempotency_key": "result-timing-result"}
    store.fail_state = True
    status, _, raw = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/{task['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 409, raw
    assert timing.events == ["task_issued", "result_received"]

    status, _, raw = service.dispatch("POST", f"/v1/runs/{started['run_id']}/tasks/{task['task_id']}/result", canonical_bytes(result), _headers())
    assert status == 200
    assert timing.events == ["task_issued", "result_received"]
    response = parse_canonical(raw)
    state = parse_canonical(store.get(f"runs/{started['run_id']}/state.json").data)
    received = parse_canonical(store.get(f"runs/{started['run_id']}/timing/000001-received.json").data)
    receipt = parse_canonical(store.get(f"runs/{started['run_id']}/receipts/000002.json").data)
    assert state["timing_sequence"] == 2
    assert state["timing_record_digest"] == digest(received)
    assert response["receipt"] == receipt
    assert receipt["payload"]["binding"]["timing"]["received"] == digest(received)


def test_timing_outbox_conflicting_reuse_fails_closed_before_recorder():
    timing = FakeTiming()
    service, _, _, _ = _service(timing)
    state = {"run_id": digest("timing-conflict-run"), "timing_sequence": 0, "timing_record_digest": None}
    service._record_timing(state, task_id="same-task", event="task_issued", payload_digest=digest("first"))
    with pytest.raises(ServiceError, match="conflicting timing request reuse"):
        service._record_timing({"run_id": state["run_id"], "timing_sequence": 0, "timing_record_digest": None}, task_id="same-task", event="task_issued", payload_digest=digest("second"))
    assert timing.events == ["task_issued"]



def test_timing_outbox_finalization_failure_recovers_record_without_second_recorder_call():
    timing = FakeIndependentTiming()
    signer, lock, manifest, base_store = _fixture()

    class OutboxFinalizationFailureStore(type(base_store)):
        def __init__(self):
            super().__init__()
            self.fail_outbox_replace = True

        def replace(self, name, data, generation):
            if "timing-outbox/sha256:" in name and self.fail_outbox_replace:
                self.fail_outbox_replace = False
                raise StoreError("injected timing outbox finalization failure")
            return super().replace(name, data, generation)

    store = OutboxFinalizationFailureStore()
    store._objects = dict(base_store._objects)
    service = EvaluatorService(
        store=store, signer=signer, verifier=StaticTokenVerifier({"token": Principal("runner")}),
        engine_factory=FakeEngineFactory(), timing_attestor=timing,
        timing_authority_id=timing.authority_id, timing_key_id=timing.key_id,
        timing_ledger_id=timing.ledger_id, timing_public_key_digest=timing.public_key_digest,
    )
    start = {"schema": "P5R0RunStartRequestV1", "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "worker_contract_digest": lock["worker_contract"]["digest"], "idempotency_key": "outbox-finalization-start"}
    started = service.start(start, Principal("runner"))
    with pytest.raises(ServiceError, match="timing recovery record could not be committed"):
        service.issue_time_seed(started["run_id"], "namespace-finalization", Principal("runner"))
    assert timing.events == ["task_issued"]

    recovered = service.issue_time_seed(started["run_id"], "namespace-finalization", Principal("runner"))
    assert timing.events == ["task_issued"]
    state = parse_canonical(store.get(f"runs/{started['run_id']}/state.json").data)
    assert state["timing_sequence"] == 1
    assert state["time_seed_timing_record_digest"] == recovered["timing_record_digest"]
