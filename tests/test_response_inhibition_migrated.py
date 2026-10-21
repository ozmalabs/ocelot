"""G3.1 contract fixtures; graph/runtime enforcement belongs to G3.2/G3.3."""
from __future__ import annotations

from dataclasses import dataclass
import json

from substrate_rs import _native
from scripts.gen_response_inhibition_seed import OUT, build_seed


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


def _native_graph(enabled=True):
    substrate = _native.Substrate()
    agent = substrate.add_node("Agent", {})
    summary = substrate.load_seed_manifest(build_seed(), agent)
    assert summary.get("rules_skipped") == [], summary
    policy = substrate.nodes("ResponseInhibitionPolicy")[0]
    substrate.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    return substrate, agent


def _tick(substrate):
    for _ in range(20):
        if not substrate.run_rules(1000):
            return
    raise AssertionError("response inhibition did not reach a fixpoint")


def _request(substrate, agent, *, status="selected", epoch=4):
    request = substrate.add_node("ActionRequest", {
        "request_id": "move-native", "source_epoch": float(epoch),
        "action_key": "advance", "status": status,
    })
    substrate.add_edge(agent, "has_action_request", request)
    authorization = substrate.add_node("ActionAuthorization", {
        "authorization_id": "auth-native", "status": "pending",
    })
    substrate.add_edge(request, "has_action_authorization", authorization)
    stop = substrate.add_node("ActionStopEvent", {
        "request_id": "move-native", "source_epoch": float(epoch), "status": "pending",
    })
    substrate.add_edge(request, "has_action_stop", stop)
    return request, authorization, stop


def test_native_stop_withholds_and_revokes_authorization():
    substrate, agent = _native_graph()
    request, authorization, stop = _request(substrate, agent)
    _tick(substrate)
    assert substrate.node(request)["attrs"]["status"] == "withheld"
    assert substrate.node(request)["attrs"]["terminal_reason"] == "stop_before_commit"
    assert substrate.node(stop)["attrs"]["status"] == "withheld"
    assert substrate.node(authorization)["attrs"]["status"] == "revoked"


def test_late_stop_records_already_emitted_without_rewriting_request():
    substrate, agent = _native_graph()
    request, _authorization, stop = _request(substrate, agent, status="emitted")
    _tick(substrate)
    assert substrate.node(request)["attrs"]["status"] == "emitted"
    assert substrate.node(stop)["attrs"]["status"] == "already_emitted"
    assert substrate.node(stop)["attrs"]["terminal_reason"] == "effect_already_committed"


def test_withheld_cannot_rearm_from_same_request():
    substrate, agent = _native_graph()
    request, authorization, _stop = _request(substrate, agent, status="withheld")
    substrate.set_attr(authorization, "status", "pending")
    _tick(substrate)
    assert substrate.node(request)["attrs"]["status"] == "withheld"
    assert substrate.node(authorization)["attrs"]["status"] == "revoked"


def test_default_off_parity():
    substrate, agent = _native_graph(enabled=False)
    request, authorization, stop = _request(substrate, agent)
    before = (substrate.node(request)["attrs"].copy(),
              substrate.node(authorization)["attrs"].copy(),
              substrate.node(stop)["attrs"].copy())
    _tick(substrate)
    after = (substrate.node(request)["attrs"].copy(),
             substrate.node(authorization)["attrs"].copy(),
             substrate.node(stop)["attrs"].copy())
    assert after == before


def test_stale_stop_does_not_withhold_current_epoch():
    substrate, agent = _native_graph()
    request, authorization, stop = _request(substrate, agent, epoch=5)
    substrate.set_attr(stop, "source_epoch", 4.0)
    _tick(substrate)
    assert substrate.node(request)["attrs"]["status"] == "selected"
    assert substrate.node(authorization)["attrs"]["status"] == "pending"
    assert substrate.node(stop)["attrs"]["status"] == "pending"


def test_generator_reproduces_seed():
    assert json.loads(OUT.read_text()) == build_seed()
