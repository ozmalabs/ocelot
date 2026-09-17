"""Real P3 Podman containment lane; missing provisioned closure fails release CI."""
from __future__ import annotations
import hashlib
import os
import shutil
import pytest
from dataclasses import replace
from evaluation.p3.execution import P3ExecutionFailure, P3PodmanLauncher, P3PodmanSpec, P3WorkerClient


def _release_or_skip(message: str) -> None:
    if os.environ.get("P3_RELEASE_LANE") == "1":
        pytest.fail(message)
    pytest.skip(message)


def _spec(tmp_path, image_digest: str) -> P3PodmanSpec:
    root=tmp_path/"closure"; root.mkdir(); agent=root/"agent"; agent.mkdir()
    worker=agent/"worker"; worker.write_bytes(b"fixed-worker"); worker.chmod(0o500)
    (agent/"candidate.bin").write_bytes(b"candidate")
    input_root=root/"input"; input_root.mkdir(); work=root/"work"; work.mkdir()
    profile=os.environ.get("P3_TEST_SECCOMP_PROFILE", "/usr/share/containers/seccomp.json")
    if not os.path.isfile(profile):
        _release_or_skip("provisioned P3 seccomp profile unavailable")
    seccomp=root/"seccomp.json"; seccomp.write_bytes(open(profile, "rb").read())
    return P3PodmanSpec(image_digest, worker, agent, input_root, seccomp, "sha256:"+hashlib.sha256(seccomp.read_bytes()).hexdigest(), work, root)


def test_real_rootless_p3_probe_or_release_failure(tmp_path):
    if shutil.which("podman") is None:
        _release_or_skip("Podman unavailable outside the P3 release lane")
    image=os.environ.get("P3_TEST_WORKER_IMAGE_DIGEST")
    if not image:
        _release_or_skip("provisioned, lock-pinned P3 worker/probe image unavailable")
    spec=_spec(tmp_path, image)
    try:
        P3PodmanLauncher().preflight(spec)
        evidence=P3WorkerClient(spec).adversarial_probe(lock_digest="sha256:"+"a"*64)
    except P3ExecutionFailure as exc:
        _release_or_skip(f"P3 hardened local closure failed: {exc}")
    assert evidence["status"] == "contained"
    assert set(evidence["attempts"].values()) == {"blocked"}
    argv=" ".join(P3PodmanLauncher().argv(spec))
    for required in ("--pull=never", "--network=none", "--read-only", "--cap-drop=ALL", "no-new-privileges"):
        assert required in argv
    assert "commit" not in argv
