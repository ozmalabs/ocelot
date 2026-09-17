from __future__ import annotations

"""Confidential Space bootstrap and capability boundary.

This module deliberately keeps the process in a locked state until a verified
Confidential Space token has been exchanged for a short-lived federated token.
No ambient ADC, service-account key, private key, GCS object, or KMS client is
created by the locked path.
"""

import json
import os
import re
import secrets
import copy
import socket
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, replace as dataclass_replace
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol

from .attestation_binding import (
    AttestationBindingError,
    VerifiedAttestationBinding,
    _build_verified_attestation_binding,
)
from .auth import GoogleOIDCVerifier
from .canonical import canonical_bytes, digest, parse_canonical
from .interfaces import ObjectStore, Signer
from .service import EvaluatorService
from .signing import KMSEd25519Signer, sign_object
from .store import GCSStore
from .timing import ExternallyKeyedTimingAttestor, TimingAttestor, TimingAuthorityConfig


CONFIDENTIAL_SPACE_LAUNCHER_SOCKET = "/run/container_launcher/teeserver.sock"
CONFIDENTIAL_SPACE_TOKEN_PATH = "/v1/token"
# These limits apply before any token, claims, or capability material can enter
# the process. Evidence is intentionally much smaller than the request limit.
MAX_METADATA_TOKEN_BYTES = 64 * 1024
MAX_LAUNCHER_HEADERS_BYTES = 8 * 1024
MAX_STS_RESPONSE_BYTES = 64 * 1024
MAX_STARTUP_EVIDENCE_BYTES = 16 * 1024
DEFAULT_WIP_TOKEN_AUDIENCE = "https://sts.googleapis.com"
DEFAULT_ATTESTATION_ISSUER = "https://confidentialcomputing.googleapis.com"
CONFIDENTIAL_SPACE_JWKS_URI = "https://www.googleapis.com/service_accounts/v1/metadata/jwk/signer@confidentialspace-sign.iam.gserviceaccount.com"
_WIP_PROVIDER_PREFIX = "//iam.googleapis.com/projects/"
_AUTHORITY_FIELDS = {"schema", "authority_id", "key_id", "public_key", "public_key_digest", "transport_attestation"}
_TRANSPORT_FIELDS = {"schema", "provider", "audience", "event"}
_CLAIM_KEYS = {"audience", "nonce", "issued_at", "expires_at", "issuer", "subject", "image_digest", "project_number", "project_id", "zone", "debug_state", "tee", "hardware_model", "secure_boot", "workload"}
MIN_NONCE_BYTES = 10
MAX_NONCE_BYTES = 74


def _wip_policy_contract(*, provider: str, token_audience: str, claim_paths: Mapping[str, str], issuer: str,
                         image_digest: str, project_number: str, project_id: str,
                         zone: str, debug_state: str, tee: str, hardware_model: str,
                         secure_boot: bool, workload: str) -> dict[str, Any]:
    """Single-source WIP mapping/condition commitment used by runtime and deploy."""
    mapped = {
        "google.subject": f"assertion.{claim_paths['subject']}",
        "attribute.image_digest": f"assertion.{claim_paths['image_digest']}",
        "attribute.project_number": f"assertion.{claim_paths['project_number']}",
        "attribute.project_id": f"assertion.{claim_paths['project_id']}",
        "attribute.zone": f"assertion.{claim_paths['zone']}",
        "attribute.debug_state": f"assertion.{claim_paths['debug_state']}",
        "attribute.tee": f"assertion.{claim_paths['tee']}",
        "attribute.hardware_model": f"assertion.{claim_paths['hardware_model']}",
        "attribute.secure_boot": f"assertion.{claim_paths['secure_boot']}",
        "attribute.workload": f"assertion.{claim_paths['workload']}",
    }
    condition = {
        "audience": f"assertion.{claim_paths['audience']}",
        "audience_value": token_audience,
        "issuer": issuer,
        "image_digest": image_digest,
        "project_number": project_number,
        "project_id": project_id,
        "zone": zone,
        "debug_state": debug_state,
        "tee": tee,
        "hardware_model": hardware_model,
        "secure_boot": secure_boot,
        "workload": workload,
    }
    return {"schema": "P5R0WIPPolicyV2", "provider": provider, "token_audience": token_audience, "mapping": mapped, "condition": condition}


class _FrozenDict(dict):
    """Dict-compatible immutable value used in canonical policy objects."""
    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("immutable policy")
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _immutable
    __ior__ = _immutable


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return _FrozenDict({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


class ConfidentialSpaceError(RuntimeError):
    """Base class for locked bootstrap and capability errors."""


class AttestationError(ConfidentialSpaceError):
    pass


class STSError(ConfidentialSpaceError):
    pass


@dataclass(frozen=True)
class LockedBootstrapConfig:
    """Non-secret policy. It is safe to parse before attestation."""

    authority: dict[str, Any]
    caller_audience: str
    allowed_subjects: frozenset[str]
    attestation_audience: str
    wip_provider: str
    project_number: str
    project_id: str
    zone: str
    image_digest: str
    debug_state: str
    tee: str
    secure_boot: bool
    bucket: str
    prefix: str
    kms_key_version: str
    runtime_digest: str
    resource_profile_digest: str
    base_image_digest: str = ""
    service_name: str = ""
    region: str = ""
    cpu_limit: str = "1"
    memory_limit: str = "512Mi"
    expected_issuer: str | None = DEFAULT_ATTESTATION_ISSUER
    workload: str = "evaluator"
    hardware_model: str = "GCP_AMD_SEV"
    claim_paths: Mapping[str, str] = field(default_factory=lambda: {
        "audience": "aud",
        "nonce": "eat_nonce",
        "issued_at": "iat",
        "expires_at": "exp",
        "issuer": "iss",
        "subject": "sub",
        "image_digest": "submods.container.image_digest",
        "project_number": "submods.gce.project_number",
        "project_id": "submods.gce.project_id",
        "zone": "submods.gce.zone",
        "debug_state": "dbgstat",
        "tee": "swname",
        "hardware_model": "hwmodel",
        "secure_boot": "secboot",
        "workload": "submods.container.env.P5R0_EXPECTED_WORKLOAD",
    })
    clock: Callable[[], int] = field(default=lambda: int(time.time()))
    timing_authority_id: str | None = None
    timing_key_id: str | None = None
    timing_ledger_id: str | None = None
    timing_public_key_digest: str | None = None
    nonce_factory: Callable[[], str] = secrets.token_urlsafe

    def __post_init__(self) -> None:
        if not isinstance(self.attestation_audience, str) or not self.attestation_audience.startswith("https://"):
            raise ValueError("WIP token audience must be an HTTPS audience")
        if self.attestation_audience == self.wip_provider:
            raise ValueError("WIP token audience must not be the provider resource")
        if self.expected_issuer != DEFAULT_ATTESTATION_ISSUER:
            raise ValueError("Confidential Space issuer must be the Google Cloud Attestation issuer")
        object.__setattr__(self, "authority", _freeze(dict(self.authority)))
        object.__setattr__(self, "claim_paths", _freeze(dict(self.claim_paths)))
        object.__setattr__(self, "allowed_subjects", frozenset(self.allowed_subjects))

    @staticmethod
    def _digest(value: str, name: str) -> str:
        if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
            raise ValueError(f"{name} must be a sha256 digest")
        if any(c not in "0123456789abcdef" for c in value[7:]):
            raise ValueError(f"{name} must be a sha256 digest")
        return value

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "LockedBootstrapConfig":
        values = dict(os.environ if env is None else env)

        def required(name: str) -> str:
            value = values.get(name, "")
            if not value:
                raise RuntimeError(f"{name} is required")
            return value

        try:
            authority = parse_canonical(required("P5R0_AUTHORITY_JSON"))
        except Exception as exc:
            raise RuntimeError("P5R0_AUTHORITY_JSON must be canonical JSON") from exc
        # This is a locked, public-only contract. Reject unknown fields before
        # metadata, STS, GCS, or KMS can be touched.
        if set(authority) != _AUTHORITY_FIELDS or authority.get("schema") != "P5R0PublicAuthorityV4":
            raise RuntimeError("P5R0_EXPECTED_IMAGE_DIGEST or closed authority metadata is required")
        transport = authority.get("transport_attestation")
        if not isinstance(transport, dict) or set(transport) != _TRANSPORT_FIELDS or transport.get("schema") != "P5R0AuthorityTransportV1":
            raise RuntimeError("P5R0_AUTHORITY_JSON transport metadata must be closed")
        if any(not isinstance(authority.get(key), str) or not authority[key] for key in ("authority_id", "key_id", "public_key", "public_key_digest")):
            raise RuntimeError("P5R0_AUTHORITY_JSON public metadata is invalid")
        try:
            public_key = __import__("base64").urlsafe_b64decode(authority["public_key"] + "=" * (-len(authority["public_key"]) % 4))
        except Exception as exc:
            raise RuntimeError("P5R0_AUTHORITY_JSON public key is invalid") from exc
        if not isinstance(authority["public_key"], str) or __import__("base64").urlsafe_b64encode(public_key).rstrip(b"=").decode("ascii") != authority["public_key"] or len(public_key) != 32 or authority["public_key_digest"] != digest(authority["public_key"]):
            raise RuntimeError("P5R0_AUTHORITY_JSON public key binding is invalid")
        provider = transport.get("provider")
        if any(not isinstance(transport.get(key), str) or not transport[key] for key in ("provider", "audience", "event")):
            raise RuntimeError("P5R0_AUTHORITY_JSON transport metadata is invalid")
        subjects = frozenset(x for x in required("P5R0_ALLOWED_SUBJECTS").split(",") if x)
        if not subjects:
            raise RuntimeError("P5R0_ALLOWED_SUBJECTS is required")
        image_digest = values.get("P5R0_EXPECTED_IMAGE_DIGEST", "")
        runtime_digest = values.get("P5R0_RUNTIME_DIGEST", "")
        resource_digest = values.get("P5R0_RESOURCE_PROFILE_DIGEST", "")
        for name, item in (("P5R0_EXPECTED_IMAGE_DIGEST", image_digest), ("P5R0_RUNTIME_DIGEST", runtime_digest), ("P5R0_RESOURCE_PROFILE_DIGEST", resource_digest)):
            try:
                cls._digest(item, name)
            except ValueError as exc:
                raise RuntimeError(str(exc)) from exc
        secure_boot = values.get("P5R0_EXPECTED_SECURE_BOOT", "true").lower()
        if secure_boot not in {"true", "false"}:
            raise RuntimeError("P5R0_EXPECTED_SECURE_BOOT must be true or false")
        base_image_digest = required("P5R0_BASE_IMAGE_DIGEST")
        try:
            cls._digest(base_image_digest, "P5R0_BASE_IMAGE_DIGEST")
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        service_name = required("P5R0_SERVICE_NAME")
        region = required("P5R0_REGION")
        cpu_limit = required("P5R0_CPU_LIMIT")
        memory_limit = required("P5R0_MEMORY_LIMIT")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", service_name) or not re.fullmatch(r"[a-z][a-z0-9-]+", region):
            raise RuntimeError("runtime service placement is invalid")
        if not re.fullmatch(r"[0-9]+(?:m)?", cpu_limit) or not re.fullmatch(r"[0-9]+(?:Mi|Gi)", memory_limit):
            raise RuntimeError("runtime resource limits are invalid")
        claim_paths: dict[str, str] = {
            "audience": values.get("P5R0_CLAIM_AUDIENCE", "aud"),
            "nonce": values.get("P5R0_CLAIM_NONCE", "eat_nonce"),
            "issued_at": values.get("P5R0_CLAIM_ISSUED_AT", "iat"),
            "expires_at": values.get("P5R0_CLAIM_EXPIRES_AT", "exp"),
            "issuer": values.get("P5R0_CLAIM_ISSUER", "iss"),
            "subject": values.get("P5R0_CLAIM_SUBJECT", "sub"),
            "image_digest": values.get("P5R0_CLAIM_IMAGE_DIGEST", "submods.container.image_digest"),
            "project_number": values.get("P5R0_CLAIM_PROJECT_NUMBER", "submods.gce.project_number"),
            "project_id": values.get("P5R0_CLAIM_PROJECT_ID", "submods.gce.project_id"),
            "zone": values.get("P5R0_CLAIM_ZONE", "submods.gce.zone"),
            "debug_state": values.get("P5R0_CLAIM_DEBUG_STATE", "dbgstat"),
            "tee": values.get("P5R0_CLAIM_TEE", "swname"),
            "hardware_model": values.get("P5R0_CLAIM_HARDWARE_MODEL", "hwmodel"),
            "secure_boot": values.get("P5R0_CLAIM_SECURE_BOOT", "secboot"),
            "workload": values.get("P5R0_CLAIM_WORKLOAD", "submods.container.env.P5R0_EXPECTED_WORKLOAD"),
        }
        if set(claim_paths) != _CLAIM_KEYS or any(not isinstance(path, str) or not path or any(part == "" for part in path.split(".")) or "\\" in path for path in claim_paths.values()):
            raise RuntimeError("attestation claim paths must be a closed non-empty dotted mapping")
        if "P5R0_METADATA_TOKEN_URL" in values:
            raise RuntimeError("legacy metadata token URL configuration is forbidden")
        expected_project_number = required("P5R0_EXPECTED_PROJECT_NUMBER")
        expected_project_id = required("P5R0_EXPECTED_PROJECT_ID")
        expected_zone = required("P5R0_EXPECTED_ZONE")
        bucket = required("P5R0_BUCKET")
        prefix = values.get("P5R0_PREFIX", "v3")
        kms_key_version = required("P5R0_KMS_KEY_VERSION")
        if not re.fullmatch(r"[0-9]+", expected_project_number):
            raise RuntimeError("expected project number is invalid")
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", expected_project_id) or not re.fullmatch(r"[a-z][a-z0-9-]+", expected_zone):
            raise RuntimeError("expected project or zone is invalid")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]", bucket):
            raise RuntimeError("bucket is invalid")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", prefix) or ".." in prefix.split("/"):
            raise RuntimeError("prefix is invalid")
        if not re.fullmatch(r"projects/[a-z][a-z0-9-]*/locations/[a-z0-9-]+/keyRings/[A-Za-z0-9_-]+/cryptoKeys/[A-Za-z0-9_-]+/cryptoKeyVersions/[1-9][0-9]*", kms_key_version):
            raise RuntimeError("KMS key version is invalid")
        attestation_audience = values.get("P5R0_ATTESTATION_AUDIENCE", DEFAULT_WIP_TOKEN_AUDIENCE)
        wip_provider = required("P5R0_WIP_PROVIDER")
        provider_match = re.fullmatch(r"//iam\.googleapis\.com/projects/([0-9]+)/locations/global/workloadIdentityPools/([a-z0-9-]+)/providers/([a-z0-9-]+)", wip_provider)
        if provider_match is None or provider_match.group(1) != expected_project_number:
            raise RuntimeError("WIP provider must be the canonical WIP provider resource")
        if not re.fullmatch(r"https://[^\s]+", attestation_audience) or attestation_audience == wip_provider:
            raise RuntimeError("WIP token audience must be a separate HTTPS audience, not the provider resource")
        if transport["provider"] != wip_provider or transport["audience"] != attestation_audience:
            raise RuntimeError("authority transport must bind provider and token audience separately")
        timing_values = [values.get("P5R0_TIMING_AUTHORITY_ID", ""), values.get("P5R0_TIMING_KEY_ID", ""), values.get("P5R0_TIMING_LEDGER_ID", ""), values.get("P5R0_TIMING_PUBLIC_KEY_DIGEST", "")]
        if not all(timing_values):
            raise RuntimeError("independent timing authority configuration is required")
        cls._digest(timing_values[3], "P5R0_TIMING_PUBLIC_KEY_DIGEST")
        expected_issuer = values.get("P5R0_ATTESTATION_ISSUER", DEFAULT_ATTESTATION_ISSUER)
        if expected_issuer != DEFAULT_ATTESTATION_ISSUER:
            raise RuntimeError("P5R0_ATTESTATION_ISSUER must be the Google Cloud Attestation issuer")
        parsed = cls(
            authority=authority,
            caller_audience=required("P5R0_AUDIENCE"),
            allowed_subjects=subjects,
            attestation_audience=attestation_audience,
            wip_provider=wip_provider,
            project_number=expected_project_number,
            project_id=expected_project_id,
            zone=expected_zone,
            image_digest=image_digest,
            debug_state=values.get("P5R0_EXPECTED_DEBUG_STATE", "disabled-since-boot"),
            tee=values.get("P5R0_EXPECTED_TEE", "CONFIDENTIAL_SPACE"),
            hardware_model=values.get("P5R0_EXPECTED_HARDWARE_MODEL", "GCP_AMD_SEV"),
            secure_boot=secure_boot == "true",
            bucket=bucket,
            prefix=prefix,
            kms_key_version=kms_key_version,
            runtime_digest=runtime_digest,
            resource_profile_digest=resource_digest,
            base_image_digest=base_image_digest,
            service_name=service_name,
            region=region,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            expected_issuer=expected_issuer,
            workload=values.get("P5R0_EXPECTED_WORKLOAD", "evaluator"),
            claim_paths=claim_paths,
            timing_authority_id=timing_values[0] or None,
            timing_key_id=timing_values[1] or None,
            timing_ledger_id=timing_values[2] or None,
            timing_public_key_digest=timing_values[3] or None,
        )
        for name, actual in (("P5R0_POLICY_DIGEST", parsed.policy_digest),
                             ("P5R0_CLAIM_PATHS_DIGEST", parsed.claim_paths_digest),
                             ("P5R0_ATTESTATION_CLAIMS_DIGEST", parsed.attestation_claims_digest),
                             ("P5R0_WIP_POLICY_DIGEST", parsed.wip_policy_digest)):
            supplied = values.get(name, "")
            if not supplied:
                raise RuntimeError(f"{name} is required")
            try:
                cls._digest(supplied, name)
            except ValueError as exc:
                raise RuntimeError(str(exc)) from exc
            if supplied != actual:
                raise RuntimeError(f"{name} does not match immutable policy")
        return parsed

    @property
    def claim_paths_digest(self) -> str:
        return digest(dict(self.claim_paths))

    @property
    def attestation_claims_digest(self) -> str:
        return digest({
            "schema": "P5R0AttestationClaimsV2", "claim_paths": dict(self.claim_paths),
            "token_audience": self.attestation_audience, "issuer": self.expected_issuer,
            "image_digest": self.image_digest, "project_number": self.project_number,
            "project_id": self.project_id, "zone": self.zone,
            "debug_state": self.debug_state, "tee": self.tee,
            "hardware_model": self.hardware_model,
            "secure_boot": self.secure_boot, "workload": self.workload,
        })

    @property
    def wip_policy_digest(self) -> str:
        return digest(_wip_policy_contract(
            provider=self.wip_provider, token_audience=self.attestation_audience, claim_paths=self.claim_paths,
            issuer=self.expected_issuer or "", image_digest=self.image_digest,
            project_number=self.project_number, project_id=self.project_id,
            zone=self.zone, debug_state=self.debug_state, tee=self.tee,
            hardware_model=self.hardware_model, secure_boot=self.secure_boot, workload=self.workload,
        ))

    @property
    def policy_digest(self) -> str:
        """Digest of non-secret policy, useful for audit output."""
        value = {
            "schema": "P5R0ConfidentialSpacePolicyV3",
            "authority": dict(self.authority),
            "wip": {
                "provider": self.wip_provider,
                "token_audience": self.attestation_audience,
                "caller_audience": self.caller_audience,
            },
            "allowed_subjects": sorted(self.allowed_subjects),
            "expected_issuer": self.expected_issuer,
            "wip_provider": self.wip_provider,
            "project_number": self.project_number,
            "project_id": self.project_id,
            "zone": self.zone,
            "image_digest": self.image_digest,
            "debug_state": self.debug_state,
            "tee": self.tee,
            "hardware_model": self.hardware_model,
            "workload": self.workload,
            "secure_boot": self.secure_boot,
            "bucket": self.bucket,
            "prefix": self.prefix,
            "kms_key_version": self.kms_key_version,
            "runtime_digest": self.runtime_digest,
            "resource_profile_digest": self.resource_profile_digest,
            "deployment": {
                "base_image_digest": self.base_image_digest,
                "service_name": self.service_name,
                "region": self.region,
                "resources": {"cpu": self.cpu_limit, "memory": self.memory_limit},
            },
            "claim_paths": dict(self.claim_paths),
            "timing_authority_id": self.timing_authority_id,
            "timing_key_id": self.timing_key_id,
            "timing_ledger_id": self.timing_ledger_id,
            "timing_public_key_digest": self.timing_public_key_digest,
            "claim_paths_digest": self.claim_paths_digest,
            "attestation_claims_digest": self.attestation_claims_digest,
            "wip_policy_digest": self.wip_policy_digest,
        }
        return digest(value)


class AttestationSource(Protocol):
    def fetch(self, *, audience: str, nonce: str) -> str: ...


class AttestationVerifier(Protocol):
    def verify(self, token: str, *, audience: str) -> Mapping[str, Any]: ...


class STSClient(Protocol):
    def exchange(self, *, subject_token: str, audience: str, provider: str) -> "FederatedAccessToken": ...


@dataclass(frozen=True)
class FederatedAccessToken:
    access_token: str
    expires_at: int
    token_type: str = "Bearer"


@dataclass(frozen=True)
class VerifiedAttestation:
    claims: dict[str, Any]
    nonce: str
    subject_token: str


class LauncherTokenSource:
    """Fetches an OIDC attestation token only through the launcher Unix socket."""

    def __init__(self, socket_path: str = CONFIDENTIAL_SPACE_LAUNCHER_SOCKET, *, socket_factory: Callable[..., Any] | None = None):
        if socket_path != CONFIDENTIAL_SPACE_LAUNCHER_SOCKET:
            raise AttestationError("Confidential Space launcher socket is immutable")
        self.socket_path = CONFIDENTIAL_SPACE_LAUNCHER_SOCKET
        self.socket_factory = socket_factory or socket.socket

    def fetch(self, *, audience: str, nonce: str) -> str:
        _validate_nonce(nonce)
        body = canonical_bytes({"audience": audience, "token_type": "OIDC", "nonces": [nonce]})
        request = (
            b"POST " + CONFIDENTIAL_SPACE_TOKEN_PATH.encode("ascii") + b" HTTP/1.1\r\n"
            b"Host: localhost\r\nContent-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n"
            b"Connection: close\r\n\r\n" + body
        )
        sock = self.socket_factory(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(5)
            sock.connect(self.socket_path)
            sock.sendall(request)
            raw = _read_launcher_response(sock)
        except AttestationError:
            raise
        except Exception as exc:
            raise AttestationError("Confidential Space launcher token unavailable") from exc
        finally:
            try:
                sock.close()
            except Exception:
                pass
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AttestationError("Confidential Space launcher response is invalid") from exc
        if not isinstance(result, dict) or set(result) != {"token"} or not isinstance(result.get("token"), str) or not result["token"]:
            raise AttestationError("Confidential Space launcher response has invalid schema")
        token = result["token"]
        if len(token.encode("utf-8")) > MAX_METADATA_TOKEN_BYTES:
            raise AttestationError("Confidential Space launcher token is too large")
        return token


def _validate_nonce(nonce: str) -> None:
    if not isinstance(nonce, str) or not nonce:
        raise AttestationError("attestation nonce is invalid")
    try:
        size = len(nonce.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise AttestationError("attestation nonce is invalid") from exc
    if not MIN_NONCE_BYTES <= size <= MAX_NONCE_BYTES:
        raise AttestationError("attestation nonce length is outside 10-74 bytes")


def _read_launcher_response(sock: Any) -> bytes:
    data = bytearray()
    separator = b"\r\n\r\n"
    while separator not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise AttestationError("Confidential Space launcher response ended early")
        data.extend(chunk)
        if len(data) > MAX_LAUNCHER_HEADERS_BYTES:
            raise AttestationError("Confidential Space launcher headers are too large")
    header_end = data.index(separator)
    header = bytes(data[:header_end]).decode("ascii", errors="strict")
    lines = header.split("\r\n")
    if not lines or lines[0] != "HTTP/1.1 200 OK":
        raise AttestationError("Confidential Space launcher returned an unexpected status")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        name, separator_text, value = line.partition(":")
        if not separator_text or name.lower() in fields:
            raise AttestationError("Confidential Space launcher response headers are invalid")
        fields[name.lower()] = value.strip()
    if fields.get("transfer-encoding") or fields.get("content-type", "").split(";", 1)[0].lower() != "application/json":
        raise AttestationError("Confidential Space launcher response headers are invalid")
    try:
        length = int(fields["content-length"])
    except (KeyError, ValueError) as exc:
        raise AttestationError("Confidential Space launcher response length is invalid") from exc
    if length < 0 or length > MAX_METADATA_TOKEN_BYTES:
        raise AttestationError("Confidential Space launcher response is too large")
    body = bytearray(data[header_end + 4:])
    while len(body) < length:
        chunk = sock.recv(min(4096, length - len(body)))
        if not chunk:
            raise AttestationError("Confidential Space launcher response ended early")
        body.extend(chunk)
    if len(body) != length:
        raise AttestationError("Confidential Space launcher response has trailing data")
    return bytes(body)


class GoogleJwtAttestationVerifier:
    """Verifies the JWT signature/standard claims before policy claims are used."""

    def verify(self, token: str, *, audience: str) -> Mapping[str, Any]:
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token
            return id_token.verify_token(
                token,
                requests.Request(),
                audience=audience,
                certs_url=CONFIDENTIAL_SPACE_JWKS_URI,
            )
        except Exception as exc:
            raise AttestationError("Confidential Space token signature verification failed") from exc


def _claim(claims: Mapping[str, Any], path: str) -> Any:
    value: Any = claims
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise AttestationError(f"attestation claim missing: {path}")
        value = value[part]
    return value


class AttestationGate:
    """The only owner of attestation, nonce, replay, and claim policy."""

    def __init__(self, config: LockedBootstrapConfig, source: AttestationSource, verifier: AttestationVerifier, *, clock: Callable[[], int] | None = None):
        self.config = config
        self.source = source
        self.verifier = verifier
        self.clock = clock or config.clock
        self._used_nonces: set[str] = set()

    def verify_startup(self) -> VerifiedAttestation:
        nonce = self.config.nonce_factory()
        _validate_nonce(nonce)
        if nonce in self._used_nonces:
            raise AttestationError("attestation nonce generation failed")
        self._used_nonces.add(nonce)
        token = self.source.fetch(audience=self.config.attestation_audience, nonce=nonce)
        claims = dict(self.verifier.verify(token, audience=self.config.attestation_audience))
        if not claims:
            raise AttestationError("empty verified attestation claims")
        audience = _claim(claims, self.config.claim_paths["audience"])
        if audience != self.config.attestation_audience and not (isinstance(audience, list) and audience == [self.config.attestation_audience]):
            raise AttestationError("attestation audience mismatch")
        now = self.clock()
        expires_at = _claim(claims, self.config.claim_paths["expires_at"])
        issued_at = _claim(claims, self.config.claim_paths["issued_at"])
        if type(expires_at) is not int or expires_at <= now:
            raise AttestationError("attestation expired")
        if type(issued_at) is not int or issued_at > now + 30 or expires_at - issued_at > 3600:
            raise AttestationError("attestation time claims are invalid")
        if _claim(claims, self.config.claim_paths["nonce"]) != nonce:
            raise AttestationError("attestation nonce mismatch")
        if self.config.expected_issuer is None or _claim(claims, self.config.claim_paths["issuer"]) != self.config.expected_issuer:
            raise AttestationError("attestation issuer mismatch")
        subject = _claim(claims, self.config.claim_paths["subject"])
        if not isinstance(subject, str) or subject not in self.config.allowed_subjects:
            raise AttestationError("attestation subject mismatch")
        expected = {
            "image_digest": self.config.image_digest,
            "project_number": self.config.project_number,
            "project_id": self.config.project_id,
            "zone": self.config.zone,
            "debug_state": self.config.debug_state,
            "tee": self.config.tee,
            "hardware_model": self.config.hardware_model,
            "workload": self.config.workload,
            "secure_boot": self.config.secure_boot,
        }
        for name, expected_value in expected.items():
            if _claim(claims, self.config.claim_paths[name]) != expected_value:
                raise AttestationError(f"attestation {name} mismatch")
        return VerifiedAttestation(claims=claims, nonce=nonce, subject_token=token)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str):
        raise STSError("STS redirect rejected")


class GoogleSTSClient:
    """Minimal RFC 8693 exchange; it never reads ADC or a service-account key."""

    endpoint = "https://sts.googleapis.com/v1/token"

    def __init__(self, *, endpoint: str = endpoint, opener: Callable[..., Any] | None = None, clock: Callable[[], int] | None = None):
        if endpoint != self.endpoint:
            raise STSError("STS endpoint is immutable")
        self.endpoint = self.endpoint
        self.opener = opener or urllib.request.build_opener(_NoRedirectHandler()).open
        self.clock = clock or (lambda: int(time.time()))

    def exchange(self, *, subject_token: str, audience: str, provider: str) -> FederatedAccessToken:
        if not isinstance(audience, str) or audience != provider or not audience.startswith("//iam.googleapis.com/"):
            raise STSError("STS audience must be the canonical WIP provider audience")
        payload = urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": audience,
            "scope": "https://www.googleapis.com/auth/cloud-platform",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "subject_token": subject_token,
        }).encode("ascii")
        request = urllib.request.Request(self.endpoint, data=payload, headers={"content-type": "application/x-www-form-urlencoded"}, method="POST")
        try:
            with self.opener(request, timeout=10) as response:
                raw = response.read(MAX_STS_RESPONSE_BYTES + 1)
                if not isinstance(raw, (bytes, bytearray)) or len(raw) > MAX_STS_RESPONSE_BYTES:
                    raise STSError("STS response is too large")
                result = json.loads(bytes(raw).decode("utf-8"))
        except STSError:
            raise
        except Exception as exc:
            raise STSError("attestation STS exchange failed") from exc
        token = result.get("access_token")
        expires_in = result.get("expires_in")
        if not isinstance(token, str) or not token or result.get("token_type") != "Bearer" or type(expires_in) is not int or expires_in <= 60:
            raise STSError("STS returned an invalid short-lived token")
        return FederatedAccessToken(token, self.clock() + expires_in, "Bearer")


class ScopedObjectStore(ObjectStore):
    """Bundle-read capability that can issue one run-bound child capability."""

    _read_prefixes = ("locks/", "manifests/", "truth/")

    def __init__(self, inner: ObjectStore):
        self.inner = inner
        self._legacy_run_id: str | None = None

    @staticmethod
    def _run_from_name(value: str) -> str | None:
        if not value.startswith("runs/"):
            return None
        parts = value.split("/")
        return parts[1] if len(parts) > 1 else None

    def _legacy_check(self, value: str) -> None:
        run_id = self._run_from_name(value)
        if run_id is None:
            raise ConfidentialSpaceError("run capability required for object access")
        if self._legacy_run_id is None:
            self._legacy_run_id = run_id
        if run_id != self._legacy_run_id:
            raise ConfidentialSpaceError("object is outside this run capability")

    @staticmethod
    def _safe(name: str) -> str:
        if not isinstance(name, str) or not name or name != name.strip("/") or "\\" in name:
            raise ConfidentialSpaceError("invalid object capability path")
        parts = name.split("/")
        if any(not part or part in {".", ".."} for part in parts):
            raise ConfidentialSpaceError("invalid object capability path")
        return name

    def bind_run(self, run_id: str) -> "RunScopedObjectStore":
        return RunScopedObjectStore(self.inner, run_id)

    def get(self, name: str):
        value = self._safe(name)
        if value.startswith(self._read_prefixes):
            if not re.fullmatch(r"(?:locks|manifests|truth)/sha256:[0-9a-f]{64}\.json", value):
                raise ConfidentialSpaceError("bundle path is not an immutable digest object")
            return self.inner.get(value)
        self._legacy_check(value)
        return self.inner.get(value)

    def create(self, name: str, data: bytes):
        value = self._safe(name)
        self._legacy_check(value)
        return self.inner.create(value, data)

    def replace(self, name: str, data: bytes, generation: int):
        value = self._safe(name)
        self._legacy_check(value)
        return self.inner.replace(value, data, generation)


class RunScopedObjectStore(ObjectStore):
    """A capability whose accepted names are confined to exactly one run."""

    def __init__(self, inner: ObjectStore, run_id: str):
        if not isinstance(run_id, str) or len(run_id) != 71 or not run_id.startswith("sha256:"):
            raise ConfidentialSpaceError("invalid run capability")
        self.inner = inner
        self.run_id = run_id
        self.prefix = f"runs/{run_id}/"

    def _safe(self, name: str) -> str:
        if not isinstance(name, str) or not name or name != name.strip("/") or "\\" in name:
            raise ConfidentialSpaceError("invalid run capability path")
        parts = name.split("/")
        if any(not part or part in {".", ".."} for part in parts):
            raise ConfidentialSpaceError("invalid run capability path")
        if not name.startswith(self.prefix):
            raise ConfidentialSpaceError("object is outside this run capability")
        suffix = name[len(self.prefix):]
        allowed = (
            suffix == "state.json" or suffix == "result.seal.json" or
            re.fullmatch(r"receipts/[0-9]{6}\.json", suffix) is not None or
            re.fullmatch(r"timing/[0-9]{6}-[A-Za-z0-9_-]+\.json", suffix) is not None or
            re.fullmatch(r"evidence/[0-9]{6}\.json", suffix) is not None or
            re.fullmatch(r"compute-class/observation-[0-9]{6}\.json", suffix) is not None or
            re.fullmatch(r"idempotency/[A-Za-z0-9_-]+-sha256:[0-9a-f]{64}\.json", suffix) is not None
        )
        if not allowed or not suffix.endswith(".json"):
            raise ConfidentialSpaceError("object is outside this run capability")
        return name

    def get(self, name: str):
        return self.inner.get(self._safe(name))

    def create(self, name: str, data: bytes):
        return self.inner.create(self._safe(name), data)

    def replace(self, name: str, data: bytes, generation: int):
        return self.inner.replace(self._safe(name), data, generation)


class SignedTimingAttestor:
    """Diagnostic-only local timing record; never an independent certification source."""

    independent = False

    def __init__(self, signer: Signer, *, clock: Callable[[], int] | None = None):
        self.signer = signer
        self.clock = clock or (lambda: int(time.time()))
        self.sequences: dict[str, int] = {}
        self._lock = threading.Lock()

    def record(self, *, run_id: str, task_id: str, event: str, payload_digest: str) -> dict[str, Any]:
        with self._lock:
            sequence = self.sequences.get(run_id, 0) + 1
            self.sequences[run_id] = sequence
        value = {
            "schema": "P5R0TimingAttestationV1",
            "run_id": run_id,
            "task_id": task_id,
            "event": event,
            "sequence": sequence,
            "seed_digest": digest({"run_id": run_id, "task_id": task_id, "sequence": sequence}),
            "payload_digest": payload_digest,
            "observed_at": datetime.fromtimestamp(self.clock(), tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "authority_id": self.signer.authority["authority_id"],
            "signature": "",
        }
        value["signature"] = sign_object(value, self.signer)
        return value


@dataclass(frozen=True)
class Capabilities:
    store: ObjectStore
    signer: Signer
    timing_attestor: TimingAttestor
    # Optional keeps local/custom capability fixtures source-compatible. The
    # locked adapter attaches a verified binding before its default service is
    # constructed.
    verified_attestation_binding: VerifiedAttestationBinding | None = None

    @property
    def attestation_binding(self) -> VerifiedAttestationBinding | None:
        return self.verified_attestation_binding

    @property
    def binding(self) -> VerifiedAttestationBinding | None:
        return self.verified_attestation_binding


class CapabilityFactory:
    """Creates cloud clients only from the token returned by STS."""

    def __init__(self, config: LockedBootstrapConfig, *, storage_client_factory: Callable[[FederatedAccessToken], Any] | None = None, kms_client_factory: Callable[[FederatedAccessToken], Any] | None = None, timing_attestor_factory: Callable[[FederatedAccessToken, LockedBootstrapConfig], TimingAttestor] | None = None, timing_recorder_factory: Callable[[FederatedAccessToken, LockedBootstrapConfig], Any] | None = None):
        self.config = config
        self.storage_client_factory = storage_client_factory
        self.kms_client_factory = kms_client_factory
        self.timing_attestor_factory = timing_attestor_factory
        self.timing_recorder_factory = timing_recorder_factory

    def _storage_client(self, credentials: FederatedAccessToken) -> Any:
        if self.storage_client_factory is not None:
            return self.storage_client_factory(credentials)
        from google.oauth2.credentials import Credentials
        from google.cloud import storage
        return storage.Client(credentials=Credentials(token=credentials.access_token, expiry=datetime.fromtimestamp(credentials.expires_at, tz=timezone.utc)))

    def _kms_client(self, credentials: FederatedAccessToken) -> Any:
        if self.kms_client_factory is not None:
            return self.kms_client_factory(credentials)
        from google.oauth2.credentials import Credentials
        from google.cloud import kms
        return kms.KeyManagementServiceClient(credentials=Credentials(token=credentials.access_token, expiry=datetime.fromtimestamp(credentials.expires_at, tz=timezone.utc)))

    def build(self, credentials: FederatedAccessToken) -> Capabilities:
        if not isinstance(credentials, FederatedAccessToken) or credentials.token_type != "Bearer" or not credentials.access_token:
            raise STSError("capabilities require a bearer federated access token")
        if credentials.expires_at <= int(time.time()) + 30:
            raise STSError("federated token is expired or too close to expiry")
        storage_client = self._storage_client(credentials)
        kms_client = self._kms_client(credentials)
        store = ScopedObjectStore(GCSStore(self.config.bucket, self.config.prefix, client=storage_client))
        signer = KMSEd25519Signer(self.config.kms_key_version, self.config.authority, client=kms_client)
        timing_values = (self.config.timing_authority_id, self.config.timing_key_id, self.config.timing_ledger_id, self.config.timing_public_key_digest)
        if any(timing_values):
            if not all(timing_values):
                raise STSError("independent timing authority configuration is incomplete")
            authority = TimingAuthorityConfig(
                authority_id=self.config.timing_authority_id or "",
                key_id=self.config.timing_key_id or "",
                ledger_id=self.config.timing_ledger_id or "",
                public_key_digest=self.config.timing_public_key_digest or "",
            )
            if self.timing_attestor_factory is not None:
                timing_attestor = self.timing_attestor_factory(credentials, self.config)
            elif self.timing_recorder_factory is not None:
                recorder = self.timing_recorder_factory(credentials, self.config)
                timing_attestor = ExternallyKeyedTimingAttestor(authority, recorder)
            else:
                raise STSError("independent timing authority is configured but no external recorder is wired")
            if not getattr(timing_attestor, "independent", False) or getattr(timing_attestor, "authority", None) != authority:
                raise STSError("configured timing recorder is not bound to the independent authority")
        else:
            # Direct in-memory fixtures may use the diagnostic V1 recorder.  The
            # locked environment parser requires all independent timing fields,
            # so this branch is not reachable by a production deployment.
            timing_attestor = SignedTimingAttestor(signer)
        return Capabilities(store=store, signer=signer, timing_attestor=timing_attestor)


class ConfidentialSpaceAdapter:
    """Locked façade around EvaluatorService; workers never receive capabilities."""

    def __init__(self, config: LockedBootstrapConfig, *, source: AttestationSource | None = None, verifier: AttestationVerifier | None = None, sts: STSClient | None = None, capability_factory: CapabilityFactory | None = None, timing_recorder_factory: Callable[[FederatedAccessToken, LockedBootstrapConfig], Any] | None = None, service_factory: Callable[[Capabilities], EvaluatorService] | None = None):
        self.config = config
        self.gate = AttestationGate(config, source or LauncherTokenSource(), verifier or GoogleJwtAttestationVerifier())
        self.sts = sts or GoogleSTSClient()
        self.capability_factory = capability_factory or CapabilityFactory(config, timing_recorder_factory=timing_recorder_factory)
        self.service_factory = service_factory or self._default_service
        self._service: EvaluatorService | None = None
        self._attestation_binding: VerifiedAttestationBinding | None = None
        self._expires_at: int | None = None
        self._lock = threading.Lock()
        self._startup_evidence = self._locked_startup_evidence()

    def _bounded_evidence(self, evidence: dict[str, Any]) -> dict[str, Any]:
        encoded = canonical_bytes(evidence)
        if len(encoded) > MAX_STARTUP_EVIDENCE_BYTES:
            raise ConfidentialSpaceError("startup attestation evidence exceeds bounded output")
        return evidence

    def _locked_startup_evidence(self, *, failure: str | None = None) -> dict[str, Any]:
        evidence: dict[str, Any] = {
            "schema": "P5R0StartupAttestationEvidenceV1",
            "status": "locked",
            "policy_digest": self.config.policy_digest,
            "claim_paths_digest": self.config.claim_paths_digest,
            "attestation_claims_digest": self.config.attestation_claims_digest,
            "wip_policy_digest": self.config.wip_policy_digest,
            "attestation": "not_verified",
            "federation": "not_exchanged",
            "capabilities": "not_constructed",
        }
        if failure is not None:
            evidence["last_failure"] = failure
        return self._bounded_evidence(evidence)

    @property
    def startup_evidence(self) -> dict[str, Any]:
        """Return non-secret evidence of the current bootstrap state.

        The raw metadata JWT, nonce, claims, and federated access token are
        never returned. Only their digests and the immutable policy bindings
        are exposed after successful activation.
        """
        return copy.deepcopy(self._startup_evidence)

    def _mark_bootstrap_failure(self, error: BaseException) -> None:
        # Error class names are deliberately less revealing than exception
        # messages, which may contain provider or transport details.
        self._startup_evidence = self._locked_startup_evidence(
            failure=type(error).__name__
        )

    def _attested_startup_evidence(self, attestation: VerifiedAttestation, token: FederatedAccessToken, binding: VerifiedAttestationBinding) -> dict[str, Any]:
        claims = attestation.claims
        return self._bounded_evidence({
            "schema": "P5R0StartupAttestationEvidenceV1",
            "status": "attested",
            "policy_digest": self.config.policy_digest,
            "claim_paths_digest": self.config.claim_paths_digest,
            "attestation_claims_digest": self.config.attestation_claims_digest,
            "wip_policy_digest": self.config.wip_policy_digest,
            "attestation": {
                "verified": True,
                "binding_digest": binding.binding_digest,
                "token_digest": digest(attestation.subject_token),
                "claims_digest": digest(claims),
                "nonce_digest": digest(attestation.nonce),
                "audience": self.config.attestation_audience,
                "issuer": self.config.expected_issuer,
                "issued_at": _claim(claims, self.config.claim_paths["issued_at"]),
                "expires_at": _claim(claims, self.config.claim_paths["expires_at"]),
                "fixed_claims": {
                    "image_digest": self.config.image_digest,
                    "project_number": self.config.project_number,
                    "project_id": self.config.project_id,
                    "zone": self.config.zone,
                    "debug_state": self.config.debug_state,
                    "tee": self.config.tee,
                    "hardware_model": self.config.hardware_model,
                    "secure_boot": self.config.secure_boot,
                    "workload": self.config.workload,
                },
            },
            "federation": {
                "exchanged": True,
                "provider": self.config.wip_provider,
                "access_token_digest": digest(token.access_token),
                "expires_at": token.expires_at,
            },
            "capabilities": "constructed_after_attestation",
        })

    @property
    def attestation_binding(self) -> VerifiedAttestationBinding | None:
        """The current redacted binding, retained only while activation is live."""
        self._expire_if_needed()
        return self._attestation_binding

    def _attach_attestation_binding(self, capabilities: Any, binding: VerifiedAttestationBinding) -> Any:
        """Preserve one-argument custom factories while threading the binding."""
        if isinstance(capabilities, Capabilities):
            return dataclass_replace(capabilities, verified_attestation_binding=binding)
        # Legacy test/application factories may return a small mutable object.
        # Attach only as a convenience; the service still validates the type.
        try:
            setattr(capabilities, "verified_attestation_binding", binding)
        except Exception:
            pass
        return capabilities

    def _default_service(self, capabilities: Capabilities) -> EvaluatorService:
        return EvaluatorService(
            store=capabilities.store,
            signer=capabilities.signer,
            verifier=GoogleOIDCVerifier(self.config.caller_audience, set(self.config.allowed_subjects)),
            timing_attestor=capabilities.timing_attestor,
            image_digest=self.config.image_digest,
            runtime_digest=self.config.runtime_digest,
            resource_profile_digest=self.config.resource_profile_digest,
            timing_authority_id=self.config.timing_authority_id,
            timing_key_id=self.config.timing_key_id,
            timing_ledger_id=self.config.timing_ledger_id,
            timing_public_key_digest=self.config.timing_public_key_digest,
            policy_digest=self.config.policy_digest,
            claim_paths_digest=self.config.claim_paths_digest,
            attestation_claims_digest=self.config.attestation_claims_digest,
            wip_policy_digest=self.config.wip_policy_digest,
            wip_provider=self.config.wip_provider,
            verified_attestation_binding=capabilities.verified_attestation_binding,
        )

    def _expire_if_needed(self) -> None:
        if self._service is not None and self._expires_at is not None and self.config.clock() >= self._expires_at:
            self._service = None
            self._attestation_binding = None
            self._expires_at = None
            self._startup_evidence = self._locked_startup_evidence(failure="FederatedAccessTokenExpired")

    @property
    def attested(self) -> bool:
        self._expire_if_needed()
        return self._service is not None

    def activate_attested_service(self) -> EvaluatorService:
        self._expire_if_needed()
        if self._service is not None:
            return self._service
        with self._lock:
            if self._service is not None:
                return self._service
            try:
                attestation = self.gate.verify_startup()
                token = self.sts.exchange(subject_token=attestation.subject_token, audience=self.config.wip_provider, provider=self.config.wip_provider)
                binding = _build_verified_attestation_binding(attestation, token, self.config)
                capabilities = self._attach_attestation_binding(self.capability_factory.build(token), binding)
                service = self.service_factory(capabilities)
            except Exception as exc:
                self._mark_bootstrap_failure(exc)
                raise
            evidence = self._attested_startup_evidence(attestation, token, binding)
            self._expires_at = token.expires_at
            self._attestation_binding = binding
            self._service = service
            self._startup_evidence = evidence
            return service

    def _health_payload(self) -> dict[str, Any]:
        evidence = self.startup_evidence
        return {
            "schema": "P5R0HealthV1",
            "status": "attested" if self.attested else "locked",
            "policy_digest": self.config.policy_digest,
            "startup_evidence_digest": digest(evidence),
        }

    def dispatch(self, method: str, path: str, raw_body: bytes, headers: dict[str, str]):
        if method == "GET" and path == "/healthz":
            return 200, {"content-type": "application/json", "cache-control": "no-store"}, canonical_bytes(self._health_payload())
        if method == "GET" and path == "/startup-attestation":
            return 200, {"content-type": "application/json", "cache-control": "no-store"}, canonical_bytes(self.startup_evidence)
        try:
            active_service = self.activate_attested_service()
        except ConfidentialSpaceError as exc:
            self._mark_bootstrap_failure(exc)
            return 503, {"content-type": "application/json", "cache-control": "no-store"}, canonical_bytes({"schema": "P5R0ErrorV1", "error": "attestation bootstrap failed; locked"})
        except Exception:
            self._mark_bootstrap_failure(RuntimeError("bootstrap"))
            return 503, {"content-type": "application/json", "cache-control": "no-store"}, canonical_bytes({"schema": "P5R0ErrorV1", "error": "attestation bootstrap failed; locked"})
        try:
            return active_service.dispatch(method, path, raw_body, headers)
        except Exception:
            return 503, {"content-type": "application/json", "cache-control": "no-store"}, canonical_bytes({"schema": "P5R0ErrorV1", "error": "service request failed closed"})


def create_locked_bootstrap(env: Mapping[str, str] | None = None, **kwargs: Any) -> ConfidentialSpaceAdapter:
    """Parse only non-secret policy and return a service with no cloud clients."""
    return ConfidentialSpaceAdapter(LockedBootstrapConfig.from_env(env), **kwargs)


def activate_attested_service(bootstrap: ConfidentialSpaceAdapter) -> EvaluatorService:
    """Explicit activation hook for tests/entrypoints; activation is fail-closed."""
    return bootstrap.activate_attested_service()
