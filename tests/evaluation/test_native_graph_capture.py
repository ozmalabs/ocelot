from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from conftest import DIGESTS, EXPORT_AUTHORITY_PRIVATE, NOW
from evaluation.p0a.canonical import ProtocolError, parse_canonical, sha256
from evaluation.p0a.native_graph_capture import NativeGraphClosureV1, capture_native_graph
from evaluation.p0a.provenance import NativeGraphExportAttestationVerifier


FIXTURES = Path(__file__).parent / "fixtures/podman_acceptance"
NATIVE = Path(__file__).parents[2] / "runners/dsl/python/substrate_rs"


def _closure(tmp_path: Path) -> NativeGraphClosureV1:
    root = tmp_path / "closure"
    (root / "substrate_rs").mkdir(parents=True)
    for name in ("__init__.py", "_native.abi3.so"):
        shutil.copyfile(NATIVE / name, root / "substrate_rs" / name)
    for name in ("native_graph_proposal_seed.json", "native_sealed_graph_action_fact.json", "native_graph_entrypoint.py"):
        shutil.copyfile(FIXTURES / name, root / name)
    return NativeGraphClosureV1.from_root(root)


def _capture(closure: NativeGraphClosureV1):
    return capture_native_graph(closure=closure, run_id="123e4567-e89b-42d3-a456-426614174000",
        agent_build_digest=closure.closure_digest, control_plane_digest=DIGESTS["control_plane_digest"],
        input_snapshot_digest=closure.files["native_sealed_graph_action_fact.json"], now_ms=NOW,
        expires_at_unix_ms=10_000, signer=EXPORT_AUTHORITY_PRIVATE, key_id="ed25519:local-test-authority")


def test_capture_reconstructs_one_attestable_native_proposal(tmp_path):
    closure = _closure(tmp_path)
    capture = _capture(closure)
    export = parse_canonical(capture.native_graph_export)
    assert len(export["evidence"]) == 1
    proposal = export["evidence"][0]["proposal"]
    assert proposal["kind"] == "GraphCounterAdvanceV1"
    assert proposal["args"] == {"steps": 1}
    assert proposal["proposal_digest"] == export["evidence"][0]["proposal_digest"]


def test_capture_rejects_missing_native_closure_before_export(tmp_path):
    closure = _closure(tmp_path)
    (closure.root / "substrate_rs/_native.abi3.so").unlink()
    with pytest.raises(ProtocolError, match="native_closure_unavailable"):
        _capture(closure)


def test_capture_rejects_abi_or_loaded_path_mismatch_before_export(tmp_path):
    closure = _closure(tmp_path)
    (closure.root / "substrate_rs/_native.abi3.so").write_bytes(b"not an extension")
    with pytest.raises(ProtocolError, match="native_closure_unavailable"):
        _capture(closure)


@pytest.mark.parametrize("mutate", ["zero", "invalid"])
def test_capture_rejects_zero_multiple_or_invalid_proposals(tmp_path, monkeypatch, mutate):
    closure = _closure(tmp_path)
    if mutate == "zero":
        seed = closure.root / "native_graph_proposal_seed.json"
        seed.write_text('{"id":"empty","version":"1","depends_on":[],"nodes":[],"edges":[],"productions":[],"rules":[]}', encoding="utf-8")
    else:
        facts = closure.root / "native_sealed_graph_action_fact.json"
        facts.write_text(facts.read_text(encoding="utf-8").replace('"steps": 1', '"steps": 101'), encoding="utf-8")
    changed = NativeGraphClosureV1.from_root(closure.root)
    with pytest.raises(ProtocolError, match="invalid_native_capture"):
        _capture(changed)


def test_capture_rejects_two_fresh_reconstructions_that_disagree(tmp_path, monkeypatch):
    closure = _closure(tmp_path)
    import evaluation.p0a.native_graph_capture as subject
    real = subject._reconstruct
    calls = []
    def differing(value):
        proposal = real(value)
        calls.append(proposal)
        if len(calls) == 2:
            proposal = dict(proposal); proposal["graph_logical_time"] += 1
            proposal["proposal_digest"] = "sha256:" + "0" * 64
        return proposal
    monkeypatch.setattr(subject, "_reconstruct", differing)
    with pytest.raises(ProtocolError, match="native_capture_disagreement"):
        _capture(closure)


def test_capture_attestation_binds_run_build_control_and_input_digests(tmp_path):
    closure = _closure(tmp_path)
    capture = _capture(closure)
    verifier = NativeGraphExportAttestationVerifier({"ed25519:local-test-authority": EXPORT_AUTHORITY_PRIVATE.public_key()}, now_ms=lambda: NOW)
    verifier.verify(capture.native_graph_export, capture.native_graph_export_attestation,
                    run_id="123e4567-e89b-42d3-a456-426614174000", agent_build_digest=closure.closure_digest,
                    control_plane_digest=DIGESTS["control_plane_digest"],
                    input_snapshot_digest=closure.files["native_sealed_graph_action_fact.json"])
    assert capture.closure_manifest["closure_digest"] == closure.closure_digest
