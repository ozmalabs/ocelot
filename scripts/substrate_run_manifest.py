"""Shared provenance manifest capture for substrate benchmark runners.

This captures benchmark inputs explicitly and summarizes dirty workspace
state without reading the contents of every unrelated/generated artifact.
"""
from __future__ import annotations

import hashlib
import atexit
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
ENV_KEYS = (
    "PYTHONPATH", "PYTHONHASHSEED", "RUSTFLAGS", "RUST_LOG",
    "RAYON_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS", "CUDA_VISIBLE_DEVICES", "TOKENIZERS_PARALLELISM",
)


class _Tee(io.TextIOBase):
    def __init__(self, console, log_stream):
        self.console = console
        self.log_stream = log_stream
        self.lock = threading.Lock()

    @property
    def encoding(self):
        return getattr(self.console, "encoding", "utf-8")

    def write(self, value):
        with self.lock:
            self.console.write(value)
            self.log_stream.write(value)
        return len(value)

    def flush(self):
        with self.lock:
            self.console.flush()
            if not self.log_stream.closed:
                self.log_stream.flush()

    def isatty(self):
        return self.console.isatty()


def start_console_capture(run_id: str) -> dict:
    """Tee parent-process stdout/stderr to a durable run log."""
    log_dir = ROOT / "evaluation/run_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{run_id}.stdout_stderr.log"
    stream = log_path.open("w", encoding="utf-8", errors="backslashreplace")
    state = {"path": log_path, "stream": stream,
             "old_stdout": sys.stdout, "old_stderr": sys.stderr}
    state["tee_stdout"] = _Tee(sys.stdout, stream)
    state["tee_stderr"] = _Tee(sys.stderr, stream)
    sys.stdout = state["tee_stdout"]
    sys.stderr = state["tee_stderr"]

    def cleanup():
        if not stream.closed:
            if sys.stdout is state["tee_stdout"]:
                sys.stdout = state["old_stdout"]
            if sys.stderr is state["tee_stderr"]:
                sys.stderr = state["old_stderr"]
            stream.flush()
            stream.close()
    state["cleanup"] = cleanup
    atexit.register(cleanup)
    return state


def finish_console_capture(state: dict) -> dict:
    state["cleanup"]()
    path = state["path"]
    return {"path": str(path.relative_to(ROOT)), "sha256": _sha_file(path),
            "bytes": path.stat().st_size,
            "scope": "parent-process stdout/stderr before the final structured summary print"}


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def _dirty_workspace() -> dict:
    status = _git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    tracked = _git("diff", "--name-only", "-z", "HEAD")
    untracked = _git("ls-files", "--others", "--exclude-standard", "-z")
    tracked_records: list[dict] = []
    for raw in sorted(set(filter(None, tracked.split(b"\0")))):
        rel = os.fsdecode(raw)
        path = ROOT / rel
        if path.is_symlink():
            digest = _sha_bytes(os.fsencode(os.readlink(path)))
            kind = "symlink"
        elif path.is_file():
            digest = _sha_file(path)
            kind = "file"
        elif path.exists():
            digest, kind = None, "non_file"
        else:
            digest, kind = None, "deleted"
        tracked_records.append({"path": rel, "kind": kind, "sha256": digest})
    tracked_payload = json.dumps(tracked_records, sort_keys=True, separators=(",", ":")).encode()
    untracked_paths = sorted(os.fsdecode(p) for p in untracked.split(b"\0") if p)
    return {
        "status_porcelain_sha256": _sha_bytes(status),
        "status_record_count": len([p for p in status.split(b"\0") if p]),
        "tracked_dirty_file_count": len(tracked_records),
        "tracked_dirty_content_index_sha256": _sha_bytes(tracked_payload),
        "untracked_path_count": len(untracked_paths),
        "untracked_path_inventory_sha256": _sha_bytes("\0".join(untracked_paths).encode("utf-8", "surrogateescape")),
        "scope_note": "Unrelated untracked artifact contents are not recursively hashed; benchmark-relevant files are content-hashed in explicit_inputs.",
    }


def _hardware() -> dict:
    cpu_model = None
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(errors="replace").splitlines():
            if line.lower().startswith(("model name", "hardware")) and ":" in line:
                cpu_model = line.split(":", 1)[1].strip()
                break
    try:
        total_memory = int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (ValueError, OSError, AttributeError):
        total_memory = None
    usage = shutil.disk_usage(ROOT)
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "cpu_model": cpu_model or platform.processor() or None,
        "logical_cpu_count": os.cpu_count(),
        "memory_total_bytes": total_memory,
        "workspace_filesystem_total_bytes": usage.total,
        "workspace_filesystem_free_bytes": usage.free,
    }


def _version(command: str) -> str | None:
    try:
        return subprocess.check_output([command, "--version"], cwd=ROOT, text=True,
                                       stderr=subprocess.STDOUT, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def capture_run_manifest(
    *,
    run_id: str,
    runner: str,
    protocol_files: Iterable[str] = (),
    source_files: Iterable[str] = (),
    data_files: Iterable[str] = (),
    analysis_files: Iterable[str] = (),
    started_utc: str | None = None,
    exit_status: int | None = None,
    stdout_stderr_capture: dict | None = None,
    child_processes: list[dict] | None = None,
) -> dict:
    """Capture common reproducibility metadata at the end of a measured run."""
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint

    groups = {
        "runner": [runner],
        "protocol": list(protocol_files),
        "source": list(source_files),
        "data": list(data_files),
        "analysis": list(analysis_files),
        "build_inputs": ["runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock"],
        "manifest_capture": ["scripts/substrate_run_manifest.py"],
    }
    explicit: dict[str, dict] = {}
    for group, names in groups.items():
        for name in names:
            rel = str(Path(name))
            path = (ROOT / rel).resolve()
            if not path.is_file():
                explicit[rel] = {"group": group, "exists": False, "sha256": None}
            else:
                explicit[rel] = {"group": group, "exists": True, "sha256": _sha_file(path)}

    native_path = None
    native_hash = None
    native_manifest_hash = None
    try:
        from substrate_rs import _native
        native_path = str(Path(_native.__file__).resolve())
        native_hash = _sha_file(Path(native_path))
        native_manifest = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
        native_manifest_hash = _sha_file(native_manifest) if native_manifest.is_file() else None
    except (ImportError, OSError):
        pass
    stale = build_is_stale(str(ROOT))
    env = {key: value for key, value in os.environ.items()
           if key in ENV_KEYS or key.startswith("SUBSTRATE_")}
    return {
        "manifest_schema": "substrate-run-manifest-v1",
        "run_id": run_id,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
            "run_started_utc": started_utc,
            "run_end_utc": datetime.now(timezone.utc).isoformat(),
            "exit_status": exit_status,
            "stdout_stderr_capture": stdout_stderr_capture,
            "stdout_stderr_note": None if stdout_stderr_capture else "No separate stdout/stderr log was captured.",
        "repository": {
            "root": str(ROOT),
            "commit": _git("rev-parse", "HEAD").decode().strip(),
            "dirty_workspace": _dirty_workspace(),
        },
        "execution": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "argv": [sys.executable, *sys.argv],
            "command_display": " ".join([sys.executable, *sys.argv]),
            "relevant_environment": env,
            "child_processes": child_processes or [],
        },
        "toolchain": {"rustc": _version("rustc"), "cargo": _version("cargo")},
        "hardware": _hardware(),
        "engine": {
            "native_extension_path": native_path,
            "native_extension_sha256": native_hash,
            "native_build_manifest_sha256": native_manifest_hash,
            "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
            "build_is_stale": bool(stale),
        },
        "explicit_inputs": explicit,
    }
