"""Bounded Confidential Space launcher socket protocol.

This module contains only the fixed local HTTP transport and token envelope
protocol.  Production and the diagnostic probe share it so their handling of
launcher framing cannot diverge.  It never logs or includes token bytes in
errors.
"""

from __future__ import annotations

import hashlib
import json
import socket
from typing import Any, Callable

LAUNCHER_SOCKET = "/run/container_launcher/teeserver.sock"
TOKEN_PATH = "/v1/token"
MAX_TOKEN_BYTES = 64 * 1024
MAX_RESPONSE_HEADERS_BYTES = 8 * 1024

_TOKEN_CHARS = frozenset("!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_JWT_SEGMENT_CHARS = frozenset("-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz")


class LauncherProtocolError(RuntimeError):
    """The launcher response violated the bounded local protocol."""


def _is_token(value: str) -> bool:
    return bool(value) and all(char in _TOKEN_CHARS for char in value)


def _receive(sock: Any, buffer: bytearray) -> None:
    chunk = sock.recv(4096)
    if not chunk:
        raise LauncherProtocolError("launcher response ended early")
    buffer.extend(chunk)


def _read_line(sock: Any, buffer: bytearray, limit: int) -> bytes:
    while True:
        end = buffer.find(b"\r\n")
        if end >= 0:
            if end + 2 > limit:
                raise LauncherProtocolError("launcher response framing line is too large")
            line = bytes(buffer[:end])
            del buffer[:end + 2]
            return line
        if len(buffer) >= limit:
            raise LauncherProtocolError("launcher response framing line is too large")
        _receive(sock, buffer)


def _parse_header_line(line: str, headers: dict[str, str]) -> None:
    name, separator, value = line.partition(":")
    if not separator or not _is_token(name) or name.lower() in headers:
        raise LauncherProtocolError("launcher response headers are invalid")
    if any(ord(char) < 32 and char != "\t" for char in value):
        raise LauncherProtocolError("launcher response headers are invalid")
    headers[name.lower()] = value.strip()


def _parse_chunk_extensions(value: str) -> None:
    for extension in value.split(";"):
        extension = extension.strip(" \t")
        if not extension:
            raise LauncherProtocolError("launcher chunk extensions are invalid")
        name, separator, extension_value = extension.partition("=")
        name = name.strip(" \t")
        if not _is_token(name):
            raise LauncherProtocolError("launcher chunk extensions are invalid")
        if not separator:
            continue
        extension_value = extension_value.strip(" \t")
        if not extension_value:
            raise LauncherProtocolError("launcher chunk extensions are invalid")
        if extension_value.startswith('"'):
            if not extension_value.endswith('"') or len(extension_value) < 2:
                raise LauncherProtocolError("launcher chunk extensions are invalid")
            escaped = False
            for char in extension_value[1:-1]:
                if ord(char) < 32 and char != "\t":
                    raise LauncherProtocolError("launcher chunk extensions are invalid")
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    raise LauncherProtocolError("launcher chunk extensions are invalid")
            if escaped:
                raise LauncherProtocolError("launcher chunk extensions are invalid")
        elif not _is_token(extension_value):
            raise LauncherProtocolError("launcher chunk extensions are invalid")


def _parse_chunk_size(line: bytes) -> int:
    try:
        value = line.decode("ascii")
    except UnicodeDecodeError as exc:
        raise LauncherProtocolError("launcher chunk size is invalid") from exc
    size_text, separator, extensions = value.partition(";")
    if not size_text or any(char not in "0123456789abcdefABCDEF" for char in size_text):
        raise LauncherProtocolError("launcher chunk size is invalid")
    if separator:
        _parse_chunk_extensions(extensions)
    try:
        size = int(size_text, 16)
    except ValueError as exc:
        raise LauncherProtocolError("launcher chunk size is invalid") from exc
    if size > MAX_TOKEN_BYTES:
        raise LauncherProtocolError("launcher token is too large")
    return size


def _read_exact(sock: Any, buffer: bytearray, length: int) -> bytes:
    while len(buffer) < length:
        _receive(sock, buffer)
    value = bytes(buffer[:length])
    del buffer[:length]
    return value


def _reject_trailing_data(sock: Any, buffer: bytearray) -> None:
    if buffer or sock.recv(1):
        raise LauncherProtocolError("launcher response has trailing data")


def _read_chunked_body(sock: Any, buffer: bytearray) -> bytes:
    body = bytearray()
    chunk_count = 0
    while True:
        size = _parse_chunk_size(_read_line(sock, buffer, MAX_RESPONSE_HEADERS_BYTES))
        if size == 0:
            trailers: dict[str, str] = {}
            trailer_bytes = 0
            while True:
                line = _read_line(sock, buffer, MAX_RESPONSE_HEADERS_BYTES)
                trailer_bytes += len(line) + 2
                if trailer_bytes > MAX_RESPONSE_HEADERS_BYTES:
                    raise LauncherProtocolError("launcher response trailers are too large")
                if not line:
                    break
                try:
                    text = line.decode("ascii")
                except UnicodeDecodeError as exc:
                    raise LauncherProtocolError("launcher response trailers are invalid") from exc
                _parse_header_line(text, trailers)
                if text.partition(":")[0].lower() in {"content-length", "transfer-encoding"}:
                    raise LauncherProtocolError("launcher response trailers are invalid")
            _reject_trailing_data(sock, buffer)
            return bytes(body)
        if size > MAX_TOKEN_BYTES - len(body):
            raise LauncherProtocolError("launcher token is too large")
        body.extend(_read_exact(sock, buffer, size))
        if _read_exact(sock, buffer, 2) != b"\r\n":
            raise LauncherProtocolError("launcher chunk data terminator is invalid")
        chunk_count += 1
        if chunk_count > MAX_TOKEN_BYTES:
            raise LauncherProtocolError("launcher response has too many chunks")


def read_response(sock: Any) -> bytes:
    """Read one bounded launcher HTTP response and return only its body."""
    data = bytearray()
    marker = b"\r\n\r\n"
    while marker not in data:
        _receive(sock, data)
        end = data.find(marker)
        if end >= 0:
            if end + len(marker) > MAX_RESPONSE_HEADERS_BYTES:
                raise LauncherProtocolError("launcher response headers are too large")
            break
        if len(data) > MAX_RESPONSE_HEADERS_BYTES:
            raise LauncherProtocolError("launcher response headers are too large")
    end = data.index(marker)
    if end + len(marker) > MAX_RESPONSE_HEADERS_BYTES:
        raise LauncherProtocolError("launcher response headers are too large")
    try:
        header = bytes(data[:end]).decode("ascii")
    except UnicodeDecodeError as exc:
        raise LauncherProtocolError("launcher response headers are invalid") from exc
    lines = header.split("\r\n")
    if not lines or not lines[0].startswith("HTTP/1.1 "):
        raise LauncherProtocolError("launcher_response_status_invalid")
    status_parts = lines[0].split()
    if len(status_parts) < 2 or status_parts[1] != "200":
        code = status_parts[1] if len(status_parts) > 1 and status_parts[1].isdigit() else "unknown"
        raise LauncherProtocolError("launcher_response_status_" + code)
    status_code = status_parts[1]
    headers: dict[str, str] = {}
    for line in lines[1:]:
        _parse_header_line(line, headers)
    content_type = headers.get("content-type", "").split(";", 1)[0].lower()
    buffer = bytearray(data[end + len(marker):])
    transfer_encoding = headers.get("transfer-encoding")
    if transfer_encoding is not None:
        encodings = [part.strip().lower() for part in transfer_encoding.split(",")]
        if "content-length" in headers or encodings != ["chunked"]:
            detail = "content_length" if "content-length" in headers else "encoding"
            raise LauncherProtocolError("launcher_header_transfer_encoding_" + detail)
        body = _read_chunked_body(sock, buffer)
    else:
        content_length = headers.get("content-length")
        if content_length is None or not content_length.isdecimal():
            raise LauncherProtocolError("launcher response length is invalid")
        length = int(content_length)
        if length > MAX_TOKEN_BYTES:
            raise LauncherProtocolError("launcher token is too large")
        body = _read_exact(sock, buffer, length)
        _reject_trailing_data(sock, buffer)
    if content_type not in {"application/json", "application/jwt", "text/html"}:
        value = headers.get("content-type", "missing").lower().replace("/", "_").replace(";", "_")[:48]
        raise LauncherProtocolError(
            "launcher_header_content_type_%s_status_%s_body_sha256_%s_len_%d"
            % (value, status_code, hashlib.sha256(body).hexdigest(), len(body))
        )
    return body


def decode_token(raw: bytes) -> str:
    """Decode the strict token envelope or a bounded compact raw JWT."""
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        try:
            token = raw.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise LauncherProtocolError("launcher_response_not_token") from exc
        if len(token.encode("ascii")) > MAX_TOKEN_BYTES:
            raise LauncherProtocolError("launcher token is too large")
        segments = token.split(".")
        if len(segments) != 3 or not all(segment and all(char in _JWT_SEGMENT_CHARS for char in segment) for segment in segments):
            raise LauncherProtocolError("launcher_response_not_token")
        return token
    if not isinstance(result, dict) or set(result) != {"token"} or not isinstance(result.get("token"), str) or not result["token"]:
        raise LauncherProtocolError("launcher_response_token_schema")
    token = result["token"]
    if len(token.encode("utf-8")) > MAX_TOKEN_BYTES:
        raise LauncherProtocolError("launcher token is too large")
    return token


def build_request(*, audience: str, nonce: str) -> bytes:
    body = json.dumps(
        {"audience": audience, "token_type": "OIDC", "nonces": [nonce]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return (
        b"POST " + TOKEN_PATH.encode("ascii") + b" HTTP/1.1\r\nHost: localhost\r\n"
        b"Content-Type: application/json\r\nAccept: application/json\r\nContent-Length: "
        + str(len(body)).encode("ascii")
        + b"\r\nConnection: close\r\n\r\n"
        + body
    )


def fetch_token(
    *,
    audience: str,
    nonce: str,
    socket_factory: Callable[..., Any] = socket.socket,
) -> str:
    """POST to the fixed launcher socket and return a redaction-safe token."""
    sock = socket_factory(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(5)
        sock.connect(LAUNCHER_SOCKET)
        sock.sendall(build_request(audience=audience, nonce=nonce))
        return decode_token(read_response(sock))
    finally:
        try:
            sock.close()
        except Exception:
            pass
