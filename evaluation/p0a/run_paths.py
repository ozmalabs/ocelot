"""Evaluator-owned, run-scoped paths for P0 terminal and receipt evidence."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from .canonical import ProtocolError

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _run_id(value: str) -> str:
    if not isinstance(value, str):
        raise ProtocolError("invalid run id")
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError) as exc:
        raise ProtocolError("invalid run id") from exc


def _digest(value: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ProtocolError("invalid manifest digest")
    return value


@dataclass(frozen=True)
class RunPaths:
    """Paths constructed solely from a verified run binding, never agent input."""
    control_root: Path
    run_id: str
    verified_manifest_hash: str

    @classmethod
    def for_verified_run(cls, control_root: Path, *, run_id: str, verified_manifest_hash: str) -> "RunPaths":
        instance = cls(Path(control_root), _run_id(run_id), _digest(verified_manifest_hash))
        instance.terminal_root.mkdir(parents=True, exist_ok=True)
        instance.receipts_root.mkdir(parents=True, exist_ok=True)
        return instance

    @property
    def root(self) -> Path:
        return self.control_root / "runs" / self.run_id / self.verified_manifest_hash

    @property
    def receipts_root(self) -> Path:
        return self.root / "receipts"

    @property
    def terminal_root(self) -> Path:
        return self.root / "terminal"

    @property
    def runtime_failure_path(self) -> Path:
        return self.terminal_root / "runtime-failure.json"

    @property
    def launch_failure_path(self) -> Path:
        return self.terminal_root / "launch-failure.json"


@dataclass(frozen=True)
class LaunchAttemptPaths:
    control_root: Path
    launch_attempt_id: str

    @classmethod
    def create(cls, control_root: Path, *, launch_attempt_id: str | None = None) -> "LaunchAttemptPaths":
        value = launch_attempt_id or str(uuid.uuid4())
        try:
            value = str(uuid.UUID(value))
        except (ValueError, AttributeError) as exc:
            raise ProtocolError("invalid launch attempt id") from exc
        instance = cls(Path(control_root), value)
        instance.root.mkdir(parents=True, exist_ok=True)
        return instance

    @property
    def root(self) -> Path:
        return self.control_root / "launch-attempts" / self.launch_attempt_id

    @property
    def launch_failure_path(self) -> Path:
        return self.root / "launch-failure.json"
