"""Typed, fail-closed seam for worker/supervisor observations.

This module validates the shape and commitments of an observation supplied by
an execution supervisor.  It does not create observations, attest a machine,
or promote a local process observation into a trusted result.
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol

from .protocol import P5R0Error, digest, is_digest


class NativeSupervisor(Protocol):
    """Adapter boundary for a separately operated worker supervisor."""

    trusted: bool
    independent: bool

    def validate_execution_evidence(self, evidence: Mapping[str, Any]) -> bool: ...

    def validate_bounded_compute_claim(self, claim: Mapping[str, Any]) -> bool: ...


SUPERVISOR_EVIDENCE_FIELDS = frozenset({
    "schema", "run_id", "lock_digest", "closure_digest", "supervisor_digest",
    "worker_invocations", "worker_exit", "observed", "timed_out", "oom",
    "process_group_killed", "cleanup_verified", "attestation_status",
    "evidence_digest",
})


def validate_supervisor_evidence(
    value: Mapping[str, Any], *, run_id: str | None = None,
    lock_digest: str | None = None, closure_digest: str | None = None,
) -> dict[str, Any]:
    """Validate a closed supervisor-observation record without certifying it."""
    if not isinstance(value, Mapping) or set(value) != SUPERVISOR_EVIDENCE_FIELDS:
        raise P5R0Error("supervisor evidence schema")
    result = dict(value)
    if result["schema"] != "P5R0SupervisorEvidenceV1" or not is_digest(result["run_id"]):
        raise P5R0Error("supervisor evidence identity")
    for key in ("lock_digest", "closure_digest", "supervisor_digest", "evidence_digest"):
        if not is_digest(result[key]):
            raise P5R0Error("supervisor evidence commitment")
    if run_id is not None and result["run_id"] != run_id:
        raise P5R0Error("supervisor evidence run binding")
    if lock_digest is not None and result["lock_digest"] != lock_digest:
        raise P5R0Error("supervisor evidence lock binding")
    if closure_digest is not None and result["closure_digest"] != closure_digest:
        raise P5R0Error("supervisor evidence closure binding")
    if type(result["worker_invocations"]) is not int or result["worker_invocations"] < 0:
        raise P5R0Error("supervisor evidence invocation count")
    for key in ("observed", "timed_out", "oom", "process_group_killed", "cleanup_verified"):
        if type(result[key]) is not bool:
            raise P5R0Error("supervisor evidence observation")
    if result["attestation_status"] not in {"unattested_local", "verified_supervisor_observation"}:
        raise P5R0Error("unsupported supervisor evidence status")
    if result["evidence_digest"] != digest({key: result[key] for key in SUPERVISOR_EVIDENCE_FIELDS if key != "evidence_digest"}):
        raise P5R0Error("supervisor evidence digest")
    return result


__all__ = ["NativeSupervisor", "SUPERVISOR_EVIDENCE_FIELDS", "validate_supervisor_evidence"]
