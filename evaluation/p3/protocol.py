"""Strict canonical P3-R0 data-plane and control-plane validation."""
from __future__ import annotations
from collections.abc import Mapping, Sequence
from typing import Any
from evaluation.p0a.canonical import object_hash, verify_signature

class P3ProtocolError(ValueError):
    pass

CONTROL_PLANE_REFERENCES = frozenset({
    "broker", "broker_image", "allowlist", "grant", "grant_schema", "grant_token", "policy", "policy_authority", "policy_key", "receipt", "receipt_writer", "receipt_key", "receipt_chain", "result_format", "result_channel", "result_seal", "evaluator", "scorer", "scoring", "oracle", "statistical_seed", "benchmark", "generator", "task_generator", "task_release", "release_order", "held_out_seed", "seed_commitment", "split", "semantic_dedup", "mount", "mount_mode", "quota", "resource", "resource_budget", "budget_ledger", "heartbeat", "kill", "stop", "supervisor", "control_plane", "lock_artifact",
})
MUTABLE_KINDS = frozenset({"rule", "seed", "codebook"})
DIGEST_PREFIX = "sha256:"

def is_digest(value: Any, *, allow_zero: bool = False) -> bool:
    return isinstance(value, str) and len(value) == 71 and value.startswith(DIGEST_PREFIX) and all(c in "0123456789abcdef" for c in value[7:]) and (allow_zero or set(value[7:]) != {"0"})

def _walk(value: Any, *, path: str = ""):
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str): raise P3ProtocolError("non-string reference key")
            lower = key.lower()
            yield lower, path + "/" + key
            yield from _walk(child, path=path + "/" + key)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for i, child in enumerate(value): yield from _walk(child, path=f"{path}/{i}")
    elif isinstance(value, str):
        yield value.lower(), path

def validate_no_control_plane_reference(value: Any, *, lock_artifacts: Mapping[str, str] | None = None) -> None:
    """Reject direct, nested, or digest-based attempts to name control authority."""
    locked = set((lock_artifacts or {}).values())
    for token, _path in _walk(value):
        normalized = token.replace("-", "_").replace(" ", "_")
        if normalized in CONTROL_PLANE_REFERENCES or any(name in normalized for name in CONTROL_PLANE_REFERENCES):
            raise P3ProtocolError("control-plane reference")
        if token in locked:
            raise P3ProtocolError("control-plane artifact digest")

def _require_keys(value: Mapping[str, Any], keys: set[str], name: str) -> None:
    if set(value) != keys: raise P3ProtocolError(f"{name} schema")

def validate_learning_proposal(value: Mapping[str, Any], *, lock_artifacts: Mapping[str, str] | None = None) -> dict[str, Any]:
    if not isinstance(value, Mapping): raise P3ProtocolError("proposal object")
    required = {"schema", "proposal_digest", "parent_snapshot_digest", "mutable_artifact", "change", "provenance_refs", "evidence_refs", "rollback_snapshot_digest", "status"}
    _require_keys(value, required, "proposal")
    if value["schema"] != "LearningProposalV1" or value["status"] != "proposed": raise P3ProtocolError("proposal state")
    for name in ("proposal_digest", "parent_snapshot_digest", "rollback_snapshot_digest"):
        if not is_digest(value[name]): raise P3ProtocolError(f"proposal {name}")
    if value["proposal_digest"] != object_hash({key: val for key, val in value.items() if key != "proposal_digest"}): raise P3ProtocolError("proposal digest")
    artifact = value["mutable_artifact"]
    if not isinstance(artifact, Mapping): raise P3ProtocolError("mutable artifact")
    _require_keys(artifact, {"path", "object_digest"}, "mutable artifact")
    if not isinstance(artifact["path"], str) or not artifact["path"].startswith("mutable-agent/") or ".." in artifact["path"].split("/"):
        raise P3ProtocolError("mutable artifact path")
    if not is_digest(artifact["object_digest"]): raise P3ProtocolError("mutable artifact digest")
    change = value["change"]
    if not isinstance(change, Mapping): raise P3ProtocolError("proposal change")
    _require_keys(change, {"kind", "patch_digest"}, "proposal change")
    if change["kind"] not in MUTABLE_KINDS or not is_digest(change["patch_digest"]): raise P3ProtocolError("proposal change")
    for field in ("provenance_refs", "evidence_refs"):
        if not isinstance(value[field], list) or not value[field] or any(not is_digest(item) for item in value[field]): raise P3ProtocolError(f"proposal {field}")
    validate_no_control_plane_reference(value, lock_artifacts=lock_artifacts)
    return dict(value)

def validate_signed(value: Mapping[str, Any], *, trusted_keys: Mapping[str, Any], schema: str, key_id_field: str = "key_id") -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("schema") != schema or not isinstance(value.get(key_id_field), str): raise P3ProtocolError("signed schema")
    key = trusted_keys.get(value[key_id_field]) if isinstance(trusted_keys, Mapping) else None
    if key is None: raise P3ProtocolError("untrusted signing key")
    try: verify_signature(dict(value), key)
    except Exception as exc: raise P3ProtocolError("signature") from exc
    return dict(value)
