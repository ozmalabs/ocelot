import json
import subprocess
from pathlib import Path

import pytest

from evaluation.p0a.canonical import canonical_bytes
from evaluation.p5_r0 import rebuild as rebuild_module
from evaluation.p5_r0.native import V3_HOST_CLOSURE_KEYS
from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.rebuild import rebuild_canonical_v3
from evaluation.p5_r0.repair import V3_PARENT_LOCK_DIGEST


STALE_IMAGE = "sha256:" + "a" * 64
NEW_IMAGE = "sha256:" + "b" * 64


def _parent():
    return {
        "lock_digest": V3_PARENT_LOCK_DIGEST,
        "manifest_digest": "sha256:" + "1" * 64,
        "case_index_digest": "sha256:" + "2" * 64,
        "truth_digest": "sha256:" + "3" * 64,
        "store_digest": "sha256:" + "4" * 64,
        "split_commitment": {"contrast_matrix": []},
        "closure": {"image_digest": STALE_IMAGE},
    }


def _host_files(tmp_path):
    files = {}
    for key in V3_HOST_CLOSURE_KEYS:
        path = tmp_path / f"{key}.py"
        path.write_text(f"# {key}\n")
        files[key] = path
    return files


def _run_fake_podman(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[1] == "build":
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, NEW_IMAGE + "\n", "")

    monkeypatch.setattr(rebuild_module.subprocess, "run", fake_run)
    return calls


def _rebuild(monkeypatch, tmp_path, **kwargs):
    calls = _run_fake_podman(monkeypatch)
    profile = tmp_path / "seccomp.json"
    profile.write_text(json.dumps({"defaultAction": "SCMP_ACT_ERRNO", "syscalls": [{"action": "SCMP_ACT_ALLOW", "names": ["read", "write"]}]}))
    runtime = tmp_path / "crun"
    runtime.write_bytes(b"local crun")
    containerfile = tmp_path / "Containerfile"
    containerfile.write_text("FROM scratch\n")
    parent_path = tmp_path / "parent-lock.json"
    parent_path.write_bytes(canonical_bytes(_parent()))
    result = rebuild_canonical_v3(
        tmp_path / "clean-v3",
        parent_lock=_parent(),
        parent_lock_path=tmp_path / "parent-lock.json",
        containerfile=containerfile,
        seccomp_profile=profile,
        runtime_path=runtime,
        host_paths=_host_files(tmp_path),
        podman="podman",
        **kwargs,
    )
    return result, calls


def test_rebuild_rejects_stale_worker_source_before_creating_root(tmp_path):
    stale = tmp_path / "stale-worker.py"
    stale.write_text("stale worker\n")
    with pytest.raises(P5R0Error, match="stale V3 worker source"):
        rebuild_canonical_v3(tmp_path / "clean-v3", parent_lock=_parent(), canonical_source=stale)
    assert not (tmp_path / "clean-v3").exists()


def test_rebuild_stages_canonical_worker_and_full_closure(monkeypatch, tmp_path):
    parent_path = tmp_path / "parent-lock.json"
    parent_path.write_bytes(canonical_bytes(_parent()))
    result, calls = _rebuild(monkeypatch, tmp_path, stale_image_digests={STALE_IMAGE})

    canonical = Path(rebuild_module.__file__).parents[2] / "evaluation/p5_r0/native_worker_entrypoint_v3.py"
    closure = result["closure"]
    assert digest(result["context"].joinpath("runtime/p5_r0_worker").read_bytes()) == digest(canonical.read_bytes())
    assert set(V3_HOST_CLOSURE_KEYS).issubset(closure["files"])
    assert {"worker", "runtime", "containerfile", "seccomp_profile"}.issubset(closure["files"])
    assert closure["worker_digest"] == digest(canonical.read_bytes())
    assert closure["image_digest"] == NEW_IMAGE
    assert closure["image_ref"].endswith("@" + NEW_IMAGE)
    assert closure["closure_digest"].startswith("sha256:")
    assert closure["seccomp_digest"].startswith("sha256:")
    assert closure["runtime_digest"].startswith("sha256:")
    assert closure["argv_digest"].startswith("sha256:")
    build = calls[0]
    assert build[1:5] == ["build", "--pull=never", "--network=none", "--runtime=crun"]
    assert result["authority_metadata"]["custody_scope"] == "local_only"
    assert result["authority_metadata"]["external_custody"] is False
    assert result["authority_metadata"]["promotion_authority"] is False
    assert result["lock"]["authority_verified"] is False
    assert result["lock_path"].exists() and result["authority_path"].exists()


def test_rebuild_preserves_prior_roots_and_parent_artifact(monkeypatch, tmp_path):
    prior = tmp_path / "p5-r0-native-stage"
    prior.mkdir()
    prior_artifact = prior / "historical-lock.json"
    prior_artifact.write_bytes(b"historical-v2")
    parent_path = tmp_path / "parent-lock.json"
    parent_bytes = canonical_bytes(_parent())
    parent_path.write_bytes(parent_bytes)

    result, _ = _rebuild(monkeypatch, tmp_path)

    assert result["root"] != prior.resolve()
    assert prior_artifact.read_bytes() == b"historical-v2"
    assert parent_path.read_bytes() == parent_bytes
    assert result["root"].exists()
    assert result["record_path"].read_bytes()
