"""Fail-closed Bubblewrap launcher for fresh P0 evaluation workers.

This module intentionally has no local/fork/container fallback.  An evaluator
controller must create a run-bound killable scope before the worker can exec;
the controller's scope-spawn operation is the only launch path.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol

from .canonical import ProtocolError, sha256


class SandboxUnavailable(ProtocolError):
    pass


class SandboxPolicyUnavailable(SandboxUnavailable):
    pass


class SandboxStartFailed(ProtocolError):
    pass


class WorkerScope(Protocol):
    """Evaluator-created scope that atomically places a child in that scope."""
    run_id: str

    def spawn(self, argv: list[str], **popen_kwargs) -> subprocess.Popen[bytes]: ...
    def kill(self, reason: str) -> None: ...


class CgroupController(Protocol):
    """Evaluator-owned factory for run-bound whole-worker scopes."""
    def verify(self) -> bool: ...
    def create_scope(self, run_id: str) -> WorkerScope: ...


@dataclass(frozen=True)
class StagedEntrypoint:
    """Exact staged artifact to execute, never an ambient import name."""
    module: str
    function: str
    artifact_digest: str

    @staticmethod
    def parse(value: str) -> tuple[str, str]:
        module, separator, function = value.partition(":")
        if (not separator or not module or not function or not module.replace(".", "").isidentifier()
                or not function.isidentifier()):
            raise SandboxPolicyUnavailable("sandbox trusted entrypoint invalid")
        return module, function

    @classmethod
    def from_staged_agent(cls, agent_root: Path, entrypoint: str) -> "StagedEntrypoint":
        module, function = cls.parse(entrypoint)
        root = Path(agent_root).resolve(strict=True)
        artifact = (root.joinpath(*module.split(".")).with_suffix(".py")).resolve(strict=True)
        try:
            artifact.relative_to(root)
        except ValueError as exc:
            raise SandboxPolicyUnavailable("sandbox entrypoint escapes staged agent") from exc
        if not artifact.is_file() or artifact.is_symlink():
            raise SandboxPolicyUnavailable("sandbox staged entrypoint unavailable")
        return cls(module, function, sha256(artifact.read_bytes()))

    def validate(self, agent_root: Path) -> Path:
        module, function = self.parse(f"{self.module}:{self.function}")
        if module != self.module or function != self.function or not isinstance(self.artifact_digest, str):
            raise SandboxPolicyUnavailable("sandbox trusted entrypoint invalid")
        if len(self.artifact_digest) != 71 or not self.artifact_digest.startswith("sha256:"):
            raise SandboxPolicyUnavailable("sandbox entrypoint digest invalid")
        root = Path(agent_root).resolve(strict=True)
        if Path(agent_root).is_symlink() or not root.is_dir():
            raise SandboxPolicyUnavailable("sandbox agent staging unavailable")
        artifact = (root.joinpath(*self.module.split(".")).with_suffix(".py")).resolve(strict=True)
        try:
            artifact.relative_to(root)
        except ValueError as exc:
            raise SandboxPolicyUnavailable("sandbox entrypoint escapes staged agent") from exc
        if not artifact.is_file() or artifact.is_symlink() or sha256(artifact.read_bytes()) != self.artifact_digest:
            raise SandboxPolicyUnavailable("sandbox staged entrypoint digest mismatch")
        return artifact

    def worker_binding(self, agent_root: Path) -> str:
        artifact = self.validate(agent_root)
        relative = artifact.relative_to(Path(agent_root).resolve(strict=True)).as_posix()
        # Canonical JSON is a single opaque binding, not separate ambient
        # module/path/digest knobs that an inherited environment can replace.
        return json.dumps({"artifact_digest": self.artifact_digest, "artifact_path": f"/agent/{relative}",
                           "function": self.function, "module": self.module},
                          sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class SandboxSpec:
    runtime_root: Path
    agent_root: Path
    input_root: Path
    command: tuple[str, ...]
    work_root: Path
    seccomp_policy: Path
    entrypoint: StagedEntrypoint
    bwrap_path: str = "bwrap"

    def validate(self) -> None:
        for name, path in (("runtime", self.runtime_root), ("agent", self.agent_root),
                           ("input", self.input_root)):
            staged = Path(path)
            if staged.is_symlink() or not staged.is_dir():
                raise SandboxPolicyUnavailable(f"sandbox {name} staging unavailable")
        policy = Path(self.seccomp_policy)
        if policy.is_symlink() or not policy.is_file():
            raise SandboxPolicyUnavailable("sandbox seccomp staging unavailable")
        if not self.command or any(not isinstance(value, str) or not value or "\x00" in value for value in self.command):
            raise SandboxPolicyUnavailable("sandbox command invalid")
        self.entrypoint.validate(self.agent_root)
        if not Path(self.work_root).is_dir():
            raise SandboxPolicyUnavailable("sandbox work root unavailable")


@dataclass(frozen=True)
class SandboxProcess:
    process: subprocess.Popen[bytes]
    scope: WorkerScope

    def kill(self, reason: str) -> None:
        self.scope.kill(reason)


class BwrapSandboxLauncher:
    """Build an empty-root bwrap command; scope.spawn performs the atomic exec."""
    def __init__(self, controller: CgroupController, *, environ: Mapping[str, str] | None = None):
        self.controller = controller
        self.environ = dict(environ or {})

    def preflight(self, spec: SandboxSpec) -> None:
        spec.validate()
        executable = shutil.which(spec.bwrap_path) if os.path.sep not in spec.bwrap_path else spec.bwrap_path
        if not executable or not os.access(executable, os.X_OK):
            raise SandboxUnavailable("sandbox_unavailable: bubblewrap executable")
        if not self.controller.verify():
            raise SandboxPolicyUnavailable("sandbox_policy_unavailable: cgroup controller")
        try:
            version = subprocess.run([executable, "--version"], stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     timeout=2, check=False, close_fds=True)
        except OSError as exc:
            raise SandboxUnavailable("sandbox_unavailable: bubblewrap probe") from exc
        if version.returncode != 0:
            raise SandboxUnavailable("sandbox_unavailable: bubblewrap probe")

    def argv(self, spec: SandboxSpec, *, seccomp_fd: int | None = None) -> list[str]:
        spec.validate()
        if seccomp_fd is None:
            seccomp_fd = -1
        return [spec.bwrap_path, "--die-with-parent", "--new-session", "--unshare-user", "--unshare-pid",
                "--unshare-net", "--unshare-ipc", "--unshare-uts", "--unshare-cgroup", "--cap-drop", "ALL",
                "--tmpfs", "/", "--dir", "/runtime", "--dir", "/agent", "--dir", "/input", "--dir", "/work",
                "--ro-bind", str(spec.runtime_root), "/runtime", "--ro-bind", str(spec.agent_root), "/agent",
                "--ro-bind", str(spec.input_root), "/input", "--tmpfs", "/work", "--proc", "/proc",
                "--dev", "/dev", "--seccomp", str(seccomp_fd), "--chdir", "/work", "--", *spec.command]

    @staticmethod
    def safe_environment(*, entrypoint_binding: str | None = None) -> dict[str, str]:
        environment = {"PATH": "/runtime", "HOME": "/work", "TMPDIR": "/work/tmp", "PYTHONNOUSERSITE": "1",
                       "PYTHONSAFEPATH": "1", "LANG": "C.UTF-8"}
        if entrypoint_binding is not None:
            environment["P0_STAGED_ENTRYPOINT_BINDING"] = entrypoint_binding
        return environment

    def start(self, spec: SandboxSpec, scope: WorkerScope) -> SandboxProcess:
        self.preflight(spec)
        if scope.run_id == "":
            raise SandboxStartFailed("sandbox scope run binding unavailable")
        policy_fd = None
        try:
            policy_fd = os.open(spec.seccomp_policy, os.O_RDONLY)
            process = scope.spawn(self.argv(spec, seccomp_fd=policy_fd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, close_fds=True, pass_fds=(policy_fd,),
                                  env=self.safe_environment(entrypoint_binding=spec.entrypoint.worker_binding(spec.agent_root)),
                                  start_new_session=True)
            return SandboxProcess(process, scope)
        except Exception as exc:
            try:
                scope.kill("sandbox_start_failed")
            except Exception:
                pass
            raise SandboxStartFailed("sandbox_start_failed") from exc
        finally:
            if policy_fd is not None:
                os.close(policy_fd)
