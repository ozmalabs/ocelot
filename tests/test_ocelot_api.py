"""Wire-level tests for the OpenAI-compatible Ocelot API."""
from __future__ import annotations

import json
import http.client
import threading
import urllib.error
import urllib.request

from scripts import ocelot_api
from scripts.ocelot_api import make_server
from substrate.world_adapter import WorldAdapter


def test_cli_baseline_uses_validated_conversation_seed_profile(monkeypatch):
    loaded = []

    def load_profile(adapter):
        loaded.append(adapter)
        adapter.s.add_node("ConversationProfileMarker", {"ready": True})
        return {"selection_complete": True, "failed": []}

    monkeypatch.setattr(ocelot_api, "load_conversation_seed_profile", load_profile)
    baseline = ocelot_api.build_default_baseline()

    assert len(loaded) == 1
    assert loaded[0] is baseline
    assert len(list(baseline.s.nodes("ConversationProfileMarker"))) == 1


def _request(server, method, path, *, token=None, body=None, session_id=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    if session_id:
        headers["Ocelot-Session-ID"] = session_id
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"http://127.0.0.1:{server.server_port}{path}",
        data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as response:
        return response.code, json.loads(response.read())


def test_openai_chat_response_and_bearer_auth():
    server = make_server("127.0.0.1", 0, WorldAdapter(),
                         {"secret-a": "principal-a"})
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, denied = _request(server, "GET", "/v1/models")
        assert status == 401
        assert denied["error"]["code"] == "invalid_api_key"

        session_id = server.manager.ensure_default_session("principal-a")
        session = server.manager.get_session("principal-a", session_id)
        submitted = []
        session.adapter.converse = lambda text, speaker: (
            submitted.append((text, speaker)) or f"received: {text}")
        status, result = _request(
            server, "POST", "/v1/chat/completions", token="secret-a",
            session_id=session_id,
            body={"model": "ocelot", "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "assistant", "content": "Previous turn already in session."},
                {"role": "user", "content": "hello"}],
                  "user": "principal-b"})
        assert status == 200
        assert result["object"] == "chat.completion"
        assert result["choices"][0]["message"]["content"] == (
            "received: Instructions:\nBe concise.\n\nUser:\nhello")
        assert submitted == [("Instructions:\nBe concise.\n\nUser:\nhello",
                              "principal-a")]
        assert result["usage"]["total_tokens"] == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_session_management_is_principal_scoped_and_clear_is_explicit():
    server = make_server("127.0.0.1", 0, WorldAdapter(), {
        "secret-a": "principal-a", "secret-b": "principal-b"})
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, created = _request(server, "POST", "/v1/ocelot/sessions",
                                  token="secret-a", body={})
        assert status == 201
        status, session_detail = _request(
            server, "GET", f"/v1/ocelot/sessions/{created['id']}",
            token="secret-a")
        assert status == 200
        assert session_detail["id"] == created["id"]
        assert session_detail["isolation"] == "whole_adapter"
        assert session_detail["baseline_mode"] == "shared"
        status, hidden = _request(
            server, "GET", f"/v1/ocelot/sessions/{created['id']}",
            token="secret-b")
        assert status == 404
        assert hidden["error"]["code"] == "session_not_found"
        status, hidden = _request(
            server, "POST", f"/v1/ocelot/sessions/{created['id']}/fork",
            token="secret-b", body={})
        assert status == 404
        assert hidden["error"]["code"] == "session_not_found"
        status, hidden = _request(
            server, "DELETE", f"/v1/ocelot/sessions/{created['id']}",
            token="secret-b")
        assert status == 404
        assert hidden["error"]["code"] == "session_not_found"
        status, sessions_b = _request(server, "GET", "/v1/ocelot/sessions",
                                      token="secret-b")
        assert status == 200
        assert sessions_b["data"] == []

        status, forked = _request(
            server, "POST", f"/v1/ocelot/sessions/{created['id']}/fork",
            token="secret-a", body={})
        assert status == 201
        assert forked["parent_id"] == created["id"]
        status, cleared = _request(
            server, "DELETE", f"/v1/ocelot/sessions/{forked['id']}",
            token="secret-a")
        assert status == 200
        assert cleared["id"] == forked["id"]
        assert server.manager.get_session("principal-a", created["id"])

        status, b_session = _request(
            server, "POST", "/v1/ocelot/sessions", token="secret-b", body={})
        assert status == 201
        status, cleared_namespace = _request(
            server, "DELETE", "/v1/ocelot/namespace", token="secret-a")
        assert status == 200
        assert cleared_namespace["cleared"] == "namespace"
        status, sessions_a = _request(server, "GET", "/v1/ocelot/sessions",
                                      token="secret-a")
        assert status == 200
        assert sessions_a["data"] == []
        status, sessions_b = _request(server, "GET", "/v1/ocelot/sessions",
                                      token="secret-b")
        assert status == 200
        assert [row["id"] for row in sessions_b["data"]] == [b_session["id"]]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_chat_rejects_invalid_model_role_and_malformed_json():
    server = make_server("127.0.0.1", 0, WorldAdapter(),
                         {"secret-a": "principal-a"})
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, unknown_model = _request(
            server, "POST", "/v1/chat/completions", token="secret-a",
            body={"model": "missing", "messages": [
                {"role": "user", "content": "hello"}]})
        assert status == 404
        assert unknown_model["error"]["code"] == "model_not_found"
        status, hidden_alias = _request(
            server, "POST", "/v1/chat/completions", token="secret-a",
            body={"model": "ocelot-chat", "messages": [
                {"role": "user", "content": "hello"}]})
        assert status == 404
        assert hidden_alias["error"]["code"] == "model_not_found"

        status, unknown_role = _request(
            server, "POST", "/v1/chat/completions", token="secret-a",
            body={"model": "ocelot", "messages": [
                {"role": "tool", "content": "hello"}]})
        assert status == 400
        assert unknown_role["error"]["code"] == "invalid_messages"

        status, unsupported_tools = _request(
            server, "POST", "/v1/chat/completions", token="secret-a",
            body={"model": "ocelot", "messages": [
                {"role": "user", "content": "hello"}],
                  "tools": [{"type": "function"}]})
        assert status == 501
        assert unsupported_tools["error"]["code"] == "unsupported_parameter"

        status, unsupported_sampling = _request(
            server, "POST", "/v1/chat/completions", token="secret-a",
            body={"model": "ocelot", "messages": [
                {"role": "user", "content": "hello"}],
                  "temperature": 0.2})
        assert status == 501
        assert unsupported_sampling["error"]["code"] == "unsupported_parameter"

        req = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
            data=b'{"messages":',
            headers={"Authorization": "Bearer secret-a",
                     "Content-Type": "application/json"},
            method="POST")
        try:
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as response:
            assert response.code == 400
            payload = json.loads(response.read())
            assert payload["error"]["code"] == "invalid_json"
        else:
            raise AssertionError("malformed JSON unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_api_rejects_payloads_above_one_megabyte():
    server = make_server("127.0.0.1", 0, WorldAdapter(),
                         {"secret-a": "principal-a"})
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_port, timeout=5)
        connection.putrequest("POST", "/v1/chat/completions")
        connection.putheader("Authorization", "Bearer secret-a")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(1024 * 1024 + 1))
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 413
        payload = json.loads(response.read())
        assert payload["error"]["code"] == "request_too_large"
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
