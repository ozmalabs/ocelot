"""Terminal receipt failures are observed through the staged protocol, not host clients."""
from __future__ import annotations

from evaluation.p0a.canonical import object_hash
from evaluation.p0a.entrypoint import evaluation_mode
from evaluation.p0a.manifest import ManifestVerifier
from evaluation.p0a.runtime_failure import RuntimeFailureRecord
from evaluation.p0a.simulator import METHOD
from conftest import (DIGESTS, NOW, PRIVATE, PUBLIC, EXPORT_AUTHORITY_KEYS, fake_sandbox, grant, manifest,
                      native_graph_export, native_graph_export_attestation, raw, staged_receipt_log)


def proposal():
    value = {"schema": "GraphActionProposalV1", "proposal_id": "123e4567-e89b-42d3-a456-426614174099",
             "kind": "GraphCounterAdvanceV1", "args": {"steps": 1}, "input_refs": [],
             "source": {"origin_rule_digest": "sha256:" + "1" * 64, "source_node_type": "NativeRuleEvidenceV1",
             "source_content_digest": "sha256:" + "2" * 64, "graph_snapshot_digest": DIGESTS["input_snapshot_digest"]},
             "causal_parent_receipt_hash": None, "requested_budget": {"wall_ms": 0, "cpu_ms": 0,
             "memory_bytes": 0, "writes": 0, "network_bytes": 0}, "graph_logical_time": 1}
    value["proposal_digest"] = object_hash(value)
    return value


def test_receipt_append_failure_is_terminal_and_kills_fake_scope(tmp_path):
    body, native = manifest(methods=(METHOD,)), proposal()
    log, control = staged_receipt_log(tmp_path, body)
    runtime = RuntimeFailureRecord.for_run_paths(log.run_paths, log, now_ms=lambda: NOW)
    log._replace = lambda *_args: (_ for _ in ()).throw(OSError("head publication failed"))
    launcher = fake_sandbox(tmp_path, proposals=(native,))
    export = native_graph_export(native, run_id=body["run_id"])
    with evaluation_mode(manifest_verifier=ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), manifest=body,
                         expected_digests=DIGESTS, grant_keys={"ed25519:test": PUBLIC}, receipt_log=log,
                         native_graph_export=export, native_graph_export_attestation=native_graph_export_attestation(export, run_id=body["run_id"]),
                         native_export_attestation_keys=EXPORT_AUTHORITY_KEYS, now_ms=lambda: NOW, runtime_failure_record=runtime,
                         allow_fixture_methods=True, fixture_registry=True, grant_resolver=lambda request: raw(grant(request)),
                         agent_spec=launcher.spec, sandbox_launcher=launcher, control_root=control) as run:
        assert run.wait(1) == -9
    assert launcher.controller.kills == ["receipt_append_failed"]
    assert runtime.read()["reason_code"] == "receipt_append_failed"
