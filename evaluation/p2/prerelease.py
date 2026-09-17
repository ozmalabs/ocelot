"""Pre-release-only P2 test scaffolding; never emits release evidence."""
from __future__ import annotations
from pathlib import Path
from .lock import validate_lock
from .protocol import P2ProtocolError

def require_release_ready(lock: dict, worker: Path, evaluator: Path) -> None:
    """Shared guard for release entrypoints after real tests have passed."""
    validate_lock(lock)
    for binary in (worker,evaluator):
        if Path(binary).is_symlink() or not Path(binary).is_file():
            raise P2ProtocolError("release native binary unavailable")

def pre_release_fixture_only() -> bool:
    """Explicit marker for test harnesses: no score, receipt, or claim is valid."""
    return True
