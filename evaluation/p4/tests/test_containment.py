import os
import os
import subprocess
import pytest

from evaluation.p4.podman import (P4PodmanLauncher, PodmanPolicyUnavailable,
                                   PROCFS_STARTUP_EVIDENCE, build_local_image,
                                   build_procfs_profile,
                                   validate_image_context)
from evaluation.p4.protocol import P4ProtocolError
from evaluation.p4.runner import _invoke_native_worker
from evaluation.p4.staging import closure_digests, validate_closure
from evaluation.p4.tests.helpers import staged_spec

def test_fixed_offline_rootless_command(tmp_path):
    _, spec = staged_spec(tmp_path)
    expected = closure_digests(spec.staging_root, spec.closure_artifacts())
    argv = P4PodmanLauncher().argv(spec, expected)
    assert "--pull=never" in argv and "--network=none" in argv and "--read-only" in argv
    assert "--pid=private" in argv
    assert "--cap-drop=ALL" in argv and "--security-opt=no-new-privileges" in argv
    assert not any(option.startswith("--volume") or option.startswith("--mount")
                   for option in argv)
    assert not any(option.startswith("--tmpfs") or option.startswith("--workdir")
                   for option in argv)
    assert "--privileged" not in argv and argv[-1] == "/runtime/p4_native_readiness_worker"


def test_procfs_profile_is_private_only_and_has_no_host_escape():
    profile = build_procfs_profile()
    assert profile == ("--pid=private",)
    assert "--pid=host" not in profile
    assert all(not option.startswith("--volume=/proc") for option in profile)

def test_procfs_startup_failure_is_preserved_as_fail_closed_evidence(monkeypatch):
    class StubLauncher:
        def argv(self, *_args):
            return ["podman"]

    def failed_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(["podman"], 255, b"", PROCFS_STARTUP_EVIDENCE.encode())

    monkeypatch.setattr("evaluation.p4.runner.subprocess.run", failed_run)
    with pytest.raises(PodmanPolicyUnavailable, match="procfs startup unavailable") as error:
        _invoke_native_worker(StubLauncher(), object(), {"closure": {}, "trusted_evaluator_digest": ""}, {})
    assert PROCFS_STARTUP_EVIDENCE in str(error.value)


def test_closure_rejects_substitution_extra_file_and_symlink(tmp_path):
    root, spec = staged_spec(tmp_path)
    expected = closure_digests(root, spec.closure_artifacts())
    spec.worker_binary.write_text("substituted")
    with pytest.raises(P4ProtocolError):
        validate_closure(root, spec.closure_artifacts(), expected)
    spec.worker_binary.write_text("#!/bin/sh\nexit 0\n")
    spec.worker_binary.chmod(0o755)
    (spec.input_root / "unlocked").write_text("extra")
    with pytest.raises(P4ProtocolError):
        validate_closure(root, spec.closure_artifacts(), expected)
    (spec.input_root / "unlocked").unlink()
    os.symlink(spec.input_root / "fixture.json", spec.input_root / "linked")
    with pytest.raises(P4ProtocolError):
        validate_closure(root, spec.closure_artifacts(), expected)

def test_spec_rejects_container_spec_outside_staging(tmp_path):
    _, spec = staged_spec(tmp_path)
    object.__setattr__(spec, "container_spec", tmp_path / "outside")
    (tmp_path / "outside").write_text("FROM scratch")
    with pytest.raises(PodmanPolicyUnavailable):
        spec.validate()



def test_embedded_context_requires_fixed_worker_trust_input_and_runtime_paths(tmp_path):
    context = tmp_path / "context"
    (context / "trust").mkdir(parents=True)
    (context / "input").mkdir()
    for directory in ("lib", "lib64", "etc"):
        (context / directory).mkdir()
    (context / "p4_native_readiness_worker").write_text("worker")
    (context / "trust" / "p4-trusted-evaluator.json").write_text("trust")
    (context / "input" / "p4_r0_public_bundle_v1.json").write_text("fixture")
    (context / "runtime-closure.json").write_text("closure")
    (context / "Containerfile").write_text(
        "FROM scratch\n"
        "COPY p4_native_readiness_worker /runtime/p4_native_readiness_worker\n"
        "COPY lib/ /lib/\n"
        "COPY lib64/ /lib64/\n"
        "COPY etc/ /etc/\n"
        "COPY trust/p4-trusted-evaluator.json /trust/p4-trusted-evaluator.json\n"
        "COPY input/p4_r0_public_bundle_v1.json /input/p4_r0_public_bundle_v1.json\n"
        "USER 65532:65532\n"
    )
    validate_image_context(context)
    (context / "input" / "p4_r0_public_bundle_v1.json").unlink()
    with pytest.raises(PodmanPolicyUnavailable, match="missing embedded image path"):
        validate_image_context(context)



def test_stdio_input_is_bounded_before_startup(monkeypatch):
    called = False

    def forbidden_run(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("worker must not start for oversized frame")

    monkeypatch.setattr("evaluation.p4.runner.subprocess.run", forbidden_run)
    from evaluation.p4.runner import _invoke_native_worker
    with pytest.raises(P4ProtocolError, match="input frame bound"):
        _invoke_native_worker(object(), object(), {"closure": {}, "trusted_evaluator_digest": ""},
                              {"payload": "x" * 70000})
    assert not called



def test_local_image_build_is_pullless_networkless_and_digest_pinned(tmp_path, monkeypatch):
    context = tmp_path / "context"
    (context / "trust").mkdir(parents=True)
    (context / "input").mkdir()
    for directory in ("lib", "lib64", "etc"):
        (context / directory).mkdir()
    for relative in ("p4_native_readiness_worker", "trust/p4-trusted-evaluator.json",
                     "input/p4_r0_public_bundle_v1.json", "runtime-closure.json"):
        (context / relative).write_text(relative)
    (context / "Containerfile").write_text(
        "FROM scratch\n"
        "COPY p4_native_readiness_worker /runtime/p4_native_readiness_worker\n"
        "COPY lib/ /lib/\nCOPY lib64/ /lib64/\nCOPY etc/ /etc/\n"
        "COPY trust/p4-trusted-evaluator.json /trust/p4-trusted-evaluator.json\n"
        "COPY input/p4_r0_public_bundle_v1.json /input/p4_r0_public_bundle_v1.json\n"
        "USER 65532:65532\n"
    )
    digest = "sha256:" + "d" * 64
    commands = []
    monkeypatch.setattr("evaluation.p4.podman.shutil.which", lambda _: "/bin/true")

    def fake_run(command, **_kwargs):
        commands.append(command)
        if command[1] == "build":
            return subprocess.CompletedProcess(command, 0, b"", b"")
        if "{{.Id}}" in command:
            return subprocess.CompletedProcess(command, 0, (digest + "\n").encode(), b"")
        metadata = b'{"Config":{"User":"65532:65532","Entrypoint":["/lib64/ld-linux-x86-64.so.2","--library-path","/lib/x86_64-linux-gnu:/lib64","/runtime/p4_native_readiness_worker"]}}'
        return subprocess.CompletedProcess(command, 0, metadata, b"")

    monkeypatch.setattr("evaluation.p4.podman.subprocess.run", fake_run)
    assert build_local_image(podman="podman", context=context, tag="p4:test",
                             expected_digest=digest) == digest
    assert commands[0][1:4] == ["build", "--pull=never", "--network=none"]
    assert "--network=none" in commands[0] and "--pull=never" in commands[0]
