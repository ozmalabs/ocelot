"""Evaluator-only staged public bundle and split-commitment verification."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from evaluation.p0a.canonical import canonical_bytes, sha256
from .protocol import P2ProtocolError

@dataclass(frozen=True)
class SplitCommitment:
    commitment: str
    family_ids: tuple[str, ...]
    matrix_size: int = 320
    def verify(self) -> None:
        if self.matrix_size != 320 or len(self.family_ids) != 4 or len(set(self.family_ids)) != 4: raise P2ProtocolError("invalid held-out split")
        if self.commitment != sha256(canonical_bytes({"families": list(self.family_ids), "matrix_size": self.matrix_size})): raise P2ProtocolError("split commitment mismatch")

def stage_public_bundle(root: Path, bundle: dict[str, Any]) -> tuple[Path, str]:
    """Create an evaluator-owned read-only public input; reject hidden authority."""
    from .protocol import _no_authority
    _no_authority(bundle)
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    target = root / "training-bundle.json"; payload = canonical_bytes(bundle)
    target.write_bytes(payload); target.chmod(0o400)
    return target, "sha256:" + hashlib.sha256(payload).hexdigest()
