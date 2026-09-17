from pathlib import Path

from evaluation.p0a.canonical import b64encode
from evaluation.p4.podman import P4PodmanSpec
from evaluation.p4.runner import preregister_local
from evaluation.p4.staging import digest_file

P4_ROOT = Path(__file__).parents[1]
FIXTURE = P4_ROOT / "fixtures" / "p4_r0_public_bundle_v1.json"
PREREGISTRATION = P4_ROOT / "preregistration.local.md"


def staged_spec(tmp_path, image_digest="sha256:" + "a" * 64):
    root = tmp_path / "stage"
    root.mkdir(parents=True)
    agent = root / "agent"
    agent.mkdir()
    worker = agent / "worker"
    worker.write_text("#!/bin/sh\nexit 0\n")
    worker.chmod(0o755)
    input_root = root / "input"
    input_root.mkdir()
    (input_root / "fixture.json").write_text("{}")
    seccomp = root / "seccomp.json"
    seccomp.write_text("{}")
    container_spec = root / "Containerfile"
    container_spec.write_text("FROM scratch\n")
    work = root / "work"
    work.mkdir()
    spec = P4PodmanSpec(image_digest, worker, agent, input_root, seccomp, digest_file(seccomp), container_spec, work, root)
    return root, spec


def local_lock(tmp_path, spec, image_digest=None, *, evaluator_signer=None, evaluator_key_id="p4-r0-local-evaluator"):
    evaluator_public_key = None
    if evaluator_signer is not None:
        evaluator_public_key = b64encode(evaluator_signer.public_key().public_bytes_raw())
    return preregister_local(PREREGISTRATION, FIXTURE, spec.staging_root, tmp_path / "local.lock.json", image_digest=image_digest or spec.image_digest, worker_binary=spec.worker_binary, agent_root=spec.agent_root, input_root=spec.input_root, seccomp_profile=spec.seccomp_profile, container_spec=spec.container_spec, evaluator_public_key=evaluator_public_key, evaluator_key_id=evaluator_key_id)
