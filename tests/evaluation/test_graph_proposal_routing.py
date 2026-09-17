import json

import pytest

from evaluation.p0a.canonical import ProtocolError, canonical_bytes, object_hash
from evaluation.p0a.entrypoint import evaluation_mode
from evaluation.p0a.graph_proposals import GraphProposalProjector
from evaluation.p0a.manifest import ManifestVerifier
from evaluation.p0a.provenance import NativeGraphProvenanceVerifier
from evaluation.p0a.simulator import METHOD
from conftest import (DIGESTS, NOW, PRIVATE, PUBLIC, EXPORT_AUTHORITY_KEYS, broker, fake_sandbox, grant,
                      manifest, native_graph_export, native_graph_export_attestation, raw, staged_receipt_log)


def proposal(*, proposal_id="123e4567-e89b-42d3-a456-426614174010", steps=1):
    value = {"schema": "GraphActionProposalV1", "proposal_id": proposal_id, "kind": "GraphCounterAdvanceV1",
             "args": {"steps": steps}, "input_refs": [], "source": {"origin_rule_digest": "sha256:" + "1" * 64,
             "source_node_type": "NativeRuleEvidenceV1", "source_content_digest": "sha256:" + "2" * 64,
             "graph_snapshot_digest": DIGESTS["input_snapshot_digest"]}, "causal_parent_receipt_hash": None,
             "requested_budget": {"wall_ms": 0, "cpu_ms": 0, "memory_bytes": 0, "writes": 0, "network_bytes": 0},
             "graph_logical_time": 7}
    value["proposal_digest"] = object_hash(value)
    return value


def provenance_for(target, *proposals):
    return NativeGraphProvenanceVerifier(native_graph_export(*proposals, run_id=target.manifest.run_id),
        run_id=target.manifest.run_id, input_snapshot_digest=DIGESTS["input_snapshot_digest"], now_ms=lambda: NOW)


def test_staged_worker_submits_attested_candidate_and_receipts_host_denial(tmp_path):
    body, native = manifest(), proposal()
    log, control = staged_receipt_log(tmp_path, body)
    launcher = fake_sandbox(tmp_path, proposals=(native,))
    export = native_graph_export(native, run_id=body["run_id"])
    with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), manifest=body,
                         expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC}, receipt_log=log,
                         native_graph_export=export, native_graph_export_attestation=native_graph_export_attestation(export, run_id=body["run_id"]),
                         native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW,
                         agent_spec=launcher.spec, sandbox_launcher=launcher, control_root=control) as run:
        assert not hasattr(run, "action_client")
        assert run.wait(1) == 0
    assert launcher.process.replies[0]["reply"]["phase"] == "denied"
    receipt = json.loads(log.path.read_text())
    assert receipt["reason_code"] == "method_not_enabled" and receipt["graph_proposal_digest"] == native["proposal_digest"]


def test_invalid_or_missing_native_evidence_never_launches_worker(tmp_path):
    body, native = manifest(), proposal()
    log, control = staged_receipt_log(tmp_path, body)
    with pytest.raises(ProtocolError, match="prelaunch rejected"):
        with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), manifest=body,
                             expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC}, receipt_log=log,
                             native_graph_export=b"{", native_export_attestation_keys=EXPORT_AUTHORITY_KEYS,
                             now_ms=lambda: NOW, control_root=control):
            pytest.fail("invalid export launched")
    assert log.last_receipt["reason_code"] == "invalid_native_graph_export"


def test_graph_projection_rejects_method_grant_and_raw_request_substitution(tmp_path):
    target, native = broker(tmp_path), proposal()
    native["method"] = "shell.exec"
    assert GraphProposalProjector(target).submit(canonical_bytes(native)).phase == "denied"
    assert target.receipt_log.last_receipt["reason_code"] == "method_substitution"
    candidate = proposal(proposal_id="123e4567-e89b-42d3-a456-426614174012")
    assert GraphProposalProjector(target, provenance_verifier=provenance_for(target, candidate)).submit(raw(candidate)).phase == "denied"
    assert target.receipt_log.last_receipt["reason_code"] == "grant_required"
    forged = {"schema": "ActionRequestV2", "request_hash": "sha256:" + "0" * 64,
              "run_id": target.manifest.run_id, "method": METHOD, "args": {},
              "input_snapshot_digest": DIGESTS["input_snapshot_digest"]}
    assert target.submit_action(raw(forged), raw(grant(forged))).phase == "denied"


def test_receipt_writer_failure_is_terminal_and_effect_free(tmp_path):
    target, native = broker(tmp_path, p0=True), proposal()
    target.receipt_log._replace = lambda *_args: (_ for _ in ()).throw(OSError("writer failed"))
    reply = GraphProposalProjector(target, provenance_verifier=provenance_for(target, native)).submit(raw(native))
    assert reply.phase == "impasse" and target.impasse and target.state["counter"] == 0



def test_native_candidate_forgery_mismatch_and_replay_are_signed_p0_denials(tmp_path):
    target, native = broker(tmp_path, p0=True), proposal()
    provenance = provenance_for(target, native)
    projector = GraphProposalProjector(target, provenance_verifier=provenance)

    forged = dict(native)
    forged["args"] = {"steps": 2}
    forged["proposal_digest"] = object_hash(forged, "proposal_digest")
    assert projector.submit_native_proposal(forged).phase == "denied"
    forged_receipt = target.receipt_log.last_receipt
    assert forged_receipt["reason_code"] == "forged_graph_provenance"
    assert forged_receipt["schema"] == "ActionReceiptV2"

    assert projector.submit_native_proposal(native).phase == "denied"
    attested_receipt = target.receipt_log.last_receipt
    assert attested_receipt["reason_code"] == "method_not_enabled"
    assert attested_receipt["schema"] == "ActionReceiptV3"
    assert attested_receipt["native_export_digest"] == provenance._export_digest

    assert projector.submit_native_proposal(native).phase == "denied"
    assert target.receipt_log.last_receipt["reason_code"] == "replay"
    target.receipt_log.validate()
    assert target.state["counter"] == 0
