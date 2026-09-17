import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.canonical import canonical_bytes
from evaluation.p4.fixtures import load_bundle, materialize
from evaluation.p4.protocol import P4ProtocolError
from evaluation.p4.receipts import P4ReceiptLog
from evaluation.p4.runner import _native_request
from evaluation.p4.tests.helpers import FIXTURE, local_lock, staged_spec
from evaluation.p4.evaluator import P4R0Evaluator


def test_materialization_is_opaque_and_record_digest_is_run_independent():
    first = materialize(FIXTURE, "run-a", "fx-0001")[0]
    second = materialize(FIXTURE, "run-b", "fx-0001")[0]
    assert first["selection_id"] == second["selection_id"]
    assert first["record_digest"] == second["record_digest"]
    assert first["fixture_id"] != second["fixture_id"]
    assert first["actions"] == ["inspect", "reverse", "advance"]
    assert first["observations"] == [{"signal": 0}, {"signal": 1}]


def test_fixture_transition_and_labels_fail_closed(tmp_path):
    value = json.loads(FIXTURE.read_text())
    value["fixtures"][0]["actions"] = ["reverse", "inspect", "advance"]
    altered = tmp_path / "altered.json"
    altered.write_bytes(canonical_bytes(value))
    with pytest.raises(P4ProtocolError):
        load_bundle(altered)
    value["fixtures"][0]["actions"] = ["inspect", "reverse", "advance"]
    value["fixtures"][0]["observations"][0] = {"hidden_rule": 0}
    altered.write_bytes(canonical_bytes(value))
    with pytest.raises(P4ProtocolError):
        load_bundle(altered)


def test_native_request_contains_locked_record_and_opaque_id(tmp_path):
    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    lock = local_lock(tmp_path, spec, evaluator_signer=signer)
    receipts = P4ReceiptLog(tmp_path / "receipts", signer)
    evaluator = P4R0Evaluator(b"seed", {"root": 1}, lock, receipts)
    request = _native_request(lock, evaluator, receipts, "p4-r0", evaluator.pre_run_graph_snapshot_digest)
    selection = lock["fixture_selection"]
    assert request["selection_id"] == selection["selection_id"]
    assert request["record_digest"] == selection["record_digest"]
    assert request["actions"] == selection["actions"]
    assert request["observations"] == selection["observations"]
    signed = json.loads(request["outcomes"][0])
    assert signed["fixture_record_digest"] == selection["record_digest"]
    assert signed["fixture_selection_id"] == selection["selection_id"]



def test_runtime_selection_catalog_accepts_both_fixture_records_and_declared_arms(tmp_path):
    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    lock = local_lock(tmp_path, spec, evaluator_signer=signer)
    receipts = P4ReceiptLog(tmp_path / "receipts", signer)
    evaluator = P4R0Evaluator(b"seed", {"root": 1}, lock, receipts)
    first = _native_request(lock, evaluator, receipts, "p4-r0-a", evaluator.pre_run_graph_snapshot_digest, fixture_key="fx-0001", arm_id="graph_planner")
    evaluator.restore()
    second = _native_request(lock, evaluator, receipts, "p4-r0-b", evaluator.pre_run_graph_snapshot_digest, fixture_key="fx-0002", arm_id="search_budget_matched")
    assert first["runtime_selection"]["fixture_key"] != second["runtime_selection"]["fixture_key"]
    assert first["arm_digest"] != second["arm_digest"]
    assert first["selection_digest"] != second["selection_digest"]


def test_runtime_selection_rejects_unavailable_fixture_or_arm(tmp_path):
    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    lock = local_lock(tmp_path, spec, evaluator_signer=signer)
    receipts = P4ReceiptLog(tmp_path / "receipts", signer)
    evaluator = P4R0Evaluator(b"seed", {"root": 1}, lock, receipts)
    with pytest.raises(P4ProtocolError):
        _native_request(lock, evaluator, receipts, "p4-r0", evaluator.pre_run_graph_snapshot_digest, fixture_key="fx-missing")
    with pytest.raises(P4ProtocolError):
        _native_request(lock, evaluator, receipts, "p4-r0", evaluator.pre_run_graph_snapshot_digest, arm_id="arm-missing")
