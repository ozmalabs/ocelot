from __future__ import annotations

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluation.p0a.canonical import canonical_bytes, object_hash, sha256, sign
from evaluation.p3.attestations import local_attestation_digest
from evaluation.p3.lock import ARTIFACT_NAMES, make_release_lock, validate_lock


def digest(char: str) -> str:
    return "sha256:" + char * 64


def local_go(phase: str, key: Ed25519PrivateKey, evidence: str) -> dict:
    body = {"schema": f"{phase.upper()}PhaseGoAttestationV1", "phase": phase, "decision": "go",
            "custody": "local-test", "evidence_digest": evidence, "key_id": f"{phase}-local", "signature": ""}
    body["signature"] = sign(body, key)
    return body


def mutable_candidate(extra: dict | None = None) -> bytes:
    payload = {"schema": "P3MutableCandidateV1", "rules": []}
    if extra:
        payload.update(extra)
    return canonical_bytes(payload)


def proposal(*, candidate_digest: str, pre_digest: str) -> dict:
    value = {"schema": "LearningProposalV1", "parent_snapshot_digest": pre_digest,
             "mutable_artifact": {"path": "mutable-agent/rules.json", "object_digest": candidate_digest},
             "change": {"kind": "rule", "patch_digest": digest("a")}, "provenance_refs": [digest("b")],
             "evidence_refs": [digest("c")], "rollback_snapshot_digest": pre_digest, "status": "proposed"}
    value["proposal_digest"] = object_hash(value)
    return value


def ready(tmp_path: Path, *, candidate_bytes: bytes | None = None):
    lock_key = Ed25519PrivateKey.generate(); p0_key = Ed25519PrivateKey.generate()
    p1_key = Ed25519PrivateKey.generate(); p2_key = Ed25519PrivateKey.generate()
    p0, p1, p2 = (local_go("p0", p0_key, digest("1")), local_go("p1", p1_key, digest("2")),
                  local_go("p2", p2_key, digest("3")))
    pre = tmp_path / "pre"; candidate = tmp_path / "candidate"; pre.write_bytes(canonical_bytes({"baseline": True}))
    candidate.write_bytes(candidate_bytes or mutable_candidate())
    lock = validate_lock(make_release_lock(signing_key=lock_key, key_id="lock-local",
        p0_go_digest=local_attestation_digest(p0), p1_go_digest=local_attestation_digest(p1),
        p2_go_digest=local_attestation_digest(p2), artifacts={name: digest(f"{(i % 9) + 1:x}") for i, name in enumerate(ARTIFACT_NAMES)},
        candidate_digest=sha256(candidate.read_bytes()), pre_snapshot_digest=sha256(pre.read_bytes()),
        native_export_digest=digest("d")), {"lock-local": lock_key.public_key()})
    return {"lock_key": lock_key, "lock": lock, "p0": p0, "p1": p1, "p2": p2, "p0_key": p0_key,
            "p1_key": p1_key, "p2_key": p2_key, "pre": pre, "candidate": candidate,
            "proposal": proposal(candidate_digest=lock.body["candidate_digest"], pre_digest=lock.body["pre_snapshot_digest"])}
