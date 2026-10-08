"""Reviewed DISPATCH-078 bootstrap orchestration.

This module is the sole repository entry boundary for the versioned
APPROVAL-018 Confidential Space bootstrap.  It consumes exactly the checked-in
APPROVAL-018 packet and its declared child-approval artifact path, then
 delegates launcher/JWT/STS/IAM work to :class:`ConfidentialSpaceAdapter`
through ``bootstrap_credentials``.  It never provisions infrastructure, calls
gcloud, creates credentials, invokes KMS/GCS/FreeTSA, or enters Track A
execution.

The default ``validate`` and ``dry-run`` modes are entirely local.  The
``effectful`` mode is explicit and uses only the verifier-owned adapter factory,
canonical request loader, and clock.  An attempt ledger is the only caller-owned
side effect sink; it is create-only, so once an effectful attempt is reserved it
cannot be retried, even after a failed bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import time
from typing import Any, Mapping, Protocol

from evaluation.p0a.canonical import canonical_bytes
from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.confidential_space import (
    ConfidentialSpaceAdapter,
    GoogleJwtAttestationVerifier,
    GoogleSTSClient,
    LauncherTokenSource,
    LockedBootstrapConfig,
)
from services.p5_r0_evaluator.deploy.signed_environment_credentials import (
    CredentialBootstrapReceipt,
    CredentialExecutionRequest,
    CredentialOnlyCapabilityFactory,
    CredentialProcessError,
    VerifiedCredentialChildApproval,
    bootstrap_credentials,
    build_execution_request,
    validate_child_approval,
    validate_execution_request,
    validate_receipt,
)
from services.p5_r0_evaluator.deploy.signed_environment_process import (
    VerifiedCapabilityBinding,
    validate_capability_binding,
    validate_kms_binding,
)
from services.p5_r0_evaluator.deploy.iam_predecessor import VerifiedIAMPredecessor, load_verified_iam_predecessor, validate_verified_iam_predecessor
from services.p5_r0_evaluator.deploy.track_a_bootstrap_request import (
    DEFAULT_REQUEST as HISTORICAL_REQUEST,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
APPROVAL_018_REQUEST_PATH = (
    Path(__file__).with_name("p5-r0-track-a-bootstrap-request-approval-018-v1.json").resolve()
)
APPROVAL_018_CHILD_APPROVAL_PATH = (
    Path(__file__).with_name("p5-r0-track-a-bootstrap-child-approval-018-v1.json").resolve()
)
APPROVAL_018_REQUEST_DIGEST = "sha256:eaa44e722611d0e6c07a3138d44b6625e1073e161cdb880b8c717bb9839cdf89"
APPROVAL_018_CHILD_APPROVAL_ARTIFACT_DIGEST = "sha256:9eb73f2318702be7bdc3c3b123341d81b16d37659b4c2dcb9d5e5ecad5935812"
APPROVAL_ID = "P5-MASTER-001/APPROVAL-018"
DISPATCH_ID = "P5-MASTER-001/DISPATCH-077"
ATTEMPT_ID = "P5-MASTER-001/APPROVAL-018/DISPATCH-077/ATTEMPT-001"
OPERATION_ID = "bootstrap_signed_environment_credentials"
FORBIDDEN_OPERATIONS = (
    "timing",
    "task_issuance",
    "native_execution",
    "kms_result_signing",
    "gcs_publication",
    "result_sealing",
    "retry",
)
RUNNER_VERSION = "P5R0DISPATCH078BootstrapRunnerV1"
CANONICAL_PACKET_PATH = str(APPROVAL_018_REQUEST_PATH)
CHILD_APPROVAL_PATH = str(APPROVAL_018_CHILD_APPROVAL_PATH)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PROVIDER_RE = re.compile(
    r"^//iam\.googleapis\.com/projects/(?P<number>[0-9]+)/locations/global/"
    r"workloadIdentityPools/(?P<pool>[a-z0-9-]+)/providers/(?P<provider>[a-z0-9-]+)$"
)
_CANONICAL_SCHEMA = "P5R0TrackABootstrapRequestV2"
_CANONICAL_STATUS = "blocked_pending_live_bindings"
_MODES = {"validate", "dry-run", "dry_run", "effectful"}
_PROTECTED_PATHS = {
    HISTORICAL_REQUEST.resolve(),
    APPROVAL_018_REQUEST_PATH,
    APPROVAL_018_CHILD_APPROVAL_PATH,
    (REPOSITORY_ROOT / "var/p5-r0-rs069/operation-ledger.jsonl").resolve(),
    (REPOSITORY_ROOT / "var/p5-r0-rs069/operation-0-dispatch-052-iam-ledger.jsonl").resolve(),
}


class BootstrapRunnerError(ValueError):
    """A DISPATCH-078 input or effectful attempt failed closed."""


class AttemptLedgerError(BootstrapRunnerError):
    """The one-attempt ledger cannot safely reserve or close an attempt."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BootstrapRunnerError(message)


def _is_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} is not a sha256 digest")
    return value


def _closed_digest(value: Mapping[str, Any], field: str) -> str:
    _is_digest(value.get(field), field)
    return digest({key: child for key, child in value.items() if key != field})


@dataclass(frozen=True)
class ReviewedBootstrapBindings:
    """Verifier-owned observations required by the bootstrap boundary.

    ``authority``, ``image_binding``, ``wip_binding`` and ``closure`` are
    immutable reviewed snapshots supplied by the verifier.  ``kms`` and
    ``capability_binding`` retain their existing typed provenance checks; a
    copied mapping is not accepted for the latter.
    """

    authority: Mapping[str, Any]
    kms: Mapping[str, Any]
    capability_binding: VerifiedCapabilityBinding
    image_binding: Mapping[str, Any]
    wip_binding: Mapping[str, Any]
    closure: Mapping[str, Any]
    # No declarative IAM digest is accepted; this must be the sealed result
    # issued by the verified IAM apply path.
    iam_predecessor: VerifiedIAMPredecessor | None = None
    iam_ledger_path: Path | None = None
    iam_root_verifier: Any = None
    iam_packet_digest: str | None = None
    iam_prestate_digest: str | None = None
    iam_evidence_digest: str | None = None


@dataclass(frozen=True)
class PreparedBootstrap:
    """Closed local preflight output; it contains no token or credential."""

    request: Mapping[str, Any]
    config: LockedBootstrapConfig
    execution_request: CredentialExecutionRequest
    bindings: ReviewedBootstrapBindings
    approval: VerifiedCredentialChildApproval


class AttemptLedger(Protocol):
    def reserve(self, *, attempt_id: str, packet_digest: str, packet_path: str, execution_request_digest: str) -> None: ...

    def complete(self, *, packet_digest: str, packet_path: str, execution_request_digest: str, receipt_digest: str) -> None: ...

    def fail(self, *, packet_digest: str, packet_path: str, execution_request_digest: str, reason: str) -> None: ...

    @property
    def ledger_digest(self) -> str: ...


class FileAttemptLedger:
    """Create-only local ledger for exactly one effectful attempt.

    The path must be supplied by the caller and must not point at a historical
    or canonical repository ledger.  Reservation uses exclusive creation, so a
    second process cannot silently retry the approved operation.
    """

    def __init__(self, path: Path):
        self.path = Path(path).resolve()
        _require(self.path not in _PROTECTED_PATHS, "bootstrap attempt ledger cannot overwrite a protected ledger")
        _require(self.path.name.endswith((".jsonl", ".json")), "bootstrap attempt ledger path must be an audit file")
        self._reserved = False
        self._closed = False
        self._binding: tuple[str, str, str] | None = None

    def _append(self, value: Mapping[str, Any]) -> None:
        try:
            with self.path.open("ab") as handle:
                handle.write(canonical_bytes(dict(value)) + b"\n")
        except FileExistsError:
            raise AttemptLedgerError("bootstrap attempt ledger already exists; retry is disabled")
        except OSError as exc:
            raise AttemptLedgerError("bootstrap attempt ledger is unavailable") from exc

    def reserve(self, *, attempt_id: str, packet_digest: str, packet_path: str, execution_request_digest: str) -> None:
        if self._reserved or self.path.exists():
            raise AttemptLedgerError("bootstrap effectful attempt already exists; retry is disabled")
        _is_digest(packet_digest, "canonical packet digest")
        _is_digest(execution_request_digest, "execution request digest")
        _require(attempt_id == ATTEMPT_ID, "bootstrap attempt identity drift")
        _require(isinstance(packet_path, str) and packet_path.startswith("/"), "canonical packet path is invalid")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "schema": "P5R0DISPATCH078BootstrapLedgerEventV1",
            "kind": "attempt_reserved",
            "attempt_id": attempt_id,
            "packet_digest": packet_digest,
            "packet_path": packet_path,
            "execution_request_digest": execution_request_digest,
            "cloud_operations": [],
            "credentials_exported": False,
        }
        try:
            with self.path.open("xb") as handle:
                handle.write(canonical_bytes(record) + b"\n")
        except FileExistsError as exc:
            raise AttemptLedgerError("bootstrap effectful attempt already exists; retry is disabled") from exc
        except OSError as exc:
            raise AttemptLedgerError("bootstrap attempt ledger could not be reserved") from exc
        self._binding = (packet_digest, packet_path, execution_request_digest)
        self._reserved = True

    def _close(self, kind: str, *, packet_digest: str, packet_path: str, execution_request_digest: str, **extra: Any) -> None:
        if not self._reserved or self._closed:
            raise AttemptLedgerError("bootstrap attempt ledger is already closed")
        if self._binding != (packet_digest, packet_path, execution_request_digest):
            raise AttemptLedgerError("bootstrap attempt ledger binding mismatch")
        record = {
            "schema": "P5R0DISPATCH078BootstrapLedgerEventV1",
            "kind": kind,
            "attempt_id": ATTEMPT_ID,
            "packet_digest": packet_digest,
            "packet_path": packet_path,
            "execution_request_digest": execution_request_digest,
            "cloud_operations": [],
            "credentials_exported": False,
            **extra,
        }
        self._append(record)
        self._closed = True

    def complete(self, *, packet_digest: str, packet_path: str, execution_request_digest: str, receipt_digest: str) -> None:
        _is_digest(receipt_digest, "bootstrap receipt digest")
        self._close("bootstrap_completed", packet_digest=packet_digest, packet_path=packet_path, execution_request_digest=execution_request_digest, receipt_digest=receipt_digest)

    def fail(self, *, packet_digest: str, packet_path: str, execution_request_digest: str, reason: str) -> None:
        _require(isinstance(reason, str) and reason and "\n" not in reason, "bootstrap failure reason is invalid")
        self._close("bootstrap_failed", packet_digest=packet_digest, packet_path=packet_path, execution_request_digest=execution_request_digest, reason=reason)

    @property
    def ledger_digest(self) -> str:
        if not self.path.is_file():
            return digest(b"")
        return digest(self.path.read_bytes())


class MemoryAttemptLedger:
    """Deterministic test/embedding ledger with the same one-shot semantics."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self._closed = False
        self._binding: tuple[str, str, str] | None = None

    def reserve(self, *, attempt_id: str, packet_digest: str, packet_path: str, execution_request_digest: str) -> None:
        if self.records:
            raise AttemptLedgerError("bootstrap effectful attempt already exists; retry is disabled")
        _is_digest(packet_digest, "canonical packet digest")
        _is_digest(execution_request_digest, "execution request digest")
        _require(attempt_id == ATTEMPT_ID, "bootstrap attempt identity drift")
        _require(isinstance(packet_path, str) and packet_path.startswith("/"), "canonical packet path is invalid")
        self.records.append({
            "schema": "P5R0DISPATCH078BootstrapLedgerEventV1",
            "kind": "attempt_reserved",
            "attempt_id": attempt_id,
            "packet_digest": packet_digest,
            "packet_path": packet_path,
            "execution_request_digest": execution_request_digest,
            "cloud_operations": [],
            "credentials_exported": False,
        })
        self._binding = (packet_digest, packet_path, execution_request_digest)

    def _close(self, kind: str, *, packet_digest: str, packet_path: str, execution_request_digest: str, **extra: Any) -> None:
        if not self.records or self._closed:
            raise AttemptLedgerError("bootstrap attempt ledger is already closed")
        if self._binding != (packet_digest, packet_path, execution_request_digest):
            raise AttemptLedgerError("bootstrap attempt ledger binding mismatch")
        self.records.append({
            "schema": "P5R0DISPATCH078BootstrapLedgerEventV1",
            "kind": kind,
            "attempt_id": self.records[0]["attempt_id"],
            "packet_digest": packet_digest,
            "packet_path": packet_path,
            "execution_request_digest": execution_request_digest,
            "cloud_operations": [],
            "credentials_exported": False,
            **extra,
        })
        self._closed = True

    def complete(self, *, packet_digest: str, packet_path: str, execution_request_digest: str, receipt_digest: str) -> None:
        self._close("bootstrap_completed", packet_digest=packet_digest, packet_path=packet_path, execution_request_digest=execution_request_digest, receipt_digest=receipt_digest)

    def fail(self, *, packet_digest: str, packet_path: str, execution_request_digest: str, reason: str) -> None:
        self._close("bootstrap_failed", packet_digest=packet_digest, packet_path=packet_path, execution_request_digest=execution_request_digest, reason=reason)

    @property
    def ledger_digest(self) -> str:
        return digest(self.records)


@dataclass(frozen=True)
class BootstrapRunResult:
    """Redacted outcome for validation, dry-run, or one bootstrap attempt."""

    mode: str
    status: str
    request_digest: str
    attempt_id: str
    receipt: CredentialBootstrapReceipt | None = None
    ledger_digest: str | None = None
    reason_code: str | None = None

    def as_public_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema": "P5R0DISPATCH078BootstrapResultV1",
            "runner_version": RUNNER_VERSION,
            "mode": self.mode,
            "status": self.status,
            "request_digest": self.request_digest,
            "attempt_id": self.attempt_id,
            "ledger_digest": self.ledger_digest,
            "reason_code": self.reason_code,
            "cloud_operations": [],
            "credentials_exported": False,
            "downstream_operations": [],
        }
        if self.receipt is not None:
            value["receipt"] = self.receipt.as_public_dict()
        return value


def _canonical_packet_path(path: Path) -> str:
    resolved = Path(path).resolve()
    _require(resolved == APPROVAL_018_REQUEST_PATH, "APPROVAL-018 packet path is not canonical")
    return str(resolved)


def _child_approval_path(path: Path) -> str:
    resolved = Path(path).resolve()
    _require(resolved == APPROVAL_018_CHILD_APPROVAL_PATH, "APPROVAL-018 child approval path is not canonical")
    return str(resolved)


def _validate_child_approval_artifact(value: Mapping[str, Any]) -> None:
    _require(isinstance(value, Mapping), "APPROVAL-018 child approval artifact must be an object")
    _require(value.get("schema") == "P5R0TrackABootstrapChildApprovalV1", "APPROVAL-018 child approval schema drift")
    _require(value.get("version") == 1, "APPROVAL-018 child approval version drift")
    _require(value.get("approval_id") == APPROVAL_ID, "APPROVAL-018 child approval identity drift")
    _require(value.get("dispatch_id") == DISPATCH_ID and value.get("attempt_id") == ATTEMPT_ID, "APPROVAL-018 child approval attempt drift")
    _require(value.get("request_path") == str(APPROVAL_018_REQUEST_PATH.relative_to(REPOSITORY_ROOT)), "APPROVAL-018 child approval request path drift")
    _require(value.get("request_digest") == APPROVAL_018_REQUEST_DIGEST, "APPROVAL-018 child approval request digest drift")
    _require(
        value.get("status") == "blocked_pending_verifier_issued_bindings"
        and value.get("approved") is False
        and value.get("enabled") is False,
        "APPROVAL-018 child approval is not the blocked placeholder",
    )
    _require(value.get("cloud_operations") == [] and value.get("mutations_performed") is False and value.get("credentials_exported") is False, "APPROVAL-018 child approval crossed a cloud boundary")
    _require(value.get("artifact_digest") == _closed_digest(value, "artifact_digest"), "APPROVAL-018 child approval artifact digest mismatch")
    _require(value.get("artifact_digest") == APPROVAL_018_CHILD_APPROVAL_ARTIFACT_DIGEST, "APPROVAL-018 child approval artifact is not approved")


def _load_child_approval_artifact(path: Path = APPROVAL_018_CHILD_APPROVAL_PATH) -> dict[str, Any]:
    canonical_path = _child_approval_path(path)
    try:
        value = json.loads(Path(canonical_path).read_text())
    except Exception as exc:
        raise BootstrapRunnerError("canonical APPROVAL-018 child approval could not be loaded") from exc
    _validate_child_approval_artifact(value)
    return value


def _load_canonical_request(path: Path = APPROVAL_018_REQUEST_PATH) -> dict[str, Any]:
    canonical_path = _canonical_packet_path(path)
    try:
        value = json.loads(Path(canonical_path).read_text())
    except Exception as exc:
        raise BootstrapRunnerError("canonical APPROVAL-018 request could not be loaded") from exc
    _require(isinstance(value, dict), "canonical APPROVAL-018 request must be an object")
    _validate_request_shape(value)
    child = _load_child_approval_artifact()
    _require(value["child_approval"]["path"] == str(APPROVAL_018_CHILD_APPROVAL_PATH.relative_to(REPOSITORY_ROOT)), "APPROVAL-018 child approval path is not bound")
    _require(child["request_digest"] == APPROVAL_018_REQUEST_DIGEST, "APPROVAL-018 child approval is not bound to the approved request")
    return value


def _validate_request_shape(request: Mapping[str, Any]) -> None:
    _require(isinstance(request, Mapping), "bootstrap request is missing")
    _require(request.get("schema") == _CANONICAL_SCHEMA, "APPROVAL-018 request schema drift")
    _require(request.get("version") == 1, "APPROVAL-018 request version drift")
    _require(request.get("status") == _CANONICAL_STATUS, "APPROVAL-018 request status drift")
    approval = request.get("approval")
    _require(isinstance(approval, Mapping), "APPROVAL-018 approval is missing")
    _require(
        approval.get("approval_id") == APPROVAL_ID
        and approval.get("dispatch_id") == DISPATCH_ID
        and approval.get("attempt_id") == ATTEMPT_ID,
        "APPROVAL-018 identity drift",
    )
    _require(approval.get("single_attempt") is True and approval.get("retry_allowed") is False, "APPROVAL-018 retry boundary drift")
    operation = request.get("operation")
    _require(isinstance(operation, Mapping), "bootstrap operation is missing")
    _require(operation.get("id") == OPERATION_ID and operation.get("scope") == [OPERATION_ID], "bootstrap operation scope drift")
    _require(
        operation.get("cloud_operations") == []
        and operation.get("mutations_performed") is False
        and operation.get("credentials_exported") is False,
        "bootstrap request crossed a cloud boundary",
    )
    _require(operation.get("forbidden_operations") == list(FORBIDDEN_OPERATIONS), "bootstrap forbidden-operation boundary drift")
    claim_boundary = request.get("claim_boundary")
    _require(isinstance(claim_boundary, str) and claim_boundary.startswith("Blocked preparation only;"), "bootstrap claim boundary drift")
    reviewed_boundary = request.get("reviewed_boundary")
    _require(isinstance(reviewed_boundary, Mapping) and reviewed_boundary.get("runner_fixed_factory") is True, "reviewed runner requirement missing")
    child = request.get("child_approval")
    _require(isinstance(child, Mapping), "APPROVAL-018 child approval metadata is missing")
    _require(child.get("path") == str(Path(CHILD_APPROVAL_PATH).relative_to(REPOSITORY_ROOT)), "APPROVAL-018 child approval path drift")
    _require(request.get("request_digest") == _closed_digest(request, "request_digest"), "APPROVAL-018 request digest mismatch")
    _require(request.get("request_digest") == APPROVAL_018_REQUEST_DIGEST, "APPROVAL-018 request digest is not approved")


def _expected_wip(request: Mapping[str, Any]) -> dict[str, Any]:
    environment = request["environment"]
    candidate = request["candidate"]
    return {
        "schema": "P5R0DISPATCH078WIPBindingV1",
        "provider": environment["wip_provider"],
        "audience": environment["wip_token_audience"],
        "issuer": environment["issuer"],
        "claim_paths": dict(environment["claim_paths"]),
        "subject_prefix": environment["attestation_subject_prefix"],
        "image_digest": candidate["image_digest"],
        "project_number": candidate["project_number"],
        "project_id": candidate["project_id"],
        "zone": environment["zone"],
        "debug_state": environment["debug_state"],
        "tee": environment["tee"],
        "hardware_model": environment["hardware_model"],
        "secure_boot": environment["secure_boot"],
        "workload": environment["workload"],
        "smoke": "1" if environment["smoke"] else "0",
    }


def _verifier_now() -> int:
    """Return the runner-owned wall clock used for one bootstrap attempt."""
    return int(time.time())


def _config_from_request(request: Mapping[str, Any], authority: Mapping[str, Any]) -> LockedBootstrapConfig:
    candidate = request["candidate"]
    environment = request["environment"]
    closure = request["closure"]
    capability = request["capability"]
    _require(isinstance(environment.get("attestation_subject_prefix"), str) and environment["attestation_subject_prefix"], "WIP attestation subject prefix is unresolved")
    _require(isinstance(authority, Mapping), "verifier-owned authority binding is required")
    return LockedBootstrapConfig(
        authority=dict(authority),
        caller_audience=environment["wip_token_audience"],
        allowed_subjects=frozenset({environment["attestation_subject_prefix"]}),
        attestation_audience=environment["wip_token_audience"],
        wip_provider=environment["wip_provider"],
        project_number=candidate["project_number"],
        project_id=candidate["project_id"],
        zone=environment["zone"],
        image_digest=candidate["image_digest"],
        debug_state=environment["debug_state"],
        tee=environment["tee"],
        secure_boot=environment["secure_boot"],
        bucket=capability["bucket"],
        prefix=capability["prefix"],
        kms_key_version=request["authority"]["kms_key_version"],
        runtime_digest=closure["runtime_digest"],
        resource_profile_digest=digest(closure["limits"]),
        base_image_digest=candidate["image_digest"],
        service_name="p5-r0-evaluator",
        region=candidate["region"],
        expected_issuer=environment["issuer"],
        workload=environment["workload"],
        attestation_subject_prefix=environment["attestation_subject_prefix"],
        hardware_model=environment["hardware_model"],
        claim_paths=dict(environment["claim_paths"]),
        clock=_verifier_now,
        confidential_space_smoke=bool(environment["smoke"]),
        capability_service_account=capability["service_account"],
    )


def _validate_bindings(request: Mapping[str, Any], bindings: ReviewedBootstrapBindings, *, packet_path: str) -> tuple[LockedBootstrapConfig, CredentialExecutionRequest]:
    _require(isinstance(bindings, ReviewedBootstrapBindings), "verifier-owned bootstrap bindings are required")
    for name in ("authority", "image_binding", "wip_binding", "closure"):
        _require(isinstance(getattr(bindings, name, None), Mapping), f"{name} binding is missing")
    _require(isinstance(bindings.kms, Mapping), "KMS observation is required")
    authority_binding = bindings.kms.get("authority_binding")
    _require(isinstance(authority_binding, Mapping), "KMS authority binding is missing")
    _require(isinstance(bindings.capability_binding, VerifiedCapabilityBinding), "verifier-issued IAM capability binding is required")
    _require(bindings.iam_predecessor is not None or bindings.iam_ledger_path is not None, "verified IAM predecessor receipt is required before bootstrap")
    try:
        predecessor = bindings.iam_predecessor
        if bindings.iam_ledger_path is not None:
            _require(bindings.iam_root_verifier is not None and all(isinstance(value, str) and value for value in (bindings.iam_packet_digest, bindings.iam_prestate_digest, bindings.iam_evidence_digest)), "trusted IAM root and exact packet/prestate/evidence bindings are required")
            predecessor = load_verified_iam_predecessor(
                ledger_path=bindings.iam_ledger_path, operation_id="provision_gcs_only_iam_boundary",
                attempt_id="dispatch082-iam-20260920-a7f4c2d9", trusted_verifier=bindings.iam_root_verifier,
                packet_digest=bindings.iam_packet_digest, prestate_digest=bindings.iam_prestate_digest, evidence_digest=bindings.iam_evidence_digest,
            )
        validate_verified_iam_predecessor(predecessor, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9", trusted_verifier=bindings.iam_root_verifier, packet_digest=bindings.iam_packet_digest, prestate_digest=bindings.iam_prestate_digest, evidence_digest=bindings.iam_evidence_digest)
    except Exception as exc:
        raise BootstrapRunnerError("exact verified IAM predecessor receipt is required") from exc
    candidate = request["candidate"]
    _require(dict(bindings.image_binding) == dict(candidate), "candidate image binding is not exact")
    _require(dict(bindings.closure) == dict(request["closure"]), "Track A closure binding is not exact")
    _require(dict(bindings.wip_binding) == _expected_wip(request), "WIP/provider binding is not exact")
    _is_digest(candidate["image_digest"], "candidate image digest")
    _require(candidate["image_reference"].endswith("@" + candidate["image_digest"]), "candidate image reference is not immutable")
    _require(candidate["remote_digest_verified"] is True, "candidate remote image digest is not verified")
    _require(_PROVIDER_RE.fullmatch(request["environment"]["wip_provider"]) is not None, "WIP provider is not canonical")
    _require(request["environment"]["wip_token_audience"] == "https://sts.googleapis.com", "WIP token audience is not exact")
    _require(request["closure"]["image_digest"] == candidate["image_digest"], "closure/image binding drift")
    _require(request["closure"]["candidate_image_reference"] == candidate["image_reference"], "closure candidate image reference is not reconciled")
    _require(request["closure"]["closure_image_reference"] == candidate["image_reference"], "closure image reference is not exact")
    _require(request["closure"]["runtime"] == "crun" and request["closure"]["network"] == "none" and request["closure"]["pull"] == "never", "closure execution posture drift")
    _require(isinstance(request["closure"]["limits"], Mapping) and all(type(request["closure"]["limits"].get(name)) is int and request["closure"]["limits"][name] > 0 for name in ("steps", "frame_bytes", "wall_seconds", "memory_mb", "cpu", "pids")), "closure resource limits are invalid")

    authority = dict(bindings.authority)
    transport = authority.get("transport_attestation")
    expected_transport = {
        "schema": "P5R0AuthorityTransportV1",
        "provider": request["environment"]["wip_provider"],
        "audience": request["environment"]["wip_token_audience"],
        "event": "confidential_space_attestation",
    }
    _require(set(authority) == {"schema", "authority_id", "key_id", "public_key", "public_key_digest", "transport_attestation"}, "authority binding is not closed")
    _require(dict(transport) == expected_transport, "authority WIP transport binding is not exact")
    request_authority = request["authority"]
    for field in ("schema", "authority_id", "key_id", "public_key", "public_key_digest"):
        _require(authority[field] == request_authority[field], f"authority {field} binding drift")
    _require(request_authority["authority_binding_digest"] is not None, "authority binding is not materialized")
    _is_digest(request_authority["authority_binding_digest"], "authority binding digest")
    _require(request_authority["transport_binding_digest"] == digest(expected_transport), "authority transport digest drift")
    _require(isinstance(bindings.kms, Mapping), "KMS observation is required")
    _require(bindings.kms["authority_binding"].get("binding_digest") == request_authority["authority_binding_digest"], "KMS authority binding digest drift")

    try:
        config = _config_from_request(request, authority)
    except Exception as exc:
        raise BootstrapRunnerError("Confidential Space policy binding is invalid") from exc
    try:
        validate_kms_binding(authority, bindings.kms, config)
        validate_capability_binding(bindings.capability_binding, config)
    except Exception as exc:
        raise BootstrapRunnerError("exact IAM/KMS binding validation failed") from exc
    capability_public = bindings.capability_binding.as_public_dict()
    _require(capability_public["run_id"] == request["capability"]["run_id"], "IAM capability run binding drift")
    try:
        execution_request = build_execution_request(
            config=config, kms=bindings.kms, capability_binding=bindings.capability_binding,
            packet_digest=request["request_digest"], packet_path=packet_path,
        )
    except Exception as exc:
        raise BootstrapRunnerError("credential execution request could not be bound") from exc
    return config, execution_request


def prepare_bootstrap(
    request: Mapping[str, Any],
    *,
    bindings: ReviewedBootstrapBindings,
    child_approval: VerifiedCredentialChildApproval,
    packet_path: str = CANONICAL_PACKET_PATH,
    child_approval_path: str = CHILD_APPROVAL_PATH,
) -> PreparedBootstrap:
    """Validate the exact APPROVAL-018 packet and verifier prerequisites."""
    try:
        _canonical_packet_path(Path(packet_path))
        _child_approval_path(Path(child_approval_path))
        _validate_request_shape(request)
        config, execution_request = _validate_bindings(request, bindings, packet_path=packet_path)
    except BootstrapRunnerError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise BootstrapRunnerError("bootstrap preflight failed closed") from exc
    try:
        validate_execution_request(
            execution_request.as_public_dict(), config=config, kms=bindings.kms,
            capability_binding=bindings.capability_binding,
            packet_digest=request["request_digest"], packet_path=packet_path,
        )
        validate_child_approval(child_approval, request=execution_request, now=_verifier_now())
    except Exception as exc:
        if isinstance(exc, BootstrapRunnerError):
            raise
        raise BootstrapRunnerError("verifier child approval or execution request is stale") from exc
    return PreparedBootstrap(
        request=dict(request), config=config, execution_request=execution_request,
        bindings=bindings, approval=child_approval,
    )


class ReviewedConfidentialSpaceAdapterFactory:
    """Production factory with verifier-owned, fixed trust components."""

    def build(self, prepared: PreparedBootstrap) -> ConfidentialSpaceAdapter:
        _require(type(prepared) is PreparedBootstrap, "prepared bootstrap is required")
        config = prepared.config
        factory = CredentialOnlyCapabilityFactory(
            config,
            capability_binding_digest=prepared.bindings.capability_binding.binding_digest,
        )
        return ConfidentialSpaceAdapter(
            config,
            source=LauncherTokenSource(),
            verifier=GoogleJwtAttestationVerifier(),
            sts=GoogleSTSClient(),
            capability_factory=factory,
        )


class ReviewedBootstrapRunner:
    """Validate, dry-run, or execute exactly one credential bootstrap."""

    def __init__(self, *, ledger: AttemptLedger | None = None) -> None:
        # These are deliberately not constructor parameters.  The effectful
        # entrypoint owns the trust components, canonical loader, and clock;
        # callers may provide only the local create-only audit sink.
        self.ledger = ledger

    def run(
        self,
        *,
        mode: str = "validate",
        request_path: Path = APPROVAL_018_REQUEST_PATH,
        bindings: ReviewedBootstrapBindings,
        child_approval: VerifiedCredentialChildApproval,
    ) -> BootstrapRunResult:
        if mode == "dry_run":
            mode = "dry-run"
        _require(mode in {"validate", "dry-run", "effectful"}, "bootstrap mode must be validate, dry-run, or effectful")
        _require(Path(request_path).resolve() == APPROVAL_018_REQUEST_PATH, "APPROVAL-018 packet path is not canonical")
        canonical_packet_path = _canonical_packet_path(APPROVAL_018_REQUEST_PATH)
        try:
            # Do not call through a caller-provided loader.  The versioned
            # loader rechecks the fixed path, exact digest, identity, and
            # child-approval artifact path before any adapter is constructed.
            request = _load_canonical_request(APPROVAL_018_REQUEST_PATH)
        except BootstrapRunnerError:
            raise
        except Exception as exc:
            raise BootstrapRunnerError("canonical APPROVAL-018 request could not be loaded") from exc
        prepared = prepare_bootstrap(
            request,
            bindings=bindings,
            child_approval=child_approval,
            packet_path=canonical_packet_path,
            child_approval_path=CHILD_APPROVAL_PATH,
        )
        if mode == "validate":
            return BootstrapRunResult("validate", "validated", prepared.request["request_digest"], ATTEMPT_ID, reason_code="local_contracts_valid")
        if mode == "dry-run":
            return BootstrapRunResult("dry-run", "ready", prepared.request["request_digest"], ATTEMPT_ID, reason_code="no_effectful_call_performed")
        _require(self.ledger is not None, "one-attempt bootstrap ledger is required")
        try:
            adapter = ReviewedConfidentialSpaceAdapterFactory().build(prepared)
        except Exception as exc:
            raise BootstrapRunnerError("reviewed adapter factory failed closed") from exc
        _require(type(adapter) is ConfidentialSpaceAdapter, "Confidential Space adapter is required")
        _require(isinstance(adapter.capability_factory, CredentialOnlyCapabilityFactory), "credential-only capability factory is required")
        try:
            self.ledger.reserve(
                attempt_id=ATTEMPT_ID,
                packet_digest=prepared.request["request_digest"],
                packet_path=canonical_packet_path,
                execution_request_digest=prepared.execution_request.request_digest,
            )
        except AttemptLedgerError:
            raise
        except Exception as exc:
            raise AttemptLedgerError("bootstrap attempt could not be reserved") from exc
        try:
            receipt = bootstrap_credentials(
                adapter=adapter,
                authority=prepared.bindings.authority,
                kms=prepared.bindings.kms,
                capability_binding=prepared.bindings.capability_binding,
                request=prepared.execution_request.as_public_dict(),
                child_approval=prepared.approval,
            )
            validate_receipt(
                receipt,
                now=_verifier_now(),
                packet_digest=prepared.request["request_digest"],
                packet_path=canonical_packet_path,
                request_digest=prepared.execution_request.request_digest,
                approval_digest=prepared.approval.approval_digest,
            )
            self.ledger.complete(
                packet_digest=prepared.request["request_digest"],
                packet_path=canonical_packet_path,
                execution_request_digest=prepared.execution_request.request_digest,
                receipt_digest=receipt.receipt_digest,
            )
        except Exception as exc:
            try:
                self.ledger.fail(
                    packet_digest=prepared.request["request_digest"],
                    packet_path=canonical_packet_path,
                    execution_request_digest=prepared.execution_request.request_digest,
                    reason=type(exc).__name__,
                )
            except Exception as ledger_exc:
                raise AttemptLedgerError("bootstrap failed and attempt ledger could not be closed") from ledger_exc
            if isinstance(exc, (BootstrapRunnerError, CredentialProcessError)):
                raise
            raise BootstrapRunnerError("Confidential Space bootstrap failed closed") from exc
        return BootstrapRunResult(
            "effectful", "completed", prepared.request["request_digest"], ATTEMPT_ID,
            receipt=receipt, ledger_digest=self.ledger.ledger_digest, reason_code="credential_bootstrap_complete",
        )


__all__ = [
    "APPROVAL_018_CHILD_APPROVAL_ARTIFACT_DIGEST", "APPROVAL_018_CHILD_APPROVAL_PATH",
    "APPROVAL_018_REQUEST_DIGEST", "APPROVAL_018_REQUEST_PATH", "APPROVAL_ID",
    "ATTEMPT_ID", "AttemptLedger", "AttemptLedgerError", "BootstrapRunResult",
    "BootstrapRunnerError", "CANONICAL_PACKET_PATH", "CHILD_APPROVAL_PATH", "DISPATCH_ID",
    "FileAttemptLedger", "MemoryAttemptLedger", "PreparedBootstrap", "ReviewedBootstrapBindings",
    "ReviewedBootstrapRunner", "ReviewedConfidentialSpaceAdapterFactory", "RUNNER_VERSION",
    "prepare_bootstrap",
]
