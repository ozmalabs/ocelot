"""DISPATCH-052 repository-only R18R13 IAM boundary.

This validator binds a new IAM packet/approval to the exact current
read-only evidence and immutable R18R12 dependency.  It deliberately keeps
execution blocked while signed-environment credential evidence and the
reviewed adapter preconditions are absent.  It never calls cloud tooling,
creates credentials, or edits historical packets, ledgers, or the master
runsheet.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.credential_evidence import VerifiedCredentialReadinessEvidence, _commitment
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import (
    IAMProvisioningError,
    ReviewedIAMExecutorAdapter,
    _desired_requests,
    _validate_requests,
    _version_value,
    build_receipt,
    normalize_prestate,
    validate_definition,
    validate_poststate,
    validate_prestate,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PACKET = Path(__file__).with_name("rs069r18r13-iam-boundary-packet-v2.json")
DEFAULT_APPROVAL = Path(__file__).with_name("rs069r18r13-iam-approval-v3.json")
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-0-dispatch-052-iam-ledger.jsonl"
DEFAULT_PRESTATE = REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json"
DEFAULT_CREDENTIAL = REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-credential-binding-evidence-v1.json"
DEFAULT_AUTHORITY = Path(__file__).with_name("rs-069r18r12-binding-review.json")
DEFAULT_R18R12_APPROVAL = Path(__file__).with_name("rs-069r18r12-operation-3-approval.json")
DEFAULT_R18R12_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-3-r18r12-ledger.jsonl"

PACKET_SCHEMA = "P5R0RS069R18R13IAMBoundaryPacketV2"
APPROVAL_SCHEMA = "P5R0RS069R18R13IAMApprovalV3"
OPERATION_ID = "provision_gcs_only_iam_boundary"
GCS_ONLY_ACCOUNT = "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com"
BUCKET = "p5-evaluator-ocelot-proof-141633828616"
CUSTOM_ROLE = "projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PACKET_DIGEST = "sha256:a9b975dc9a66ec5bc12a9c3dd8c825f494ddbe76b4b3e51578b7f2b367b2b546"
APPROVAL_DIGEST = "sha256:4314b6699bd5f56135e8d5d2f48daed5ee4254275eaf7376db14bf69a013b682"
PRESTATE_ARTIFACT_DIGEST = "sha256:03c83325fd531f0a2db39f0d54d02b10ae7cfa96577ab3cc93046602f109b946"
PRESTATE_STATE_DIGEST = "sha256:a7580109437962f92903ff8d03f03a3f3de386b1da0f51e2cb73aff2518dc692"
CREDENTIAL_DIGEST = "sha256:725608ffadaadc94bbcb0ff9fc640d14350f914c5508530969a584df65fedeef"
AUTHORITY_DIGEST = "sha256:c8e186d51eb0dcce6d3b2db4939f0e62af69ee88fc5ada19c4ad8c878245fd61"
AUTHORITY_BINDING_DIGEST = "sha256:9837a8f8e5f214a474f685e259f0acb1d6b6fff4b02d9ebbc3919fbf1e7c13e6"
R18R12_APPROVAL_DIGEST = "sha256:cfa0b7cc40f288282fdb432538460fc65cc4b0c8d3d247c73786fd4fa5cc9dd0"
R18R12_VERIFIED_EVENT_DIGEST = "sha256:bbb534870778e46c38c6e0fc03dbc36f47f5f78c6127b12ef2e8557877f0a727"
R18R12_LEDGER_HEAD_DIGEST = "sha256:30a59807d8dbf7aa2529d4efab406b4dcd5e87597442be71045827c816833329"
OLD_PACKET_DIGEST = "sha256:a8c313f6e5b775b4ba48a8e8ff4cc5e2561c560930c4e89ec2e9666fb509c447"
IAM_DEFINITION_DIGEST = "sha256:817ce6cff5f25487ba131a2d587fbcd489a52245e3a8173aa6320862ed49ce25"
GCS_DEFINITION_DIGEST = "sha256:705c5323a8bf8f300547d2051cf128825b03e0415c334dd452cd4e9db0280ee2"


class IAMBoundaryError(ValueError):
    """The DISPATCH-052 packet is malformed or not safe to apply."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IAMBoundaryError(message)


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return sha256({key: item for key, item in value.items() if key != field})


def _digest(value: Any) -> str:
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _is_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None, f"{label} is missing or invalid")


CREDENTIAL_UNRESOLVED = "unresolved"
CREDENTIAL_VERIFIED = "verified"
_UNRESOLVED_PACKET_STATUS = "required_but_not_injected"
_VERIFIED_PACKET_STATUS = "injected_reviewed_execution_path"
_CREDENTIAL_PROVIDER = "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production"
_CREDENTIAL_IMAGE_DIGEST = "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c"
_CREDENTIAL_AUDIENCE = "https://sts.googleapis.com"


def _active_credential_contract(*, evidence_digest: str | None = None) -> dict[str, str]:
    """Derive readiness commitments from the active packet and its artifacts."""
    root = REPOSITORY_ROOT.resolve()
    packet = _load_self(DEFAULT_PACKET, "R18R13-IAM packet", "packet_digest")
    _require(packet["packet_digest"] == PACKET_DIGEST and packet["schema"] == PACKET_SCHEMA and packet.get("packet_version") == 2, "active R18R13-IAM packet identity drift")
    capability = packet["capability_identity"]
    binding = packet["credential_binding"]
    sources = packet["source_bindings"]
    authority_dependency = packet["authority_dependency"]
    _require(capability["service_account"] == GCS_ONLY_ACCOUNT and binding["service_account"] == GCS_ONLY_ACCOUNT, "active credential account drift")
    _require(capability["service_account_resource"] == f"projects/ocelot-proof/serviceAccounts/{GCS_ONLY_ACCOUNT}", "active credential resource drift")
    _require(capability["wif_principal"].endswith(_CREDENTIAL_IMAGE_DIGEST), "active credential image binding drift")
    _require(sources["gcs_capability_definition_digest"] == GCS_DEFINITION_DIGEST, "active capability definition drift")
    authority = _load_self(_resolve(authority_dependency["binding_path"], "authority binding", root), "authority binding", "artifact_digest")
    _require(authority["artifact_digest"] == AUTHORITY_DIGEST and authority["kms"]["authority_binding"]["binding_digest"] == AUTHORITY_BINDING_DIGEST, "active authority binding drift")
    return {
        "packet_digest": PACKET_DIGEST,
        "evidence_digest": evidence_digest or CREDENTIAL_DIGEST,
        "provider": _CREDENTIAL_PROVIDER,
        "image_digest": _CREDENTIAL_IMAGE_DIGEST,
        "audience": _CREDENTIAL_AUDIENCE,
        "principal": capability["wif_principal"],
        "target_resource": capability["service_account_resource"],
        "authority_binding_digest": AUTHORITY_BINDING_DIGEST,
        "service_account": GCS_ONLY_ACCOUNT,
        "capability_binding_digest": GCS_DEFINITION_DIGEST,
    }


def _credential_state(packet: Mapping[str, Any]) -> str:
    status = packet["credential_binding"].get("status")
    _require(status in {_UNRESOLVED_PACKET_STATUS, _VERIFIED_PACKET_STATUS}, "credential readiness state is not versioned")
    return CREDENTIAL_VERIFIED if status == _VERIFIED_PACKET_STATUS else CREDENTIAL_UNRESOLVED


def _validate_verified_credential(
    evidence: VerifiedCredentialReadinessEvidence,
    *,
    now: int,
) -> None:
    _require(type(evidence) is VerifiedCredentialReadinessEvidence, "verified credential readiness requires verifier-owned evidence")
    from services.p5_r0_evaluator.credential_evidence import _is_registered_credential_evidence
    _require(_is_registered_credential_evidence(evidence), "verified credential readiness requires verifier-issued evidence")
    _require(evidence.seal_digest == _commitment({field: getattr(evidence, field) for field in evidence.__dataclass_fields__}), "verified credential evidence seal digest drift")
    expected = _active_credential_contract(evidence_digest=evidence.signed_environment_evidence_digest)
    expected_values = {
        "packet_digest": evidence.packet_digest,
        "evidence_digest": evidence.signed_environment_evidence_digest,
        "provider": evidence.provider,
        "image_digest": evidence.image_digest,
        "audience": evidence.audience,
        "principal": evidence.principal,
        "target_resource": evidence.target_resource,
        "authority_binding_digest": evidence.authority_binding_digest,
        "service_account": evidence.service_account,
        "capability_binding_digest": evidence.capability_binding_digest,
    }
    for name, value in expected_values.items():
        _require(expected.get(name) == value, f"verified credential {name} binding drift")
    for name in ("packet_digest", "evidence_digest", "image_digest", "authority_binding_digest", "capability_binding_digest"):
        _is_digest(expected_values[name], name)
    _require(evidence.attestation_binding_digest and evidence.source_token_digest and evidence.capability_token_digest, "verified credential verifier commitments are missing")
    _is_digest(evidence.attestation_binding_digest, "attestation binding digest")
    _is_digest(evidence.source_token_digest, "source token digest")
    _is_digest(evidence.capability_token_digest, "capability token digest")
    _require(type(evidence.attestation_expires_at) is int and type(evidence.source_expires_at) is int and type(evidence.expires_at) is int, "verified credential expiry is unresolved")
    _require(evidence.expires_at > now + 30 and evidence.expires_at <= evidence.source_expires_at <= now + 3600, "verified credential is expired or not source-bounded")
    _require(evidence.expires_at <= evidence.attestation_expires_at, "verified credential exceeds attestation lifetime")


def transition_credential_readiness(
    previous: str,
    candidate: str,
    *,
    credential_evidence: VerifiedCredentialReadinessEvidence | None,
    now: int | None = None,
) -> str:
    """Apply readiness only from verifier-owned sealed evidence.

    The promotion branch intentionally has no provenance boolean and no
    mapping input.  A plain dict, public serialization, or forged lookalike
    cannot satisfy the exact sealed-type check.
    """
    _require(previous in {CREDENTIAL_UNRESOLVED, CREDENTIAL_VERIFIED}, "credential readiness predecessor is invalid")
    _require(candidate in {CREDENTIAL_UNRESOLVED, CREDENTIAL_VERIFIED}, "credential readiness candidate is invalid")
    _require(candidate == CREDENTIAL_VERIFIED or previous != CREDENTIAL_VERIFIED, "credential readiness cannot regress")
    if candidate == CREDENTIAL_UNRESOLVED:
        _require(credential_evidence is None, "unresolved credential state contains verifier evidence")
        return CREDENTIAL_UNRESOLVED
    _require(credential_evidence is not None, "verified credential readiness requires verifier-owned evidence")
    _validate_verified_credential(credential_evidence, now=int(time.time()) if now is None else now)
    return CREDENTIAL_VERIFIED


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise IAMBoundaryError(f"{label} is unavailable or invalid JSON") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _load_self(path: Path, label: str, field: str) -> dict[str, Any]:
    value = _load_json(path, label)
    _is_digest(value.get(field), f"{label}.{field}")
    _require(value[field] == _digest_without(value, field), f"{label} digest mismatch")
    return value


def _resolve(path: str, label: str, root: Path) -> Path:
    _require(isinstance(path, str) and path and not Path(path).is_absolute(), f"{label} path is not repository-relative")
    resolved = (root / path).resolve()
    _require(root in resolved.parents and resolved.is_file(), f"{label} is missing")
    return resolved


def _validate_r18r12(ledger_path: Path, approval_path: Path) -> None:
    lines = ledger_path.read_bytes().splitlines()
    _require(len(lines) == 4, "R18R12 ledger event count drift")
    previous: str | None = None
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = parse_canonical(line)
        except Exception as exc:
            raise IAMBoundaryError("R18R12 ledger is not canonical") from exc
        _require(record.get("previous_event_digest") == previous, "R18R12 ledger chain drift")
        _require(record.get("event_digest") == _digest_without(record, "event_digest"), "R18R12 event digest drift")
        records.append(record)
        previous = record["event_digest"]
    _require(records[2]["event_digest"] == R18R12_VERIFIED_EVENT_DIGEST and records[3]["event_digest"] == R18R12_LEDGER_HEAD_DIGEST, "R18R12 ledger head drift")
    _require(records[3].get("status") == "verified_repository_binding_review_only" and records[3].get("mutations_performed") is False and records[3].get("later_operations_enabled") is False, "R18R12 terminal boundary drift")
    approval = _load_self(approval_path, "R18R12 approval", "artifact_digest")
    _require(approval["artifact_digest"] == R18R12_APPROVAL_DIGEST and approval.get("enabled") is True and approval.get("operation_id") == "bind_self_custodied_authority_and_kms", "R18R12 approval drift")


def validate_iam_boundary(*, packet_path: Path = DEFAULT_PACKET, approval_path: Path = DEFAULT_APPROVAL, repository_root: Path = REPOSITORY_ROOT, credential_evidence: VerifiedCredentialReadinessEvidence | None = None) -> dict[str, Any]:
    """Validate the new packet and return explicit unresolved apply gates."""
    root = Path(repository_root).resolve()
    packet = _load_self(Path(packet_path), "R18R13-IAM packet", "packet_digest")
    approval = _load_self(Path(approval_path), "R18R13-IAM approval", "artifact_digest")
    _require(packet["packet_digest"] == PACKET_DIGEST and packet["schema"] == PACKET_SCHEMA and packet.get("packet_version") == 2 and packet.get("status") == "blocked_pending_signed_environment_credential_and_executor", "R18R13-IAM packet identity or version drift")
    _require(approval["artifact_digest"] == APPROVAL_DIGEST and approval["schema"] == APPROVAL_SCHEMA and approval.get("dispatch_id") == "DISPATCH-052" and approval.get("operation_id") == OPERATION_ID and approval.get("scope") == [OPERATION_ID], "R18R13-IAM approval identity or version drift")
    _require(packet["capability_identity"]["service_account"] == GCS_ONLY_ACCOUNT and packet["capability_identity"]["custom_role"] == CUSTOM_ROLE, "GCS-only capability identity drift")
    _require(packet["credential_binding"]["service_account"] == GCS_ONLY_ACCOUNT, "credential target account drift")
    _require(packet["supersession"]["prior_packet_digest"] == OLD_PACKET_DIGEST and packet["supersession"]["historical_packet_rewritten"] is False, "historical packet supersession drift")
    historical = _load_self(_resolve(packet["supersession"]["prior_packet_path"], "historical superseded packet", root), "historical superseded packet", "packet_digest")
    _require(historical["packet_digest"] == OLD_PACKET_DIGEST and historical.get("schema") == "P5R0RS069R18R13GCSBoundaryPacketV1", "historical superseded packet identity drift")

    sources = packet["source_bindings"]
    _require(sources["iam_definition_digest"] == IAM_DEFINITION_DIGEST and sources["gcs_capability_definition_digest"] == GCS_DEFINITION_DIGEST, "source definition digest drift")
    _require(sources["prestate_artifact_digest"] == PRESTATE_ARTIFACT_DIGEST and sources["prestate_state_digest"] == PRESTATE_STATE_DIGEST and sources["credential_evidence_digest"] == CREDENTIAL_DIGEST, "current evidence digest drift")
    iam_definition = _load_self(_resolve(sources["iam_definition_path"], "IAM definition", root), "IAM definition", "definition_digest")
    gcs_definition = _load_self(_resolve(sources["gcs_capability_definition_path"], "GCS definition", root), "GCS definition", "definition_digest")
    _require(iam_definition["definition_digest"] == IAM_DEFINITION_DIGEST and gcs_definition["definition_digest"] == GCS_DEFINITION_DIGEST, "source definition content drift")

    prestate_artifact = _load_self(_resolve(sources["prestate_path"], "IAM prestate", root), "IAM prestate", "artifact_digest")
    _require(prestate_artifact["artifact_digest"] == PRESTATE_ARTIFACT_DIGEST and prestate_artifact["state"]["state_digest"] == PRESTATE_STATE_DIGEST, "prestate digest drift")
    state = prestate_artifact["state"]
    _require(state["state_digest"] == _digest_without(state, "state_digest"), "prestate state digest drift")
    _require(state["target_account"]["email"] == GCS_ONLY_ACCOUNT and state["target_account"]["exists"] is False and state["target_account_policy"] is None, "target account prestate drift")
    _require(state["custom_role"]["name"] == CUSTOM_ROLE and state["custom_role"]["exists"] is False, "custom-role prestate drift")
    _require("roles/cloudkms.signerVerifier" in state["existing_account"]["project_roles"], "existing KMS authority prestate missing")

    credential = _load_self(_resolve(sources["credential_evidence_path"], "credential evidence", root), "credential evidence", "artifact_digest")
    _require(credential["artifact_digest"] == CREDENTIAL_DIGEST and credential["service_account"] == GCS_ONLY_ACCOUNT and credential["credential_injected"] is False and credential["evidence"]["token_present"] is False, "credential evidence drift")
    credential_provenance_ok = (
        credential.get("packet_digest") == PACKET_DIGEST
        and credential.get("principal") == packet["capability_identity"]["wif_principal"]
        and credential.get("provider") == "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production"
        and credential.get("target_resource") == packet["capability_identity"]["service_account_resource"]
        and credential.get("authority_binding_digest") == AUTHORITY_BINDING_DIGEST
    )
    authority = _load_self(_resolve(packet["authority_dependency"]["binding_path"], "authority binding", root), "authority binding", "artifact_digest")
    _require(authority["artifact_digest"] == AUTHORITY_DIGEST and authority["kms"]["authority_binding"]["binding_digest"] == AUTHORITY_BINDING_DIGEST, "authority binding drift")
    _validate_r18r12(_resolve(packet["authority_dependency"]["r18r12_ledger_path"], "R18R12 ledger", root), _resolve(packet["authority_dependency"]["r18r12_approval_path"], "R18R12 approval", root))

    _require(approval["packet_digest"] == PACKET_DIGEST and approval["service_account"] == GCS_ONLY_ACCOUNT, "approval packet/account binding drift")
    for field in ("iam_definition_digest", "gcs_capability_definition_digest", "prestate_artifact_digest", "prestate_state_digest", "credential_binding_digest", "authority_artifact_digest", "authority_binding_digest", "r18r12_approval_digest", "r18r12_ledger_head_digest", "r18r12_verified_event_digest"):
        _is_digest(approval.get(field), f"approval.{field}")
    _require(approval["credential_binding_digest"] == CREDENTIAL_DIGEST and approval["signed_environment_evidence_digest"] is None, "approval credential binding drift")
    _require(approval.get("status") == "approved_single_operation_blocked_pending_credential_and_reviewed_executor" and approval.get("approved") is True and approval.get("master_approved") is True and approval.get("user_approved") is True and approval["enabled"] is False and approval["ready_for_executor"] is False and approval["mutations_performed"] is False and approval["cloud_operations"] == [], "approval crosses apply boundary")

    credential_state = _credential_state(packet)
    credential_ready = False
    if credential_state == CREDENTIAL_UNRESOLVED:
        _require(credential["credential_injected"] is False and credential["evidence"]["token_present"] is False, "unresolved credential state contains readiness evidence")
        transition_credential_readiness(CREDENTIAL_UNRESOLVED, CREDENTIAL_UNRESOLVED, credential_evidence=None)
    else:
        credential_ready = transition_credential_readiness(CREDENTIAL_UNRESOLVED, CREDENTIAL_VERIFIED, credential_evidence=credential_evidence) == CREDENTIAL_VERIFIED
    approval_ready = approval["enabled"] is True and approval["ready_for_executor"] is True
    ready_for_executor = credential_ready and approval_ready
    unresolved = []
    if not credential_provenance_ok:
        unresolved.append("credential evidence is not bound to the current V2 packet, provider, authority, and exact capability account")
    if not credential_ready:
        unresolved.append("signed-environment evidence digest is absent or not cryptographically verified; no short-lived credential is injected")
    if not (state["target_account"]["exists"] is False and state["custom_role"]["exists"] is False):
        unresolved.append("fresh prestate target account/custom-role preconditions drifted")
    if not approval_ready:
        unresolved.append("approval is deliberately disabled until the external credential and reviewed executor gates are supplied")
    credential_binding_digest = credential_evidence.signed_environment_evidence_digest if credential_ready else CREDENTIAL_DIGEST
    return {
        "schema": "P5R0RS069R18R13IAMBoundaryReportV1",
        "packet_digest": PACKET_DIGEST,
        "approval_digest": APPROVAL_DIGEST,
        "service_account": GCS_ONLY_ACCOUNT,
        "iam_definition_digest": IAM_DEFINITION_DIGEST,
        "gcs_capability_definition_digest": GCS_DEFINITION_DIGEST,
        "prestate_artifact_digest": PRESTATE_ARTIFACT_DIGEST,
        "prestate_state_digest": PRESTATE_STATE_DIGEST,
        "credential_binding_digest": credential_binding_digest,
        "authority_artifact_digest": AUTHORITY_DIGEST,
        "authority_binding_digest": AUTHORITY_BINDING_DIGEST,
        "r18r12_approval_digest": R18R12_APPROVAL_DIGEST,
        "r18r12_ledger_head_digest": R18R12_LEDGER_HEAD_DIGEST,
        "r18r12_verified_event_digest": R18R12_VERIFIED_EVENT_DIGEST,
        "old_packet_digest": OLD_PACKET_DIGEST,
        "historical_packet_verified": True,
        "credential_provenance_verified": credential_provenance_ok,
        "credential_readiness": credential_state,
        "credential_ready": credential_ready,
        "cloud_operations": [],
        "mutations_performed": False,
        "applied_state": False,
        "ready_for_executor": ready_for_executor,
        "later_operations_enabled": False,
        "unresolved": unresolved,
    }


def _append_event(path: Path, body: Mapping[str, Any], previous: str | None) -> dict[str, Any]:
    event = {**dict(body), "previous_event_digest": previous}
    event["event_digest"] = _digest(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(canonical_bytes(event) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return event


def _ledger_exists(path: Path) -> bool:
    return path.exists() and bool(path.read_bytes().strip())


def _receipt_is_closed(receipt: Mapping[str, Any]) -> None:
    _require(receipt.get("project_id") == "ocelot-proof" and receipt.get("bucket") == BUCKET and receipt.get("service_account") == GCS_ONLY_ACCOUNT, "IAM receipt identity drift")
    _require(receipt.get("role") == CUSTOM_ROLE and receipt.get("role_title") == "P5 R0 operation 4 bundle writer" and receipt.get("role_stage") == "GA" and receipt.get("role_permissions") == ["storage.objects.create", "storage.objects.get"] and receipt.get("bucket_visibility") == {"name": BUCKET, "project_id": "ocelot-proof", "uniform_bucket_level_access": True, "public_access_prevention": "inherited"} and receipt.get("condition_title") == "p5_r0_r18r13_op4_exact_run", "IAM receipt role or visibility drift")
    _is_digest(receipt.get("receipt_digest"), "IAM receipt digest")
    _require(receipt["receipt_digest"] == _digest_without(receipt, "receipt_digest"), "IAM receipt digest mismatch")


def execute_reviewed_iam(*, executor: ReviewedIAMExecutorAdapter, packet_path: Path = DEFAULT_PACKET, approval_path: Path = DEFAULT_APPROVAL, ledger_path: Path = DEFAULT_LEDGER, repository_root: Path = REPOSITORY_ROOT, credential_evidence: VerifiedCredentialReadinessEvidence | None = None) -> dict[str, Any]:
    """Apply exactly one enabled packet through the injected reviewed adapter.

    The checked-in DISPATCH-052 packet is disabled and therefore stops before
    this function calls the adapter.  A future version may enable the same
    packet shape only after signed-environment evidence and a fresh approval
    are reviewed.  The sequence below is intentionally explicit and mirrors
    the immutable definition order; every poststate/receipt ambiguity rolls
    back in reverse order or returns manual-review/no-retry.
    """
    root = Path(repository_root).resolve()
    report = validate_iam_boundary(packet_path=packet_path, approval_path=approval_path, repository_root=root, credential_evidence=credential_evidence)
    _require(report["ready_for_executor"], "R18R13-IAM apply is blocked; signed credential and enabled approval are required")
    if report["ready_for_executor"]:
        _require(type(credential_evidence) is VerifiedCredentialReadinessEvidence, "R18R13-IAM executor requires verifier-owned credential evidence")
        _validate_verified_credential(credential_evidence, now=int(executor._clock()))
    ledger = Path(ledger_path)
    _require(not _ledger_exists(ledger), "R18R13-IAM attempt already exists; retry is disabled")
    packet = _load_self(Path(packet_path), "R18R13-IAM packet", "packet_digest")
    sources = packet["source_bindings"]
    prestate_artifact = _load_self(_resolve(sources["prestate_path"], "IAM prestate", root), "IAM prestate", "artifact_digest")
    expected = normalize_prestate(prestate_artifact["state"])
    definition_path = _resolve(sources["iam_definition_path"], "IAM definition", root)
    definition = _load_json(definition_path, "IAM definition")
    checked_definition = validate_definition(definition_path)
    requests = _desired_requests(definition, expected)
    _validate_requests(requests, expected)
    executor.validate_credential_binding({"evidence_digest": report["credential_binding_digest"], "packet_digest": report["packet_digest"]})
    common = {"schema": "P5R0RS069R18R13IAMLedgerEventV1", "operation_id": OPERATION_ID, "packet_digest": report["packet_digest"], "approval_digest": report["approval_digest"], "definition_digest": checked_definition["definition_digest"], "prestate_digest": report["prestate_state_digest"], "later_operations_enabled": False, "cloud_operations": ["iam.service_account_create", "iam.custom_role_update", "iam.bucket_policy_update", "iam.service_account_policy_update", "iam.poststate_describe"]}
    previous: str | None = None
    started = _append_event(ledger, {**common, "kind": "run_started", "mutations_performed": False}, previous)
    previous = started["event_digest"]
    mutation_started = False
    phase = "prestate_describe"
    try:
        observed = normalize_prestate(executor.describe_prestate())
        validate_prestate(observed, expected)
        checked = _append_event(ledger, {**common, "kind": "prestate_verified", "prestate_normalized_digest": observed["state_digest"], "mutations_performed": False}, previous)
        previous = checked["event_digest"]
        mutation_started = True
        phase = "ensure_service_account"
        executor.ensure_service_account(GCS_ONLY_ACCOUNT)
        phase = "custom_role"
        executor.apply_custom_role(requests["custom_role"])
        phase = "bucket_policy"
        executor.update_bucket_policy(requests["bucket_policy"])
        phase = "target_account_policy"
        executor.update_target_account_policy(requests["target_account_policy"])
        phase = "poststate_describe"
        poststate = normalize_prestate(executor.describe_poststate())
        validate_poststate(poststate, expected)
        receipt = build_receipt(expected, poststate)
        _receipt_is_closed(receipt)
        verified = _append_event(ledger, {**common, "kind": "poststate_verified", "poststate_digest": poststate["state_digest"], "receipt": dict(receipt), "mutations_performed": True}, previous)
        stopped = _append_event(ledger, {**common, "kind": "run_stopped", "status": "verified", "verified_event_digest": verified["event_digest"], "rollback_status": "not_required_verified", "receipt": dict(receipt), "mutations_performed": True}, verified["event_digest"])
        return {"status": "verified", "operation_id": OPERATION_ID, "ledger_head_digest": stopped["event_digest"], "poststate_digest": poststate["state_digest"], "receipt": dict(receipt), "mutations_performed": True, "later_operations_enabled": False}
    except Exception as exc:
        rollback_status = "not_applicable_no_mutation"
        if mutation_started:
            try:
                current = normalize_prestate(executor.describe_poststate())
                executor.restore_target_account_policy({"schema": "P5R0DISPATCH050ServiceAccountPolicyRestoreV1", "service_account": GCS_ONLY_ACCOUNT, "expected_version": _version_value(current["target_account_policy"]), "expected_absent": current["target_account_policy"] is None, "restore_state": expected["target_account_policy"]})
                executor.restore_bucket_policy({"schema": "P5R0DISPATCH050BucketPolicyRestoreV1", "bucket": BUCKET, "expected_version": _version_value(current["bucket_policy"]), "expected_absent": False, "restore_state": expected["bucket_policy"]})
                executor.restore_custom_role({"schema": "P5R0DISPATCH050CustomRoleRestoreV1", "resource": CUSTOM_ROLE, "expected_version": _version_value(current["custom_role"] if current["custom_role"]["exists"] else None), "expected_absent": not current["custom_role"]["exists"], "restore_state": expected["custom_role"]})
                restored = normalize_prestate(executor.describe_poststate())
                _require(restored == expected, "IAM rollback prestate mismatch")
                rollback_status = "rolled_back_verified"
            except Exception:
                rollback_status = "rollback_failed_manual_review"
        stopped = _append_event(ledger, {**common, "kind": "run_stopped", "status": "failed_closed", "failed_phase": phase, "failed_error_type": type(exc).__name__, "rollback_status": rollback_status, "mutations_performed": mutation_started}, previous)
        return {"status": "failed_closed", "operation_id": OPERATION_ID, "ledger_head_digest": stopped["event_digest"], "mutations_performed": mutation_started, "rollback_status": rollback_status, "later_operations_enabled": False}


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Validate the repository-only DISPATCH-052 R18R13-IAM boundary")
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    args = parser.parse_args()
    print(json.dumps(validate_iam_boundary(packet_path=args.packet, approval_path=args.approval), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = ["APPROVAL_DIGEST", "CREDENTIAL_UNRESOLVED", "CREDENTIAL_VERIFIED", "DEFAULT_APPROVAL", "DEFAULT_PACKET", "IAMBoundaryError", "PACKET_DIGEST", "execute_reviewed_iam", "transition_credential_readiness", "validate_iam_boundary"]
