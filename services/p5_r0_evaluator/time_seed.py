"""Derive one-shot inputs only after an independently verified timing record."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
from typing import Any, Callable, Mapping

from .canonical import canonical_bytes, digest


TIME_SEED_SCHEMA = "P5R0TimeSeedV1"
TIME_SEEDED_EVIDENCE_SCHEMA = "P5R0ExecutionEvidenceV2"
TIME_SEED_IMPLEMENTATION = "services.p5_r0_evaluator.time_seed.derive_time_seed"
TIME_SEED_VERSION = "P5R0TimeSeedAlgorithmV1"
TIME_SEED_SOURCE_PATH = "services/p5_r0_evaluator/time_seed.py"


def time_seed_algorithm_binding(repository_root: Path | None = None) -> dict[str, Any]:
    root = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
    source = root / TIME_SEED_SOURCE_PATH
    if not source.is_file():
        raise ValueError("time-seed source is missing")
    source_digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    value = {"schema": "P5R0TimeSeedAlgorithmBindingV1", "implementation": TIME_SEED_IMPLEMENTATION,
             "version": TIME_SEED_VERSION, "source_path": TIME_SEED_SOURCE_PATH, "source_digest": source_digest}
    value["binding_digest"] = digest({key: child for key, child in value.items() if key != "binding_digest"})
    return value


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise ValueError(f"{name} is not a digest")
    try:
        int(value[7:], 16)
    except ValueError as exc:
        raise ValueError(f"{name} is not a digest") from exc
    return value


@dataclass(frozen=True)
class TimeSeededInput:
    timing_record_digest: str
    input_seed_digest: str
    input_digest: str
    input_value: Mapping[str, Any]
    run_id: str
    task_id: str
    sequence: int
    input_builder_binding: Mapping[str, Any] | None = None
    time_seed_algorithm_binding: Mapping[str, Any] | None = None

    def public_commitment(self) -> dict[str, Any]:
        value = {
            "schema": TIME_SEED_SCHEMA,
            "timing_record_digest": self.timing_record_digest,
            "input_seed_digest": self.input_seed_digest,
            "input_digest": self.input_digest,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "sequence": self.sequence,
        }
        if self.input_builder_binding is not None:
            value["input_builder_binding_digest"] = self.input_builder_binding.get("binding_digest")
        if self.time_seed_algorithm_binding is not None:
            value["time_seed_algorithm_source_digest"] = self.time_seed_algorithm_binding.get("source_digest")
        return value


def derive_time_seed(
    timing_record: Mapping[str, Any], *, run_id: str, namespace: str,
    sequence: int, input_builder: Callable[[str], Mapping[str, Any]],
    input_builder_binding: Mapping[str, Any] | None = None,
    time_seed_algorithm_binding: Mapping[str, Any] | None = None,
) -> TimeSeededInput:
    """Derive a deterministic input only from a verified V3 timing record.

    The timing record is assumed to have already been verified by the
    independent timing attestor. This function still requires the V3 schema and
    RFC3161 digest before deriving any input.
    """
    if not isinstance(timing_record, Mapping) or timing_record.get("schema") != "P5R0IndependentTimingAttestationV3":
        raise ValueError("time seed requires V3 timing evidence")
    _digest(timing_record.get("rfc3161_evidence_digest"), "RFC3161 evidence digest")
    _digest(timing_record.get("public_key_digest"), "timing public key digest")
    if not isinstance(timing_record.get("signature"), str) or not timing_record["signature"]:
        raise ValueError("timing signature is required")
    if not isinstance(run_id, str) or not run_id or not isinstance(namespace, str) or not namespace:
        raise ValueError("time seed identity is invalid")
    if type(sequence) is not int or sequence < 1:
        raise ValueError("time seed sequence is invalid")
    if not callable(input_builder):
        raise ValueError("time seed input builder is required")
    timing_digest = digest(dict(timing_record))
    input_seed_digest = digest({
        "schema": TIME_SEED_SCHEMA,
        "timing_record_digest": timing_digest,
        "run_id": run_id,
        "namespace": namespace,
        "sequence": sequence,
    })
    value = input_builder(input_seed_digest)
    if not isinstance(value, Mapping):
        raise ValueError("time seed input builder returned no mapping")
    input_value = dict(value)
    canonical_bytes(input_value)
    return TimeSeededInput(
        timing_record_digest=timing_digest,
        input_seed_digest=input_seed_digest,
        input_digest=digest(input_value),
        input_value=input_value,
        run_id=run_id,
        task_id=str(timing_record.get("task_id", "")),
        sequence=sequence,
        input_builder_binding=dict(input_builder_binding) if input_builder_binding is not None else None,
        time_seed_algorithm_binding=dict(time_seed_algorithm_binding) if time_seed_algorithm_binding is not None else None,
    )


def validate_time_seeded_evidence(value: Mapping[str, Any], seeded: TimeSeededInput) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("schema") != TIME_SEEDED_EVIDENCE_SCHEMA:
        raise ValueError("time-seeded execution evidence schema")
    expected = {
        "timing_record_digest": seeded.timing_record_digest,
        "input_seed_digest": seeded.input_seed_digest,
        "input_digest": seeded.input_digest,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ValueError(f"time-seeded evidence {key} mismatch")
    for key in ("closure_digest", "runtime_digest", "host_digest", "kill_digest"):
        _digest(value.get(key), key)
    if value.get("native_verified") is not False:
        raise ValueError("one-shot evidence cannot self-claim native verification")
    if seeded.input_builder_binding is not None or seeded.time_seed_algorithm_binding is not None:
        required = {
            "input_builder_implementation": seeded.input_builder_binding.get("implementation") if seeded.input_builder_binding else None,
            "input_builder_version": seeded.input_builder_binding.get("version") if seeded.input_builder_binding else None,
            "input_builder_source_digest": seeded.input_builder_binding.get("source_digest") if seeded.input_builder_binding else None,
            "time_seed_algorithm_source_digest": seeded.time_seed_algorithm_binding.get("source_digest") if seeded.time_seed_algorithm_binding else None,
        }
        for key, expected_value in required.items():
            if value.get(key) != expected_value:
                raise ValueError(f"time-seeded evidence {key} mismatch")
    return dict(value)


__all__ = ["TIME_SEED_SCHEMA", "TIME_SEEDED_EVIDENCE_SCHEMA", "TIME_SEED_IMPLEMENTATION", "TIME_SEED_VERSION", "TIME_SEED_SOURCE_PATH", "TimeSeededInput", "derive_time_seed", "time_seed_algorithm_binding", "validate_time_seeded_evidence"]
