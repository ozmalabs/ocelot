from __future__ import annotations
import hashlib
import pytest
from evaluation.p2.podman import PodmanLauncher, PodmanPolicyUnavailable, PodmanSpec

def spec(tmp_path):
    stage=tmp_path/"stage"; stage.mkdir(); agent=stage/"agent"; agent.mkdir(); worker=agent/"p2_native_worker"; worker.write_text("native"); worker.chmod(0o500)
    input_root=stage/"input"; input_root.mkdir(); work=stage/"work"; work.mkdir(); seccomp=stage/"seccomp.json"; seccomp.write_text('{"defaultAction":"SCMP_ACT_ERRNO"}')
    digest="sha256:"+hashlib.sha256(seccomp.read_bytes()).hexdigest()
    return PodmanSpec("sha256:"+"a"*64,worker,agent,input_root,seccomp,digest,work,stage)
def test_hardened_argv_has_no_network_writable_host_mount_or_pull(tmp_path):
    argv=PodmanLauncher().argv(spec(tmp_path)); joined=" ".join(argv)
    for required in ("--interactive","--pull=never","--network=none","--read-only","--cap-drop=ALL","no-new-privileges","--pids-limit=32","--memory=512m","--tmpfs=/work:rw,noexec,nosuid,nodev,size=64k",":/agent:ro,nosuid,nodev,noexec",":/input:ro,nosuid,nodev,noexec"):
        assert required in joined
    assert "--volume=/:" not in joined and "podman.sock" not in joined
def test_invalid_digest_and_staging_escape_fail_closed_before_podman(tmp_path):
    s=spec(tmp_path); invalid=PodmanSpec("not-a-digest",s.worker_binary,s.agent_root,s.input_root,s.seccomp_profile,s.seccomp_digest,s.work_root,s.staging_root)
    with pytest.raises(PodmanPolicyUnavailable): PodmanLauncher().argv(invalid)
    escaped=PodmanSpec(s.image_digest,s.worker_binary,tmp_path,s.input_root,s.seccomp_profile,s.seccomp_digest,s.work_root,s.staging_root)
    with pytest.raises(PodmanPolicyUnavailable): PodmanLauncher().argv(escaped)
def test_seccomp_content_is_digest_bound(tmp_path):
    s=spec(tmp_path); s.seccomp_profile.write_text("{}")
    with pytest.raises(PodmanPolicyUnavailable,match="seccomp digest"): PodmanLauncher().argv(s)


def test_uid_gid_is_fixed_to_the_release_nonroot_identity(tmp_path):
    s=spec(tmp_path)
    invalid=PodmanSpec(s.image_digest,s.worker_binary,s.agent_root,s.input_root,s.seccomp_profile,s.seccomp_digest,s.work_root,s.staging_root,uid_gid="1000:1000")
    with pytest.raises(PodmanPolicyUnavailable,match="fixed P2 non-root uid/gid"):
        PodmanLauncher().argv(invalid)
