"""Evaluator-side Cloud IAM authentication for the timing bridge.

The evaluator receives a short-lived federated access token only after the
Confidential Space attestation gate and STS exchange.  This module contains
separate fixed IAM Credentials exchanges: `generateAccessToken` for the
committed evaluator capability service account and `generateIdToken` for the
reviewed timing bridge account.  It never uses ambient credentials, follows
redirects, or emits token material in errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .canonical import canonical_bytes

IAM_CREDENTIALS_ENDPOINT = "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts"
MAX_ID_TOKEN_RESPONSE_BYTES = 16 * 1024
MAX_ACCESS_TOKEN_RESPONSE_BYTES = 16 * 1024
MAX_ACCESS_TOKEN_LIFETIME_SECONDS = 3600
_SERVICE_ACCOUNT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{5,127}@[a-z][a-z0-9-]{4,29}\.iam\.gserviceaccount\.com$")


class IAMCredentialsError(ValueError):
    """The fixed IAM Credentials exchange failed closed."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        raise IAMCredentialsError("IAM Credentials redirects are forbidden")


def _federated_token_is_valid(token: Any, clock: Callable[[], int]) -> bool:
    # Import locally to keep the locked evaluator import path free of cloud
    # dependencies and to avoid accepting arbitrary lookalike dictionaries.
    from .confidential_space import FederatedAccessToken

    return (
        isinstance(token, FederatedAccessToken)
        and token.token_type == "Bearer"
        and isinstance(token.access_token, str)
        and bool(token.access_token)
        and isinstance(token.expires_at, int)
        and token.expires_at > clock() + 30
    )


@dataclass(frozen=True)
class IAMCredentialsIDTokenFactory:
    """Mint a bridge-bound ID token with one verified federated token.

    ``credentials`` is intentionally the post-attestation
    :class:`FederatedAccessToken`; no service-account key or ambient ADC is
    accepted by this factory.  The endpoint is a fixed Google API resource and
    is not configurable by callers.
    """

    service_account: str
    audience: str
    credentials: Any = field(repr=False, compare=False)
    timeout_seconds: float = 5.0
    max_response_bytes: int = MAX_ID_TOKEN_RESPONSE_BYTES
    opener: Any | None = field(default=None, repr=False, compare=False)
    clock: Callable[[], int] = field(default=lambda: __import__("time").time(), repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.service_account, str) or not _SERVICE_ACCOUNT_RE.fullmatch(self.service_account):
            raise IAMCredentialsError("bridge service account is invalid")
        if not isinstance(self.audience, str) or not self.audience.startswith("https://") or any(char in self.audience for char in "\r\n"):
            raise IAMCredentialsError("bridge audience must be HTTPS")
        if not 0 < len(self.audience) <= 2048 or "?" in self.audience or "#" in self.audience:
            raise IAMCredentialsError("bridge audience must not contain query or fragment")
        if not _federated_token_is_valid(self.credentials, self.clock):
            raise IAMCredentialsError("verified federated access token is required")
        if not isinstance(self.timeout_seconds, (int, float)) or not 0 < self.timeout_seconds <= 10:
            raise IAMCredentialsError("IAM Credentials timeout")
        if type(self.max_response_bytes) is not int or not 0 < self.max_response_bytes <= MAX_ID_TOKEN_RESPONSE_BYTES:
            raise IAMCredentialsError("IAM Credentials response bound")
        if self.opener is None:
            object.__setattr__(self, "opener", build_opener(_NoRedirect()))

    @property
    def endpoint(self) -> str:
        return f"{IAM_CREDENTIALS_ENDPOINT}/{quote(self.service_account, safe='@')}:generateIdToken"

    def __call__(self) -> str:
        if not _federated_token_is_valid(self.credentials, self.clock):
            raise IAMCredentialsError("federated access token expired")
        body = canonical_bytes({"audience": self.audience, "includeEmail": True})
        request = Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.credentials.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            response = self.opener.open(request, timeout=self.timeout_seconds)
            if getattr(response, "status", 200) != 200:
                raise IAMCredentialsError("IAM Credentials HTTP status")
            geturl = getattr(response, "geturl", None)
            if callable(geturl) and geturl() != self.endpoint:
                raise IAMCredentialsError("IAM Credentials redirect")
            headers = getattr(response, "headers", None)
            content_type = headers.get("Content-Type") if headers is not None else None
            if not isinstance(content_type, str) or content_type.lower().split(";", 1)[0].strip() != "application/json":
                raise IAMCredentialsError("IAM Credentials content type")
            raw = response.read(self.max_response_bytes + 1)
            if not isinstance(raw, bytes) or len(raw) > self.max_response_bytes:
                raise IAMCredentialsError("IAM Credentials response too large")
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_pairs)
            if not isinstance(value, dict) or set(value) != {"token"} or not isinstance(value["token"], str) or not value["token"]:
                raise IAMCredentialsError("IAM Credentials response schema")
            if any(ord(char) < 0x20 or ord(char) == 0x7f for char in value["token"]):
                raise IAMCredentialsError("IAM Credentials token is invalid")
            return value["token"]
        except IAMCredentialsError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, UnicodeError) as exc:
            raise IAMCredentialsError("IAM Credentials request failed") from exc
        except Exception as exc:
            raise IAMCredentialsError("IAM Credentials request failed") from exc

    def authorization_header(self) -> str:
        """Return the short-lived header for ``TimingBridgeConfig`` injection."""
        return f"Bearer {self()}"


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IAMCredentialsError("IAM Credentials response schema")
        result[key] = value
    return result


class IAMCredentialsAccessTokenFactory:
    """Mint a short-lived access token for one reviewed evaluator account."""

    def __init__(self, service_account: str, credentials: Any, *, timeout_seconds: float = 5.0,
                 max_response_bytes: int = MAX_ACCESS_TOKEN_RESPONSE_BYTES,
                 opener: Any | None = None, clock: Callable[[], int] | None = None):
        if not isinstance(service_account, str) or not _SERVICE_ACCOUNT_RE.fullmatch(service_account):
            raise IAMCredentialsError("target service account is invalid")
        if not _federated_token_is_valid(credentials, clock or (lambda: int(__import__("time").time()))):
            raise IAMCredentialsError("verified federated access token is required")
        if not isinstance(timeout_seconds, (int, float)) or not 0 < timeout_seconds <= 10:
            raise IAMCredentialsError("IAM Credentials timeout")
        if type(max_response_bytes) is not int or not 0 < max_response_bytes <= MAX_ACCESS_TOKEN_RESPONSE_BYTES:
            raise IAMCredentialsError("IAM Credentials response bound")
        self.service_account = service_account
        self.credentials = credentials
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.opener = opener or build_opener(_NoRedirect())
        self.clock = clock or (lambda: int(__import__("time").time()))

    @property
    def endpoint(self) -> str:
        return f"{IAM_CREDENTIALS_ENDPOINT}/{quote(self.service_account, safe='@')}:generateAccessToken"

    def __call__(self):
        from .confidential_space import FederatedAccessToken

        if not _federated_token_is_valid(self.credentials, self.clock):
            raise IAMCredentialsError("federated access token expired")
        now = int(self.clock())
        remaining = self.credentials.expires_at - now
        # IAM Credentials must not mint a token that outlives the federated
        # source token.  STS commonly returns 3598s rather than a full hour;
        # requesting a fixed 3600s would therefore make the later expiry
        # check fail even when IAM authorization is correct.
        lifetime_seconds = min(MAX_ACCESS_TOKEN_LIFETIME_SECONDS, remaining - 30)
        if lifetime_seconds <= 30:
            raise IAMCredentialsError("federated access token is too close to expiry")
        body = canonical_bytes({
            "lifetime": f"{lifetime_seconds}s",
            "scope": ["https://www.googleapis.com/auth/cloud-platform"],
        })
        request = Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.credentials.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            response = self.opener.open(request, timeout=self.timeout_seconds)
            if getattr(response, "status", 200) != 200:
                raise IAMCredentialsError("IAM Credentials HTTP status")
            geturl = getattr(response, "geturl", None)
            if callable(geturl) and geturl() != self.endpoint:
                raise IAMCredentialsError("IAM Credentials redirect")
            headers = getattr(response, "headers", None)
            content_type = headers.get("Content-Type") if headers is not None else None
            if not isinstance(content_type, str) or content_type.lower().split(";", 1)[0].strip() != "application/json":
                raise IAMCredentialsError("IAM Credentials content type")
            raw = response.read(self.max_response_bytes + 1)
            if not isinstance(raw, bytes) or len(raw) > self.max_response_bytes:
                raise IAMCredentialsError("IAM Credentials response too large")
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_pairs)
            if not isinstance(value, dict) or set(value) != {"accessToken", "expireTime"}:
                raise IAMCredentialsError("IAM Credentials response schema")
            access_token = value["accessToken"]
            expire_time = value["expireTime"]
            if not isinstance(access_token, str) or not access_token or any(ord(char) < 0x20 or ord(char) == 0x7f for char in access_token):
                raise IAMCredentialsError("IAM Credentials access token is invalid")
            if not isinstance(expire_time, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", expire_time) is None:
                raise IAMCredentialsError("IAM Credentials expiry is invalid")
            expires_at = int(datetime.fromisoformat(expire_time.replace("Z", "+00:00")).timestamp())
            now = int(self.clock())
            if expires_at <= now + 30 or expires_at > self.credentials.expires_at or expires_at > now + MAX_ACCESS_TOKEN_LIFETIME_SECONDS:
                raise IAMCredentialsError("IAM Credentials expiry is outside the allowed lifetime")
            return FederatedAccessToken(access_token, expires_at, "Bearer")
        except IAMCredentialsError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, UnicodeError, OverflowError) as exc:
            raise IAMCredentialsError("IAM Credentials request failed") from exc
        except Exception as exc:
            raise IAMCredentialsError("IAM Credentials request failed") from exc

    mint = __call__

EvaluatorIAMCredentialsIDTokenFactory = IAMCredentialsIDTokenFactory
EvaluatorIAMCredentialsAccessTokenFactory = IAMCredentialsAccessTokenFactory

__all__ = [
    "IAM_CREDENTIALS_ENDPOINT",
    "MAX_ID_TOKEN_RESPONSE_BYTES",
    "MAX_ACCESS_TOKEN_RESPONSE_BYTES",
    "MAX_ACCESS_TOKEN_LIFETIME_SECONDS",
    "IAMCredentialsError",
    "IAMCredentialsIDTokenFactory",
    "IAMCredentialsAccessTokenFactory",
    "EvaluatorIAMCredentialsIDTokenFactory",
    "EvaluatorIAMCredentialsAccessTokenFactory",
]
