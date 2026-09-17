"""Local content-addressed staging contract; explicitly not cross-UID custody."""
from __future__ import annotations

from pathlib import Path

from .canonical import ProtocolError, sha256


class LocalMountContract:
    local_approximation = True

    def __init__(self, root: Path, input_digest: str):
        self.root = Path(root)
        self.input_digest = input_digest
        self.inputs = self.root / "inputs" / "sha256"
        self.workspace = self.root / "workspace"
        self.inputs.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def stage(self, data: bytes) -> str:
        digest = sha256(data)
        target = self.inputs / digest.removeprefix("sha256:")
        target.write_bytes(data)
        target.chmod(0o400)
        return digest

    def resolve_input(self, reference: str) -> Path:
        if not reference.startswith("sha256:") or "/" in reference:
            raise ProtocolError("only content-addressed input references are accepted")
        path = self.inputs / reference.removeprefix("sha256:")
        if not path.is_file():
            raise ProtocolError("sealed input is absent")
        return path

    def reject_agent_path(self, _path: str) -> None:
        raise ProtocolError("agent-supplied host paths are denied")
