import pytest
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluation.p0a.canonical import b64encode, object_hash, parse_canonical, verify_signature
from evaluation.p4.evaluator import P4R0Evaluator
from evaluation.p4.protocol import P4ProtocolError, reservation_digest
from evaluation.p4.receipts import P4ReceiptLog, payload
from evaluation.p4.tests.helpers import local_lock, staged_spec

D = "sha256:" + "2" * 64

def proposal(parent, *, proposal_id="p", sequence=1, kind="inspect", reservation=None):
    p = {"schema": "GraphActionProposalV1", "proposal_id": proposal_id, "run_id": "r", "sequence": sequence, "kind": kind, "causal_parent_receipt_hash": parent, "reservation": reservation or {"actions": 1, "risk": 1, "transactions": 1}, "graph_digest": D}
    p["proposal_digest"] = object_hash(p)
    return p

def authorized(tmp_path):
    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    log = P4ReceiptLog(tmp_path / "receipts", signer)
    lock = local_lock(tmp_path, spec, evaluator_signer=signer)
    evaluator = P4R0Evaluator(b"x", {"g": 1}, lock, log)
    replan = log.append("replan", payload(run_id="r", lock_digest=lock["lock_digest"], fixture_digest=lock["artifacts"]["fixtures"], snapshot_digest=evaluator.pre_run_graph_snapshot_digest, outcome="verified", reason="verified_replan", resources={"actions": 0, "risk": 0, "transactions": 0}))
    return evaluator, replan["receipt_hash"]

def test_grant_expiry_and_replay_call_simulator_zero_times(tmp_path):
    evaluator, parent = authorized(tmp_path)
    p = proposal(parent)
    grant = evaluator.grant(p, 0)
    with pytest.raises(P4ProtocolError):
        evaluator.act(p, grant, 2)
    assert evaluator.simulator_calls == 0
    evaluator, parent = authorized(tmp_path / "replay")
    p = proposal(parent)
    grant = evaluator.grant(p, 0)
    evaluator.act(p, grant, 0)
    with pytest.raises(P4ProtocolError):
        evaluator.act(p, grant, 0)
    assert evaluator.simulator_calls == 1

def test_grants_reject_unapproved_kind_parent_and_lock_overreservation(tmp_path):
    evaluator, parent = authorized(tmp_path)
    with pytest.raises(P4ProtocolError):
        evaluator.grant(proposal(parent, kind="delete_everything"), 0)
    with pytest.raises(P4ProtocolError):
        evaluator.grant(proposal(parent, reservation={"actions": 1, "risk": 9, "transactions": 1}), 0)
    with pytest.raises(P4ProtocolError):
        evaluator.grant(proposal("sha256:" + "f" * 64), 0)
    assert evaluator.simulator_calls == 0

def test_cumulative_signed_lock_reservations_cannot_be_bypassed(tmp_path):
    evaluator, parent = authorized(tmp_path)
    for sequence in range(1, 9):
        evaluator.grant(proposal(parent, proposal_id=f"p{sequence}", sequence=sequence), 0)
    with pytest.raises(P4ProtocolError):
        evaluator.grant(proposal(parent, proposal_id="p9", sequence=9), 0)
    assert evaluator.reserved == {"actions": 8, "risk": 8, "transactions": 8}
    assert evaluator.simulator_calls == 0

def test_signed_outcome_binds_run_proposal_grant_broker_sequence_and_snapshot(tmp_path):
    evaluator, parent = authorized(tmp_path)
    p = proposal(parent, sequence=7)
    outcome = evaluator.act(p, evaluator.grant(p, 0), 0)
    verified = evaluator.verify_sealed_action_outcome(outcome)
    assert verified["proposal_digest"] == p["proposal_digest"] and verified["sequence"] == 8
    outcome["sequence"] = 9
    with pytest.raises(P4ProtocolError):
        evaluator.verify_sealed_action_outcome(outcome)

def test_exact_restore():
    evaluator = P4R0Evaluator(b"x", {"g": 1})
    evaluator.graph["g"] = 2
    assert evaluator.restore() == evaluator.pre_run_graph_snapshot_digest


def test_action_reservation_debits_signed_limit_by_requested_amount(tmp_path):
    evaluator, parent = authorized(tmp_path)
    for sequence in range(1, 5):
        evaluator.grant(proposal(parent, proposal_id=f"two-{sequence}", sequence=sequence, reservation={"actions": 2, "risk": 1, "transactions": 1}), 0)
    with pytest.raises(P4ProtocolError):
        evaluator.grant(proposal(parent, proposal_id="two-5", sequence=5, reservation={"actions": 2, "risk": 1, "transactions": 1}), 0)
    assert evaluator.reserved["actions"] == 8

def test_verified_native_outcome_emits_canonical_signed_reservation_bound_transport(tmp_path):
    evaluator, parent = authorized(tmp_path)
    p = proposal(parent)
    outcome = evaluator.act(p, evaluator.grant(p, 0), 0)
    native = evaluator.verified_native_outcome(outcome)
    assert native["reservation_digest"] == reservation_digest(
        run_id=p["run_id"], proposal_digest=p["proposal_digest"],
        proposal_sequence=p["sequence"], snapshot_digest=evaluator.pre_run_graph_snapshot_digest,
        reservation=p["reservation"],
    )
    signed = parse_canonical(evaluator.serialized_verified_native_outcome(outcome))
    assert signed["schema"] == "P4R0EvaluatorSignedOutcomeV1"
    assert signed["authority_id"] == "p4-r0-evaluator"
    assert signed["key_id"] == "p4-r0-local-evaluator"
    assert signed["authority_public_key"] == b64encode(evaluator.receipts.public_key.public_bytes_raw())
    assert signed["lock_digest"] == evaluator.lock["lock_digest"]
    assert {key: signed[key] for key in native} == native
    verify_signature(signed, evaluator.receipts.public_key)


def test_verified_native_outcome_rejects_missing_or_altered_reservation(tmp_path):
    evaluator, parent = authorized(tmp_path)
    p = proposal(parent)
    outcome = evaluator.act(p, evaluator.grant(p, 0), 0)
    missing = dict(outcome)
    missing.pop("reservation_digest")
    with pytest.raises(P4ProtocolError):
        evaluator.verified_native_outcome(missing)
    altered = dict(outcome)
    altered["reservation"] = {"actions": 2, "risk": 1, "transactions": 1}
    with pytest.raises(P4ProtocolError):
        evaluator.verified_native_outcome(altered)


def test_verified_native_outcome_rejects_forged_reservation_export(tmp_path):
    evaluator, parent = authorized(tmp_path)
    p = proposal(parent)
    outcome = evaluator.act(p, evaluator.grant(p, 0), 0)
    forged = dict(outcome)
    forged["reservation_digest"] = "sha256:" + "f" * 64
    with pytest.raises(P4ProtocolError):
        evaluator.serialized_verified_native_outcome(forged)


def test_verified_native_outcome_only_exposes_verified_receipt_chain(tmp_path):
    evaluator, parent = authorized(tmp_path)
    p = proposal(parent)
    outcome = evaluator.act(p, evaluator.grant(p, 0), 0)
    native = evaluator.verified_native_outcome(outcome)
    assert native["proposal_digest"] == p["proposal_digest"]
    outcome["proposal_receipt_digest"] = "sha256:" + "f" * 64
    with pytest.raises(P4ProtocolError):
        evaluator.verified_native_outcome(outcome)
