"""Deployment entrypoint for the independent production timing bridge.

This is the only bridge module that obtains ambient Google ADC.  The adapter
and WSGI modules remain import-safe and require explicit clients/credentials.
The module-level application stays behind a generic 503 lock when startup
configuration, dependency imports, ADC, or production construction fails.

The FreeTSA CA is public trust material, not a build input: it must be mounted
at ``P5R0_BRIDGE_FREETSA_CA_PEM_PATH`` and its configured SHA-256 pin must
match the bytes read during startup.
"""

from __future__ import annotations

from hashlib import sha256
import hmac
import os
import re
from typing import Any, Callable, Mapping

from .auth import GoogleOIDCVerifier
from .timing_bridge_app import _LockedApplication
from .timing_bridge_production import (
    ProductionBridgeRuntime,
    create_production_bridge,
)


OIDC_AUDIENCE_ENV = "P5R0_BRIDGE_OIDC_AUDIENCE"
ALLOWED_EVALUATOR_SUBJECT_ENV = "P5R0_BRIDGE_ALLOWED_EVALUATOR_SUBJECT"
_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_HTTPS_AUDIENCE_RE = re.compile(r"^https://[^\s/?#]+(?:/[^\s?#]*)?$")

# Only these values are copied into the production factory.  In particular,
# no arbitrary environment value or credential material is passed through.
_BRIDGE_CONFIG_ENV = (
    "P5R0_BRIDGE_AUTHORITY_JSON",
    "P5R0_BRIDGE_LEDGER_ID",
    "P5R0_BRIDGE_KMS_KEY_VERSION",
    "P5R0_BRIDGE_BUCKET",
    "P5R0_BRIDGE_PREFIX",
    "P5R0_BRIDGE_FREETSA_CA_PEM_PATH",
    "P5R0_BRIDGE_FREETSA_CA_PEM_SHA256",
    "P5R0_BRIDGE_FREETSA_CERTIFICATE_SHA256",
    "P5R0_BRIDGE_FREETSA_TIMEOUT_SECONDS",
    # If present, the production factory rejects reuse of the evaluator key.
    "P5R0_KMS_KEY_VERSION",
    OIDC_AUDIENCE_ENV,
    ALLOWED_EVALUATOR_SUBJECT_ENV,
)


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} is required")
    return value


def _explicit_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = os.environ if source is None else source
    return {name: values[name] for name in _BRIDGE_CONFIG_ENV if name in values}


def _verify_ca_pin(env: Mapping[str, str]) -> None:
    """Verify the mounted CA bytes before acquiring cloud credentials."""
    path = _required(env, "P5R0_BRIDGE_FREETSA_CA_PEM_PATH")
    configured = _required(env, "P5R0_BRIDGE_FREETSA_CA_PEM_SHA256")
    if not _DIGEST_RE.fullmatch(configured):
        raise ValueError("FreeTSA CA digest is invalid")
    try:
        with open(path, "rb") as handle:
            material = handle.read()
    except Exception as exc:
        raise ValueError("FreeTSA CA PEM could not be loaded") from exc
    actual = "sha256:" + sha256(material).hexdigest()
    if not hmac.compare_digest(actual, configured):
        raise ValueError("FreeTSA CA PEM digest mismatch")


def _oidc_authenticator(env: Mapping[str, str]) -> Callable[[dict[str, Any]], Any]:
    audience = _required(env, OIDC_AUDIENCE_ENV)
    subject = _required(env, ALLOWED_EVALUATOR_SUBJECT_ENV)
    if not _HTTPS_AUDIENCE_RE.fullmatch(audience):
        raise ValueError("bridge OIDC audience must be an HTTPS URL")
    if any(char.isspace() or ord(char) < 0x20 or ord(char) == 0x7F for char in subject):
        raise ValueError("allowed evaluator subject is invalid")
    verifier = GoogleOIDCVerifier(audience, {subject})

    def authenticate(headers: dict[str, Any]) -> Any:
        # timing_bridge_app normalizes WSGI headers.  Do not accept the
        # nonstandard X-P5 header for Google OIDC authentication.
        return verifier.verify(headers.get("authorization"))

    return authenticate


def _bootstrap(
    env: Mapping[str, str] | None = None,
    *,
    adc_loader: Callable[..., tuple[Any, Any]] | None = None,
) -> ProductionBridgeRuntime:
    """Construct the bridge in the active worker process only."""
    values = _explicit_environment(env)
    _verify_ca_pin(values)
    authenticator = _oidc_authenticator(values)

    if adc_loader is None:
        # Keep cloud imports and ADC out of the locked adapter import path.
        from google.auth import default as adc_loader

    credentials, _project = adc_loader(scopes=[_CLOUD_PLATFORM_SCOPE])
    if credentials is None:
        raise RuntimeError("Google ADC did not return credentials")
    return create_production_bridge(
        env=values,
        credentials=credentials,
        authenticator=authenticator,
    )


# Gunicorn imports this object.  A failed import/configuration never exposes
# a partially constructed or unauthenticated service; it remains generic 503.
application: Callable[..., list[bytes]] = _LockedApplication()
try:
    application = _bootstrap().application
except Exception:
    # Deliberately do not log exception text: it may contain paths, provider
    # details, or credential/configuration material.
    pass


__all__ = [
    "ALLOWED_EVALUATOR_SUBJECT_ENV",
    "OIDC_AUDIENCE_ENV",
    "application",
]
