from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p5_r0.domain_cards import authority_from_private
from evaluation.p5_r0.evaluator import P5R0Evaluator
from evaluation.p5_r0.fixture_generator import generate_fixtures, make_task_v3, private_store_for
from evaluation.p5_r0.native_worker import validate_reply_v3, validate_task, run
from evaluation.p5_r0.preregister import preregister
from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.repair import V3_PARENT_LOCK_DIGEST, preregister_repair, validate_repair_lock


def test_v3_worker_null_is_authoritative_and_zero_is_distinct():
    artifact = preregister(Path(TemporaryDirectory().name) / "lock.json")
    case = artifact["bundle"]["case_index"][0]
    private = private_store_for(artifact["bundle"])["cases"][0]
    task = make_task_v3(private, task_nonce="control", control_metadata={"control_id": "exact_memorization", "training_commitment": digest([]), "challenge_commitment": case["case_digest"], "policy": "abstain_if_no_exact_or_template_match"})
    validate_task(task)
    assert run(task, lambda _: None) is None
    assert run(task, lambda _: 0) == 0
    assert validate_reply_v3({"schema": "P5R0WorkerReplyV3", "action": None}, task)["action"] is None


def test_v3_task_privacy_and_fresh_episode_with_persistent_projection():
    artifact = preregister(Path(TemporaryDirectory().name) / "lock.json")
    evaluator = P5R0Evaluator(artifact["bundle"])
    order = digest([c["case_id"] for c in artifact["bundle"]["case_index"]])
    evaluator.arm_context("warm_adaptive", order)
    first = next(c for c in artifact["bundle"]["case_index"] if c["combination_id"] == "T02")
    for ordinal, prior in enumerate(artifact["bundle"]["case_index"][:artifact["bundle"]["case_index"].index(first)]):
        evaluator.begin_case(prior["case_id"], ordinal); evaluator.evaluate(prior, "warm_adaptive", 0)
    evaluator.begin_case(first["case_id"], artifact["bundle"]["case_index"].index(first))
    task = evaluator.task(first, "nonce", evaluator._active_context)
    assert task["schema"] == "P5R0WorkerTaskV3" and task["episode_step"] == 0
    assert all(key not in task for key in ("truth", "target_action", "secret_seed", "private_domain_family", "split"))
    evaluator.evaluate(first, "warm_adaptive", 0)
    second = artifact["bundle"]["case_index"][artifact["bundle"]["case_index"].index(first) + 1]
    evaluator.begin_case(second["case_id"], artifact["bundle"]["case_index"].index(second))
    next_task = evaluator.task(second, "nonce2", evaluator._active_context)
    assert next_task["episode_step"] == 0
    assert next_task["reset_policy"] == "fresh_case"


def _proposal(evaluator, source, target, task_digest, confidence=900):
    return {"schema": "P5R0AdaptationProposalV3", "domain_token": target["domain_token"], "source_case_id": source["case_id"], "source_split": source["split"], "source_session_id": evaluator.state["session_id"], "source_case_digest": source["case_digest"], "target_case_id": target["case_id"], "target_case_digest": target["case_digest"], "task_digest": task_digest, "confidence_milli": confidence, "safe_success": True, "value": {"bounded": True}}


def test_v3_safeguard_confidence_provenance_and_exact_boundary():
    artifact = preregister(Path(TemporaryDirectory().name) / "lock.json")
    evaluator = P5R0Evaluator(artifact["bundle"]); rows = artifact["bundle"]["case_index"]
    order = digest([c["case_id"] for c in rows]); evaluator.arm_context("warm_adaptive", order)
    source = next(c for c in rows if c["combination_id"] == "T01"); target = next(c for c in rows if c["combination_id"] == "T02")
    for ordinal, prior in enumerate(rows[:rows.index(target)]):
        evaluator.begin_case(prior["case_id"], ordinal); evaluator.evaluate(prior, "warm_adaptive", 0)
    evaluator.begin_case(target["case_id"], rows.index(target))
    low = evaluator.adopt_adaptation(_proposal(evaluator, source, target, digest({"task": "low"}), 899))
    assert low["accepted"] is False
    accepted = evaluator.adopt_adaptation(_proposal(evaluator, source, target, digest({"task": "exact"}), 900))
    assert accepted["accepted"] is True
    assert evaluator.adopt_adaptation(_proposal(evaluator, source, target, digest({"task": "second"}), 900))["accepted"] is False
    held = next(c for c in rows if c["split"] == "held_out")
    with pytest.raises(P5R0Error): evaluator.adopt_adaptation(_proposal(evaluator, held, target, digest({"task": "held"}), 900))


def test_v3_lock_is_new_and_requires_independent_authority(tmp_path):
    parent = {"lock_digest": V3_PARENT_LOCK_DIGEST, "manifest_digest": "sha256:" + "1" * 64, "case_index_digest": "sha256:" + "2" * 64, "truth_digest": "sha256:" + "3" * 64, "store_digest": "sha256:" + "4" * 64, "split_commitment": {"contrast_matrix": []}}
    artifact = preregister_repair(tmp_path / "v3-lock.json", parent_lock=parent)
    assert artifact["lock"]["schema"] == "P5R0LocalLockV3"
    assert artifact["lock"]["parent_lock_digest"] == V3_PARENT_LOCK_DIGEST
    with pytest.raises(P5R0Error): validate_repair_lock(artifact["lock"])
    key = Ed25519PrivateKey.generate(); authority = authority_from_private(key, "external-test-authority", "external-test-key"); authority["transport_attestation"] = {"schema": "external", "nonce": "test"}
    # The local signer is not allowed to masquerade as the injected authority.
    with pytest.raises(P5R0Error): validate_repair_lock(artifact["lock"], trusted_authority=authority)



def test_explicit_private_store_and_checkpoint_rehydrate_without_registry():
    from evaluation.p5_r0 import fixture_generator

    artifact = preregister(Path(TemporaryDirectory().name) / "lock.json")
    bundle = artifact["bundle"]
    store = private_store_for(bundle)
    fixture_generator._PRIVATE_STORES.pop(bundle["manifest_digest"], None)
    evaluator = P5R0Evaluator(bundle, store)
    order = digest([row["case_id"] for row in bundle["case_index"]])
    context = evaluator.arm_context("warm_adaptive", order)
    case = bundle["case_index"][0]
    evaluator.begin_case(case["case_id"], 0)
    evaluator.evaluate(case, "warm_adaptive", 0)
    checkpoint = evaluator.checkpoint()

    restored = P5R0Evaluator(bundle, store)
    restored.restore_checkpoint(checkpoint)
    assert restored.session_digest() == evaluator.session_digest()
    assert restored._active_context == context
    with pytest.raises(P5R0Error):
        P5R0Evaluator(bundle, {**store, "store_digest": digest("tampered")})
