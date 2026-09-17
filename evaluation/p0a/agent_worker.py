"""Fresh-exec P0 worker with only bounded native graph proposal stdio."""
from __future__ import annotations

import json
import os
import sys
import types
from dataclasses import dataclass
from pathlib import Path

from .agent_protocol import SCHEMA, decode_frame, validate_frame, write_frame
from .canonical import ProtocolError, sha256


@dataclass
class WorkerActionClient:
    run_id: str
    nonce: str
    _next: int = 0

    def submit_native_graph_proposal(self, proposal: dict) -> dict:
        """Submit a graph-native candidate; evaluator provenance remains authoritative."""
        if not isinstance(proposal, dict):
            raise TypeError("native graph proposal must be an object")
        self._next += 1
        correlation_id = str(self._next)
        write_frame(sys.stdout.buffer, {"schema": SCHEMA, "type": "submit_native_graph_proposal", "run_id": self.run_id,
                                        "session_nonce": self.nonce, "correlation_id": correlation_id,
                                        "proposal": proposal})
        reply = validate_frame(decode_frame(sys.stdin.buffer), run_id=self.run_id, nonce=self.nonce)
        if reply["type"] != "reply" or reply["correlation_id"] != correlation_id:
            raise ProtocolError("agent reply correlation")
        return reply


def _assert_fds() -> None:
    try:
        snapshot = os.listdir("/proc/self/fd")
        # os.listdir itself transiently opens the directory, so only retain
        # descriptors that still exist after that enumeration has completed.
        visible = {fd for fd in snapshot if os.path.exists(f"/proc/self/fd/{fd}")}
    except OSError:
        return
    if visible != {"0", "1", "2"}:
        raise ProtocolError("unexpected inherited descriptor")


def _staged_target(binding_text: str, *, agent_root: Path = Path("/agent"),
                   mount_root: Path = Path("/agent")):
    """Read, hash, and execute only the exact bytes selected by the evaluator."""
    try:
        binding = json.loads(binding_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProtocolError("staged entrypoint binding invalid") from exc
    if not isinstance(binding, dict) or set(binding) != {"artifact_digest", "artifact_path", "function", "module"}:
        raise ProtocolError("staged entrypoint binding invalid")
    module, function = binding["module"], binding["function"]
    artifact_path, expected_digest = binding["artifact_path"], binding["artifact_digest"]
    if (not all(isinstance(value, str) and value for value in binding.values())
            or not module.replace(".", "").isidentifier() or not function.isidentifier()
            or not expected_digest.startswith("sha256:") or len(expected_digest) != 71):
        raise ProtocolError("staged entrypoint binding invalid")
    agent_root = agent_root.resolve(strict=True)
    mount_root = mount_root.resolve(strict=True)
    requested = Path(artifact_path)
    if not requested.is_absolute() or requested.suffix != ".py":
        raise ProtocolError("staged entrypoint path invalid")
    try:
        relative = requested.relative_to(mount_root)
        artifact = (agent_root / relative).resolve(strict=True)
        artifact.relative_to(agent_root)
    except (OSError, ValueError) as exc:
        raise ProtocolError("staged entrypoint escapes agent mount") from exc
    try:
        expected_path = (agent_root.joinpath(*module.split(".")).with_suffix(".py")).resolve(strict=True)
    except OSError as exc:
        raise ProtocolError("staged entrypoint module path mismatch") from exc
    if artifact != expected_path or not artifact.is_file():
        raise ProtocolError("staged entrypoint module path mismatch")
    source = artifact.read_bytes()
    if sha256(source) != expected_digest:
        raise ProtocolError("staged entrypoint digest mismatch")
    # Compile the verified bytes directly: importlib must not reopen a path or
    # resolve an ambient module after the content check.
    loaded = types.ModuleType(module)
    loaded.__file__ = str(artifact)
    loaded.__package__ = module.rpartition(".")[0]
    sys.modules[module] = loaded
    exec(compile(source, str(artifact), "exec"), loaded.__dict__)
    if Path(str(loaded.__file__)).resolve(strict=True) != artifact:
        raise ProtocolError("staged entrypoint imported path mismatch")
    target = getattr(loaded, function, None)
    if not callable(target):
        raise ProtocolError("staged entrypoint target unavailable")
    return target


def main() -> int:
    hello = validate_frame(decode_frame(sys.stdin.buffer))
    if hello["type"] != "hello":
        raise ProtocolError("agent handshake")
    _assert_fds()
    binding = os.environ.get("P0_STAGED_ENTRYPOINT_BINDING")
    if not binding:
        raise ProtocolError("staged agent entrypoint unavailable")
    target = _staged_target(binding)
    target(WorkerActionClient(hello["run_id"], hello["session_nonce"]))
    write_frame(sys.stdout.buffer, {"schema": SCHEMA, "type": "terminal", "run_id": hello["run_id"],
                                    "session_nonce": hello["session_nonce"]})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"P0 agent worker failure: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(70)
