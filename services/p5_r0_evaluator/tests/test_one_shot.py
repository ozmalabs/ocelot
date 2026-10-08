import pytest

from services.p5_r0_evaluator.attestation_binding import _build_verified_attestation_binding
from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest, parse_canonical
from services.p5_r0_evaluator.confidential_space import FederatedAccessToken, VerifiedAttestation
from services.p5_r0_evaluator.one_shot import OneShotConfig, OneShotProductionError, OneShotProductionRunner
from services.p5_r0_evaluator.tests.test_client import _authority, _task_response
from services.p5_r0_evaluator.tests.test_confidential_space import _claims, _config


class FakeTiming:
    independent = True
    authority = object()

    def record(self, *, run_id, task_id, event, payload_digest):
        return {
            "schema": "P5R0IndependentTimingAttestationV3", "ledger_id": "timing-ledger",
            "run_id": run_id, "task_id": task_id, "event": event, "sequence": 1,
            "previous_digest": None, "seed_digest": digest({"timing": task_id}),
            "payload_digest": payload_digest, "observed_at": "2026-01-01T00:00:00Z",
            "authority_id": "timing-authority", "key_id": "timing-key",
            "public_key": "timing-public", "public_key_digest": digest("timing-public"),
            "rfc3161_evidence_digest": digest({"rfc3161": task_id}), "signature": "timing-signature",
        }


class FakeService:
    timing_certified = True
    timing_attestor = FakeTiming()
    signer = object()
    store = object()

    def __init__(self, task_response, result):
        self.task_response = task_response
        self.result_value = result
        self.started = False
        self.submitted = []

    def start(self, request, principal):
        self.started = True
        return {
            "run_id": self.task_response["run_id"],
            "lock_digest": digest("lock"),
            "manifest_digest": digest("manifest"),
            "worker_contract_digest": digest("worker"),
        }

    def issue_time_seed(self, run_id, namespace, principal):
        task_id = digest({"schema": "P5R0TimeSeedTaskV1", "run_id": run_id, "namespace": namespace, "sequence": 0})
        payload_digest = digest({"schema": "P5R0TimeSeedRequestV1", "run_id": run_id, "namespace": namespace, "sequence": 0})
        record = self.timing_attestor.record(run_id=run_id, task_id=task_id, event="task_issued", payload_digest=payload_digest)
        return {"schema": "P5R0TimeSeedResponseV1", "run_id": run_id, "task_id": task_id, "timing_record": record, "timing_record_digest": digest(record), "namespace_digest": digest(namespace)}

    def next_task(self, run_id, request, principal):
        return self.task_response

    def submit_result(self, run_id, task_id, result, principal):
        self.submitted.append(result)
        return {"disposition": "impasse", "done": True}

    def result(self, run_id, principal):
        return self.result_value


class FakeAdapter:
    def __init__(self, service, binding=None, *, attested=True):
        self._service = service
        self._binding = binding
        self._attested = attested
        self.startup_evidence = {"schema": "P5R0StartupAttestationEvidenceV1", "status": "attested", "policy_digest": digest("policy")}

    @property
    def attested(self):
        return self._attested

    @property
    def attestation_binding(self):
        return self._binding

    def activate_attested_service(self):
        return self._service


def _binding():
    config, _ = _config()
    claims = _claims(config)
    attestation = VerifiedAttestation(claims=claims, nonce="nonce-1234", subject_token="attested-token")
    token = FederatedAccessToken("federated-token", 4_000_000_000)
    return _build_verified_attestation_binding(attestation, token, config)


def _config_for(bundle_validator=lambda: None, closure_validator=lambda: None, evidence_validator=lambda *_: None, executor=lambda *_: {}, authorized_task_validator=lambda response: None):
    return OneShotConfig(
        lock_digest=digest("lock"), manifest_digest=digest("manifest"), worker_contract_digest=digest("worker"),
        principal_subject="attested-one-shot-subject", input_namespace="test-inputs",
        input_builder=lambda seed: {"seed": seed}, bundle_validator=bundle_validator,
        closure_validator=closure_validator, evidence_validator=evidence_validator,
        task_executor=executor, authorized_task_validator=authorized_task_validator, max_tasks=1,
    )


def _task_and_result():
    key, authority = _authority()
    run_id = digest("run")
    task = _task_response(key, authority, run_id=run_id)
    result = {
        "schema": "P5R0TaskResultRequestV1", "run_id": run_id, "task_id": task["task_id"],
        "sequence": 1, "task_digest": task["task_digest"],
        "reply": {"schema": "P5R0WorkerReplyV3", "action": None},
        "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None},
        "worker_invocation": "unknown",
        "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False},
        "idempotency_key": "one-shot-result",
    }
    return task, result


def _seeded_result(result, seeded):
    value = dict(result)
    evidence = dict(value["execution_evidence"])
    evidence.update({
        "schema": "P5R0ExecutionEvidenceV2",
        "timing_record_digest": seeded.timing_record_digest,
        "input_seed_digest": seeded.input_seed_digest,
        "input_digest": seeded.input_digest,
        "input_builder_implementation": seeded.input_builder_binding["implementation"],
        "input_builder_version": seeded.input_builder_binding["version"],
        "input_builder_source_digest": seeded.input_builder_binding["source_digest"],
        "time_seed_algorithm_source_digest": seeded.time_seed_algorithm_binding["source_digest"],
    })
    value["execution_evidence"] = evidence
    return value


def test_one_shot_requires_authorized_task_validator():
    config = OneShotConfig(
        lock_digest=digest("lock"), manifest_digest=digest("manifest"), worker_contract_digest=digest("worker"),
        principal_subject="attested-one-shot-subject", input_namespace="test-inputs", input_builder=lambda seed: {"seed": seed},
        bundle_validator=lambda: None, closure_validator=lambda: None,
        evidence_validator=lambda *_: None, task_executor=lambda *_: {},
    )
    with pytest.raises(OneShotProductionError, match="authorized task validator"):
        config.validate()


def test_one_shot_authorizes_before_callback_and_uses_service_timing():
    task, result = _task_and_result()
    service = FakeService(task, {"schema": "P5R0RunResultResponseV1", "run_id": task["run_id"], "status": "impasse", "disposition": "impasse"})
    called = []
    config = _config_for(
        authorized_task_validator=lambda response: (_ for _ in ()).throw(OneShotProductionError("unauthorized task")),
        executor=lambda *_: called.append(True) or {},
    )
    with pytest.raises(OneShotProductionError, match="task issuance"):
        OneShotProductionRunner(FakeAdapter(service, _binding()), config).run()
    assert called == []


def test_one_shot_fails_closed_without_service_owned_timing_operation():
    task, result = _task_and_result()
    service = FakeService(task, {"schema": "P5R0RunResultResponseV1", "run_id": task["run_id"], "status": "impasse", "disposition": "impasse"})
    service.issue_time_seed = None
    called = []
    config = _config_for(executor=lambda *_: called.append(True) or result)
    with pytest.raises(OneShotProductionError, match="time-seeded input derivation"):
        OneShotProductionRunner(FakeAdapter(service, _binding()), config).run()
    assert called == []

    with pytest.raises(OneShotProductionError, match="principal subject"):
        OneShotConfig(
            lock_digest=digest("lock"), manifest_digest=digest("manifest"), worker_contract_digest=digest("worker"),
            principal_subject="runner", input_namespace="test-inputs", input_builder=lambda seed: {"seed": seed},
            bundle_validator=lambda: None, closure_validator=lambda: None,
            evidence_validator=lambda _: None, task_executor=lambda _: {},
        ).validate()


def test_one_shot_requires_attested_binding_and_capabilities():
    task, _ = _task_and_result()
    service = FakeService(task, {"schema": "P5R0RunResultResponseV1", "run_id": task["run_id"], "status": "impasse", "disposition": "impasse"})
    runner = OneShotProductionRunner(FakeAdapter(service, binding=None, attested=False), _config_for())
    with pytest.raises(OneShotProductionError, match="attested"):
        runner.run()


def test_one_shot_validates_external_seams_and_emits_redacted_impasse():
    task, result = _task_and_result()
    service = FakeService(task, {"schema": "P5R0RunResultResponseV1", "run_id": task["run_id"], "status": "impasse", "disposition": "impasse", "result_seal": {"secret": "not emitted"}, "chain_digest": digest("chain")})
    calls = []
    emitted = []
    config = _config_for(
        bundle_validator=lambda: calls.append("bundle"),
        closure_validator=lambda: calls.append("closure"),
        evidence_validator=lambda value, seeded: calls.append(("evidence", value["task_id"], seeded.input_digest)),
        executor=lambda _, seeded: _seeded_result(result, seeded),
    )
    public = OneShotProductionRunner(FakeAdapter(service, _binding()), config).run(emit=emitted.append)
    assert calls[0:2] == ["bundle", "closure"]
    assert calls[2][0] == "evidence"
    assert calls[2][2].startswith("sha256:")
    assert public["status"] == "impasse"
    assert public["input_seed_digest"].startswith("sha256:")
    assert public["input_digest"].startswith("sha256:")
    assert public["timing_certified"] is True
    assert public["native_verified"] is False
    assert "secret" not in public
    assert parse_canonical(emitted[0].encode()) == public


def test_one_shot_stops_before_start_when_external_bundle_validation_fails():
    task, _ = _task_and_result()
    service = FakeService(task, {"schema": "P5R0RunResultResponseV1", "run_id": task["run_id"], "status": "impasse", "disposition": "impasse"})
    def reject():
        raise ValueError("local lock")
    runner = OneShotProductionRunner(FakeAdapter(service, _binding()), _config_for(bundle_validator=reject))
    with pytest.raises(OneShotProductionError, match="bundle/closure"):
        runner.run()
    assert service.started is False



def test_one_shot_rejects_start_commitment_mismatch_before_timing_or_callback():
    task, result = _task_and_result()
    service = FakeService(task, {"schema": "P5R0RunResultResponseV1", "run_id": task["run_id"], "status": "impasse", "disposition": "impasse"})
    original_start = service.start
    def mismatched_start(request, principal):
        started = original_start(request, principal)
        started["lock_digest"] = digest("different-lock")
        return started
    service.start = mismatched_start
    called = []
    config = _config_for(executor=lambda *_: called.append(True) or result)
    with pytest.raises(OneShotProductionError, match="start commitments"):
        OneShotProductionRunner(FakeAdapter(service, _binding()), config).run()
    assert called == []
