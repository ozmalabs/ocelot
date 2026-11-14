"""test_dev_memory_mcp_migrated — stdio transport and argument checks of the
dev-memory MCP server.

Dev tooling, not agent runtime. These tests drive `serve()` in-process over
`io.BytesIO` streams, so they exercise the real line framing, batch handling
and error replies without starting a subprocess.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.ocelot_dev_memory import DevMemory, build_index
from scripts.ocelot_dev_memory_mcp import DevMemoryServer, serve

PING = b'{"jsonrpc":"2.0","id":5,"method":"ping"}\n'
ADD_EDIT = {"file": "domains/foo.py",
            "ops": [{"op": "replace_body", "symbol": "add",
                     "text": "return a + b + 1"}]}


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _fixture(root: Path) -> None:
    _write(root / "domains" / "foo.py", '''"""Foo domain."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')
    _write(root / "seeds" / "demo.json", json.dumps({
        "id": "demo",
        "version": "1.2.0",
        "depends_on": [],
        "description": "demo seed",
        "nodes": [],
        "rules": [],
    }))
    _write(root / "README.md", "# Fixture repo\n\n`seeds/demo.json`.\n")


@pytest.fixture()
def server(tmp_path: Path) -> DevMemoryServer:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl", root=tmp_path)
    return DevMemoryServer(mem)


def _serve(monkeypatch: pytest.MonkeyPatch, server: DevMemoryServer,
           payload: bytes) -> list[Any]:
    """Run serve() over `payload`; return every JSON line written to stdout."""
    stdout = io.BytesIO()
    monkeypatch.setattr(sys, "stdin",
                        SimpleNamespace(buffer=io.BytesIO(payload)))
    monkeypatch.setattr(sys, "stdout", SimpleNamespace(buffer=stdout))
    assert serve(server) == 0
    return [json.loads(line) for line in
            stdout.getvalue().splitlines() if line.strip()]


def _call(name: str, arguments: Any, req_id: int = 1) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_blank_line_is_skipped_and_ping_answered(monkeypatch, server) -> None:
    out = _serve(monkeypatch, server, b"\n" + PING)
    assert out == [{"jsonrpc": "2.0", "id": 5, "result": {}}]


def test_batch_of_two_pings_gets_one_array(monkeypatch, server) -> None:
    batch = json.dumps([
        {"jsonrpc": "2.0", "id": 1, "method": "ping"},
        {"jsonrpc": "2.0", "id": 2, "method": "ping"},
    ]).encode() + b"\n"
    out = _serve(monkeypatch, server, batch)
    assert len(out) == 1 and isinstance(out[0], list)
    assert [r["id"] for r in out[0]] == [1, 2]
    assert all(r["result"] == {} for r in out[0])


def test_batch_of_only_notifications_writes_nothing(monkeypatch, server) -> None:
    batch = b'[{"jsonrpc":"2.0","method":"notifications/initialized"}]\n'
    assert _serve(monkeypatch, server, batch) == []


def test_empty_batch_is_invalid_request(monkeypatch, server) -> None:
    out = _serve(monkeypatch, server, b"[]\n" + PING)
    assert out[0]["id"] is None
    assert out[0]["error"]["code"] == -32600
    assert out[1]["id"] == 5 and out[1]["result"] == {}


def test_bare_string_is_invalid_then_server_continues(monkeypatch, server) -> None:
    out = _serve(monkeypatch, server, b'"hello"\n' + PING)
    assert out[0]["id"] is None and out[0]["error"]["code"] == -32600
    assert out[1]["id"] == 5 and out[1]["result"] == {}


def test_malformed_json_is_parse_error_then_server_continues(
        monkeypatch, server) -> None:
    out = _serve(monkeypatch, server, b"{not json\n" + PING)
    assert out[0]["id"] is None
    assert out[0]["error"]["code"] == -32700
    assert out[0]["error"]["message"].startswith("parse error: ")
    assert out[1]["id"] == 5 and out[1]["result"] == {}


def test_notification_error_is_never_answered(monkeypatch, server) -> None:
    bad = b'{"jsonrpc":"2.0","method":"tools/call","params":{"name":"nope"}}\n'
    out = _serve(monkeypatch, server, bad + PING)
    assert [r["id"] for r in out] == [5]


def test_params_not_an_object_is_invalid_params(server) -> None:
    resp = server.handle({"jsonrpc": "2.0", "id": 1,
                          "method": "tools/call", "params": "x"})
    assert resp["error"]["code"] == -32602


def test_resources_read_exception_is_internal_error(
        monkeypatch, server) -> None:
    def boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(server.mem, "brief", boom)
    read = (b'{"jsonrpc":"2.0","id":7,"method":"resources/read",'
            b'"params":{"uri":"ocelot://brief"}}\n')
    out = _serve(monkeypatch, server, read + PING)
    assert out[0]["id"] == 7
    assert out[0]["error"]["code"] == -32603
    assert out[0]["error"]["message"] == "internal error: RuntimeError: boom"
    assert out[1]["id"] == 5 and out[1]["result"] == {}


def test_unknown_tool_is_invalid_params(server) -> None:
    resp = server.handle(_call("dev_no_such_tool", {}))
    assert resp["error"]["code"] == -32602
    assert "dev_no_such_tool" in resp["error"]["message"]


def test_unknown_argument_key_is_invalid_params(server) -> None:
    resp = server.handle(_call("dev_seed", {"seed_id": "demo", "bogus": 1}))
    assert resp["error"]["code"] == -32602
    assert "bogus" in resp["error"]["message"]


def test_missing_required_argument_is_invalid_params(server) -> None:
    resp = server.handle(_call("dev_seed", {}))
    assert resp["error"]["code"] == -32602
    assert "seed_id" in resp["error"]["message"]


def test_string_booleans_and_integers_are_coerced(server) -> None:
    resp = server.handle(_call("dev_search", {"text": "add", "limit": "1"}))
    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert len(payload["results"]) == 1
    changed = server.handle(_call("dev_changed", {"all": "TRUE"}))
    assert changed["result"]["isError"] is False


def test_dev_edit_apply_false_string_is_preview(server) -> None:
    target = server.mem.raw_repo_root + "/domains/foo.py"
    before = _sha(Path(target))
    resp = server.handle(_call("dev_edit", {**ADD_EDIT, "apply": "false"}))
    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["applied"] is False
    assert _sha(Path(target)) == before


def test_dev_edit_apply_maybe_is_invalid_params(server) -> None:
    target = Path(server.mem.raw_repo_root) / "domains" / "foo.py"
    before = _sha(target)
    resp = server.handle(_call("dev_edit", {**ADD_EDIT, "apply": "maybe"}))
    assert resp["error"]["code"] == -32602
    assert "apply" in resp["error"]["message"]
    assert _sha(target) == before


def test_arguments_must_be_an_object(server) -> None:
    resp = server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": "dev_stats", "arguments": [1]}})
    assert resp["error"]["code"] == -32602


def test_initialize_negotiates_protocol_version(server) -> None:
    echoed = server.handle({"jsonrpc": "2.0", "id": 1,
                            "method": "initialize",
                            "params": {"protocolVersion": "2025-03-26"}})
    assert echoed["result"]["protocolVersion"] == "2025-03-26"
    newest = server.handle({"jsonrpc": "2.0", "id": 2,
                            "method": "initialize",
                            "params": {"protocolVersion": "1999-01-01"}})
    assert newest["result"]["protocolVersion"] == "2025-06-18"


def _framed_replies(raw: bytes) -> list[Any]:
    """Decode a stream that may mix newline and Content-Length replies."""
    out: list[Any] = []
    stream = io.BytesIO(raw)
    while True:
        line = stream.readline()
        if not line:
            break
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1].strip())
            assert stream.readline() in (b"\r\n", b"\n")
            out.append(json.loads(stream.read(length).decode("utf-8")))
        elif line.strip():
            out.append(json.loads(line))
    return out


def _serve_framed(monkeypatch, server, payload: bytes) -> list[Any]:
    stdout = io.BytesIO()
    monkeypatch.setattr(sys, "stdin",
                        SimpleNamespace(buffer=io.BytesIO(payload)))
    monkeypatch.setattr(sys, "stdout", SimpleNamespace(buffer=stdout))
    assert serve(server) == 0
    return _framed_replies(stdout.getvalue())


@pytest.mark.parametrize("length", [-1, 64 * 1024 * 1024 + 1])
def test_out_of_range_content_length_is_parse_error_then_continues(
        monkeypatch, server, length: int) -> None:
    body = json.dumps({"jsonrpc": "2.0", "id": 5, "method": "ping"}).encode()
    payload = (f"Content-Length: {length}\r\n\r\n".encode()
               + body + b"\n" + PING)
    replies = _serve_framed(monkeypatch, server, payload)
    assert replies[0]["error"]["code"] == -32700
    assert replies[0]["id"] is None
    assert replies[-1]["id"] == 5 and "result" in replies[-1]


def test_non_integer_content_length_is_parse_error(monkeypatch, server) -> None:
    replies = _serve_framed(monkeypatch, server,
                            b"Content-Length: nope\r\n\r\n")
    assert replies[0]["error"]["code"] == -32700


def test_dev_edit_diagnostics_defaults_to_off(server) -> None:
    listed = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = {t["name"]: t for t in listed["result"]["tools"]}
    prop = tools["dev_edit"]["inputSchema"]["properties"]["diagnostics"]
    assert prop["default"] is False
    assert "diagnostics=true" in prop["description"]
