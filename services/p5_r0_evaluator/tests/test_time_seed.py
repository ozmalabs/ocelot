import pytest

from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.time_seed import derive_time_seed, validate_time_seeded_evidence


def _record():
    return {
        "schema": "P5R0IndependentTimingAttestationV3",
        "run_id": digest("run"), "task_id": digest("seed-task"), "event": "task_issued",
        "sequence": 1, "previous_digest": None, "seed_digest": digest("seed"),
        "payload_digest": digest("payload"), "observed_at": "2026-01-01T00:00:00Z",
        "authority_id": "timing-authority", "key_id": "timing-key",
        "public_key": "public-key", "public_key_digest": digest("public-key"),
        "rfc3161_evidence_digest": digest("rfc3161"), "signature": "signature",
    }


def test_input_is_derived_after_timing_record_and_bound_to_seed():
    seen = []
    seeded = derive_time_seed(_record(), run_id=digest("run"), namespace="production-inputs", sequence=1, input_builder=lambda seed: seen.append(seed) or {"seed": seed})
    assert seen == [seeded.input_seed_digest]
    assert seeded.input_digest == digest(seeded.input_value)
    assert seeded.timing_record_digest == digest(_record())
    assert seeded.public_commitment()["input_digest"] == seeded.input_digest


def test_time_seed_requires_v3_rfc3161_evidence():
    record = _record()
    record["schema"] = "P5R0TimingAttestationV1"
    with pytest.raises(ValueError, match="V3"):
        derive_time_seed(record, run_id=digest("run"), namespace="inputs", sequence=1, input_builder=lambda seed: {"seed": seed})


def test_execution_evidence_cannot_bind_a_different_seed():
    seeded = derive_time_seed(_record(), run_id=digest("run"), namespace="inputs", sequence=1, input_builder=lambda seed: {"seed": seed})
    evidence = {
        "schema": "P5R0ExecutionEvidenceV2",
        "closure_digest": digest("closure"), "runtime_digest": digest("runtime"),
        "host_digest": digest("host"), "kill_digest": digest("kill"), "native_verified": False,
        "timing_record_digest": seeded.timing_record_digest,
        "input_seed_digest": digest("different-seed"), "input_digest": seeded.input_digest,
    }
    with pytest.raises(ValueError, match="input_seed_digest mismatch"):
        validate_time_seeded_evidence(evidence, seeded)
