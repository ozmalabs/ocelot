from copy import deepcopy
from pathlib import Path

import pytest

from evaluation.p0a.canonical import sha256
from services.p5_r0_evaluator.deploy.gcs_boundary_packet import (
    DEFAULT_PACKET,
    GCSBoundaryPacketError,
    validate_packet,
)

ROOT = Path(__file__).resolve().parents[3]


def _packet() -> dict:
    import json

    return json.loads(DEFAULT_PACKET.read_text(encoding="utf-8"))


def test_review_only_packet_binds_exact_private_bundle_and_generation_zero_state():
    checked = validate_packet()
    assert checked["project_id"] == "ocelot-proof"
    assert checked["bucket"] == "p5-evaluator-ocelot-proof-141633828616"
    assert checked["run_id"] == "rs069r18r13-op4-04a98e3e"
    assert checked["object_count"] == 11
    assert checked["expected_generation"] == 0
    assert checked["cloud_operations"] == []
    assert checked["mutations_performed"] is False
    assert checked["child_approval_present"] is False


def test_packet_digest_and_generation_tamper_fail_closed(tmp_path):
    packet = _packet()
    packet["objects"][0]["generation_precondition"]["expected_generation"] = 7
    packet["packet_digest"] = sha256({key: value for key, value in packet.items() if key != "packet_digest"})
    path = tmp_path / "tampered.json"
    path.write_text(__import__("json").dumps(packet), encoding="utf-8")
    with pytest.raises(GCSBoundaryPacketError, match="generation precondition drift"):
        validate_packet(path, ROOT)


def test_packet_cannot_promote_credentials_or_iam(tmp_path):
    packet = _packet()
    packet["credential_binding"]["credential_injected"] = True
    packet["desired_iam"]["apply_performed"] = True
    packet["packet_digest"] = sha256({key: value for key, value in packet.items() if key != "packet_digest"})
    path = tmp_path / "promoted.json"
    path.write_text(__import__("json").dumps(packet), encoding="utf-8")
    with pytest.raises(GCSBoundaryPacketError, match="credential boundary drift"):
        validate_packet(path, ROOT)


def test_packet_does_not_reference_master_runsheet_as_writable_input():
    packet = _packet()
    assert packet["approval_context"]["master_runsheet_modified"] is False
    assert "docs/research/engine_substrate/P5_MASTER_RUNSHEET.md" not in packet["artifact_binding"].values()



def test_exact_probe_and_unsigned_lock_commitments_are_closed(tmp_path):
    packet = _packet()
    packet["read_only_evidence"]["object_probes"][0]["object_name"] = "wrong-object"
    packet["packet_digest"] = sha256({key: value for key, value in packet.items() if key != "packet_digest"})
    path = tmp_path / "probe-tampered.json"
    path.write_text(__import__("json").dumps(packet), encoding="utf-8")
    with pytest.raises(GCSBoundaryPacketError, match="exact object probe drift"):
        validate_packet(path, ROOT)

    packet = _packet()
    packet["artifact_binding"]["unsigned_lock_digest"] = "sha256:" + "0" * 64
    packet["packet_digest"] = sha256({key: value for key, value in packet.items() if key != "packet_digest"})
    path = tmp_path / "lock-tampered.json"
    path.write_text(__import__("json").dumps(packet), encoding="utf-8")
    with pytest.raises(GCSBoundaryPacketError, match="unsigned lock digest drift"):
        validate_packet(path, ROOT)
