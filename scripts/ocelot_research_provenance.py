"""Read-only adapters for empirical research provenance records.

These helpers re-check current repository facts and report what they cannot
establish. They never execute a recorded experiment command or edit a prereg.
"""
from __future__ import annotations

import re
import hashlib
import subprocess
from pathlib import Path
from typing import Any, Mapping


_SEED_LINE = re.compile(r"SEED CLAIM\s+(\d+)\s*[-–]\s*(\d+)\s*:\s*(CLEAN|REFUSED)", re.I)


def verify_engine_provenance(recorded: Mapping[str, Any] | None = None, *, tree: str | None = None) -> dict[str, Any]:
    """Compare a recorded engine stamp with the engine visible in this process.

    ``current`` means the current source-content check passes. ``matches`` is
    separately reported because a new process may load a different artifact.
    """
    from domains import engine_provenance as engine

    try:
        current = engine.engine_provenance(tree or engine.THIS_TREE)
    except (OSError, RuntimeError, ImportError) as exc:
        return {"status": "unavailable", "verified": False, "reason": str(exc)}
    source_ok = current.get("source_match") in {"own", "shared"} and not current.get("stale_rust")
    matches = None
    if recorded is not None and not isinstance(recorded, Mapping):
        return {"status": "invalid_record", "verified": False, "reason": "engine stamp must be an object"}
    if recorded is not None:
        recorded_hash = recorded.get("sha256")
        current_hash = current.get("sha256")
        matches = (isinstance(recorded_hash, str) and bool(recorded_hash)
                   and isinstance(current_hash, str) and bool(current_hash)
                   and recorded_hash == current_hash
                   and recorded.get("source_match") == current.get("source_match"))
    return {
        "status": "current" if source_ok else "unverified",
        "verified": source_ok,
        "matches_recorded": matches,
        "current": current,
        "reason": None if source_ok else "engine source match is not own/shared or Rust sources are stale",
        "limitation": "Checks the engine loaded in this process; it cannot prove which engine produced a past run.",
    }


def verify_seed_claim(text: str, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Re-scan a prereg's seed claim against the current tree, read-only.

    A clean result is only ``no collision detected`` under seed_claim's
    documented scan scope; it is not evidence that the range was historically
    unused or that unresolved seed sinks do not collide.
    """
    hits = list(_SEED_LINE.finditer(text))
    if not hits:
        return {"status": "missing", "verified": False, "reason": "no SEED CLAIM verdict found"}
    if len(hits) != 1:
        return {"status": "ambiguous", "verified": False, "reason": "expected exactly one seed claim verdict"}
    match = hits[0]
    lo, hi, verdict = int(match.group(1)), int(match.group(2)), match.group(3).upper()
    if lo > hi:
        return {"status": "invalid", "verified": False, "reason": "seed range is reversed"}
    try:
        from scripts import seed_claim
        if repo_root is not None and Path(repo_root).resolve() != Path(seed_claim.ROOT).resolve():
            return {"status": "unsupported_root", "verified": False,
                    "reason": "seed_claim currently scans its configured Ocelot repository root"}
        report = seed_claim.claim_report(lo, hi, refresh=True)
    except (OSError, ValueError, RuntimeError) as exc:
        return {"status": "unavailable", "verified": False, "reason": str(exc)}
    reproduced = verdict == "CLEAN" and bool(report.get("clean"))
    return {
        "status": "current_match" if reproduced else "stale_or_conflict",
        "verified": reproduced,
        "range": [lo, hi], "recorded_verdict": verdict,
        "current_verdict": "CLEAN" if report.get("clean") else "REFUSED",
        "report": report,
        "limitation": "Rechecks current files and ledger only; cannot establish historical availability or exclude unresolved seed sinks.",
    }


def verify_prereg(path: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Inspect a prereg file and re-check its embedded seed claim, if present."""
    p = Path(path)
    try:
        resolved = p.resolve(strict=True)
        if repo_root is not None and not resolved.is_relative_to(Path(repo_root).resolve(strict=True)):
            return {"status": "unsafe_path", "verified": False, "reason": "prereg path escapes repository root"}
        if not resolved.is_file():
            return {"status": "unavailable", "verified": False, "reason": "prereg is not a regular file"}
        content = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {"status": "unavailable", "verified": False, "reason": str(exc)}
    seed = verify_seed_claim(content, repo_root=repo_root)
    return {"status": "inspected", "verified": seed.get("verified", False),
            "path": str(resolved), "seed_claim": seed,
            "limitation": "File presence and a current seed scan do not prove the prereg was committed before a run; verify its immutable revision and run receipt separately."}


def verify_prereg_git(repo_path: str | Path, commit_oid: str, relative_path: str) -> dict[str, Any]:
    """Compare a working prereg with an immutable Git commit blob.

    The commit must be identified by a full SHA-1/SHA-256 object ID. Git is
    invoked with an argument array and fixed subcommands; no shell, hooks,
    user supplied options, or repository writes are involved. The committer
    timestamp is metadata only and is not proof that preregistration preceded
    an experiment.
    """
    if not isinstance(commit_oid, str) or not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit_oid):
        return {"status": "invalid_commit", "verified": False,
                "reason": "commit_oid must be a full 40- or 64-character hexadecimal object ID"}
    if not isinstance(relative_path, str) or not relative_path or "\\" in relative_path or ":" in relative_path:
        return {"status": "invalid_path", "verified": False,
                "reason": "path must be a nonempty repository-relative POSIX path"}
    rel = Path(relative_path)
    if rel.is_absolute() or any(part in {"", ".", ".."} for part in relative_path.split("/")) or relative_path.startswith("-"):
        return {"status": "invalid_path", "verified": False,
                "reason": "path must not be absolute, traverse directories, or resemble an option"}
    try:
        root = Path(repo_path).resolve(strict=True)
        if not root.is_dir():
            raise OSError("repository path is not a directory")
        working = (root / rel).resolve(strict=True)
        if not working.is_relative_to(root) or not working.is_file():
            return {"status": "unsafe_path", "verified": False,
                    "reason": "working prereg must be a regular file inside the repository"}
        object_type = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-t", commit_oid.lower()],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        if object_type != "commit":
            return {"status": "invalid_commit", "verified": False,
                    "reason": "object ID does not identify a commit object"}
        blob = subprocess.run(
            ["git", "-C", str(root), "cat-file", "blob", f"{commit_oid.lower()}:{relative_path}"],
            check=True, capture_output=True, timeout=10,
        ).stdout
        timestamp = subprocess.run(
            ["git", "-C", str(root), "show", "-s", "--format=%cI", commit_oid.lower()],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        current = working.read_bytes()
    except subprocess.CalledProcessError as exc:
        return {"status": "unavailable", "verified": False,
                "reason": "commit or path is not available as a Git blob",
                "git_error": exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "").strip()}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "unavailable", "verified": False, "reason": str(exc)}
    committed_hash = hashlib.sha256(blob).hexdigest()
    working_hash = hashlib.sha256(current).hexdigest()
    same = committed_hash == working_hash
    return {
        "status": "current_matches_commit" if same else "working_copy_differs",
        "verified": True,
        "commit_oid": commit_oid.lower(), "path": relative_path,
        "committed_sha256": committed_hash, "working_sha256": working_hash,
        "working_matches_commit": same,
        "committer_timestamp": timestamp,
        "timestamp_is_assertion": True,
        "limitation": "The commit identifies immutable content; its committer timestamp is metadata, not proof that registration preceded the run.",
    }
