"""Evaluator-owned, local-only Podman acceptance launcher for P0 tests.

This module is deliberately test-only: production P0 code retains Bubblewrap with
no container fallback.  It never mounts the checkout, a control path, or a
container-control socket into a worker.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import ProtocolError, sha256
from evaluation.p0a.native_graph_capture import NativeGraphClosureV1
from evaluation.p0a.sandbox import (SandboxPolicyUnavailable, SandboxProcess,
                                    SandboxSpec, SandboxStartFailed,
                                    SandboxUnavailable, StagedEntrypoint)

BASE_IMAGE_ID = "a6f700b96627c9d19a0147d664febb16fa0039b631cf2351b4c51365048ca962"
SECCOMP_POLICY = "/usr/share/containers/seccomp.json"
FORBIDDEN_RUN_FLAGS = ("--volume", "--mount", "--volumes-from", "--env-host", "--privileged",
                       "--device", "--group-add", "--userns=keep-id", "--pid=host", "--ipc=host",
                       "--network=host")

# This is deliberately finite and contains every repository-local module reached
# while importing ``evaluation.p0a.agent_worker`` with Python's normal package
# initialisation semantics.  Do not replace it with a directory copy: the fresh
# context must prove precisely what source crosses the container boundary.
WORKER_RUNTIME_FILES = (
    "__init__.py",
    "p0a/__init__.py",
    "p0a/agent_worker.py",
    "p0a/agent_protocol.py",
    "p0a/canonical.py",
    "p0a/broker.py",
    "p0a/manifest.py",
    "p0a/simulator.py",
)
WORKER_IMPORT_CLOSURE = (
    "evaluation",
    "evaluation.p0a",
    "evaluation.p0a.agent_worker",
    "evaluation.p0a.agent_protocol",
    "evaluation.p0a.canonical",
    "evaluation.p0a.broker",
    "evaluation.p0a.manifest",
    "evaluation.p0a.simulator",
)
WORKER_PYTHON_VERSION = (3, 13)
# A test can run under Python 3.12, so package staging selects a locally
# installed interpreter compatible with the pinned image rather than inheriting
# the test runner's ABI.  The environment override is evaluator-controlled.
STAGING_PYTHON_CANDIDATES = tuple(dict.fromkeys(filter(None, (
    os.environ.get("P0A_STAGING_PYTHON"), sys.executable, "python3.13", "python3",
))))
# These paths name the only interpreters provided by the pinned base image.
# The import check executes each existing path and therefore cannot silently
# validate only an alias while the entrypoint uses another interpreter.
WORKER_INTERPRETER_PATHS = ("/usr/local/bin/python3", "/usr/local/bin/python3.13")
WORKER_SITE_PACKAGES = "/usr/local/lib/python3.13/site-packages"
WORKER_SITE_ROOT = f"{WORKER_SITE_PACKAGES}/evaluation"

# Staging must not depend on wheel metadata being installed.  This is the
# complete import closure for the Ed25519 signing/verification used by P0A,
# relative to the verified ``cryptography`` package root.  In particular,
# ``_rust.abi3.so`` is intentionally named: it is the required ABI-stable
# native extension and not a directory or a site-packages sweep.
CRYPTOGRAPHY_RUNTIME_MANIFEST = (
    "__about__.py",
    "__init__.py",
    "exceptions.py",
    "utils.py",
    "hazmat/__init__.py",
    "hazmat/bindings/__init__.py",
    "hazmat/bindings/_rust.abi3.so",
    "hazmat/primitives/__init__.py",
    "hazmat/primitives/_serialization.py",
    "hazmat/primitives/hashes.py",
    "hazmat/primitives/asymmetric/__init__.py",
    "hazmat/primitives/asymmetric/ed25519.py",
)
CRYPTOGRAPHY_IMPORT_CLOSURE = {
    "cryptography": "cryptography/__init__.py",
    "cryptography.hazmat.primitives.asymmetric.ed25519": "cryptography/hazmat/primitives/asymmetric/ed25519.py",
    "cryptography.hazmat.bindings._rust": "cryptography/hazmat/bindings/_rust.abi3.so",
}
# The selected cryptography Rust extension dynamically imports this exact native
# module.  It is a required extension file, not permission to copy cffi's
# package or an arbitrary distribution manifest.
CFFI_BACKEND_EXTENSION = "_cffi_backend.cpython-313-x86_64-linux-gnu.so"
# The P1 acceptance closure is exactly these two native package files; seed,
# facts, and entrypoint are separately named NativeGraphClosureV1 artifacts.
NATIVE_RUNTIME_MANIFEST = ("__init__.py", "_native.abi3.so")
EXACT_ID_MAPPINGS = {
    "UidMap": ["0:1:65536"],
    "GidMap": ["0:1:65536"],
}
EXACT_NAMESPACE_MODES = {"PidMode": "private", "IpcMode": "private", "UTSMode": "private",
                         "CgroupMode": "private", "UsernsMode": "private"}


class PodmanAcceptanceFailure(SandboxUnavailable):
    """A requested acceptance gate could not prove its required condition."""


def _json(command: list[str], *, timeout: int = 10) -> dict[str, Any]:
    completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False, close_fds=True, timeout=timeout)
    if completed.returncode:
        raise PodmanAcceptanceFailure(f"podman command failed: {' '.join(command[:3])}: "
                                     f"{completed.stderr.decode('utf-8', 'replace')[:300]}")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PodmanAcceptanceFailure("podman returned non-JSON inspection data") from exc
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, dict):
        raise PodmanAcceptanceFailure("podman inspection object invalid")
    return value


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _clean_id(value: object) -> str:
    return str(value).removeprefix("sha256:").lower()


@dataclass(frozen=True)
class ProbeContract:
    mode: str
    native_proposal: dict[str, Any] | None
    sentinels: tuple[str, ...]
    loopback_port: int
    podman_sockets: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"mode": self.mode, "native_proposal": self.native_proposal, "sentinels": list(self.sentinels),
                "loopback_port": self.loopback_port, "podman_sockets": list(self.podman_sockets)}


class PodmanScope:
    """Evaluator-created scope whose only spawn path is the hardened Podman CLI."""
    def __init__(self, run_id: str, launcher: "PodmanAcceptanceLauncher") -> None:
        self.run_id, self.launcher = run_id, launcher
        self.process: subprocess.Popen[bytes] | None = None
        self.kills: list[str] = []

    def spawn(self, argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        if self.process is not None:
            raise AssertionError("Podman scope spawned more than one worker")
        if argv != self.launcher.run_command():
            raise PodmanAcceptanceFailure("scope spawn command substitution")
        kwargs["close_fds"] = True
        kwargs.pop("pass_fds", None)
        self.process = subprocess.Popen(argv, **kwargs)
        return self.process

    def kill(self, reason: str) -> None:
        self.kills.append(reason)
        self.launcher.stop_container()


class PodmanController:
    def __init__(self, launcher: "PodmanAcceptanceLauncher") -> None:
        self.launcher, self.scopes = launcher, []

    def verify(self) -> bool:
        return self.launcher.preflight_ok

    def create_scope(self, run_id: str) -> PodmanScope:
        scope = PodmanScope(run_id, self.launcher)
        self.scopes.append(scope)
        return scope


class PodmanAcceptanceLauncher:
    """Stages immutable local inputs, then launches a rootless, socket-free worker."""
    def __init__(self, tmp_path: Path, *, contract: ProbeContract, checkout: Path | None = None,
                 native_closure: NativeGraphClosureV1 | None = None) -> None:
        self.tmp_path = Path(tmp_path)
        self.checkout = Path(checkout or Path.cwd()).resolve()
        self.contract, self.native_closure = contract, native_closure
        self.nonce = secrets.token_hex(12)
        prefix = "p1-native" if native_closure is not None else "p0a"
        tag_prefix = "p1-native-acceptance" if native_closure is not None else "p0a-acceptance"
        self.name = f"{prefix}-{self.nonce}"
        self.tag = f"localhost/{tag_prefix}:{self.nonce}"
        self.context = self.tmp_path / "podman-build-context"
        self.evidence_path = self.tmp_path / "podman-acceptance-evidence.json"
        self.evidence: dict[str, Any] = {"run_nonce": self.nonce, "contract": contract.as_dict(),
                                         "base_image_id": BASE_IMAGE_ID}
        self.controller = PodmanController(self)
        self.preflight_ok = False
        self.built = False
        self.derived_image_id: str | None = None
        self._spec: SandboxSpec | None = None

    def spec(self) -> SandboxSpec:
        """A test-only spec used only for entrypoint's staged-artifact validation."""
        if self._spec is None:
            runtime, agent, inputs, work = (self.tmp_path / name for name in ("runtime", "agent", "input", "work"))
            for path in (runtime, agent, inputs, work):
                path.mkdir(parents=True, exist_ok=True)
            source_name = "native_graph_entrypoint.py" if self.native_closure is not None else "hostile_entrypoint.py"
            source = self.checkout / "tests/evaluation/fixtures/podman_acceptance" / source_name
            copied = agent / source_name
            shutil.copyfile(source, copied)
            policy = self.tmp_path / "seccomp-policy-reference"
            policy.write_text(SECCOMP_POLICY, encoding="utf-8")
            entrypoint = StagedEntrypoint.from_staged_agent(agent, f"{source_name.removesuffix('.py')}:run")
            self._spec = SandboxSpec(runtime, agent, inputs,
                                     ("/usr/local/bin/python3", "-I", "-m", "evaluation.p0a.agent_worker"),
                                     work, policy, entrypoint)
        return self._spec

    def preflight(self, spec: SandboxSpec) -> None:
        spec.validate()
        info = _json(["podman", "info", "--format", "json"])
        host = info.get("host") if isinstance(info.get("host"), dict) else {}
        remote = host.get("serviceIsRemote", info.get("serviceIsRemote"))
        rootless = host.get("security", {}).get("rootless") if isinstance(host.get("security"), dict) else None
        if rootless is None:
            rootless = host.get("rootless", info.get("rootless"))
        self.evidence["engine"] = {"rootless": rootless, "serviceIsRemote": remote,
                                   "version": info.get("version", {})}
        if rootless is not True or remote is not False:
            self._write_evidence()
            raise PodmanAcceptanceFailure("Podman acceptance requires local rootless non-remote engine")
        image = _json(["podman", "image", "inspect", BASE_IMAGE_ID, "--format", "json"])
        image_id = _clean_id(image.get("Id"))
        self.evidence["base_image_inspect_id"] = image.get("Id")
        if image_id != BASE_IMAGE_ID:
            self._write_evidence()
            raise PodmanAcceptanceFailure("required cached local base image is absent or mismatched")
        if not Path(SECCOMP_POLICY).is_file():
            self._write_evidence()
            raise PodmanAcceptanceFailure("explicit Podman seccomp policy is absent")
        self.preflight_ok = True
        self.evidence["preflight"] = "passed"
        self._write_evidence()

    @staticmethod
    def _compatible_cryptography_runtime() -> dict[str, Any]:
        """Resolve a local package root for the pinned image's Python ABI."""
        probe = (
            "import importlib.util,json,sys,sysconfig,cryptography; "
            "package=importlib.util.find_spec('cryptography'); "
            "extension=importlib.util.find_spec('cryptography.hazmat.bindings._rust'); "
            "cffi_backend=importlib.util.find_spec('_cffi_backend'); "
            "print(json.dumps({'executable':sys.executable, 'version':list(sys.version_info[:2]), "
            "'version_text':sys.version, 'soabi':sysconfig.get_config_var('SOABI'), "
            "'package_roots':list(package.submodule_search_locations or ()), "
            "'extension_origin':extension.origin if extension else None, "
            "'cffi_backend_origin':cffi_backend.origin if cffi_backend else None, "
            "'cryptography_version':cryptography.__version__}))"
        )
        failures: list[str] = []
        for executable in STAGING_PYTHON_CANDIDATES:
            try:
                completed = subprocess.run([executable, "-I", "-c", probe], stdin=subprocess.DEVNULL,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                                           close_fds=True, timeout=15)
            except OSError as exc:
                failures.append(f"{executable}: {type(exc).__name__}")
                continue
            if completed.returncode:
                failures.append(f"{executable}: unavailable")
                continue
            try:
                runtime = json.loads(completed.stdout)
            except json.JSONDecodeError:
                failures.append(f"{executable}: invalid probe output")
                continue
            if runtime.get("version") != list(WORKER_PYTHON_VERSION):
                failures.append(f"{executable}: Python {runtime.get('version')!r}")
                continue
            if not isinstance(runtime.get("package_roots"), list) or len(runtime["package_roots"]) != 1:
                failures.append(f"{executable}: cryptography root ambiguous")
                continue
            return runtime
        detail = "; ".join(failures) or "no candidate"
        raise PodmanAcceptanceFailure(f"no local Python {WORKER_PYTHON_VERSION[0]}.{WORKER_PYTHON_VERSION[1]} cryptography runtime: {detail}")

    def _stage_cryptography_runtime(self) -> list[dict[str, str]]:
        """Stage an explicit Ed25519 closure from a verified package root.

        ``importlib.metadata.Distribution.files`` is optional metadata, so it
        cannot be the authority for an acceptance build.  A local interpreter
        matching the pinned image's Python version supplies the verified root;
        this keeps a Python 3.12 test runner from staging incompatible native
        files.  Every copied file remains constrained to the finite manifest.
        """
        runtime = self._compatible_cryptography_runtime()
        root = Path(runtime["package_roots"][0]).resolve(strict=True)
        if not root.is_dir():
            raise PodmanAcceptanceFailure("cryptography package root is unavailable")
        expected_extension = root / "hazmat/bindings/_rust.abi3.so"
        expected_cffi_backend = root.parent / CFFI_BACKEND_EXTENSION
        if Path(str(runtime.get("extension_origin"))).resolve(strict=True) != expected_extension:
            raise PodmanAcceptanceFailure("cryptography ABI3 extension does not match the required manifest")
        if Path(str(runtime.get("cffi_backend_origin"))).resolve(strict=True) != expected_cffi_backend:
            raise PodmanAcceptanceFailure("cffi backend extension does not match the required manifest")
        copied: list[dict[str, str]] = []
        for relative_name in CRYPTOGRAPHY_RUNTIME_MANIFEST:
            relative = Path(relative_name)
            source = (root / relative).resolve(strict=True)
            if root not in source.parents or not source.is_file() or source.is_symlink():
                raise PodmanAcceptanceFailure(f"cryptography runtime file unavailable: {relative}")
            target = self.context / "site-packages" / "cryptography" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied.append({"path": f"site-packages/cryptography/{relative.as_posix()}", "digest": _digest(target)})
        if not expected_cffi_backend.is_file() or expected_cffi_backend.is_symlink():
            raise PodmanAcceptanceFailure("required cffi backend extension unavailable")
        backend_target = self.context / "site-packages" / CFFI_BACKEND_EXTENSION
        shutil.copyfile(expected_cffi_backend, backend_target)
        copied.append({"path": f"site-packages/{CFFI_BACKEND_EXTENSION}", "digest": _digest(backend_target)})
        self.evidence["third_party_runtime"] = {
            "package": "cryptography",
            "version": runtime["cryptography_version"],
            "package_root": str(root),
            "manifest": list(CRYPTOGRAPHY_RUNTIME_MANIFEST),
            "files": copied,
            "staging_interpreter": {key: runtime[key] for key in ("executable", "version", "version_text", "soabi")},
        }
        return copied

    def _stage(self, spec: SandboxSpec) -> None:
        if self.context.exists():
            shutil.rmtree(self.context)
        (self.context / "evaluation/p0a").mkdir(parents=True)
        (self.context / "agent").mkdir()
        package = self.checkout / "evaluation"
        copied: list[dict[str, str]] = []
        for relative in WORKER_RUNTIME_FILES:
            source, target = package / relative, self.context / "evaluation" / relative
            if not source.is_file() or source.is_symlink():
                raise PodmanAcceptanceFailure(f"required local source unavailable: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied.append({"path": relative, "digest": _digest(target)})
        third_party = self._stage_cryptography_runtime()
        source_name = "native_graph_entrypoint.py" if self.native_closure is not None else "hostile_entrypoint.py"
        fixture = self.checkout / "tests/evaluation/fixtures/podman_acceptance" / source_name
        if not fixture.is_file() or fixture.is_symlink():
            raise PodmanAcceptanceFailure("local worker entrypoint fixture unavailable")
        shutil.copyfile(fixture, self.context / "agent" / source_name)
        native_inputs: list[dict[str, str]] = []
        if self.native_closure is not None:
            try:
                self.native_closure.validate()
            except ProtocolError as exc:
                raise PodmanAcceptanceFailure("native_closure_unavailable") from exc
            destinations = {
                "substrate_rs/__init__.py": "site-packages/substrate_rs/__init__.py",
                "substrate_rs/_native.abi3.so": "site-packages/substrate_rs/_native.abi3.so",
                "native_graph_proposal_seed.json": "agent/native_graph_proposal_seed.json",
                "native_sealed_graph_action_fact.json": "agent/native_sealed_graph_action_fact.json",
                "native_graph_entrypoint.py": "agent/native_graph_entrypoint.py",
            }
            for source_name, destination in destinations.items():
                source, target = self.native_closure.root / source_name, self.context / destination
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                native_inputs.append({"path": destination, "digest": _digest(target)})
            self.evidence["native_closure"] = self.native_closure.manifest
        (self.context / "agent/probe_contract.json").write_text(json.dumps(self.contract.as_dict(), sort_keys=True), encoding="utf-8")
        containerfile = self.checkout / "tests/evaluation/fixtures/podman_acceptance/Containerfile"
        if not containerfile.is_file() or containerfile.is_symlink():
            raise PodmanAcceptanceFailure("local Containerfile unavailable")
        shutil.copyfile(containerfile, self.context / "Containerfile")
        self.evidence["worker_runtime_manifest"] = list(WORKER_RUNTIME_FILES)
        self.evidence["build_inputs"] = copied + third_party + native_inputs + [
            {"path": f"agent/{source_name}", "digest": _digest(self.context / "agent" / source_name)},
            {"path": "agent/probe_contract.json", "digest": _digest(self.context / "agent/probe_contract.json")},
            {"path": "Containerfile", "digest": _digest(self.context / "Containerfile")},
        ]
        self.evidence["entrypoint_binding"] = spec.entrypoint.worker_binding(spec.agent_root)

    def build_command(self) -> list[str]:
        return ["podman", "build", "--pull=never", "--network=none", "--http-proxy=false", "--layers=false",
                "--file", str(self.context / "Containerfile"), "--tag", self.tag, str(self.context)]

    def import_check_command(self, interpreter: str = WORKER_INTERPRETER_PATHS[0]) -> list[str]:
        if self.derived_image_id is None:
            raise PodmanAcceptanceFailure("worker import check attempted without a derived image")
        expected = self._expected_worker_import_paths()
        closure_script = (
            "import importlib,json; from pathlib import Path; "
            f"expected={expected!r}; files={{name:str(Path(importlib.import_module(name).__file__).resolve()) for name in expected}}; "
            "assert files == expected, (files, expected); print(json.dumps(files, sort_keys=True))"
        )
        return ["podman", "run", "--rm", "--pull=never", "--network=none", "--read-only",
                "--read-only-tmpfs=false", "--tmpfs", "/workspace:rw,nosuid,nodev,noexec,size=64m,mode=0700",
                "--workdir", "/workspace", "--uidmap=0:1:65536", "--gidmap=0:1:65536", "--user", "65534:65534",
                "--pid=private", "--ipc=private", "--uts=private", "--cgroupns=private", "--cap-drop=ALL",
                "--security-opt=no-new-privileges", f"--security-opt=seccomp={SECCOMP_POLICY}", "--pids-limit=64",
                "--memory=256m", "--memory-swap=256m", "--cpus=0.5", "--ulimit", "nofile=128:128", "--ulimit",
                "nproc=64:64", "--log-driver=none", "--env", "HOME=/workspace", "--env", "TMPDIR=/workspace/tmp",
                "--env", "PATH=/usr/local/bin:/usr/bin:/bin", "--env", "LANG=C.UTF-8", "--env", "PYTHONNOUSERSITE=1",
                "--env", "PYTHONSAFEPATH=1", "--env", "PYTHONDONTWRITEBYTECODE=1", "--entrypoint",
                interpreter, self.derived_image_id, "-I", "-c", closure_script]

    def _expected_worker_import_paths(self) -> dict[str, str]:
        root = Path(WORKER_SITE_ROOT)
        expected: dict[str, str] = {}
        for name in WORKER_IMPORT_CLOSURE:
            relative = "__init__.py" if name == "evaluation" else name.removeprefix("evaluation.").replace(".", "/")
            if name == "evaluation.p0a":
                relative += "/__init__.py"
            elif name != "evaluation":
                relative += ".py"
            expected[name] = str(root / relative)
        expected.update({name: f"{WORKER_SITE_PACKAGES}/{relative}" for name, relative in CRYPTOGRAPHY_IMPORT_CLOSURE.items()})
        expected["_cffi_backend"] = f"{WORKER_SITE_PACKAGES}/{CFFI_BACKEND_EXTENSION}"
        if self.native_closure is not None:
            expected["substrate_rs"] = f"{WORKER_SITE_PACKAGES}/substrate_rs/__init__.py"
            expected["substrate_rs._native"] = f"{WORKER_SITE_PACKAGES}/substrate_rs/_native.abi3.so"
        return expected

    def _verify_import_closure(self) -> None:
        checks: list[dict[str, Any]] = []
        expected = self._expected_worker_import_paths()
        for interpreter in WORKER_INTERPRETER_PATHS:
            command = self.import_check_command(interpreter)
            completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       check=False, close_fds=True, timeout=30)
            record: dict[str, Any] = {"interpreter": interpreter, "command": command, "returncode": completed.returncode,
                                      "stderr": completed.stderr.decode("utf-8", "replace")[-2000:]}
            try:
                files = json.loads(completed.stdout)
            except json.JSONDecodeError:
                files = None
            record["loaded_paths"] = files
            checks.append(record)
            if completed.returncode or files != expected:
                self.evidence["import_closure"] = {"checks": checks}
                self._write_evidence()
                detail = record["stderr"] or f"loaded paths: {files!r}"
                raise PodmanAcceptanceFailure(f"derived image worker import closure mismatch: {detail[:300]}")
        self.evidence["import_closure"] = {"checks": checks}

    def _native_health_probe(self) -> None:
        if self.native_closure is None:
            return
        if self.derived_image_id is None:
            raise PodmanAcceptanceFailure("native health probe without derived image")
        script = (
            "import json,substrate_rs; from pathlib import Path; "
            "seed=json.loads(Path('/agent/native_graph_proposal_seed.json').read_text()); "
            "facts=json.loads(Path('/agent/native_sealed_graph_action_fact.json').read_text()); "
            "s=substrate_rs.Substrate(); root=s.add_node(facts['root_type'],facts['root_attrs']); "
            "fact=s.add_node('SealedGraphActionFactV1',facts['proposal']); "
            "s.add_edge_unchecked(root,facts['edge_type'],fact); s.load_seed_manifest(seed); "
            "assert s.tick(16) < 16 and len(s.nodes('GraphActionProposalV1')) == 1"
        )
        command = self.import_check_command()[:-3] + ["-I", "-c", script]
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   check=False, close_fds=True, timeout=30)
        self.evidence["native_health_probe"] = {"command": command, "returncode": completed.returncode,
            "stderr": completed.stderr.decode("utf-8", "replace")[-2000:]}
        if completed.returncode:
            self._write_evidence()
            raise PodmanAcceptanceFailure("native runtime health probe failed")

    def build(self, spec: SandboxSpec) -> None:
        if not self.preflight_ok:
            raise PodmanAcceptanceFailure("Podman build attempted before passed preflight")
        self._stage(spec)
        completed = subprocess.run(self.build_command(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, check=False, close_fds=True, timeout=120)
        self.evidence["build"] = {"command": self.build_command(), "returncode": completed.returncode,
                                  "stderr": completed.stderr.decode("utf-8", "replace")[-2000:]}
        if completed.returncode:
            self._write_evidence()
            raise PodmanAcceptanceFailure("local-only Podman build failed")
        derived = _json(["podman", "image", "inspect", self.tag, "--format", "json"])
        derived_id = derived.get("Id")
        if not isinstance(derived_id, str) or len(_clean_id(derived_id)) != 64:
            raise PodmanAcceptanceFailure("derived local image ID unavailable")
        self.evidence["derived_image_id"] = derived_id
        self.derived_image_id = derived_id
        self._verify_import_closure()
        self._native_health_probe()
        self.built = True
        self._write_evidence()

    def run_command(self) -> list[str]:
        if self._spec is None:
            raise PodmanAcceptanceFailure("Podman worker spec unavailable")
        binding = self._spec.entrypoint.worker_binding(self._spec.agent_root)
        return ["podman", "run", "--name", self.name, "--pull=never", "--network=none", "--read-only",
                "--read-only-tmpfs=false", "--tmpfs", "/workspace:rw,nosuid,nodev,noexec,size=64m,mode=0700",
                "--workdir", "/workspace", "--uidmap=0:1:65536", "--gidmap=0:1:65536", "--user", "65534:65534", "--pid=private",
                "--ipc=private", "--uts=private", "--cgroupns=private", "--cap-drop=ALL",
                "--security-opt=no-new-privileges", f"--security-opt=seccomp={SECCOMP_POLICY}", "--pids-limit=64",
                "--memory=256m", "--memory-swap=256m", "--cpus=0.5", "--ulimit", "nofile=128:128", "--ulimit",
                "nproc=64:64", "--log-driver=none", "--interactive", "--env", "HOME=/workspace", "--env",
                "TMPDIR=/workspace/tmp", "--env", "PATH=/usr/local/bin:/usr/bin:/bin", "--env", "LANG=C.UTF-8",
                "--env", "PYTHONNOUSERSITE=1", "--env", "PYTHONSAFEPATH=1", "--env", "PYTHONDONTWRITEBYTECODE=1",
                "--env", f"P0_STAGED_ENTRYPOINT_BINDING={binding}", self.derived_image_id or self.tag]

    def _inspect_live(self) -> dict[str, Any]:
        value = _json(["podman", "inspect", self.name, "--format", "json"])
        self.evidence["inspect"] = value
        self._assert_inspect(value)
        return value

    @staticmethod
    def _assert_inspect(value: dict[str, Any]) -> None:
        config, host, state = value.get("Config", {}), value.get("HostConfig", {}), value.get("State", {})
        if config.get("User") != "65534:65534" or host.get("IDMappings") != EXACT_ID_MAPPINGS:
            raise PodmanAcceptanceFailure("inspect worker user or ID mappings mismatch")
        if not host.get("ReadonlyRootfs") or {key: host.get(key) for key in EXACT_NAMESPACE_MODES} != EXACT_NAMESPACE_MODES:
            raise PodmanAcceptanceFailure("inspect root or namespace isolation mismatch")
        if host.get("NetworkMode") != "none" or host.get("Privileged") is not False:
            raise PodmanAcceptanceFailure("inspect network or privilege mismatch")
        if host.get("CapAdd") != [] or value.get("EffectiveCaps") not in (None, []):
            raise PodmanAcceptanceFailure("inspect capability isolation mismatch")
        if host.get("NoNewPrivileges") is False:
            raise PodmanAcceptanceFailure("inspect no-new-privileges mismatch")
        if host.get("PidsLimit") != 64 or host.get("Memory") != 268435456 or host.get("MemorySwap") != 268435456:
            raise PodmanAcceptanceFailure("inspect resource ceiling mismatch")
        if not (host.get("NanoCpus") == 500000000 or
                (host.get("NanoCpus") in (None, 0) and host.get("CpuQuota") == 50000 and host.get("CpuPeriod") == 100000)):
            raise PodmanAcceptanceFailure("inspect CPU ceiling mismatch")
        security = host.get("SecurityOpt")
        if not isinstance(security, list) or set(map(str, security)) != {"no-new-privileges", f"seccomp={SECCOMP_POLICY}"}:
            raise PodmanAcceptanceFailure("inspect security policy mismatch")
        expected_ulimits = {"RLIMIT_NOFILE": (128, 128), "RLIMIT_NPROC": (64, 64)}
        ulimits = host.get("Ulimits")
        actual_ulimits = ({str(item.get("Name")): (item.get("Soft"), item.get("Hard")) for item in ulimits}
                         if isinstance(ulimits, list) and all(isinstance(item, dict) for item in ulimits) else None)
        if actual_ulimits != expected_ulimits or host.get("LogConfig", {}).get("Type") != "none":
            raise PodmanAcceptanceFailure("inspect ulimit or logging isolation mismatch")
        tmpfs = host.get("Tmpfs")
        required_tmpfs_options = {"rw", "nosuid", "nodev", "noexec", "size=64m", "mode=0700"}
        if (not isinstance(tmpfs, dict) or set(tmpfs) != {"/workspace"} or
                not isinstance(tmpfs.get("/workspace"), str) or
                not required_tmpfs_options.issubset(set(tmpfs["/workspace"].split(",")))):
            raise PodmanAcceptanceFailure("inspect workspace tmpfs isolation mismatch")
        mounts = value.get("Mounts", [])
        writable = []
        for mount in mounts:
            mount_type, destination, source = mount.get("Type"), mount.get("Destination"), mount.get("Source")
            if mount_type in {"bind", "volume"} or source:
                raise PodmanAcceptanceFailure("inspect found a host bind/volume mount")
            if mount_type == "tmpfs" and not mount.get("RW", False):
                continue
            if mount.get("RW", False):
                writable.append(destination)
        if writable not in ([], ["/workspace"]):
            raise PodmanAcceptanceFailure(f"inspect writable mount mismatch: {writable}")
        if state.get("Running") is not True:
            raise PodmanAcceptanceFailure("container did not remain running for inspection")

    def start(self, spec: SandboxSpec, scope: PodmanScope) -> SandboxProcess:
        self.preflight(spec)
        if not self.built:
            self.build(spec)
        if scope.run_id == "":
            raise SandboxStartFailed("sandbox scope run binding unavailable")
        try:
            command = self.run_command()
            self.evidence["run"] = {"command": command}
            self._write_evidence()
            process = scope.spawn(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, start_new_session=True)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.evidence["run"]["returncode"] = process.returncode
                    self.evidence["run"]["stderr"] = (process.stderr.read().decode("utf-8", "replace")[-2000:]
                                                        if process.stderr else "")
                    self._write_evidence()
                    raise PodmanAcceptanceFailure("Podman worker exited before inspection")
                try:
                    self._inspect_live()
                    break
                except PodmanAcceptanceFailure:
                    time.sleep(0.1)
            else:
                raise PodmanAcceptanceFailure("Podman inspect never met hardened profile")
            self._write_evidence()
            return SandboxProcess(process, scope)
        except Exception as exc:
            try: scope.kill("sandbox_start_failed")
            except Exception: pass
            self._write_evidence()
            if isinstance(exc, PodmanAcceptanceFailure): raise
            raise SandboxStartFailed("sandbox_start_failed") from exc

    def _top_processes(self) -> list[str]:
        command = ["podman", "top", self.name]
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   check=False, close_fds=True, timeout=10)
        if completed.returncode:
            raise PodmanAcceptanceFailure(f"podman top failed: {completed.stderr.decode('utf-8', 'replace')[:300]}")
        lines = [line.rstrip() for line in completed.stdout.decode("utf-8", "replace").splitlines() if line.strip()]
        if not lines:
            raise PodmanAcceptanceFailure("podman top returned no process table")
        return lines[1:]

    def top(self) -> list[str]:
        processes = self._top_processes()
        self.evidence["live_descendants"] = {"command": ["podman", "top", self.name],
                                              "processes": processes}
        self._write_evidence()
        return processes

    def stop_container(self) -> None:
        completed = subprocess.run(["podman", "stop", "--time", "2", self.name], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, close_fds=True, timeout=10)
        self.evidence["stop"] = {"command": ["podman", "stop", "--time", "2", self.name],
                                 "returncode": completed.returncode,
                                 "stderr": completed.stderr.decode("utf-8", "replace")[-1000:]}
        if completed.returncode not in (0, 125):
            self._write_evidence(); raise PodmanAcceptanceFailure("podman stop failed")
        self._write_evidence()

    def verify_stopped(self) -> None:
        value = _json(["podman", "inspect", self.name, "--format", "json"])
        state = value.get("State", {})
        self.evidence["post_stop_inspect"] = value
        if state.get("Running") or state.get("Pid") not in (0, None):
            raise PodmanAcceptanceFailure("container remained running after evaluator stop")
        try:
            processes = self._top_processes()
            top_unavailable = None
        except PodmanAcceptanceFailure as exc:
            # Podman 4.9 rejects top for an already-stopped container.  Accept
            # only that exact state-specific response; any other failure remains
            # a closed acceptance failure.
            if "top can only be used on running containers" not in str(exc):
                raise
            processes, top_unavailable = [], str(exc)
        if processes:
            raise PodmanAcceptanceFailure("container exposes surviving descendant after stop")
        live = self.evidence.get("live_descendants", {}).get("processes", [])
        if not isinstance(live, list) or not live:
            raise PodmanAcceptanceFailure("live descendant evidence invalid")
        self.evidence["post_stop_top"] = {"command": ["podman", "top", self.name],
                                          "processes": processes, "unavailable_after_stop": top_unavailable,
                                          "live_processes_before_stop": live}
        self._write_evidence()

    def collect_worker_evidence(self, process: subprocess.Popen[bytes]) -> dict[str, Any]:
        stderr = process.stderr.read().decode("utf-8", "replace") if process.stderr else ""
        reports = [line.removeprefix("P0_HOSTILE_REPORT=") for line in stderr.splitlines() if line.startswith("P0_HOSTILE_REPORT=")]
        if len(reports) != 1: raise PodmanAcceptanceFailure("worker did not emit exactly one bounded hostile report")
        try: report = json.loads(reports[0])
        except json.JSONDecodeError as exc: raise PodmanAcceptanceFailure("worker hostile report invalid") from exc
        if not isinstance(report, dict): raise PodmanAcceptanceFailure("worker hostile report invalid")
        self.evidence["worker_stderr"] = stderr[-8192:]
        self.evidence["worker_report"] = report
        self._write_evidence()
        return report

    def verify_sentinels(self, snapshots: dict[str, tuple[str, tuple[str, ...]]]) -> None:
        after = {path: (_digest(Path(path)), tuple(sorted(p.name for p in Path(path).parent.iterdir()))) for path in snapshots}
        self.evidence["sentinels"] = {"before": snapshots, "after": after}
        if after != snapshots: raise PodmanAcceptanceFailure("host sentinel changed during worker probe")
        self._write_evidence()

    def cleanup(self) -> None:
        """Remove only this launcher's task-tagged artifacts, with evidence first."""
        prefixes = (("p0a-", "localhost/p0a-acceptance:"), ("p1-native-", "localhost/p1-native-acceptance:"))
        if not any(self.name.startswith(name_prefix) and self.tag.startswith(tag_prefix) for name_prefix, tag_prefix in prefixes):
            raise PodmanAcceptanceFailure("refusing cleanup outside the acceptance artifact prefixes")
        inventory_command = ["podman", "ps", "-a", "--filter", f"name=^{self.name}$", "--format", "{{.Names}}"]
        image_command = ["podman", "image", "ls", "--filter", f"reference={self.tag}", "--format", "{{.Repository}}:{{.Tag}}"]
        inventory = subprocess.run(inventory_command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, check=False, close_fds=True, timeout=15)
        images = subprocess.run(image_command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=False, close_fds=True, timeout=15)
        names = [line for line in inventory.stdout.decode("utf-8", "replace").splitlines() if line]
        tags = [line for line in images.stdout.decode("utf-8", "replace").splitlines() if line]
        if inventory.returncode or images.returncode or any(name != self.name for name in names) or any(tag != self.tag for tag in tags):
            self.evidence["cleanup"] = {"prefix_confirmed": False, "inventory_command": inventory_command,
                                        "image_command": image_command, "containers": names, "images": tags}
            self._write_evidence()
            raise PodmanAcceptanceFailure("P0A cleanup inventory was not exactly scoped to this launcher")
        cleanup: dict[str, Any] = {"prefix_confirmed": True, "container_name_prefix": "p0a-",
                                    "image_tag_prefix": "localhost/p0a-acceptance:", "before": {
                                        "containers": names, "container_count": len(names), "images": tags,
                                        "image_count": len(tags)}, "commands": []}
        failures: list[str] = []
        if names:
            for command in (["podman", "stop", "--time", "2", self.name], ["podman", "rm", self.name]):
                completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           check=False, close_fds=True, timeout=15)
                cleanup["commands"].append({"command": command, "returncode": completed.returncode,
                                            "stderr": completed.stderr.decode("utf-8", "replace")[-1000:]})
                if completed.returncode:
                    failures.append(" ".join(command[:3]))
                    break
        if not failures and tags:
            command = ["podman", "rmi", self.tag]
            completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       check=False, close_fds=True, timeout=30)
            cleanup["commands"].append({"command": command, "returncode": completed.returncode,
                                        "stderr": completed.stderr.decode("utf-8", "replace")[-1000:]})
            if completed.returncode:
                failures.append(" ".join(command[:2]))
        post_containers = subprocess.run(inventory_command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         check=False, close_fds=True, timeout=15)
        post_images = subprocess.run(image_command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     check=False, close_fds=True, timeout=15)
        cleanup["after"] = {"containers": post_containers.stdout.decode("utf-8", "replace").splitlines(),
                            "container_count": len([line for line in post_containers.stdout.splitlines() if line]),
                            "images": post_images.stdout.decode("utf-8", "replace").splitlines(),
                            "image_count": len([line for line in post_images.stdout.splitlines() if line])}
        self.evidence["cleanup"] = cleanup
        self._write_evidence()
        if failures or post_containers.returncode or post_images.returncode or cleanup["after"]["container_count"] or cleanup["after"]["image_count"]:
            raise PodmanAcceptanceFailure("scoped P0A cleanup did not remove all launcher artifacts")

    def _write_evidence(self) -> None:
        self.evidence_path.write_text(json.dumps(self.evidence, sort_keys=True, indent=2, default=str), encoding="utf-8")


def snapshot_sentinels(paths: list[Path]) -> dict[str, tuple[str, tuple[str, ...]]]:
    return {str(path): (_digest(path), tuple(sorted(item.name for item in path.parent.iterdir()))) for path in paths}


def assert_hostile_report(report: dict[str, Any], *, proposal_digest: str | None = None) -> None:
    if report.get("fds") != [0, 1, 2] or any(report.get("mmap", {}).get(str(fd)) == "ok" for fd in (0, 1, 2)):
        raise AssertionError("hostile worker retained or mmaped an unexpected descriptor")
    for item in report.get("paths", []):
        if any(item.get(key) == "ok" for key in ("listdir", "stat", "write")):
            raise AssertionError("hostile worker accessed a host sentinel")
    for item in report.get("network", []):
        if item.get("result") == "ok": raise AssertionError("hostile worker reached a network/socket target")
    if proposal_digest is not None and report.get("submitted_proposal_digests") != [proposal_digest]:
        raise AssertionError("worker did not submit exactly its native graph proposal")
