"""test_lsp_migrated — protocol framing, queries, diagnostics cache, impact.

The default suite uses a tiny fake stdio language server (a subprocess with
Content-Length framing). It proves our framing, request/notification routing
and result normalization; it does not prove compatibility with pyright,
rust-analyzer or clangd. Those are optional live smoke tests, gated behind
`OCELOT_LIVE_LSP=1`, and skip when the server is absent, cold or unhappy.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from scripts.ocelot_lsp import (
    LANGUAGE_SERVERS,
    LSPClient,
    ROOT,
    available_servers,
    detect_language,
    server_candidates,
)


FAKE_SERVER = r'''"""A minimal LSP stdio server used by tests/test_lsp_migrated.py."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

LOG = os.environ.get("FAKE_LSP_LOG")
ROOT = None
INITIALIZED = False
DOCS = {}
SEEN_REFS = set()


def log(message):
    if not LOG:
        return
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(message, ensure_ascii=False) + "\n")


def read_message():
    headers = {}
    content_header = None
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, sep, value = line.decode("ascii").partition(":")
        if sep:
            headers[name.strip().lower()] = value.strip()
            if name.strip().lower() == "content-length":
                content_header = line.decode("ascii").strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    if len(body) != length:
        return None
    log({"__frame__": {"header": content_header, "length": length,
                       "body_bytes": len(body)}})
    return json.loads(body.decode("utf-8"))


def send(message):
    body = json.dumps(message, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(
        f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def result(rid, value):
    send({"jsonrpc": "2.0", "id": rid, "result": value})


def error(rid, code, message):
    send({"jsonrpc": "2.0", "id": rid,
          "error": {"code": code, "message": message}})


def notify(method, params):
    send({"jsonrpc": "2.0", "method": method, "params": params})


def uri_to_path(value):
    return Path(unquote(urlparse(value).path))


def path_uri(path):
    return Path(path).resolve().as_uri()


def rng(sl, sc, el, ec):
    return {"start": {"line": sl, "character": sc},
            "end": {"line": el, "character": ec}}


def root_path():
    return uri_to_path(ROOT)


def publish(doc):
    path = uri_to_path(doc.get("uri", ""))
    text = doc.get("text", "")
    diagnostics = []
    if path.name == "b.py":
        if "BROKEN" in text:
            diagnostics = [{"range": rng(0, 0, 0, 6), "severity": 1,
                            "source": "fake", "message": "broken token"}]
        else:
            diagnostics = [{"range": rng(0, 0, 0, 9), "severity": 2,
                            "source": "fake", "code": "F401",
                            "message": "imported but unused"}]
    notify("textDocument/publishDiagnostics",
           {"uri": doc.get("uri"), "version": doc.get("version"),
            "diagnostics": diagnostics})


def call_item(name, path, sl, sc, el, ec, data=None):
    item = {"name": name, "kind": 12, "uri": path_uri(path),
            "range": rng(sl, sc, el, ec),
            "selectionRange": rng(sl, sc, sl, sc + len(name))}
    if data is not None:
        item["data"] = data
    return item


def main():
    global ROOT, INITIALIZED
    while True:
        message = read_message()
        if message is None:
            return
        log(message)
        method = message.get("method")
        rid = message.get("id")
        params = message.get("params") or {}
        if method is None:
            continue
        if method == "initialize":
            ROOT = params.get("rootUri")
            result(rid, {
                "capabilities": {
                    "definitionProvider": True,
                    "referencesProvider": True,
                    "documentSymbolProvider": True,
                    "hoverProvider": True,
                    "callHierarchyProvider": True,
                    "renameProvider": True,
                },
                "serverInfo": {"name": "fake-lsp", "version": "1.0"},
            })
        elif method == "initialized":
            INITIALIZED = True
        elif method == "exit":
            return
        elif not INITIALIZED:
            error(rid, -32002, "server not initialized")
        elif method == "shutdown":
            result(rid, None)
        elif method == "textDocument/didOpen":
            doc = dict(params.get("textDocument") or {})
            DOCS[doc.get("uri")] = doc
            publish(doc)
        elif method == "textDocument/didChange":
            uri = (params.get("textDocument") or {}).get("uri")
            doc = DOCS.setdefault(uri, {"uri": uri})
            doc["version"] = (params.get("textDocument") or {}).get("version")
            changes = params.get("contentChanges") or [{}]
            doc["text"] = changes[0].get("text", "")
            publish(doc)
        elif method == "textDocument/didClose":
            uri = (params.get("textDocument") or {}).get("uri")
            DOCS.pop(uri, None)
            notify("textDocument/publishDiagnostics",
                   {"uri": uri, "diagnostics": []})
        elif method == "textDocument/definition":
            result(rid, {"uri": path_uri(root_path() / "a.py"),
                         "range": rng(2, 4, 2, 9)})
        elif method == "textDocument/references":
            target_uri = (params.get("textDocument") or {}).get("uri", "")
            if target_uri not in SEEN_REFS:
                # Simulate a cold server: the first reference query misses,
                # the client must retry an empty result before believing it.
                SEEN_REFS.add(target_uri)
                result(rid, [])
            else:
                result(rid, [
                    {"uri": path_uri(root_path() / "a.py"),
                     "range": rng(2, 4, 2, 9)},
                    {"uri": path_uri(root_path() / "b.py"),
                     "range": rng(3, 4, 3, 9)},
                    {"uri": path_uri(root_path() / "b.py"),
                     "range": rng(5, 8, 5, 13)},
                ])
        elif method == "textDocument/documentSymbol":
            result(rid, [
                {"name": "alpha", "kind": 12, "range": rng(0, 0, 1, 10),
                 "selectionRange": rng(0, 4, 0, 9), "children": []},
                {"name": "Widget", "kind": 5, "range": rng(3, 0, 8, 0),
                 "selectionRange": rng(3, 6, 3, 12),
                 "children": [
                     {"name": "render", "kind": 6,
                      "range": rng(4, 4, 7, 0),
                      "selectionRange": rng(4, 8, 4, 14),
                      "children": []},
                 ]},
            ])
        elif method == "textDocument/hover":
            result(rid, {
                "contents": {"kind": "markdown",
                             "value": "```python\ndef alpha(x): ...\n```"},
                "range": rng(0, 4, 0, 9),
            })
        elif method == "textDocument/prepareCallHierarchy":
            result(rid, [call_item("alpha", root_path() / "a.py", 0, 0, 1, 10,
                                   {"fake": "alpha"})])
        elif method == "callHierarchy/incomingCalls":
            item = params.get("item") or {}
            if item.get("data") != {"fake": "alpha"}:
                error(rid, -32602, "missing call item data")
            else:
                result(rid, [{
                    "from": call_item("caller", root_path() / "b.py",
                                      2, 0, 4, 0),
                    "fromRanges": [rng(3, 12, 3, 17)],
                }])
        elif method == "callHierarchy/outgoingCalls":
            item = params.get("item") or {}
            if item.get("data") != {"fake": "alpha"}:
                error(rid, -32602, "missing call item data")
            else:
                result(rid, [{
                    "to": call_item("callee", root_path() / "c.py",
                                    0, 0, 1, 10),
                    "fromRanges": [rng(0, 20, 0, 26)],
                }])
        elif method == "textDocument/rename":
            result(rid, {"changes": {
                path_uri(root_path() / "a.py"): [
                    {"range": rng(0, 4, 0, 9), "newText": "omega"},
                    {"range": rng(2, 4, 2, 9), "newText": "omega"},
                ],
                path_uri(root_path() / "b.py"): [
                    {"range": rng(3, 4, 3, 9), "newText": "omega"},
                ],
            }})
        elif method == "fake/hang":
            pass  # deliberately never answers; the client must time out
        else:
            error(rid, -32601, f"method not found: {method}")


if __name__ == "__main__":
    main()
'''


def _write_fixture(root: Path) -> None:
    (root / "a.py").write_text(
        "def alpha(x):\n"
        "    return x + 1\n"
        "\n"
        "print(alpha(1))\n",
        encoding="utf-8")
    (root / "b.py").write_text(
        "from a import alpha\n"
        "\n"
        "\n"
        "def use():\n"
        "    return alpha(2)\n",
        encoding="utf-8")
    (root / "c.py").write_text(
        "def callee():\n"
        "    return 1\n",
        encoding="utf-8")
    (root / "u.py").write_text(
        "# café α\n"
        "value = 1\n",
        encoding="utf-8")


@pytest.fixture()
def fake_lsp(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    _write_fixture(root)
    server = tmp_path / "fake_lsp_server.py"
    server.write_text(FAKE_SERVER, encoding="utf-8")
    log = tmp_path / "fake_lsp.log"
    client = LSPClient(
        root, "python", command=[sys.executable, str(server)],
        timeout=5.0, initialize_timeout=5.0, diagnostics_timeout=2.0,
        env={"FAKE_LSP_LOG": str(log)})
    try:
        yield {"root": root, "client": client, "log": log, "server": server}
    finally:
        client.close()


def _messages(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(line) for line in
            log.read_text(encoding="utf-8").splitlines() if line.strip()]


def _client_messages(log: Path) -> list[dict]:
    return [m for m in _messages(log) if m.get("method")]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_registry_and_language_detection() -> None:
    assert LANGUAGE_SERVERS["python"][0].name == "pyright-langserver"
    assert LANGUAGE_SERVERS["python"][0].args == ("--stdio",)
    assert LANGUAGE_SERVERS["python"][1].name == "pylsp"
    assert LANGUAGE_SERVERS["rust"][0].name == "rust-analyzer"
    assert LANGUAGE_SERVERS["c"][0].name == "clangd"
    assert LANGUAGE_SERVERS["cpp"][0].name == "clangd"
    assert LANGUAGE_SERVERS["typescript"][0].name == "typescript-language-server"

    assert detect_language("x.py") == "python"
    assert detect_language("x.rs") == "rust"
    assert detect_language("x.cpp") == "cpp"
    assert detect_language("x.tsx") == "typescript"
    assert detect_language("x.zzz") is None

    python = server_candidates("python", ROOT)
    assert [c["name"] for c in python] == ["pyright-langserver", "pylsp"]
    assert isinstance(python[0]["available"], bool)
    venv_pyright = ROOT / ".venv" / "bin" / "pyright-langserver"
    if venv_pyright.exists():
        assert python[0]["available"] is True
        assert Path(python[0]["path"]).name == "pyright-langserver"

    snapshot = available_servers(ROOT)
    assert snapshot["ok"] is True
    assert {"python", "rust", "c", "cpp", "typescript"} <= set(
        snapshot["languages"])


def test_shared_client_is_reused_and_closed(tmp_path: Path) -> None:
    from scripts.ocelot_lsp import close_all, get_client

    root = tmp_path / "shared_repo"
    root.mkdir()
    _write_fixture(root)
    server = tmp_path / "shared_fake_lsp.py"
    server.write_text(FAKE_SERVER, encoding="utf-8")
    command = [sys.executable, str(server)]
    env = {"FAKE_LSP_LOG": str(tmp_path / "shared.log")}
    first = get_client(root, "python", command, env=env)
    second = get_client(root, "python", command, env=env)
    try:
        assert first is second
        assert first.server_status()["running"] is False
        assert first.definition("b.py", 3, 4)["ok"] is True
        receipt = close_all()
        assert receipt["ok"] is True
        assert receipt["closed"] >= 1
        assert receipt["started"] >= 1
    finally:
        close_all()


def test_protocol_framing_initialize_and_open_before_query(fake_lsp) -> None:
    root, client, log = fake_lsp["root"], fake_lsp["client"], fake_lsp["log"]
    status = client.server_status()
    assert status["available"] is True
    assert status["running"] is False  # status must not spawn a server

    response = client.definition("b.py", 3, 4)
    assert response["ok"] is True, response
    assert response["locations"][0]["path"] == "a.py"

    messages = _client_messages(log)
    methods = [m["method"] for m in messages]
    assert methods[0] == "initialize"
    assert "initialized" in methods
    assert "textDocument/didOpen" in methods
    assert methods.index("textDocument/didOpen") < methods.index(
        "textDocument/definition")
    initialize = next(m for m in messages if m["method"] == "initialize")
    assert initialize["jsonrpc"] == "2.0"
    assert initialize["params"]["rootUri"] == root.resolve().as_uri()
    caps = initialize["params"]["capabilities"]
    assert caps["textDocument"]["definition"]["linkSupport"] is True
    assert caps["textDocument"]["references"] == {"dynamicRegistration": False}
    # Every client request has a unique integer id; no notification has one.
    ids = [m["id"] for m in messages if isinstance(m.get("id"), int)]
    assert ids and len(ids) == len(set(ids))
    assert all("id" not in m for m in messages
               if m["method"] in ("initialized", "textDocument/didOpen"))

    # Framing: every frame carries a Content-Length matching the UTF-8 body.
    frames = [m["__frame__"] for m in _messages(log) if "__frame__" in m]
    assert frames
    for frame in frames:
        assert frame["header"].startswith("Content-Length: ")
        assert frame["length"] == frame["body_bytes"] == int(
            frame["header"].split(":", 1)[1].strip())


def test_utf8_content_length_framing(fake_lsp) -> None:
    """Non-ASCII source must be framed by UTF-8 byte length, not characters."""
    client, log = fake_lsp["client"], fake_lsp["log"]
    result = client.document_symbols("u.py")
    assert result["ok"] is True, result
    frames = [m["__frame__"] for m in _messages(log) if "__frame__" in m]
    assert frames
    assert any(frame["body_bytes"] > 100 for frame in frames)
    for frame in frames:
        assert frame["length"] == frame["body_bytes"]


def test_definition_document_symbols_and_hover(fake_lsp) -> None:
    client = fake_lsp["client"]
    definition = client.definition("b.py", 3, 4)
    assert definition["ok"] is True
    assert definition["count"] == 1 and definition["found"] is True
    location = definition["locations"][0]
    assert location["path"] == "a.py"
    assert (location["line"], location["character"]) == (2, 4)
    assert location["uri"].startswith("file://")

    symbols = client.document_symbols("a.py")
    assert symbols["ok"] is True
    assert symbols["top_level"] == 2
    assert symbols["count"] == 3
    assert [s["name"] for s in symbols["symbols"]] == ["alpha", "Widget"]
    assert symbols["symbols"][1]["children"][0]["name"] == "render"
    assert symbols["symbols"][1]["children"][0]["kind_name"] == "method"

    hover = client.hover("a.py", 0, 4)
    assert hover["ok"] is True and hover["found"] is True
    assert "alpha" in hover["contents"]
    assert hover["markup_kind"] == "markdown"


def test_references_and_symbol_impact_grouping(fake_lsp) -> None:
    root, client = fake_lsp["root"], fake_lsp["client"]
    before = {name: _hash(root / name) for name in ("a.py", "b.py", "c.py")}

    refs = client.references("a.py", 0, 4)
    assert refs["ok"] is True
    assert refs["count"] == 3
    assert refs["attempts"] == 2
    assert refs["retried"] is True
    assert [loc["path"] for loc in refs["locations"]] == ["a.py", "b.py", "b.py"]
    assert refs["include_declaration"] is False

    impact = client.symbol_impact("a.py", 0, 4)
    assert impact["ok"] is True
    assert impact["file_count"] == 2
    assert impact["total"] == 3
    assert impact["attempts"] == 1
    assert impact["retried"] is False
    assert impact["written"] is False and impact["writes"] is False
    assert impact["read_only"] is True
    # Groups are ordered by reference count, then path.
    assert impact["files"][0]["path"] == "b.py"
    assert impact["files"][0]["count"] == 2
    assert impact["files"][0]["references"] == [
        {"line": 3, "character": 4, "end_line": 3, "end_character": 9},
        {"line": 5, "character": 8, "end_line": 5, "end_character": 13},
    ]
    assert impact["files"][1]["path"] == "a.py"
    assert impact["files"][1]["count"] == 1
    assert {name: _hash(root / name) for name in before} == before


def test_diagnostics_cache_and_change_invalidation(fake_lsp) -> None:
    root, client, log = fake_lsp["root"], fake_lsp["client"], fake_lsp["log"]
    first = client.diagnostics("b.py")
    assert first["ok"] is True
    assert first["published"] is True
    assert first["count"] == 1
    assert first["diagnostics"][0]["message"] == "imported but unused"
    assert first["diagnostics"][0]["severity_name"] == "warning"
    assert first["diagnostics"][0]["code"] == "F401"

    second = client.diagnostics("b.py")
    assert second["ok"] is True
    assert second["cached"] is True
    assert second["waited"] is False
    assert second["count"] == 1

    opens = [m for m in _client_messages(log)
             if m["method"] == "textDocument/didOpen"
             and m["params"]["textDocument"]["uri"].endswith("/b.py")]
    assert len(opens) == 1

    # Empty diagnostics are cached too (a published empty list is a fact).
    quiet = client.diagnostics("a.py")
    assert quiet["ok"] is True and quiet["count"] == 0
    assert quiet["published"] is True

    (root / "b.py").write_text("BROKEN\n", encoding="utf-8")
    changed = client.diagnostics("b.py")
    assert changed["ok"] is True
    assert changed["count"] == 1
    assert changed["diagnostics"][0]["message"] == "broken token"
    changes = [m for m in _client_messages(log)
               if m["method"] == "textDocument/didChange"]
    assert len(changes) == 1
    assert changes[0]["params"]["textDocument"]["version"] == 2


def test_call_hierarchy_roundtrips_the_server_item(fake_lsp) -> None:
    client = fake_lsp["client"]
    prepared = client.prepare_call_hierarchy("a.py", 0, 4)
    assert prepared["ok"] is True and prepared["count"] == 1
    assert prepared["items"][0]["name"] == "alpha"
    assert prepared["items"][0]["path"] == "a.py"

    incoming = client.incoming_calls("a.py", 0, 4)
    assert incoming["ok"] is True, incoming
    assert incoming["count"] == 1
    assert incoming["calls"][0]["name"] == "caller"
    assert incoming["calls"][0]["path"] == "b.py"
    assert incoming["calls"][0]["direction"] == "incoming"
    assert incoming["calls"][0]["ranges"][0]["line"] == 3

    outgoing = client.outgoing_calls("a.py", 0, 4)
    assert outgoing["ok"] is True, outgoing
    assert outgoing["count"] == 1
    assert outgoing["calls"][0]["name"] == "callee"
    assert outgoing["calls"][0]["path"] == "c.py"
    assert outgoing["calls"][0]["direction"] == "outgoing"


def test_rename_preview_is_read_only_and_grouped(fake_lsp) -> None:
    root, client = fake_lsp["root"], fake_lsp["client"]
    before = {name: _hash(root / name) for name in ("a.py", "b.py")}
    preview = client.rename_preview("a.py", 0, 4, "omega")
    assert preview["ok"] is True, preview
    assert preview["applied"] is False
    assert preview["writes"] is False
    assert preview["preview"] is True
    assert preview["new_name"] == "omega"
    assert preview["file_count"] == 2
    assert preview["total_edits"] == 3
    assert [f["path"] for f in preview["files"]] == ["a.py", "b.py"]
    assert [f["count"] for f in preview["files"]] == [2, 1]
    assert preview["files"][0]["edits"][0]["newText"] == "omega"
    assert {name: _hash(root / name) for name in before} == before


def test_request_timeout_is_honest_and_server_stays_usable(fake_lsp) -> None:
    client = fake_lsp["client"]
    timed = client.request("fake/hang", {}, timeout=0.25)
    assert timed["ok"] is False
    assert timed["timeout"] is True
    assert "timed out" in timed["error"]
    assert client.server_status()["running"] is True
    again = client.definition("b.py", 3, 4)
    assert again["ok"] is True


def test_server_error_is_reported(fake_lsp) -> None:
    client = fake_lsp["client"]
    response = client.request("fake/unknown", {}, timeout=2.0)
    assert response["ok"] is False
    assert "server error" in response["error"]
    assert "-32601" in response["error"]


def test_absent_server_fails_honestly(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write_fixture(root)
    missing = tmp_path / "definitely-not-a-language-server"
    client = LSPClient(root, "python", command=str(missing))
    try:
        status = client.server_status()
        assert status["ok"] is False
        assert status["available"] is False
        assert status["running"] is False
        assert "not found" in status["error"]

        response = client.definition("a.py", 0, 4)
        assert response["ok"] is False
        assert response["available"] is False
        assert "not found" in response["error"]
    finally:
        closed = client.close()
    assert closed["ok"] is True
    assert closed["started"] is False


def test_unsupported_language_fails_honestly(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write_fixture(root)
    client = LSPClient(root, "cobol")
    try:
        status = client.server_status()
        assert status["ok"] is False
        assert status["supported"] is False
        assert "unsupported language" in status["error"]
        response = client.document_symbols("a.py")
        assert response["ok"] is False
        assert response["available"] is False
    finally:
        client.close()


def test_close_is_explicit_and_idempotent(fake_lsp) -> None:
    client, log = fake_lsp["client"], fake_lsp["log"]
    assert client.definition("a.py", 0, 4)["ok"] is True
    closed = client.close()
    assert closed["ok"] is True
    assert closed["started"] is True
    assert closed["running"] is False
    assert client.server_status()["running"] is False
    again = client.close()
    assert again["already_closed"] is True
    methods = [m["method"] for m in _client_messages(log)]
    assert "shutdown" in methods and "exit" in methods


# --------------------------------------------------------------------------- #
# Optional live smoke tests. NOT part of the default gate.
# --------------------------------------------------------------------------- #
LIVE = os.environ.get("OCELOT_LIVE_LSP") == "1"
LIVE_REASON = "set OCELOT_LIVE_LSP=1 to run live language-server smoke tests"


def _cargo_project(root: Path) -> None:
    (root / "src").mkdir(parents=True)
    (root / "Cargo.toml").write_text(
        "[package]\n"
        "name = \"lsp_live\"\n"
        "version = \"0.1.0\"\n"
        "edition = \"2021\"\n",
        encoding="utf-8")
    (root / "src" / "main.rs").write_text(
        "fn alpha() -> i32 { 1 }\n"
        "\n"
        "fn main() {\n"
        "    let _ = alpha();\n"
        "}\n",
        encoding="utf-8")


@pytest.mark.skipif(not LIVE, reason=LIVE_REASON)
def test_live_rust_analyzer_definition(tmp_path: Path) -> None:
    if shutil.which("rust-analyzer") is None:
        pytest.skip("rust-analyzer is not on PATH")
    root = tmp_path / "rust_live"
    root.mkdir()
    _cargo_project(root)
    client = LSPClient(root, "rust", timeout=30.0, initialize_timeout=60.0)
    try:
        response = client.definition("src/main.rs", 3, 12)
    finally:
        status = client.server_status()
        client.close()
    if not response.get("ok"):
        pytest.skip(f"rust-analyzer unavailable in this environment: "
                    f"{response.get('error')}")
    if not response.get("locations"):
        pytest.skip(f"rust-analyzer gave no definition yet; status={status}")
    assert any(loc["path"].endswith("src/main.rs")
               for loc in response["locations"])


@pytest.mark.skipif(not LIVE, reason=LIVE_REASON)
def test_live_pyright_definition(tmp_path: Path) -> None:
    if (shutil.which("pyright-langserver") is None
            and not (ROOT / ".venv" / "bin" / "pyright-langserver").exists()):
        pytest.skip("pyright-langserver is not installed")
    root = tmp_path / "python_live"
    root.mkdir()
    (root / "a.py").write_text(
        "def alpha(x: int) -> int:\n"
        "    return x + 1\n",
        encoding="utf-8")
    (root / "b.py").write_text(
        "from a import alpha\n"
        "\n"
        "value = alpha(1)\n",
        encoding="utf-8")
    client = LSPClient(root, "python", timeout=30.0, initialize_timeout=60.0)
    try:
        response = client.definition("b.py", 2, 8)
    finally:
        client.close()
    if not response.get("ok"):
        pytest.skip(f"pyright unavailable in this environment: "
                    f"{response.get('error')}")
    if not response.get("locations"):
        pytest.skip("pyright gave no definition for the smoke fixture")
    assert any(loc["path"] == "a.py" for loc in response["locations"])
