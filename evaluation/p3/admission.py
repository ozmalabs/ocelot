"""Fail-closed P3 candidate admission and rollback operations."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import object_hash, parse_canonical, sha256
from .attestations import local_attestation_digest, validate_local_phase_go
from .lock import P3ReleaseLockV1
from .protocol import P3ProtocolError, validate_learning_proposal, validate_no_control_plane_reference
from .receipts import P3ReceiptLog, receipt_payload

@dataclass(frozen=True)
class P3ReadinessRequestV1:
    p0_go: Mapping[str, Any]
    p1_go: Mapping[str, Any]
    p2_go: Mapping[str, Any]
    native_export_digest: str
    candidate_digest: str
    pre_snapshot: Path
    candidate: Path
    stage: Path

@dataclass(frozen=True)
class StagedCandidateV1:
    path: Path
    candidate_digest: str
    pre_snapshot_digest: str
    proposal_digest: str


def _read_regular(path: Path, label: str) -> bytes:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise P3ProtocolError(f"{label} unavailable")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            return os.read(fd, os.fstat(fd).st_size)
        finally:
            os.close(fd)
    except OSError as exc:
        raise P3ProtocolError(f"{label} unavailable") from exc

def _digest(path: Path, label: str = "snapshot") -> str:
    return sha256(_read_regular(path, label))

def _bindings(lock: P3ReleaseLockV1) -> dict[str, str]:
    return {key: lock.body[key] for key in ("p0_go_digest", "p1_go_digest", "p2_go_digest",
                                             "native_export_digest", "candidate_digest", "pre_snapshot_digest")}

def verify_preflight(request: P3ReadinessRequestV1, lock: P3ReleaseLockV1, *,
                     trusted_p0_keys: Mapping[str, Any], trusted_p1_keys: Mapping[str, Any],
                     trusted_p2_keys: Mapping[str, Any]) -> None:
    """Verify every signed prerequisite and every immutable byte binding."""
    for phase, artifact, keys in (("p0", request.p0_go, trusted_p0_keys),
                                  ("p1", request.p1_go, trusted_p1_keys),
                                  ("p2", request.p2_go, trusted_p2_keys)):
        signed = validate_local_phase_go(artifact, phase=phase, trusted_keys=keys)
        if local_attestation_digest(signed) != lock.body[f"{phase}_go_digest"]:
            raise P3ProtocolError(f"{phase} go binding")
    if request.native_export_digest != lock.body["native_export_digest"]:
        raise P3ProtocolError("native export binding")
    if request.candidate_digest != lock.body["candidate_digest"]:
        raise P3ProtocolError("candidate request binding")
    if _digest(request.pre_snapshot, "pre snapshot") != lock.body["pre_snapshot_digest"]:
        raise P3ProtocolError("pre snapshot binding")
    if _digest(request.candidate, "candidate") != lock.body["candidate_digest"]:
        raise P3ProtocolError("candidate byte binding")

def validate_staged_proposal(proposal: Mapping[str, Any], lock: P3ReleaseLockV1) -> dict[str, Any]:
    parsed = validate_learning_proposal(proposal, lock_artifacts=lock.artifacts)
    if (parsed["parent_snapshot_digest"] != lock.body["pre_snapshot_digest"]
            or parsed["rollback_snapshot_digest"] != lock.body["pre_snapshot_digest"]
            or parsed["mutable_artifact"]["object_digest"] != lock.body["candidate_digest"]):
        raise P3ProtocolError("proposal snapshot binding")
    return parsed

def stage_isolated_candidate(*, pre_snapshot: Path, candidate: Path, stage: Path,
                             expected_candidate_digest: str) -> Path:
    """Copy only a verified regular candidate to a new evaluator-owned directory."""
    if _digest(pre_snapshot, "pre snapshot") == "":  # Defensive: also rejects absent/symlink files.
        raise P3ProtocolError("snapshot unavailable")
    candidate_bytes = _read_regular(candidate, "candidate")
    if sha256(candidate_bytes) != expected_candidate_digest:
        raise P3ProtocolError("candidate stage binding")
    stage = Path(stage)
    if stage.exists() or stage.is_symlink() or stage.parent.is_symlink():
        raise P3ProtocolError("candidate stage")
    try:
        stage.mkdir(mode=0o700, parents=True, exist_ok=False)
        staged = stage / "candidate.bin"
        fd = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        try:
            os.write(fd, candidate_bytes); os.fsync(fd)
        finally:
            os.close(fd)
        staged.chmod(0o444)
        # The fixed rootless worker may read this one immutable candidate, but
        # cannot traverse any writable evaluator directory or modify the file.
        stage.chmod(0o555)
    except OSError as exc:
        raise P3ProtocolError("candidate stage") from exc
    if _digest(staged, "staged candidate") != expected_candidate_digest:
        raise P3ProtocolError("candidate stage mismatch")
    return staged

def validate_candidate_payload(candidate: Path, lock: P3ReleaseLockV1) -> dict[str, Any]:
    """Accept only canonical mutable data, then inspect every direct/transitive reference."""
    try:
        payload = parse_canonical(_read_regular(candidate, "candidate"))
    except Exception as exc:
        raise P3ProtocolError("candidate payload") from exc
    if payload.get("schema") != "P3MutableCandidateV1":
        raise P3ProtocolError("candidate payload schema")
    validate_no_control_plane_reference(payload, lock_artifacts=lock.artifacts)
    return payload

def validate_and_stage(*, request: P3ReadinessRequestV1, proposal: Mapping[str, Any],
                       lock: P3ReleaseLockV1) -> StagedCandidateV1:
    parsed = validate_staged_proposal(proposal, lock)
    validate_candidate_payload(request.candidate, lock)
    path = stage_isolated_candidate(pre_snapshot=request.pre_snapshot, candidate=request.candidate,
                                    stage=request.stage, expected_candidate_digest=lock.body["candidate_digest"])
    return StagedCandidateV1(path, lock.body["candidate_digest"], lock.body["pre_snapshot_digest"],
                             parsed["proposal_digest"])

def reject_and_rollback(*, candidate: Path, pre_snapshot: Path, receipt_log: P3ReceiptLog,
                        lock: P3ReleaseLockV1, proposal_digest: str | None, reason: str) -> dict[str, Any]:
    source = _read_regular(pre_snapshot, "pre snapshot")
    candidate = Path(candidate)
    if candidate.is_symlink() or not candidate.is_file():
        raise P3ProtocolError("candidate unavailable")
    try:
        fd = os.open(candidate, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
        try:
            os.write(fd, source); os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise P3ProtocolError("rollback write") from exc
    after = _digest(candidate, "candidate")
    if after != sha256(source): raise P3ProtocolError("rollback mismatch")
    payload = receipt_payload(lock_digest=lock.digest, proposal_digest=proposal_digest, outcome="rejected",
                              reason=reason, control_digests=lock.artifacts, snapshot_digest=after,
                              release_bindings=_bindings(lock))
    return receipt_log.append("rollback", payload)

def denial_payload(*, lock: P3ReleaseLockV1, proposal: Mapping[str, Any] | None, reason: str) -> dict[str, Any]:
    digest = proposal.get("proposal_digest") if isinstance(proposal, Mapping) else None
    return receipt_payload(lock_digest=lock.digest, proposal_digest=digest, outcome="no_go", reason=reason,
                           control_digests=lock.artifacts, release_bindings=_bindings(lock))

def deny_before_evaluation(*, receipt_log: P3ReceiptLog | None, lock: P3ReleaseLockV1 | None,
                           reason: str, proposal: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if receipt_log is None or lock is None:
        return {"outcome":"impasse", "reason":reason, "worker_launch":False}
    return receipt_log.append("denial", denial_payload(lock=lock, proposal=proposal, reason=reason))



def terminal_rollback_impasse(*, candidate: Path, pre_snapshot: Path, receipt_log: P3ReceiptLog,
                              lock: P3ReleaseLockV1, proposal_digest: str | None, cause: Exception) -> dict[str, Any]:
    """Record a signed terminal impasse when byte-exact rollback cannot be proven.

    This intentionally does not retry, downgrade, or claim a completed no-go.
    The receipt chain signature is the evaluator-authority signature over the
    bounded failure evidence and expected snapshot binding.
    """
    expected = lock.body["pre_snapshot_digest"]
    observed: str | None = None
    try:
        observed = _digest(candidate, "candidate")
    except Exception:
        # Never follow a hostile replacement simply to improve diagnostics.
        observed = None
    evidence = {"schema": "P3RollbackImpasseEvidenceV1", "lock_digest": lock.digest,
                "proposal_digest": proposal_digest, "expected_pre_snapshot_digest": expected,
                "observed_candidate_digest": observed, "failure_class": type(cause).__name__}
    evidence["evidence_digest"] = object_hash(evidence)
    payload = receipt_payload(lock_digest=lock.digest, proposal_digest=proposal_digest, outcome="impasse",
                              reason="rollback_restore_or_verification_failed", control_digests=lock.artifacts,
                              snapshot_digest=observed, release_bindings=_bindings(lock))
    payload["terminal_evidence"] = evidence
    return receipt_log.append("impasse", payload)
