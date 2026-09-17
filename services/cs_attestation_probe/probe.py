"""Read-only Confidential Space launcher probe.

This probe is diagnostic only. It uses the same fixed launcher protocol as the
production gate and never prints a token or unverified claims.
"""

import hashlib
import json
import os
import re
import secrets
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

LAUNCHER_SOCKET = "/run/container_launcher/teeserver.sock"
TOKEN_PATH = "/v1/token"
MAX_TOKEN_BYTES = 64 * 1024
MAX_RESPONSE_HEADERS_BYTES = 8 * 1024
MAX_EVIDENCE_BYTES = 16 * 1024
MAX_PUBLIC_VALUE_LENGTH = 512
MIN_NONCE_BYTES = 10
MAX_NONCE_BYTES = 74
DEFAULT_WIP_TOKEN_AUDIENCE = "https://sts.googleapis.com"
CONFIDENTIAL_SPACE_JWKS_URI = "https://www.googleapis.com/service_accounts/v1/metadata/jwk/signer@confidentialspace-sign.iam.gserviceaccount.com"
STS_ENDPOINT = "https://sts.googleapis.com/v1/token"
MAX_STS_RESPONSE_BYTES = 64 * 1024


def _bounded_public(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str) and len(value) <= MAX_PUBLIC_VALUE_LENGTH:
        return value
    return None


def _bounded_keys(value: object) -> list[str] | None:
    if not isinstance(value, dict) or len(value) > 128:
        return None
    keys = sorted(key for key in value if isinstance(key, str) and len(key) <= MAX_PUBLIC_VALUE_LENGTH)
    return keys if len(keys) == len(value) else None


def _bounded_strings(value: object) -> list[str] | None:
    if not isinstance(value, list) or len(value) > 16:
        return None
    if not all(isinstance(item, str) and len(item) <= MAX_PUBLIC_VALUE_LENGTH for item in value):
        return None
    return list(value)


def _nonce() -> str:
    value = secrets.token_urlsafe(32)
    size = len(value.encode("utf-8"))
    if not MIN_NONCE_BYTES <= size <= MAX_NONCE_BYTES:
        raise RuntimeError("nonce length is outside 10-74 bytes")
    return value


_TOKEN_CHARS = frozenset("!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _is_token(value: str) -> bool:
    return bool(value) and all(char in _TOKEN_CHARS for char in value)


def _receive(sock: socket.socket, buffer: bytearray) -> None:
    chunk = sock.recv(4096)
    if not chunk:
        raise RuntimeError("launcher response ended early")
    buffer.extend(chunk)


def _read_line(sock: socket.socket, buffer: bytearray, limit: int) -> bytes:
    while True:
        end = buffer.find(b"\r\n")
        if end >= 0:
            if end + 2 > limit:
                raise RuntimeError("launcher response framing line is too large")
            line = bytes(buffer[:end])
            del buffer[:end + 2]
            return line
        if len(buffer) >= limit:
            raise RuntimeError("launcher response framing line is too large")
        _receive(sock, buffer)


def _parse_header_line(line: str, headers: dict[str, str]) -> None:
    name, separator, value = line.partition(":")
    if not separator or not _is_token(name) or name.lower() in headers:
        raise RuntimeError("launcher response headers are invalid")
    if any(ord(char) < 32 and char != "\t" for char in value):
        raise RuntimeError("launcher response headers are invalid")
    headers[name.lower()] = value.strip()


def _parse_chunk_extensions(value: str) -> None:
    for extension in value.split(";"):
        extension = extension.strip(" \t")
        if not extension:
            raise RuntimeError("launcher chunk extensions are invalid")
        name, separator, extension_value = extension.partition("=")
        name = name.strip(" \t")
        if not _is_token(name):
            raise RuntimeError("launcher chunk extensions are invalid")
        if not separator:
            continue
        extension_value = extension_value.strip(" \t")
        if not extension_value:
            raise RuntimeError("launcher chunk extensions are invalid")
        if extension_value.startswith('"'):
            if not extension_value.endswith('"') or len(extension_value) < 2:
                raise RuntimeError("launcher chunk extensions are invalid")
            escaped = False
            for char in extension_value[1:-1]:
                if ord(char) < 32 and char != "\t":
                    raise RuntimeError("launcher chunk extensions are invalid")
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    raise RuntimeError("launcher chunk extensions are invalid")
            if escaped:
                raise RuntimeError("launcher chunk extensions are invalid")
        elif not _is_token(extension_value):
            raise RuntimeError("launcher chunk extensions are invalid")


def _parse_chunk_size(line: bytes) -> int:
    try:
        value = line.decode("ascii")
    except UnicodeDecodeError as exc:
        raise RuntimeError("launcher chunk size is invalid") from exc
    size_text, separator, extensions = value.partition(";")
    if not size_text or any(char not in "0123456789abcdefABCDEF" for char in size_text):
        raise RuntimeError("launcher chunk size is invalid")
    if separator:
        _parse_chunk_extensions(extensions)
    try:
        size = int(size_text, 16)
    except ValueError as exc:
        raise RuntimeError("launcher chunk size is invalid") from exc
    if size > MAX_TOKEN_BYTES:
        raise RuntimeError("launcher token is too large")
    return size


def _read_exact(sock: socket.socket, buffer: bytearray, length: int) -> bytes:
    while len(buffer) < length:
        _receive(sock, buffer)
    value = bytes(buffer[:length])
    del buffer[:length]
    return value


def _reject_trailing_data(sock: socket.socket, buffer: bytearray) -> None:
    if buffer or sock.recv(1):
        raise RuntimeError("launcher response has trailing data")


def _read_chunked_body(sock: socket.socket, buffer: bytearray) -> bytes:
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
                    raise RuntimeError("launcher response trailers are too large")
                if not line:
                    break
                try:
                    text = line.decode("ascii")
                except UnicodeDecodeError as exc:
                    raise RuntimeError("launcher response trailers are invalid") from exc
                _parse_header_line(text, trailers)
                if text.partition(":")[0].lower() in {"content-length", "transfer-encoding"}:
                    raise RuntimeError("launcher response trailers are invalid")
            _reject_trailing_data(sock, buffer)
            return bytes(body)
        if size > MAX_TOKEN_BYTES - len(body):
            raise RuntimeError("launcher token is too large")
        body.extend(_read_exact(sock, buffer, size))
        if _read_exact(sock, buffer, 2) != b"\r\n":
            raise RuntimeError("launcher chunk data terminator is invalid")
        chunk_count += 1
        if chunk_count > MAX_TOKEN_BYTES:
            raise RuntimeError("launcher response has too many chunks")


def _read_response(sock: socket.socket) -> bytes:
    data = bytearray()
    marker = b"\r\n\r\n"
    while marker not in data:
        _receive(sock, data)
        end = data.find(marker)
        if end >= 0:
            if end + len(marker) > MAX_RESPONSE_HEADERS_BYTES:
                raise RuntimeError("launcher response headers are too large")
            break
        if len(data) > MAX_RESPONSE_HEADERS_BYTES:
            raise RuntimeError("launcher response headers are too large")
    end = data.index(marker)
    if end + len(marker) > MAX_RESPONSE_HEADERS_BYTES:
        raise RuntimeError("launcher response headers are too large")
    try:
        header = bytes(data[:end]).decode("ascii")
    except UnicodeDecodeError as exc:
        raise RuntimeError("launcher response headers are invalid") from exc
    lines = header.split("\r\n")
    if not lines or not lines[0].startswith("HTTP/1.1 "):
        raise RuntimeError("launcher_response_status_invalid")
    status_parts = lines[0].split()
    if len(status_parts) < 2 or status_parts[1] != "200":
        code = status_parts[1] if len(status_parts) > 1 and status_parts[1].isdigit() else "unknown"
        raise RuntimeError("launcher_response_status_" + code)
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
            raise RuntimeError("launcher_header_transfer_encoding_" + detail)
        body = _read_chunked_body(sock, buffer)
    else:
        content_length = headers.get("content-length")
        if content_length is None or not content_length.isdecimal():
            raise RuntimeError("launcher response length is invalid")
        length = int(content_length)
        if length > MAX_TOKEN_BYTES:
            raise RuntimeError("launcher token is too large")
        body = _read_exact(sock, buffer, length)
        _reject_trailing_data(sock, buffer)
    if content_type not in {"application/json", "application/jwt", "text/html"}:
        value = headers.get("content-type", "missing").lower().replace("/", "_").replace(";", "_")[:48]
        raise RuntimeError("launcher_header_content_type_%s_status_%s_body_sha256_%s_len_%d" % (value, status_code, hashlib.sha256(body).hexdigest(), len(body)))
    return body


def fetch_token(*, audience: str, nonce: str) -> str:
    body = json.dumps(
        {"audience": audience, "token_type": "OIDC", "nonces": [nonce]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    request = (
        b"POST " + TOKEN_PATH.encode("ascii") + b" HTTP/1.1\r\nHost: localhost\r\n"
        b"Content-Type: application/json\r\nAccept: application/json\r\nContent-Length: " + str(len(body)).encode("ascii")
        + b"\r\nConnection: close\r\n\r\n" + body
    )
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(5)
        sock.connect(LAUNCHER_SOCKET)
        sock.sendall(request)
        raw = _read_response(sock)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("launcher token unavailable") from exc
    finally:
        sock.close()
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        try:
            token = raw.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise RuntimeError("launcher_response_not_token") from exc
        if len(token.encode("ascii")) > MAX_TOKEN_BYTES or token.count(".") != 2 or not all(token.split(".")):
            raise RuntimeError("launcher_response_not_token")
        return token
    if not isinstance(result, dict) or set(result) != {"token"} or not isinstance(result.get("token"), str) or not result["token"]:
        raise RuntimeError("launcher_response_token_schema")
    token = result["token"]
    if len(token.encode("utf-8")) > MAX_TOKEN_BYTES:
        raise RuntimeError("launcher token is too large")
    return token


def verify_jwt(token: str, *, audience: str, issuer: str, nonce: str) -> dict:
    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
        claims = dict(
            id_token.verify_token(
                token,
                requests.Request(),
                audience=audience,
                certs_url=CONFIDENTIAL_SPACE_JWKS_URI,
            )
        )
    except Exception as exc:
        raise RuntimeError("launcher JWT signature verification failed") from exc
    if claims.get("iss") != issuer or claims.get("aud") != audience:
        raise RuntimeError("launcher JWT issuer or audience mismatch")
    if claims.get("eat_nonce") != nonce:
        raise RuntimeError("launcher JWT nonce mismatch")
    if type(claims.get("exp")) is not int or claims["exp"] <= int(time.time()):
        raise RuntimeError("launcher JWT expired")
    return claims


def nested(value: object, path: tuple[str, ...]) -> object:
    for part in path:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _validate_wip_provider(provider: str) -> None:
    if not re.fullmatch(
        r"//iam\.googleapis\.com/projects/[0-9]+/locations/global/"
        r"workloadIdentityPools/[a-z0-9-]+/providers/[a-z0-9-]+",
        provider,
    ):
        raise RuntimeError("STS WIP provider is invalid")


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("STS redirect rejected")


def exchange_sts(*, subject_token: str, provider: str) -> dict[str, object]:
    """Exchange the verified attestation JWT and return only non-secret evidence."""
    _validate_wip_provider(provider)
    payload = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": provider,
            "scope": "https://www.googleapis.com/auth/cloud-platform",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "subject_token": subject_token,
        }
    ).encode("ascii")
    request = urllib.request.Request(
        STS_ENDPOINT,
        data=payload,
        headers={"content-type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=10) as response:
            raw = response.read(MAX_STS_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"STS exchange HTTP {exc.code}") from exc
    except Exception as exc:
        raise RuntimeError("STS exchange failed") from exc
    if len(raw) > MAX_STS_RESPONSE_BYTES:
        raise RuntimeError("STS response is too large")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("STS response is invalid") from exc
    token = result.get("access_token") if isinstance(result, dict) else None
    expires_in = result.get("expires_in") if isinstance(result, dict) else None
    if (
        not isinstance(token, str)
        or not token
        or not isinstance(result, dict)
        or result.get("token_type") != "Bearer"
        or type(expires_in) is not int
        or expires_in <= 60
    ):
        raise RuntimeError("STS returned an invalid short-lived token")
    return {
        "status": "exchanged",
        "expires_in": expires_in,
        "token_digest": "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest(),
    }


def main() -> None:
    expected_digest = os.environ.get("CS_EXPECTED_IMAGE_DIGEST")
    audience = os.environ.get("CS_ATTESTATION_AUDIENCE", DEFAULT_WIP_TOKEN_AUDIENCE)
    issuer = os.environ.get("CS_ATTESTATION_ISSUER")
    if not expected_digest or not issuer:
        raise RuntimeError("expected image digest, audience, and issuer are required")
    nonce = _nonce()
    token = fetch_token(audience=audience, nonce=nonce)
    claims = verify_jwt(token, audience=audience, issuer=issuer, nonce=nonce)
    submods = claims.get("submods")
    actual_digest = nested(claims, ("submods", "container", "image_digest"))
    if actual_digest != expected_digest:
        raise RuntimeError("image digest mismatch")
    sts_evidence = None
    provider = os.environ.get("CS_WIP_PROVIDER")
    if provider:
        sts_evidence = exchange_sts(subject_token=token, provider=provider)
    selected = {
        "issuer": _bounded_public(claims.get("iss")),
        "audience": _bounded_public(claims.get("aud")),
        "subject": _bounded_public(claims.get("sub")),
        "swname": _bounded_public(claims.get("swname")),
        "swversion": _bounded_public(claims.get("swversion")),
        "dbgstat": _bounded_public(claims.get("dbgstat")),
        "hwmodel": _bounded_public(claims.get("hwmodel")),
        "secboot": _bounded_public(claims.get("secboot")),
        "workload": _bounded_public(nested(claims, ("submods", "container", "env", "P5R0_EXPECTED_WORKLOAD"))),
        "submods_keys": _bounded_keys(submods),
        "image_digest": _bounded_public(actual_digest),
        "project_number": _bounded_public(nested(claims, ("submods", "gce", "project_number"))),
        "project_id": _bounded_public(nested(claims, ("submods", "gce", "project_id"))),
        "zone": _bounded_public(nested(claims, ("submods", "gce", "zone"))),
        "support_attributes": _bounded_strings(nested(claims, ("submods", "confidential_space", "support_attributes"))),
        "token_digest": "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest(),
        "expected_image_match": True,
    }
    result = {"schema": "CSAttestationProbeV1", "claims": selected}
    if sts_evidence is not None:
        result["sts"] = sts_evidence
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"))
    if len(payload.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        raise RuntimeError("probe evidence exceeds bounded output")
    print(payload, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"schema": "CSAttestationProbeV1", "error": type(exc).__name__, "reason": str(exc)[:96]}, sort_keys=True), flush=True)
        raise
