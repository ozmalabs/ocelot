"""Production adapters for the independently operated FreeTSA bridge.

This module is deployment wiring only.  It does not provision Cloud Run, IAM,
GCS, or KMS resources.  Construction is fail-closed and requires explicit
clients/credentials, reviewed public authority metadata, a private GCS
bucket/prefix, and a pinned FreeTSA trust configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Any, Callable, Mapping

from .canonical import canonical_bytes, digest, parse_canonical
from .rfc3161 import (
    FREETSA_ENDPOINT,
    FREETSA_POLICY_OID,
    RFC3161Config,
    RFC3161TimingEvidenceAdapter,
)
from .signing import KMSEd25519Signer, KMSConfigurationError
from .timing import TimingAuthorityConfig
from .timing_bridge_app import create_application
from .timing_bridge_service import (
    BRIDGE_RESPONSE_SCHEMA,
    TimingBridgeLedger,
    TimingBridgeService,
    TimingBridgeServiceError,
    TimingLedgerEntry,
    TimingLedgerHead,
)


_BRIDGE_KEY_VERSION_RE = re.compile(
    r"^projects/[a-z][a-z0-9-]*/locations/[a-z0-9-]+/keyRings/[A-Za-z0-9_-]+/"
    r"cryptoKeys/[A-Za-z0-9_-]+/cryptoKeyVersions/[1-9][0-9]*$"
)
_BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_LEDGER_SCHEMA = "P5R0TimingBridgeLedgerV1"


class TimingBridgeProductionError(ValueError):
    """Production bridge configuration or adapter construction failed."""


def _required(values: Mapping[str, str], name: str) -> str:
    value = values.get(name, "")
    if not isinstance(value, str) or not value:
        raise TimingBridgeProductionError(f"{name} is required")
    return value


def _validate_digest(value: str, name: str) -> None:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise TimingBridgeProductionError(f"{name} is invalid")


def _validate_prefix(prefix: str) -> str:
    if not isinstance(prefix, str) or not prefix or prefix.startswith("/") or prefix.endswith("/"):
        raise TimingBridgeProductionError("bridge ledger prefix is invalid")
    parts = prefix.split("/")
    if any(not part or part in {".", ".."} for part in parts) or any(not re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in parts):
        raise TimingBridgeProductionError("bridge ledger prefix is invalid")
    return prefix


def _validate_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not run_id or len(run_id) > 256:
        raise TimingBridgeServiceError("timing run identifier is invalid")
    if run_id in {".", ".."} or "/" in run_id or "\\" in run_id or any(ord(char) < 0x20 for char in run_id):
        raise TimingBridgeServiceError("timing run identifier is invalid")
    return run_id


def _not_found(error: BaseException) -> bool:
    code = getattr(error, "code", None)
    if callable(code):
        try:
            code = code()
        except Exception:
            code = None
    status = getattr(error, "status_code", None)
    return code == 404 or status == 404 or type(error).__name__ == "NotFound"


class GCSDurableTimingBridgeLedger:
    """Generation-conditional ledger stored under one exact object per run.

    Object names are always ``{prefix}/runs/{run_id}/timing-bridge/ledger.json``.
    The complete small index is replaced with ``if_generation_match``; a
    missing object is created with generation ``0``.  Thus concurrent bridge
    workers cannot both commit the same head, and no list/delete capability is
    needed.  The object contains only request/record digests and public IDs.
    """

    durable = True
    non_production = False

    def __init__(self, bucket: str, prefix: str, *, client: Any):
        if not isinstance(bucket, str) or not _BUCKET_RE.fullmatch(bucket):
            raise TimingBridgeProductionError("bridge GCS bucket is invalid")
        if client is None:
            raise TimingBridgeProductionError("explicit bridge GCS client is required")
        self.bucket_name = bucket
        self.prefix = _validate_prefix(prefix)
        try:
            self._bucket = client.bucket(bucket)
        except Exception as exc:
            raise TimingBridgeProductionError("bridge GCS bucket is unavailable") from exc

    def object_name(self, run_id: str) -> str:
        return f"{self.prefix}/runs/{_validate_run_id(run_id)}/timing-bridge/ledger.json"

    @staticmethod
    def _entry(value: Any) -> TimingLedgerEntry:
        fields = {"request_digest", "record_digest", "sequence", "task_id", "event"}
        if not isinstance(value, dict) or set(value) != fields:
            raise TimingBridgeServiceError("timing ledger entry schema")
        if not all(isinstance(value.get(key), str) and value[key] for key in ("request_digest", "record_digest", "task_id", "event")):
            raise TimingBridgeServiceError("timing ledger entry metadata")
        if not _DIGEST_RE.fullmatch(value["request_digest"]) or not _DIGEST_RE.fullmatch(value["record_digest"]):
            raise TimingBridgeServiceError("timing ledger entry digest")
        if type(value["sequence"]) is not int or value["sequence"] < 1:
            raise TimingBridgeServiceError("timing ledger entry sequence")
        if value["event"] not in {"task_issued", "result_received"}:
            raise TimingBridgeServiceError("timing ledger entry event")
        return TimingLedgerEntry(
            value["request_digest"], value["record_digest"], value["sequence"], value["task_id"], value["event"]
        )

    def _read(self, run_id: str) -> tuple[list[TimingLedgerEntry], int | None]:
        blob = self._bucket.blob(self.object_name(run_id))
        try:
            blob.reload()
            generation = int(blob.generation)
            value = parse_canonical(blob.download_as_bytes())
        except Exception as exc:
            if _not_found(exc):
                return [], None
            raise TimingBridgeServiceError("timing ledger read failed") from exc
        if set(value) != {"schema", "run_id", "entries"} or value.get("schema") != _LEDGER_SCHEMA or value.get("run_id") != run_id or not isinstance(value.get("entries"), list):
            raise TimingBridgeServiceError("timing ledger schema")
        entries = [self._entry(item) for item in value["entries"]]
        for expected, entry in enumerate(entries, 1):
            if entry.sequence != expected:
                raise TimingBridgeServiceError("timing ledger sequence")
        return entries, generation

    def head(self, run_id: str) -> TimingLedgerHead:
        entries, _ = self._read(run_id)
        if not entries:
            return TimingLedgerHead(0, None)
        return TimingLedgerHead(entries[-1].sequence, entries[-1].record_digest)

    def find_request(self, run_id: str, request_digest: str) -> TimingLedgerEntry | None:
        entries, _ = self._read(run_id)
        return next((entry for entry in entries if entry.request_digest == request_digest), None)

    def find_event(self, run_id: str, task_id: str, event: str) -> TimingLedgerEntry | None:
        entries, _ = self._read(run_id)
        return next((entry for entry in entries if entry.task_id == task_id and entry.event == event), None)

    def append(
        self,
        run_id: str,
        *,
        request_digest: str,
        record_digest: str,
        sequence: int,
        previous_digest: str | None,
        task_id: str,
        event: str,
    ) -> None:
        entries, generation = self._read(run_id)
        expected_previous = entries[-1].record_digest if entries else None
        if sequence != len(entries) + 1 or previous_digest != expected_previous:
            raise TimingBridgeServiceError("timing ledger sequence conflict")
        if any(entry.request_digest == request_digest for entry in entries):
            raise TimingBridgeServiceError("timing ledger replay")
        if any(entry.task_id == task_id and entry.event == event for entry in entries):
            raise TimingBridgeServiceError("timing ledger event conflict")
        entry = TimingLedgerEntry(request_digest, record_digest, sequence, task_id, event)
        value = {
            "schema": _LEDGER_SCHEMA,
            "run_id": run_id,
            "entries": [
                {
                    "request_digest": item.request_digest,
                    "record_digest": item.record_digest,
                    "sequence": item.sequence,
                    "task_id": item.task_id,
                    "event": item.event,
                }
                for item in (*entries, entry)
            ],
        }
        blob = self._bucket.blob(self.object_name(run_id))
        try:
            blob.upload_from_string(
                canonical_bytes(value),
                content_type="application/json",
                if_generation_match=0 if generation is None else generation,
            )
        except Exception as exc:
            # A precondition failure is intentionally exposed only as a generic
            # conflict; provider text must never reach the bridge response.
            raise TimingBridgeServiceError("timing ledger generation conflict") from exc


class BridgeKMSEd25519Signer(KMSEd25519Signer):
    """Bridge-owned Ed25519 KMS signer with no private-key export path."""

    def __init__(self, key_version: str, authority: dict[str, Any], *, credentials: Any | None = None, client: Any | None = None):
        if not isinstance(key_version, str) or not _BRIDGE_KEY_VERSION_RE.fullmatch(key_version):
            raise KMSConfigurationError("bridge KMS key version is invalid")
        if credentials is not None and client is not None:
            raise KMSConfigurationError("bridge KMS client supplied twice")
        if client is None:
            if credentials is None:
                raise KMSConfigurationError("explicit bridge KMS credentials are required")
            try:
                from google.cloud import kms
                client = kms.KeyManagementServiceClient(credentials=credentials)
            except Exception as exc:
                raise KMSConfigurationError("bridge KMS client construction failed") from exc
        super().__init__(key_version, authority, client=client)


@dataclass(frozen=True)
class BridgeProductionConfig:
    authority_metadata: dict[str, Any]
    authority: TimingAuthorityConfig
    kms_key_version: str
    bucket: str
    prefix: str
    rfc3161_config: RFC3161Config

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "BridgeProductionConfig":
        values = dict(os.environ if env is None else env)
        raw_authority = _required(values, "P5R0_BRIDGE_AUTHORITY_JSON")
        try:
            authority = parse_canonical(raw_authority)
        except Exception as exc:
            raise TimingBridgeProductionError("P5R0_BRIDGE_AUTHORITY_JSON must be canonical JSON") from exc
        if set(authority) != {"schema", "authority_id", "key_id", "public_key", "public_key_digest", "transport_attestation"} or authority.get("schema") not in {"P5R0AuthorityV3", "P5R0PublicAuthorityV4"}:
            raise TimingBridgeProductionError("bridge authority metadata is not closed")
        transport = authority.get("transport_attestation")
        if not isinstance(transport, dict) or set(transport) != {"schema", "provider", "audience", "event"} or transport.get("schema") != "P5R0AuthorityTransportV1" or any(not isinstance(transport.get(key), str) or not transport[key] for key in ("provider", "audience", "event")):
            raise TimingBridgeProductionError("bridge authority transport metadata is invalid")
        _validate_digest(authority.get("public_key_digest"), "bridge public key digest")
        if digest(authority.get("public_key")) != authority.get("public_key_digest"):
            raise TimingBridgeProductionError("bridge public key binding is invalid")
        ledger_id = _required(values, "P5R0_BRIDGE_LEDGER_ID")
        timing_authority = TimingAuthorityConfig(
            authority_id=authority["authority_id"],
            key_id=authority["key_id"],
            ledger_id=ledger_id,
            public_key_digest=authority["public_key_digest"],
        )
        key_version = _required(values, "P5R0_BRIDGE_KMS_KEY_VERSION")
        if values.get("P5R0_KMS_KEY_VERSION") and values.get("P5R0_KMS_KEY_VERSION") == key_version:
            raise TimingBridgeProductionError("bridge KMS key must be separate from evaluator KMS key")
        if not _BRIDGE_KEY_VERSION_RE.fullmatch(key_version):
            raise TimingBridgeProductionError("P5R0_BRIDGE_KMS_KEY_VERSION is invalid")
        bucket = _required(values, "P5R0_BRIDGE_BUCKET")
        if not _BUCKET_RE.fullmatch(bucket):
            raise TimingBridgeProductionError("P5R0_BRIDGE_BUCKET is invalid")
        prefix = _validate_prefix(_required(values, "P5R0_BRIDGE_PREFIX"))
        ca_path = _required(values, "P5R0_BRIDGE_FREETSA_CA_PEM_PATH")
        try:
            with open(ca_path, "rb") as handle:
                ca_pem = handle.read()
        except Exception as exc:
            raise TimingBridgeProductionError("FreeTSA CA PEM could not be loaded") from exc
        ca_pin = _required(values, "P5R0_BRIDGE_FREETSA_CA_PEM_SHA256")
        cert_pin = _required(values, "P5R0_BRIDGE_FREETSA_CERTIFICATE_SHA256")
        try:
            rfc_config = RFC3161Config(
                endpoint=FREETSA_ENDPOINT,
                tsa_ca_pem=ca_pem,
                tsa_ca_pem_sha256=ca_pin,
                tsa_certificate_sha256=cert_pin,
                policy_oid=FREETSA_POLICY_OID,
                timeout_seconds=float(values.get("P5R0_BRIDGE_FREETSA_TIMEOUT_SECONDS", "5")),
            )
        except Exception as exc:
            raise TimingBridgeProductionError("FreeTSA pinned configuration is invalid") from exc
        return cls(authority, timing_authority, key_version, bucket, prefix, rfc_config)


@dataclass(frozen=True)
class ProductionBridgeRuntime:
    config: BridgeProductionConfig
    ledger: GCSDurableTimingBridgeLedger
    signer: BridgeKMSEd25519Signer
    adapter: RFC3161TimingEvidenceAdapter
    service: TimingBridgeService
    application: Callable[..., list[bytes]]


def create_production_bridge(
    *,
    env: Mapping[str, str] | None = None,
    credentials: Any | None = None,
    gcs_client: Any | None = None,
    kms_client: Any | None = None,
    authenticator: Callable[[dict[str, Any]], Any] | None = None,
    rfc_opener: Any | None = None,
    rfc_verifier: Callable[[bytes, RFC3161Config], str] | None = None,
    rfc_clock: Callable[[], float] | None = None,
) -> ProductionBridgeRuntime:
    """Build the production bridge only after every reviewed input is present."""
    if not callable(authenticator):
        raise TimingBridgeProductionError("bridge authenticator is required")
    config = BridgeProductionConfig.from_env(env)
    if gcs_client is None:
        if credentials is None:
            raise TimingBridgeProductionError("explicit bridge GCS credentials are required")
        try:
            from google.cloud import storage
            gcs_client = storage.Client(credentials=credentials)
        except Exception as exc:
            raise TimingBridgeProductionError("bridge GCS client construction failed") from exc
    ledger = GCSDurableTimingBridgeLedger(config.bucket, config.prefix, client=gcs_client)
    signer = BridgeKMSEd25519Signer(config.kms_key_version, config.authority_metadata, credentials=credentials, client=kms_client)
    adapter = RFC3161TimingEvidenceAdapter(
        config.rfc3161_config, opener=rfc_opener, verifier=rfc_verifier, clock=rfc_clock
    )
    service = TimingBridgeService(
        adapter=adapter,
        authority=config.authority,
        signer=signer,
        ledger=ledger,
        production_ready=True,
    )
    application = create_application(service, authenticator)
    return ProductionBridgeRuntime(config, ledger, signer, adapter, service, application)


def create_production_bridge_app(**kwargs: Any) -> Callable[..., list[bytes]]:
    """Return only the WSGI app for Gunicorn/framework entrypoints."""
    return create_production_bridge(**kwargs).application


__all__ = [
    "BridgeProductionConfig",
    "BridgeKMSEd25519Signer",
    "GCSDurableTimingBridgeLedger",
    "ProductionBridgeRuntime",
    "TimingBridgeProductionError",
    "create_production_bridge",
    "create_production_bridge_app",
]
