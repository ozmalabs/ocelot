"""Measured, finite local closure staging for the scratch P2 worker.

This module never pulls images or resolves packages.  It copies exactly the
interpreter and shared objects measured from a supplied local ELF binary and
writes a canonical manifest that is bound into the release lock.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, parse_canonical
from .protocol import P2ProtocolError

_RUNTIME_SCHEMA = "P2NativeRuntimeClosureV1"
_ABSOLUTE_LIBRARY = re.compile(r"(?<!\S)(/[A-Za-z0-9_./+:-]+\.so(?:\.[0-9]+)*)")
_INTERPRETER = re.compile(r"Requesting program interpreter:\s*([^\]]+)")


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _regular(path: Path, label: str) -> Path:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise P2ProtocolError(f"P2 {label} unavailable")
    return path.resolve(strict=True)


def _host_artifact(path: Path, label: str) -> Path:
    """Resolve the host linker alias, but stage it as an ordinary file."""
    try:
        resolved = Path(path).resolve(strict=True)
    except OSError as exc:
        raise P2ProtocolError(f"P2 {label} unavailable") from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise P2ProtocolError(f"P2 {label} unavailable")
    return resolved


def _elf_identity(path: Path) -> dict[str, int]:
    raw = _host_artifact(path, "runtime ELF").read_bytes()[:20]
    if len(raw) < 20 or raw[:4] != b"\x7fELF" or raw[5] != 1 or raw[4] not in (1, 2):
        raise P2ProtocolError("P2 runtime ELF identity")
    return {"elf_class": raw[4], "elf_machine": int.from_bytes(raw[18:20], "little")}


def _run(argv: list[str], failure: str) -> str:
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, check=False, close_fds=True,
                                timeout=10, text=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise P2ProtocolError(f"P2 {failure}") from exc
    if result.returncode:
        raise P2ProtocolError(f"P2 {failure}")
    return result.stdout


def _interpreter(binary: Path) -> Path:
    headers = _run(["readelf", "-l", str(binary)], "runtime interpreter inspection")
    match = _INTERPRETER.search(headers)
    if not match:
        raise P2ProtocolError("P2 runtime interpreter absent")
    value = Path(match.group(1).strip())
    if not value.is_absolute() or value.parts[1] not in {"lib", "lib64"}:
        raise P2ProtocolError("P2 runtime interpreter path")
    _host_artifact(value, "runtime interpreter")
    return value


def measure_runtime_closure(worker: Path) -> dict[str, Any]:
    """Measure the worker's loader/DT_NEEDED closure from local host artifacts."""
    worker = _regular(worker, "native worker")
    worker_elf = _elf_identity(worker)
    interpreter = _interpreter(worker)
    ldd = _run(["ldd", str(worker)], "runtime closure inspection")
    sources: dict[str, Path] = {str(interpreter): _host_artifact(interpreter, "runtime interpreter")}
    for raw in _ABSOLUTE_LIBRARY.findall(ldd):
        image_path = Path(raw)
        if not image_path.is_absolute() or image_path.parts[1] not in {"lib", "lib64"}:
            raise P2ProtocolError("P2 runtime library path")
        destination = str(image_path)
        if destination == str(interpreter):
            continue
        if destination in sources:
            raise P2ProtocolError("P2 duplicate runtime library")
        sources[destination] = _host_artifact(image_path, "runtime library")
    if len(sources) < 2:
        raise P2ProtocolError("P2 runtime closure incomplete")
    files: list[dict[str, Any]] = []
    for image_name, source in sorted(sources.items()):
        identity = _elf_identity(source)
        if identity != worker_elf:
            raise P2ProtocolError("P2 runtime ABI mismatch")
        files.append({"path": image_name, "digest": _digest(source), **identity})
    cache = _host_artifact(Path("/etc/ld.so.cache"), "runtime loader cache")
    return {"schema": _RUNTIME_SCHEMA, "binary_digest": _digest(worker),
            "interpreter": str(interpreter), "files": files,
            "support_files": [{"path": "/etc/ld.so.cache", "digest": _digest(cache)}]}


def stage_runtime_context(*, context: Path, worker: Path, containerfile: Path,
                          runtime_name: str = "p2_native_worker") -> dict[str, Any]:
    """Create a scratch build context with only a measured runtime closure."""
    context = Path(context)
    if context.exists() and (context.is_symlink() or not context.is_dir()):
        raise P2ProtocolError("P2 runtime context")
    context.mkdir(mode=0o700, parents=True, exist_ok=True)
    manifest = measure_runtime_closure(worker)
    source_containerfile = _regular(containerfile, "Containerfile")
    shutil.copyfile(source_containerfile, context / "Containerfile")
    if runtime_name not in {"p2_native_worker", "p2_bypass_probe", "python3"}:
        raise P2ProtocolError("P2 runtime entrypoint")
    staged_worker = context / runtime_name
    shutil.copyfile(_regular(worker, "native worker"), staged_worker)
    staged_worker.chmod(0o555)
    source_by_name = {Path(path).name: _host_artifact(Path(path), "runtime library")
                      for path in _ABSOLUTE_LIBRARY.findall(_run(["ldd", str(worker)], "runtime closure inspection"))}
    source_by_name[Path(manifest["interpreter"]).name] = _host_artifact(Path(manifest["interpreter"]), "runtime interpreter")
    for entry in manifest["files"]:
        destination = context / Path(entry["path"]).relative_to("/")
        destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        destination.parent.chmod(0o755)
        source = source_by_name.get(Path(entry["path"]).name)
        if source is None:
            raise P2ProtocolError("P2 runtime closure source")
        shutil.copyfile(source, destination)
        destination.chmod(0o555 if entry["path"] == manifest["interpreter"] else 0o444)
        if _digest(destination) != entry["digest"]:
            raise P2ProtocolError("P2 runtime closure copy mismatch")
    for entry in manifest["support_files"]:
        destination = context / Path(entry["path"]).relative_to("/")
        destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        destination.parent.chmod(0o755)
        source = _host_artifact(Path(entry["path"]), "runtime support")
        shutil.copyfile(source, destination)
        destination.chmod(0o444)
        if _digest(destination) != entry["digest"]:
            raise P2ProtocolError("P2 runtime support copy mismatch")
    (context / "lib").mkdir(mode=0o755, exist_ok=True)
    (context / "lib").chmod(0o755)
    target = context / "closure.json"
    target.write_bytes(canonical_bytes(manifest))
    target.chmod(0o400)
    return manifest


def validate_runtime_closure(path: Path, *, worker_digest: str) -> dict[str, Any]:
    """Validate the locked finite closure manifest without inspecting host state."""
    try:
        manifest = parse_canonical(_regular(path, "runtime closure").read_bytes())
    except Exception as exc:
        raise P2ProtocolError("P2 runtime closure manifest") from exc
    if (set(manifest) != {"schema", "binary_digest", "interpreter", "files", "support_files"}
            or manifest.get("schema") != _RUNTIME_SCHEMA
            or manifest.get("binary_digest") != worker_digest
            or not isinstance(manifest.get("interpreter"), str)
            or not isinstance(manifest.get("files"), list) or not manifest["files"]
            or not isinstance(manifest.get("support_files"), list) or len(manifest["support_files"]) != 1):
        raise P2ProtocolError("P2 runtime closure manifest")
    seen: set[str] = set()
    interpreter_seen = False
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "digest", "elf_class", "elf_machine"}:
            raise P2ProtocolError("P2 runtime closure entry")
        path_value = entry["path"]
        if (not isinstance(path_value, str) or not path_value.startswith("/lib")
                or path_value in seen or entry["digest"] is None
                or entry["elf_class"] not in (1, 2) or type(entry["elf_machine"]) is not int):
            raise P2ProtocolError("P2 runtime closure entry")
        if not isinstance(entry["digest"], str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", entry["digest"]):
            raise P2ProtocolError("P2 runtime closure digest")
        seen.add(path_value)
        interpreter_seen |= path_value == manifest["interpreter"]
    if not interpreter_seen:
        raise P2ProtocolError("P2 runtime closure interpreter")
    support = manifest["support_files"][0]
    if (not isinstance(support, dict) or set(support) != {"path", "digest"}
            or support.get("path") != "/etc/ld.so.cache"
            or not isinstance(support.get("digest"), str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", support["digest"])):
        raise P2ProtocolError("P2 runtime closure support")
    return manifest



def stage_python_bypass_context(*, context: Path, python_binary: Path, probe: Path,
                                containerfile: Path) -> dict[str, Any]:
    """Stage a finite local Python hostile-probe image with no package install/pull.

    The worker closure remains native-only. This helper is solely for the
    separately digest-pinned hostile image and copies a selected, local Python
    standard library so valid Python can exercise the documented bypass routes.
    """
    context = Path(context)
    python_binary = _regular(python_binary, "Python probe binary")
    probe = _regular(probe, "Python probe script")
    manifest = stage_runtime_context(context=context, worker=python_binary,
        containerfile=containerfile, runtime_name="python3")
    version_details = _run([str(python_binary), "-I", "-S", "-c",
                            "import sys,sysconfig; print(f'{sys.version_info[0]}.{sys.version_info[1]}'); print(sysconfig.get_path('stdlib'))"],
                           "Python probe version").splitlines()
    if len(version_details) != 2:
        raise P2ProtocolError("P2 Python probe version")
    version, standard_library_value = version_details
    if not re.fullmatch(r"3\.\d+", version):
        raise P2ProtocolError("P2 Python probe version")
    standard_library = Path(standard_library_value).resolve(strict=True)
    if standard_library.is_symlink() or not standard_library.is_dir():
        raise P2ProtocolError("P2 Python standard library")
    target_library = context / "python-lib" / f"python{version}"
    ignored = shutil.ignore_patterns("__pycache__", "test", "tests", "ensurepip", "idlelib",
                                    "tkinter", "turtledemo", "venv", "site-packages",
                                    "dist-packages", "config-*")
    shutil.copytree(standard_library, target_library, symlinks=False, ignore=ignored)
    for path in target_library.rglob("*"):
        if path.is_symlink():
            raise P2ProtocolError("P2 Python probe symlink")
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    target_probe = context / "p2_python_bypass_probe.py"
    shutil.copyfile(probe, target_probe)
    target_probe.chmod(0o444)
    return manifest
