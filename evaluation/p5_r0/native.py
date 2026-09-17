"""Native rootless Podman/crun closure and lock-bound command construction."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import shutil
from .protocol import P5R0Error, digest, is_digest

DEFAULT_LIMITS = {"steps": 8, "frame_bytes": 65536, "wall_seconds": 3, "memory_mb": 512, "cpu": 1, "pids": 32}
# These host modules control admission, invocation, validation, sealing, and
# termination.  A V3 container digest alone is not an execution closure.
V3_HOST_CLOSURE_KEYS = frozenset({
    "host_runner", "host_native", "host_evaluator", "host_worker_validator",
    "host_repair", "host_receipts", "host_evidence", "host_rollback", "host_kill",
})


def _profile(path: Path) -> Path:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not path.stat().st_mode & 0o444:
        raise P5R0Error("seccomp profile")
    return path


def _bound_file(path: Path, label: str) -> Path:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not path.stat().st_mode & 0o444:
        raise P5R0Error(label)
    return path.resolve()


def runtime_digest(path: Path) -> str:
    return digest(_bound_file(Path(path), "crun runtime").read_bytes())


def hardened_crun_argv(*, podman: str, image_digest: str, seccomp_profile: Path, entrypoint: str = "/runtime/p5_r0_worker", limits: dict[str, Any] | None = None) -> list[str]:
    if not is_digest(image_digest):
        raise P5R0Error("immutable image digest")
    profile = _profile(seccomp_profile)
    bounded = dict(DEFAULT_LIMITS); bounded.update(limits or {})
    if bounded != DEFAULT_LIMITS:
        raise P5R0Error("unsupported native limits")
    return [podman, "run", "--rm", "--interactive", "--runtime=crun", "--pull=never", "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", f"--security-opt=seccomp={profile.resolve()}", "--user=65532:65532", "--pid=private", "--ipc=private", "--uts=private", "--pids-limit=32", "--memory=512m", "--cpus=1", image_digest, entrypoint]


def closure_digest(paths: dict[str, Path], limits: dict[str, Any], schema: str = "P5R0ClosureV2") -> str:
    files: dict[str, str] = {}
    for name, raw in sorted(paths.items()):
        path = Path(raw)
        if path.is_symlink() or not path.is_file():
            raise P5R0Error("closure file")
        files[name] = digest(path.read_bytes())
    return digest({"schema": schema, "files": files, "limits": dict(limits), "network": "none", "pull": "never", "runtime": "crun", "argv_digest": digest({"entrypoint": "/runtime/p5_r0_worker", "flags": ["--runtime=crun", "--pull=never", "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--user=65532:65532", "--pid=private", "--ipc=private", "--uts=private"], "limits": dict(limits)})})


def seccomp_digest(profile: Path) -> str:
    return digest(_profile(Path(profile)).read_bytes())


def closure_spec(*, image_digest: str, image_ref: str, entrypoint: str, profile: Path, paths: dict[str, Path], limits: dict[str, Any] | None = None, allowed_syscalls: list[str] | None = None) -> dict[str, Any]:
    bounded = dict(DEFAULT_LIMITS); bounded.update(limits or {})
    if bounded != DEFAULT_LIMITS or not is_digest(image_digest) or not image_ref or entrypoint != "/runtime/p5_r0_worker":
        raise P5R0Error("closure commitment")
    profile = _profile(Path(profile))
    syscalls = sorted(set(allowed_syscalls or []))
    if not syscalls:
        raise P5R0Error("seccomp syscall commitment")
    files = {name: digest(Path(path).read_bytes()) for name, path in sorted(paths.items())}
    files.setdefault("seccomp_profile", seccomp_digest(profile))
    bound_paths = dict(paths); bound_paths.setdefault("seccomp_profile", profile)
    return {"schema": "P5R0ClosureBindingV2", "bound": True, "image_ref": image_ref, "image_digest": image_digest, "entrypoint": entrypoint, "files": files, "closure_digest": closure_digest(bound_paths, bounded), "seccomp_profile": str(profile.resolve()), "seccomp_digest": seccomp_digest(profile), "architecture": "native", "seccomp_default_action": "SCMP_ACT_ERRNO", "allowed_syscalls": syscalls, "allowed_syscalls_digest": digest(syscalls), "argv_digest": digest({"entrypoint": entrypoint, "limits": bounded, "runtime": "crun", "network": "none", "pull": "never"}), "limits": bounded, "runtime": "crun", "network": "none", "pull": "never"}



def closure_spec_v3(*, image_digest: str, image_ref: str, entrypoint: str, profile: Path, paths: dict[str, Path], limits: dict[str, Any] | None = None, allowed_syscalls: list[str] | None = None, runtime_path: Path | None = None) -> dict[str, Any]:
    """Bind a V3 worker closure, including the exact local runtime binary."""
    bounded = dict(DEFAULT_LIMITS); bounded.update(limits or {})
    if bounded != DEFAULT_LIMITS or not is_digest(image_digest) or not image_ref or not image_ref.endswith("@" + image_digest) or entrypoint != "/runtime/p5_r0_worker": raise P5R0Error("V3 closure commitment")
    profile = _profile(Path(profile)); syscalls = sorted(set(allowed_syscalls or []))
    if not syscalls: raise P5R0Error("V3 seccomp commitment")
    bound_paths = {name: _bound_file(Path(path), f"V3 closure file: {name}") for name, path in paths.items()}
    worker = _bound_file(Path(bound_paths.get("worker", "")), "V3 worker")
    runtime = _bound_file(Path(runtime_path or (shutil.which("crun") or "")), "V3 crun runtime")
    supplied_runtime = bound_paths.get("runtime")
    if supplied_runtime is not None and _bound_file(Path(supplied_runtime), "V3 crun runtime") != runtime: raise P5R0Error("V3 runtime binding")
    bound_paths["worker"] = worker; bound_paths["runtime"] = runtime; bound_paths["seccomp_profile"] = profile
    files = {name: digest(Path(path).read_bytes()) for name, path in sorted(bound_paths.items())}
    worker_hash = files["worker"]; runtime_hash = files["runtime"]
    return {"schema": "P5R0ClosureBindingV3", "bound": True, "image_ref": image_ref, "image_digest": image_digest, "entrypoint": entrypoint, "files": files, "worker_digest": worker_hash, "worker_path": "/runtime/p5_r0_worker", "runtime_path": str(runtime), "runtime_digest": runtime_hash, "closure_digest": closure_digest(bound_paths, bounded, schema="P5R0ClosureV3"), "seccomp_profile": str(profile.resolve()), "seccomp_digest": seccomp_digest(profile), "architecture": "native", "seccomp_default_action": "SCMP_ACT_ERRNO", "allowed_syscalls": syscalls, "allowed_syscalls_digest": digest(syscalls), "argv_digest": digest({"entrypoint": entrypoint, "limits": bounded, "runtime": "crun", "network": "none", "pull": "never"}), "limits": bounded, "runtime": "crun", "network": "none", "pull": "never", "worker_contract": "P5R0WorkerContractV3"}
