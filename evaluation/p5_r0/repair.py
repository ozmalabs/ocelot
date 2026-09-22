"""Versioned P5-R0 repair contract.

V3 is intentionally separate from the V2 ledger.  It binds the V2 parent,
keeps the old workload commitments visible, and refuses native execution until
a separately supplied authority trust binding and a V3 worker closure are present.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from evaluation.p0a.canonical import b64decode, b64encode, canonical_bytes, object_hash, parse_canonical, sign, verify_signature
from .domain_cards import authority_from_private
from .fixture_generator import build_private_manifest
from .native import V3_HOST_CLOSURE_KEYS
from .protocol import P5R0Error, digest, is_digest
from .receipts import ReceiptChain
from .rollback import Snapshot, rollback_receipt

V3_SCHEMA = "P5R0LocalLockV3"
V3_FEATURE_ID = "p5-r0-local-transfer-gate-v3-repair"
V3_PARENT_LOCK_DIGEST = "sha256:43c1f1e7d64b6a9be16bb77f086483811b8e4c6a13671b8372b0600b56c033a4"
V3_CONTROL_IDS = ["exact_memorization", "template_memorization", "label_permutation", "mechanics_permutation", "altered_semantics", "illegal_action", "resource_exhaustion", "safety_control", "leakage_audit", "containment_audit", "negative_transfer"]


def repair_policy(*, case_count: int = 48, contrast_matrix: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if case_count != 48: raise P5R0Error("V3 workload cardinality")
    return {"schema": "P5R0GatePolicyV3", "expected_primary_records": 144, "expected_cases": 48, "expected_arms": 3, "minimum_held_out": 36, "required_control_ids": list(V3_CONTROL_IDS), "contrast_matrix": contrast_matrix or [], "native_required": True, "external_authority_required": True, "native_controls_required": True, "mechanics_contrast_required": True, "host_evidence_required": True, "session_state_required": True, "episode_boundary_required": True, "persistent_namespace_required": True, "safeguards": {"schema": "P5R0SafeguardPolicyV3", "confidence_milli_min": 900, "source_splits": ["train", "development"], "held_out_adoption": False, "cross_domain_reads": False, "cross_domain_writes": False, "max_adoptions_per_case": 1, "max_adoptions_per_domain": 4, "rollback_on_invalid": True, "low_confidence": "non_adoption", "malformed": "protocol_failure"}, "max_safety_violations": 0, "max_resource_exhaustions": 0, "max_leakage": 0, "max_rollback_impasses": 0}


def _authority_check(authority: dict[str, Any]) -> None:
    if not isinstance(authority, dict) or authority.get("schema") != "P5R0AuthorityV2" or not authority.get("authority_id") or not authority.get("key_id") or authority.get("public_key_digest") != digest(authority.get("public_key")):
        raise P5R0Error("V3 authority trust binding")
    try: Ed25519PublicKey.from_public_bytes(b64decode(authority["public_key"]))
    except Exception as exc: raise P5R0Error("V3 authority key") from exc
    if authority.get("authority_id", "").startswith("p5-r0-local") or authority.get("transport_attestation") is None:
        raise P5R0Error("V3 authority trust binding required")


def preregister_repair(out: Path, *, parent_lock: dict[str, Any], signer: Ed25519PrivateKey | None = None, trusted_authority: dict[str, Any] | None = None, parent_lock_path: Path | None = None, parent_authority: dict[str, Any] | None = None, closure: dict[str, Any] | None = None, bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    """Write a new V3 lock; never mutate or reuse the V2 lock/receipt directory."""
    target = Path(out)
    if target.exists(): raise P5R0Error("V3 output already exists")
    if parent_lock_path is not None:
        parent_path = Path(parent_lock_path)
        if target.resolve() == parent_path.resolve(): raise P5R0Error("V3 output overlaps V2 parent")
        try: loaded_parent = parse_canonical(parent_path.read_bytes())
        except Exception as exc: raise P5R0Error("V2 parent canonical") from exc
        if loaded_parent != parent_lock: raise P5R0Error("V2 parent mismatch")
        if parent_authority is not None:
            from .preregister import validate_lock
            validate_lock(loaded_parent, trusted_authority=parent_authority)
    if parent_lock.get("schema") is not None and parent_lock.get("schema") != "P5R0LocalLockV2": raise P5R0Error("unexpected V2 parent schema")
    if parent_lock.get("schema") == "P5R0LocalLockV2":
        from .preregister import validate_lock
        parent_trust = parent_authority or trusted_authority
        if parent_trust is None: raise P5R0Error("verified V2 parent authority required")
        validate_lock(parent_lock, trusted_authority=parent_trust)
    if parent_lock.get("lock_digest") != V3_PARENT_LOCK_DIGEST: raise P5R0Error("unexpected V2 parent lock")
    signer = signer or Ed25519PrivateKey.generate()
    if trusted_authority is not None:
        _authority_check(trusted_authority)
        if trusted_authority.get("public_key") != b64encode(signer.public_key().public_bytes_raw()): raise P5R0Error("V3 signer authority mismatch")
        authority = dict(trusted_authority)
    else:
        authority = authority_from_private(signer, authority_id="p5-r0-v3-local-preflight-authority", key_id="p5-r0-v3-local-preflight-key")
    if bundle is None:
        from .domain_cards import create_domain_cards
        from .split import build_split_commitment
        split = build_split_commitment(seed="p5-r0-v2")
        cards = create_domain_cards(signer, authority_id=authority["authority_id"], key_id=authority["key_id"])
        bundle, _ = build_private_manifest(split, cards)
    split = parent_lock["split_commitment"]
    policy = repair_policy(contrast_matrix=split.get("contrast_matrix", []))
    worker_contract = {"schema": "P5R0WorkerContractV3", "task_schema": "P5R0WorkerTaskV3", "reply_schema": "P5R0WorkerReplyV3", "control_null_action": "worker_reply_only", "control_metadata_public": True, "private_fields_forbidden": ["truth", "target_action", "secret_seed", "private_domain_family", "split"], "digest": ""}
    worker_contract["digest"] = digest({k: v for k, v in worker_contract.items() if k != "digest"})
    evaluator_contract = {"schema": "P5R0EvaluatorContractV3", "episode_reset_policy": "fresh_case", "session_state": "declared_persistent_namespace", "namespace_isolation": "per_domain", "digest": ""}
    evaluator_contract["digest"] = digest({k: v for k, v in evaluator_contract.items() if k != "digest"})
    lock = {"schema": V3_SCHEMA, "feature_id": V3_FEATURE_ID, "classification": "local_readiness_only", "non_release": True, "adopted": False, "promotion_authority": False, "parent_lock_digest": V3_PARENT_LOCK_DIGEST, "parent_manifest_digest": parent_lock["manifest_digest"], "parent_case_index_digest": parent_lock["case_index_digest"], "parent_truth_digest": parent_lock["truth_digest"], "parent_store_digest": parent_lock["store_digest"], "parent_split_commitment": split, "authority": authority, "authority_digest": digest(authority), "authority_verified": trusted_authority is not None, "authority_transport_digest": digest(trusted_authority["transport_attestation"]) if trusted_authority else None, "manifest_digest": bundle["manifest_digest"], "case_index_digest": bundle["index_digest"], "truth_digest": bundle["truth_digest"], "store_digest": bundle["store_digest"], "policy": policy, "worker_contract": worker_contract, "evaluator_contract": evaluator_contract, "closure": closure or {"schema": "P5R0ClosureBindingV3", "bound": False, "runtime": "crun", "network": "none", "pull": "never"}, "limits": {"steps": 8, "frame_bytes": 65536, "wall_seconds": 3, "memory_mb": 512, "cpu": 1, "pids": 32}, "no_claims": ["P5 release", "general intelligence", "positive transfer", "adoption"]}
    lock["lock_digest"] = object_hash(lock, "lock_digest", "signature")
    lock["signature"] = sign(lock, signer, "lock_digest")
    target = Path(out); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(canonical_bytes(lock)); target.chmod(0o400)
    return {"lock": lock, "bundle": bundle, "signer": signer}


def validate_repair_lock(lock: dict[str, Any], *, trusted_authority: dict[str, Any] | None = None, expected_manifest_digest: str | None = None) -> dict[str, Any]:
    required = {"schema", "feature_id", "classification", "non_release", "adopted", "promotion_authority", "parent_lock_digest", "parent_manifest_digest", "parent_case_index_digest", "parent_truth_digest", "parent_store_digest", "parent_split_commitment", "authority", "authority_digest", "authority_verified", "authority_transport_digest", "manifest_digest", "case_index_digest", "truth_digest", "store_digest", "policy", "worker_contract", "evaluator_contract", "closure", "limits", "no_claims", "lock_digest", "signature"}
    if set(lock) != required or lock.get("schema") != V3_SCHEMA or lock.get("feature_id") != V3_FEATURE_ID or lock.get("parent_lock_digest") != V3_PARENT_LOCK_DIGEST or lock.get("classification") != "local_readiness_only" or lock.get("non_release") is not True or lock.get("adopted") is not False or lock.get("promotion_authority") is not False or lock.get("lock_digest") != object_hash(lock, "lock_digest", "signature"): raise P5R0Error("V3 lock")
    if expected_manifest_digest is not None and lock["manifest_digest"] != expected_manifest_digest: raise P5R0Error("V3 manifest binding")
    if trusted_authority is None: raise P5R0Error("V3 authority trust binding required")
    _authority_check(trusted_authority)
    if lock.get("authority") != trusted_authority or lock.get("authority_digest") != digest(trusted_authority) or lock.get("authority_verified") is not True or lock.get("authority_transport_digest") != digest(trusted_authority["transport_attestation"]): raise P5R0Error("V3 authority binding")
    try: verify_signature(lock, Ed25519PublicKey.from_public_bytes(b64decode(trusted_authority["public_key"])), "lock_digest")
    except Exception as exc: raise P5R0Error("V3 lock signature") from exc
    if lock["worker_contract"].get("task_schema") != "P5R0WorkerTaskV3" or lock["worker_contract"].get("reply_schema") != "P5R0WorkerReplyV3" or lock["worker_contract"].get("control_null_action") != "worker_reply_only" or lock["worker_contract"].get("digest") != digest({k: v for k, v in lock["worker_contract"].items() if k != "digest"}): raise P5R0Error("V3 worker contract")
    if lock["evaluator_contract"].get("schema") != "P5R0EvaluatorContractV3" or lock["evaluator_contract"].get("digest") != digest({k: v for k, v in lock["evaluator_contract"].items() if k != "digest"}): raise P5R0Error("V3 evaluator contract")
    closure = lock.get("closure")
    if not isinstance(closure, dict) or closure.get("schema") != "P5R0ClosureBindingV3" or closure.get("bound") is not True or closure.get("runtime") != "crun" or closure.get("network") != "none" or closure.get("pull") != "never" or closure.get("limits") != lock["limits"] or closure.get("worker_contract") != "P5R0WorkerContractV3": raise P5R0Error("V3 native closure")
    files = closure.get("files")
    if not isinstance(files, dict) or not V3_HOST_CLOSURE_KEYS.issubset(files) or not {"worker", "runtime"}.issubset(files) or not is_digest(closure.get("image_digest")) or not isinstance(closure.get("image_ref"), str) or not closure["image_ref"].endswith("@" + closure["image_digest"]) or closure.get("entrypoint") != "/runtime/p5_r0_worker": raise P5R0Error("V3 image/host closure binding")
    if not is_digest(closure.get("worker_digest")) or files.get("worker") != closure.get("worker_digest") or not is_digest(closure.get("runtime_digest")) or files.get("runtime") != closure.get("runtime_digest"): raise P5R0Error("V3 worker/runtime binding")
    if not is_digest(closure.get("seccomp_digest")) or not is_digest(closure.get("closure_digest")) or not is_digest(closure.get("allowed_syscalls_digest")) or not is_digest(closure.get("argv_digest")): raise P5R0Error("V3 closure digests")
    if not all(is_digest(lock.get(key)) for key in ("parent_manifest_digest", "parent_case_index_digest", "parent_truth_digest", "parent_store_digest", "manifest_digest", "case_index_digest", "truth_digest", "store_digest")): raise P5R0Error("V3 parent commitment")
    if lock["policy"].get("safeguards", {}).get("confidence_milli_min") != 900 or lock["policy"].get("safeguards", {}).get("held_out_adoption") is not False or lock["policy"].get("native_required") is not True or lock["policy"].get("external_authority_required") is not True: raise P5R0Error("V3 safeguard policy")
    return lock


def fail_closed_repair(receipts_root: Path, *, reason: str, lock_digest: str | None = None) -> dict[str, Any]:
    """Create a normal signed V3 no-go/rollback chain without native execution."""
    signer = Ed25519PrivateKey.generate()
    authority = authority_from_private(signer, authority_id="p5-r0-v3-local-preflight-authority", key_id="p5-r0-v3-local-preflight-key")
    chain = ReceiptChain(receipts_root, signer, authority_id=authority["authority_id"], key_id=authority["key_id"], protocol="V3")
    run_id = digest({"schema": "P5R0RunEnvelopeV3", "root": str(Path(receipts_root).resolve()), "lock": lock_digest, "reason": reason[:256]})
    snap = Snapshot({"graph": {}, "codebook": {}, "counter": 0, "episode": {"step": 0}})
    chain.append(run_id=run_id, kind="impasse", outcome="containment_failure", binding={"schema": "P5R0ImpasseBindingV3", "reason": reason[:256], "lock_digest": lock_digest})
    restored = snap.restore({"graph": {}, "codebook": {}, "counter": 0, "episode": {"step": 0}})
    rollback = rollback_receipt(run_id=run_id, pre_snapshot=snap.digest, restored_snapshot=restored, chain_digest=chain.digest)
    rollback["lock_digest"] = lock_digest
    chain.append(run_id=run_id, kind="rollback", outcome="restored" if rollback["exact"] else "rollback_impasse", binding=rollback)
    _append = chain.append(run_id=run_id, kind="run_closed", outcome="containment_failure" if rollback["exact"] else "rollback_impasse", binding={"lock_digest": lock_digest, "chain_digest_before_close": chain.digest})
    chain.verify_chain()
    public_key = b64encode(chain.public_key.public_bytes_raw())
    return {"schema": "P5R0ResultSealV3", "run_id": run_id, "disposition": "impasse", "outcome": "local_readiness_only/no_go", "manifest_digest": None, "lock_digest": lock_digest, "policy_digest": digest({}), "closure_digest": digest({"available": False, "network": "none", "pull": "never", "runtime": "crun"}), "receipt_public_key_digest": chain.public_key_digest, "record_count": 0, "control_count": 0, "contrast_count": 0, "records": [], "controls": [], "contrast_evidence": [], "mutation_artifacts": [], "receipts": len(chain.records), "chain_digest": chain.digest, "rollback": rollback, "rollback_cleanup": "exact" if rollback["exact"] else "impasse", "reason": reason, "closure": {"available": False, "network": "none", "pull": "never", "runtime": "crun"}, "gate_reasons": ["fail_closed_repair"], "claim_boundary": "No release, adoption, positive transfer, P5 claim, or general intelligence claim.", "evaluator_authority_id": chain.authority_id, "evaluator_key_id": chain.key_id, "receipt_key_id": chain.key_id, "receipt_public_key": public_key, "evaluator_public_key_digest": chain.public_key_digest, "signature_metadata": {"algorithm": "Ed25519", "receipt_schema": "P5R0ReceiptV3", "authority_id": chain.authority_id, "key_id": chain.key_id, "public_key_digest": chain.public_key_digest}, "receipt_chain_root": str(chain.root.resolve()), "receipt_chain_path": str(chain.root.resolve()), "receipt_chain_root_digest": chain.root_digest, "receipt_chain_final_digest": chain.final_digest, "first_receipt_hash": chain.records[0]["receipt_hash"], "final_receipt_hash": chain.records[-1]["receipt_hash"]}
