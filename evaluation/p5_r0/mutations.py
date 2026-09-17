from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from evaluation.p0a.canonical import b64decode, b64encode, canonical_bytes, object_hash, parse_canonical, sign, verify_signature
from .protocol import P5R0Error, digest, is_digest
from .receipts import ReceiptChain

MUTATION_FIELDS = {
    "schema", "run_id", "mutation_id", "mutation_kind", "target", "ordinal",
    "lock_digest", "task_digest", "pre_state_digest", "proposed_state_digest",
    "post_state_digest", "write_set_digest", "expected_effect_digest",
    "observed_effect_digest", "outcome", "changed", "rollback_exact",
    "receipt_hash", "signer_key_id", "signer_public_key_digest", "result_digest",
    "signature",
}
MUTATION_KINDS = {"preflight", "reset", "adoption", "rollback"}
MUTATION_OUTCOMES = {"applied", "rejected", "rolled_back", "impasse"}
MUTATION_TARGETS = {"manifest", "private_store", "cold_reset", "frozen_reset", "warm_session_namespace", "rollback"}


def _validate_result_shape(result: dict[str, Any]) -> None:
    if not isinstance(result, dict) or set(result) != MUTATION_FIELDS or result.get("schema") != "P5R0MutationResultV1":
        raise P5R0Error("mutation result schema")
    for key in ("run_id", "mutation_id", "lock_digest", "pre_state_digest", "post_state_digest", "write_set_digest", "expected_effect_digest", "observed_effect_digest", "receipt_hash", "signer_public_key_digest", "result_digest"):
        if not is_digest(result.get(key)):
            raise P5R0Error(f"mutation digest: {key}")
    if result.get("task_digest") is not None and not is_digest(result["task_digest"]):
        raise P5R0Error("mutation task digest")
    if result.get("proposed_state_digest") is not None and not is_digest(result["proposed_state_digest"]):
        raise P5R0Error("mutation proposed digest")
    if result.get("mutation_kind") not in MUTATION_KINDS or result.get("outcome") not in MUTATION_OUTCOMES or result.get("target") not in MUTATION_TARGETS:
        raise P5R0Error("mutation identity")
    if type(result.get("ordinal")) is not int or result["ordinal"] < 0 or type(result.get("changed")) is not bool or type(result.get("rollback_exact")) is not bool:
        raise P5R0Error("mutation flags")
    if result["changed"] != (result["pre_state_digest"] != result["post_state_digest"]):
        raise P5R0Error("mutation changed flag")
    if result["outcome"] in {"rejected", "impasse"} and result["rollback_exact"] is not True:
        raise P5R0Error("mutation rollback")


def build_mutation_result(*, run_id: str, mutation_id: str | None = None, mutation_kind: str, target: str, ordinal: int, lock_digest: str, task_digest: str | None, pre_state_digest: str, proposed_state_digest: str | None, post_state_digest: str, write_set_digest: str, expected_effect_digest: str, observed_effect_digest: str, outcome: str, rollback_exact: bool, receipt_hash: str, signer_key_id: str, signer_public_key_digest: str) -> dict[str, Any]:
    mutation_id = mutation_id or digest({"run_id": run_id, "kind": mutation_kind, "target": target, "ordinal": ordinal, "pre": pre_state_digest, "task": task_digest})
    result = {"schema": "P5R0MutationResultV1", "run_id": run_id, "mutation_id": mutation_id, "mutation_kind": mutation_kind, "target": target, "ordinal": ordinal, "lock_digest": lock_digest, "task_digest": task_digest, "pre_state_digest": pre_state_digest, "proposed_state_digest": proposed_state_digest, "post_state_digest": post_state_digest, "write_set_digest": write_set_digest, "expected_effect_digest": expected_effect_digest, "observed_effect_digest": observed_effect_digest, "outcome": outcome, "changed": pre_state_digest != post_state_digest, "rollback_exact": rollback_exact, "receipt_hash": receipt_hash, "signer_key_id": signer_key_id, "signer_public_key_digest": signer_public_key_digest, "result_digest": "", "signature": ""}
    result["result_digest"] = object_hash(result, "result_digest", "signature")
    return result


def write_mutation_artifact(result: dict[str, Any], out: Path, signer: Any) -> dict[str, Any]:
    _validate_result_shape(result)
    if result["result_digest"] != object_hash(result, "result_digest", "signature"):
        raise P5R0Error("mutation result digest")
    if result["signer_public_key_digest"] != digest(b64encode(signer.public_key().public_bytes_raw())):
        raise P5R0Error("mutation signer binding")
    result = dict(result)
    result["signature"] = sign(result, signer, "result_digest")
    target = Path(out); target.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        try:
            os.write(fd, canonical_bytes(result)); os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise P5R0Error("mutation artifact persistence") from exc
    return result


def record_mutation(*, chain: ReceiptChain, artifact_root: Path, run_id: str, lock_digest: str, mutation_kind: str, target: str, ordinal: int, task_digest: str | None, pre_state_digest: str, proposed_state_digest: str | None, post_state_digest: str, write_set_digest: str, expected_effect_digest: str, observed_effect_digest: str, outcome: str, rollback_exact: bool) -> dict[str, Any]:
    if chain.protocol != "V3" or chain.signer is None:
        raise P5R0Error("V3 mutation chain required")
    receipt_link = digest({"run_id": run_id, "kind": "mutation", "mutation_kind": mutation_kind, "target": target, "ordinal": ordinal, "pre": pre_state_digest, "post": post_state_digest, "write_set": write_set_digest})
    result = build_mutation_result(run_id=run_id, mutation_kind=mutation_kind, target=target, ordinal=ordinal, lock_digest=lock_digest, task_digest=task_digest, pre_state_digest=pre_state_digest, proposed_state_digest=proposed_state_digest, post_state_digest=post_state_digest, write_set_digest=write_set_digest, expected_effect_digest=expected_effect_digest, observed_effect_digest=observed_effect_digest, outcome=outcome, rollback_exact=rollback_exact, receipt_hash=receipt_link, signer_key_id=chain.key_id, signer_public_key_digest=chain.public_key_digest)
    artifact = write_mutation_artifact(result, Path(artifact_root) / f"{result['mutation_id']}.json", chain.signer)
    receipt = chain.append(run_id=run_id, kind="mutation", outcome="verified" if outcome == "applied" else "containment_failure", binding={"mutation_id": result["mutation_id"], "mutation_kind": mutation_kind, "target": target, "ordinal": ordinal, "lock_digest": lock_digest, "receipt_hash": receipt_link, "artifact_digest": result["result_digest"], "pre_state_digest": pre_state_digest, "post_state_digest": post_state_digest, "write_set_digest": write_set_digest, "rollback_exact": rollback_exact})
    return {"artifact": artifact, "artifact_path": str(Path(artifact_root) / f"{result['mutation_id']}.json"), "receipt": receipt}


def record_rejected_reset(*, chain: ReceiptChain, artifact_root: Path, run_id: str, lock_digest: str, ordinal: int, task_digest: str | None, pre_state_digest: str, proposed_session_id: str, rollback_exact: bool = True) -> dict[str, Any]:
    """Receipt-bind a rejected warm-reset mutation before native execution."""
    proposed = digest({"session_id": proposed_session_id, "mutation": "warm_reset"})
    return record_mutation(
        chain=chain,
        artifact_root=artifact_root,
        run_id=run_id,
        lock_digest=lock_digest,
        mutation_kind="reset",
        target="warm_session_namespace",
        ordinal=ordinal,
        task_digest=task_digest,
        pre_state_digest=pre_state_digest,
        proposed_state_digest=proposed,
        post_state_digest=pre_state_digest,
        write_set_digest=digest({}),
        expected_effect_digest=digest({"accepted": False}),
        observed_effect_digest=digest({"accepted": False, "reason": "warm reset session identity mismatch"}),
        outcome="rejected",
        rollback_exact=rollback_exact,
    )


def verify_mutation_artifact(path: Path, public_key: Ed25519PublicKey, *, expected_receipt_hash: str | None = None) -> dict[str, Any]:
    try: result = parse_canonical(Path(path).read_bytes())
    except Exception as exc: raise P5R0Error("mutation artifact canonical") from exc
    _validate_result_shape(result)
    if result["result_digest"] != object_hash(result, "result_digest", "signature") or result["signer_public_key_digest"] != digest(b64encode(public_key.public_bytes_raw())):
        raise P5R0Error("mutation artifact digest")
    if expected_receipt_hash is not None and result["receipt_hash"] != expected_receipt_hash:
        raise P5R0Error("mutation receipt binding")
    try: verify_signature(result, public_key, "result_digest")
    except Exception as exc: raise P5R0Error("mutation artifact signature") from exc
    return result
