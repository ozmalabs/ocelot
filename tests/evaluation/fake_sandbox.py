"""Serializable staged-worker fixture; it never claims OS containment."""
from __future__ import annotations

import io
import threading
from collections import deque
from pathlib import Path
from typing import Iterable

from evaluation.p0a.agent_protocol import SCHEMA, decode_frame, validate_frame, write_frame
from evaluation.p0a.sandbox import SandboxProcess, SandboxSpec, StagedEntrypoint


class FakeWorkerScope:
    """Models an evaluator-precreated scope whose spawn covers descendants."""
    def __init__(self, run_id: str, controller: "FakeCgroupController") -> None:
        self.run_id, self.controller = run_id, controller
        self.spawned: list[list[str]] = []
        self.covered_descendants: set[int] = set()
        self.kills: list[str] = []
        self._process: _FakeProcess | None = None

    def spawn(self, argv: list[str], **_popen_kwargs) -> "_FakeProcess":
        if self._process is not None:
            raise AssertionError("scope spawned more than one worker")
        self.spawned.append(argv)
        self._process = self.controller._make_process()
        self.covered_descendants.add(4242)  # worker enters scope before it can run
        return self._process

    def attempt_descendant(self, pid: int) -> None:
        """Test seam: descendants inherit the precreated scope membership."""
        if self._process is None:
            raise AssertionError("descendant attempt before scoped worker spawn")
        self.covered_descendants.add(pid)

    def kill(self, reason: str) -> None:
        self.kills.append(reason)
        self.controller.kills.append(reason)
        if self._process is not None:
            self._process.close()


class FakeCgroupController:
    """Records evaluator-created scopes and their whole-scope kills."""
    def __init__(self) -> None:
        self.scopes: list[FakeWorkerScope] = []
        self.kills: list[str] = []
        self._process_factory = None

    def verify(self) -> bool:
        return True

    def create_scope(self, run_id: str) -> FakeWorkerScope:
        scope = FakeWorkerScope(run_id, self)
        self.scopes.append(scope)
        return scope

    def _make_process(self) -> "_FakeProcess":
        if self._process_factory is None:
            raise AssertionError("worker process factory not configured")
        return self._process_factory()


class _FrameReader:
    def __init__(self) -> None:
        self._parts: deque[bytes] = deque()
        self._buffer = bytearray()
        self._closed = False
        self._condition = threading.Condition()

    def feed(self, data: bytes) -> None:
        with self._condition:
            self._parts.append(data)
            self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def read(self, size: int = -1) -> bytes:
        with self._condition:
            while len(self._buffer) < size and self._parts:
                self._buffer.extend(self._parts.popleft())
            while size >= 0 and len(self._buffer) < size and not self._closed:
                self._condition.wait()
                while self._parts:
                    self._buffer.extend(self._parts.popleft())
            if size < 0:
                result = bytes(self._buffer)
                self._buffer.clear()
                return result
            result = bytes(self._buffer[:size])
            del self._buffer[:size]
            return result


class _FrameWriter:
    def __init__(self, receive) -> None:
        self._receive = receive

    def write(self, data: bytes) -> int:
        self._receive(data)
        return len(data)

    def flush(self) -> None:
        pass


class _FakeProcess:
    def __init__(self, proposals: Iterable[dict], heartbeats: int, terminal: bool) -> None:
        self.stdout = _FrameReader()
        self.stderr = io.BytesIO()
        self.stdin = _FrameWriter(self._receive)
        self._proposals = deque(proposals)
        self._heartbeats = heartbeats
        self._terminal = terminal
        self.replies: list[dict] = []
        self._returncode: int | None = None
        self._finished = threading.Event()

    def _send(self, frame: dict) -> None:
        data = io.BytesIO()
        write_frame(data, frame)
        self.stdout.feed(data.getvalue())

    def _emit_next(self, hello: dict) -> None:
        for _ in range(self._heartbeats):
            self._send({"schema": SCHEMA, "type": "heartbeat", "run_id": hello["run_id"],
                        "session_nonce": hello["session_nonce"]})
        if self._proposals:
            self._send({"schema": SCHEMA, "type": "submit_native_graph_proposal", "run_id": hello["run_id"],
                        "session_nonce": hello["session_nonce"], "correlation_id": str(len(self.replies) + 1),
                        "proposal": self._proposals.popleft()})
        elif self._terminal:
            self._send({"schema": SCHEMA, "type": "terminal", "run_id": hello["run_id"],
                        "session_nonce": hello["session_nonce"]})
            self._returncode = 0
            self._finished.set()

    def _receive(self, data: bytes) -> None:
        frame = decode_frame(io.BytesIO(data))
        if frame["type"] == "hello":
            self._hello = validate_frame(frame)
            self._emit_next(self._hello)
        elif frame["type"] == "reply":
            self.replies.append(validate_frame(frame, run_id=self._hello["run_id"], nonce=self._hello["session_nonce"]))
            self._emit_next(self._hello)
        else:
            raise AssertionError(f"unexpected host frame {frame['type']}")

    def poll(self) -> int | None:
        return self._returncode

    def wait(self, timeout: float | None = None) -> int:
        if not self._finished.wait(timeout):
            raise TimeoutError("fake worker did not finish")
        return self._returncode if self._returncode is not None else 0

    def close(self) -> None:
        if self._returncode is None:
            self._returncode = -9
        self._finished.set()
        self.stdout.close()


class FakeSandboxLauncher:
    """Test-only launcher for the protocol boundary, not an isolation substitute."""
    def __init__(self, spec: SandboxSpec, *, proposals: Iterable[dict] = (), heartbeats: int = 0,
                 terminal: bool = True) -> None:
        self.spec = spec
        self.controller = FakeCgroupController()
        self._proposals, self._heartbeats, self._terminal = tuple(proposals), heartbeats, terminal
        self.process: _FakeProcess | None = None
        self.scope: FakeWorkerScope | None = None

    def preflight(self, spec: SandboxSpec) -> None:
        assert spec == self.spec
        spec.validate()

    def start(self, spec: SandboxSpec, scope: FakeWorkerScope) -> SandboxProcess:
        self.preflight(spec)
        self.scope = scope
        self.controller._process_factory = lambda: _FakeProcess(self._proposals, self._heartbeats, self._terminal)
        self.process = scope.spawn(["fake-bwrap"])
        return SandboxProcess(self.process, scope)


def fake_sandbox(tmp_path: Path, *, proposals: Iterable[dict] = (), heartbeats: int = 0,
                 terminal: bool = True) -> FakeSandboxLauncher:
    staged = tmp_path / "fake-staged-agent"
    runtime, agent, inputs, work = (staged / name for name in ("runtime", "agent", "input", "work"))
    for path in (runtime, agent, inputs, work):
        path.mkdir(parents=True, exist_ok=True)
    (agent / "trusted_staged_agent.py").write_text("def run(client):\n    return None\n")
    policy = staged / "seccomp.bpf"
    policy.write_bytes(b"fake-test-policy")
    entrypoint = StagedEntrypoint.from_staged_agent(agent, "trusted_staged_agent:run")
    spec = SandboxSpec(runtime, agent, inputs, ("/runtime/python", "-I", "-m", "evaluation.p0a.agent_worker"),
                       work, policy, entrypoint)
    return FakeSandboxLauncher(spec, proposals=proposals, heartbeats=heartbeats, terminal=terminal)
