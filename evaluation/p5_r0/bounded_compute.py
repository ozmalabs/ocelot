"""Canonical bounded-compute evidence for local P5 native executions.

This module only constructs local, unattested evidence.  Confidential Space
verification is a separate production concern and is intentionally unavailable
here: caller metadata cannot upgrade a local record into an attestation.
"""
from __future__ import annotations

import os
import platform
from typing import Any, Mapping

from .protocol import P5R0Error, digest, is_digest

SCHEMA = "P5R0BoundedComputeEvidenceV1"
ATTESTATION_STATUSES = frozenset({"unattested_local", "verified_confidential_space"})
LOCAL_ATTESTATION_STATUS = "unattested_local"
DEADLINE_STATUSES = frozenset({"within_deadline", "over_deadline", "timeout"})
DURATION_BUCKETS = ("<100ms", "<1s", "<10s", "<100s", "timeout")

_DEFAULT_LIMITS = {
    "steps": 8,
    "frame_bytes": 65536,
    "wall_seconds": 3,
    "memory_mb": 512,
    "cpu": 1,
    "pids": 32,
}

EVIDENCE_FIELDS = frozenset({
    "schema", "algorithm_digest", "task_digest", "input_digest", "image_digest",
    "runtime_digest", "resource_profile_digest", "closure_digest",
    "run_id", "task_id", "sequence", "hardware_model", "machine_type",
    "vcpu_count", "secure_boot", "tee", "deadline_ms", "max_cpu_millis",
    "duration_bucket", "deadline_status", "result_digest", "attestation_digest",
    "attestation_status", "binding_digest",
})


def duration_bucket(duration_ms: int) -> str:
    """Return the only persisted representation of a wall interval."""
    if type(duration_ms) is not int or duration_ms < 0:
        raise P5R0Error("duration")
    if duration_ms < 100:
        return "<100ms"
    if duration_ms < 1_000:
        return "<1s"
    if duration_ms < 10_000:
        return "<10s"
    if duration_ms < 100_000:
        return "<100s"
    return "timeout"


coarse_wall_bucket = duration_bucket


def local_hardware_profile() -> dict[str, Any]:
    """Describe the host without implying that the description is attested."""
    return {
        "hardware_model": platform.processor() or "unknown",
        "machine_type": platform.machine() or "unknown",
        "vcpu_count": int(os.cpu_count() or 1),
        "secure_boot": False,
        "tee": "none",
    }


def _profile(limits: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(_DEFAULT_LIMITS)
    if limits is not None:
        value.update(dict(limits))
    if set(value) != set(_DEFAULT_LIMITS):
        raise P5R0Error("resource profile")
    for key in ("steps", "frame_bytes", "wall_seconds", "memory_mb", "cpu", "pids"):
        if type(value[key]) is not int or value[key] <= 0:
            raise P5R0Error("resource profile")
    return value


def _hardware(profile: Mapping[str, Any] | None) -> dict[str, Any]:
    value = local_hardware_profile() if profile is None else dict(profile)
    fields = {"hardware_model", "machine_type", "vcpu_count", "secure_boot", "tee"}
    if set(value) != fields:
        raise P5R0Error("hardware profile")
    if (not isinstance(value["hardware_model"], str) or not value["hardware_model"] or
            not isinstance(value["machine_type"], str) or not value["machine_type"]):
        raise P5R0Error("hardware profile")
    if type(value["vcpu_count"]) is not int or value["vcpu_count"] < 1:
        raise P5R0Error("hardware profile")
    if type(value["secure_boot"]) is not bool or value["tee"] not in {"none", "confidential_space"}:
        raise P5R0Error("hardware profile")
    return value


def _digest(value: Any, label: str) -> str:
    if not is_digest(value):
        raise P5R0Error(label)
    return value


def _algorithm_digest(entrypoint: str = "/runtime/p5_r0_worker") -> str:
    return digest({"algorithm": "P5R0NativeWorker", "entrypoint": entrypoint, "contract": SCHEMA})


def _expected(
    *, task: dict[str, Any], reply: dict[str, Any], image_digest: str,
    limits: Mapping[str, Any] | None, duration_ms: int,
    hardware_profile: Mapping[str, Any] | None = None,
    runtime_digest_value: str | None = None,
    algorithm_digest_value: str | None = None,
    closure_digest_value: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    sequence: int | None = None,
    attestation_digest: str | None = None,
    attestation_status: str = LOCAL_ATTESTATION_STATUS,
) -> dict[str, Any]:
    if not isinstance(task, dict) or not isinstance(reply, dict):
        raise P5R0Error("evidence input")
    effective = _profile(limits)
    hardware = _hardware(hardware_profile)
    _digest(image_digest, "image digest")
    if runtime_digest_value is None:
        runtime_digest_value = digest({"runtime": "crun"})
    _digest(runtime_digest_value, "runtime digest")
    if algorithm_digest_value is None:
        algorithm_digest_value = _algorithm_digest()
    _digest(algorithm_digest_value, "algorithm digest")
    if attestation_status != LOCAL_ATTESTATION_STATUS:
        raise P5R0Error("local evidence cannot claim Confidential Space verification")
    if attestation_digest is not None:
        raise P5R0Error("local evidence cannot carry attestation")
    if closure_digest_value is None:
        closure_digest_value = digest({"closure": "unbound_local"})
    _digest(closure_digest_value, "closure digest")
    for value, label in ((run_id, "run id"), (task_id, "task id")):
        if value is not None:
            _digest(value, label)
    if sequence is not None and (type(sequence) is not int or sequence < 1):
        raise P5R0Error("sequence")
    deadline_ms = effective["wall_seconds"] * 1_000
    if duration_ms > deadline_ms:
        raise P5R0Error("native execution exceeded deadline")
    result = {
        "schema": SCHEMA,
        "algorithm_digest": algorithm_digest_value,
        "task_digest": digest(task),
        "input_digest": digest(task),
        "image_digest": image_digest,
        "runtime_digest": runtime_digest_value,
        "resource_profile_digest": digest(effective),
        "closure_digest": closure_digest_value,
        "run_id": run_id,
        "task_id": task_id,
        "sequence": sequence,
        "hardware_model": hardware["hardware_model"],
        "machine_type": hardware["machine_type"],
        "vcpu_count": hardware["vcpu_count"],
        "secure_boot": hardware["secure_boot"],
        "tee": hardware["tee"],
        "deadline_ms": deadline_ms,
        "max_cpu_millis": deadline_ms * effective["cpu"],
        "duration_bucket": duration_bucket(duration_ms),
        "deadline_status": "within_deadline",
        "result_digest": digest(reply),
        "attestation_digest": None,
        "attestation_status": LOCAL_ATTESTATION_STATUS,
    }
    result["binding_digest"] = digest(result)
    return result


def recompute_bounded_compute_evidence(
    *, task: dict[str, Any], reply: dict[str, Any], image_digest: str,
    limits: Mapping[str, Any] | None = None, duration_ms: int,
    hardware_profile: Mapping[str, Any] | None = None,
    runtime_digest_value: str | None = None,
    algorithm_digest_value: str | None = None,
    closure_digest_value: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    sequence: int | None = None,
    attestation_digest: str | None = None,
    attestation_status: str = LOCAL_ATTESTATION_STATUS,
) -> dict[str, Any]:
    """Build local evidence; any attempted attestation claim fails closed."""
    return _expected(
        task=task, reply=reply, image_digest=image_digest, limits=limits,
        duration_ms=duration_ms, hardware_profile=hardware_profile,
        runtime_digest_value=runtime_digest_value,
        algorithm_digest_value=algorithm_digest_value,
        closure_digest_value=closure_digest_value, run_id=run_id,
        task_id=task_id, sequence=sequence,
        attestation_digest=attestation_digest, attestation_status=attestation_status,
    )


def validate_bounded_compute_evidence(
    value: dict[str, Any], *, task: dict[str, Any], reply: dict[str, Any],
    image_digest: str, limits: Mapping[str, Any] | None = None,
    duration_ms: int | None = None,
    hardware_profile: Mapping[str, Any] | None = None,
    runtime_digest_value: str | None = None,
    algorithm_digest_value: str | None = None,
    closure_digest_value: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    sequence: int | None = None,
    attestation_digest: str | None = None,
) -> dict[str, Any]:
    """Recompute every local binding and reject changed facts or claims."""
    if not isinstance(value, dict) or set(value) != EVIDENCE_FIELDS or value.get("schema") != SCHEMA:
        raise P5R0Error("bounded evidence schema")
    if duration_ms is None:
        raise P5R0Error("bounded evidence requires observed duration")
    expected = _expected(
        task=task, reply=reply, image_digest=image_digest, limits=limits,
        duration_ms=duration_ms, hardware_profile=hardware_profile,
        runtime_digest_value=runtime_digest_value,
        algorithm_digest_value=algorithm_digest_value,
        closure_digest_value=closure_digest_value, run_id=run_id,
        task_id=task_id, sequence=sequence, attestation_digest=attestation_digest,
        attestation_status=value.get("attestation_status"),
    )
    if value != expected:
        raise P5R0Error("bounded evidence binding mismatch")
    if value["duration_bucket"] not in DURATION_BUCKETS or value["deadline_status"] not in DEADLINE_STATUSES:
        raise P5R0Error("bounded evidence bucket/status")
    if value["deadline_status"] != "within_deadline":
        raise P5R0Error("bounded evidence deadline")
    if value["binding_digest"] != digest({key: value[key] for key in value if key != "binding_digest"}):
        raise P5R0Error("bounded evidence binding digest")
    return dict(value)


def bounded_compute_evidence_digest(value: Mapping[str, Any]) -> str:
    """Return a validated digest suitable for records and receipt bindings."""
    if not isinstance(value, dict) or set(value) != EVIDENCE_FIELDS or value.get("schema") != SCHEMA:
        raise P5R0Error("bounded evidence schema")
    if value.get("binding_digest") != digest({key: value[key] for key in value if key != "binding_digest"}):
        raise P5R0Error("bounded evidence binding digest")
    if value.get("attestation_status") != LOCAL_ATTESTATION_STATUS:
        raise P5R0Error("local evidence cannot claim Confidential Space verification")
    for key in ("algorithm_digest", "task_digest", "input_digest", "image_digest", "runtime_digest", "resource_profile_digest", "closure_digest", "result_digest"):
        _digest(value.get(key), key)
    for key in ("run_id", "task_id"):
        if value.get(key) is not None:
            _digest(value.get(key), key)
    if value.get("sequence") is not None and (type(value["sequence"]) is not int or value["sequence"] < 1):
        raise P5R0Error("sequence")
    if value.get("attestation_digest") is not None:
        raise P5R0Error("local evidence cannot carry attestation")
    if value.get("duration_bucket") not in DURATION_BUCKETS or value.get("deadline_status") != "within_deadline":
        raise P5R0Error("bounded evidence deadline")
    return digest(value)


def recompute_confidential_space_evidence(**_: Any) -> dict[str, Any]:
    """Reserved production hook; local code must never manufacture attestation."""
    raise P5R0Error("Confidential Space evidence is unavailable in local construction")


def attach_bounded_compute_evidence(
    record: Mapping[str, Any], receipt_binding: Mapping[str, Any], evidence: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Attach only the canonical evidence digest, never raw timing."""
    evidence_digest = bounded_compute_evidence_digest(evidence)
    updated_record = dict(record)
    updated_binding = dict(receipt_binding)
    updated_record["bounded_compute_evidence_digest"] = evidence_digest
    updated_binding["bounded_compute_evidence_digest"] = evidence_digest
    return updated_record, updated_binding
