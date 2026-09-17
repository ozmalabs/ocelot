from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p5_r0.domain_cards import authority_from_private
from evaluation.p5_r0.evaluator import P5R0Evaluator
from evaluation.p5_r0.fixture_generator import private_store_for
from evaluation.p5_r0.mechanics import private_truth, spec_for, transition
from evaluation.p5_r0.preregister import preregister, validate_lock
from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.runner import run_readiness_gate


def test_production_lock_requires_external_authority_and_native_closure_fails_closed():
    with TemporaryDirectory() as directory:
        root = Path(directory); key = Ed25519PrivateKey.generate(); authority = authority_from_private(key); authority["transport_attestation"] = {"transport": "local-test", "nonce": "trusted"}
        artifact = preregister(root / "lock.json", signer=key, trusted_authority=authority)
        with pytest.raises(P5R0Error): validate_lock(artifact["lock"])
        validate_lock(artifact["lock"], trusted_authority=authority, expected_manifest_digest=artifact["bundle"]["manifest_digest"])
        result = run_readiness_gate(artifact["bundle"], receipts_root=root / "receipts", lock=artifact["lock"], trusted_authority=authority, receipt_signer=key)
        assert result["disposition"] == "impasse"
        assert result["rollback"]["exact"] is True


def test_controls_have_worker_evidence_and_factor_transition_is_behavioral():
    with TemporaryDirectory() as directory:
        root = Path(directory); artifact = preregister(root / "lock.json")
        result = run_readiness_gate(artifact["bundle"], receipts_root=root / "receipts", require_native=False)
        assert all(control["task_digest"] and control["worker_invocation"] for control in result["controls"])
        assert all(control["passed"] for control in result["controls"])
        private = private_store_for(artifact["bundle"])["cases"][0]
        flat = dict(private); flat["factors"] = {**private["factors"], "action_effect": "flat_primitive"}; flat["case_digest"] = private["case_digest"]
        composed = dict(private); composed["factors"] = {**private["factors"], "action_effect": "compositional", "reward": "constrained_progress"}; composed["case_digest"] = private["case_digest"]
        flat_spec = spec_for(flat); composed_spec = spec_for(composed)
        flat_truth = private_truth(flat, flat_spec); composed_truth = private_truth(composed, composed_spec)
        flat_result = transition({}, 0, flat_truth, flat_spec, 0); composed_result = transition({}, 0, composed_truth, composed_spec, 0)
        assert flat_result["effect_digest"] != composed_result["effect_digest"]
        assert flat_result["terminal"] != composed_result["terminal"]


def test_warm_session_chains_and_frozen_write_is_contained():
    with TemporaryDirectory() as directory:
        artifact = preregister(Path(directory) / "lock.json"); evaluator = P5R0Evaluator(artifact["bundle"]); order = digest([case["case_id"] for case in artifact["bundle"]["case_index"]])
        warm = evaluator.arm_context("warm_adaptive", order); first = artifact["bundle"]["case_index"][0]; evaluator.begin_case(first["case_id"], 0); first_outcome = evaluator.evaluate(first, "warm_adaptive", 0)
        second = artifact["bundle"]["case_index"][1]; session = evaluator.begin_case(second["case_id"], 1)
        assert session["pre_state_digest"] == first_outcome["post_state_digest"]
        evaluator._active_context = None; frozen = evaluator.arm_context("frozen_transfer", order); evaluator.begin_case(first["case_id"], 0); before = evaluator.session_digest(); blocked = evaluator.evaluate(first, "frozen_transfer", 0, write_attempt=True)
        assert blocked["outcome"] == "containment_failure" and before == blocked["post_state_digest"]
