from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p5_r0.domain_cards import create_domain_cards
from evaluation.p5_r0.evaluator import P5R0Evaluator
from evaluation.p5_r0.fixture_generator import build_private_manifest, make_task_v3, private_store_for
from evaluation.p5_r0.mutations import record_rejected_reset, verify_mutation_artifact
from evaluation.p5_r0.native_worker import run
from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.receipts import ReceiptChain
from evaluation.p5_r0.repair import repair_policy
from evaluation.p5_r0.scoring import evaluate_gate
from evaluation.p5_r0.split import build_split_commitment


def _bundle():
    bundle, _store = build_private_manifest(build_split_commitment(), create_domain_cards())
    return bundle


def test_illegal_action_is_a_locked_worker_protocol_error_before_evaluator():
    bundle = _bundle()
    case = bundle["case_index"][0]
    task = make_task_v3(
        private_store_for(bundle)["cases"][0],
        task_nonce="illegal",
        control_metadata={
            "control_id": "illegal_action",
            "training_commitment": digest("train"),
            "challenge_commitment": case["case_digest"],
            "policy": "locked_protocol_error",
        },
    )
    with pytest.raises(P5R0Error, match="locked protocol_error"):
        run(task, lambda _: 0)


def test_warm_reset_rejects_identity_and_receipts_signed_mutation(tmp_path):
    from evaluation.p5_r0.preregister import preregister

    bundle = preregister(tmp_path / "v2.json")["bundle"]
    evaluator = P5R0Evaluator(bundle)
    order = digest([case["case_id"] for case in bundle["case_index"]])
    context = evaluator.arm_context("warm_adaptive", order)
    before = evaluator.session_digest()
    with pytest.raises(P5R0Error, match="warm reset"):
        evaluator.arm_context("warm_adaptive", order, session_id=digest("wrong-session"))
    assert evaluator.session_digest() == before

    signer = Ed25519PrivateKey.generate()
    chain = ReceiptChain(tmp_path / "receipts", signer, authority_id="authority", key_id="key", protocol="V3")
    chain.append(run_id=digest("run"), kind="preregistered", outcome="verified", binding={})
    mutation = record_rejected_reset(
        chain=chain,
        artifact_root=tmp_path / "mutations",
        run_id=digest("run"),
        lock_digest=digest("lock"),
        ordinal=0,
        task_digest=None,
        pre_state_digest=before,
        proposed_session_id=digest("wrong-session"),
    )
    artifact = verify_mutation_artifact(Path(mutation["artifact_path"]), chain.public_key, expected_receipt_hash=mutation["artifact"]["receipt_hash"])
    assert artifact["outcome"] == "rejected"
    assert artifact["post_state_digest"] == before
    assert chain.records[-1]["payload"]["kind"] == "mutation"


def test_gate_marks_missing_lock_bound_host_evidence_no_go():
    policy = repair_policy(case_count=48, contrast_matrix=[])
    result = evaluate_gate(
        {
            "records": [],
            "controls": [],
            "score_report": {},
            "native_verified": True,
            "external_authority_verified": True,
            "host_execution_evidence": None,
            "runtime_evidence": None,
            "kill_evidence": None,
            "rollback_exact": True,
            "rollback_impasses": 0,
        },
        policy,
    )
    assert result["disposition"] == "local_readiness_only/no_go"
    assert {"host_execution_evidence", "runtime_evidence", "kill_evidence"} <= set(result["reasons"])
