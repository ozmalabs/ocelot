"""Terminal local control state; no agent-originated reset API exists."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunControl:
    run_id: str
    state: str = "running"
    last_heartbeat_ms: int = 0

    def heartbeat(self, now_ms: int) -> None:
        if self.state == "running":
            self.last_heartbeat_ms = now_ms

    def kill(self, reason: str) -> str:
        if self.state == "running":
            self.state = "killed"
        return self.state

    def check_heartbeat(self, now_ms: int, deadline_ms: int) -> str:
        if self.state == "running" and now_ms - self.last_heartbeat_ms > deadline_ms:
            self.state = "killed"
        return self.state
