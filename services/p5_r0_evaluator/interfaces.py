from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class StoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class Object:
    data: bytes
    generation: int


class ObjectStore(Protocol):
    def get(self, name: str) -> Object: ...
    def create(self, name: str, data: bytes) -> Object: ...
    def replace(self, name: str, data: bytes, generation: int) -> Object: ...


class Signer(Protocol):
    authority: dict[str, Any]
    def sign_digest(self, message_digest: bytes) -> str: ...


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None = None


class TokenVerifier(Protocol):
    def verify(self, authorization: str | None) -> Principal: ...


class TimingAttestor(Protocol):
    def record(self, *, run_id: str, task_id: str, event: str, payload_digest: str) -> dict[str, Any]: ...


class Engine(Protocol):
    def issue(self, *, arm: str, case: dict[str, Any], sequence: int,
              task_id: str, nonce: str, control: dict[str, Any] | None) -> dict[str, Any]: ...
    def evaluate(self, *, arm: str, case: dict[str, Any], task: dict[str, Any],
                 reply: dict[str, Any]) -> dict[str, Any]: ...
    def restore(self) -> str: ...


class EngineFactory(Protocol):
    def create(self, manifest: dict[str, Any], private_store: dict[str, Any]) -> Engine: ...
