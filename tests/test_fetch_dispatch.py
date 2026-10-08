"""test_fetch_dispatch — end-to-end exercise of the fetch-dispatch MECHANISM
(domains/fetch_dispatch.py): mint a FetchRequest against a LOCAL stdlib
http.server (no real internet), scan_and_fetch it, and verify the fetched
content lands in the graph per the node-vocabulary contract. Also covers the
failure path (unreachable port) and the scheme-refusal security boundary
(file://).

Mirrors tests/test_experiment_dispatch.py's shape (mint -> scan -> assert on
the graph), but fetch is synchronous so there's no poll-loop.
"""
from __future__ import annotations

import http.server
import concurrent.futures
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.fetch_dispatch import mint_fetch_request, scan_and_fetch

# The small fast-boot seed set (mirrors scripts/converse_demo.py's CHAT_SEEDS).
CHAT_SEEDS = ["relations", "intent", "conversation", "discourse", "conversation_reply",
              "reference_resolution", "language_foundation", "lang_production",
              "communication_concepts", "grounding"]

PAGE_HTML = """<html><head><title>Fetch Test Page</title></head>
<body><p>Hello from the local test server.</p>
<script>should_not_appear();</script>
<p>Second paragraph, more words here.</p>
</body></html>"""


@pytest.fixture()
def adapter():
    a = WorldAdapter()
    for sid in CHAT_SEEDS:
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception:
            pass
    return a


@pytest.fixture()
def local_server(tmp_path):
    """A local stdlib http.server on an ephemeral port, serving PAGE_HTML
    from a temp dir. No real network access."""
    (tmp_path / "index.html").write_text(PAGE_HTML)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(tmp_path), **kw)

        def log_message(self, fmt, *a):  # quiet
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}/index.html"
    finally:
        srv.shutdown()
        srv.server_close()


def test_scan_and_fetch_success(adapter, local_server):
    req = mint_fetch_request(adapter, local_server, purpose="test fetch")
    assert adapter.s.node(req)["attrs"]["status"] == "requested"

    touched = scan_and_fetch(adapter, timeout=5)
    assert touched == [req]

    a = adapter.s.node(req)["attrs"]
    assert a["status"] == "done", a
    assert "error" not in a or not a["error"]

    S, I = adapter.s, adapter.inner
    fetched_ids = [n for n in I.neighbours(req, "fetched") if I.has_node(n)]
    assert len(fetched_ids) == 1
    doc = fetched_ids[0]
    doc_a = S.node(doc)["attrs"]
    assert S.node(doc)["type"] == "WebDocument"
    assert doc_a["title"] == "Fetch Test Page"
    assert "Hello from the local test server" in doc_a["text"]
    assert "Second paragraph" in doc_a["text"]
    assert "should_not_appear" not in doc_a["text"]     # <script> content excluded
    assert doc_a["status"] == 200
    assert doc_a["byte_length"] > 0

    mentions = [n for n in I.neighbours(doc, "has_mention") if I.has_node(n)]
    assert len(mentions) > 0
    mention_texts = {S.node(m)["attrs"]["text"] for m in mentions}
    assert "hello" in mention_texts
    assert "paragraph" in mention_texts

    # next_mention/prev_mention chain is wired (at least one link).
    chained = [m for m in mentions if list(I.neighbours(m, "next_mention"))]
    assert len(chained) >= 1


def test_authored_http_get_reuses_keep_alive_connection():
    from domains.http_transport import close_idle_connections
    from domains.runtime_design import (agent_specify_http_get,
                                        emit_external_io_binding)

    class KeepAliveHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self):
            super().setup()
            self.server.connection_count += 1

        def do_GET(self):
            self.server.request_count += 1
            body = f"body:{self.path}".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), KeepAliveHandler)
    srv.connection_count = 0
    srv.request_count = 0
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    namespace = {}
    source = emit_external_io_binding(agent_specify_http_get())[
        "world_adapter.py (binding)"]
    exec(compile(source, "<test-authored-http-get>", "exec"), namespace)
    get = namespace["http_get"]
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        first = get(base + "/first", timeout=2)
        second = get(base + "/second", timeout=2)
        assert first["text"] == "body:/first"
        assert second["text"] == "body:/second"
        assert first["status"] == second["status"] == 200
        assert srv.request_count == 2
        assert srv.connection_count == 1
    finally:
        close_idle_connections()
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)


def test_https_connections_reuse_process_client_trust_context(monkeypatch):
    import domains.http_transport as transport

    context = object()
    created = []
    connections = []

    def create_context():
        created.append(context)
        return context

    class FakeHTTPSConnection:
        def __init__(self, host, port, *, timeout, context):
            self.host = host
            self.port = port
            self.timeout = timeout
            self.context = context
            connections.append(self)

    monkeypatch.setattr(transport, "_SSL_CONTEXT", None)
    monkeypatch.setattr(transport.ssl, "create_default_context", create_context)
    monkeypatch.setattr(transport.http.client, "HTTPSConnection",
                        FakeHTTPSConnection)

    first = transport._new_connection(("https", "example.test", 443), 2)
    second = transport._new_connection(("https", "example.test", 443), 2)

    assert len(created) == 1
    assert len(connections) == 2
    assert first.context is second.context is context
    assert (first.host, first.port, first.timeout) == (
        "example.test", 443, 2)


def test_authored_http_get_allows_bounded_same_origin_concurrency():
    from domains.http_transport import close_idle_connections, http_get

    class ConcurrentHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self):
            super().setup()
            with self.server.guard:
                self.server.connections.add(self.connection.fileno())

        def do_GET(self):
            with self.server.guard:
                self.server.active += 1
                self.server.max_active = max(self.server.max_active,
                                             self.server.active)
            time.sleep(0.08)
            body = self.path.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            with self.server.guard:
                self.server.active -= 1

        def log_message(self, fmt, *args):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ConcurrentHandler)
    srv.guard = threading.Lock()
    srv.connections = set()
    srv.active = 0
    srv.max_active = 0
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(
                lambda i: http_get(f"{base}/item-{i}", timeout=3), range(4)))
        assert [item["text"] for item in results] == [
            f"/item-{i}" for i in range(4)]
        assert srv.max_active > 1
        assert len(srv.connections) <= 4
    finally:
        srv.shutdown()
        srv.server_close()
        close_idle_connections()
        thread.join(timeout=2)


def test_scan_and_fetch_failure_unreachable(adapter):
    # Bind an ephemeral port then close it immediately -> nothing listens there,
    # connection refused (still entirely local, no real internet touched).
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    req = mint_fetch_request(adapter, f"http://127.0.0.1:{port}/nope")
    touched = scan_and_fetch(adapter, timeout=3)
    assert touched == [req]

    a = adapter.s.node(req)["attrs"]
    assert a["status"] == "failed", a
    assert a.get("error")

    I = adapter.inner
    assert [n for n in I.neighbours(req, "fetched") if I.has_node(n)] == []


def test_scan_and_fetch_refuses_file_scheme(adapter, tmp_path):
    local_file = tmp_path / "secret.txt"
    local_file.write_text("should never be read")

    req = mint_fetch_request(adapter, f"file://{local_file}")
    touched = scan_and_fetch(adapter, timeout=3)
    assert touched == [req]

    a = adapter.s.node(req)["attrs"]
    assert a["status"] == "failed", a
    assert "scheme" in a.get("error", "").lower()

    I = adapter.inner
    assert [n for n in I.neighbours(req, "fetched") if I.has_node(n)] == []


def test_scan_and_fetch_noop_when_nothing_requested(adapter):
    assert scan_and_fetch(adapter, timeout=3) == []


def test_optional_reference_transports_stay_out_of_profile_imports():
    code = (
        "import sys; "
        "import domains.fetch_dispatch; "
        "import domains.wiktionary_reference; "
        "assert 'urllib.request' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_fetch_dispatch_urllib_fallback_remains_available(monkeypatch):
    from urllib import request
    from domains import fetch_dispatch as fd

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, size):
            assert size == 5
            return b"test!"

    monkeypatch.setattr(fd, "_materialize_http_get", lambda: None)
    monkeypatch.setattr(request, "urlopen", lambda *_a, **_kw: FakeResponse())
    result, route = fd._fetch(
        "https://example.invalid/test", timeout=1, max_bytes=4)

    assert route == "fallback_urllib"
    assert result == {
        "status": 200, "length": 5, "text": "test",
        "url": "https://example.invalid/test",
    }


def test_scan_and_fetch_with_supplied_http_get(adapter, local_server):
    """`http_get` override path (mainly for tests / callers with their own
    materialized effector) — used AS GIVEN, no fallback."""
    calls = []

    def fake_get(url, *, timeout=15):
        calls.append((url, timeout))
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "test-agent"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
        return {"status": resp.status, "length": len(body),
               "text": body.decode("utf-8"), "url": url}

    req = mint_fetch_request(adapter, local_server)
    touched = scan_and_fetch(adapter, http_get=fake_get, timeout=5)
    assert touched == [req]
    assert calls and calls[0][0] == local_server
    assert adapter.s.node(req)["attrs"]["status"] == "done"
