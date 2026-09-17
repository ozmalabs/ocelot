from pathlib import Path

import pytest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.canonical import canonical_bytes, parse_canonical

from evaluation.p4.evaluator import P4R0Evaluator
from evaluation.p4.podman import P4PodmanLauncher
from evaluation.p4.protocol import P4ProtocolError
from evaluation.p4.receipts import P4ReceiptLog
from evaluation.p4.runner import run_local
from evaluation.p4.runtime import measure_runtime_closure, validate_runtime_closure
from evaluation.p4.seccomp import validate_seccomp_profile
from evaluation.p4.staging import digest_file
from evaluation.p4.tests.helpers import local_lock, staged_spec


def test_canonical_snapshot_restore_breaks_nested_aliases_and_resets_side_state():
    evaluator = P4R0Evaluator(b"seed", {"nested": {"items": ["before"]}})
    evaluator.graph["nested"]["items"].append("mutated")
    evaluator.reserved["actions"] = 3
    evaluator.simulator_calls = 2
    evaluator.grants["stale"] = {"value": [1]}
    restored = evaluator.restore()
    assert restored == evaluator.pre_run_graph_snapshot_digest
    assert evaluator.graph == {"nested": {"items": ["before"]}}
    assert evaluator.reserved == {"actions": 0, "risk": 0, "transactions": 0}
    assert evaluator.simulator_calls == 0 and evaluator.grants == {}
    with pytest.raises(TypeError):
        evaluator._snapshot["nested"] = {}  # type: ignore[index]


def test_seccomp_rejects_unavailable_permissive_profile(tmp_path):
    profile = tmp_path / "seccomp.json"
    profile.write_text("{}")
    with pytest.raises(P4ProtocolError):
        validate_seccomp_profile(profile)
    validate_seccomp_profile(Path(__file__).parents[1] / "seccomp.json")


def test_seccomp_rejects_extra_syscall_and_duplicate_broad_rules(tmp_path):
    source = Path(__file__).parents[1] / "seccomp.json"
    profile = parse_canonical(source.read_bytes())
    profile["syscalls"][0]["names"] = sorted(profile["syscalls"][0]["names"] + ["mount"])
    extra = tmp_path / "extra.json"
    extra.write_bytes(canonical_bytes(profile))
    with pytest.raises(P4ProtocolError):
        validate_seccomp_profile(extra)

    duplicate = parse_canonical(source.read_bytes())
    duplicate["syscalls"].append({"action": "SCMP_ACT_ALLOW", "names": ["read"]})
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_bytes(canonical_bytes(duplicate))
    with pytest.raises(P4ProtocolError):
        validate_seccomp_profile(duplicate_path)


def test_seccomp_rejects_unknown_action_and_architecture(tmp_path):
    source = Path(__file__).parents[1] / "seccomp.json"
    for name, mutate in (("action", lambda p: p["syscalls"][0].__setitem__("action", "SCMP_ACT_LOG")),
                         ("architecture", lambda p: p["archMap"][0].__setitem__("architecture", "SCMP_ARCH_ARM"))):
        profile = parse_canonical(source.read_bytes())
        mutate(profile)
        target = tmp_path / f"{name}.json"
        target.write_bytes(canonical_bytes(profile))
        with pytest.raises(P4ProtocolError):
            validate_seccomp_profile(target)


def test_seccomp_keeps_measured_startup_set_exact(tmp_path, monkeypatch):
    source = Path(__file__).parents[1] / "seccomp.json"
    profile = parse_canonical(source.read_bytes())
    profile["syscalls"][0]["names"].remove("access")
    target = tmp_path / "missing-measured.json"
    target.write_bytes(canonical_bytes(profile))
    worker = tmp_path / "worker"
    worker.write_bytes(b"\x7fELF")
    monkeypatch.setattr("evaluation.p4.seccomp._probe_syscalls", lambda _: {"access"})
    with pytest.raises(P4ProtocolError):
        validate_seccomp_profile(target, worker=worker)

    _, spec = staged_spec(tmp_path)
    signer = Ed25519PrivateKey.generate()
    log = P4ReceiptLog(tmp_path / "receipts", signer)
    evaluator = P4R0Evaluator(b"seed", {"nested": {"items": [1]}})
    lock = local_lock(tmp_path, spec)
    result = run_local(lock, evaluator, log, podman_spec=spec, launcher=P4PodmanLauncher())
    rollback = log.get(result["rollback_receipt_digest"])
    assert rollback["kind"] == "rollback"
    assert rollback["payload"]["binding"] == {
        "pre_run_snapshot_digest": evaluator.pre_run_graph_snapshot_digest,
        "restored_snapshot_digest": result["rollback_digest"],
        "snapshot_encoding": "canonical-deep",
    }


def test_native_runtime_manifest_is_finite_and_lockable_when_worker_exists(tmp_path):
    worker = Path(__file__).parents[3] / "runners" / "dsl" / "target" / "debug" / "p4_native_readiness_worker"
    if not worker.is_file():
        pytest.skip("offline native worker has not been built")
    manifest = measure_runtime_closure(worker)
    assert manifest["schema"] == "P4R0NativeRuntimeClosureV1"
    assert any(entry["path"] == "/lib64/ld-linux-x86-64.so.2" for entry in manifest["files"])
    assert any(entry["path"] == "/etc/ld.so.cache" for entry in manifest["support_files"])
    # A manifest digest is the exact lock input, not a host lookup at launch.
    lock_manifest = tmp_path / "runtime-closure.json"
    lock_manifest.write_bytes(__import__("evaluation.p0a.canonical", fromlist=["canonical_bytes"]).canonical_bytes(manifest))
    try:
        assert validate_runtime_closure(lock_manifest, worker_digest=digest_file(worker))["binary_digest"] == digest_file(worker)
    finally:
        lock_manifest.unlink()
