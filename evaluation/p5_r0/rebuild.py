"""Canonical, clean-root V3 rebuild and relock workflow.

This module deliberately does not update any existing stage root.  It creates a
new root, stages the canonical worker source, builds exactly one local image,
and records a V3 closure and lock.  The default authority is explicitly local
only; callers must inject an independent authority if they want to perform the
separate validator/activation step.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.canonical import canonical_bytes

from .native import DEFAULT_LIMITS, V3_HOST_CLOSURE_KEYS, closure_spec_v3
from .protocol import P5R0Error, digest, is_digest
from .repair import preregister_repair, validate_repair_lock

CANONICAL_WORKER = Path("evaluation/p5_r0/native_worker_entrypoint_v3.py")
DEFAULT_CONTAINERFILE = Path("evaluation/p5_r0/Containerfile.v3")
DEFAULT_SECCOMP = Path("/usr/share/containers/seccomp.json")
DEFAULT_RUNTIME = Path("/usr/bin/crun")
DEFAULT_OUTPUT_ROOT = Path("var/p5-r0-native-stage-v3-clean")
PRESERVED_ROOT_NAMES = frozenset(
    {
        "p5-r0-native-stage",
        "p5-r0-native-stage-v3-repair",
        "p5-r0-native-stage-v3-repair-closure",
    }
)


def _regular(path: Path, label: str) -> Path:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not path.stat().st_mode & 0o444:
        raise P5R0Error(label)
    return path.resolve()


def _write_private(path: Path, value: Mapping[str, Any]) -> None:
    path.write_bytes(canonical_bytes(dict(value)))
    path.chmod(0o400)


def _image_digest(raw: str) -> str:
    value = raw.strip()
    if value.startswith("sha256:"):
        value = value
    elif len(value) == 64:
        value = f"sha256:{value}"
    if not is_digest(value):
        raise P5R0Error("Podman image digest")
    return value


def _allowed_syscalls(profile: Path) -> list[str]:
    try:
        data = json.loads(profile.read_text())
        groups = data.get("syscalls", [])
        return sorted(
            {
                name
                for group in groups
                if group.get("action") == "SCMP_ACT_ALLOW"
                for name in group.get("names", [])
            }
        )
    except (OSError, TypeError, ValueError) as exc:
        raise P5R0Error("seccomp syscall commitment") from exc


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _default_host_paths(root: Path) -> dict[str, Path]:
    p5 = root / "evaluation" / "p5_r0"
    return {
        "host_runner": p5 / "runner.py",
        "host_native": p5 / "native.py",
        "host_evaluator": p5 / "evaluator.py",
        "host_worker_validator": p5 / "native_worker.py",
        "host_repair": p5 / "repair.py",
        "host_receipts": p5 / "receipts.py",
        "host_evidence": p5 / "evidence.py",
        "host_rollback": p5 / "rollback.py",
        # CgroupSupervisor is the evaluator-owned kill authority.  The
        # LocalSupervisor in the same module is intentionally not used.
        "host_kill": root / "evaluation" / "p0a" / "supervisor.py",
    }


def _run_local(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        environment = os.environ.copy()
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise P5R0Error("local Podman command") from exc


def _build_image(*, podman: str, context: Path, containerfile: Path, tag: str) -> tuple[str, dict[str, list[str]]]:
    build_argv = [
        podman,
        "build",
        "--pull=never",
        "--network=none",
        "--runtime=crun",
        "--file",
        str(containerfile),
        "--tag",
        tag,
        str(context),
    ]
    built = _run_local(build_argv, cwd=context)
    if built.returncode != 0:
        raise P5R0Error("local image build")
    inspect_argv = [podman, "image", "inspect", tag, "--format", "{{.Id}}"]
    inspected = _run_local(inspect_argv, cwd=context)
    if inspected.returncode != 0:
        raise P5R0Error("local image inspect")
    return _image_digest(inspected.stdout), {"build": build_argv, "inspect": inspect_argv}


def _assert_full_closure(closure: Mapping[str, Any]) -> None:
    files = closure.get("files")
    if not isinstance(files, dict) or not V3_HOST_CLOSURE_KEYS.issubset(files) or not {"worker", "runtime", "containerfile", "seccomp_profile"}.issubset(files):
        raise P5R0Error("V3 full host closure")
    if any(not is_digest(files.get(key)) for key in files):
        raise P5R0Error("V3 closure file digest")
    for key in ("image_digest", "worker_digest", "runtime_digest", "seccomp_digest", "closure_digest", "allowed_syscalls_digest", "argv_digest"):
        if not is_digest(closure.get(key)):
            raise P5R0Error(f"V3 closure digest: {key}")


def rebuild_canonical_v3(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    parent_lock: dict[str, Any],
    parent_lock_path: Path | None = None,
    parent_authority: dict[str, Any] | None = None,
    bundle: dict[str, Any] | None = None,
    canonical_source: Path | None = None,
    containerfile: Path | None = None,
    seccomp_profile: Path = DEFAULT_SECCOMP,
    runtime_path: Path = DEFAULT_RUNTIME,
    host_paths: Mapping[str, Path] | None = None,
    podman: str = "podman",
    image_tag: str = "localhost/p5-r0-native-v3-clean",
    stale_image_digests: set[str] | None = None,
    trusted_authority: dict[str, Any] | None = None,
    signer: Ed25519PrivateKey | None = None,
) -> dict[str, Any]:
    """Build one clean local V3 image and write a separate relock root.

    ``trusted_authority`` is optional by design.  When omitted, the lock is
    signed by a generated local authority and the returned metadata explicitly
    says that there is no external custody or promotion authority.  When it is
    supplied, the lock is additionally checked with ``validate_repair_lock``;
    that is an injected verification input, not a claim made by this local
    rebuild process.
    """
    root = Path(output_root).resolve()
    repository = _repo_root()
    if root.exists():
        raise P5R0Error("V3 clean output already exists")
    if root.name in PRESERVED_ROOT_NAMES:
        raise P5R0Error("V3 output is a preserved root")
    preserved = [repository / "var" / name for name in PRESERVED_ROOT_NAMES]
    if any(_inside(root, prior.resolve()) for prior in preserved if prior.exists()):
        raise P5R0Error("V3 output overlaps preserved root")
    if parent_lock_path is not None and root == Path(parent_lock_path).resolve():
        raise P5R0Error("V3 output overlaps V2 parent")

    source = _regular(canonical_source or repository / CANONICAL_WORKER, "canonical V3 worker")
    expected_source = (repository / CANONICAL_WORKER).resolve()
    if source != expected_source:
        raise P5R0Error("stale V3 worker source")
    source_digest = digest(source.read_bytes())
    profile = _regular(Path(seccomp_profile), "seccomp profile")
    runtime = _regular(Path(runtime_path), "crun runtime")
    if runtime.name != "crun":
        raise P5R0Error("crun runtime")
    source_containerfile = _regular(containerfile or repository / DEFAULT_CONTAINERFILE, "V3 Containerfile")

    root.mkdir(parents=True, mode=0o700)
    context = root / "context"
    runtime_dir = context / "runtime"
    runtime_dir.mkdir(parents=True, mode=0o700)
    staged_worker = runtime_dir / "p5_r0_worker"
    shutil.copyfile(source, staged_worker)
    staged_worker.chmod(0o555)
    staged_containerfile = context / "Containerfile"
    shutil.copyfile(source_containerfile, staged_containerfile)
    staged_containerfile.chmod(0o444)
    if digest(staged_worker.read_bytes()) != source_digest:
        raise P5R0Error("canonical V3 worker staging")

    tag = f"{image_tag}:clean-{source_digest[7:19]}"
    image_digest, command_record = _build_image(podman=podman, context=context, containerfile=staged_containerfile, tag=tag)
    forbidden = set(stale_image_digests or set())
    parent_closure = parent_lock.get("closure") if isinstance(parent_lock, dict) else None
    if isinstance(parent_closure, dict) and is_digest(parent_closure.get("image_digest")):
        forbidden.add(parent_closure["image_digest"])
    if image_digest in forbidden:
        raise P5R0Error("rebuilt image reused stale digest")

    closure_paths = dict(_default_host_paths(repository))
    closure_paths.update({str(key): Path(value) for key, value in (host_paths or {}).items()})
    closure_paths.update({"worker": staged_worker, "runtime": runtime, "containerfile": staged_containerfile})
    missing = V3_HOST_CLOSURE_KEYS.difference(closure_paths)
    if missing:
        raise P5R0Error("V3 host closure keys")
    closure = closure_spec_v3(
        image_digest=image_digest,
        image_ref=f"{tag}@{image_digest}",
        entrypoint="/runtime/p5_r0_worker",
        profile=profile,
        paths=closure_paths,
        limits=DEFAULT_LIMITS,
        allowed_syscalls=_allowed_syscalls(profile),
        runtime_path=runtime,
    )
    _assert_full_closure(closure)

    lock_path = root / "p5-r0-local-lock-v3.json"
    artifact = preregister_repair(
        lock_path,
        parent_lock=parent_lock,
        signer=signer,
        trusted_authority=trusted_authority,
        parent_lock_path=parent_lock_path,
        parent_authority=parent_authority,
        closure=closure,
        bundle=bundle,
    )
    lock = artifact["lock"]
    if trusted_authority is not None:
        validate_repair_lock(lock, trusted_authority=trusted_authority, expected_manifest_digest=lock["manifest_digest"])

    authority = lock["authority"]
    local_authority = {
        "schema": "P5R0LocalAuthorityMetadataV1",
        "authority_id": authority["authority_id"],
        "key_id": authority["key_id"],
        "authority_digest": digest(authority),
        "authority_verified": lock["authority_verified"],
        "external_custody": False,
        "promotion_authority": False,
        "custody_scope": "local_only",
        "transport_attestation": None,
        "claim_boundary": "No external custody, release, adoption, or promotion claim.",
    }
    authority_path = root / "authority.local.json"
    _write_private(authority_path, local_authority)
    manifest_path = root / "manifest.v3.json"
    _write_private(manifest_path, artifact["bundle"])
    record = {
        "schema": "P5R0CanonicalV3RebuildV1",
        "root": str(root),
        "canonical_worker": str(source),
        "canonical_worker_digest": source_digest,
        "staged_worker": str(staged_worker),
        "image_tag": tag,
        "image_digest": image_digest,
        "image_ref": closure["image_ref"],
        "build_argv": command_record,
        "build_policy": {"pull": "never", "network": "none", "runtime": "crun"},
        "closure_digest": closure["closure_digest"],
        "seccomp_digest": closure["seccomp_digest"],
        "runtime_digest": closure["runtime_digest"],
        "argv_digest": closure["argv_digest"],
        "authority_metadata": str(authority_path),
        "external_custody": False,
        "preserved_roots": [str(path) for path in preserved],
        "lock_path": str(lock_path),
        "manifest_path": str(manifest_path),
    }
    record_path = root / "rebuild.v3.json"
    _write_private(record_path, record)
    return {
        "root": root,
        "context": context,
        "lock": lock,
        "bundle": artifact["bundle"],
        "closure": closure,
        "closure_paths": closure_paths,
        "authority": authority,
        "authority_metadata": local_authority,
        "lock_path": lock_path,
        "authority_path": authority_path,
        "manifest_path": manifest_path,
        "record_path": record_path,
        "build_argv": command_record,
    }


build_canonical_v3 = rebuild_canonical_v3
