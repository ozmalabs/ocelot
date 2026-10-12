"""Unified, fail-closed DISPATCH-066 Track A orchestration.

This module is deliberately an interface boundary.  It does not create cloud
clients, timing records, worker observations, signatures, or generated input.
A verifier-owned adapter supplies those capabilities only after attestation.
The runner accepts protocol objects, never caller callbacks or local evidence
booleans, and returns a redacted typed result when an external gate is absent.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable

from .attestation_binding import VerifiedAttestationBinding, _is_registered_attestation_binding
from .canonical import b64decode, digest
from evaluation.p0a.canonical import object_hash, verify_signature
from evaluation.p5_r0.receipts import ReceiptChain
from .signing import KMSEd25519Signer, VerifierIssuedKMSCapability
from .time_seed import TimeSeededInput, derive_time_seed, time_seed_algorithm_binding
from .input_builder import input_builder_binding
from .deploy.iam_predecessor import VerifiedIAMPredecessor, validate_verified_iam_predecessor

from evaluation.p5_r0.native_worker import validate_reply_v3, validate_task
from evaluation.p5_r0.rs050_contract import validate_rs050_evidence


TRACK_A_RESULT_SCHEMA = "P5R0TrackAResultV1"
TRACK_A_SELECTION_SCHEMA = "P5R0TrackAMVPSelectionV1"
TRACK_A_PROVISION_SCHEMA = "P5R0TrackAProvisionedInputsV1"
TRACK_A_REHYDRATION_SCHEMA = "P5R0TrackARehydratedInputsV1"
TRACK_A_FINAL_BINDING_SCHEMA = "P5R0TrackAFinalBindingV1"
TRACK_A_TASK_SCHEMA = "P5R0TrackATaskEnvelopeV1"
TRACK_A_RECEIPT_SCHEMA = "P5R0TrackAReceiptVerificationV2"
TRACK_A_IMPASSE_SEAL_SCHEMA = "P5R0TrackAImpasseSealV1"
TRACK_A_ACTIVATION_SCHEMA = "P5R0TrackACapabilityActivationV1"
_TRACK_A_CLAIM_BOUNDARY = (
    "Self-custodied Track A diagnostic only; no independent evaluator, release, "
    "adoption, positive transfer, exact CPU timing, or general-intelligence claim."
)
class TrackAError(RuntimeError):
    """A Track A contract failed closed."""


class TrackABlocked(TrackAError):
    """A required external or pre-execution gate was unavailable."""


@dataclass(frozen=True)
class TrackAResult:
    """Redacted typed public outcome; private evidence stays behind adapters."""

    status: str
    disposition: str
    stage: str
    reason_code: str
    run_id: str | None = None
    result_digest: str | None = None
    result_seal_digest: str | None = None
    final_binding_digest: str | None = None
    final_signature: str | None = None
    attestation_binding_digest: str | None = None
    timing_record_digest: str | None = None
    input_seed_digest: str | None = None
    input_digest: str | None = None
    public_input_digest: str | None = None
    access_binding_digest: str | None = None
    receipt_chain_digest: str | None = None
    closure_digest: str | None = None
    supervisor_commitment_digest: str | None = None
    kms_authority_commitment_digest: str | None = None
    kms_key_version: str | None = None
    kms_transport_commitment_digest: str | None = None
    production_promotable: bool = False
    rollback_digest: str | None = None
    closure_receipt_digest: str | None = None
    impasse_seal_digest: str | None = None
    publication: Mapping[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema": TRACK_A_RESULT_SCHEMA,
            "status": self.status,
            "disposition": self.disposition,
            "stage": self.stage,
            "reason_code": self.reason_code,
            "run_id": self.run_id,
            "result_digest": self.result_digest,
            "result_seal_digest": self.result_seal_digest,
            "final_binding_digest": self.final_binding_digest,
            "final_signature": self.final_signature,
            "attestation_binding_digest": self.attestation_binding_digest,
            "timing_record_digest": self.timing_record_digest,
            "input_seed_digest": self.input_seed_digest,
            "input_digest": self.input_digest,
            "public_input_digest": self.public_input_digest,
            "access_binding_digest": self.access_binding_digest,
            "receipt_chain_digest": self.receipt_chain_digest,
            "closure_digest": self.closure_digest,
            "supervisor_commitment_digest": self.supervisor_commitment_digest,
            "kms_authority_commitment_digest": self.kms_authority_commitment_digest,
            "kms_key_version": self.kms_key_version,
            "kms_transport_commitment_digest": self.kms_transport_commitment_digest,
            "production_promotable": self.production_promotable,
            "rollback_digest": self.rollback_digest,
            "closure_receipt_digest": self.closure_receipt_digest,
            "impasse_seal_digest": self.impasse_seal_digest,
            "claim_boundary": _TRACK_A_CLAIM_BOUNDARY,
        }
        if self.publication is not None:
            value["publication"] = dict(self.publication)
        return value


@dataclass(frozen=True)
class TrackASelection:
    """The immutable, explicitly selected one-task/one-control MVP contract."""

    lock_digest: str
    manifest_digest: str
    worker_contract_digest: str
    case_id: str
    case_digest: str
    ordinal: int
    arm: str = "cold_reset"
    control_id: str = "illegal_action"
    task_schema: str = "P5R0WorkerTaskV3"

    def validate(self) -> None:
        for name in ("lock_digest", "manifest_digest", "worker_contract_digest", "case_digest"):
            value = getattr(self, name)
            if not _is_digest(value):
                raise TrackAError(f"selection_{name}")
        if not isinstance(self.case_id, str) or not self.case_id or len(self.case_id) > 256:
            raise TrackAError("selection_case_id")
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise TrackAError("selection_ordinal")
        if self.arm != "cold_reset" or self.control_id != "illegal_action":
            raise TrackAError("selection_mvp_contract")
        if self.task_schema != "P5R0WorkerTaskV3":
            raise TrackAError("selection_task_schema")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        value = {
            "schema": TRACK_A_SELECTION_SCHEMA,
            "lock_digest": self.lock_digest,
            "manifest_digest": self.manifest_digest,
            "worker_contract_digest": self.worker_contract_digest,
            "case_id": self.case_id,
            "case_digest": self.case_digest,
            "ordinal": self.ordinal,
            "arm": self.arm,
            "control_id": self.control_id,
            "task_schema": self.task_schema,
        }
        value["selection_digest"] = digest(value)
        return value


@dataclass(frozen=True)
class TrackAConfig:
    selection: TrackASelection
    input_namespace: str
    iam_predecessor: VerifiedIAMPredecessor | None = None

    def validate(self) -> None:
        self.selection.validate()
        if not isinstance(self.input_namespace, str) or not self.input_namespace or len(self.input_namespace) > 256:
            raise TrackAError("input_namespace")
        try:
            validate_verified_iam_predecessor(self.iam_predecessor, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9")
        except Exception as exc:
            raise TrackAError("verified_iam_predecessor_required") from exc


class VerifierIssuedSupervisorCapability:
    """Opaque verifier capability for authenticating supervisor evidence."""
    __slots__ = ("_commitment", "_token", "_observation", "_resource")
    _TOKEN = object()

    def __init__(self, commitment: Mapping[str, Any], observation: Any, resource: Any, token: object):
        if token is not self._TOKEN:
            raise TrackAError("verifier-issued supervisor capability required")
        if not callable(observation) or not callable(resource):
            raise TrackAError("supervisor capability validators required")
        self._commitment = dict(commitment)
        self._observation = observation
        self._resource = resource
        self._token = token

    @property
    def commitment(self) -> Mapping[str, Any]:
        return dict(self._commitment)

    def authenticate(self, evidence: Mapping[str, Any], resource_claim: Mapping[str, Any]) -> Mapping[str, Any]:
        if self._observation(evidence) is not True or self._resource(resource_claim) is not True:
            raise TrackAError("supervisor evidence authentication")
        return {
            "schema": "P5R0TrackASupervisorAuthenticationV1",
            "evidence_digest": digest(dict(evidence)),
            "capability_digest": self._commitment.get("capability_digest"),
            "authenticated": True,
            "promotable": True,
        }


def issue_verifier_supervisor_capability(*, issuer: str, commitment: Mapping[str, Any], observation: Any, resource: Any) -> VerifierIssuedSupervisorCapability:
    """Factory for a verifier-owned adapter; local fixtures remain structural."""
    if not issuer or not isinstance(commitment, Mapping):
        raise TrackAError("supervisor capability inputs")
    value = dict(commitment)
    value.setdefault("schema", "P5R0TrackASupervisorCapabilityV1")
    value.setdefault("issuer", issuer)
    value.setdefault("capability_digest", digest({key: child for key, child in value.items() if key != "capability_digest"}))
    return VerifierIssuedSupervisorCapability(value, observation, resource, VerifierIssuedSupervisorCapability._TOKEN)


@dataclass(frozen=True)
class TrackACapabilities:
    """Capabilities constructed by a verifier-owned adapter after attestation."""

    execution: "TrackAExecution"
    worker: "TrackAWorker"
    supervisor: VerifierIssuedSupervisorCapability
    signer: "TrackASigner"
    seal_store: "TrackASealStore"
    input_builder: "TrackAInputBuilder"
    timing_verifier: "TrackATimingVerifier"
    closure: Mapping[str, Any]
    attestation_binding: VerifiedAttestationBinding
    publisher: "TrackAPublisher | None" = None
    activation_commitment: Mapping[str, Any] | None = None
    production_promotable: bool = False


@runtime_checkable
class TrackAInputBuilder(Protocol):
    binding: Mapping[str, Any]

    def build(self, input_seed_digest: str) -> Mapping[str, Any]: ...


@runtime_checkable
class TrackATimingVerifier(Protocol):
    def verify(self, record: Mapping[str, Any], *, run_id: str, event: str) -> Mapping[str, Any]: ...


@runtime_checkable
class TrackAWorker(Protocol):
    def preflight(self, closure: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def execute(self, task: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]: ...


@runtime_checkable
class TrackASigner(Protocol):
    authority: Mapping[str, Any]

    def sign_digest(self, message_digest: bytes) -> str: ...


@runtime_checkable
class TrackASealStore(Protocol):
    def create(self, result: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def persist(self, run_id: str, seal: Mapping[str, Any]) -> None: ...

    def read(self, run_id: str) -> Mapping[str, Any]: ...

    def verify(self, result: Mapping[str, Any], seal: Mapping[str, Any]) -> Mapping[str, Any]: ...


@runtime_checkable
class TrackAPublisher(Protocol):
    def publish(self, signed_result: Mapping[str, Any]) -> Mapping[str, Any]: ...


@runtime_checkable
class TrackAExecution(Protocol):
    def start(self, selection: TrackASelection, inputs: Mapping[str, Any]) -> str: ...

    def acquire_timing_record(self, run_id: str, namespace: str) -> Mapping[str, Any]: ...

    def issue_task(self, run_id: str, selection: TrackASelection, seeded: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def submit_task(self, run_id: str, task: Mapping[str, Any], reply: Mapping[str, Any], evidence: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def issue_control(self, run_id: str, selection: TrackASelection, seeded: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def submit_control(self, run_id: str, task: Mapping[str, Any], reply: Mapping[str, Any], evidence: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def verify_receipts(self, run_id: str) -> Mapping[str, Any]: ...

    def rollback(self, run_id: str) -> Mapping[str, Any]: ...

    def create_result(self, run_id: str, selection: TrackASelection, task_outcome: Mapping[str, Any], control_outcome: Mapping[str, Any], evidence: Mapping[str, Any], receipts: Mapping[str, Any], rollback: Mapping[str, Any], attestation: Mapping[str, Any], seeded: TimeSeededInput) -> Mapping[str, Any]: ...


@runtime_checkable
class TrackAAdapter(Protocol):
    """The only runner entry boundary; implementations own real attestation.

    ``activate_attested_capabilities`` receives a closed commitment containing
    the verifier-validated attestation, immutable selection, and every input
    delivery commitment.  An adapter must independently verify that map before
    constructing or exposing capabilities; the runner also verifies the
    returned capability echo.
    """

    def provision_inputs(self, selection: TrackASelection) -> Mapping[str, Any]: ...

    def activate_attested_capabilities(self, activation_commitment: Mapping[str, Any]) -> TrackACapabilities: ...

    def read_and_rehydrate_inputs(self, provisioned: Mapping[str, Any]) -> Mapping[str, Any]: ...

    @property
    def attestation_binding(self) -> VerifiedAttestationBinding: ...

    @property
    def startup_evidence(self) -> Mapping[str, Any]: ...


class _Stop(Exception):
    def __init__(self, stage: str, code: str):
        super().__init__(code)
        self.stage = stage
        self.code = code


def _is_digest(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        return False
    return all(char in "0123456789abcdef" for char in value[7:])


def _require_mapping(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _Stop("contract", code)
    return value


def _validate_provisioned(value: Any, selection: TrackASelection) -> Mapping[str, Any]:
    value = _require_mapping(value, "provisioning_shape")
    fields = {"schema", "status", "lock_digest", "manifest_digest", "public_input_digest", "private_store_digest", "access_binding_digest", "provisioning_digest"}
    if set(value) != fields or value.get("schema") != TRACK_A_PROVISION_SCHEMA or value.get("status") != "provisioned":
        raise _Stop("provisioning", "provisioning_shape")
    if value.get("lock_digest") != selection.lock_digest or value.get("manifest_digest") != selection.manifest_digest:
        raise _Stop("provisioning", "provisioning_commitment")
    for key in fields - {"schema", "status"}:
        if not _is_digest(value.get(key)):
            raise _Stop("provisioning", "provisioning_digest")
    expected = digest({key: value[key] for key in fields if key != "provisioning_digest"})
    if value["provisioning_digest"] != expected:
        raise _Stop("provisioning", "provisioning_digest")
    return value


def _activation_commitment(selection: TrackASelection, provisioned: Mapping[str, Any], attestation: Mapping[str, Any], iam_predecessor: VerifiedIAMPredecessor) -> dict[str, Any]:
    selection_value = selection.as_dict()
    predecessor = validate_verified_iam_predecessor(iam_predecessor, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9")
    value = {
        "schema": TRACK_A_ACTIVATION_SCHEMA,
        "lock_digest": selection.lock_digest,
        "manifest_digest": selection.manifest_digest,
        "worker_contract_digest": selection.worker_contract_digest,
        "selection": selection_value,
        "selection_digest": digest(selection_value),
        "public_input_digest": provisioned["public_input_digest"],
        "private_store_digest": provisioned["private_store_digest"],
        "access_binding_digest": provisioned["access_binding_digest"],
        "attestation_binding_digest": attestation["binding_digest"],
        "provisioning_digest": provisioned["provisioning_digest"],
        "iam_receipt_digest": predecessor.receipt_digest,
        "iam_ledger_head_digest": predecessor.ledger_head_digest,
        "iam_poststate_digest": predecessor.poststate_digest,
        "iam_predecessor_digest": predecessor.capability_digest,
    }
    value["commitment_digest"] = digest(value)
    return value


def _validate_activation_commitment(value: Any, expected: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(expected) or dict(value) != dict(expected):
        raise _Stop("attestation", "capability_activation_commitment")
    if value.get("schema") != TRACK_A_ACTIVATION_SCHEMA or value.get("commitment_digest") != digest({key: item for key, item in value.items() if key != "commitment_digest"}):
        raise _Stop("attestation", "capability_activation_commitment")
    return dict(value)


def _validate_rehydrated(value: Any, provisioned: Mapping[str, Any]) -> Mapping[str, Any]:
    value = _require_mapping(value, "rehydration_shape")
    fields = {"schema", "status", "lock_digest", "manifest_digest", "public_input_digest", "private_store_digest", "access_binding_digest", "rehydration_digest"}
    if set(value) != fields or value.get("schema") != TRACK_A_REHYDRATION_SCHEMA or value.get("status") != "verified_fresh_process":
        raise _Stop("rehydration", "rehydration_shape")
    for key in fields - {"schema", "status", "rehydration_digest"}:
        if not _is_digest(value.get(key)):
            raise _Stop("rehydration", "rehydration_digest")
        if value.get(key) != provisioned.get(key):
            raise _Stop("rehydration", "rehydration_commitment")
    if not _is_digest(value.get("rehydration_digest")):
        raise _Stop("rehydration", "rehydration_digest")
    if value["rehydration_digest"] != digest({key: value[key] for key in fields if key != "rehydration_digest"}):
        raise _Stop("rehydration", "rehydration_digest")
    return value


def _validate_authority(signer: TrackASigner) -> Mapping[str, Any]:
    if not isinstance(signer, KMSEd25519Signer):
        raise _Stop("signing", "kms_signer_required")
    authority = getattr(signer, "authority", None)
    if not isinstance(authority, Mapping):
        raise _Stop("signing", "authority_missing")
    required = {"schema", "authority_id", "key_id", "public_key", "public_key_digest", "transport_attestation"}
    if set(authority) != required or authority.get("schema") not in {"P5R0AuthorityV3", "P5R0PublicAuthorityV4"}:
        raise _Stop("signing", "authority_shape")
    if not isinstance(authority.get("authority_id"), str) or not isinstance(authority.get("key_id"), str):
        raise _Stop("signing", "authority_identity")
    if not _is_digest(authority.get("public_key_digest")) or digest(authority.get("public_key")) != authority.get("public_key_digest"):
        raise _Stop("signing", "authority_digest")
    try:
        public = b64decode(str(authority["public_key"]))
    except Exception as exc:
        raise _Stop("signing", "authority_key") from exc
    if len(public) != 32:
        raise _Stop("signing", "authority_key")
    capability = getattr(signer, "verifier_capability", None)
    if not isinstance(capability, VerifierIssuedKMSCapability):
        raise _Stop("signing", "kms_capability_required")
    try:
        capability_commitment = capability.commitment
    except Exception as exc:
        raise _Stop("signing", "kms_capability_required") from exc
    required_capability_fields = {"schema", "issuer", "authority_id", "key_id", "key_version", "public_key_digest", "transport_digest", "capability_digest"}
    if (set(capability_commitment) != required_capability_fields
            or capability_commitment.get("schema") != "P5R0VerifierKMSCapabilityV1"
            or not isinstance(capability_commitment.get("issuer"), str) or not capability_commitment.get("issuer")
            or capability_commitment.get("capability_digest") != digest({key: value for key, value in capability_commitment.items() if key != "capability_digest"})):
        raise _Stop("signing", "kms_capability_commitment")
    if not capability.matches(key_version=getattr(signer, "key_version", ""), authority=dict(authority)):
        raise _Stop("signing", "kms_capability_required")
    return authority


def _kms_authority_commitment(signer: TrackASigner, authority: Mapping[str, Any]) -> dict[str, Any]:
    key_version = getattr(signer, "key_version", None)
    transport = authority.get("transport_attestation")
    value = {
        "schema": "P5R0KMSAuthorityCommitmentV1",
        "authority_id": authority.get("authority_id"),
        "key_id": authority.get("key_id"),
        "key_version": key_version,
        "public_key_digest": authority.get("public_key_digest"),
        "transport_digest": digest(transport),
    }
    value["commitment_digest"] = digest(value)
    return value


def _validate_attestation(adapter: TrackAAdapter, selection: TrackASelection) -> Mapping[str, Any]:
    # This is intentionally a separate gate from capability construction.  A
    # protocol-shaped adapter cannot activate anything until the runner has
    # observed the adapter-created, registry-sealed binding and matching
    # startup evidence.
    binding = getattr(adapter, "attestation_binding", None)
    if type(binding) is not VerifiedAttestationBinding or not _is_registered_attestation_binding(binding):
        raise _Stop("attestation", "attestation_binding_unavailable")
    evidence = _require_mapping(getattr(adapter, "startup_evidence", None), "attestation_evidence")
    required = {"schema", "status", "policy_digest", "claim_paths_digest", "attestation_claims_digest", "wip_policy_digest", "attestation", "federation", "capabilities"}
    if set(evidence) != required or evidence.get("schema") != "P5R0StartupAttestationEvidenceV1" or evidence.get("status") != "attested":
        raise _Stop("attestation", "attestation_unavailable")
    for field in ("policy_digest", "claim_paths_digest", "attestation_claims_digest", "wip_policy_digest"):
        if evidence.get(field) != getattr(binding, field):
            raise _Stop("attestation", "attestation_binding_mismatch")
    attestation = evidence.get("attestation")
    federation = evidence.get("federation")
    if (not isinstance(attestation, Mapping) or attestation.get("verified") is not True
            or attestation.get("binding_digest") != binding.binding_digest
            or attestation.get("claims_digest") != binding.claims_digest
            or not isinstance(federation, Mapping) or federation.get("exchanged") is not True
            or federation.get("access_token_digest") != binding.federated_token_digest
            or evidence.get("capabilities") != "constructed_after_attestation"):
        raise _Stop("attestation", "attestation_binding_mismatch")
    if not _is_digest(binding.image_digest) or not _is_digest(binding.binding_digest):
        raise _Stop("attestation", "attestation_image_binding")
    return {"startup_evidence_digest": digest(dict(evidence)), "binding_digest": binding.binding_digest, "image_digest": binding.image_digest, "claims_digest": binding.claims_digest,
            "policy_digest": binding.policy_digest, "claim_paths_digest": binding.claim_paths_digest,
            "attestation_claims_digest": binding.attestation_claims_digest, "wip_policy_digest": binding.wip_policy_digest}


def _validate_timing(verifier: TrackATimingVerifier, record: Mapping[str, Any], run_id: str) -> Mapping[str, Any]:
    if not isinstance(verifier, TrackATimingVerifier):
        raise _Stop("timing", "timing_verifier_interface")
    try:
        verified = verifier.verify(record, run_id=run_id, event="task_issued")
    except Exception as exc:
        raise _Stop("timing", "timing_proof_unavailable") from exc
    if (not isinstance(verified, Mapping) or verified.get("status") != "verified"
            or verified.get("record_digest") != digest(dict(record))
            or not _is_digest(verified.get("authority_digest"))):
        raise _Stop("timing", "timing_proof_unverified")
    return dict(verified)


def _validate_closure(closure: Mapping[str, Any], image_digest: str) -> None:
    required = {"schema", "bound", "image_ref", "image_digest", "entrypoint", "files", "worker_digest", "runtime_path", "runtime_digest", "closure_digest", "seccomp_profile", "seccomp_digest", "argv_digest", "limits", "runtime", "network", "pull", "worker_contract"}
    allowed_extra = {"worker_path", "architecture", "seccomp_default_action", "allowed_syscalls", "allowed_syscalls_digest"}
    if not required.issubset(set(closure)) or set(closure) - required - allowed_extra or closure.get("schema") != "P5R0ClosureBindingV3" or closure.get("bound") is not True:
        raise _Stop("attestation", "closure_binding")
    if closure.get("image_digest") != image_digest or not isinstance(closure.get("image_ref"), str) or not closure["image_ref"].endswith("@" + image_digest):
        raise _Stop("attestation", "closure_image_binding")
    if closure.get("entrypoint") != "/runtime/p5_r0_worker" or closure.get("runtime") != "crun" or closure.get("network") != "none" or closure.get("pull") != "never" or closure.get("worker_contract") != "P5R0WorkerContractV3":
        raise _Stop("attestation", "closure_posture")
    if not isinstance(closure.get("files"), Mapping) or not closure["files"] or any(not _is_digest(value) for value in closure["files"].values()):
        raise _Stop("attestation", "closure_files")
    if "allowed_syscalls" in closure and (not isinstance(closure["allowed_syscalls"], list) or not closure["allowed_syscalls"] or closure.get("allowed_syscalls_digest") != digest(closure["allowed_syscalls"])):
        raise _Stop("attestation", "closure_syscalls")
    for key in ("worker_digest", "runtime_digest", "closure_digest", "seccomp_digest", "argv_digest"):
        if not _is_digest(closure.get(key)):
            raise _Stop("attestation", "closure_digest")
    if not isinstance(closure.get("limits"), Mapping) or set(closure["limits"]) != {"steps", "frame_bytes", "wall_seconds", "memory_mb", "cpu", "pids"}:
        raise _Stop("attestation", "closure_limits")
    if any(type(closure["limits"][key]) is not int or closure["limits"][key] <= 0 for key in closure["limits"]):
        raise _Stop("attestation", "closure_limits")


def _validate_task(value: Any, selection: TrackASelection, *, control: bool, expected_run_id: str) -> Mapping[str, Any]:
    value = _require_mapping(value, "task_shape")
    fields = {"schema", "run_id", "task_id", "sequence", "case_id", "case_digest", "ordinal", "arm", "task", "task_digest", "control_id"}
    if set(value) != fields or value.get("schema") != TRACK_A_TASK_SCHEMA:
        raise _Stop("task", "task_shape")
    if value.get("case_id") != selection.case_id or value.get("case_digest") != selection.case_digest or value.get("ordinal") != selection.ordinal or value.get("arm") != selection.arm:
        raise _Stop("task", "task_selection_mismatch")
    if value.get("control_id") != (selection.control_id if control else None):
        raise _Stop("control" if control else "task", "task_control_mismatch")
    if value.get("run_id") != expected_run_id:
        raise _Stop("control" if control else "task", "task_run_mismatch")
    if not _is_digest(value.get("run_id")) or not _is_digest(value.get("task_id")) or not _is_digest(value.get("task_digest")):
        raise _Stop("task", "task_identity")
    task = value.get("task")
    if not isinstance(task, Mapping) or task.get("schema") != selection.task_schema or task.get("arm") != selection.arm:
        raise _Stop("task", "task_protocol")
    inner_control = task.get("control")
    if control:
        if not isinstance(inner_control, Mapping) or inner_control.get("control_id") != selection.control_id:
            raise _Stop("control", "illegal_action_contract")
    elif inner_control is not None:
        raise _Stop("task", "unexpected_control")
    try:
        validate_task(dict(task))
    except Exception as exc:
        raise _Stop("task", "task_protocol") from exc
    if digest(dict(task)) != value.get("task_digest"):
        raise _Stop("task", "task_digest")
    return value


def _validate_execution(worker: TrackAWorker, supervisor: VerifierIssuedSupervisorCapability, closure: Mapping[str, Any], task: Mapping[str, Any], *, lock_digest: str, expected_run_id: str, control: bool) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    if not isinstance(worker, TrackAWorker) or not callable(getattr(worker, "execute", None)) or not callable(getattr(worker, "preflight", None)):
        raise _Stop("native", "worker_interface")
    if not isinstance(supervisor, VerifierIssuedSupervisorCapability):
        raise _Stop("native", "supervisor_capability_required")
    commitment = supervisor.commitment
    if (set(commitment) != {"schema", "authority_id", "issuer", "capability_digest"}
            or commitment.get("schema") != "P5R0TrackASupervisorCapabilityV1"
            or not isinstance(commitment.get("issuer"), str) or not commitment.get("issuer")
            or not isinstance(commitment.get("authority_id"), str)
            or commitment.get("capability_digest") != digest({key: value for key, value in commitment.items() if key != "capability_digest"})):
        raise _Stop("native", "supervisor_capability_commitment")
    try:
        preflight = worker.preflight(closure)
    except Exception as exc:
        raise _Stop("native", "closure_preflight") from exc
    if (not isinstance(preflight, Mapping) or preflight.get("schema") != "P5R0TrackAClosurePreflightV1"
            or preflight.get("status") != "verified" or preflight.get("closure_digest") != closure.get("closure_digest")
            or preflight.get("preflight_digest") != digest({key: preflight[key] for key in preflight if key != "preflight_digest"})):
        raise _Stop("native", "closure_preflight")
    try:
        reply, evidence = worker.execute(task)
    except Exception as exc:
        raise _Stop("native", "worker_execution_unavailable") from exc
    if not isinstance(reply, Mapping) or not isinstance(evidence, Mapping):
        raise _Stop("native", "worker_result_shape")
    try:
        validate_reply_v3(dict(reply), dict(task["task"]), allow_invalid=control)
    except Exception as exc:
        raise _Stop("native", "worker_reply") from exc
    if control:
        action = reply.get("action")
        legal = task["task"].get("legal_actions", [])
        if action is None or action in legal:
            raise _Stop("control", "illegal_action_not_rejected")
    try:
        validate_rs050_evidence(evidence)
        resource_claim = {
            "schema": "P5R0RS050ResourceClaimV1",
            "run_id": expected_run_id,
            "lock_digest": lock_digest,
            "closure_digest": closure.get("closure_digest"),
            "resource_profile_digest": evidence.get("resource_profile_digest"),
            "evidence_digest": evidence.get("evidence_digest"),
        }
        report = supervisor.authenticate(evidence, resource_claim)
    except Exception as exc:
        raise _Stop("native", "supervisor_evidence_unavailable") from exc
    if (not isinstance(report, Mapping) or report.get("schema") != "P5R0TrackASupervisorAuthenticationV1"
            or report.get("authenticated") is not True or report.get("promotable") is not True
            or report.get("evidence_digest") != digest(dict(evidence))
            or report.get("capability_digest") != supervisor.commitment.get("capability_digest")):
        raise _Stop("native", "supervisor_evidence_unavailable")
    if evidence.get("run_id") != expected_run_id:
        raise _Stop("native", "supervisor_run_mismatch")
    invocations = evidence.get("invocations")
    if not isinstance(invocations, list) or len(invocations) != 1:
        raise _Stop("native", "worker_invocation_count")
    invocation = invocations[0]
    if (invocation.get("run_id") != task.get("run_id")
            or invocation.get("task_id") != task.get("task_id")
            or invocation.get("lock_digest") != lock_digest
            or invocation.get("closure_digest") != closure.get("closure_digest")
            or invocation.get("sequence") != 1):
        raise _Stop("native", "supervisor_task_binding")
    if len(invocations) != 1:
        raise _Stop("native", "worker_invocation_count")
    report = dict(report)
    report["worker_invocations"] = 1
    return dict(reply), dict(evidence), report


def _signature_bytes(value: str) -> bytes:
    try:
        result = b64decode(value)
    except Exception as exc:
        raise _Stop("signing", "final_signature_shape") from exc
    if len(result) != 64:
        raise _Stop("signing", "final_signature_shape")
    return result


def _verify_signature(signer: TrackASigner, message_digest: str, signature: str) -> None:
    authority = _validate_authority(signer)
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        public = b64decode(str(authority["public_key"]))
        Ed25519PublicKey.from_public_bytes(public).verify(_signature_bytes(signature), bytes.fromhex(message_digest[7:]))
    except _Stop:
        raise
    except Exception as exc:
        raise _Stop("signing", "final_signature_invalid") from exc


def _validate_receipts(value: Mapping[str, Any], task: Mapping[str, Any], control: Mapping[str, Any], *, run_id: str, timing_record_digest: str, closure_digest: str) -> Mapping[str, Any]:
    fields = {"schema", "status", "run_id", "chain_digest", "task_digest", "control_digest", "timing_record_digest", "closure_digest", "result_digest", "authority_id", "key_id", "public_key", "public_key_digest", "records", "records_digest"}
    if set(value) != fields or value.get("schema") != TRACK_A_RECEIPT_SCHEMA or value.get("status") != "verified":
        raise _Stop("receipts", "receipt_chain_unverified")
    if value.get("run_id") != run_id or value.get("task_digest") != task.get("task_digest") or value.get("control_digest") != control.get("task_digest"):
        raise _Stop("receipts", "receipt_coverage")
    for key in ("chain_digest", "timing_record_digest", "closure_digest", "result_digest", "public_key_digest"):
        if not _is_digest(value.get(key)):
            raise _Stop("receipts", "receipt_chain_shape")
    if value.get("timing_record_digest") != timing_record_digest or value.get("closure_digest") != closure_digest:
        raise _Stop("receipts", "receipt_commitment_mismatch")
    if not isinstance(value.get("authority_id"), str) or not isinstance(value.get("key_id"), str) or not isinstance(value.get("public_key"), str):
        raise _Stop("receipts", "receipt_authority_shape")
    if not isinstance(value.get("records"), list) or not value["records"] or value["records_digest"] != digest(value["records"]):
        raise _Stop("receipts", "receipt_chain_digest")
    try:
        public_bytes = b64decode(value["public_key"])
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        public = Ed25519PublicKey.from_public_bytes(public_bytes)
    except Exception as exc:
        raise _Stop("receipts", "receipt_authority_key") from exc
    if digest(value["public_key"]) != value["public_key_digest"]:
        raise _Stop("receipts", "receipt_authority_digest")
    previous = None
    kinds: set[str] = set()
    for sequence, record in enumerate(value["records"], 1):
        if not isinstance(record, Mapping) or set(record) != {"schema", "sequence", "previous_hash", "payload", "receipt_hash", "signature"}:
            raise _Stop("receipts", "receipt_record_shape")
        if record["schema"] != "P5R0ReceiptV3" or record["sequence"] != sequence or record["previous_hash"] != previous:
            raise _Stop("receipts", "receipt_sequence")
        if record["receipt_hash"] != object_hash(dict(record), "receipt_hash", "signature"):
            raise _Stop("receipts", "receipt_hash")
        try:
            verify_signature(dict(record), public, "receipt_hash")
        except Exception as exc:
            raise _Stop("receipts", "receipt_signature") from exc
        payload = record.get("payload")
        binding = payload.get("binding") if isinstance(payload, Mapping) else None
        if (not isinstance(payload, Mapping) or payload.get("schema") != "P5R0ReceiptPayloadV3"
                or payload.get("run_id") != run_id or not isinstance(binding, Mapping)
                or binding.get("closure_digest") != closure_digest
                or binding.get("timing_record_digest") != timing_record_digest
                or binding.get("result_digest") != value["result_digest"]):
            raise _Stop("receipts", "receipt_link_mismatch")
        if sequence == 1:
            if (payload.get("kind") != "preregistered" or binding.get("authority_id") != value["authority_id"]
                    or binding.get("key_id") != value["key_id"] or binding.get("public_key_digest") != value["public_key_digest"]):
                raise _Stop("receipts", "receipt_authority_binding")
        else:
            if binding.get("preregistration_receipt_hash") != value["records"][0]["receipt_hash"]:
                raise _Stop("receipts", "receipt_preregistration_link")
        kind = payload.get("kind")
        if kind not in {"preregistered", "start", "timing", "task", "control", "result", "rollback", "close", "impasse"}:
            raise _Stop("receipts", "receipt_kind")
        kinds.add(kind)
        if kind == "task" and binding.get("task_digest") != task.get("task_digest"):
            raise _Stop("receipts", "receipt_task_link")
        if kind == "control" and binding.get("task_digest") != control.get("task_digest"):
            raise _Stop("receipts", "receipt_control_link")
        previous = record["receipt_hash"]
    if value["chain_digest"] != digest(value["records"]):
        raise _Stop("receipts", "receipt_chain_digest")
    if not {"preregistered", "start", "timing", "task", "control", "result", "rollback", "close"}.issubset(kinds):
        raise _Stop("receipts", "receipt_closure")
    return dict(value)


def _canonical_result_digest(value: Mapping[str, Any]) -> str:
    """Digest the result payload without its separately bound receipt chain head."""
    return digest({key: item for key, item in value.items() if key != "receipt_chain_digest"})


def _validate_seal(seal: Mapping[str, Any], *, run_id: str, result_digest: str, chain_digest: str) -> None:
    fields = {"schema", "run_id", "result_digest", "chain_digest", "seal_digest"}
    if set(seal) != fields or seal.get("schema") != "P5R0TrackAResultSealV1" or seal.get("run_id") != run_id or seal.get("result_digest") != result_digest or seal.get("chain_digest") != chain_digest:
        raise _Stop("seal", "result_seal_binding")
    if seal.get("seal_digest") != digest({key: seal[key] for key in fields if key != "seal_digest"}):
        raise _Stop("seal", "result_seal_digest")


def _validate_failure_closure(value: Mapping[str, Any], *, run_id: str) -> Mapping[str, Any]:
    if set(value) != {"schema", "run_id", "status", "rollback_digest", "receipt_chain_digest", "receipt_chain", "closure_receipt", "impasse_seal"}:
        raise _Stop("rollback", "rollback_closure_shape")
    if value.get("schema") != "P5R0TrackAFailureClosureV1" or value.get("run_id") != run_id or value.get("status") != "exact":
        raise _Stop("rollback", "rollback_closure_unverified")
    for key in ("rollback_digest", "receipt_chain_digest"):
        if not _is_digest(value.get(key)):
            raise _Stop("rollback", "rollback_closure_digest")
    receipt = value.get("closure_receipt")
    receipt_fields = {"schema", "run_id", "kind", "status", "rollback_digest", "receipt_chain_digest", "rollback_receipt_hash", "impasse_receipt_hash", "close_receipt_hash", "receipt_digest"}
    if (not isinstance(receipt, Mapping) or set(receipt) != receipt_fields
            or receipt.get("schema") != "P5R0TrackAClosureReceiptV1"
            or receipt.get("run_id") != run_id or receipt.get("kind") != "close"
            or receipt.get("status") != "verified"
            or receipt.get("rollback_digest") != value["rollback_digest"]
            or receipt.get("receipt_chain_digest") != value["receipt_chain_digest"]
            or any(not _is_digest(receipt.get(key)) for key in ("rollback_receipt_hash", "impasse_receipt_hash", "close_receipt_hash", "receipt_digest"))
            or receipt.get("receipt_digest") != digest({key: receipt[key] for key in receipt if key != "receipt_digest"})):
        raise _Stop("rollback", "closure_receipt_unverified")
    chain = value.get("receipt_chain")
    chain_fields = {"schema", "root", "root_digest", "authority_id", "key_id", "public_key", "records", "records_digest"}
    if (not isinstance(chain, Mapping) or set(chain) != chain_fields
            or chain.get("schema") != "P5R0TrackAFailureReceiptChainV1"
            or not isinstance(chain.get("root"), str) or chain.get("root_digest") != digest(str(Path(chain["root"]).resolve()))
            or not isinstance(chain.get("authority_id"), str) or not isinstance(chain.get("key_id"), str)
            or not isinstance(chain.get("public_key"), str) or not isinstance(chain.get("records"), list)
            or chain.get("records_digest") != digest(chain["records"])):
        raise _Stop("rollback", "failure_receipt_chain_shape")
    try:
        public_key = __import__("cryptography.hazmat.primitives.asymmetric.ed25519", fromlist=["Ed25519PublicKey"]).Ed25519PublicKey.from_public_bytes(b64decode(chain["public_key"]))
        durable = ReceiptChain.reload(Path(chain["root"]), public_key, authority_id=chain["authority_id"], key_id=chain["key_id"], protocol="V3")
    except Exception as exc:
        raise _Stop("rollback", "failure_receipt_chain_unverified") from exc
    if durable.records != chain["records"] or durable.final_digest != value["receipt_chain_digest"]:
        raise _Stop("rollback", "failure_receipt_chain_mismatch")
    records_by_kind: dict[str, Mapping[str, Any]] = {}
    for record in durable.records:
        payload = record.get("payload")
        binding = payload.get("binding") if isinstance(payload, Mapping) else None
        kind = payload.get("kind") if isinstance(payload, Mapping) else None
        if (not isinstance(payload, Mapping) or payload.get("run_id") != run_id
                or not isinstance(binding, Mapping) or binding.get("run_id") != run_id
                or kind in records_by_kind):
            raise _Stop("rollback", "failure_receipt_chain_binding")
        if kind in {"impasse", "rollback", "close"} and binding.get("rollback_digest") != value["rollback_digest"]:
            raise _Stop("rollback", "failure_receipt_chain_binding")
        records_by_kind[kind] = record
    if not {"impasse", "rollback", "close"}.issubset(records_by_kind):
        raise _Stop("rollback", "failure_receipt_chain_closure")
    expected_links = {
        "rollback_receipt_hash": records_by_kind["rollback"]["receipt_hash"],
        "impasse_receipt_hash": records_by_kind["impasse"]["receipt_hash"],
        "close_receipt_hash": records_by_kind["close"]["receipt_hash"],
    }
    if any(receipt.get(key) != expected for key, expected in expected_links.items()):
        raise _Stop("rollback", "failure_receipt_cross_link")
    seal = value.get("impasse_seal")
    seal_fields = {"schema", "run_id", "rollback_digest", "closure_receipt_digest", "receipt_chain_digest", "rollback_receipt_hash", "impasse_receipt_hash", "close_receipt_hash", "seal_digest"}
    if (not isinstance(seal, Mapping) or set(seal) != seal_fields
            or seal.get("schema") != TRACK_A_IMPASSE_SEAL_SCHEMA or seal.get("run_id") != run_id
            or seal.get("rollback_digest") != value["rollback_digest"]
            or seal.get("closure_receipt_digest") != digest(dict(receipt))
            or seal.get("receipt_chain_digest") != value["receipt_chain_digest"]
            or any(seal.get(key) != expected for key, expected in expected_links.items())
            or seal.get("seal_digest") != digest({key: seal[key] for key in seal if key != "seal_digest"})):
        raise _Stop("rollback", "impasse_seal_unverified")
    return dict(value)


class TrackARunner:
    """Execute exactly the adapter-backed Track A MVP, or return an impasse."""

    def __init__(self, adapter: TrackAAdapter, config: TrackAConfig):
        if not isinstance(adapter, TrackAAdapter):
            raise TrackAError("Track A verifier-owned adapter is required")
        if not isinstance(config, TrackAConfig):
            raise TrackAError("TrackAConfig is required")
        config.validate()
        self.adapter = adapter
        self.config = config
        self._run_id: str | None = None
        self._rollback_done = False
        self._seal_store: TrackASealStore | None = None
        self._failure_commitments: dict[str, str] = {}

    def _cleanup_after_failure(self, execution: TrackAExecution | None) -> bool:
        if self._run_id is None or execution is None or self._rollback_done:
            return True
        try:
            rollback = _validate_failure_closure(execution.rollback(self._run_id), run_id=self._run_id)
            if self._seal_store is None:
                raise _Stop("rollback", "impasse_seal_store_unavailable")
            seal = rollback["impasse_seal"]
            self._seal_store.persist(self._run_id, seal)
            persisted = _require_mapping(self._seal_store.read(self._run_id), "persisted_impasse_seal")
            if dict(persisted) != dict(seal):
                raise _Stop("rollback", "impasse_seal_readback")
            verification = _require_mapping(self._seal_store.verify(rollback, persisted), "impasse_seal_verification")
            if verification.get("status") != "verified" or verification.get("seal_digest") != digest(dict(persisted)):
                raise _Stop("rollback", "impasse_seal_unverified")
            self._failure_commitments = {
                "rollback_digest": rollback["rollback_digest"],
                "closure_receipt_digest": digest(dict(rollback["closure_receipt"])),
                "impasse_seal_digest": digest(dict(persisted)),
            }
            self._rollback_done = True
            return True
        except Exception:
            self._rollback_done = True
            return False

    def _blocked(self, stop: _Stop) -> TrackAResult:
        disposition = "blocked" if self._run_id is None else "impasse"
        return TrackAResult(
            "blocked" if self._run_id is None else "impasse", disposition, stop.stage, stop.code, self._run_id,
            rollback_digest=self._failure_commitments.get("rollback_digest"),
            closure_receipt_digest=self._failure_commitments.get("closure_receipt_digest"),
            impasse_seal_digest=self._failure_commitments.get("impasse_seal_digest"),
        )

    def run(self) -> TrackAResult:
        stage = "provisioning"
        execution: TrackAExecution | None = None
        self._run_id = None
        self._rollback_done = False
        self._failure_commitments = {}
        try:
            selection = self.config.selection
            provisioned = _validate_provisioned(self.adapter.provision_inputs(selection), selection)
            stage = "attestation"
            # Attestation validation is deliberately complete before the
            # activation call.  The adapter therefore cannot expose KMS,
            # timing, storage, worker, or task capabilities on stale/missing
            # startup evidence.
            attestation = _validate_attestation(self.adapter, selection)
            activation_commitment = _activation_commitment(selection, provisioned, attestation, self.config.iam_predecessor)
            capabilities = self.adapter.activate_attested_capabilities(activation_commitment)
            if not isinstance(capabilities.execution, TrackAExecution) or not isinstance(capabilities.seal_store, TrackASealStore) or not isinstance(capabilities.input_builder, TrackAInputBuilder):
                raise _Stop(stage, "capability_interface")
            if capabilities.publisher is not None and not isinstance(capabilities.publisher, TrackAPublisher):
                raise _Stop(stage, "publisher_interface")
            _validate_activation_commitment(capabilities.activation_commitment, activation_commitment)
            if capabilities.attestation_binding is not getattr(self.adapter, "attestation_binding", None):
                raise _Stop(stage, "attestation_capability_binding")
            _validate_closure(capabilities.closure, attestation["image_digest"])
            authority = _validate_authority(capabilities.signer)
            if type(capabilities.production_promotable) is not bool:
                raise _Stop(stage, "production_status_shape")
            verifier_kms_promotable = getattr(getattr(capabilities.signer, "verifier_capability", None), "production_promotable", False)
            if capabilities.production_promotable and verifier_kms_promotable is not True:
                raise _Stop(stage, "production_kms_capability_required")
            production_promotable = capabilities.production_promotable and verifier_kms_promotable is True
            if not isinstance(capabilities.supervisor, VerifierIssuedSupervisorCapability):
                raise _Stop(stage, "supervisor_capability_required")
            if not isinstance(capabilities.closure, Mapping) or not _is_digest(capabilities.closure.get("closure_digest")):
                raise _Stop(stage, "closure_binding")
            execution = capabilities.execution
            self._seal_store = capabilities.seal_store
            stage = "rehydration"
            inputs = _validate_rehydrated(self.adapter.read_and_rehydrate_inputs(provisioned), provisioned)
            stage = "timing"
            run_id = capabilities.execution.start(selection, inputs)
            if not _is_digest(run_id):
                raise _Stop(stage, "run_identity")
            self._run_id = run_id
            timing_response = _require_mapping(capabilities.execution.acquire_timing_record(run_id, self.config.input_namespace), "timing_record")
            if set(timing_response) != {"timing_record", "timing_record_digest"}:
                raise _Stop(stage, "timing_record_shape")
            timing_record = timing_response.get("timing_record")
            if not isinstance(timing_record, Mapping) or timing_response.get("timing_record_digest") != digest(dict(timing_record)):
                raise _Stop(stage, "timing_record_unavailable")
            timing_verification = _validate_timing(capabilities.timing_verifier, timing_record, run_id)
            binding = dict(getattr(capabilities.input_builder, "binding", {}))
            if binding != input_builder_binding() or dict(getattr(capabilities.input_builder, "algorithm_binding", time_seed_algorithm_binding())) != time_seed_algorithm_binding():
                raise _Stop(stage, "input_source_binding")
            seeded = derive_time_seed(timing_record, run_id=run_id, namespace=self.config.input_namespace, sequence=timing_record.get("sequence"), input_builder=capabilities.input_builder.build, input_builder_binding=binding, time_seed_algorithm_binding=time_seed_algorithm_binding())
            if timing_response.get("timing_record_digest") != seeded.timing_record_digest:
                raise _Stop(stage, "timing_seed_binding")
            stage = "native"
            task = _validate_task(capabilities.execution.issue_task(run_id, selection, seeded.public_commitment()), selection, control=False, expected_run_id=run_id)
            task_reply, task_evidence, task_report = _validate_execution(capabilities.worker, capabilities.supervisor, capabilities.closure, task, lock_digest=selection.lock_digest, expected_run_id=run_id, control=False)
            task_outcome = _require_mapping(capabilities.execution.submit_task(run_id, task, task_reply, task_evidence), "task_outcome")
            if task_outcome.get("run_id") != run_id or task_outcome.get("task_digest") != task.get("task_digest"):
                raise _Stop("task", "task_outcome_binding")
            control = _validate_task(capabilities.execution.issue_control(run_id, selection, seeded.public_commitment()), selection, control=True, expected_run_id=run_id)
            if control.get("task_id") == task.get("task_id"):
                raise _Stop("control", "task_control_replay")
            control_reply, control_evidence, control_report = _validate_execution(capabilities.worker, capabilities.supervisor, capabilities.closure, control, lock_digest=selection.lock_digest, expected_run_id=run_id, control=True)
            control_outcome = _require_mapping(capabilities.execution.submit_control(run_id, control, control_reply, control_evidence), "control_outcome")
            if control_outcome.get("run_id") != run_id or control_outcome.get("task_digest") != control.get("task_digest"):
                raise _Stop("control", "control_outcome_binding")
            if control_outcome.get("outcome") != "protocol_error":
                raise _Stop("control", "illegal_action_outcome")
            stage = "receipts"
            receipts = _validate_receipts(_require_mapping(capabilities.execution.verify_receipts(run_id), "receipt_verification"), task, control, run_id=run_id, timing_record_digest=seeded.timing_record_digest, closure_digest=capabilities.closure["closure_digest"])
            rollback = _validate_failure_closure(_require_mapping(capabilities.execution.rollback(run_id), "rollback"), run_id=run_id)
            self._rollback_done = True
            if rollback.get("status") != "exact" or not _is_digest(rollback.get("rollback_digest")):
                raise _Stop("rollback", "rollback_unverified")
            result = _require_mapping(capabilities.execution.create_result(run_id, selection, task_outcome, control_outcome, {"task": task_report, "control": control_report, "task_evidence_digest": digest(task_evidence), "control_evidence_digest": digest(control_evidence), "timing": {"seed": seeded.public_commitment(), "verification": dict(timing_verification)}}, receipts, rollback, attestation, seeded), "canonical_result")
            if result.get("run_id") != run_id or result.get("claim_boundary") != _TRACK_A_CLAIM_BOUNDARY:
                raise _Stop("result", "canonical_result_binding")
            expected_commitments = {
                "timing_record_digest": seeded.timing_record_digest,
                "input_seed_digest": seeded.input_seed_digest,
                "input_digest": seeded.input_digest,
                "public_input_digest": provisioned["public_input_digest"],
                "access_binding_digest": provisioned["access_binding_digest"],
                "receipt_chain_digest": receipts["chain_digest"],
                "attestation_binding_digest": attestation["binding_digest"],
                "closure_digest": capabilities.closure["closure_digest"],
                "supervisor_commitment_digest": digest(dict(capabilities.supervisor.commitment)),
                "kms_authority_commitment_digest": _kms_authority_commitment(capabilities.signer, authority)["commitment_digest"],
                "kms_key_version": capabilities.signer.key_version,
                "kms_transport_commitment_digest": digest(authority["transport_attestation"]),
            }
            if any(result.get(key) != expected for key, expected in expected_commitments.items()):
                raise _Stop("result", "canonical_result_commitments")
            result_digest = _canonical_result_digest(result)
            if receipts["result_digest"] != result_digest:
                raise _Stop("receipts", "receipt_result_digest_mismatch")
            stage = "seal"
            seal = _require_mapping(capabilities.seal_store.create(result), "result_seal")
            capabilities.seal_store.persist(run_id, seal)
            persisted = _require_mapping(capabilities.seal_store.read(run_id), "persisted_result_seal")
            if dict(persisted) != dict(seal) or digest(dict(persisted)) != digest(dict(seal)):
                raise _Stop(stage, "result_seal_readback")
            _validate_seal(persisted, run_id=run_id, result_digest=result_digest, chain_digest=receipts["chain_digest"])
            seal_verification = _require_mapping(capabilities.seal_store.verify(result, persisted), "result_seal_verification")
            if seal_verification.get("status") != "verified" or seal_verification.get("seal_digest") != digest(dict(persisted)):
                raise _Stop(stage, "result_seal_unverified")
            final_binding = {
                "schema": TRACK_A_FINAL_BINDING_SCHEMA,
                "lock_digest": selection.lock_digest,
                "manifest_digest": selection.manifest_digest,
                "worker_contract_digest": selection.worker_contract_digest,
                "activation_commitment": dict(activation_commitment),
                "selection": selection.as_dict(),
                "provisioned_inputs": dict(provisioned),
                "rehydrated_inputs": dict(inputs),
                "attestation": dict(attestation),
                "timing_input": {"seed": seeded.public_commitment(), "verification": dict(timing_verification)},
                "closure": dict(capabilities.closure),
                "executions": {
                    "task": {"envelope": dict(task), "reply": dict(task_reply), "evidence_digest": digest(task_evidence), "outcome": dict(task_outcome)},
                    "control": {"envelope": dict(control), "reply": dict(control_reply), "evidence_digest": digest(control_evidence), "outcome": dict(control_outcome)},
                },
                "supervisor_evidence": {"task": task_report, "control": control_report},
                "receipts": dict(receipts),
                "rollback": dict(rollback),
                "receipt_chain_digest": receipts["chain_digest"],
                "commitments": {
                    "timing_record_digest": seeded.timing_record_digest,
                    "input_seed_digest": seeded.input_seed_digest,
                    "input_digest": seeded.input_digest,
                    "public_input_digest": provisioned["public_input_digest"],
                    "private_store_digest": provisioned["private_store_digest"],
                    "access_binding_digest": provisioned["access_binding_digest"],
                    "attestation_binding_digest": attestation["binding_digest"],
                    "closure_digest": capabilities.closure["closure_digest"],
                    "supervisor_commitment_digest": digest(dict(capabilities.supervisor.commitment)),
                    "kms_authority_commitment": _kms_authority_commitment(capabilities.signer, authority),
                },
                "signer": {
                    "authority_id": authority["authority_id"],
                    "key_id": authority["key_id"],
                    "key_version": capabilities.signer.key_version,
                    "public_key_digest": authority["public_key_digest"],
                    "transport_attestation": dict(authority["transport_attestation"]),
                    "verifier_capability_digest": capabilities.signer.verifier_capability.commitment["capability_digest"],
                },
                "result_digest": result_digest,
                "result_seal": dict(persisted),
                "result_seal_digest": digest(dict(persisted)),
                "disposition": result.get("disposition"),
                "production_promotable": production_promotable,
            }
            final_digest = digest(final_binding)
            stage = "signing"
            signature = capabilities.signer.sign_digest(bytes.fromhex(final_digest[7:]))
            if not isinstance(signature, str):
                raise _Stop(stage, "final_signature_shape")
            _verify_signature(capabilities.signer, final_digest, signature)
            signed = {
                "schema": TRACK_A_RESULT_SCHEMA,
                "status": "signed_diagnostic" if production_promotable else "diagnostic_only",
                "production_promotable": production_promotable,
                "disposition": result.get("disposition"),
                "run_id": run_id,
                "result_digest": result_digest,
                "result_seal_digest": digest(dict(persisted)),
                "final_binding_digest": final_digest,
                "final_signature": signature,
                "attestation_binding_digest": attestation["binding_digest"],
                "public_input_digest": provisioned["public_input_digest"],
                "access_binding_digest": provisioned["access_binding_digest"],
                "timing_record_digest": seeded.timing_record_digest,
                "input_seed_digest": seeded.input_seed_digest,
                "input_digest": seeded.input_digest,
                "receipt_chain_digest": receipts["chain_digest"],
                "closure_digest": capabilities.closure["closure_digest"],
                "supervisor_commitment_digest": digest(dict(capabilities.supervisor.commitment)),
                "kms_authority_commitment_digest": _kms_authority_commitment(capabilities.signer, authority)["commitment_digest"],
                "kms_key_version": capabilities.signer.key_version,
                "kms_transport_commitment_digest": digest(authority["transport_attestation"]),
                "claim_boundary": _TRACK_A_CLAIM_BOUNDARY,
            }
            publication: Mapping[str, Any] | None = None
            if capabilities.publisher is not None:
                try:
                    candidate_publication = capabilities.publisher.publish(signed)
                    if not isinstance(candidate_publication, Mapping):
                        raise ValueError("publication shape")
                    publication = candidate_publication
                except Exception:
                    # Publication is transport-only and occurs after the
                    # verified signature; its absence cannot promote or
                    # invalidate the already signed Track A artifact.
                    publication = {"status": "not_published", "reason_code": "optional_publication_unavailable"}
            return TrackAResult(
                status="signed_diagnostic" if production_promotable else "diagnostic_only", disposition=str(result.get("disposition", "diagnostic")), stage="complete", reason_code="ok",
                run_id=run_id, result_digest=result_digest, result_seal_digest=digest(dict(persisted)),
                final_binding_digest=final_digest, final_signature=signature,
                attestation_binding_digest=attestation["binding_digest"], public_input_digest=provisioned["public_input_digest"],
                access_binding_digest=provisioned["access_binding_digest"], timing_record_digest=seeded.timing_record_digest,
                input_seed_digest=seeded.input_seed_digest, input_digest=seeded.input_digest,
                receipt_chain_digest=receipts["chain_digest"], closure_digest=capabilities.closure["closure_digest"],
                supervisor_commitment_digest=digest(dict(capabilities.supervisor.commitment)),
                kms_authority_commitment_digest=_kms_authority_commitment(capabilities.signer, authority)["commitment_digest"],
                kms_key_version=capabilities.signer.key_version,
                kms_transport_commitment_digest=digest(authority["transport_attestation"]), production_promotable=production_promotable, publication=publication,
            )
        except _Stop as stop:
            if self._run_id is not None and not self._cleanup_after_failure(execution):
                return self._blocked(_Stop("rollback", "rollback_unverified"))
            return self._blocked(stop)
        except Exception:
            if self._run_id is not None and not self._cleanup_after_failure(execution):
                return self._blocked(_Stop("rollback", "rollback_unverified"))
            # Never expose provider text, stack traces, tokens, or private data.
            return self._blocked(_Stop(stage, "external_evidence_unavailable"))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the verifier-owned DISPATCH-066 Track A adapter boundary")
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--selection", type=argparse.FileType("r"), required=False, help="canonical selection is inspected only; no adapter is created by this CLI")
    args = parser.parse_args(argv)
    # There is intentionally no local adapter factory.  A CLI cannot promote
    # fixtures or construct cloud capabilities, so it reports the first safe
    # external blocker instead of pretending to run Track A.
    result = TrackAResult("blocked", "blocked", "attestation", "verifier_owned_adapter_required")
    print(json.dumps(result.as_dict(), sort_keys=True, separators=(",", ":")))
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = [
    "TRACK_A_RESULT_SCHEMA", "TRACK_A_SELECTION_SCHEMA", "TRACK_A_PROVISION_SCHEMA", "TRACK_A_REHYDRATION_SCHEMA", "TRACK_A_FINAL_BINDING_SCHEMA", "TRACK_A_TASK_SCHEMA", "TRACK_A_RECEIPT_SCHEMA", "TRACK_A_IMPASSE_SEAL_SCHEMA",
    "TrackAAdapter", "TrackACapabilities", "TrackAConfig", "TrackAError", "TrackAExecution", "TrackAInputBuilder", "TrackAPublisher", "TrackARunner", "TrackASealStore", "TrackASelection", "TrackASigner", "TrackAWorker", "TrackABlocked", "TrackAResult", "VerifierIssuedSupervisorCapability", "issue_verifier_supervisor_capability",
]
