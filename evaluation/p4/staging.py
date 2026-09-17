"""No-symlink finite P4-R0 staging closure validation."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path

from evaluation.p0a.canonical import canonical_bytes
from .protocol import P4ProtocolError, is_digest

def _root(root: Path) -> Path:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise P4ProtocolError("staging root")
    return root.resolve(strict=True)

def _contained(root: Path, path: Path) -> Path:
    path = Path(path)
    if path.is_symlink() or not path.exists():
        raise P4ProtocolError("staging escape")
    resolved = path.resolve(strict=True)
    if root not in resolved.parents:
        raise P4ProtocolError("staging escape")
    return resolved

def digest_file(path: Path) -> str:
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise P4ProtocolError("staged regular file required")
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        h = hashlib.sha256()
        while block := os.read(fd, 65536):
            h.update(block)
    finally:
        os.close(fd)
    return "sha256:" + h.hexdigest()

def digest_tree(path: Path) -> str:
    root = Path(path)
    if root.is_symlink() or not root.is_dir():
        raise P4ProtocolError("staged directory required")
    entries: list[dict[str, str]] = []
    for entry in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
            raise P4ProtocolError("staged tree entry")
        relative = entry.relative_to(root).as_posix()
        if entry.is_dir():
            entries.append({"path": relative, "kind": "directory"})
        else:
            entries.append({"path": relative, "kind": "file", "digest": digest_file(entry)})
    return "sha256:" + hashlib.sha256(canonical_bytes({"schema": "P4R0StagedTreeV1", "files": entries})).hexdigest()

def closure_digests(root: Path, artifacts: dict[str, Path]) -> dict[str, str]:
    resolved_root = _root(root)
    out = {}
    for name, path in artifacts.items():
        resolved = _contained(resolved_root, path)
        out[name] = digest_tree(resolved) if resolved.is_dir() else digest_file(resolved)
    return out

def validate_closure(root: Path, artifacts: dict[str, Path], expected: dict[str, str]) -> dict[str, str]:
    if set(artifacts) != set(expected) or not all(is_digest(value) for value in expected.values()):
        raise P4ProtocolError("staging closure")
    out = closure_digests(root, artifacts)
    if out != expected:
        raise P4ProtocolError("staging digest")
    return out
