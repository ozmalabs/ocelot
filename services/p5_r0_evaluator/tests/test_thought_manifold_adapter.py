from __future__ import annotations

import json
import pytest

from services.p5_r0_evaluator.canonical import canonical_bytes, digest, parse_canonical
from services.p5_r0_evaluator.one_shot import OneShotConfig, OneShotProductionError, OneShotProductionRunner
from services.p5_r0_evaluator.tests.test_client import _authority, _task_response
from services.p5_r0_evaluator.tests.test_one_shot import FakeAdapter, FakeService, _binding
from services.p5_r0_evaluator.thought_manifold_adapter import (
    CANONICAL_SEED_TOPICS,
    THOUGHT_MANIFOLD_INPUT_SCHEMA,
    build_knowledge_substrate,
    create_thought_manifold_one_shot_config,
    thought_manifold_evidence_validator,
    thought_manifold_input_builder,
    thought_manifold_task_executor,
)
from services.p5_r0_evaluator.time_seed import derive_time_seed


def _fake_timing_record(task_id: str | None = None) -> dict:
    tid = task_id or digest("task-0")
    return {
        "schema": "P5R0IndependentTimingAttestationV3",
        "ledger_id": "timing-ledger",
        "run_id": digest("run-1"),
        "task_id": tid,
        "event": "task_issued",
        "sequence": 1,
        "previous_digest": None,
        "seed_digest": digest({"timing": tid}),
        "payload_digest": digest("payload"),
        "observed_at": "2026-09-20T23:50:00Z",
        "authority_id": "timing-authority",
        "key_id": "timing-key",
        "public_key": "timing-public",
        "public_key_digest": digest("timing-public"),
        "rfc3161_evidence_digest": digest({"rfc3161": tid}),
        "signature": "timing-signature",
    }


def test_input_builder_deterministic():
    seed1 = digest("seed-1234")
    inp1 = thought_manifold_input_builder(seed1)
    inp1_again = thought_manifold_input_builder(seed1)

    assert inp1 == inp1_again
    assert inp1["schema"] == THOUGHT_MANIFOLD_INPUT_SCHEMA
    assert inp1["start_topic"] in CANONICAL_SEED_TOPICS
    assert inp1["target_topic"] in CANONICAL_SEED_TOPICS
    assert inp1["initial_width"] in (0, 1, 2, 3)
    assert inp1["tube_mode"] in ("focus", "steer", "evade", "tunnel")
    assert len(inp1["tube_region"]) >= 1
    assert inp1["combinatorial_entropy_bits"] > 100

    # Different seed yields deterministic variation
    seed2 = digest("seed-5678")
    inp2 = thought_manifold_input_builder(seed2)
    assert inp1 != inp2


def test_thought_manifold_task_executor_runs_and_redacts():
    timing = _fake_timing_record()
    seeded = derive_time_seed(
        timing,
        run_id=digest("run-1"),
        namespace="thought-manifold-trajectory",
        sequence=1,
        input_builder=thought_manifold_input_builder,
    )

    task_response = {
        "run_id": digest("run-1"),
        "task_id": digest("task-1"),
        "sequence": 1,
        "task_digest": digest("task"),
    }

    result = thought_manifold_task_executor(task_response, seeded)

    assert result["schema"] == "P5R0TaskResultRequestV1"
    assert result["run_id"] == digest("run-1")
    assert result["task_id"] == digest("task-1")
    assert result["worker_invocation"] == "native"
    assert "summary_digest" in result

    # Evidence bindings
    evidence = result["execution_evidence"]
    assert evidence["schema"] == "P5R0ExecutionEvidenceV2"
    assert evidence["timing_record_digest"] == seeded.timing_record_digest
    assert evidence["input_seed_digest"] == seeded.input_seed_digest
    assert evidence["input_digest"] == seeded.input_digest

    # Verify zero-disclosure: none of the concept names appear as raw strings in result
    thought_manifold_evidence_validator(result, seeded)


def test_zero_disclosure_gate_rejects_leakage():
    timing = _fake_timing_record()
    seeded = derive_time_seed(
        timing,
        run_id=digest("run-1"),
        namespace="thought-manifold-trajectory",
        sequence=1,
        input_builder=thought_manifold_input_builder,
    )

    task_response = {
        "run_id": digest("run-1"),
        "task_id": digest("task-1"),
        "sequence": 1,
    }

    result = thought_manifold_task_executor(task_response, seeded)
    # Deliberately leak a concept node name into result
    result["leaked_concept"] = "poodle"

    with pytest.raises(OneShotProductionError, match="zero-disclosure violation"):
        thought_manifold_evidence_validator(result, seeded)


def test_end_to_end_one_shot_attestation():
    key, authority = _authority()
    run_id = digest("run-manifold")
    task = _task_response(key, authority, run_id=run_id)

    service = FakeService(
        task,
        {
            "schema": "P5R0RunResultResponseV1",
            "run_id": run_id,
            "status": "impasse",
            "disposition": "impasse",
            "result_seal": {"sealed_proof": "zk-proof-record"},
            "chain_digest": digest("chain"),
        },
    )

    config = create_thought_manifold_one_shot_config(
        lock_digest=digest("lock"),
        manifest_digest=digest("manifest"),
        worker_contract_digest=digest("worker"),
        principal_subject="thought-manifold-attestor",
        max_tasks=1,
    )

    emitted = []
    runner = OneShotProductionRunner(FakeAdapter(service, _binding()), config)
    public = runner.run(emit=emitted.append)

    assert public["schema"] == "P5R0OneShotResultV1"
    assert public["status"] == "impasse"
    assert public["timing_certified"] is True
    assert public["native_verified"] is False
    assert public["input_seed_digest"].startswith("sha256:")
    assert public["input_digest"].startswith("sha256:")
    assert public["time_seed_timing_record_digest"].startswith("sha256:")
    assert public["result_seal_digest"].startswith("sha256:")

    # Confirm emission
    assert len(emitted) == 1
    raw_public = emitted[0]
    for topic in CANONICAL_SEED_TOPICS:
        assert topic not in raw_public


def test_tampered_time_seed_rejected():
    key, authority = _authority()
    run_id = digest("run-manifold-tamper")
    task = _task_response(key, authority, run_id=run_id)

    service = FakeService(
        task,
        {
            "schema": "P5R0RunResultResponseV1",
            "run_id": run_id,
            "status": "impasse",
            "disposition": "impasse",
            "result_seal": {"sealed_proof": "zk-proof-record"},
            "chain_digest": digest("chain"),
        },
    )

    # Tampered executor that attempts to use a forged input_seed_digest in evidence
    def tampered_executor(task_response, seeded):
        res = thought_manifold_task_executor(task_response, seeded)
        res["execution_evidence"]["input_seed_digest"] = digest("forged-seed")
        return res

    config = create_thought_manifold_one_shot_config(
        lock_digest=digest("lock"),
        manifest_digest=digest("manifest"),
        worker_contract_digest=digest("worker"),
        principal_subject="thought-manifold-attestor",
        max_tasks=1,
    )
    # Replace executor with tampered version
    config = OneShotConfig(
        lock_digest=config.lock_digest,
        manifest_digest=config.manifest_digest,
        worker_contract_digest=config.worker_contract_digest,
        principal_subject=config.principal_subject,
        input_namespace=config.input_namespace,
        input_builder=config.input_builder,
        bundle_validator=config.bundle_validator,
        closure_validator=config.closure_validator,
        evidence_validator=config.evidence_validator,
        task_executor=tampered_executor,
        authorized_task_validator=config.authorized_task_validator,
        max_tasks=config.max_tasks,
    )

    runner = OneShotProductionRunner(FakeAdapter(service, _binding()), config)
    with pytest.raises(OneShotProductionError, match="evidence validation failed"):
        runner.run()
