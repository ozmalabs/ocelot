"""Server-side RFC3161-to-V3 timing bridge seam.

This module consumes verified RFC3161 evidence and emits one canonical,
bounded ``P5R0RFC3161TimingBridgeEnvelopeV1`` containing a signed
``P5R0IndependentTimingAttestationV3`` record plus the exact RFC response proof.
The proof is internal to the authenticated bridge/evaluator boundary; public
result and startup responses remain digest-only.

The bridge signer, authority, RFC3161 adapter, and ledger are all injected.
This module deliberately does not provision HTTPS, authentication, key custody,
FreeTSA configuration, cloud resources, IAM, a durable-ledger implementation,
or a production runtime; those remain external deployment requirements.
The in-memory ledger is explicitly non-production and is accepted only when
``production_ready=False``.  A production-ready construction must provide a
ledger whose ``durable`` attribute is true.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import threading
from typing import Any, Protocol
import inspect

from .canonical import canonical_bytes, digest, parse_canonical
from .rfc3161 import (
    RFC3161RecordedProof,
    RFC3161TimingEvidenceAdapter,
    validate_rfc3161_evidence,
    validate_rfc3161_proof,
)
from .timing import (
    TimingAttestationError,
    TimingAuthorityConfig,
    sign_independent_timing_attestation_v3,
    validate_attestation,
)
from .timing_bridge import MAX_BRIDGE_REQUEST_BYTES


BRIDGE_REQUEST_SCHEMA = "P5R0RFC3161TimingBridgeRequestV1"
BRIDGE_RECORD_SCHEMA = "P5R0IndependentTimingAttestationV3"
BRIDGE_RESPONSE_SCHEMA = "P5R0RFC3161TimingBridgeEnvelopeV1"
_ALLOWED_EVENTS = frozenset({"task_issued", "result_received"})
_GEN_TIME_RE = re.compile(r"^(\d{14})(?:\.(\d{1,6}))?Z$")


class TimingBridgeServiceError(ValueError):
    """A bridge request, dependency, evidence, or ledger operation failed closed."""


@dataclass(frozen=True)
class TimingLedgerHead:
    """The durable V3 chain head for one run."""

    sequence: int
    previous_digest: str | None


@dataclass(frozen=True)
class TimingLedgerEntry:
    """The minimum durable index needed for replay and conflict detection."""

    request_digest: str
    record_digest: str
    sequence: int
    task_id: str
    event: str


class TimingBridgeLedger(Protocol):
    """Atomic durable ledger required by production bridge deployments.

    ``append`` must reject an unexpected current head (including a concurrent
    writer) and must durably store the request and resulting record digest.
    The service performs the same checks locally to fail closed before calling
    the adapter, but only the ledger can make them restart- and process-safe.
    """

    durable: bool

    def head(self, run_id: str) -> TimingLedgerHead: ...

    def find_request(self, run_id: str, request_digest: str) -> TimingLedgerEntry | None: ...

    def find_event(self, run_id: str, task_id: str, event: str) -> TimingLedgerEntry | None: ...

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
    ) -> None: ...


class InMemoryTimingBridgeLedger:
    """Test-only ledger; never use this implementation for production.

    ``non_production=True`` is intentionally mandatory so a test fixture has
    to make its non-production status explicit at construction time.
    """

    durable = False
    non_production = True

    def __init__(self, *, non_production: bool):
        if non_production is not True:
            raise TimingBridgeServiceError("in-memory timing ledger is test-only")
        self._entries: dict[str, list[TimingLedgerEntry]] = {}
        self._lock = threading.Lock()

    def head(self, run_id: str) -> TimingLedgerHead:
        with self._lock:
            entries = self._entries.get(run_id, [])
            if not entries:
                return TimingLedgerHead(0, None)
            latest = entries[-1]
            return TimingLedgerHead(latest.sequence, latest.record_digest)

    def find_request(self, run_id: str, request_digest: str) -> TimingLedgerEntry | None:
        with self._lock:
            return next((entry for entry in self._entries.get(run_id, []) if entry.request_digest == request_digest), None)

    def find_event(self, run_id: str, task_id: str, event: str) -> TimingLedgerEntry | None:
        with self._lock:
            return next((entry for entry in self._entries.get(run_id, []) if entry.task_id == task_id and entry.event == event), None)

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
        with self._lock:
            entries = self._entries.setdefault(run_id, [])
            expected_sequence = entries[-1].sequence + 1 if entries else 1
            expected_previous = entries[-1].record_digest if entries else None
            if sequence != expected_sequence or previous_digest != expected_previous:
                raise TimingBridgeServiceError("timing ledger sequence conflict")
            if any(entry.request_digest == request_digest for entry in entries):
                raise TimingBridgeServiceError("timing ledger replay")
            if any(entry.task_id == task_id and entry.event == event for entry in entries):
                raise TimingBridgeServiceError("timing ledger event conflict")
            entries.append(TimingLedgerEntry(request_digest, record_digest, sequence, task_id, event))


def _require_digest(value: Any, name: str) -> None:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise TimingBridgeServiceError(f"{name} digest")
    try:
        int(value[7:], 16)
    except ValueError as exc:
        raise TimingBridgeServiceError(f"{name} digest") from exc


def _observed_at(gen_time: Any) -> str:
    """Convert verified RFC3161 GeneralizedTime to V3's canonical UTC form."""
    if not isinstance(gen_time, str):
        raise TimingBridgeServiceError("RFC3161 gen_time")
    match = _GEN_TIME_RE.fullmatch(gen_time)
    if match is None:
        raise TimingBridgeServiceError("RFC3161 gen_time")
    try:
        parsed = datetime.strptime(match.group(1), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise TimingBridgeServiceError("RFC3161 gen_time") from exc
    fraction = match.group(2)
    suffix = f".{(fraction + '000000')[:6]}" if fraction else ""
    return parsed.strftime("%Y-%m-%dT%H:%M:%S") + suffix + "Z"


class TimingBridgeService:
    """Turn verified RFC3161 V1 evidence into signed independent V3 records."""

    independent = True
    bridge_required = False

    def __init__(
        self,
        adapter: RFC3161TimingEvidenceAdapter | None = None,
        authority: TimingAuthorityConfig | None = None,
        signer: Any | None = None,
        ledger: TimingBridgeLedger | None = None,
        *,
        rfc3161_adapter: RFC3161TimingEvidenceAdapter | None = None,
        timing_authority: TimingAuthorityConfig | None = None,
        bridge_signer: Any | None = None,
        production_ready: bool = True,
    ):
        if adapter is not None and rfc3161_adapter is not None:
            raise TimingBridgeServiceError("RFC3161 adapter supplied twice")
        if authority is not None and timing_authority is not None:
            raise TimingBridgeServiceError("timing authority supplied twice")
        if signer is not None and bridge_signer is not None:
            raise TimingBridgeServiceError("bridge signer supplied twice")
        adapter = adapter if adapter is not None else rfc3161_adapter
        authority = authority if authority is not None else timing_authority
        signer = signer if signer is not None else bridge_signer
        if (
            not isinstance(adapter, RFC3161TimingEvidenceAdapter)
            and not callable(getattr(adapter, "record_with_proof", None))
        ) or not callable(getattr(adapter, "verify_proof", None)):
            raise TimingBridgeServiceError("RFC3161 proof-verifying adapter is required")
        if not isinstance(authority, TimingAuthorityConfig):
            raise TimingBridgeServiceError("timing authority is required")
        if signer is None or not callable(getattr(signer, "sign_digest", None)):
            raise TimingBridgeServiceError("bridge signer is required")
        if ledger is None or not all(callable(getattr(ledger, name, None)) for name in ("head", "find_request", "find_event", "append")):
            raise TimingBridgeServiceError("durable timing ledger is required")
        if type(production_ready) is not bool:
            raise TimingBridgeServiceError("production mode")
        if production_ready and getattr(ledger, "durable", False) is not True:
            raise TimingBridgeServiceError("production bridge requires a durable ledger")
        if not production_ready and getattr(ledger, "durable", False) is not True and getattr(ledger, "non_production", False) is not True:
            raise TimingBridgeServiceError("non-durable ledger must be explicitly non-production")
        self.adapter = adapter
        self.authority = authority
        self.signer = signer
        self.ledger = ledger
        self.production_ready = production_ready
        self._lock = threading.Lock()
        self._validate_signer_authority()

    def _validate_signer_authority(self) -> None:
        metadata = getattr(self.signer, "authority", None)
        if not isinstance(metadata, dict):
            raise TimingBridgeServiceError("bridge signer authority metadata is required")
        if any(metadata.get(key) != expected for key, expected in {
            "authority_id": self.authority.authority_id,
            "key_id": self.authority.key_id,
            "public_key_digest": self.authority.public_key_digest,
        }.items()):
            raise TimingBridgeServiceError("bridge signer/authority mismatch")
        public_key = metadata.get("public_key")
        if not isinstance(public_key, str) or digest(public_key) != self.authority.public_key_digest:
            raise TimingBridgeServiceError("bridge signer/authority mismatch")

    @staticmethod
    def _validate_request(request: Any) -> dict[str, Any]:
        fields = {"schema", "run_id", "task_id", "event", "payload_digest"}
        if not isinstance(request, dict) or set(request) != fields or request.get("schema") != BRIDGE_REQUEST_SCHEMA:
            raise TimingBridgeServiceError("timing bridge request schema")
        for key in ("run_id", "task_id", "event"):
            if not isinstance(request.get(key), str) or not request[key]:
                raise TimingBridgeServiceError("timing bridge request metadata")
        if request["event"] not in _ALLOWED_EVENTS:
            raise TimingBridgeServiceError("timing bridge request event")
        _require_digest(request.get("payload_digest"), "payload")
        # Also reject values that could not have been sent as canonical JSON.
        try:
            canonical_bytes(request)
        except Exception as exc:
            raise TimingBridgeServiceError("timing bridge request canonical JSON") from exc
        return request

    def handle(self, raw_request: bytes) -> dict[str, Any]:
        """Parse one canonical request and return an authenticated proof envelope."""
        if not isinstance(raw_request, bytes) or len(raw_request) > MAX_BRIDGE_REQUEST_BYTES:
            raise TimingBridgeServiceError("timing bridge request bound")
        try:
            request = parse_canonical(raw_request)
        except Exception as exc:
            raise TimingBridgeServiceError("timing bridge request must be canonical JSON") from exc
        return self.record(request)

    def handle_request(self, raw_request: bytes) -> dict[str, Any]:
        """Compatibility name for HTTP/framework adapters around ``handle``."""
        return self.handle(raw_request)

    def record(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process a validated request and return the authenticated internal proof envelope."""
        request = self._validate_request(request)
        request_digest = digest(request)
        run_id = request["run_id"]
        with self._lock:
            try:
                if self.ledger.find_request(run_id, request_digest) is not None:
                    raise TimingBridgeServiceError("timing bridge request replay")
                if self.ledger.find_event(run_id, request["task_id"], request["event"]) is not None:
                    raise TimingBridgeServiceError("timing bridge event conflict")
                head = self.ledger.head(run_id)
                if not isinstance(head, TimingLedgerHead) or type(head.sequence) is not int or head.sequence < 0:
                    raise TimingBridgeServiceError("timing ledger head")
                next_sequence = head.sequence + 1
                # The adapter must return both the legacy digest-only evidence and
                # the exact bounded response proof. Legacy ``record``-only adapters
                # are rejected at construction rather than weakening verification.
                record_with_proof = self.adapter.record_with_proof
                adapter_kwargs = {
                    "run_id": run_id,
                    "task_id": request["task_id"],
                    "event": request["event"],
                    "payload_digest": request["payload_digest"],
                }
                # Production RFC adapters accept the durable ledger position so
                # their evidence chain survives bridge process restarts.  Keep
                # compatibility with older injected test adapters that expose
                # only the original four-argument seam.
                try:
                    parameters = inspect.signature(record_with_proof).parameters
                    if "sequence" in parameters:
                        adapter_kwargs.update(sequence=next_sequence, previous_digest=head.previous_digest)
                except (TypeError, ValueError):
                    pass
                recorded = record_with_proof(**adapter_kwargs)
                if not isinstance(recorded, RFC3161RecordedProof):
                    raise TimingBridgeServiceError("RFC3161 proof recording result")
                evidence = recorded.evidence
                proof = recorded.proof
                self._validate_evidence(evidence, request, next_sequence)
                try:
                    validate_rfc3161_proof(proof)
                    proof_evidence = self.adapter.verify_proof(
                        proof,
                        run_id=run_id,
                        task_id=request["task_id"],
                        event=request["event"],
                        payload_digest=request["payload_digest"],
                        sequence=next_sequence,
                        previous_digest=evidence.get("previous_digest"),
                    )
                    if not isinstance(proof_evidence, dict) or digest(proof_evidence) != digest(evidence):
                        raise ValueError("proof/evidence digest")
                except Exception as exc:
                    raise TimingBridgeServiceError("RFC3161 proof mismatch") from exc
                evidence_digest = digest(evidence)
                record = {
                    "schema": BRIDGE_RECORD_SCHEMA,
                    "ledger_id": self.authority.ledger_id,
                    "run_id": run_id,
                    "task_id": request["task_id"],
                    "event": request["event"],
                    "sequence": next_sequence,
                    "previous_digest": head.previous_digest,
                    "seed_digest": evidence_digest,
                    "payload_digest": request["payload_digest"],
                    "observed_at": _observed_at(evidence["gen_time"]),
                    "authority_id": self.authority.authority_id,
                    "key_id": self.authority.key_id,
                    "public_key": self.signer.authority["public_key"],
                    "public_key_digest": self.authority.public_key_digest,
                    "rfc3161_evidence_digest": evidence_digest,
                    "signature": "",
                }
                signed = sign_independent_timing_attestation_v3(record, self.signer)
                validate_attestation(
                    signed,
                    run_id=run_id,
                    task_id=request["task_id"],
                    event=request["event"],
                    payload_digest=request["payload_digest"],
                    expected_authority_id=self.authority.authority_id,
                    expected_key_id=self.authority.key_id,
                    expected_public_key_digest=self.authority.public_key_digest,
                    expected_ledger_id=self.authority.ledger_id,
                    previous_digest=head.previous_digest,
                    last_sequence=head.sequence,
                    expected_rfc3161_evidence_digest=evidence_digest,
                )
                self.ledger.append(
                    run_id,
                    request_digest=request_digest,
                    record_digest=digest(signed),
                    sequence=next_sequence,
                    previous_digest=head.previous_digest,
                    task_id=request["task_id"],
                    event=request["event"],
                )
                return {
                    "schema": BRIDGE_RESPONSE_SCHEMA,
                    "record": signed,
                    "proof": proof,
                }
            except TimingBridgeServiceError:
                raise
            except Exception as exc:
                raise TimingBridgeServiceError("timing bridge failed closed") from exc

    @staticmethod
    def _validate_evidence(evidence: Any, request: dict[str, Any], expected_sequence: int) -> None:
        if not isinstance(evidence, dict):
            raise TimingBridgeServiceError("RFC3161 evidence mismatch")
        try:
            sequence = evidence.get("sequence")
            validate_rfc3161_evidence(
                evidence,
                run_id=request["run_id"],
                task_id=request["task_id"],
                event=request["event"],
                payload_digest=request["payload_digest"],
                previous_digest=evidence.get("previous_digest"),
                last_sequence=sequence - 1 if type(sequence) is int else 0,
            )
        except Exception as exc:
            raise TimingBridgeServiceError("RFC3161 evidence mismatch") from exc
        if evidence.get("sequence") != expected_sequence:
            raise TimingBridgeServiceError("RFC3161 evidence sequence mismatch")


__all__ = [
    "BRIDGE_REQUEST_SCHEMA",
    "BRIDGE_RECORD_SCHEMA",
    "BRIDGE_RESPONSE_SCHEMA",
    "TimingBridgeServiceError",
    "TimingLedgerHead",
    "TimingLedgerEntry",
    "TimingBridgeLedger",
    "InMemoryTimingBridgeLedger",
    "TimingBridgeService",
]
