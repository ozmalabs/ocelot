"""Evaluator-owned worker-scope supervision for P0 sandbox runs."""
from __future__ import annotations

from .control import RunControl
from .sandbox import WorkerScope


class CgroupSupervisor:
    """P0 supervisor that kills the evaluator-created run scope exactly once."""
    def __init__(self, run_id: str, scope: WorkerScope, *, control: RunControl | None = None):
        if control is not None and control.run_id != run_id: raise ValueError("control run_id mismatch")
        if scope.run_id != run_id: raise ValueError("scope run_id mismatch")
        self.control = control or RunControl(run_id)
        self.scope = scope

    def heartbeat(self, now_ms: int) -> None: self.control.heartbeat(now_ms)

    def stop(self, reason: str, **_ignored) -> str:
        was_running = self.control.state == "running"
        state = self.control.kill(reason)
        if was_running:
            self.scope.kill(reason)
        return state

    def expire_if_stale(self, now_ms: int, deadline_ms: int) -> str:
        was_running = self.control.state == "running"
        state = self.control.check_heartbeat(now_ms, deadline_ms)
        if was_running and state != "running":
            self.scope.kill("heartbeat_expired")
        return state


class LocalSupervisor:
    """Non-P0/dev-only logical state helper; it is not an isolation primitive."""
    def __init__(self, run_id: str, process_group: int | None = None, control: RunControl | None = None):
        if control is not None and control.run_id != run_id: raise ValueError("control run_id mismatch")
        self.control = control or RunControl(run_id)
        self.process_group = process_group

    def heartbeat(self, now_ms: int) -> None: self.control.heartbeat(now_ms)
    def stop(self, reason: str, **_ignored) -> str: return self.control.kill(reason)
    def expire_if_stale(self, now_ms: int, deadline_ms: int) -> str: return self.control.check_heartbeat(now_ms, deadline_ms)
