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

try:
    from services.cs_attestation_probe import launcher_protocol
except ImportError:  # The minimal probe image copies this module beside probe.py.
    import launcher_protocol

LAUNCHER_SOCKET = launcher_protocol.LAUNCHER_SOCKET
TOKEN_PATH = launcher_protocol.TOKEN_PATH
MAX_TOKEN_BYTES = launcher_protocol.MAX_TOKEN_BYTES
MAX_RESPONSE_HEADERS_BYTES = launcher_protocol.MAX_RESPONSE_HEADERS_BYTES
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


def _read_response(sock: object) -> bytes:
    try:
        return launcher_protocol.read_response(sock)
    except launcher_protocol.LauncherProtocolError as exc:
        raise RuntimeError(str(exc)) from exc


def fetch_token(*, audience: str, nonce: str) -> str:
    try:
        return launcher_protocol.fetch_token(
            audience=audience,
            nonce=nonce,
            socket_factory=socket.socket,
        )
    except launcher_protocol.LauncherProtocolError as exc:
        raise RuntimeError(str(exc)) from exc
    except Exception as exc:
        raise RuntimeError("launcher token unavailable") from exc


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
