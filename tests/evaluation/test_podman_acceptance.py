"""Deterministic unit tests for the evaluator-owned Podman profile builder."""
from __future__ import annotations

from pathlib import Path

import pytest

from podman_acceptance import (BASE_IMAGE_ID, CFFI_BACKEND_EXTENSION, CRYPTOGRAPHY_RUNTIME_MANIFEST, EXACT_ID_MAPPINGS, FORBIDDEN_RUN_FLAGS,
                               PodmanAcceptanceFailure, PodmanAcceptanceLauncher, ProbeContract,
                               WORKER_INTERPRETER_PATHS, WORKER_RUNTIME_FILES)


def _launcher(tmp_path: Path) -> PodmanAcceptanceLauncher:
    return PodmanAcceptanceLauncher(tmp_path, contract=ProbeContract("hostile", "proposal", ("/sentinel",), 1,
        ("/run/user/1000/podman/podman.sock", "/run/podman/podman.sock")))


def test_podman_command_is_deterministic_and_has_no_control_mounts(tmp_path):
    launcher = _launcher(tmp_path)
    spec = launcher.spec()
    command = launcher.run_command()
    assert command[:7] == ["podman", "run", "--name", launcher.name, "--pull=never", "--network=none", "--read-only"]
    assert ["--tmpfs", "/workspace:rw,nosuid,nodev,noexec,size=64m,mode=0700"] == command[command.index("--tmpfs"):command.index("--tmpfs") + 2]
    assert ["--uidmap=0:1:65536", "--gidmap=0:1:65536", "--user", "65534:65534"] == command[command.index("--uidmap=0:1:65536"):command.index("--uidmap=0:1:65536") + 4]
    assert "--userns" not in command
    assert command[-1] == launcher.tag and BASE_IMAGE_ID not in command
    assert not any(flag in command for flag in FORBIDDEN_RUN_FLAGS)
    rendered = " ".join(command)
    for forbidden in ("--volume", "--mount", "podman.sock", str(Path.cwd()), "--env-host"):
        assert forbidden not in rendered
    build = launcher.build_command()
    assert build[:7] == ["podman", "build", "--pull=never", "--network=none", "--http-proxy=false", "--layers=false", "--file"]
    assert build[-1] == str(launcher.context)


def test_staged_worker_manifest_is_finite_and_complete(tmp_path):
    launcher = _launcher(tmp_path)
    launcher._stage(launcher.spec())
    staged = {item["path"] for item in launcher.evidence["build_inputs"] if item["path"] in WORKER_RUNTIME_FILES}
    assert tuple(launcher.evidence["worker_runtime_manifest"]) == WORKER_RUNTIME_FILES
    assert staged == set(WORKER_RUNTIME_FILES)
    assert not (launcher.context / "evaluation/p0a/sandbox.py").exists()


def test_inspect_profile_rejects_bind_mount_or_missing_hardening():
    accepted = {"Config": {"User": "65534:65534"}, "HostConfig": {"IDMappings": EXACT_ID_MAPPINGS,
        "ReadonlyRootfs": True, "PidMode": "private", "IpcMode": "private", "UTSMode": "private",
        "CgroupMode": "private", "UsernsMode": "private", "NetworkMode": "none", "Privileged": False, "CapAdd": [],
        "NoNewPrivileges": True, "PidsLimit": 64, "Memory": 268435456, "MemorySwap": 268435456,
        "NanoCpus": 500000000, "SecurityOpt": ["no-new-privileges", "seccomp=/usr/share/containers/seccomp.json"],
        "Ulimits": [{"Name": "RLIMIT_NOFILE", "Soft": 128, "Hard": 128},
                    {"Name": "RLIMIT_NPROC", "Soft": 64, "Hard": 64}], "LogConfig": {"Type": "none"},
        "Tmpfs": {"/workspace": "rw,nosuid,nodev,noexec,size=64m,mode=0700"}},
        "State": {"Running": True}, "EffectiveCaps": None, "Mounts": [{"Type": "tmpfs", "Destination": "/workspace", "RW": True}]}
    PodmanAcceptanceLauncher._assert_inspect(accepted)
    rejected = {**accepted, "Mounts": [{"Type": "bind", "Destination": "/agent", "Source": "/host", "RW": False}]}
    with pytest.raises(PodmanAcceptanceFailure, match="bind/volume"):
        PodmanAcceptanceLauncher._assert_inspect(rejected)
    rejected_mapping = {**accepted, "HostConfig": {**accepted["HostConfig"], "IDMappings": {
        "UidMap": ["0:0:65536"], "GidMap": EXACT_ID_MAPPINGS["GidMap"]}}}
    with pytest.raises(PodmanAcceptanceFailure, match="ID mappings"):
        PodmanAcceptanceLauncher._assert_inspect(rejected_mapping)
    rejected_namespace = {**accepted, "HostConfig": {**accepted["HostConfig"], "PidMode": "host"}}
    with pytest.raises(PodmanAcceptanceFailure, match="namespace isolation"):
        PodmanAcceptanceLauncher._assert_inspect(rejected_namespace)



def test_cryptography_fallback_manifest_is_explicit_and_rooted(tmp_path):
    launcher = _launcher(tmp_path)
    launcher._stage(launcher.spec())
    runtime = launcher.evidence["third_party_runtime"]
    assert runtime["package"] == "cryptography"
    assert tuple(runtime["manifest"]) == CRYPTOGRAPHY_RUNTIME_MANIFEST
    staged = {item["path"] for item in runtime["files"]}
    assert staged == {f"site-packages/cryptography/{path}" for path in CRYPTOGRAPHY_RUNTIME_MANIFEST} | {
        f"site-packages/{CFFI_BACKEND_EXTENSION}"}
    assert all(not path.startswith("site-packages/cffi/") for path in staged)
    assert runtime["staging_interpreter"]["version"] == [3, 13]
    assert runtime["staging_interpreter"]["executable"]


def test_cleanup_lists_exact_prefixed_artifacts_before_removing_them(tmp_path, monkeypatch):
    launcher = _launcher(tmp_path)
    calls = []
    inventory_calls = {"containers": 0, "images": 0}

    class Completed:
        def __init__(self, stdout=b"", returncode=0):
            self.stdout, self.stderr, self.returncode = stdout, b"", returncode

    def fake_run(command, **_kwargs):
        calls.append(command)
        if command[:3] == ["podman", "ps", "-a"]:
            inventory_calls["containers"] += 1
            return Completed((launcher.name + "\n").encode() if inventory_calls["containers"] == 1 else b"")
        if command[:3] == ["podman", "image", "ls"]:
            inventory_calls["images"] += 1
            return Completed((launcher.tag + "\n").encode() if inventory_calls["images"] == 1 else b"")
        return Completed()

    monkeypatch.setattr("podman_acceptance.subprocess.run", fake_run)
    launcher.cleanup()
    assert launcher.evidence["cleanup"]["prefix_confirmed"] is True
    assert launcher.evidence["cleanup"]["before"] == {"containers": [launcher.name], "container_count": 1,
                                                         "images": [launcher.tag], "image_count": 1}
    assert ["podman", "stop", "--time", "2", launcher.name] in calls
    assert ["podman", "rm", launcher.name] in calls
    assert ["podman", "rmi", launcher.tag] in calls
    assert launcher.evidence["cleanup"]["after"]["container_count"] == 0
    assert launcher.evidence["cleanup"]["after"]["image_count"] == 0


def test_import_closure_checks_each_pinned_image_interpreter(tmp_path):
    launcher = _launcher(tmp_path)
    launcher.derived_image_id = "sha256:" + "1" * 64
    commands = [launcher.import_check_command(interpreter) for interpreter in WORKER_INTERPRETER_PATHS]
    assert [command[command.index("--entrypoint") + 1] for command in commands] == list(WORKER_INTERPRETER_PATHS)
    assert all(command[-3:] [0] == "-I" for command in commands)
