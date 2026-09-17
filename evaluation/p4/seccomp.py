"""Measured, restrictive seccomp policy for the P4 native worker."""
from __future__ import annotations

import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, parse_canonical
from .protocol import P4ProtocolError
from .staging import digest_file

# Loader, Rust stdlib, libc and OpenSSL startup calls.  This is an explicit
# small floor; a profile may add only calls observed by the local startup
# probe and those calls must remain in this reviewed vocabulary.
REQUIRED_SYSCALLS = frozenset({
    "read", "write", "close", "fstat", "newfstatat", "lseek", "readlink",
    "openat", "pread64", "mmap", "mprotect", "munmap", "brk", "madvise",
    "futex", "clock_gettime", "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
    "arch_prctl", "set_tid_address", "set_robust_list", "rseq", "prlimit64",
    "getrandom", "ioctl", "exit", "exit_group",
})
# These are the measured additions in the pinned x86-64 startup profile.  A
# syscall is not accepted merely because it is identifier-shaped: it must be
# explicitly reviewed or measured for this worker.  In particular, mount and
# wildcard aliases are intentionally absent.
_REVIEWED_SYSCALLS = REQUIRED_SYSCALLS | frozenset({
    "access", "execve", "poll", "sched_getaffinity", "sigaltstack",
})
_BROAD_SYSCALL_NAMES = frozenset({"all", "*", "@default", "@known", "@system-service"})
_ARCH = {"x86_64": "SCMP_ARCH_X86_64", "amd64": "SCMP_ARCH_X86_64"}
_SUPPORTED_ARCHITECTURES = frozenset(_ARCH.values())
_SYSCALL_LINE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\([^)]*\)\s+=")


def _architecture() -> str:
    try:
        return _ARCH[platform.machine().lower()]
    except KeyError as exc:
        raise P4ProtocolError("P4 unsupported seccomp architecture") from exc


def _probe_syscalls(worker: Path) -> set[str]:
    strace = shutil.which("strace")
    if not strace:
        raise P4ProtocolError("P4 syscall measurement unavailable")
    try:
        result = subprocess.run(
            [strace, "-f", "-qq", "-e", "trace=all", str(worker)],
            input=b"", stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            close_fds=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise P4ProtocolError("P4 syscall measurement failed") from exc
    if result.returncode not in {0, 65}:
        raise P4ProtocolError("P4 native startup probe failed")
    observed: set[str] = set()
    for raw in result.stderr.decode("utf-8", "replace").splitlines():
        line = raw.strip()
        match = _SYSCALL_LINE.search(line)
        if match is None:
            continue
        name = match.group(1)
        if name.isidentifier():
            observed.add(name)
    if not observed:
        raise P4ProtocolError("P4 syscall measurement empty")
    return observed


def derive_seccomp_profile(worker: Path) -> dict[str, Any]:
    """Measure native startup and return an exact restrictive profile."""
    worker = Path(worker)
    if not worker.is_file() or worker.is_symlink():
        raise P4ProtocolError("P4 worker for seccomp measurement")
    observed = _probe_syscalls(worker)
    unknown = observed - _REVIEWED_SYSCALLS
    if unknown:
        raise P4ProtocolError("P4 unreviewed startup syscall")
    allowed = REQUIRED_SYSCALLS | observed
    if len(allowed) > 64:
        raise P4ProtocolError("P4 syscall surface exceeds bounded profile")
    return {"defaultAction": "SCMP_ACT_ERRNO", "archMap": [{"architecture": _architecture(), "subArchitectures": []}],
            "syscalls": [{"action": "SCMP_ACT_ALLOW", "names": sorted(allowed)}]}


def validate_seccomp_profile(path: Path, *, worker: Path | None = None) -> dict[str, Any]:
    """Validate one explicit, architecture-bound, default-deny policy."""
    try:
        raw = Path(path).read_bytes()
        profile = parse_canonical(raw)
    except Exception as exc:
        raise P4ProtocolError("P4 seccomp profile unavailable") from exc
    if set(profile) != {"defaultAction", "archMap", "syscalls"}:
        raise P4ProtocolError("P4 seccomp profile schema")
    architecture = profile["archMap"]
    if (profile["defaultAction"] != "SCMP_ACT_ERRNO"
            or not isinstance(architecture, list) or len(architecture) != 1
            or not isinstance(architecture[0], dict)
            or set(architecture[0]) != {"architecture", "subArchitectures"}
            or not isinstance(architecture[0]["architecture"], str)
            or architecture[0]["architecture"] not in _SUPPORTED_ARCHITECTURES
            or architecture[0]["architecture"] != _architecture()
            or architecture[0]["subArchitectures"] != []):
        raise P4ProtocolError("P4 restrictive architecture-bound policy required")
    entries = profile["syscalls"]
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        raise P4ProtocolError("P4 seccomp syscall policy")
    entry = entries[0]
    if set(entry) != {"action", "names"} or entry["action"] not in {"SCMP_ACT_ALLOW"}:
        raise P4ProtocolError("P4 seccomp syscall policy")
    names = entry["names"]
    if not isinstance(names, list) or not names:
        raise P4ProtocolError("P4 seccomp syscall policy")
    if any(not isinstance(name, str) or not name.isidentifier()
           or name in _BROAD_SYSCALL_NAMES or name not in _REVIEWED_SYSCALLS
           for name in names):
        raise P4ProtocolError("P4 seccomp syscall policy")
    if (names != sorted(names) or len(names) != len(set(names))
            or not REQUIRED_SYSCALLS.issubset(names) or len(names) > 64):
        raise P4ProtocolError("P4 seccomp syscall policy")
    expected = set(_REVIEWED_SYSCALLS)
    if worker is not None:
        try:
            native = Path(worker).read_bytes()[:4] == b"\x7fELF"
        except OSError as exc:
            raise P4ProtocolError("P4 worker for seccomp validation") from exc
        if native:
            observed = _probe_syscalls(Path(worker))
            unknown = observed - _REVIEWED_SYSCALLS
            if unknown:
                raise P4ProtocolError("P4 unreviewed startup syscall")
            # With a native worker, every non-floor syscall must be observed
            # by the bounded startup probe.  Reviewed-but-unobserved calls are
            # not permission to widen the runtime policy.
            expected = set(REQUIRED_SYSCALLS) | observed
    if set(names) != expected:
        raise P4ProtocolError("P4 seccomp profile is not the exact measured syscall set")
    return profile


def pin_seccomp_profile(path: Path, profile: dict[str, Any]) -> str:
    """Write canonical bytes and return the digest used by the lock."""
    target = Path(path)
    if target.is_symlink():
        raise P4ProtocolError("P4 seccomp profile symlink")
    target.write_bytes(canonical_bytes(profile))
    target.chmod(0o444)
    validate_seccomp_profile(target)
    return digest_file(target)
