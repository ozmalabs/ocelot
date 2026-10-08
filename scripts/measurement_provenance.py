"""Small reusable primitives for reproducible substrate measurements.

This module hashes source trees and runtime data explicitly. Callers should
list the assets their measured path reads; the helpers never guess imports or
silently omit a missing path.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lock_files(paths: Iterable[str | Path], *, root: str | Path) -> dict[str, str]:
    """Return relative-path -> SHA-256 for an explicit file set."""
    base = Path(root).resolve()
    rows = {}
    for raw in paths:
        path = Path(raw).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            key = path.relative_to(base).as_posix()
        except ValueError as exc:
            raise ValueError(f"path is outside lock root: {path}") from exc
        rows[key] = sha256_file(path)
    return dict(sorted(rows.items()))


def lock_tree(
    path: str | Path,
    *,
    root: str | Path,
    suffixes: Iterable[str] = (".py",),
    exclude_dirs: Iterable[str] = ("__pycache__", ".git"),
) -> dict[str, str]:
    """Hash a source/runtime tree with deterministic filters and ordering."""
    tree = Path(path).resolve()
    if not tree.is_dir():
        raise NotADirectoryError(tree)
    excluded = set(exclude_dirs)
    allowed = set(suffixes)
    files = [p for p in tree.rglob("*") if p.is_file()
             and not (excluded & set(p.parts))
             and (not allowed or p.suffix in allowed)]
    return lock_files(files, root=root)
