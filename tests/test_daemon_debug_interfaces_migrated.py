"""Non-cognitive daemon status and read-only graph debugging surfaces."""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import jabberwock_daemon as daemon  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _agent() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest_for("instruction_understanding"), agent.agent)
    return agent


def test_runtime_status_never_reads_graph_or_invokes_cognition():
    state = daemon.DaemonState(_agent(), "test")

    class _NoAccess:
        def __getattribute__(self, name):
            raise AssertionError(f"runtime status touched adapter.{name}")

    state.adapter = _NoAccess()
    status = daemon._runtime_status_dict(state)

    assert status["ok"] is True
    assert status["requires_cognition"] is False
    assert status["ticks"] == 0
    assert status["node_count_snapshot"] > 0


def test_graph_helpers_are_paged_filtered_json_safe_and_read_only():
    agent = _agent()
    blob = agent.s.add_node("DebugBlob", {"payload": b"\x00\xff"})
    before = agent.inner.graph_to_dict()

    summary = daemon.debug_graph_summary(agent)
    nodes = daemon.debug_graph_nodes(agent, {"type": ["DebugBlob"], "limit": ["1"]})
    detail = daemon.debug_graph_node(agent, str(blob.value))
    rules = daemon.debug_graph_rules(agent, {"name": ["iu_confirm"], "limit": ["10"]})

    assert summary["read_only"] and summary["node_types"]["DebugBlob"] == 1
    payload = nodes["nodes"][0]["attrs"]["payload"]
    assert nodes["total"] == 1 and payload["kind"] == "bytes" and payload["payload"] == "00ff"
    assert detail is not None and detail["node"]["id"] == blob.value
    assert rules["total"] == 1
    json.dumps({"summary": summary, "nodes": nodes, "detail": detail, "rules": rules})
    assert agent.inner.graph_to_dict() == before


def test_http_runtime_and_graph_debug_routes_do_not_tick_agent():
    agent = _agent()
    target = agent.s.add_node("DebugTarget", {"name": "visible"})
    pending_turn = agent.receive_utterance("pending turn")
    state = daemon.DaemonState(agent, "test")
    server = daemon.JbwHTTPServer(("127.0.0.1", 0), daemon.Handler, state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    response_headers = {}

    def get(path):
        with urllib.request.urlopen(base + path, timeout=5) as response:
            response_headers[path] = dict(response.headers.items())
            return json.load(response)

    try:
        # The request is served by another HTTP thread while this test owns the
        # cognition lock: acquiring AGENT_LOCK in the route would time out.
        with daemon.AGENT_LOCK:
            status = get("/api/runtime/status")
        summary = get("/api/debug/graph")
        nodes = get("/api/debug/graph/nodes?type=DebugTarget&limit=1")
        detail = get(f"/api/debug/graph/nodes/{target.value}")
        edges = get(f"/api/debug/graph/edges?source={target.value}&limit=5")
        rules = get("/api/debug/graph/rules?name=iu_confirm&limit=5")
        pending = get(f"/api/chat/turns/{pending_turn.value}")
        reply = agent.s.add_node("Message", {"from": "agent", "text": "settled"})
        agent.inner.add_edge_unchecked(reply, "responds_to", pending_turn)
        completed = get(f"/api/chat/turns/{pending_turn.value}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert status["requires_cognition"] is False and status["ticks"] == 0
    assert response_headers["/api/runtime/status"]["Access-Control-Allow-Origin"] == "*"
    assert "Access-Control-Allow-Origin" not in response_headers["/api/debug/graph"]
    assert summary["read_only"] is True
    assert nodes["total"] == 1 and nodes["nodes"][0]["id"] == target.value
    assert detail["node"]["attrs"]["name"] == "visible"
    assert edges["read_only"] is True
    assert rules["total"] == 1
    assert pending == {"ok": True, "turn_id": pending_turn.value,
                       "status": "pending", "transport_pending": False}
    assert completed == {"ok": True, "turn_id": pending_turn.value,
                         "status": "completed", "reply": "settled",
                         "transport_pending": False}
    assert state.ticks == 0


def test_web_interface_renders_the_cognition_free_runtime_status():
    html = (ROOT / "web" / "index.html").read_text()
    app = (ROOT / "web" / "app.js").read_text()

    assert 'id="runtime-status-bar"' in html
    for field in ("runtime-state", "runtime-tick", "runtime-work", "runtime-nodes",
                  "runtime-actions", "runtime-last-action", "runtime-error"):
        assert f'id="{field}"' in html
    assert 'fetch("/api/runtime/status"' in app
    assert "function updateRuntimeStatus" in app
    assert "RUNTIME_STATUS_POLL_MS" in app
