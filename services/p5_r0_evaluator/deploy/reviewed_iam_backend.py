"""APPROVAL-023/DISPATCH-082 fixed-command IAM boundary.

This module is the only effectful IAM path for the reviewed operation.  It
constructs a closed, allowlisted argv for the absolute Google Cloud SDK
binary, invokes it without a shell or stdin, and never discovers ADC,
creates/exports keys, or accepts caller-supplied commands/approval booleans.

The checked-in child packet is a fresh, digest-bound execution plan.  Applying
it is intentionally not performed by this implementation task; the CLI
``validate`` command is read-only and prints the future ``apply`` invocation.
The apply path is one-shot: it reserves its JSONL ledger atomically before
any cloud read, verifies the exact captured prestate, performs only the
reviewed IAM operations, verifies an exact private poststate/receipt, or
closes with rollback/manual-review and no retry.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import os
import select
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, Sequence

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.credential_evidence import VerifiedCredentialReadinessEvidence, _commitment, _is_registered_credential_evidence
from services.p5_r0_evaluator.deploy import iam_capability_provisioning as iam
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import InjectedSignedEnvironmentCredential
from services.p5_r0_evaluator.deploy.iam_predecessor import issue_signed_iam_ledger_root, issue_verified_iam_predecessor, load_verified_iam_predecessor

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
GCLOUD = "/home/matt/google-cloud-sdk/bin/gcloud"
DEFAULT_PACKET = Path(__file__).with_name("approval-023-dispatch-082-iam-child-packet-v1.json")
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-0-approval-023-dispatch-082-iam-ledger.jsonl"
SOURCE_PATHS = {
    "iam_definition_path": "services/p5_r0_evaluator/deploy/rs069r18r13-iam-provisioning-definition-v1.json",
    "gcs_capability_definition_path": "services/p5_r0_evaluator/deploy/gcs-capability-definition.json",
    "prestate_artifact_path": "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json",
    "live_observation_path": "var/p5-r0-approval-022/approval-022-live-observation-v1.json",
}
APPLY_PREREQUISITES = (
    "verifier-issued InjectedSignedEnvironmentCredential with live expiry and no ADC/export/key material",
    "registered VerifiedCredentialReadinessEvidence bound to this packet, authority, principal, resource, and credential expiry",
    "registered VerifiedIAMChildApproval signed by confidential-space-verifier and bound to packet digest, attempt, prestate, evidence digest, authority, and expiry",
    "verifier-issued VerifiedIAMApprovalSignatureVerifier for the trusted authority and exact canonical approval payload",
    "reviewed non-ADC, non-direct-gcloud executor adapter",
)
FUTURE_APPLY_COMMAND = "blocked: supply verifier-issued signed-environment prerequisites to ReviewedFixedCommandExecutor.apply"

PROJECT_ID = iam.PROJECT_ID
PROJECT_NUMBER = iam.PROJECT_NUMBER
BUCKET = iam.BUCKET
EXISTING_ACCOUNT = iam.EXISTING_ACCOUNT
TARGET_ACCOUNT = iam.GCS_ONLY_ACCOUNT
CUSTOM_ROLE = iam.CUSTOM_ROLE
CUSTOM_ROLE_ID = "p5R0Operation4BundleWriterV1"
CUSTOM_ROLE_TITLE = iam.CUSTOM_ROLE_TITLE
CUSTOM_ROLE_STAGE = iam.CUSTOM_ROLE_STAGE
CUSTOM_ROLE_PERMISSIONS = list(iam.CUSTOM_ROLE_PERMISSIONS)
TOKEN_CREATOR = iam.TOKEN_CREATOR
WIF_PRINCIPAL = iam.WIF_PRINCIPAL
BROAD_ROLE = iam.BROAD_ROLE
STALE_WIF_PRINCIPAL = iam.STALE_WIF_PRINCIPAL
STALE_WIF_ROLE = iam.STALE_WIF_ROLE
EXACT_CONDITION_TITLE = iam.EXACT_CONDITION_TITLE
EXACT_CONDITION = iam.EXACT_CONDITION

PACKET_SCHEMA = "P5R0APPROVAL023DISPATCH082IAMChildPacketV1"
LEDGER_SCHEMA = "P5R0APPROVAL023DISPATCH082IAMLedgerEventV1"
OPERATION_ID = iam.OPERATION_ID
PARENT_APPROVAL_ID = "P5-MASTER-001/APPROVAL-023"
DISPATCH_ID = "P5-MASTER-001/DISPATCH-082"
ATTEMPT_ID = "dispatch082-iam-20260920-a7f4c2d9"
CHILD_PACKET_DIGEST = "sha256:5c1671e34559897a4fb62c67c575280df9897bb733496fd8fbea224d7961e4e4"
PRESTATE_ARTIFACT_DIGEST = "sha256:03c83325fd531f0a2db39f0d54d02b10ae7cfa96577ab3cc93046602f109b946"
PRESTATE_STATE_DIGEST = "sha256:a7580109437962f92903ff8d03f03a3f3de386b1da0f51e2cb73aff2518dc692"
PRESTATE_NORMALIZED_DIGEST = "sha256:c8bf59b8cd71a0a5ee5d7b4f74d6a21a87e67ccc630434af897300d56a42e90e"
LIVE_OBSERVATION_DIGEST = "sha256:2c458caa916c4720e70a50e2c84b362e9c8be05bcee796a707d0b3f7c3f2ca0f"
IAM_DEFINITION_DIGEST = "sha256:817ce6cff5f25487ba131a2d587fbcd489a52245e3a8173aa6320862ed49ce25"
GCS_DEFINITION_DIGEST = "sha256:705c5323a8bf8f300547d2051cf128825b03e0415c334dd452cd4e9db0280ee2"
AUTHORITY_BINDING_DIGEST = iam.AUTHORITY_BINDING_DIGEST


class ReviewedIAMError(ValueError):
    """The reviewed fixed-command boundary rejected an input or outcome."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewedIAMError(message)


_APPROVAL_SEAL = object()
_APPROVAL_REGISTRY: dict[int, tuple["VerifiedIAMChildApproval", tuple[Any, ...]]] = {}
_APPROVAL_FIELDS = (
    "schema", "approval_id", "operation_id", "scope", "status", "packet_digest", "attempt_id",
    "prestate_digest", "credential_evidence_digest", "authority_binding_digest", "signer_id",
    "issued_at", "expires_at", "signature", "approval_digest",
)


@dataclass(frozen=True, init=False)
class VerifiedIAMChildApproval:
    """Verifier-issued approval for exactly one IAM attempt.

    The object is intentionally not constructible from a mapping.  Its
    registry snapshot prevents copying or re-sealing a public representation;
    the supplied verifier must additionally validate ``signature_payload``
    against the trusted approval authority.
    """

    schema: str
    approval_id: str
    operation_id: str
    scope: tuple[str, ...]
    status: str
    packet_digest: str
    attempt_id: str
    prestate_digest: str
    credential_evidence_digest: str
    authority_binding_digest: str
    signer_id: str
    issued_at: int
    expires_at: int
    signature: str
    approval_digest: str

    def __init__(self, **values: Any) -> None:
        _require(values.pop("_seal", None) is _APPROVAL_SEAL, "IAM child approval is verifier-created")
        _require(set(values) == set(_APPROVAL_FIELDS), "IAM child approval fields are closed")
        for field in _APPROVAL_FIELDS:
            object.__setattr__(self, field, tuple(values[field]) if field == "scope" else values[field])

    def as_public_dict(self) -> dict[str, Any]:
        _require(_is_registered_iam_approval(self), "IAM child approval is not verifier-issued")
        return {field: (list(getattr(self, field)) if field == "scope" else getattr(self, field)) for field in _APPROVAL_FIELDS}

    def signature_payload(self) -> dict[str, Any]:
        public = self.as_public_dict()
        return {field: public[field] for field in _APPROVAL_FIELDS if field not in {"signature", "approval_digest"}}


def _approval_snapshot(value: VerifiedIAMChildApproval) -> tuple[Any, ...]:
    return tuple(getattr(value, field) for field in _APPROVAL_FIELDS)


def _is_registered_iam_approval(value: Any) -> bool:
    return (
        type(value) is VerifiedIAMChildApproval
        and id(value) in _APPROVAL_REGISTRY
        and _APPROVAL_REGISTRY[id(value)][0] is value
        and _approval_snapshot(value) == _APPROVAL_REGISTRY[id(value)][1]
    )


_VERIFIER_SEAL = object()
_VERIFIER_REGISTRY: dict[int, "VerifiedIAMApprovalSignatureVerifier"] = {}
try:  # cryptography is already a repository dependency for the verifier boundary.
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError:  # pragma: no cover - production/test environments install it.
    Ed25519PrivateKey = Ed25519PublicKey = None  # type: ignore[assignment]
_TEST_VERIFIER_KEY = Ed25519PrivateKey.generate() if Ed25519PrivateKey is not None else None


@dataclass(frozen=True, init=False)
class VerifiedIAMApprovalSignatureVerifier:
    """Verifier-owned public-key capability; no caller callback is trusted."""

    verifier_id: str
    authority_binding_digest: str
    public_key: str
    capability_digest: str

    def __init__(self, **values: Any) -> None:
        _require(values.pop("_seal", None) is _VERIFIER_SEAL, "approval signature verifier is verifier-created")
        _require(set(values) == {"verifier_id", "authority_binding_digest", "public_key", "capability_digest"}, "approval signature verifier fields are closed")
        for field in ("verifier_id", "authority_binding_digest", "public_key", "capability_digest"):
            object.__setattr__(self, field, values[field])

    def verify(self, payload: Mapping[str, Any], signature: str) -> bool:
        _require(_VERIFIER_REGISTRY.get(id(self)) is self, "approval signature verifier is not verifier-issued")
        _require(self.verifier_id == "confidential-space-verifier" and self.authority_binding_digest == AUTHORITY_BINDING_DIGEST, "approval signature verifier authority drift")
        _require(self.capability_digest == _digest({"verifier_id": self.verifier_id, "authority_binding_digest": self.authority_binding_digest, "public_key": self.public_key}), "approval signature verifier capability drift")
        if Ed25519PublicKey is None:
            return False
        try:
            key = Ed25519PublicKey.from_public_bytes(base64.b64decode(self.public_key, validate=True))
            key.verify(base64.b64decode(signature, validate=True), canonical_bytes(dict(payload)))
            return True
        except Exception:
            return False


def _issue_verified_signature_verifier() -> VerifiedIAMApprovalSignatureVerifier:
    """Verifier adapter fixture hook; the capability owns its public key."""
    _require(_TEST_VERIFIER_KEY is not None, "signed verifier capability is unavailable")
    public_key = base64.b64encode(_TEST_VERIFIER_KEY.public_key().public_bytes_raw()).decode("ascii")
    values = {"verifier_id": "confidential-space-verifier", "authority_binding_digest": AUTHORITY_BINDING_DIGEST, "public_key": public_key}
    verifier = VerifiedIAMApprovalSignatureVerifier(**values, capability_digest=_digest(values), _seal=_VERIFIER_SEAL)
    _VERIFIER_REGISTRY[id(verifier)] = verifier
    return verifier


def _sign_approval_payload(payload: Mapping[str, Any]) -> str:
    _require(_TEST_VERIFIER_KEY is not None, "signed verifier capability is unavailable")
    return base64.b64encode(_TEST_VERIFIER_KEY.sign(canonical_bytes(dict(payload)))).decode("ascii")


def _sign_ledger_root_payload(payload: Mapping[str, Any]) -> str:
    """Test verifier hook; production must inject an external signer."""
    return _sign_approval_payload(payload)

def _issue_verified_iam_child_approval(
    *, packet_digest: str, attempt_id: str, prestate_digest: str,
    credential_evidence_digest: str, authority_binding_digest: str,
    issued_at: int, expires_at: int, signature: str | None = None,
) -> VerifiedIAMChildApproval:
    """Verifier-side fixture hook; production receives the sealed object."""
    values: dict[str, Any] = {
        "schema": "P5R0APPROVAL023IAMChildApprovalV1",
        "approval_id": "P5-MASTER-001/APPROVAL-023-IAM-CHILD",
        "operation_id": OPERATION_ID,
        "scope": [OPERATION_ID],
        "status": "approved_single_operation_pending_apply",
        "packet_digest": packet_digest,
        "attempt_id": attempt_id,
        "prestate_digest": prestate_digest,
        "credential_evidence_digest": credential_evidence_digest,
        "authority_binding_digest": authority_binding_digest,
        "signer_id": "confidential-space-verifier",
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    values["signature"] = signature or _sign_approval_payload(values)
    values["approval_digest"] = _digest(values)
    approval = VerifiedIAMChildApproval(**values, _seal=_APPROVAL_SEAL)
    _APPROVAL_REGISTRY[id(approval)] = (approval, _approval_snapshot(approval))
    return approval


def load_verified_iam_child_approval(path: Path, *, trusted_public_key: str) -> VerifiedIAMChildApproval:
    """Reload a canonical, verifier-signed child approval artifact.

    The artifact's embedded key is not trusted.  The caller supplies the
    verifier trust root, and only after signature and closed-field checks is a
    runtime capability registered for the existing apply validator.
    """
    try:
        artifact = parse_canonical(Path(path).read_bytes())
        _require(artifact.get("schema") == "P5R0SignedIAMChildApprovalV1", "IAM approval artifact schema drift")
        _require(artifact.get("artifact_digest") == _digest({key: value for key, value in artifact.items() if key != "artifact_digest"}), "IAM approval artifact digest drift")
        approval = artifact.get("approval")
        _require(isinstance(approval, Mapping), "IAM approval artifact payload is missing")
        _require(set(approval) == set(_APPROVAL_FIELDS), "IAM approval artifact is not closed")
        _require(approval.get("schema") == "P5R0APPROVAL023IAMChildApprovalV1", "IAM approval schema drift")
        _require(approval.get("signature") and approval.get("approval_digest") == _digest({key: value for key, value in approval.items() if key != "approval_digest"}), "IAM approval digest/signature fields are invalid")
        _require(artifact.get("public_key") == trusted_public_key, "IAM approval signer is not trusted")
        if Ed25519PublicKey is None:
            raise ReviewedIAMError("signed approval verifier is unavailable")
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted_public_key, validate=True))
        payload = {field: approval[field] for field in _APPROVAL_FIELDS if field not in {"signature", "approval_digest"}}
        key.verify(base64.b64decode(approval["signature"], validate=True), canonical_bytes(payload))
        values = {field: approval[field] for field in _APPROVAL_FIELDS}
        loaded = VerifiedIAMChildApproval(**values, _seal=_APPROVAL_SEAL)
        _APPROVAL_REGISTRY[id(loaded)] = (loaded, _approval_snapshot(loaded))
        return loaded
    except ReviewedIAMError:
        raise
    except Exception as exc:
        raise ReviewedIAMError("persisted IAM child approval signature is invalid") from exc


def build_signed_iam_child_approval_artifact(approval: VerifiedIAMChildApproval, *, public_key: str) -> dict[str, Any]:
    """Build the canonical envelope emitted by the verifier boundary."""
    public = approval.as_public_dict()
    value = {"schema": "P5R0SignedIAMChildApprovalV1", "approval": public, "public_key": public_key}
    value["artifact_digest"] = _digest(value)
    return value


def _validate_approval(
    approval: VerifiedIAMChildApproval, *, packet: Mapping[str, Any], prestate: Mapping[str, Any],
    credential_evidence_digest: str, now: int, signature_verifier: VerifiedIAMApprovalSignatureVerifier | None,
) -> dict[str, Any]:
    _require(_is_registered_iam_approval(approval), "IAM child approval is not verifier-issued")
    public = approval.as_public_dict()
    _require(public["schema"] == "P5R0APPROVAL023IAMChildApprovalV1", "IAM child approval schema drift")
    _require(public["approval_id"] == "P5-MASTER-001/APPROVAL-023-IAM-CHILD", "IAM child approval identity drift")
    _require(public["operation_id"] == OPERATION_ID and public["scope"] == [OPERATION_ID], "IAM child approval scope drift")
    _require(public["status"] == "approved_single_operation_pending_apply", "IAM child approval is not ready")
    _require(public["packet_digest"] == packet["artifact_digest"], "IAM child approval packet binding drift")
    _require(public["attempt_id"] == packet["attempt_id"] == ATTEMPT_ID, "IAM child approval attempt binding drift")
    _require(public["prestate_digest"] == prestate["state_digest"], "IAM child approval prestate binding drift")
    _require(public["credential_evidence_digest"] == credential_evidence_digest, "IAM child approval credential evidence binding drift")
    _require(public["authority_binding_digest"] == AUTHORITY_BINDING_DIGEST, "IAM child approval authority binding drift")
    _require(public["signer_id"] == "confidential-space-verifier", "IAM child approval signer drift")
    _require(type(public["issued_at"]) is int and type(public["expires_at"]) is int and public["issued_at"] <= now + 30 and public["expires_at"] > now, "IAM child approval is expired")
    _require(isinstance(public["signature"], str) and bool(public["signature"]), "IAM child approval signature is missing")
    _require(public["approval_digest"] == _digest({key: value for key, value in public.items() if key != "approval_digest"}), "IAM child approval digest mismatch")
    _require(type(signature_verifier) is VerifiedIAMApprovalSignatureVerifier and _VERIFIER_REGISTRY.get(id(signature_verifier)) is signature_verifier, "verifier-issued signature checker is required")
    _require(signature_verifier.verify(approval.signature_payload(), public["signature"]), "IAM child approval signature verification failed")
    return public


def _credential_resource_digests(state: Mapping[str, Any]) -> dict[str, str]:
    return {
        resource: _digest(state[resource])
        for resource in ("target_account", "target_account_policy", "bucket_policy", "custom_role")
        if state.get(resource) is not None
    }


def _credential_versions(state: Mapping[str, Any]) -> dict[str, dict[str, str] | None]:
    versions: dict[str, dict[str, str] | None] = {"target_account": None}
    for resource in ("target_account_policy", "bucket_policy", "custom_role"):
        value = state.get(resource)
        if resource == "custom_role" and isinstance(value, Mapping) and value.get("exists") is False:
            versions[resource] = None
        elif value is not None:
            versions[resource] = iam._version_value(value)
    return versions


def _without_versions(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _without_versions(item) for key, item in value.items() if key not in {"etag", "fingerprint", "state_digest"}}
    if isinstance(value, list):
        return [_without_versions(item) for item in value]
    return value


def _digest(value: Any) -> str:
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _semantic_state_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _without_versions(left) == _without_versions(right)


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return _digest({key: item for key, item in value.items() if key != field})


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ReviewedIAMError(f"invalid JSON artifact: {path}") from exc
    _require(isinstance(value, dict), "artifact root must be an object")
    return value


def _verify_source_artifacts() -> None:
    checks = {
        "iam_definition_path": ("definition_digest", IAM_DEFINITION_DIGEST),
        "gcs_capability_definition_path": ("definition_digest", GCS_DEFINITION_DIGEST),
        "prestate_artifact_path": ("artifact_digest", PRESTATE_ARTIFACT_DIGEST),
        "live_observation_path": ("artifact_digest", LIVE_OBSERVATION_DIGEST),
    }
    for name, (field, expected) in checks.items():
        artifact = _load_json(REPOSITORY_ROOT / SOURCE_PATHS[name])
        _require(artifact.get(field) == expected, f"{name} content digest drift")
        _require(artifact.get(field) == _digest_without(artifact, field), f"{name} digest seal drift")


def _load_packet(path: Path = DEFAULT_PACKET) -> dict[str, Any]:
    packet = _load_json(path)
    _require(packet.get("schema") == PACKET_SCHEMA, "child packet schema drift")
    _require(packet.get("artifact_digest") == CHILD_PACKET_DIGEST, "child packet is not the reviewed APPROVAL-023 packet")
    _require(packet.get("artifact_digest") == _digest_without(packet, "artifact_digest"), "child packet digest seal drift")
    _require(packet.get("parent_approval_id") == PARENT_APPROVAL_ID, "parent approval drift")
    _require(packet.get("dispatch_id") == DISPATCH_ID and packet.get("operation_id") == OPERATION_ID, "dispatch/operation drift")
    _require(packet.get("scope") == [OPERATION_ID], "child packet scope drift")
    _require(packet.get("status") == "approved_single_operation_enabled", "child packet is not enabled")
    _require(packet.get("attempt_id") == ATTEMPT_ID, "child packet attempt identity drift")
    _require(packet.get("later_operations_enabled") is False, "downstream operations are enabled")
    _require(packet.get("cloud_operations") == [], "child packet contains executed cloud operations")
    _require(packet.get("mutations_performed") is False, "child packet claims prior mutation")
    _require(packet.get("target") == {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER, "bucket": BUCKET, "service_account": TARGET_ACCOUNT, "custom_role": CUSTOM_ROLE, "wif_principal": WIF_PRINCIPAL}, "child packet target drift")
    _require(packet.get("apply_contract") == {"fixed_gcloud_path": GCLOUD, "shell": False, "stdin": "DEVNULL", "adc_discovery": False, "credential_export": False, "service_account_keys": False, "later_operations_enabled": False, "cloud_operations": [], "mutations_performed": False}, "child packet execution boundary drift")
    sources = packet.get("sources")
    _require(isinstance(sources, Mapping), "child packet sources are missing")
    _require(sources == {
        "iam_definition_digest": IAM_DEFINITION_DIGEST,
        "gcs_capability_definition_digest": GCS_DEFINITION_DIGEST,
        "prestate_artifact_digest": PRESTATE_ARTIFACT_DIGEST,
        "prestate_state_digest": PRESTATE_STATE_DIGEST,
        "live_observation_digest": LIVE_OBSERVATION_DIGEST,
    }, "child packet source binding drift")
    _require(packet.get("source_paths") == SOURCE_PATHS, "child packet source path drift")
    _verify_source_artifacts()
    return packet


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    def run(self, argv: Sequence[str]) -> CommandResult: ...


# Every command used by the production backend is selected by name below.  No
# method accepts an argv from a caller.  The values are intentionally literal;
# this is also the command-shape review surface used by tests.
_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "project_describe": (GCLOUD, "projects", "describe", PROJECT_ID, "--format=json"),
    "bucket_describe": (GCLOUD, "storage", "buckets", "describe", f"gs://{BUCKET}", f"--project={PROJECT_ID}", "--format=json"),
    "project_policy": (GCLOUD, "projects", "get-iam-policy", PROJECT_ID, "--format=json"),
    "bucket_policy": (GCLOUD, "storage", "buckets", "get-iam-policy", f"gs://{BUCKET}", f"--project={PROJECT_ID}", "--format=json"),
    "existing_describe": (GCLOUD, "iam", "service-accounts", "describe", EXISTING_ACCOUNT, f"--project={PROJECT_ID}", "--format=json"),
    "target_describe": (GCLOUD, "iam", "service-accounts", "describe", TARGET_ACCOUNT, f"--project={PROJECT_ID}", "--format=json"),
    "existing_policy": (GCLOUD, "iam", "service-accounts", "get-iam-policy", EXISTING_ACCOUNT, f"--project={PROJECT_ID}", "--format=json"),
    "target_policy": (GCLOUD, "iam", "service-accounts", "get-iam-policy", TARGET_ACCOUNT, f"--project={PROJECT_ID}", "--format=json"),
    "existing_keys": (GCLOUD, "iam", "service-accounts", "keys", "list", f"--iam-account={EXISTING_ACCOUNT}", f"--project={PROJECT_ID}", "--managed-by=user", "--format=json"),
    "target_keys": (GCLOUD, "iam", "service-accounts", "keys", "list", f"--iam-account={TARGET_ACCOUNT}", f"--project={PROJECT_ID}", "--managed-by=user", "--format=json"),
    "role_describe": (GCLOUD, "iam", "roles", "describe", CUSTOM_ROLE_ID, f"--project={PROJECT_ID}", "--format=json"),
    "account_create": (GCLOUD, "iam", "service-accounts", "create", "p5-r0-gcs-only", f"--project={PROJECT_ID}", f"--display-name=P5 R0 operation 4 GCS-only writer", "--quiet"),
    "role_create": (GCLOUD, "iam", "roles", "create", CUSTOM_ROLE_ID, f"--project={PROJECT_ID}", f"--title={CUSTOM_ROLE_TITLE}", f"--stage={CUSTOM_ROLE_STAGE}", f"--permissions={','.join(CUSTOM_ROLE_PERMISSIONS)}", "--quiet"),
    "role_update": (GCLOUD, "iam", "roles", "update", CUSTOM_ROLE_ID, f"--project={PROJECT_ID}", f"--title={CUSTOM_ROLE_TITLE}", f"--stage={CUSTOM_ROLE_STAGE}", f"--permissions={','.join(CUSTOM_ROLE_PERMISSIONS)}", "--quiet"),
    "bucket_add_exact": (GCLOUD, "storage", "buckets", "add-iam-policy-binding", f"gs://{BUCKET}", f"--member=serviceAccount:{TARGET_ACCOUNT}", f"--role={CUSTOM_ROLE}", f"--condition=title={EXACT_CONDITION_TITLE},expression={EXACT_CONDITION}", f"--project={PROJECT_ID}", "--quiet"),
    "bucket_remove_broad": (GCLOUD, "storage", "buckets", "remove-iam-policy-binding", f"gs://{BUCKET}", f"--member=serviceAccount:{EXISTING_ACCOUNT}", f"--role={BROAD_ROLE}", f"--project={PROJECT_ID}", "--quiet"),
    "bucket_remove_stale": (GCLOUD, "storage", "buckets", "remove-iam-policy-binding", f"gs://{BUCKET}", f"--member={STALE_WIF_PRINCIPAL}", f"--role={STALE_WIF_ROLE}", "--condition=expression=resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')", f"--project={PROJECT_ID}", "--quiet"),
    "target_add_token_creator": (GCLOUD, "iam", "service-accounts", "add-iam-policy-binding", TARGET_ACCOUNT, f"--member={WIF_PRINCIPAL}", f"--role={TOKEN_CREATOR}", f"--project={PROJECT_ID}", "--quiet"),
    "target_remove_token_creator": (GCLOUD, "iam", "service-accounts", "remove-iam-policy-binding", TARGET_ACCOUNT, f"--member={WIF_PRINCIPAL}", f"--role={TOKEN_CREATOR}", f"--project={PROJECT_ID}", "--quiet"),
    "bucket_remove_exact": (GCLOUD, "storage", "buckets", "remove-iam-policy-binding", f"gs://{BUCKET}", f"--member=serviceAccount:{TARGET_ACCOUNT}", f"--role={CUSTOM_ROLE}", f"--condition=title={EXACT_CONDITION_TITLE},expression={EXACT_CONDITION}", f"--project={PROJECT_ID}", "--quiet"),
    "bucket_add_broad": (GCLOUD, "storage", "buckets", "add-iam-policy-binding", f"gs://{BUCKET}", f"--member=serviceAccount:{EXISTING_ACCOUNT}", f"--role={BROAD_ROLE}", f"--project={PROJECT_ID}", "--quiet"),
    "bucket_add_stale": (GCLOUD, "storage", "buckets", "add-iam-policy-binding", f"gs://{BUCKET}", f"--member={STALE_WIF_PRINCIPAL}", f"--role={STALE_WIF_ROLE}", "--condition=expression=resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')", f"--project={PROJECT_ID}", "--quiet"),
    "role_delete": (GCLOUD, "iam", "roles", "delete", CUSTOM_ROLE_ID, f"--project={PROJECT_ID}", "--quiet"),
}


_ALLOWLIST = MappingProxyType(_ALLOWLIST)


def allowlisted_argv(name: str) -> tuple[str, ...]:
    """Return a copy of one closed command; unknown commands are impossible."""
    _require(name in _ALLOWLIST, "unknown fixed cloud operation")
    return tuple(_ALLOWLIST[name])


_TRANSPORT_SCHEMA = "P5R0VerifierBoundCredentialTransportV2"
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError:  # pragma: no cover
    Ed25519PrivateKey = Ed25519PublicKey = None  # type: ignore[assignment]
_TRANSPORT_TEST_KEY = Ed25519PrivateKey.generate() if Ed25519PrivateKey is not None else None


def _transport_payload(*, evidence_digest: str, target_service_account: str, expires_at: int, transport_bytes_digest: str, packet_digest: str | None = None, source_digest: str | None = None) -> dict[str, Any]:
    return {"schema": _TRANSPORT_SCHEMA, "evidence_digest": evidence_digest, "target_service_account": target_service_account, "expires_at": expires_at, "transport_bytes_digest": transport_bytes_digest, "packet_digest": packet_digest, "source_digest": source_digest or evidence_digest}


MAX_TRANSPORT_BYTES = 64 * 1024


def _fd_identity(fd: int) -> tuple[int, int, int, int]:
    try:
        info = os.fstat(fd)
    except OSError as exc:
        raise ReviewedIAMError("credential transport fd is unavailable") from exc
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size)


def _read_bounded_fd(fd: int) -> bytes:
    """Read exact bounded bytes while preserving a usable inherited FD.

    Regular/seekable descriptors are rewound to their original offset.  Pipes
    cannot be rewound, so their bytes are copied into a fresh pipe and dup2'd
    back onto the original descriptor number.  This keeps argv/env secret-free
    and makes the descriptor passed to gcloud the bytes that were verified.
    """
    identity = _fd_identity(fd)
    try:
        offset = os.lseek(fd, 0, os.SEEK_CUR)
        seekable = True
    except OSError:
        offset = None
        seekable = False
    chunks: list[bytes] = []
    total = 0
    was_blocking = True
    if not seekable:
        try:
            was_blocking = os.get_blocking(fd)
            os.set_blocking(fd, False)
        except OSError as exc:
            raise ReviewedIAMError("credential transport cannot be read safely") from exc
    try:
        while True:
            if not seekable and chunks and not select.select([fd], [], [], 0.05)[0]:
                break
            try:
                chunk = os.read(fd, min(8192, MAX_TRANSPORT_BYTES + 1 - total))
            except BlockingIOError:
                break
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_TRANSPORT_BYTES:
                raise ReviewedIAMError("credential transport is oversized")
    finally:
        if not seekable:
            os.set_blocking(fd, was_blocking)
    value = b"".join(chunks)
    if not value:
        raise ReviewedIAMError("credential transport reached EOF")
    try:
        if seekable:
            os.lseek(fd, int(offset), os.SEEK_SET)
        else:
            try:
                if hasattr(os, "memfd_create"):
                    replay_fd = os.memfd_create("ocelot-credential", os.MFD_CLOEXEC)
                    view = memoryview(value)
                    while view:
                        written = os.write(replay_fd, view)
                        view = view[written:]
                    os.lseek(replay_fd, 0, os.SEEK_SET)
                else:  # pragma: no cover - Linux production has memfd_create.
                    replay_fd, replay_write = os.pipe()
                    view = memoryview(value)
                    while view:
                        written = os.write(replay_write, view)
                        view = view[written:]
                    os.close(replay_write)
                os.dup2(replay_fd, fd)
                os.close(replay_fd)
            finally:
                pass
    except OSError as exc:
        raise ReviewedIAMError("credential transport cannot be safely replayed") from exc
    _require(_fd_identity(fd)[:3] == identity[:3] or not seekable, "credential transport descriptor changed")
    return value


class VerifierOwnedCredentialTransport:
    """A signed, bounded, verifier-owned credential transport envelope."""

    __slots__ = ("evidence_digest", "target_service_account", "expires_at", "token_fd", "transport_bytes_digest", "transport_digest", "evidence_signature", "verifier_public_key", "packet_digest", "source_digest", "descriptor_identity", "_seal")
    _SEAL = object()
    _registry: dict[int, tuple["VerifierOwnedCredentialTransport", tuple[Any, ...]]] = {}

    def __init__(self, *, evidence_digest: str, target_service_account: str, expires_at: int, token_fd: int, transport_bytes_digest: str, transport_digest: str, evidence_signature: str, verifier_public_key: str, packet_digest: str | None = None, source_digest: str | None = None, descriptor_identity: tuple[int, int, int, int] | None = None, _seal: object):
        _require(_seal is self._SEAL, "credential transport is verifier-created")
        _require(isinstance(token_fd, int) and token_fd > 2, "credential transport fd is invalid")
        _require(isinstance(evidence_digest, str) and evidence_digest.startswith("sha256:"), "credential transport evidence binding is invalid")
        _require(isinstance(transport_bytes_digest, str) and transport_bytes_digest.startswith("sha256:"), "credential transport byte commitment is invalid")
        self.evidence_digest, self.target_service_account, self.expires_at = evidence_digest, target_service_account, expires_at
        self.token_fd, self.transport_bytes_digest = token_fd, transport_bytes_digest
        self.transport_digest, self.evidence_signature, self.verifier_public_key = transport_digest, evidence_signature, verifier_public_key
        self.packet_digest, self.source_digest = packet_digest, source_digest or evidence_digest
        self.descriptor_identity = descriptor_identity or _fd_identity(token_fd)
        self._seal = _seal

    def _snapshot(self) -> tuple[Any, ...]:
        return (self.evidence_digest, self.target_service_account, self.expires_at, self.token_fd, self.transport_bytes_digest, self.transport_digest, self.evidence_signature, self.verifier_public_key, self.packet_digest, self.source_digest, self.descriptor_identity)

    def is_registered(self) -> bool:
        return self._registry.get(id(self), (None, None))[0] is self and self._registry[id(self)][1] == self._snapshot()

    def public_evidence(self) -> dict[str, Any]:
        return {**_transport_payload(evidence_digest=self.evidence_digest, target_service_account=self.target_service_account, expires_at=self.expires_at, transport_bytes_digest=self.transport_bytes_digest, packet_digest=self.packet_digest, source_digest=self.source_digest), "transport_digest": self.transport_digest, "signature": self.evidence_signature, "verifier_public_key": self.verifier_public_key}


def _verify_transport_signature(transport: VerifierOwnedCredentialTransport) -> bool:
    if Ed25519PublicKey is None:
        return False
    try:
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(transport.verifier_public_key, validate=True))
        payload = _transport_payload(evidence_digest=transport.evidence_digest, target_service_account=transport.target_service_account, expires_at=transport.expires_at, transport_bytes_digest=transport.transport_bytes_digest, packet_digest=transport.packet_digest, source_digest=transport.source_digest)
        key.verify(base64.b64decode(transport.evidence_signature, validate=True), canonical_bytes(payload))
        return transport.transport_digest == _digest(payload)
    except Exception:
        return False


def verify_transport_bytes(transport: VerifierOwnedCredentialTransport, transport_bytes: bytes) -> bool:
    """Verify exact bytes against the signed transport envelope."""
    _require(type(transport) is VerifierOwnedCredentialTransport and _verify_transport_signature(transport), "credential transport signature is invalid")
    return digest(transport_bytes) == transport.transport_bytes_digest


def issue_verifier_credential_transport(*, evidence_digest: str, target_service_account: str, expires_at: int, token_fd: int, transport_bytes: bytes | None = None, transport_bytes_digest: str | None = None, evidence_signature: str | None = None, verifier_public_key: str | None = None, packet_digest: str | None = None, source_digest: str | None = None) -> VerifierOwnedCredentialTransport:
    """Issue only after hashing the actual bounded FD contents.

    The optional ``transport_bytes`` is a test/source assertion; it is never
    stored.  A caller-supplied digest without readable matching FD bytes is
    rejected, including closed, empty, changed, and oversized descriptors.
    """
    actual = _read_bounded_fd(token_fd)
    actual_digest = digest(actual)
    if transport_bytes is not None:
        _require(actual == transport_bytes, "credential transport bytes do not match the signed envelope")
    if transport_bytes_digest is not None:
        _require(transport_bytes_digest == actual_digest, "credential transport byte digest does not match the FD")
    transport_bytes_digest = actual_digest
    payload = _transport_payload(evidence_digest=evidence_digest, target_service_account=target_service_account, expires_at=expires_at, transport_bytes_digest=transport_bytes_digest, packet_digest=packet_digest, source_digest=source_digest or evidence_digest)
    if evidence_signature is None:
        _require(_TRANSPORT_TEST_KEY is not None, "signed transport verifier is unavailable")
        evidence_signature = base64.b64encode(_TRANSPORT_TEST_KEY.sign(canonical_bytes(payload))).decode("ascii")
    if verifier_public_key is None:
        _require(_TRANSPORT_TEST_KEY is not None, "signed transport verifier is unavailable")
        verifier_public_key = base64.b64encode(_TRANSPORT_TEST_KEY.public_key().public_bytes_raw()).decode("ascii")
    transport = VerifierOwnedCredentialTransport(evidence_digest=evidence_digest, target_service_account=target_service_account, expires_at=expires_at, token_fd=token_fd, transport_bytes_digest=transport_bytes_digest, transport_digest=_digest(payload), evidence_signature=evidence_signature, verifier_public_key=verifier_public_key, packet_digest=packet_digest, source_digest=source_digest or evidence_digest, _seal=VerifierOwnedCredentialTransport._SEAL)
    _require(_verify_transport_signature(transport) and verify_transport_bytes(transport, actual), "verifier-signed credential transport is invalid")
    VerifierOwnedCredentialTransport._registry[id(transport)] = (transport, transport._snapshot())
    return transport


def _verify_live_transport(transport: VerifierOwnedCredentialTransport) -> None:
    _require(type(transport) is VerifierOwnedCredentialTransport and transport.is_registered() and _verify_transport_signature(transport), "verifier-owned signed credential transport is required")
    _require(_fd_identity(transport.token_fd) == transport.descriptor_identity, "credential transport descriptor mismatch")
    actual = _read_bounded_fd(transport.token_fd)
    _require(verify_transport_bytes(transport, actual), "credential transport bytes do not match signed envelope")
    _require(_fd_identity(transport.token_fd) == transport.descriptor_identity, "credential transport descriptor mismatch")

def build_signed_credential_transport_artifact(transport: VerifierOwnedCredentialTransport) -> dict[str, Any]:
    _require(type(transport) is VerifierOwnedCredentialTransport and transport.is_registered() and _verify_transport_signature(transport), "credential transport is not verifier-issued")
    value = {"schema": "P5R0SignedCredentialTransportV2", "transport": transport.public_evidence()}
    value["artifact_digest"] = _digest(value)
    return value


def load_signed_credential_transport_artifact(path: Path, *, trusted_public_key: str, signed_environment_source: Callable[[Mapping[str, Any]], int]) -> VerifierOwnedCredentialTransport:
    """Reissue a fresh FD from the signed environment after process restart."""
    try:
        artifact = parse_canonical(Path(path).read_bytes())
        _require(artifact.get("schema") == "P5R0SignedCredentialTransportV2", "credential transport artifact schema drift")
        _require(artifact.get("artifact_digest") == _digest({key: value for key, value in artifact.items() if key != "artifact_digest"}), "credential transport artifact digest drift")
        public = artifact.get("transport")
        _require(isinstance(public, Mapping) and public.get("verifier_public_key") == trusted_public_key, "credential transport signer is not trusted")
        _require(_verify_transport_public_payload(public, trusted_public_key), "credential transport signature is invalid")
        fresh_fd = signed_environment_source(dict(public))
        _require(isinstance(fresh_fd, int) and fresh_fd > 2, "signed environment did not issue a fresh transport fd")
        for existing, _snapshot in VerifierOwnedCredentialTransport._registry.values():
            if existing.token_fd == fresh_fd:
                _require(_fd_identity(fresh_fd) != existing.descriptor_identity, "signed environment attempted to reuse a stale transport fd")
        try:
            return issue_verifier_credential_transport(evidence_digest=public["evidence_digest"], target_service_account=public["target_service_account"], expires_at=public["expires_at"], token_fd=fresh_fd, transport_bytes_digest=public["transport_bytes_digest"], evidence_signature=public["signature"], verifier_public_key=trusted_public_key, packet_digest=public.get("packet_digest"), source_digest=public.get("source_digest"))
        except Exception:
            try:
                os.close(fresh_fd)
            except OSError:
                pass
            raise
    except ReviewedIAMError:
        raise
    except Exception as exc:
        raise ReviewedIAMError("signed credential transport rehydration failed") from exc


def reissue_verifier_credential_transport(*, artifact_path: Path, trusted_public_key: str, signed_environment_source: Callable[[Mapping[str, Any]], int]) -> VerifierOwnedCredentialTransport:
    return load_signed_credential_transport_artifact(artifact_path, trusted_public_key=trusted_public_key, signed_environment_source=signed_environment_source)


def _verify_transport_public_payload(public: Mapping[str, Any], trusted_public_key: str) -> bool:
    try:
        payload = _transport_payload(evidence_digest=public["evidence_digest"], target_service_account=public["target_service_account"], expires_at=public["expires_at"], transport_bytes_digest=public["transport_bytes_digest"], packet_digest=public.get("packet_digest"), source_digest=public.get("source_digest"))
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted_public_key, validate=True))
        key.verify(base64.b64decode(public["signature"], validate=True), canonical_bytes(payload))
        return public.get("transport_digest") == _digest(payload)
    except Exception:
        return False


class SubprocessGcloudRunner:
    """Shell-free runner with explicit inherited-fd credential transport only."""

    uses_adc = False
    exports_credentials = False
    creates_keys = False
    requires_explicit_credential_transport = True

    def __init__(self, *, executable: str = GCLOUD) -> None:
        _require(executable == GCLOUD, "only the reviewed absolute gcloud path is permitted")
        self.executable = executable

    def run(self, argv: Sequence[str], *, credential: InjectedSignedEnvironmentCredential | None = None) -> CommandResult:
        checked = tuple(argv)
        _require(checked in _ALLOWLIST.values(), "command is not in the reviewed gcloud allowlist")
        _require(checked[0] == GCLOUD, "absolute gcloud path is required")
        _require(type(credential) is InjectedSignedEnvironmentCredential, "explicit signed-environment credential is required")
        _require(credential.source == "signed_environment_injected" and credential.token_present is True and credential.ambient_adc is False and credential.exported is False and credential.contains_key_material is False, "ambient gcloud/ADC or exported credentials are forbidden")
        transport = credential.transport
        _require(type(transport) is VerifierOwnedCredentialTransport and transport.is_registered() and _verify_transport_signature(transport), "verifier-owned signed credential transport is required")
        _require(transport.evidence_digest == credential.evidence_digest and transport.target_service_account == credential.target_service_account and transport.expires_at == credential.expires_at and transport.transport_bytes_digest.startswith("sha256:"), "credential transport binding mismatch")
        if credential.packet_digest is not None:
            _require(transport.packet_digest == credential.packet_digest, "credential transport packet binding mismatch")
        _require(transport.source_digest == credential.evidence_digest, "credential transport source binding mismatch")
        _require(type(transport.expires_at) is int and transport.expires_at > int(__import__("time").time()), "signed-environment credential is expired")
        _verify_live_transport(transport)
        # No HOME, CLOUDSDK_CONFIG, ADC variables, metadata hints, or token
        # bytes are inherited. gcloud reads only the verified verifier-owned fd.
        env = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
        command = list(checked) + [f"--access-token-file=/proc/self/fd/{transport.token_fd}"]
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False, check=False, env=env, pass_fds=(transport.token_fd,))
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class FixedCommandIAMBackend:
    """Concrete IAM/GCS backend with no shell, ADC lookup, or key material."""

    reviewed = True
    direct_gcloud = True
    uses_adc = False
    exports_credentials = False
    creates_keys = False
    requires_explicit_credential_transport = True
    target_service_account = TARGET_ACCOUNT
    custom_role = CUSTOM_ROLE

    def __init__(self, *, runner: CommandRunner | None = None) -> None:
        self.runner = runner or SubprocessGcloudRunner()
        self._expected: dict[str, Any] | None = None
        self._credential: InjectedSignedEnvironmentCredential | None = None
        self._snapshots: dict[str, Any] = {}
        self.mutation_count = 0

    def bind_credential(self, credential: InjectedSignedEnvironmentCredential) -> None:
        _require(type(credential) is InjectedSignedEnvironmentCredential, "explicit signed-environment credential is required")
        _require(type(credential.transport) is VerifierOwnedCredentialTransport and credential.transport.is_registered() and _verify_transport_signature(credential.transport), "verifier-owned signed credential transport is required")
        _require(credential.transport.evidence_digest == credential.evidence_digest and credential.transport.target_service_account == credential.target_service_account and credential.transport.expires_at == credential.expires_at and credential.transport.transport_bytes_digest.startswith("sha256:"), "credential transport binding mismatch")
        if credential.packet_digest is not None:
            _require(credential.transport.packet_digest == credential.packet_digest, "credential transport packet binding mismatch")
        _require(credential.transport.source_digest == credential.evidence_digest, "credential transport source binding mismatch")
        self._credential = credential

    def validate_credential_binding(self, expected: Mapping[str, str]) -> None:
        _require(self._credential is not None, "explicit signed-environment credential is required")
        _require(self._credential.evidence_digest == expected["evidence_digest"], "credential evidence transport mismatch")
        self.bind_credential(self._credential)

    def _run(self, name: str, *, optional: bool = False) -> dict[str, Any] | None:
        if isinstance(self.runner, SubprocessGcloudRunner):
            result = self.runner.run(allowlisted_argv(name), credential=self._credential)
        elif getattr(self.runner, "requires_explicit_credential_transport", False):
            _require(type(self._credential) is InjectedSignedEnvironmentCredential and type(self._credential.transport) is VerifierOwnedCredentialTransport, "credential transport mismatch")
            result = self.runner.run(allowlisted_argv(name), credential=self._credential)
        else:
            result = self.runner.run(allowlisted_argv(name))
        if result.returncode != 0:
            not_found = result.returncode == 1 and any(line.strip() == "NOT_FOUND" for line in f"{result.stdout}\n{result.stderr}".splitlines())
            if optional and not_found:
                return None
            raise ReviewedIAMError(f"fixed gcloud operation failed: {name}")
        try:
            value = json.loads(result.stdout or "{}")
        except Exception as exc:
            raise ReviewedIAMError(f"fixed gcloud operation returned invalid JSON: {name}") from exc
        _require(isinstance(value, dict) or isinstance(value, list), f"fixed gcloud operation returned malformed JSON: {name}")
        return value

    @staticmethod
    def _policy(raw: Mapping[str, Any]) -> dict[str, Any]:
        bindings: list[dict[str, Any]] = []
        for binding in raw.get("bindings", []):
            condition = binding.get("condition")
            if condition is not None:
                condition = {key: condition[key] for key in ("title", "expression") if key in condition}
            for member in binding.get("members", []):
                bindings.append({"member": member, "role": binding.get("role"), "condition": condition})
        return {"etag": raw.get("etag"), "bindings": sorted(bindings, key=lambda item: (item["member"], item["role"], json.dumps(item["condition"], sort_keys=True)))}

    def _account(self, email: str, prefix: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
        raw = self._run(f"{prefix}_describe", optional=True)
        if raw is None:
            return {"email": email, "exists": False, "has_key_material": False, "project_roles": []}, None
        keys = self._run(f"{prefix}_keys")
        policy = self._policy(self._run(f"{prefix}_policy") or {})
        return {"email": email, "exists": True, "has_key_material": bool(keys), "project_roles": []}, policy

    def describe_prestate(self) -> Mapping[str, Any]:
        project = self._run("project_describe") or {}
        bucket = self._run("bucket_describe") or {}
        project_policy = self._policy(self._run("project_policy") or {})
        bucket_policy = self._policy(self._run("bucket_policy") or {})
        existing, existing_policy = self._account(EXISTING_ACCOUNT, "existing")
        target, target_policy = self._account(TARGET_ACCOUNT, "target")
        for account in (existing, target):
            account["project_roles"] = [item["role"] for item in project_policy["bindings"] if item["member"] == f"serviceAccount:{account['email']}"]
        role_raw = self._run("role_describe", optional=True)
        role = {"name": CUSTOM_ROLE, "exists": role_raw is not None, "etag": None, "fingerprint": None, "title": None, "stage": None, "permissions": []}
        if role_raw is not None:
            role.update({"etag": role_raw.get("etag"), "fingerprint": role_raw.get("fingerprint"), "title": role_raw.get("title"), "stage": role_raw.get("stage"), "permissions": list(role_raw.get("includedPermissions", []))})
        visibility = bucket.get("iamConfiguration", {})
        state = {
            "project": {"project_id": project.get("projectId", PROJECT_ID), "project_number": str(project.get("projectNumber", PROJECT_NUMBER))},
            "bucket": {"name": BUCKET, "project_id": bucket.get("project", PROJECT_ID), "uniform_bucket_level_access": visibility.get("uniformBucketLevelAccess", {}).get("enabled", False), "public_access_prevention": visibility.get("publicAccessPrevention", "unspecified")},
            "bucket_policy": bucket_policy,
            "existing_account": existing,
            "existing_account_policy": existing_policy,
            "target_account": target,
            "target_account_policy": target_policy,
            "custom_role": role,
        }
        return iam.normalize_prestate(state)

    def bind_expected_prestate(self, expected: Mapping[str, Any]) -> None:
        self._expected = copy.deepcopy(dict(expected))

    def _current(self) -> dict[str, Any]:
        _require(self._expected is not None, "fixed backend has no exact prestate binding")
        return dict(iam.normalize_prestate(self.describe_prestate()))

    def _mutate(self, name: str, *resources: str) -> None:
        # Mark attempted before crossing the remote effect boundary.  A
        # transport exception can follow a successful remote write.
        self.mutation_count += 1
        self._run(name)
        current = self._current()
        for resource in resources:
            self._snapshots[resource] = copy.deepcopy(current[resource])

    def _guard_rollback_resource(self, resource: str, current: Mapping[str, Any]) -> None:
        expected = self._snapshots.get(resource, self._expected[resource])
        _require(current == expected, f"{resource} version/state drift during rollback")

    def _require_same(self, current: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
        _require(current == expected, f"{label} precondition drift")

    def ensure_service_account(self, email: str) -> None:
        _require(email == TARGET_ACCOUNT, "service-account target drift")
        current = self._current()
        account = current["target_account"]
        expected = self._expected["target_account"]
        if not expected["exists"]:
            _require(account["exists"] is False, "target service-account precondition drift")
            self._mutate("account_create", "target_account", "target_account_policy")
            return
        _require(account == expected and account["has_key_material"] is False and account["project_roles"] == [], "existing target account is not GCS-only")

    def apply_custom_role(self, request: Mapping[str, Any] | None = None) -> None:
        current = self._current()
        role = current["custom_role"]
        expected = self._expected["custom_role"]
        if not expected["exists"]:
            _require(role["exists"] is False, "custom role precondition drift")
            self._mutate("role_create", "custom_role")
            return
        _require(role["exists"] is True and iam._version_value(role) == iam._version_value(expected), "custom role version drift")
        self._mutate("role_update", "custom_role")

    def update_bucket_policy(self, request: Mapping[str, Any] | None = None) -> None:
        current = self._current()
        _require(current["bucket"] == self._expected["bucket"], "bucket visibility precondition drift")
        _require(current["bucket_policy"] == self._expected["bucket_policy"], "bucket policy etag/fingerprint drift")
        self._mutate("bucket_add_exact", "bucket_policy")
        self._mutate("bucket_remove_broad", "bucket_policy")
        self._mutate("bucket_remove_stale", "bucket_policy")

    def update_target_account_policy(self, request: Mapping[str, Any] | None = None) -> None:
        current = self._current()
        _require(current["target_account"]["exists"] is True, "target account was not created")
        expected_account = self._expected["target_account"]
        expected_policy = self._expected["target_account_policy"]
        if expected_account["exists"]:
            _require(current["target_account_policy"] == expected_policy, "target service-account policy etag/fingerprint drift")
        else:
            _require(current["target_account_policy"] is not None and current["target_account_policy"]["bindings"] == [], "target service-account policy precondition drift")
        self._mutate("target_add_token_creator", "target_account_policy")

    def describe_poststate(self) -> Mapping[str, Any]:
        return self.describe_prestate()

    def _bucket_bindings_allowed_for_rollback(self, bindings: list[dict[str, Any]]) -> bool:
        expected = self._expected["bucket_policy"]["bindings"]
        broad = {"member": f"serviceAccount:{EXISTING_ACCOUNT}", "role": BROAD_ROLE, "condition": None}
        stale = {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}}
        exact = {"member": f"serviceAccount:{TARGET_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}
        base = [item for item in expected if item != broad and item != stale]
        for mask in range(8):
            candidate = list(base)
            if mask & 1:
                candidate.append(broad)
            if mask & 2:
                candidate.append(stale)
            if mask & 4:
                candidate.append(exact)
            if Counter(map(repr, candidate)) == Counter(map(repr, bindings)):
                return True
        return False

    def restore_target_account_policy(self, request: Mapping[str, Any] | None = None) -> None:
        current = self._current()
        policy = current["target_account_policy"]
        _require(policy is not None, "target policy disappeared during rollback")
        self._guard_rollback_resource("target_account_policy", policy)
        token = {"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}
        expected = self._expected["target_account_policy"]
        if self._expected["target_account"]["exists"]:
            allowed = [expected["bindings"], expected["bindings"] + [token]]
            _require(any(Counter(map(repr, candidate)) == Counter(map(repr, policy["bindings"])) for candidate in allowed), "target policy rollback drift")
        else:
            _require(policy["bindings"] in ([], [token]), "target policy rollback drift")
        if token in policy["bindings"]:
            self._run("target_remove_token_creator")

    def restore_bucket_policy(self, request: Mapping[str, Any] | None = None) -> None:
        current = self._current()
        self._guard_rollback_resource("bucket_policy", current["bucket_policy"])
        _require(current["bucket"]["name"] == BUCKET and self._bucket_bindings_allowed_for_rollback(current["bucket_policy"]["bindings"]), "bucket rollback drift; manual review required")
        exact = {"member": f"serviceAccount:{TARGET_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}
        broad = {"member": f"serviceAccount:{EXISTING_ACCOUNT}", "role": BROAD_ROLE, "condition": None}
        stale = {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}}
        bindings = current["bucket_policy"]["bindings"]
        if exact in bindings:
            self._run("bucket_remove_exact")
        if broad not in bindings:
            self._run("bucket_add_broad")
        if stale not in bindings:
            self._run("bucket_add_stale")

    def restore_custom_role(self, request: Mapping[str, Any] | None = None) -> None:
        expected = self._expected["custom_role"] if self._expected else None
        _require(expected is not None, "custom role rollback lacks prestate")
        current = self._current()["custom_role"]
        self._guard_rollback_resource("custom_role", current)
        if not expected["exists"]:
            if not current["exists"]:
                return
            _require(current["title"] == CUSTOM_ROLE_TITLE and current["stage"] == CUSTOM_ROLE_STAGE and current["permissions"] == CUSTOM_ROLE_PERMISSIONS, "custom role rollback drift; manual review required")
            self._run("role_delete")
            return
        _require(expected["title"] == CUSTOM_ROLE_TITLE and expected["stage"] == CUSTOM_ROLE_STAGE and expected["permissions"] == CUSTOM_ROLE_PERMISSIONS, "existing custom role cannot be safely restored")
        _require(current["exists"] is True and current["title"] == CUSTOM_ROLE_TITLE and current["stage"] == CUSTOM_ROLE_STAGE and current["permissions"] == CUSTOM_ROLE_PERMISSIONS, "custom role rollback drift; manual review required")
        self._mutate("role_update", "custom_role")


class ExecutorBackend(Protocol):
    def describe_prestate(self) -> Mapping[str, Any]: ...
    def bind_expected_prestate(self, expected: Mapping[str, Any]) -> None: ...
    def ensure_service_account(self, email: str) -> None: ...
    def apply_custom_role(self, request: Mapping[str, Any] | None = None) -> None: ...
    def update_bucket_policy(self, request: Mapping[str, Any] | None = None) -> None: ...
    def update_target_account_policy(self, request: Mapping[str, Any] | None = None) -> None: ...
    def describe_poststate(self) -> Mapping[str, Any]: ...
    def restore_target_account_policy(self, request: Mapping[str, Any] | None = None) -> None: ...
    def restore_bucket_policy(self, request: Mapping[str, Any] | None = None) -> None: ...
    def restore_custom_role(self, request: Mapping[str, Any] | None = None) -> None: ...


def _load_expected_prestate() -> dict[str, Any]:
    artifact = _load_json(REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json")
    _require(artifact.get("artifact_digest") == PRESTATE_ARTIFACT_DIGEST, "IAM prestate artifact digest drift")
    _require(artifact.get("artifact_digest") == _digest_without(artifact, "artifact_digest"), "IAM prestate artifact seal drift")
    raw_state = artifact.get("state")
    _require(isinstance(raw_state, Mapping), "IAM prestate state is missing")
    _require(raw_state.get("state_digest") == PRESTATE_STATE_DIGEST, "IAM prestate raw state digest drift")
    _require(raw_state.get("state_digest") == _digest_without(raw_state, "state_digest"), "IAM prestate raw state seal drift")
    expected = iam.normalize_prestate(raw_state)
    _require(expected["state_digest"] == PRESTATE_NORMALIZED_DIGEST, "IAM prestate normalized state digest drift")
    return expected


def _exact_poststate(post: Mapping[str, Any], pre: Mapping[str, Any]) -> dict[str, Any]:
    checked = iam.validate_poststate(post, pre)
    expected_bucket = [item for item in pre["bucket_policy"]["bindings"] if not (
        (item["member"] == f"serviceAccount:{EXISTING_ACCOUNT}" and item["role"] == BROAD_ROLE)
        or (item["member"] == STALE_WIF_PRINCIPAL and item["role"] == STALE_WIF_ROLE)
    )]
    expected_bucket.append({"member": f"serviceAccount:{TARGET_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}})
    _require(Counter(map(repr, checked["bucket_policy"]["bindings"])) == Counter(map(repr, expected_bucket)), "poststate bucket policy is not exact")
    _require(checked["target_account_policy"]["bindings"] == [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}], "poststate token-creator policy is not exact")
    _require(checked["target_account"]["has_key_material"] is False and checked["target_account"]["project_roles"] == [], "poststate target account is not GCS-only")
    return checked


def _receipt(pre: Mapping[str, Any], post: Mapping[str, Any]) -> dict[str, Any]:
    value = {
        "schema": "P5R0APPROVAL023IAMReceiptV1",
        "operation_id": OPERATION_ID,
        "project_id": PROJECT_ID,
        "bucket": BUCKET,
        "service_account": TARGET_ACCOUNT,
        "custom_role": CUSTOM_ROLE,
        "custom_role_permissions": CUSTOM_ROLE_PERMISSIONS,
        "wif_principal": WIF_PRINCIPAL,
        "condition_title": EXACT_CONDITION_TITLE,
        "condition_expression": EXACT_CONDITION,
        "private": True,
        "prestate_digest": pre["state_digest"],
        "poststate_digest": post["state_digest"],
        "prestate_versions": {"bucket_policy": iam._version_value(pre["bucket_policy"]), "existing_account_policy": iam._version_value(pre["existing_account_policy"]), "custom_role": iam._version_value(pre["custom_role"] if pre["custom_role"]["exists"] else None)},
        "poststate_versions": {"bucket_policy": iam._version_value(post["bucket_policy"]), "existing_account_policy": iam._version_value(post["existing_account_policy"]), "target_account_policy": iam._version_value(post["target_account_policy"]), "custom_role": iam._version_value(post["custom_role"])},
        "later_operations_enabled": False,
        "credentials_exported": False,
        "keys_created": False,
    }
    return {**value, "receipt_digest": _digest(value)}


def _append_event(path: Path, body: Mapping[str, Any], previous: str | None) -> dict[str, Any]:
    event = {**dict(body), "previous_event_digest": previous}
    event["event_digest"] = _digest(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(canonical_bytes(event) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return event


def _reserve_ledger(path: Path, common: Mapping[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ReviewedIAMError("IAM attempt already exists; retry is disabled") from exc
    os.close(fd)
    return _append_event(path, {**common, "kind": "run_started", "mutations_performed": False}, None)


def _fixed_requests(expected: Mapping[str, Any]) -> dict[str, Any]:
    definition = _load_json(REPOSITORY_ROOT / SOURCE_PATHS["iam_definition_path"])
    requests = iam._desired_requests(definition, expected)
    iam._validate_requests(requests, expected)
    return requests


def _rollback_requests(current: Mapping[str, Any], expected: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "target_account_policy": {"schema": "P5R0DISPATCH050ServiceAccountPolicyRestoreV1", "service_account": TARGET_ACCOUNT, "expected_version": iam._version_value(current["target_account_policy"]), "expected_absent": current["target_account_policy"] is None, "restore_state": expected["target_account_policy"]},
        "bucket_policy": {"schema": "P5R0DISPATCH050BucketPolicyRestoreV1", "bucket": BUCKET, "expected_version": iam._version_value(current["bucket_policy"]), "expected_absent": False, "restore_state": expected["bucket_policy"]},
        "custom_role": {"schema": "P5R0DISPATCH050CustomRoleRestoreV1", "resource": CUSTOM_ROLE, "expected_version": iam._version_value(current["custom_role"] if current["custom_role"]["exists"] else None), "expected_absent": not current["custom_role"]["exists"], "restore_state": expected["custom_role"]},
    }


class ReviewedFixedCommandExecutor:
    """One exact APPROVAL-023 attempt, with signed prerequisites and closure."""

    def __init__(
        self,
        *,
        backend: ExecutorBackend,
        packet_path: Path = DEFAULT_PACKET,
        credential: InjectedSignedEnvironmentCredential | None = None,
        credential_evidence: VerifiedCredentialReadinessEvidence | None = None,
        child_approval: VerifiedIAMChildApproval | None = None,
        signature_verifier: VerifiedIAMApprovalSignatureVerifier | None = None,
        ledger_root_signer: Callable[[Mapping[str, Any]], str] | None = None,
        clock: Callable[[], float] = __import__("time").time,
    ) -> None:
        self.backend = backend
        self.packet = _load_packet(packet_path)
        self.credential = credential
        self.credential_evidence = credential_evidence
        self.child_approval = child_approval
        self.signature_verifier = signature_verifier
        self.ledger_root_signer = ledger_root_signer
        self.clock = clock

    def _validate_apply_prerequisites(self, expected: Mapping[str, Any]) -> dict[str, Any]:
        _require(type(self.credential) is InjectedSignedEnvironmentCredential, "verifier-issued signed-environment credential object is required")
        _require(type(self.credential_evidence) is VerifiedCredentialReadinessEvidence and _is_registered_credential_evidence(self.credential_evidence), "verifier-issued credential evidence is required")
        evidence = self.credential_evidence
        credential = self.credential
        _require(evidence.seal_digest == _commitment({field: getattr(evidence, field) for field in evidence.__dataclass_fields__}), "credential evidence seal digest drift")
        evidence_digest = evidence.signed_environment_evidence_digest
        _require(evidence.packet_digest == self.packet["artifact_digest"] and credential.packet_digest == self.packet["artifact_digest"], "credential packet digest binding drift")
        _require(credential.evidence_digest == evidence_digest, "credential evidence digest binding drift")
        _require(evidence.authority_binding_digest == credential.authority_binding_digest == AUTHORITY_BINDING_DIGEST, "credential authority binding drift")
        _require(evidence.service_account == credential.target_service_account == TARGET_ACCOUNT, "credential target account drift")
        _require(evidence.provider == credential.provider == iam.WIF_PROVIDER and evidence.image_digest == credential.image_digest == iam.WIF_IMAGE_DIGEST and evidence.audience == credential.audience == iam.STS_AUDIENCE, "credential signed-environment provenance drift")
        _require(credential.source == "signed_environment_injected" and credential.token_present is True and credential.exported is False and credential.contains_key_material is False and credential.ambient_adc is False, "credential handling crosses the no-key/no-ADC boundary")
        _require(credential.target_resource == f"projects/{PROJECT_ID}/serviceAccounts/{TARGET_ACCOUNT}" and credential.principal == WIF_PRINCIPAL, "credential capability binding drift")
        now = int(self.clock())
        _require(type(credential.expires_at) is int and credential.expires_at > now, "signed-environment credential is expired")
        _require(type(evidence.expires_at) is int and evidence.expires_at > now and evidence.expires_at == credential.expires_at, "credential evidence expiry is not live")
        _require(getattr(self.backend, "reviewed", False) is True and getattr(self.backend, "uses_adc", True) is False and getattr(self.backend, "direct_gcloud", True) is False, "effectful IAM backend must be the reviewed credential adapter")
        if getattr(self.backend, "requires_explicit_credential_transport", False):
            _require(type(credential.transport) is VerifierOwnedCredentialTransport and credential.transport.is_registered() and _verify_transport_signature(credential.transport), "verifier-owned signed credential transport is required")
            _require(credential.transport.evidence_digest == evidence_digest and credential.transport.target_service_account == credential.target_service_account and credential.transport.expires_at == credential.expires_at and credential.transport.transport_bytes_digest.startswith("sha256:"), "credential transport binding mismatch")
            _require(credential.transport.source_digest == credential.evidence_digest, "credential transport source binding mismatch")
            _require(credential.transport.packet_digest == credential.packet_digest, "credential transport packet binding mismatch")
            _verify_live_transport(credential.transport)
        _require(callable(getattr(self.backend, "validate_credential_binding", None)), "reviewed IAM backend credential verifier is required")
        binder = getattr(self.backend, "bind_credential", None)
        if callable(binder):
            binder(credential)
        self.backend.validate_credential_binding({"packet_digest": self.packet["artifact_digest"], "evidence_digest": evidence_digest})
        checked_approval = _validate_approval(self.child_approval, packet=self.packet, prestate=expected, credential_evidence_digest=evidence_digest, now=now, signature_verifier=self.signature_verifier)
        _require(checked_approval["expires_at"] <= evidence.expires_at <= credential.expires_at, "approval lifetime exceeds credential evidence")
        return {"credential_evidence_digest": evidence_digest, "approval_digest": self.child_approval.approval_digest}

    def apply(self, *, ledger_path: Path = DEFAULT_LEDGER) -> dict[str, Any]:
        expected = _load_expected_prestate()
        bindings = self._validate_apply_prerequisites(expected)
        requests = _fixed_requests(expected)
        common = {"schema": LEDGER_SCHEMA, "operation_id": OPERATION_ID, "dispatch_id": DISPATCH_ID, "approval_id": PARENT_APPROVAL_ID, "attempt_id": ATTEMPT_ID, "packet_digest": self.packet["artifact_digest"], "prestate_digest": expected["state_digest"], "credential_evidence_digest": bindings["credential_evidence_digest"], "child_approval_digest": bindings["approval_digest"], "later_operations_enabled": False, "cloud_operations": ["iam.service_account_create", "iam.custom_role_create_or_update", "iam.bucket_iam_add_remove", "iam.target_service_account_token_creator", "iam.poststate_describe"], "credentials_exported": False, "keys_created": False}
        started = _reserve_ledger(Path(ledger_path), common)
        previous = started["event_digest"]
        mutation_started = False
        completed_mutation = False
        phase = "prestate_describe"
        try:
            observed = iam.normalize_prestate(self.backend.describe_prestate())
            iam.validate_prestate(observed, expected)
            binder = getattr(self.backend, "bind_expected_prestate", None)
            if callable(binder):
                binder(expected)
            verified_pre = _append_event(Path(ledger_path), {**common, "kind": "prestate_verified", "prestate_digest": observed["state_digest"], "mutations_performed": False}, previous)
            previous = verified_pre["event_digest"]
            phase = "ensure_service_account"
            mutation_started = True
            self.backend.ensure_service_account(TARGET_ACCOUNT)
            completed_mutation = True
            phase = "custom_role"
            mutation_started = True
            self.backend.apply_custom_role(requests["custom_role"])
            completed_mutation = True
            phase = "bucket_policy"
            mutation_started = True
            self.backend.update_bucket_policy(requests["bucket_policy"])
            completed_mutation = True
            phase = "target_account_policy"
            mutation_started = True
            self.backend.update_target_account_policy(requests["target_account_policy"])
            completed_mutation = True
            phase = "poststate_describe"
            post_observation = iam.normalize_prestate(self.backend.describe_poststate())
            post = _exact_poststate(post_observation, expected)
            receipt = _receipt(expected, post)
            verified = _append_event(Path(ledger_path), {**common, "kind": "poststate_verified", "poststate_digest": post["state_digest"], "receipt": receipt, "mutations_performed": True}, previous)
            _require(type(self.signature_verifier) is VerifiedIAMApprovalSignatureVerifier, "trusted IAM ledger-root verifier is required")
            if self.ledger_root_signer is None:
                _require(_TEST_VERIFIER_KEY is not None and self.signature_verifier.public_key == base64.b64encode(_TEST_VERIFIER_KEY.public_key().public_bytes_raw()).decode("ascii"), "external IAM ledger-root signer is required")
            signer = self.ledger_root_signer or _sign_ledger_root_payload
            ledger_root = issue_signed_iam_ledger_root(records=[started, verified_pre, verified, {}], signer=signer, public_key=self.signature_verifier.public_key)
            stopped = _append_event(Path(ledger_path), {**common, "kind": "run_stopped", "status": "verified", "verified_event_digest": verified["event_digest"], "rollback_status": "not_required_verified", "receipt": receipt, "ledger_root": ledger_root, "mutations_performed": True}, verified["event_digest"])
            result = {"status": "verified", "operation_id": OPERATION_ID, "attempt_id": ATTEMPT_ID, "ledger_head_digest": stopped["event_digest"], "poststate_digest": post["state_digest"], "receipt": receipt, "mutations_performed": True, "later_operations_enabled": False}
            result["iam_predecessor"] = load_verified_iam_predecessor(
                ledger_path=Path(ledger_path), operation_id=OPERATION_ID, attempt_id=ATTEMPT_ID,
                evidence_digest=bindings["credential_evidence_digest"], packet_digest=self.packet["artifact_digest"],
                prestate_digest=expected["state_digest"], trusted_verifier=self.signature_verifier,
            )
            return result
        except Exception as exc:
            rollback_status = "not_applicable_no_mutation"
            rollback_receipt: dict[str, Any] | None = None
            if mutation_started:
                try:
                    # Reobserve first even when the call raised: the remote
                    # operation may have committed before transport failure.
                    rollback_current = iam.normalize_prestate(self.backend.describe_poststate())
                    known_mutation = completed_mutation or (isinstance(getattr(self.backend, "mutation_count", None), int) and getattr(self.backend, "mutation_count") > 0)
                    if _semantic_state_equal(rollback_current, expected) and not known_mutation:
                        rollback_status = "not_applicable_no_mutation"
                    else:
                        rollback_requests = _rollback_requests(rollback_current, expected)
                        self.backend.restore_target_account_policy(rollback_requests["target_account_policy"])
                        self.backend.restore_bucket_policy(rollback_requests["bucket_policy"])
                        self.backend.restore_custom_role(rollback_requests["custom_role"])
                        restored = iam.normalize_prestate(self.backend.describe_poststate())
                        semantically_restored = _semantic_state_equal(restored, expected)
                        rollback_body = {"schema": "P5R0APPROVAL023IAMRollbackReceiptV2", "prestate_digest": expected["state_digest"], "restored_state_digest": restored["state_digest"], "restored_resource_digests": _credential_resource_digests(restored), "restored_versions": _credential_versions(restored), "verified": semantically_restored, "manual_review_required": not semantically_restored}
                        rollback_receipt = {**rollback_body, "receipt_digest": _digest(rollback_body)}
                        rollback_status = "rolled_back_verified" if semantically_restored else "rollback_failed_manual_review"
                except Exception:
                    rollback_status = "rollback_failed_manual_review"
                    rollback_body = {"schema": "P5R0APPROVAL023IAMRollbackReceiptV2", "prestate_digest": expected["state_digest"], "restored_state_digest": None, "restored_resource_digests": {}, "restored_versions": {}, "verified": False, "manual_review_required": True}
                    rollback_receipt = {**rollback_body, "receipt_digest": _digest(rollback_body)}
            stopped = _append_event(Path(ledger_path), {**common, "kind": "run_stopped", "status": "failed_closed", "failed_phase": phase, "error_type": type(exc).__name__, "rollback_status": rollback_status, "rollback_receipt": rollback_receipt, "mutations_performed": mutation_started, "manual_review_required": rollback_status == "rollback_failed_manual_review"}, previous)
            return {"status": "failed_closed", "operation_id": OPERATION_ID, "attempt_id": ATTEMPT_ID, "ledger_head_digest": stopped["event_digest"], "mutations_performed": mutation_started, "rollback_status": rollback_status, "manual_review_required": rollback_status == "rollback_failed_manual_review", "later_operations_enabled": False}


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="APPROVAL-023/DISPATCH-082 reviewed fixed-command IAM runner")
    parser.add_argument("command", choices=("validate", "apply"))
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args(argv)
    packet = _load_packet(args.packet)
    if args.command == "validate":
        _load_expected_prestate()
        print(json.dumps({"schema": PACKET_SCHEMA, "status": packet["status"], "dispatch_id": DISPATCH_ID, "approval_id": PARENT_APPROVAL_ID, "attempt_id": ATTEMPT_ID, "cloud_operations": [], "mutations_performed": False, "applied_state": False, "later_operations_enabled": False, "apply_prerequisites": APPLY_PREREQUISITES, "future_apply_command": FUTURE_APPLY_COMMAND}, sort_keys=True, separators=(",", ":")))
        return 0
    # CLI callers cannot provide opaque verifier-owned objects without
    # exporting credentials or unsigned approval material.  Keep the command
    # read-only; the object API is the only possible apply entrypoint.
    print(json.dumps({"schema": PACKET_SCHEMA, "status": "blocked_missing_verifier_prerequisites", "applied_state": False, "mutations_performed": False, "later_operations_enabled": False, "apply_prerequisites": APPLY_PREREQUISITES}, sort_keys=True, separators=(",", ":")))
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = ["ALLOWLIST", "APPLY_PREREQUISITES", "AUTHORITY_BINDING_DIGEST", "BUCKET", "CommandResult", "DEFAULT_LEDGER", "DEFAULT_PACKET", "FUTURE_APPLY_COMMAND", "FixedCommandIAMBackend", "ReviewedFixedCommandExecutor", "ReviewedIAMError", "SubprocessGcloudRunner", "VerifierOwnedCredentialTransport", "VerifiedIAMApprovalSignatureVerifier", "VerifiedIAMChildApproval", "allowlisted_argv", "issue_verifier_credential_transport", "verify_transport_bytes", "build_signed_credential_transport_artifact", "load_signed_credential_transport_artifact", "reissue_verifier_credential_transport", "load_verified_iam_child_approval", "build_signed_iam_child_approval_artifact"]
ALLOWLIST = _ALLOWLIST
