"""Fail-closed, rootless Podman policy for P2 native workers."""
from __future__ import annotations

import hashlib
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .protocol import MAX_FRAME_BYTES, P2ProtocolError

class PodmanUnavailable(P2ProtocolError): pass
class PodmanPolicyUnavailable(P2ProtocolError): pass

@dataclass(frozen=True)
class PodmanSpec:
    image_digest: str
    worker_binary: Path
    agent_root: Path
    input_root: Path
    seccomp_profile: Path
    seccomp_digest: str
    work_root: Path
    staging_root: Path
    uid_gid: str = "65532:65532"
    podman_path: str = "podman"
    entrypoint: str = "/runtime/p2_native_worker"

    def validate(self) -> None:
        if not isinstance(self.image_digest, str) or not self.image_digest.startswith("sha256:") or len(self.image_digest) != 71:
            raise PodmanPolicyUnavailable("p2 image digest")
        if self.uid_gid != "65532:65532": raise PodmanPolicyUnavailable("fixed P2 non-root uid/gid required")
        if self.entrypoint not in {"/runtime/p2_native_worker", "/runtime/p2_bypass_probe", "/runtime/p2_python_bypass_probe"}:
            raise PodmanPolicyUnavailable("fixed P2 native entrypoint")
        root = Path(self.staging_root)
        if root.is_symlink() or not root.is_dir(): raise PodmanPolicyUnavailable("p2 evaluator staging root")
        root = root.resolve(strict=True)
        resolved: dict[str, Path] = {}
        for label, raw in (("worker", self.worker_binary), ("agent", self.agent_root), ("input", self.input_root), ("seccomp", self.seccomp_profile), ("work", self.work_root)):
            path = Path(raw)
            if path.is_symlink() or not path.exists(): raise PodmanPolicyUnavailable(f"p2 {label} staging")
            path = path.resolve(strict=True)
            if path == root or root not in path.parents: raise PodmanPolicyUnavailable(f"p2 {label} escapes evaluator staging")
            resolved[label] = path
        if not resolved["worker"].is_file() or not os.access(resolved["worker"], os.X_OK): raise PodmanPolicyUnavailable("p2 worker binary")
        if not resolved["agent"].is_dir() or not resolved["input"].is_dir() or not resolved["work"].is_dir() or not resolved["seccomp"].is_file():
            raise PodmanPolicyUnavailable("p2 staging type")
        if resolved["worker"].parent != resolved["agent"] or resolved["agent"] == resolved["input"]: raise PodmanPolicyUnavailable("p2 artifact staging")
        actual = "sha256:" + hashlib.sha256(resolved["seccomp"].read_bytes()).hexdigest()
        if actual != self.seccomp_digest: raise PodmanPolicyUnavailable("p2 seccomp digest")

class PodmanLauncher:
    """Exact container command; there is intentionally no local fallback."""
    def __init__(self, *, environ: dict[str, str] | None = None): self.environ = dict(environ or {})
    def executable(self, spec: PodmanSpec) -> str:
        candidate = shutil.which(spec.podman_path) if os.path.sep not in spec.podman_path else spec.podman_path
        if not candidate or not os.access(candidate, os.X_OK): raise PodmanUnavailable("podman unavailable")
        return candidate
    def _local_image(self, executable: str, image_digest: str) -> None:
        if not isinstance(image_digest, str) or not image_digest.startswith("sha256:") or len(image_digest) != 71:
            raise PodmanPolicyUnavailable("p2 image digest")
        try:
            image = subprocess.run([executable, "image", "inspect", "--format", "{{.Id}}", image_digest], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2, check=False, close_fds=True, env={"PATH": os.environ.get("PATH", "")})
        except OSError as exc: raise PodmanUnavailable("local image probe") from exc
        actual = image.stdout.strip().decode("ascii", "ignore")
        if image.returncode != 0 or actual not in {image_digest, image_digest[7:]}:
            raise PodmanPolicyUnavailable("digest-pinned local P2 image unavailable")
    def preflight_image(self, spec: PodmanSpec, image_digest: str) -> None:
        spec.validate(); executable=self.executable(spec)
        self._local_image(executable,image_digest)
    def preflight(self, spec: PodmanSpec) -> None:
        spec.validate(); executable = self.executable(spec)
        try:
            probe = subprocess.run([executable, "info", "--format", "{{.Host.Security.Rootless}}"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2, check=False, close_fds=True, env={"PATH": os.environ.get("PATH", "")})
        except OSError as exc: raise PodmanUnavailable("podman probe") from exc
        if probe.returncode != 0 or probe.stdout.strip().lower() != b"true": raise PodmanPolicyUnavailable("rootless Podman required")
        self._local_image(executable,spec.image_digest)
    def argv(self, spec: PodmanSpec) -> list[str]:
        spec.validate()
        return [spec.podman_path, "run", "--rm", "--interactive", "--pull=never", "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", f"--security-opt=seccomp={Path(spec.seccomp_profile).resolve(strict=True)}", f"--user={spec.uid_gid}", "--pids-limit=32", "--memory=512m", "--cpus=1", "--tmpfs=/work:rw,noexec,nosuid,nodev,size=64k", f"--volume={Path(spec.agent_root).resolve(strict=True)}:/agent:ro,nosuid,nodev,noexec", f"--volume={Path(spec.input_root).resolve(strict=True)}:/input:ro,nosuid,nodev,noexec", "--workdir=/work", "--env=HOME=/work", "--env=PATH=/agent", "--env=LANG=C.UTF-8", spec.image_digest, spec.entrypoint]
    def start(self, spec: PodmanSpec) -> subprocess.Popen[bytes]:
        self.preflight(spec)
        return subprocess.Popen(self.argv(spec), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, env={"PATH": os.environ.get("PATH", "")}, start_new_session=True)
    def exchange(self, spec: PodmanSpec, request: bytes) -> tuple[bytes, bytes, int]:
        """Apply the locked wall/output budget and kill the process group on breach."""
        if len(request) > MAX_FRAME_BYTES: raise PodmanPolicyUnavailable("p2 input frame bound")
        process = self.start(spec)
        try:
            stdout, stderr = process.communicate(request, timeout=3)
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(); raise PodmanPolicyUnavailable("p2 wall budget exhausted") from exc
        if len(stdout) > MAX_FRAME_BYTES or len(stderr) > MAX_FRAME_BYTES:
            raise PodmanPolicyUnavailable("p2 output frame bound")
        return stdout, stderr, process.returncode
