"""Authenticated OpenAI-compatible API backed by CoW Ocelot sessions.

Configure ``OCELOT_API_TOKENS`` as a JSON object mapping bearer tokens to
stable principal IDs. This process owns its own baseline adapter and CoW
session registry; it does not expose the daemon's administrative API.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import signal
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlsplit

from domains.cow_sessions import CowSessionManager
from domains.world_adapter_cow import AdapterForkError
from substrate.world_adapter import WorldAdapter
from substrate.boot_profiles import load_conversation_seed_profile

_MAX_BODY = 1_048_576
_MAX_WORKERS = 32
_UNSUPPORTED_FIELDS = {
    "tools", "tool_choice", "functions", "function_call", "response_format",
    "modalities", "audio", "temperature", "top_p", "n", "seed",
    "max_tokens", "max_completion_tokens", "stop", "presence_penalty",
    "frequency_penalty", "logit_bias", "logprobs", "top_logprobs",
    "stream_options",
}


def _error(message: str, *, kind: str = "invalid_request_error",
           code: str | None = None) -> dict:
    return {"error": {"message": message, "type": kind, "param": None,
                       "code": code}}


def _message_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            else:
                raise ValueError("only text message content is supported")
        return "".join(parts)
    raise ValueError("message content must be a string or text-part list")


class OcelotAPIServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, manager: CowSessionManager,
                 tokens: dict[str, str]):
        token_map = {str(token): str(principal).strip()
                     for token, principal in tokens.items()
                     if str(token) and str(principal).strip()}
        if not token_map:
            raise ValueError("at least one OCELOT_API_TOKENS bearer token is required")
        self.manager = manager
        self.tokens = token_map
        self._request_slots = threading.BoundedSemaphore(_MAX_WORKERS)
        super().__init__(address, OcelotAPIHandler)

    def process_request(self, request, client_address):
        if not self._request_slots.acquire(blocking=False):
            try:
                request.sendall(
                    b"HTTP/1.1 503 Service Unavailable\r\n"
                    b"Connection: close\r\nContent-Length: 0\r\n\r\n")
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._request_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()


class OcelotAPIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def log_message(self, _format, *args):
        # Avoid logging authorization headers, request bodies, or user prompts.
        return

    def _send(self, status: int, obj: dict, *, headers: dict | None = None):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if self.close_connection:
            self.send_header("Connection", "close")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _principal(self) -> str | None:
        scheme, _, token = self.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer":
            return None
        supplied = token.encode("utf-8")
        matched = None
        for configured, principal in self.server.tokens.items():
            if hmac.compare_digest(supplied, configured.encode("utf-8")):
                matched = principal
        return matched

    def _auth_or_reject(self) -> str | None:
        principal = self._principal()
        if principal is None:
            self.close_connection = True
            self._send(401, _error("Invalid or missing bearer token",
                                   kind="authentication_error",
                                   code="invalid_api_key"),
                       headers={"WWW-Authenticate": "Bearer"})
        return principal

    def _body(self) -> dict:
        if self.headers.get("Transfer-Encoding"):
            raise ValueError("Transfer-Encoding requests are not supported")
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > _MAX_BODY:
            raise OverflowError("request body exceeds 1 MiB")
        raw = self.rfile.read(length)
        value = json.loads(raw or b"{}")
        if not isinstance(value, dict):
            raise ValueError("request JSON must be an object")
        return value

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            return self._send(200, {"ok": True})
        principal = self._auth_or_reject()
        if principal is None:
            return
        if path == "/v1/models":
            return self._send(200, {"object": "list", "data": [{
                "id": "ocelot", "object": "model", "created": 0,
                "owned_by": "ocelot"}]})
        if path == "/v1/ocelot/sessions":
            return self._send(200, {
                "object": "list", "data": self.server.manager.list_sessions(principal)})
        prefix = "/v1/ocelot/sessions/"
        if path.startswith(prefix):
            session_id = unquote(path[len(prefix):])
            try:
                session = self.server.manager.get_session(principal, session_id)
                return self._send(200, self.server.manager.describe_session(session))
            except KeyError:
                return self._send(404, _error("session not found",
                                               code="session_not_found"))
        return self._send(404, _error("Not found", code="not_found"))

    def do_POST(self):
        path = urlsplit(self.path).path
        principal = self._auth_or_reject()
        if principal is None:
            return
        try:
            payload = self._body()
        except OverflowError as exc:
            self.close_connection = True
            return self._send(413, _error(str(exc), code="request_too_large"))
        except (ValueError, json.JSONDecodeError) as exc:
            self.close_connection = True
            return self._send(400, _error(str(exc), code="invalid_json"))

        manager = self.server.manager
        if path == "/v1/chat/completions":
            return self._chat(principal, payload)
        if path == "/v1/ocelot/sessions":
            try:
                return self._send(201, manager.create_session(principal))
            except AdapterForkError as exc:
                return self._send(409, _error(str(exc), code="snapshot_unavailable"))
        suffix = "/fork"
        prefix = "/v1/ocelot/sessions/"
        if path.startswith(prefix) and path.endswith(suffix):
            session_id = unquote(path[len(prefix):-len(suffix)])
            try:
                return self._send(201, manager.fork_session(principal, session_id))
            except KeyError:
                return self._send(404, _error("session not found",
                                               code="session_not_found"))
            except AdapterForkError as exc:
                return self._send(409, _error(str(exc), code="snapshot_unavailable"))
        return self._send(404, _error("Not found", code="not_found"))

    def _chat(self, principal: str, payload: dict):
        manager = self.server.manager
        if payload.get("stream"):
            return self._send(501, _error("streaming is not supported yet",
                                          code="streaming_not_supported"))
        unsupported = sorted(
            field for field in _UNSUPPORTED_FIELDS
            if field in payload and payload[field] is not None)
        if unsupported:
            return self._send(501, _error(
                f"unsupported request parameter: {unsupported[0]}",
                code="unsupported_parameter"))
        model = payload.get("model", "ocelot")
        if model != "ocelot":
            return self._send(404, _error(f"model {model!r} is not available",
                                          code="model_not_found"))
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            return self._send(400, _error("messages must be a non-empty array",
                                          code="invalid_messages"))
        try:
            extracted = []
            for message in messages:
                if not isinstance(message, dict):
                    raise ValueError("each message must be an object")
                role = message.get("role")
                if role not in {"system", "developer", "user", "assistant"}:
                    raise ValueError(f"unsupported message role: {role!r}")
                extracted.append((role, _message_text(message.get("content"))))
        except ValueError as exc:
            return self._send(400, _error(str(exc), code="invalid_messages"))
        user_messages = [text for role, text in extracted if role == "user"]
        if not user_messages or not user_messages[-1].strip():
            return self._send(400, _error("the final conversation input must contain a user message",
                                          code="missing_user_message"))

        session_id = self.headers.get("Ocelot-Session-ID")
        if not session_id:
            session_id = manager.ensure_default_session(principal)
        try:
            session = manager.get_session(principal, session_id)
        except KeyError:
            return self._send(404, _error("session not found",
                                          code="session_not_found"))
        try:
            # Previous turns already live in this graph. Do not replay the
            # caller's complete message list into the stateful adapter. System
            # and developer messages are carried as labeled text context on
            # this turn because WorldAdapter.converse has no role-aware prompt
            # contract of its own.
            instructions = [text for role, text in extracted
                            if role in {"system", "developer"} and text.strip()]
            agent_input = user_messages[-1]
            if instructions:
                agent_input = ("Instructions:\n" + "\n".join(instructions)
                               + "\n\nUser:\n" + agent_input)
            reply = manager.chat(principal, session_id, agent_input)
        except KeyError:
            return self._send(404, _error("session not found",
                                          code="session_not_found"))
        except Exception as exc:  # don't expose internals or prompt contents
            return self._send(500, _error(
                f"Ocelot turn failed ({type(exc).__name__})",
                kind="server_error", code="ocelot_turn_failed"))
        return self._send(200, {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion", "created": int(time.time()),
            "model": "ocelot", "choices": [{"index": 0,
                "message": {"role": "assistant", "content": str(reply)},
                "finish_reason": "stop"}],
            # Ocelot does not currently expose tokenizer-level usage counts.
            "usage": {"prompt_tokens": 0, "completion_tokens": 0,
                      "total_tokens": 0},
        })

    def do_DELETE(self):
        path = urlsplit(self.path).path
        principal = self._auth_or_reject()
        if principal is None:
            return
        manager = self.server.manager
        if path == "/v1/ocelot/namespace":
            try:
                manager.clear_user(principal)
            except AdapterForkError as exc:
                return self._send(409, _error(str(exc), code="snapshot_unavailable"))
            return self._send(200, {"ok": True, "cleared": "namespace"})
        prefix = "/v1/ocelot/sessions/"
        if path.startswith(prefix):
            session_id = unquote(path[len(prefix):])
            try:
                return self._send(200, manager.clear_session(principal, session_id))
            except KeyError:
                return self._send(404, _error("session not found",
                                               code="session_not_found"))
            except AdapterForkError as exc:
                return self._send(409, _error(str(exc), code="snapshot_unavailable"))
        return self._send(404, _error("Not found", code="not_found"))


def make_server(host: str, port: int, baseline: WorldAdapter,
                tokens: dict[str, str], *,
                storage_dir: str | os.PathLike | None = None,
                baseline_mode: str = "shared",
                isolation_mode: str = "whole_adapter") -> OcelotAPIServer:
    return OcelotAPIServer((host, port),
                           CowSessionManager(baseline, storage_dir=storage_dir,
                                             baseline_mode=baseline_mode,
                                             isolation_mode=isolation_mode),
                           tokens)


def build_default_baseline() -> WorldAdapter:
    """Build the same validated connected conversation profile as the daemon."""
    adapter = WorldAdapter(seeds=())
    report = load_conversation_seed_profile(adapter)
    if not report.get("selection_complete") or report.get("failed"):
        raise RuntimeError(
            "connected conversation seed profile failed: "
            f"selection_complete={report.get('selection_complete')}, "
            f"failed={report.get('failed')}")
    return adapter


def _load_tokens(raw: str) -> dict[str, str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("OCELOT_API_TOKENS must be a JSON object") from exc
    if not isinstance(value, dict):
        raise ValueError("OCELOT_API_TOKENS must be a JSON object")
    return value


def _handle_sigterm(_signum, _frame) -> None:
    """Route container shutdown through the server's normal cleanup path."""
    raise KeyboardInterrupt


def main() -> int:
    # Register before parsing configuration or booting the seeded profile.
    # Python's default SIGTERM disposition is ignored when it is the
    # container's PID 1; route shutdown through the normal cleanup path.
    signal.signal(signal.SIGTERM, _handle_sigterm)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("OCELOT_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("OCELOT_API_PORT", "8790")))
    args = parser.parse_args()
    storage_dir = os.environ.get(
        "OCELOT_STATE_DIR", os.path.expanduser("~/.ocelot/api"))
    server = None
    try:
        server = make_server(
            args.host, args.port, build_default_baseline(),
            _load_tokens(os.environ.get("OCELOT_API_TOKENS", "{}")),
            storage_dir=storage_dir,
            baseline_mode=os.environ.get("OCELOT_BASELINE_MODE", "shared"),
            isolation_mode=os.environ.get("OCELOT_ISOLATION_MODE", "whole_adapter"))
        print(f"Ocelot API listening on http://{args.host}:{args.port}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if server is not None:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
