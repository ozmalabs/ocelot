from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import os
import shutil
import subprocess

from .protocol import P4ProtocolError, is_digest
from .seccomp import validate_seccomp_profile
from .staging import digest_file, validate_closure


class PodmanUnavailable(P4ProtocolError):
    pass


class PodmanPolicyUnavailable(P4ProtocolError):
    pass


PROCFS_STARTUP_EVIDENCE = "ensure /proc/thread-self/fd is on procfs: operation not permitted"
_IMAGE_REQUIRED_CONTEXT_PATHS = (
    "Containerfile",
    "p4_native_readiness_worker",
    "trust/p4-trusted-evaluator.json",
    "input/p4_r0_public_bundle_v1.json",
    "runtime-closure.json",
)
_IMAGE_REQUIRED_CONTEXT_DIRS = ("lib", "lib64", "etc")


def build_procfs_profile() -> tuple[str, ...]:
    """Construct only the safe private-PID/procfs policy."""
    return ("--pid=private",)


def validate_image_context(context: Path) -> None:
    """Validate the finite files that are copied into the scratch image."""
    root = Path(context)
    if root.is_symlink() or not root.is_dir():
        raise PodmanPolicyUnavailable("finite P4 image context")
    for relative in _IMAGE_REQUIRED_CONTEXT_DIRS:
        path = root / relative
        if path.is_symlink() or not path.is_dir():
            raise PodmanPolicyUnavailable(f"missing embedded runtime path: /{relative}")
    for relative in _IMAGE_REQUIRED_CONTEXT_PATHS:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise PodmanPolicyUnavailable(f"missing embedded image path: /{relative}")
    containerfile = (root / "Containerfile").read_text(encoding="utf-8")
    lines = containerfile.splitlines()
    required_lines = (
        "FROM scratch",
        "COPY p4_native_readiness_worker /runtime/p4_native_readiness_worker",
        "COPY lib/ /lib/",
        "COPY lib64/ /lib64/",
        "COPY etc/ /etc/",
        "COPY trust/p4-trusted-evaluator.json /trust/p4-trusted-evaluator.json",
        "COPY input/p4_r0_public_bundle_v1.json /input/p4_r0_public_bundle_v1.json",
        "USER 65532:65532",
    )
    if (any(line.startswith(("RUN ", "ADD ", "VOLUME ")) for line in lines)
            or any("--mount" in line for line in lines)
            or any(line.startswith("FROM ") and line != "FROM scratch" for line in lines)
            or any(line not in lines for line in required_lines)):
        raise PodmanPolicyUnavailable("P4 Containerfile does not embed fixed paths")


def _validate_image_metadata(raw: bytes) -> None:
    try:
        value = json.loads(raw.decode("utf-8"))
        record = value[0] if isinstance(value, list) and len(value) == 1 else value
        config = record["Config"]
        if (config.get("User") != "65532:65532"
                or config.get("Entrypoint") != [
                    "/lib64/ld-linux-x86-64.so.2", "--library-path",
                    "/lib/x86_64-linux-gnu:/lib64",
                    "/runtime/p4_native_readiness_worker"]):
            raise ValueError
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PodmanPolicyUnavailable("P4 image internal paths or identity") from exc


def build_local_image(*, podman: str, context: Path, tag: str,
                      expected_digest: str | None = None) -> str:
    """Build and inspect a finite local P4 image, never pulling or networking."""
    validate_image_context(context)
    if expected_digest is not None and not is_digest(expected_digest):
        raise PodmanPolicyUnavailable("P4 image digest")
    executable = shutil.which(podman) if os.path.sep not in podman else podman
    if not executable or not os.access(executable, os.X_OK):
        raise PodmanUnavailable("podman unavailable")
    command = [executable, "build", "--pull=never", "--network=none",
               "--http-proxy=false", "--layers=false", "--file",
               str(Path(context) / "Containerfile"), "--tag", tag, str(context)]
    try:
        built = subprocess.run(command, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=120, check=False, close_fds=True)
        if built.returncode:
            raise PodmanPolicyUnavailable("local P4 image build failed")
        inspected = subprocess.run(
            [executable, "image", "inspect", "--format", "{{.Id}}", tag],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=10, check=False, close_fds=True)
        metadata = subprocess.run(
            [executable, "image", "inspect", "--format", "json", tag],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=10, check=False, close_fds=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PodmanPolicyUnavailable("local P4 image unavailable") from exc
    value = inspected.stdout.decode("ascii", "ignore").strip()
    digest = value if value.startswith("sha256:") else f"sha256:{value}"
    if inspected.returncode or not is_digest(digest):
        raise PodmanPolicyUnavailable("P4 image digest unavailable")
    if expected_digest is not None and digest != expected_digest:
        raise PodmanPolicyUnavailable("P4 image digest mismatch")
    if metadata.returncode:
        raise PodmanPolicyUnavailable("P4 image metadata unavailable")
    _validate_image_metadata(metadata.stdout)
    return digest


@dataclass(frozen=True)
class P4PodmanSpec:
    image_digest: str
    worker_binary: Path
    agent_root: Path
    input_root: Path
    seccomp_profile: Path
    seccomp_digest: str
    container_spec: Path
    work_root: Path
    staging_root: Path
    uid_gid: str = "65532:65532"
    podman_path: str = "podman"
    entrypoint: str = "/runtime/p4_native_readiness_worker"
    runtime_context: Path | None = None
    image_context: Path | None = None

    def closure_artifacts(self) -> dict[str, Path]:
        artifacts = {"worker": self.worker_binary, "agent": self.agent_root,
                     "input": self.input_root, "seccomp": self.seccomp_profile,
                     "container_spec": self.container_spec}
        runtime = self.runtime_context or (Path(self.staging_root) / "runtime")
        if runtime.is_dir():
            artifacts["runtime"] = runtime
        return artifacts

    def trusted_evaluator_artifact(self) -> Path:
        return Path(self.staging_root) / "p4-trusted-evaluator.json"

    def validate(self) -> None:
        if (not is_digest(self.image_digest) or self.uid_gid != "65532:65532"
                or self.entrypoint != "/runtime/p4_native_readiness_worker"):
            raise PodmanPolicyUnavailable("fixed P4 policy")
        root = Path(self.staging_root)
        if root.is_symlink() or not root.is_dir():
            raise PodmanPolicyUnavailable("staging root")
        root = root.resolve(strict=True)
        paths = {}
        for label, raw in {**self.closure_artifacts(), "work": self.work_root}.items():
            p = Path(raw)
            if p.is_symlink() or not p.exists():
                raise PodmanPolicyUnavailable("staged path")
            p = p.resolve(strict=True)
            if root not in p.parents:
                raise PodmanPolicyUnavailable("staging escape")
            paths[label] = p
        if (not paths["worker"].is_file() or not os.access(paths["worker"], os.X_OK)
                or not paths["agent"].is_dir() or not paths["input"].is_dir()
                or not paths["work"].is_dir() or not paths["seccomp"].is_file()
                or not paths["container_spec"].is_file()
                or paths["worker"].parent != paths["agent"]):
            raise PodmanPolicyUnavailable("staging type")
        if self.image_context is not None:
            context = Path(self.image_context)
            if root not in context.resolve(strict=True).parents:
                raise PodmanPolicyUnavailable("image context escape")
            validate_image_context(context)
        if digest_file(paths["seccomp"]) != self.seccomp_digest:
            raise PodmanPolicyUnavailable("seccomp digest")
        try:
            native = paths["worker"].read_bytes()[:4] == b"\x7fELF"
        except OSError as exc:
            raise PodmanPolicyUnavailable("worker probe") from exc
        if native:
            try:
                validate_seccomp_profile(paths["seccomp"], worker=paths["worker"])
            except P4ProtocolError as exc:
                raise PodmanPolicyUnavailable("unavailable measured seccomp") from exc


class P4PodmanLauncher:
    def executable(self, spec: P4PodmanSpec) -> str:
        executable = (shutil.which(spec.podman_path)
                      if os.path.sep not in spec.podman_path else spec.podman_path)
        if not executable or not os.access(executable, os.X_OK):
            raise PodmanUnavailable("podman unavailable")
        return executable

    def _validate_trusted_evaluator(self, spec: P4PodmanSpec,
                                    expected_digest: str | None) -> Path | None:
        if expected_digest is None:
            return None
        path = spec.trusted_evaluator_artifact()
        root = Path(spec.staging_root).resolve(strict=True)
        if (not is_digest(expected_digest) or path.is_symlink() or not path.is_file()
                or root not in path.resolve(strict=True).parents):
            raise PodmanPolicyUnavailable("staged trusted evaluator")
        if digest_file(path) != expected_digest:
            raise PodmanPolicyUnavailable("trusted evaluator digest")
        return path.resolve(strict=True)

    def preflight(self, spec: P4PodmanSpec,
                  expected_closure: dict[str, str] | None = None,
                  trusted_evaluator_digest: str | None = None) -> None:
        spec.validate()
        if expected_closure is None:
            raise PodmanPolicyUnavailable("signed closure required")
        validate_closure(spec.staging_root, spec.closure_artifacts(), expected_closure)
        self._validate_trusted_evaluator(spec, trusted_evaluator_digest)
        executable = self.executable(spec)
        env = {"PATH": os.environ.get("PATH", "")}
        try:
            rootless = subprocess.run(
                [executable, "info", "--format", "{{.Host.Security.Rootless}}"],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=2, env=env, check=False)
            image = subprocess.run(
                [executable, "image", "inspect", "--format", "{{.Id}}",
                 spec.image_digest], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2,
                env=env, check=False)
        except OSError as exc:
            raise PodmanUnavailable("podman probe") from exc
        actual = image.stdout.strip().decode("ascii", "ignore")
        if (rootless.returncode or rootless.stdout.strip().lower() != b"true"
                or image.returncode
                or actual not in {spec.image_digest, spec.image_digest[7:]}):
            raise PodmanPolicyUnavailable("rootless local digest image required")

    def argv(self, spec: P4PodmanSpec,
             expected_closure: dict[str, str] | None = None,
             trusted_evaluator_digest: str | None = None) -> list[str]:
        """Return the image-only command; no host artifact is mounted."""
        spec.validate()
        if expected_closure is None:
            raise PodmanPolicyUnavailable("signed closure required")
        validate_closure(spec.staging_root, spec.closure_artifacts(), expected_closure)
        # The trust bytes are image-owned.  Validate their staging/lock binding
        # in preflight, but deliberately do not resolve or pass the host path.
        if trusted_evaluator_digest is not None and not is_digest(trusted_evaluator_digest):
            raise PodmanPolicyUnavailable("trusted evaluator digest")
        resolve = lambda path: str(Path(path).resolve(strict=True))
        return [spec.podman_path, "run", "--rm", "--interactive", "--pull=never",
                "--network=none", "--read-only", "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                f"--security-opt=seccomp={resolve(spec.seccomp_profile)}",
                f"--user={spec.uid_gid}", *build_procfs_profile(),
                "--pids-limit=32", "--memory=512m", "--cpus=1",
                spec.image_digest, spec.entrypoint]
