"""Finite, local-only runtime closure handling for the P4 native worker.

The native worker is deliberately staged as an ELF closure rather than relying
on a distribution image or a host loader at launch time.  Every copied byte is
measured before and after staging; missing local artifacts are a hard failure.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, parse_canonical
from .protocol import P4ProtocolError, is_digest

_RUNTIME_SCHEMA = "P4R0NativeRuntimeClosureV1"
_INTERPRETER = re.compile(r"Requesting program interpreter: (.+?)\]")
_ABSOLUTE_LIBRARY = re.compile(r"(?:=>\s*)?(/(?:lib|lib64)(?:/[^\s()]+)+)")


def _regular(path: Path, label: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=True)
    except OSError as exc:
        raise P4ProtocolError(f"P4 {label} unavailable") from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise P4ProtocolError(f"P4 {label} unavailable")
    return resolved


def _host_artifact(path: Path, label: str) -> Path:
    value = _regular(path, label)
    approved = value.parts[1] in {"lib", "lib64", "etc"} or (
        value.parts[1] == "usr" and len(value.parts) > 2 and value.parts[2] in {"lib", "lib64"}
    )
    if not approved:
        raise P4ProtocolError(f"P4 {label} outside approved roots")
    return value


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(65536), b""):
                h.update(block)
    except OSError as exc:
        raise P4ProtocolError("P4 runtime digest") from exc
    return "sha256:" + h.hexdigest()


def _run(argv: list[str], failure: str, *, accept: set[int] | None = None) -> str:
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, check=False, close_fds=True,
                                timeout=10, text=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise P4ProtocolError(f"P4 {failure}") from exc
    if result.returncode not in (accept or {0}):
        raise P4ProtocolError(f"P4 {failure}")
    return result.stdout


def _elf_identity(path: Path) -> dict[str, int]:
    raw = _regular(path, "runtime ELF").read_bytes()[:20]
    if len(raw) < 20 or raw[:4] != b"\x7fELF" or raw[5] != 1 or raw[4] not in (1, 2):
        raise P4ProtocolError("P4 native worker must be a little-endian ELF")
    return {"elf_class": raw[4], "elf_machine": int.from_bytes(raw[18:20], "little")}


def _interpreter(binary: Path) -> Path:
    headers = _run(["readelf", "-l", str(binary)], "runtime interpreter inspection")
    match = _INTERPRETER.search(headers)
    if not match:
        raise P4ProtocolError("P4 runtime interpreter absent")
    value = Path(match.group(1).strip())
    if not value.is_absolute() or value.parts[1] not in {"lib", "lib64"}:
        raise P4ProtocolError("P4 runtime interpreter path")
    return value


def _openssl_data() -> list[Path]:
    # The worker currently uses OpenSSL through the local crypto/runtime stack
    # only when its native dependency closure asks for it.  Keep the data set
    # finite: the config file is the only ambient OpenSSL data accepted here;
    # certificates or provider trees must be explicitly added and measured by
    # a future worker contract rather than copied from the host implicitly.
    config = Path("/etc/ssl/openssl.cnf")
    return [_host_artifact(config, "OpenSSL runtime data")] if config.exists() else []


def measure_runtime_closure(worker: Path) -> dict[str, Any]:
    """Measure exact loader/DT_NEEDED/OpenSSL support files from local host state."""
    worker = _regular(worker, "native worker")
    identity = _elf_identity(worker)
    interpreter = _interpreter(worker)
    ldd = _run(["ldd", str(worker)], "runtime closure inspection")
    sources: dict[str, Path] = {str(interpreter): interpreter}
    for raw in _ABSOLUTE_LIBRARY.findall(ldd):
        image = Path(raw)
        if image.parts[1] not in {"lib", "lib64"}:
            raise P4ProtocolError("P4 runtime library path")
        if str(image) in sources:
            continue
        sources[str(image)] = _host_artifact(image, "runtime library")
    if len(sources) < 2:
        raise P4ProtocolError("P4 runtime closure incomplete")
    files = []
    for name, source in sorted(sources.items()):
        if _elf_identity(source) != identity:
            raise P4ProtocolError("P4 runtime ABI mismatch")
        files.append({"path": name, "digest": _digest(source), **identity})
    support: list[dict[str, str]] = []
    cache = _host_artifact(Path("/etc/ld.so.cache"), "runtime loader cache")
    support.append({"path": "/etc/ld.so.cache", "digest": _digest(cache)})
    # Only include OpenSSL data when the measured DT_NEEDED closure uses it.
    if any("libssl" in path or "libcrypto" in path for path in sources):
        for data in _openssl_data():
            support.append({"path": str(data), "digest": _digest(data)})
    return {"schema": _RUNTIME_SCHEMA, "binary_digest": _digest(worker),
            "interpreter": str(interpreter), "files": files,
            "support_files": sorted(support, key=lambda item: item["path"])}


def validate_runtime_closure(path: Path, *, worker_digest: str) -> dict[str, Any]:
    """Validate a canonical, finite manifest without consulting host state."""
    try:
        manifest = parse_canonical(_regular(path, "runtime closure").read_bytes())
    except Exception as exc:
        raise P4ProtocolError("P4 runtime closure manifest") from exc
    if (set(manifest) != {"schema", "binary_digest", "interpreter", "files", "support_files"}
            or manifest.get("schema") != _RUNTIME_SCHEMA
            or manifest.get("binary_digest") != worker_digest
            or not isinstance(manifest.get("interpreter"), str)
            or not isinstance(manifest.get("files"), list) or len(manifest["files"]) < 2
            or not isinstance(manifest.get("support_files"), list) or not manifest["support_files"]):
        raise P4ProtocolError("P4 runtime closure manifest")
    seen: set[str] = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "digest", "elf_class", "elf_machine"}:
            raise P4ProtocolError("P4 runtime closure entry")
        value = entry["path"]
        if (not isinstance(value, str) or not value.startswith(("/lib/", "/lib64/"))
                or value in seen or not is_digest(entry["digest"])
                or entry["elf_class"] not in (1, 2) or type(entry["elf_machine"]) is not int):
            raise P4ProtocolError("P4 runtime closure entry")
        seen.add(value)
    if manifest["interpreter"] not in seen:
        raise P4ProtocolError("P4 runtime interpreter missing from closure")
    for entry in manifest["support_files"]:
        if (not isinstance(entry, dict) or set(entry) != {"path", "digest"}
                or not isinstance(entry["path"], str) or not entry["path"].startswith("/etc/")
                or not is_digest(entry["digest"])):
            raise P4ProtocolError("P4 runtime support entry")
    return manifest


def stage_runtime_context(*, context: Path, worker: Path, containerfile: Path,
                          runtime_name: str = "p4_native_readiness_worker") -> dict[str, Any]:
    """Copy a measured native closure into a scratch build context."""
    context = Path(context)
    if context.exists():
        if context.is_symlink() or not context.is_dir() or any(context.iterdir()):
            raise P4ProtocolError("P4 runtime context must be fresh")
    context.mkdir(mode=0o700, parents=True, exist_ok=True)
    worker = _regular(worker, "native worker")
    manifest = measure_runtime_closure(worker)
    source_containerfile = _regular(containerfile, "Containerfile")
    shutil.copyfile(source_containerfile, context / "Containerfile")
    staged_worker = context / runtime_name
    shutil.copyfile(worker, staged_worker)
    staged_worker.chmod(0o555)
    sources = {Path(entry["path"]).name: _host_artifact(Path(entry["path"]), "runtime closure source")
               for entry in manifest["files"]}
    for entry in manifest["files"]:
        destination = context / Path(entry["path"]).relative_to("/")
        destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        source = sources.get(Path(entry["path"]).name)
        if source is None:
            raise P4ProtocolError("P4 runtime closure source")
        shutil.copyfile(source, destination)
        destination.chmod(0o555 if entry["path"] == manifest["interpreter"] else 0o444)
        if _digest(destination) != entry["digest"]:
            raise P4ProtocolError("P4 runtime closure copy mismatch")
    for entry in manifest["support_files"]:
        destination = context / Path(entry["path"]).relative_to("/")
        destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        shutil.copyfile(_host_artifact(Path(entry["path"]), "runtime support"), destination)
        destination.chmod(0o444)
        if _digest(destination) != entry["digest"]:
            raise P4ProtocolError("P4 runtime support copy mismatch")
    target = context / "runtime-closure.json"
    target.write_bytes(canonical_bytes(manifest))
    target.chmod(0o400)
    return manifest


def stage_embedded_image_context(*, context: Path, worker: Path, containerfile: Path,
                                 trust_artifact: Path, fixture: Path, arms: Path | None = None,
                                 runtime_name: str = "p4_native_readiness_worker") -> dict[str, Any]:
    """Create the finite scratch-image context used by the P4 launcher.

    The runtime closure is copied first, then the fixed trust and fixture
    bytes are copied to their image-owned paths.  Nothing in the resulting
    image launch needs a host bind mount; the context itself is the measured
    boundary used to build the image.
    """
    context = Path(context)
    trust_artifact = _regular(trust_artifact, "trusted evaluator artifact")
    fixture = _regular(fixture, "sealed input fixture")
    if arms is not None:
        arms = _regular(arms, "sealed mechanics arms")
    manifest = stage_runtime_context(context=context, worker=worker,
                                     containerfile=containerfile,
                                     runtime_name=runtime_name)
    trust_target = context / "trust" / "p4-trusted-evaluator.json"
    input_target = context / "input" / "p4_r0_public_bundle_v1.json"
    arms_target = context / "input" / "p4_r0_mechanics_arms_v1.json"
    trust_target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    input_target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    shutil.copyfile(trust_artifact, trust_target)
    shutil.copyfile(fixture, input_target)
    if arms is not None:
        shutil.copyfile(arms, arms_target)
    trust_target.chmod(0o444)
    input_target.chmod(0o444)
    for target in (context / runtime_name, trust_target, input_target, arms_target if arms is not None else input_target):
        if target.is_symlink() or not target.is_file():
            raise P4ProtocolError("P4 embedded image path")
    return manifest


def post_build_runtime_probe(worker: Path) -> dict[str, Any]:
    """Prove the staged native executable reaches its runtime before protocol use.

    A readiness worker is expected to reject an empty frame; return code 65 is
    therefore the successful startup signal.  Any loader failure or timeout is
    unavailable and callers must fail closed.
    """
    worker = _regular(worker, "post-build worker")
    _elf_identity(worker)
    try:
        result = subprocess.run([str(worker)], input=b"", stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, close_fds=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise P4ProtocolError("P4 post-build runtime probe") from exc
    if result.returncode not in {0, 65}:
        raise P4ProtocolError("P4 post-build runtime probe")
    return {"schema": "P4R0NativeRuntimeProbeV1", "worker_digest": _digest(worker),
            "startup": True, "returncode": result.returncode}
