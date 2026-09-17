"""Provisioned, evaluator-owned rootless-Podman acceptance gate for P0 isolation.

This is not a product launcher and does not loosen P0's Bubblewrap-only
production contract.  It is skipped unless the exact provisioned acceptance
command requests it; once requested, absent local prerequisites fail closed.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from pathlib import Path

import pytest

from evaluation.p0a.agent_protocol import SCHEMA, write_frame
from evaluation.p0a.canonical import object_hash, sha256, sign
from evaluation.p0a.native_graph_capture import NativeGraphClosureV1, capture_native_graph
from evaluation.p0a.entrypoint import evaluation_mode
from evaluation.p0a.manifest import ManifestVerifier
from conftest import (DIGESTS, EXPORT_AUTHORITY_KEYS, EXPORT_AUTHORITY_PRIVATE, NOW, PRIVATE, PUBLIC, manifest, native_graph_export,
                      native_graph_export_attestation, staged_receipt_log)
from podman_acceptance import (PodmanAcceptanceFailure, PodmanAcceptanceLauncher, ProbeContract,
                               assert_hostile_report, snapshot_sentinels)


pytestmark = pytest.mark.skipif(os.environ.get("P0_RUN_OS_ISOLATION_TESTS") != "1",
                                reason="explicit deployment acceptance command not requested")


def _require_provisioned() -> None:
    assert os.environ.get("P0_OS_ISOLATION_PROVISIONED") == "1", (
        "OS isolation acceptance requires a provisioned local rootless Podman profile; requested gate fails closed")


def _proposal() -> dict:
    value = {"schema": "GraphActionProposalV1", "proposal_id": "123e4567-e89b-42d3-a456-426614174010",
             "kind": "GraphCounterAdvanceV1", "args": {"steps": 1}, "input_refs": [],
             "source": {"origin_rule_digest": "sha256:" + "1" * 64, "source_node_type": "NativeRuleEvidenceV1",
                        "source_content_digest": "sha256:" + "2" * 64,
                        "graph_snapshot_digest": DIGESTS["input_snapshot_digest"]}, "causal_parent_receipt_hash": None,
             "requested_budget": {"wall_ms": 0, "cpu_ms": 0, "memory_bytes": 0, "writes": 0, "network_bytes": 0},
             "graph_logical_time": 7}
    value["proposal_digest"] = object_hash(value)
    return value


def _sentinels(tmp_path: Path) -> tuple[list[Path], Path]:
    nonce = uuid.uuid4().hex
    control, receipt, terminal, result = (tmp_path / name for name in ("control", "receipt", "terminal", "result"))
    for root in (control, receipt, terminal, result): root.mkdir()
    paths = [Path.cwd() / f".p0a-host-sentinel-{nonce}", Path.home() / f".p0a-host-sentinel-{nonce}",
             control / "control-sentinel", receipt / "receipt-sentinel", terminal / "terminal-sentinel", result / "result-sentinel"]
    for path in paths: path.write_text("evaluator-owned-sentinel\n", encoding="utf-8")
    return paths, control


def _contract(mode: str, native_proposal: dict | None, paths: list[Path]) -> ProbeContract:
    # The worker receives a complete graph candidate, not an evaluator-selected
    # opaque ID. The evaluator independently accepts only the candidate bound
    # to its verified export attestation.
    return ProbeContract(mode, native_proposal, tuple(map(str, paths)), 9,
                         (f"/run/user/{os.getuid()}/podman/podman.sock", "/run/podman/podman.sock"))


def _evaluation_kwargs(tmp_path: Path, launcher: PodmanAcceptanceLauncher, proposal: dict):
    body = manifest()
    log, control = staged_receipt_log(tmp_path, body)
    export = native_graph_export(proposal, run_id=body["run_id"])
    return {"manifest_verifier": ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), "manifest": body,
            "expected_digests": DIGESTS, "grant_keys": {"ed25519:test": PUBLIC}, "receipt_log": log,
            "native_graph_export": export,
            "native_graph_export_attestation": native_graph_export_attestation(export, run_id=body["run_id"]),
            "native_export_attestation_keys": EXPORT_AUTHORITY_KEYS, "now_ms": lambda: NOW,
            "agent_spec": launcher.spec(), "sandbox_launcher": launcher, "control_root": control}, log


def test_rootless_podman_hostile_worker_isolation_and_attested_native_graph_gate(tmp_path):
    _require_provisioned()
    paths, _ = _sentinels(tmp_path)
    snapshots = snapshot_sentinels(paths)
    proposal = _proposal()
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract("hostile", proposal, paths))
    kwargs, log = _evaluation_kwargs(tmp_path, launcher, proposal)
    try:
        with evaluation_mode(**kwargs) as run:
            assert run.wait(20) == 0
        process = launcher.controller.scopes[0].process
        assert process is not None
        report = launcher.collect_worker_evidence(process)
        assert_hostile_report(report, proposal_digest=proposal["proposal_digest"])
        assert report["proposal_phases"] == ["denied"]
        launcher.verify_sentinels(snapshots)
        receipt = json.loads(log.path.read_text())
        assert receipt["reason_code"] == "method_not_enabled"
        assert receipt["graph_proposal_digest"] == proposal["proposal_digest"]
        assert receipt["schema"] == "ActionReceiptV3"
        assert receipt["native_export_digest"] == json.loads(kwargs["native_graph_export"])["export_digest"]
        assert isinstance(receipt["native_attestation_digest"], str)
        log.validate()
        launcher.evidence["receipt_hash"] = sha256(log.path.read_bytes())
        launcher.evidence["receipt_provenance"] = {"proposal_digest": proposal["proposal_digest"],
                                                    "native_export_digest": receipt["native_export_digest"],
                                                    "native_attestation_digest": receipt["native_attestation_digest"]}
        launcher._write_evidence()
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)


def test_rootless_podman_forged_authority_frame_is_terminal(tmp_path):
    _require_provisioned()
    paths, _ = _sentinels(tmp_path)
    proposal = _proposal()
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract("forged", None, paths))
    kwargs, log = _evaluation_kwargs(tmp_path, launcher, proposal)
    try:
        with evaluation_mode(**kwargs) as run:
            run.wait(20)
        runtime = json.loads(run.run_paths.runtime_failure_path.read_text())
        assert runtime["reason_code"] == "sandbox_protocol_violation"
        assert log.sequence == 0
        launcher.evidence["runtime_record_hash"] = sha256(run.run_paths.runtime_failure_path.read_bytes())
        launcher.evidence["accepted_effects"] = 0
        launcher._write_evidence()
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)


def test_rootless_podman_stop_kills_container_and_descendant(tmp_path):
    _require_provisioned()
    paths, _ = _sentinels(tmp_path)
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract("stop", None, paths))
    spec = launcher.spec()
    try:
        launcher.preflight(spec)
        launcher.build(spec)
        scope = launcher.controller.create_scope("123e4567-e89b-42d3-a456-426614174000")
        wrapped = launcher.start(spec, scope)
        write_frame(wrapped.process.stdin, {"schema": SCHEMA, "type": "hello", "run_id": scope.run_id, "session_nonce": "A" * 64})
        ready = wrapped.process.stderr.readline().decode("utf-8", "replace")
        assert json.loads(ready)["ready"] is True
        live = launcher.top()
        assert len(live) >= 2
        init_pid = launcher.evidence["inspect"]["State"]["Pid"]
        cgroup_file = Path(f"/proc/{init_pid}/cgroup")
        launcher.evidence["live_cgroup"] = cgroup_file.read_text(encoding="utf-8")
        launcher.stop_container()
        wrapped.process.wait(timeout=10)
        launcher.verify_stopped()
        launcher.evidence["stop_profile"] = "podman stop --time 2"
        launcher._write_evidence()
    except PodmanAcceptanceFailure:
        raise
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)



@pytest.mark.parametrize(("mode", "expected_reasons"), [
    ("forged_proposal", ["forged_graph_provenance"]),
    ("mismatched_proposal", ["forged_graph_provenance"]),
    ("replay_proposal", ["method_not_enabled", "replay"]),
])
def test_rootless_podman_native_graph_adversaries_are_signed_default_denials(tmp_path, mode, expected_reasons):
    """Each malicious candidate uses a fresh hardened container and retained evidence."""
    _require_provisioned()
    paths, _ = _sentinels(tmp_path)
    snapshots = snapshot_sentinels(paths)
    proposal = _proposal()
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract(mode, proposal, paths))
    kwargs, log = _evaluation_kwargs(tmp_path, launcher, proposal)
    try:
        with evaluation_mode(**kwargs) as run:
            assert run.wait(20) == 0
        process = launcher.controller.scopes[0].process
        assert process is not None
        report = launcher.collect_worker_evidence(process)
        assert_hostile_report(report)
        launcher.verify_sentinels(snapshots)
        receipts = [json.loads(line) for line in log.path.read_bytes().splitlines()]
        assert [receipt["reason_code"] for receipt in receipts] == expected_reasons
        assert all(receipt["outcome"] == "denied" for receipt in receipts)
        # A mismatch is deliberately not claimed as attested provenance.  The
        # signed denial is still chained; only a verified candidate receives
        # an ActionReceiptV3 export/attestation binding.
        if mode == "replay_proposal":
            assert receipts[0]["schema"] == "ActionReceiptV3"
            assert receipts[0]["native_export_digest"] == json.loads(kwargs["native_graph_export"])["export_digest"]
            assert isinstance(receipts[0]["native_attestation_digest"], str)
        else:
            assert receipts[0]["schema"] == "ActionReceiptV2"
        assert log.validate() == (len(receipts), receipts[-1]["receipt_hash"])
        launcher.evidence["adversarial_proposal_case"] = {"mode": mode, "reasons": expected_reasons,
                                                            "receipt_hashes": [receipt["receipt_hash"] for receipt in receipts],
                                                            "accepted_effects": 0}
        launcher._write_evidence()
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)



# P1 dynamic-native path.  The evaluator reconstructs and signs its own
# export before evaluation_mode is entered; these tests never use worker bytes
# as an export source.
def _native_closure(tmp_path: Path) -> NativeGraphClosureV1:
    root = tmp_path / "native-closure"
    (root / "substrate_rs").mkdir(parents=True)
    native = Path(__file__).parents[2] / "runners/dsl/python/substrate_rs"
    fixture = Path(__file__).parent / "fixtures/podman_acceptance"
    for name in ("__init__.py", "_native.abi3.so"):
        shutil.copyfile(native / name, root / "substrate_rs" / name)
    for name in ("native_graph_proposal_seed.json", "native_sealed_graph_action_fact.json", "native_graph_entrypoint.py"):
        shutil.copyfile(fixture / name, root / name)
    return NativeGraphClosureV1.from_root(root)


def _dynamic_evaluation_kwargs(tmp_path: Path, launcher: PodmanAcceptanceLauncher, closure: NativeGraphClosureV1):
    expected = {**DIGESTS, "agent_build_digest": closure.closure_digest,
                "input_snapshot_digest": closure.files["native_sealed_graph_action_fact.json"]}
    body = manifest()
    body.update({"agent_build_digest": expected["agent_build_digest"], "input_snapshot_digest": expected["input_snapshot_digest"]})
    body["signature"] = sign(body, PRIVATE)
    log, control = staged_receipt_log(tmp_path, body)
    capture = capture_native_graph(closure=closure, run_id=body["run_id"], agent_build_digest=closure.closure_digest,
        control_plane_digest=expected["control_plane_digest"], input_snapshot_digest=expected["input_snapshot_digest"],
        now_ms=NOW, expires_at_unix_ms=10_000, signer=EXPORT_AUTHORITY_PRIVATE,
        key_id="ed25519:local-test-authority")
    kwargs = {"manifest_verifier": ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW), "manifest": body,
              "expected_digests": expected, "grant_keys": {"ed25519:test": PUBLIC}, "receipt_log": log,
              "native_graph_export": capture.native_graph_export,
              "native_graph_export_attestation": capture.native_graph_export_attestation,
              "native_export_attestation_keys": EXPORT_AUTHORITY_KEYS, "now_ms": lambda: NOW,
              "agent_spec": launcher.spec(), "sandbox_launcher": launcher, "control_root": control}
    return kwargs, log, capture


def test_rootless_podman_dynamic_native_proposal_is_independently_captured_and_mediated(tmp_path):
    _require_provisioned()
    paths, _ = _sentinels(tmp_path); snapshots = snapshot_sentinels(paths)
    closure = _native_closure(tmp_path)
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract("dynamic_native", None, paths), native_closure=closure)
    try:
        kwargs, log, capture = _dynamic_evaluation_kwargs(tmp_path, launcher, closure)
        with evaluation_mode(**kwargs) as run:
            assert run.wait(20) == 0
        report = launcher.collect_worker_evidence(launcher.controller.scopes[0].process)
        proposal = json.loads(capture.native_graph_export)["evidence"][0]["proposal"]
        assert_hostile_report(report, proposal_digest=proposal["proposal_digest"])
        launcher.verify_sentinels(snapshots)
        receipt = json.loads(log.path.read_text())
        assert receipt["reason_code"] == "method_not_enabled"
        assert receipt["native_export_digest"] == json.loads(capture.native_graph_export)["export_digest"]
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)


def test_rootless_podman_dynamic_native_candidate_substitution_is_signed_denial(tmp_path):
    _require_provisioned()
    paths, _ = _sentinels(tmp_path); closure = _native_closure(tmp_path)
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract("candidate_substitution", None, paths), native_closure=closure)
    try:
        kwargs, log, _ = _dynamic_evaluation_kwargs(tmp_path, launcher, closure)
        with evaluation_mode(**kwargs) as run: assert run.wait(20) == 0
        assert json.loads(log.path.read_text())["reason_code"] == "forged_graph_provenance"
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)


def test_rootless_podman_dynamic_native_candidate_replay_is_signed_denial(tmp_path):
    _require_provisioned()
    paths, _ = _sentinels(tmp_path); closure = _native_closure(tmp_path)
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract("candidate_replay", None, paths), native_closure=closure)
    try:
        kwargs, log, _ = _dynamic_evaluation_kwargs(tmp_path, launcher, closure)
        with evaluation_mode(**kwargs) as run: assert run.wait(20) == 0
        assert [json.loads(line)["reason_code"] for line in log.path.read_bytes().splitlines()] == ["method_not_enabled", "replay"]
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)


def test_rootless_podman_dynamic_native_export_frame_substitution_is_terminal(tmp_path):
    _require_provisioned()
    paths, _ = _sentinels(tmp_path); closure = _native_closure(tmp_path)
    launcher = PodmanAcceptanceLauncher(tmp_path, contract=_contract("export_frame_substitution", None, paths), native_closure=closure)
    try:
        kwargs, log, _ = _dynamic_evaluation_kwargs(tmp_path, launcher, closure)
        with evaluation_mode(**kwargs) as run: run.wait(20)
        assert json.loads(run.run_paths.runtime_failure_path.read_text())["reason_code"] == "sandbox_protocol_violation"
        assert log.sequence == 0
    finally:
        launcher.cleanup()
        for path in paths: path.unlink(missing_ok=True)


@pytest.mark.parametrize("failure", ["missing_native_module", "bad_native_digest", "abi_import_failure"])
def test_rootless_podman_dynamic_native_missing_closure_or_abi_fails_prelaunch(tmp_path, failure):
    _require_provisioned()
    closure = _native_closure(tmp_path)
    target = closure.root / "substrate_rs/_native.abi3.so"
    if failure == "missing_native_module":
        target.unlink()
    elif failure == "bad_native_digest":
        target.write_bytes(target.read_bytes() + b"x")
    else:
        target.write_bytes(b"not a native extension")
    with pytest.raises(Exception, match="native_closure_unavailable|invalid_native_capture"):
        _dynamic_evaluation_kwargs(tmp_path, PodmanAcceptanceLauncher(tmp_path, contract=_contract("dynamic_native", None, []), native_closure=closure), closure)
