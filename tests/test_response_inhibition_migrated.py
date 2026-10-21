"""G3.1 contract fixtures; graph/runtime enforcement belongs to G3.2/G3.3."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Request:
    request_id: str
    epoch: int
    status: str = "proposed"
    authorization_id: str | None = None
    sink_receipt_id: str | None = None
    terminal_reason: str | None = None


def _commit(request: Request, events: list[tuple[str, str, int]]) -> str:
    """Small contract oracle: resolve same-epoch stop before consuming go."""
    if request.status in {"withheld", "emitted"}:
        return request.status
    matching = [(kind, identity) for kind, identity, epoch in events
                if identity == request.request_id and epoch == request.epoch]
    if any(kind == "stop" for kind, _ in matching):
        request.status = "withheld"
        request.authorization_id = None
        request.terminal_reason = "stop_before_commit"
        return request.status
    if not any(kind == "go" for kind, _ in matching):
        request.status = "withheld"
        request.terminal_reason = "missing_authorization"
        return request.status
    request.authorization_id = f"auth:{request.request_id}:{request.epoch}"
    request.sink_receipt_id = f"sink:{request.request_id}:{request.epoch}"
    request.status = "emitted"
    return request.status


def test_stop_before_emit_withholds():
    request = Request("move-1", 4, status="selected")
    assert _commit(request, [("stop", "move-1", 4), ("go", "move-1", 4)]) == "withheld"
    assert request.authorization_id is None
    assert request.sink_receipt_id is None
    assert request.terminal_reason == "stop_before_commit"


def test_go_executes_once():
    request = Request("move-2", 4, status="selected")
    events = [("go", "move-2", 4)]
    assert _commit(request, events) == "emitted"
    receipt = request.sink_receipt_id
    assert _commit(request, events) == "emitted"
    assert request.sink_receipt_id == receipt
    assert request.authorization_id == "auth:move-2:4"


def test_late_stop_reports_already_emitted():
    request = Request("move-3", 4, status="selected")
    assert _commit(request, [("go", "move-3", 4)]) == "emitted"
    receipt = request.sink_receipt_id
    result = "already_emitted" if request.status == "emitted" else _commit(
        request, [("stop", "move-3", 4)])
    assert result == "already_emitted"
    assert request.sink_receipt_id == receipt


def test_same_epoch_stop_wins():
    outcomes = []
    for events in (
        [("stop", "move-4", 8), ("go", "move-4", 8)],
        [("go", "move-4", 8), ("stop", "move-4", 8)],
    ):
        request = Request("move-4", 8, status="selected")
        outcomes.append(_commit(request, events))
        assert request.sink_receipt_id is None
    assert outcomes == ["withheld", "withheld"]
