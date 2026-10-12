import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest, signing_digest
from services.p5_r0_evaluator.client import EvaluatorClientConfig, EvaluatorImpasse, P5EvaluatorClient
from services.p5_r0_evaluator.input_builder import deterministic_input_builder, input_builder_binding
from services.p5_r0_evaluator.production_runner import P5ProductionRunner, ProductionRunConfig, ProductionRunError, validate_production_bundle
from services.p5_r0_evaluator.time_seed import derive_time_seed, time_seed_algorithm_binding


class Response:
    def __init__(self, status, value):
        self.status = status
        self.headers = {"Content-Type": "application/json"}
        self.body = canonical_bytes(value)

    def read(self, limit):
        return self.body[:limit]


class Opener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        return self.responses.pop(0)


def _authority():
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4", "authority_id": "receipt-authority", "key_id": "receipt-key",
        "public_key": public, "public_key_digest": digest(public),
        "transport_attestation": {"schema": "P5R0AuthorityTransportV1", "provider": "provider", "audience": "https://sts.googleapis.com", "event": "attestation"},
    }
    return key, authority


def _task_response(key, authority, run_id):
    task_id = digest("task")
    task = {"schema": "P5R0WorkerTaskV3", "case_token": digest("case")}
    envelope = {
        "schema": "P5R0TaskEnvelopeV1", "run_id": run_id, "task_id": task_id, "sequence": 1,
        "task_digest": digest(task), "task": task, "issued_at_ms": 1, "expires_at_ms": 10_000,
        "authority_id": authority["authority_id"], "key_id": authority["key_id"],
        "public_key_digest": authority["public_key_digest"], "signature": "",
    }
    envelope["signature"] = b64encode(key.sign(signing_digest(envelope)))
    return {
        "schema": "P5R0NextTaskResponseV1", "run_id": run_id, "task_id": task_id, "sequence": 1,
        "phase": "primary", "case_id": "case-1", "side": "primary", "pair_id": None,
        "task_digest": digest(task), "task": task, "task_envelope": envelope,
        "authority": authority, "issued_at_ms": 1, "expires_at_ms": 10_000,
    }


def _seed_response(run_id):
    record = {
        "schema": "P5R0IndependentTimingAttestationV3", "ledger_id": "ledger", "run_id": run_id,
        "task_id": digest("seed-task"), "event": "task_issued", "sequence": 1,
        "previous_digest": None, "seed_digest": digest("seed"), "payload_digest": digest("payload"),
        "observed_at": "2026-01-01T00:00:00Z", "authority_id": "timing-authority", "key_id": "timing-key",
        "public_key": "timing-public", "public_key_digest": digest("timing-public"),
        "rfc3161_evidence_digest": digest("rfc3161"), "signature": "timing-signature",
    }
    seeded = derive_time_seed(record, run_id=run_id, namespace="production-inputs", sequence=1,
                              input_builder=deterministic_input_builder,
                              input_builder_binding=input_builder_binding(),
                              time_seed_algorithm_binding=time_seed_algorithm_binding())
    return {"schema": "P5R0TimeSeedResponseV1", "run_id": run_id, "task_id": record["task_id"],
            "timing_record": record, "timing_record_digest": seeded.timing_record_digest,
            "namespace_digest": digest("production-inputs"), "input_seed_digest": seeded.input_seed_digest,
            "input_digest": seeded.input_digest, "input_builder_binding": input_builder_binding(),
            "time_seed_algorithm_binding": time_seed_algorithm_binding()}


def _seeded_result(result, seeded):
    value = dict(result)
    evidence = dict(value["execution_evidence"])
    evidence.update({
        "schema": "P5R0ExecutionEvidenceV2", "timing_record_digest": seeded.timing_record_digest,
        "input_seed_digest": seeded.input_seed_digest, "input_digest": seeded.input_digest,
        "input_builder_implementation": seeded.input_builder_binding["implementation"],
        "input_builder_version": seeded.input_builder_binding["version"],
        "input_builder_source_digest": seeded.input_builder_binding["source_digest"],
        "time_seed_algorithm_source_digest": seeded.time_seed_algorithm_binding["source_digest"],
    })
    value["execution_evidence"] = evidence
    return value


def _client(responses, authority):
    return P5EvaluatorClient(EvaluatorClientConfig(
        endpoint="https://evaluator.example.test", authority=authority,
        token_provider=lambda: "caller-token", opener=Opener(responses),
        clock_ms=lambda: 100,
    ))


def _config(bundle_validator, executor, **changes):
    values = dict(
        lock_digest=digest("lock"), manifest_digest=digest("manifest"), worker_contract_digest=digest("worker"),
        caller_audience="https://caller.example.test", caller_subject="service-subject-123",
        idempotency_prefix="run-1", bundle_validator=bundle_validator, task_executor=executor, max_tasks=2,
    )
    values.update(changes)
    return ProductionRunConfig(**values)


def test_runner_executes_sequence_and_surfaces_impasse():
    key, authority = _authority()
    run_id = digest("run")
    task_response = _task_response(key, authority, run_id)
    result = {
        "schema": "P5R0TaskResultRequestV1", "run_id": run_id, "task_id": task_response["task_id"],
        "sequence": 1, "task_digest": task_response["task_digest"],
        "reply": {"schema": "P5R0WorkerReplyV3", "action": None},
        "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None},
        "worker_invocation": "unknown",
        "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False},
        "idempotency_key": "result-1",
    }
    responses = [
        Response(200, {"schema": "P5R0RunStartResponseV1", "run_id": run_id}),
        Response(200, _seed_response(run_id)),
        Response(200, task_response),
        Response(200, {"schema": "P5R0TaskResultResponseV2", "run_id": run_id, "task_id": task_response["task_id"], "sequence": 1, "done": True, "disposition": "impasse"}),
    ]
    calls = []
    runner = P5ProductionRunner(_client(responses, authority), _config(lambda: calls.append("bundle"), lambda _, seeded: _seeded_result(result, seeded)))
    with pytest.raises(EvaluatorImpasse):
        runner.run()
    assert calls == ["bundle"]


def test_runner_refuses_placeholder_or_missing_external_bundle():
    _, authority = _authority()
    with pytest.raises(ProductionRunError, match="real explicit"):
        P5ProductionRunner(_client([], authority), _config(lambda: None, lambda _: {} , caller_audience="aud"))
    with pytest.raises(ProductionRunError, match="bundle validator"):
        P5ProductionRunner(_client([], authority), _config(None, lambda _: {}))


def test_bundle_validator_rejects_local_readiness_lock():
    _, authority = _authority()
    bundle = {
        "authority": authority,
        "lock": {"schema": "P5R0LocalLockV3", "classification": "local_readiness_only", "non_release": True},
        "manifest": {},
        "private_store": {},
    }
    with pytest.raises(ProductionRunError, match="local/non-release"):
        validate_production_bundle(bundle)


def test_runner_requires_task_executor_to_return_exact_identity():
    key, authority = _authority()
    run_id = digest("run")
    task_response = _task_response(key, authority, run_id)
    client = _client([Response(200, {"run_id": run_id}), Response(200, _seed_response(run_id)), Response(200, task_response)], authority)
    runner = P5ProductionRunner(client, _config(lambda: None, lambda _, seeded: {"run_id": run_id, "sequence": 1}))
    with pytest.raises(ProductionRunError, match="task_id"):
        runner.run()


def test_runner_rejects_budget_exhaustion_before_claiming_success():
    key, authority = _authority()
    run_id = digest("run")
    task_response = _task_response(key, authority, run_id)
    result = {
        "schema": "P5R0TaskResultRequestV1", "run_id": run_id, "task_id": task_response["task_id"],
        "sequence": 1, "task_digest": task_response["task_digest"],
        "reply": {"schema": "P5R0WorkerReplyV3", "action": None},
        "worker_exit": {"schema": "P5R0WorkerExitV1", "code": 0, "timed_out": False, "signal": None},
        "worker_invocation": "unknown",
        "execution_evidence": {"schema": "P5R0ExecutionEvidenceV1", "closure_digest": digest("closure"), "runtime_digest": digest("runtime"), "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False},
        "idempotency_key": "result-1",
    }
    client = _client([
        Response(200, {"run_id": run_id}), Response(200, _seed_response(run_id)), Response(200, task_response),
        Response(200, {"schema": "P5R0TaskResultResponseV2", "run_id": run_id, "task_id": task_response["task_id"], "sequence": 1, "done": False, "next_sequence": 2, "disposition": "in_progress"}),
    ], authority)
    runner = P5ProductionRunner(_client(client.config.opener.responses, authority), _config(lambda: None, lambda _, seeded: _seeded_result(result, seeded), max_tasks=1))
    with pytest.raises(ProductionRunError, match="budget exhausted"):
        runner.run()