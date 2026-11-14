"""Shared read/hash/write transaction for the edit adapters.

DEV TOOLING, NOT AGENT RUNTIME. Nothing in `runners/dsl` or the live substrate
loads this module. The Python, JSON, Markdown, CST and IR edit adapters use it
to read a file once, bind every hash to the bytes on disk, keep the original
line endings and byte-order mark, and write atomically with a backup.

Contract:

  * `read_source` reads the exact bytes once. It strips a UTF-8 BOM, decodes
    strictly as UTF-8, and refuses other declared encodings. Line endings stay
    in the text; `detect_newline` names the file's dominant style.
  * `sha256` values are over the raw bytes on disk, BOM included.
  * `write_source` writes the bytes that were read to a backup, writes the
    edited text to a temp file in the same directory, re-reads the target just
    before replacing it, and refuses if it changed since the read.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_BOM = b"\xef\xbb\xbf"
_CODING_RE = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)")
_UTF8_NAMES = frozenset({"utf-8", "utf8", "utf-8-sig"})
_LONE_CR_RE = re.compile(r"\r(?!\n)")
_BACKUP_ATTEMPTS = 5


def detect_newline(text: str) -> str:
    """The dominant newline style: "\\r\\n", "\\n" or "\\r".

    Counts CRLF pairs, LFs not preceded by CR, and lone CRs. A tie, or a text
    with no newline, resolves to "\\n".
    """
    counts = {
        "\r\n": text.count("\r\n"),
        "\n": len(re.findall(r"(?<!\r)\n", text)),
        "\r": len(re.findall(r"\r(?!\n)", text)),
    }
    best = max(counts.values())
    if best == 0:
        return "\n"
    winners = [name for name, n in counts.items() if n == best]
    return winners[0] if len(winners) == 1 else "\n"


def normalize_newlines(text: str, newline: str) -> str:
    """Convert every CRLF, lone CR and lone LF in `text` to `newline`."""
    return re.sub(r"\r\n|\r|\n", lambda _m: newline, text)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class SourceFile:
    rel: str
    path: Path
    raw: bytes
    text: str
    bom: bool
    newline: str
    sha256: str
    mode: int


def _check_encoding_cookie(text: str, rel: str, error_cls: type[Exception]) -> None:
    for line in text.splitlines()[:2]:
        m = _CODING_RE.match(line)
        if not m:
            continue
        name = m.group(1).lower()
        if name not in _UTF8_NAMES:
            raise error_cls(
                f"{rel} declares encoding {m.group(1)!r}; only UTF-8 is supported")


def read_source(root: str | Path, file: str, *, suffixes: tuple[str, ...],
                max_bytes: int, error_cls: type[Exception]) -> SourceFile:
    """Read one repo file as bytes, decoded text and its metadata."""
    if not str(file or "").strip():
        raise error_cls("edit script needs file")
    root_path = Path(root).resolve()
    path = (root_path / str(file).strip()).resolve()
    try:
        rel = path.relative_to(root_path).as_posix()
    except ValueError as e:
        raise error_cls("file escapes the repo root") from e
    if path.suffix.lower() not in suffixes:
        raise error_cls(
            f"{rel}: suffix {path.suffix or '<none>'!r} is not supported; "
            f"allowed: {', '.join(suffixes)}")
    if not path.is_file():
        raise error_cls(f"no such file: {file}")
    if path.stat().st_size > max_bytes:
        raise error_cls(f"file exceeds {max_bytes} bytes")

    raw = path.read_bytes()
    bom = raw.startswith(_BOM)
    body = raw[len(_BOM):] if bom else raw
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise error_cls(
            f"{rel} is not valid UTF-8 ({exc.reason} at byte {exc.start}); "
            f"the edit layer only writes UTF-8") from exc
    _check_encoding_cookie(text, rel, error_cls)
    if _LONE_CR_RE.search(text):
        raise error_cls(
            f"{rel} contains lone CR characters; the edit layer supports LF and "
            f"CRLF line endings only")
    return SourceFile(
        rel=rel,
        path=path,
        raw=raw,
        text=text,
        bom=bom,
        newline=detect_newline(text),
        sha256=sha256_bytes(raw),
        mode=path.stat().st_mode,
    )


def check_base(src: SourceFile, expected: Any, error_cls: type[Exception]) -> None:
    """Refuse when the script names a base hash that is not the file's hash."""
    if expected and str(expected) != src.sha256:
        raise error_cls(
            f"stale base: file sha256 is {src.sha256}, script expected {expected}")


def encode_text(src: SourceFile, new_text: str) -> bytes:
    """The bytes that would be written for `new_text`, BOM restored if present."""
    data = new_text.encode("utf-8")
    return _BOM + data if src.bom else data


def _current_bytes(path: Path) -> bytes:
    """Re-read of the target just before replace. Separate so tests can wrap it."""
    return path.read_bytes()


def write_source(root: str | Path, src: SourceFile, new_text: str, *,
                 error_cls: type[Exception]) -> str:
    """Back up the bytes that were read, then replace the file atomically.

    Returns the backup path. Raises `error_cls` if the file changed on disk
    after it was read; the temp file is removed in that case.
    """
    backup_dir = Path(root) / "var" / "ocelot_dev_edits" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = None
    for _ in range(_BACKUP_ATTEMPTS):
        candidate = backup_dir / (
            f"{time.strftime('%Y%m%d-%H%M%S')}_"
            f"{time.time_ns() % 1_000_000_000:09d}_"
            f"{src.sha256[:12]}_{src.path.name}")
        try:
            with open(candidate, "xb") as fh:
                fh.write(src.raw)
        except FileExistsError:
            continue
        backup = candidate
        break
    if backup is None:
        raise error_cls("could not create a unique backup file")

    data = encode_text(src, new_text)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(src.path.parent), prefix=f".{src.path.name}.",
        suffix=".ocelot_tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, stat.S_IMODE(src.mode))
        if sha256_bytes(_current_bytes(src.path)) != src.sha256:
            raise error_cls(
                "stale base: file changed on disk after it was read; "
                "re-read and retry")
        os.replace(tmp, src.path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    try:
        dir_fd = os.open(str(src.path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass
    return str(backup)


__all__ = [
    "SourceFile",
    "check_base",
    "detect_newline",
    "encode_text",
    "normalize_newlines",
    "read_source",
    "sha256_bytes",
    "write_source",
]
