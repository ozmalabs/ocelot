"""Evaluator-custody result sealing for local P5-R0 runs."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from evaluation.p0a.canonical import b64decode, canonical_bytes, parse_canonical
from .protocol import P5R0Error, digest, is_digest
from .receipts import ReceiptChain


def _v3_chain(result: dict[str, Any]) -> ReceiptChain:
    required = {"evaluator_authority_id", "evaluator_key_id", "receipt_key_id", "receipt_public_key", "evaluator_public_key_digest", "receipt_public_key_digest", "signature_metadata", "receipt_chain_root", "receipt_chain_path", "receipt_chain_root_digest", "receipt_chain_final_digest", "first_receipt_hash", "final_receipt_hash", "chain_digest", "receipts"}
    if not required.issubset(result) or result.get("evaluator_key_id") != result.get("receipt_key_id") or result.get("evaluator_public_key_digest") != result.get("receipt_public_key_digest") or result.get("receipt_chain_path") != result.get("receipt_chain_root") or not all(isinstance(result.get(k), str) and result.get(k) for k in ("evaluator_authority_id", "receipt_key_id", "receipt_public_key", "receipt_chain_root")):
        raise P5R0Error("V3 result signature metadata")
    try: public = Ed25519PublicKey.from_public_bytes(b64decode(result["receipt_public_key"]))
    except Exception as exc: raise P5R0Error("V3 result public key") from exc
    public_key_digest = digest(result["receipt_public_key"])
    metadata = result["signature_metadata"]
    if metadata != {"algorithm": "Ed25519", "receipt_schema": "P5R0ReceiptV3", "authority_id": result["evaluator_authority_id"], "key_id": result["receipt_key_id"], "public_key_digest": public_key_digest} or result["receipt_public_key_digest"] != public_key_digest:
        raise P5R0Error("V3 result signature metadata")
    root = Path(result["receipt_chain_root"])
    if result["receipt_chain_root_digest"] != digest(str(root.resolve())) or not root.is_dir(): raise P5R0Error("V3 receipt chain root")
    chain = ReceiptChain.reload(root, public, authority_id=result["evaluator_authority_id"], key_id=result["receipt_key_id"], protocol="V3")
    if not chain.records or chain.final_digest != result["receipt_chain_final_digest"] or result["chain_digest"] != chain.final_digest or result["first_receipt_hash"] != chain.records[0]["receipt_hash"] or result["final_receipt_hash"] != chain.records[-1]["receipt_hash"] or result.get("receipts") != len(chain.records):
        raise P5R0Error("V3 receipt chain closure")
    if not is_digest(result.get("run_id")) or any(record["payload"].get("run_id") != result["run_id"] for record in chain.records): raise P5R0Error("V3 run binding")
    first_kind = chain.records[0]["payload"].get("kind")
    if first_kind not in {"preregistered", "impasse"}: raise P5R0Error("V3 preregistration ordering")
    if first_kind == "preregistered":
        binding = chain.records[0]["payload"].get("binding", {}); summary = result.get("preregistration", {})
        if binding.get("authority_id") != result["evaluator_authority_id"] or binding.get("key_id") != result["receipt_key_id"] or binding.get("public_key_digest") != public_key_digest: raise P5R0Error("V3 preregistration authority binding")
        expected = {"content_digest": result.get("preregistration_content_digest"), "order": [case.get("case_id") for case in result.get("case_index", [])], "order_digest": digest([case.get("case_id") for case in result.get("case_index", [])]), "parent_lock_digest": result.get("lock", {}).get("parent_lock_digest") if isinstance(result.get("lock"), dict) else summary.get("parent_lock_digest"), "parent_manifest_digest": summary.get("parent_manifest_digest"), "parent_case_index_digest": summary.get("parent_case_index_digest"), "parent_truth_digest": summary.get("parent_truth_digest"), "parent_store_digest": summary.get("parent_store_digest"), "lock_digest": result.get("lock_digest"), "manifest_digest": result.get("manifest_digest"), "truth_digest": result.get("truth_digest"), "store_digest": result.get("store_digest"), "policy_digest": result.get("preregistration_policy_digest"), "worker_contract_digest": result.get("preregistration_worker_contract_digest"), "evaluator_contract_digest": result.get("preregistration_evaluator_contract_digest"), "closure_digest": result.get("preregistration_closure_digest")}
        for key, value in expected.items():
            if value is not None and binding.get(key) != value: raise P5R0Error("V3 preregistration result binding")
        if summary.get("receipt_hash") != chain.records[0]["receipt_hash"] or summary.get("order_digest") != binding.get("order_digest") or summary.get("content_digest") != binding.get("content_digest"): raise P5R0Error("V3 preregistration summary")
    if result.get("outcome") != result.get("disposition") and not (result.get("disposition") == "impasse" and result.get("outcome") == "local_readiness_only/no_go"): raise P5R0Error("V3 disposition binding")
    # A completed no-go is still a claim about a completed locked workload.  Do
    # not let its shorter evidence shape be resealed as a harmless diagnostic;
    # only an explicit impasse may omit primary/control/contrast closure.
    if result.get("disposition") != "impasse":
        from .scoring import _validate_bound_evidence
        locked_evidence = {key: result.get(key) for key in ("run_id", "records", "case_index", "case_index_digest", "split_digest", "split_commitment", "controls", "contrast_evidence", "score_report", "chain_digest", "lock_digest", "closure", "rollback", "rollback_exact", "rollback_impasses", "leakage_findings", "controls_passed", "held_out_complete", "native_verified", "external_authority_verified", "native_controls_verified", "mechanics_contrasts_verified", "session_state_verified", "host_execution_evidence", "runtime_evidence", "kill_evidence")}
        locked_evidence["closure_digest"] = result.get("closure", {}).get("closure_digest") if isinstance(result.get("closure"), dict) else None
        locked_evidence["receipt_chain"] = chain
        _validate_bound_evidence(locked_evidence, result.get("policy", {}))
    if result.get("outcome") == "local_readiness_only/go":
        if result.get("gate_reasons") or result.get("closure", {}).get("available") is not True or result.get("native_verified") is not True or result.get("external_authority_verified") is not True or result.get("native_controls_verified") is not True or result.get("mechanics_contrasts_verified") is not True or result.get("controls_passed") is not True or result.get("rollback", {}).get("exact") is not True:
            raise P5R0Error("V3 GO gate")
        terminal_hashes = {record["receipt_hash"] for record in chain.records if record["payload"].get("kind") == "terminal"}; control_hashes = {record["receipt_hash"] for record in chain.records if record["payload"].get("kind") == "control"}; contrast_hashes = {record["receipt_hash"] for record in chain.records if record["payload"].get("kind") == "contrast"}
        referenced = {row.get("receipt_hash") for row in result.get("records", [])} | {row.get("receipt_hash") for row in result.get("controls", [])} | {row.get("left_receipt_hash") for row in result.get("contrast_evidence", [])} | {row.get("right_receipt_hash") for row in result.get("contrast_evidence", [])}
        if result.get("record_count") != len(result.get("records", [])) or result.get("control_count") != len(result.get("controls", [])) or not terminal_hashes.issubset(referenced) or not control_hashes.issubset(referenced) or not contrast_hashes.issubset(referenced): raise P5R0Error("V3 result receipt coverage")
        from .scoring import evaluate_gate
        evidence = {key: result.get(key) for key in ("run_id", "records", "case_index", "case_index_digest", "split_digest", "split_commitment", "controls", "contrast_evidence", "score_report", "chain_digest", "lock_digest", "closure", "native_verified", "external_authority_verified", "native_controls_verified", "mechanics_contrasts_verified", "session_state_verified", "rollback_exact", "rollback_impasses", "rollback", "leakage_findings", "controls_passed", "held_out_complete", "host_execution_evidence", "runtime_evidence", "kill_evidence")}
        evidence["closure_digest"] = result.get("closure", {}).get("closure_digest") if isinstance(result.get("closure"), dict) else None
        evidence["receipt_chain"] = chain
        policy = result.get("policy")
        if not isinstance(policy, dict) or evaluate_gate(evidence, policy)["disposition"] != "local_readiness_only/go": raise P5R0Error("V3 GO evidence")
    return chain


def verify_result_seal(path: Path) -> dict[str, Any]:
    """Reload a seal and independently verify its V3 receipt chain."""
    try: result = parse_canonical(Path(path).read_bytes())
    except Exception as exc: raise P5R0Error("result seal canonical") from exc
    if result.get("schema") == "P5R0ResultSealV3":
        _v3_chain(result)
        expected = result.get("seal_digest")
        if not is_digest(expected) or expected != digest({k: v for k, v in result.items() if k != "seal_digest"}): raise P5R0Error("result seal digest")
    elif result.get("schema") in {"P5R0ResultSealV1", "P5R0ResultSealV2"}:
        expected = result.get("seal_digest")
        if not is_digest(expected) or expected != digest({k: v for k, v in result.items() if k != "seal_digest"}): raise P5R0Error("legacy result seal digest")
    return result


def seal_result(result: dict[str, Any], out: Path, *, ledger: Path | None = None) -> dict[str, Any]:
    if result.get("schema") not in {"P5R0ResultSealV1", "P5R0ResultSealV2", "P5R0ResultSealV3"} or result.get("outcome") not in {"local_readiness_only/go", "local_readiness_only/no_go", "impasse"}: raise P5R0Error("result seal")
    if "claim_boundary" not in result or "general intelligence" not in result["claim_boundary"].lower(): raise P5R0Error("claim boundary")
    result = dict(result)
    if result.get("schema") == "P5R0ResultSealV2":
        if not result.get("chain_digest") or not result.get("rollback", {}).get("exact", False): raise P5R0Error("unverified result closure")
        if result.get("outcome") == "local_readiness_only/go":
            if result.get("gate_reasons") or any(not is_digest(row.get("receipt_hash")) for row in result.get("records", [])) or any(not is_digest(control.get("receipt_hash")) for control in result.get("controls", [])) or any(not is_digest(row.get("left_receipt_hash")) or not is_digest(row.get("right_receipt_hash")) for row in result.get("contrast_evidence", [])): raise P5R0Error("unverified GO evidence")
    elif result.get("schema") == "P5R0ResultSealV3":
        _v3_chain(result)
        if result.get("rollback", {}).get("exact") is not True: raise P5R0Error("unverified V3 rollback")
    result["seal_digest"] = digest({k: v for k, v in result.items() if k != "seal_digest"})
    target = Path(out); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(canonical_bytes(result)); target.chmod(0o400)
    if ledger is not None:
        path = Path(ledger); path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle: handle.write(canonical_bytes({"schema": "P5R0LedgerV2", "status": "sealed", "disposition": result.get("disposition"), "result_path": str(target), "no_release": True, "chain_digest": result.get("chain_digest")}) + b"\n"); handle.flush()
    return result
