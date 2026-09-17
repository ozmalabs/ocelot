import json

import pytest

from evaluation.p0a.canonical import ProtocolError, object_hash
from evaluation.p0a.entrypoint import EvaluationActionClient, evaluation_mode
from evaluation.p0a.legacy_io_guard import ROUTE_INVENTORY
from evaluation.p0a.manifest import ManifestVerifier
from evaluation.p0a.receipt_log import ReceiptLog
from conftest import (DIGESTS, NOW, PRIVATE, PUBLIC, EXPORT_AUTHORITY_KEYS, broker, fake_sandbox,
                      manifest, native_graph_export, native_graph_export_attestation, staged_receipt_log)


def proposal():
    body = {"schema": "GraphActionProposalV1", "proposal_id": "123e4567-e89b-42d3-a456-426614174099",
            "kind": "GraphCounterAdvanceV1", "args": {"steps": 1}, "input_refs": [],
            "source": {"origin_rule_digest": "sha256:" + "1" * 64,
                       "source_node_type": "NativeRuleEvidenceV1",
                       "source_content_digest": "sha256:" + "2" * 64,
                       "graph_snapshot_digest": DIGESTS["input_snapshot_digest"]},
            "causal_parent_receipt_hash": None,
            "requested_budget": {"wall_ms": 0, "cpu_ms": 0, "memory_bytes": 0, "writes": 0,
                                 "network_bytes": 0}, "graph_logical_time": 1}
    body["proposal_digest"] = object_hash(body)
    return body


def test_p0a_inventory_is_explicit_and_startup_has_no_enabled_methods(tmp_path):
    assert {"world.dispatch_pending_io", "fetch.materialize", "experiment.spawn", "browser.launch_apply",
            "voice.capture_playback", "seed.arbitrary_load", "raw.host.dispatch"} <= set(ROUTE_INVENTORY)
    assert not broker(tmp_path, p0=True).manifest.enabled_methods


def test_staged_worker_routes_valid_proposal_to_default_deny_broker(tmp_path):
    body, native = manifest(), proposal()
    log, control_root = staged_receipt_log(tmp_path, body)
    launcher = fake_sandbox(tmp_path, proposals=(native,))
    with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW),
                         manifest=body, expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC},
                         receipt_log=log, native_graph_export=native_graph_export(native, run_id=body["run_id"]),
                         native_graph_export_attestation=native_graph_export_attestation(
                             native_graph_export(native, run_id=body["run_id"]), run_id=body["run_id"]),
                         native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW,
                         agent_spec=launcher.spec, sandbox_launcher=launcher, control_root=control_root) as run:
        assert not hasattr(run, "action_client")
        assert run.wait(1) == 0
    assert launcher.process is not None
    assert launcher.process.replies[0]["reply"]["phase"] == "denied"
    receipt = json.loads(log.path.read_text())
    assert receipt["outcome"] == "denied" and receipt["reason_code"] == "method_not_enabled"


def test_removed_host_client_is_fail_closed():
    with pytest.raises(ProtocolError, match="isolated worker"):
        EvaluationActionClient().submit_native_graph_proposal({})


def test_malformed_startup_export_is_a_signed_terminal_receipt(tmp_path):
    body = manifest()
    log = ReceiptLog(tmp_path, manifest_hash=object_hash(body), broker_image_digest=DIGESTS["broker_image_digest"],
                     input_digest=DIGESTS["input_snapshot_digest"], signer=PRIVATE, writer_public_key=PUBLIC,
                     now_ms=lambda: NOW)
    with pytest.raises(ProtocolError, match="prelaunch rejected"):
        with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW),
                             manifest=body, expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC},
                             receipt_log=log, native_graph_export=b"{", native_graph_export_attestation=None,
                             native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW):
            pytest.fail("malformed export must not launch")
    assert log.last_receipt["reason_code"] == "invalid_native_graph_export"



def test_missing_worker_heartbeat_kills_the_bound_controller_scope(tmp_path):
    body = manifest()
    log, control_root = staged_receipt_log(tmp_path, body)
    launcher = fake_sandbox(tmp_path, terminal=False)
    export = native_graph_export(run_id=body["run_id"])
    times = iter((100, 100, 102))
    with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW),
                         manifest=body, expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC},
                         receipt_log=log, native_graph_export=export,
                         native_graph_export_attestation=native_graph_export_attestation(export, run_id=body["run_id"], captured_at_unix_ms=100),
                         native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: next(times, 102),
                         agent_spec=launcher.spec, sandbox_launcher=launcher, control_root=control_root,
                         heartbeat_deadline_ms=1) as run:
        assert run.wait(1) == -9
    assert launcher.controller.kills == ["heartbeat_expired"]



def test_fake_controller_precreates_scope_and_covers_attempted_descendants(tmp_path):
    body = manifest()
    log, control_root = staged_receipt_log(tmp_path, body)
    launcher = fake_sandbox(tmp_path, terminal=True)
    export = native_graph_export(run_id=body["run_id"])
    with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW),
                         manifest=body, expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC},
                         receipt_log=log, native_graph_export=export,
                         native_graph_export_attestation=native_graph_export_attestation(export, run_id=body["run_id"]),
                         native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW,
                         agent_spec=launcher.spec, sandbox_launcher=launcher, control_root=control_root) as run:
        assert launcher.scope is not None
        assert launcher.controller.scopes == [launcher.scope]
        assert launcher.scope.run_id == body["run_id"]
        assert launcher.scope.spawned  # scope.spawn, not post-Popen attach, made the worker.
        assert run.wait(1) == 0
        launcher.scope.attempt_descendant(4243)
        launcher.scope.kill("descendant_probe")
    assert launcher.scope.covered_descendants == {4242, 4243}
    assert launcher.scope.kills == ["descendant_probe"]
