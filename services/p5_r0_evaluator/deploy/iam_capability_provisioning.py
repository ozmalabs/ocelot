"""Fail-closed DISPATCH-050 IAM provisioning and verification boundary.

This module is intentionally an injected-IaC boundary.  It reads a reviewed
local definition, requires a fresh versioned prestate and exact child approval,
and delegates every mutation to an explicitly supplied executor.  It never
imports a cloud SDK, obtains credentials, invokes gcloud, or edits the master
runsheet.  Tests use a fake executor to exercise apply order, poststate
verification, rollback, and no-retry behavior without cloud access.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from evaluation.p0a.canonical import canonical_bytes, sha256

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEFINITION = Path(__file__).with_name("rs069r18r13-iam-provisioning-definition-v1.json")
DEFAULT_APPROVAL = REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-iam-approval.json"
DEFAULT_PRESTATE = REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-iam-expected-prestate.json"
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-0-dispatch-050-iam-ledger.jsonl"
SCHEMA = "P5R0DISPATCH050GCSIAMProvisioningDefinitionV1"
PRESTATE_SCHEMA = "P5R0DISPATCH050IAMPrestateV1"
OPERATION_ID = "provision_gcs_only_iam_boundary"
PROJECT_ID = "ocelot-proof"
PROJECT_NUMBER = "141633828616"
BUCKET = "p5-evaluator-ocelot-proof-141633828616"
RUN_PREFIX = "p5-r0/operation-4/rs069r18r13-op4-04a98e3e/"
EXISTING_ACCOUNT = "p5-evaluator@ocelot-proof.iam.gserviceaccount.com"
GCS_ONLY_ACCOUNT = "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com"
WIF_PRINCIPAL = "principalSet://iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/attribute.image_digest/sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c"
CUSTOM_ROLE = "projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1"
CUSTOM_ROLE_TITLE = "P5 R0 operation 4 bundle writer"
CUSTOM_ROLE_STAGE = "GA"
CUSTOM_ROLE_PERMISSIONS = ("storage.objects.create", "storage.objects.get")
TOKEN_CREATOR = "roles/iam.serviceAccountTokenCreator"
WIF_PROVIDER = "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production"
WIF_IMAGE_DIGEST = "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c"
STS_AUDIENCE = "https://sts.googleapis.com"
AUTHORITY_BINDING_DIGEST = "sha256:9837a8f8e5f214a474f685e259f0acb1d6b6fff4b02d9ebbc3919fbf1e7c13e6"
BROAD_ROLE = "roles/storage.objectAdmin"
STALE_WIF_ROLE = "roles/storage.objectUser"
STALE_WIF_PRINCIPAL = "principalSet://iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/attribute.image_digest/sha256:0a42a061ac593c7dd4e21e90fab7b8bb62d1836666e5507549fb4194b18dcca7"
EXACT_CONDITION_TITLE = "p5_r0_r18r13_op4_exact_run"
EXACT_CONDITION = "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/p5-r0/operation-4/rs069r18r13-op4-04a98e3e/')"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ATTEMPT_RE = re.compile(r"^dispatch050-iam-[a-z0-9][a-z0-9-]{7,63}$")


class IAMProvisioningError(ValueError):
    """A definition, approval, prestate, poststate, or rollback is unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IAMProvisioningError(message)


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return sha256({key: item for key, item in value.items() if key != field})


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise IAMProvisioningError(f"invalid JSON: {path}") from exc
    _require(isinstance(value, dict), "JSON root must be an object")
    return value


def _load_canonical_artifact(path: Path, label: str) -> dict[str, Any]:
    value = _load_json(path)
    _require(isinstance(value.get("artifact_digest"), str), f"{label} digest is missing")
    _require(value["artifact_digest"] == _digest_without(value, "artifact_digest"), f"{label} digest mismatch")
    return value


def _digest(value: Any) -> str:
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _is_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None, f"{label} is not a digest")


def _version(value: Mapping[str, Any], label: str) -> tuple[str, str]:
    fields = [field for field in ("etag", "fingerprint") if field in value]
    _require(len(fields) == 1, f"{label} must contain exactly one etag or fingerprint")
    result = value[fields[0]]
    _require(isinstance(result, str) and bool(result), f"{label} version is unresolved")
    return fields[0], result


def _condition(value: Any, label: str) -> dict[str, str] | None:
    if value is None:
        return None
    _require(isinstance(value, Mapping), f"{label} condition is malformed")
    _require(set(value) in ({"title", "expression"}, {"expression"}), f"{label} condition is not closed")
    _require(all(isinstance(item, str) and item for item in value.values()), f"{label} condition is unresolved")
    return {key: value[key] for key in ("title", "expression") if key in value}


def _binding(value: Any, label: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} binding is malformed")
    _require(set(value) == {"member", "role", "condition"}, f"{label} binding is not closed")
    _require(isinstance(value["member"], str) and value["member"], f"{label} member is unresolved")
    _require(isinstance(value["role"], str) and value["role"], f"{label} role is unresolved")
    return {"member": value["member"], "role": value["role"], "condition": _condition(value["condition"], label)}


def _bindings(value: Any, label: str) -> list[dict[str, Any]]:
    _require(isinstance(value, list), f"{label} bindings are malformed")
    return sorted((_binding(item, f"{label}[{index}]") for index, item in enumerate(value)), key=lambda item: (item["member"], item["role"], json.dumps(item["condition"], sort_keys=True)))


def _versioned_policy(value: Any, label: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} is malformed")
    _require(set(value) in ({"etag", "bindings"}, {"fingerprint", "bindings"}), f"{label} must contain exactly one etag or fingerprint")
    field, version = _version(value, label)
    return {field: version, "bindings": _bindings(value["bindings"], label)}


def _role(value: Any, label: str, *, allow_absent: bool) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} is malformed")
    _require(set(value) == {"name", "exists", "etag", "fingerprint", "title", "stage", "permissions"}, f"{label} is not closed")
    _require(value["name"] == CUSTOM_ROLE and isinstance(value["exists"], bool), f"{label} identity drift")
    if not value["exists"]:
        _require(allow_absent and value["etag"] is None and value["fingerprint"] is None and value["permissions"] == [], f"{label} absent state is invalid")
        _require(value["title"] is None and value["stage"] is None, f"{label} absent metadata is invalid")
        return dict(value)
    _require((value["etag"] is None) != (value["fingerprint"] is None), f"{label} must carry exactly one version")
    _require(isinstance(value["title"], str) and isinstance(value["stage"], str), f"{label} metadata is unresolved")
    _require(value["title"] == CUSTOM_ROLE_TITLE and value["stage"] == CUSTOM_ROLE_STAGE, f"{label} metadata drift")
    _require(value["permissions"] == list(CUSTOM_ROLE_PERMISSIONS), f"{label} permissions drift")
    return dict(value)


def _account(value: Any, label: str, email: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} is malformed")
    _require(set(value) == {"email", "exists", "has_key_material", "project_roles"}, f"{label} is not closed")
    _require(value["email"] == email and isinstance(value["exists"], bool), f"{label} identity drift")
    _require(isinstance(value["has_key_material"], bool) and isinstance(value["project_roles"], list), f"{label} material state is malformed")
    return {"email": email, "exists": value["exists"], "has_key_material": value["has_key_material"], "project_roles": sorted(value["project_roles"])}


def _bucket(value: Any, label: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} is malformed")
    _require(set(value) == {"name", "project_id", "uniform_bucket_level_access", "public_access_prevention"}, f"{label} is not closed")
    _require(value["name"] == BUCKET and value["project_id"] == PROJECT_ID, f"{label} identity drift")
    _require(type(value["uniform_bucket_level_access"]) is bool, f"{label} uniform access is unresolved")
    _require(value["public_access_prevention"] in {"inherited", "enforced", "unspecified"}, f"{label} public access prevention is unresolved")
    return {
        "name": BUCKET,
        "project_id": PROJECT_ID,
        "uniform_bucket_level_access": value["uniform_bucket_level_access"],
        "public_access_prevention": value["public_access_prevention"],
    }


def _validate_state(state: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(state, Mapping), "IAM state is not an object")
    expected = {"schema", "project", "bucket", "bucket_policy", "existing_account", "existing_account_policy", "target_account", "target_account_policy", "custom_role", "state_digest"}
    _require(set(state) == expected, "IAM state fields are not closed")
    _require(state["schema"] == PRESTATE_SCHEMA, "IAM state schema drift")
    _require(state["project"] == {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER}, "IAM project drift")
    bucket = _bucket(state["bucket"], "bucket")
    bucket_policy = _versioned_policy(state["bucket_policy"], "bucket policy")
    existing_account = _account(state["existing_account"], "existing account", EXISTING_ACCOUNT)
    existing_policy = _versioned_policy(state["existing_account_policy"], "existing account policy")
    target = _account(state["target_account"], "target account", GCS_ONLY_ACCOUNT)
    if target["exists"]:
        target_policy = _versioned_policy(state["target_account_policy"], "target account policy")
    else:
        _require(state["target_account_policy"] is None, "absent target account cannot have a policy")
        target_policy = None
    role = _role(state["custom_role"], "custom role", allow_absent=True)
    normalized = {
        "schema": PRESTATE_SCHEMA,
        "project": {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER},
        "bucket": bucket,
        "bucket_policy": bucket_policy,
        "existing_account": existing_account,
        "existing_account_policy": existing_policy,
        "target_account": target,
        "target_account_policy": target_policy,
        "custom_role": role,
    }
    _require(state["state_digest"] == _digest(normalized), "IAM state digest drift")
    return {**normalized, "state_digest": state["state_digest"]}


def _raw_binding(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    _require(isinstance(value.get("members"), list), f"{label} members are malformed")
    condition = value.get("condition")
    if condition is not None:
        _require(isinstance(condition, Mapping), f"{label} condition is malformed")
        condition = {key: condition[key] for key in ("title", "expression") if key in condition}
    return {"members": list(value["members"]), "role": value.get("role"), "condition": condition}


def _raw_policy(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    _require(set(value) == {"etag", "bindings"}, f"{label} must contain exactly etag and bindings")
    bindings = []
    for index, raw in enumerate(value["bindings"]):
        checked = _raw_binding(raw, f"{label}[{index}]")
        _require(isinstance(checked["role"], str) and checked["role"], f"{label}[{index}] role is unresolved")
        for member in checked["members"]:
            _require(isinstance(member, str) and member, f"{label}[{index}] member is unresolved")
            bindings.append({"member": member, "role": checked["role"], "condition": checked["condition"]})
    return {"etag": value["etag"], "bindings": bindings}


def _normalize_v2_observation(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Convert the read-only GCP-shaped V2 evidence into the closed state model."""
    _require(raw.get("schema") == "P5R0RS069R18R13IAMStateV2", "IAM V2 state schema drift")
    project, bucket = raw["project"], raw["bucket"]
    existing, target, role = raw["existing_account"], raw["target_account"], raw["custom_role"]
    _require(project.get("project_id") == PROJECT_ID and project.get("project_number") == PROJECT_NUMBER, "IAM project drift")
    _require(bucket.get("name") == BUCKET and bucket.get("project_id") == PROJECT_ID, "IAM bucket drift")
    bucket_visibility = _bucket({key: bucket.get(key) for key in ("name", "project_id", "uniform_bucket_level_access", "public_access_prevention")}, "IAM V2 bucket")
    _require(existing.get("email") == EXISTING_ACCOUNT and target.get("email") == GCS_ONLY_ACCOUNT, "IAM account identity drift")
    existing_keys, target_keys = existing.get("user_managed_key_count"), target.get("user_managed_key_count")
    normalized = {
        "project": {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER},
        "bucket": bucket_visibility,
        "bucket_policy": _raw_policy(raw["bucket_policy"], "bucket policy"),
        "existing_account": {"email": EXISTING_ACCOUNT, "exists": existing.get("exists") is True, "has_key_material": existing_keys not in (None, 0), "project_roles": list(existing.get("project_roles", []))},
        "existing_account_policy": _raw_policy(raw["existing_account_policy"], "existing account policy"),
        "target_account": {"email": GCS_ONLY_ACCOUNT, "exists": target.get("exists") is True, "has_key_material": target_keys not in (None, 0), "project_roles": list(target.get("project_roles", []))},
        "target_account_policy": raw.get("target_account_policy"),
        "custom_role": role,
    }
    if normalized["target_account"]["exists"]:
        normalized["target_account_policy"] = _raw_policy(raw["target_account_policy"], "target account policy")
    return normalized


def normalize_prestate(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one fresh read-only observation into a version-bound state."""
    if raw.get("schema") == "P5R0RS069R18R13IAMStateV2":
        raw = _normalize_v2_observation(raw)
    if "state_digest" in raw:
        _require(raw["state_digest"] is None or isinstance(raw["state_digest"], str), "raw state digest is malformed")
    value = dict(raw)
    value.pop("state_digest", None)
    normalized = {
        "schema": PRESTATE_SCHEMA,
        "project": {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER},
        "bucket": _bucket(value["bucket"], "bucket"),
        "bucket_policy": _versioned_policy(value["bucket_policy"], "bucket policy"),
        "existing_account": _account(value["existing_account"], "existing account", EXISTING_ACCOUNT),
        "existing_account_policy": _versioned_policy(value["existing_account_policy"], "existing account policy"),
        "target_account": _account(value["target_account"], "target account", GCS_ONLY_ACCOUNT),
        "target_account_policy": None,
        "custom_role": _role(value["custom_role"], "custom role", allow_absent=True),
    }
    if normalized["target_account"]["exists"]:
        normalized["target_account_policy"] = _versioned_policy(value["target_account_policy"], "target account policy")
    else:
        _require(value["target_account_policy"] is None, "absent target account cannot have a policy")
    return {**normalized, "state_digest": _digest(normalized)}


def validate_definition(path: Path = DEFAULT_DEFINITION) -> dict[str, Any]:
    """Validate the closed, blocked, non-release DISPATCH-050 definition."""
    definition = _load_json(Path(path))
    expected = {"schema", "classification", "status", "dispatch_id", "review", "operation", "target", "service_accounts", "custom_role", "wif_binding", "bucket_bindings", "prestate_contract", "apply_order", "rollback", "poststate", "execution_boundary", "definition_digest"}
    _require(set(definition) == expected, "IAM definition fields are not closed")
    _require(definition["schema"] == SCHEMA and definition["classification"] == "repository_definition_only_non_release", "IAM definition identity drift")
    _require(definition["status"] == "blocked_pending_fresh_prestate_child_approval_and_signed_environment", "IAM definition must remain blocked")
    _require(definition["dispatch_id"] == "DISPATCH-050", "dispatch identity drift")
    _is_digest(definition["definition_digest"], "definition digest")
    _require(definition["definition_digest"] == _digest_without(definition, "definition_digest"), "definition digest mismatch")
    review = definition["review"]
    _require(review["review_id"] == "P5-MASTER-001/REVIEW-050" and review["master_runsheet_modified"] is False and review["cloud_operations_performed"] == [] and review["credentials_created"] is False, "review boundary drift")
    packet = _load_json(REPOSITORY_ROOT / review["source_packet_path"])
    _require(packet.get("packet_digest") == review["source_packet_digest"] and packet.get("packet_digest") == _digest_without(packet, "packet_digest"), "source packet digest drift")
    capability = _load_json(REPOSITORY_ROOT / review["source_capability_definition_path"])
    _require(capability.get("definition_digest") == review["source_capability_definition_digest"] and capability.get("definition_digest") == _digest_without(capability, "definition_digest"), "source capability definition digest drift")
    operation = definition["operation"]
    _require(operation["id"] == OPERATION_ID and operation["scope"] == [OPERATION_ID] and operation["depends_on"] == ["bind_self_custodied_authority_and_kms", "reviewed_gcs_capability_definition"] and operation["later_operations_enabled"] is False and operation["direct_cloud_commands"] is False and operation["cloud_operations"] == [] and operation["mutations_performed"] is False, "operation boundary drift")
    target = definition["target"]
    _require(target == {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER, "bucket": BUCKET, "exact_run_prefix": RUN_PREFIX, "visibility": {"required": "private", "uniform_bucket_level_access": True, "public_access_prevention": "inherited", "public_principals_allowed": False}}, "target drift")
    accounts = definition["service_accounts"]
    _require(accounts["existing_kms_capable_account"] == EXISTING_ACCOUNT and accounts["gcs_only_required"] is True and accounts["gcs_only_account"] == GCS_ONLY_ACCOUNT, "service-account split drift")
    role = definition["custom_role"]
    _require(role["resource"] == CUSTOM_ROLE and role["title"] == CUSTOM_ROLE_TITLE and role["stage"] == CUSTOM_ROLE_STAGE and role["permissions"] == list(CUSTOM_ROLE_PERMISSIONS) and role["condition_title"] == EXACT_CONDITION_TITLE and role["condition_expression"] == EXACT_CONDITION, "custom role drift")
    wif = definition["wif_binding"]
    _require(wif["principal"] == WIF_PRINCIPAL and wif["token_creator_role"] == TOKEN_CREATOR and wif["target_resource"] == f"projects/{PROJECT_ID}/serviceAccounts/{GCS_ONLY_ACCOUNT}" and wif["direct_bucket_access"] is False, "exact WIF/token-creator binding drift")
    bindings = definition["bucket_bindings"]
    _require(bindings["grant"] == {"member": f"serviceAccount:{GCS_ONLY_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}, "bucket grant drift")
    _require(bindings["remove"] == [{"member": f"serviceAccount:{EXISTING_ACCOUNT}", "role": BROAD_ROLE, "condition": None}, {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}}] and bindings["public_principals_allowed"] is False, "bucket removal boundary drift")
    _require(definition["apply_order"] == ["capture_and_digest_fresh_read_only_prestate", "ensure_gcs_only_service_account_without_key_material", "create_or_reconcile_exact_custom_role", "atomically_update_bucket_policy_add_exact_writer_and_remove_broad_or_stale_grants", "atomically_update_gcs_only_service_account_policy_add_exact_token_creator", "reobserve_and_verify_exact_poststate_and_private_visibility"], "apply order drift")
    _require(definition["prestate_contract"] == {"schema": PRESTATE_SCHEMA, "required": ["project", "bucket", "bucket_policy", "existing_account_policy", "target_account", "custom_role"], "approval_artifact_path": "var/p5-r0-rs069/rs069r18r13-iam-approval.json", "expected_prestate_artifact_path": "var/p5-r0-rs069/rs069r18r13-iam-expected-prestate.json", "version_fields": "Each existing IAM policy/role must carry exactly one observed etag or fingerprint; missing or ambiguous versions fail closed.", "fresh_capture_required": True, "capture_read_only": True, "expected_current_observation": {"existing_account_bucket_role": BROAD_ROLE, "existing_account_project_role": "roles/cloudkms.signerVerifier", "target_account_exists": "not_observed", "custom_role_exists": "not_observed"}}, "prestate contract drift")
    _require(definition["rollback"] == {"required_on_any_post_mutation_failure": True, "order": ["restore_service_account_policy_from_prestate", "restore_bucket_policy_from_prestate", "restore_custom_role_from_prestate"], "verification": "reobserve all restored policies/role and require exact prestate digests and versions", "ambiguous_state": "manual_review_no_retry", "created_service_account": "never delete automatically; manual review is required if creation succeeds before a later step fails"}, "rollback contract drift")
    _require(definition["poststate"] == {"required": True, "bucket_policy": "exactly the reviewed grant, with both listed stale/broad grants absent and no public principals", "target_account_policy": "exactly one roles/iam.serviceAccountTokenCreator binding for the reviewed principal", "custom_role": "exactly storage.objects.create and storage.objects.get", "service_account": "gcs-only account exists and has no key material or KMS role", "receipt": "IAM digests plus project, bucket, service-account, principal, and role condition must be recorded before operation-4 child approval"}, "poststate contract drift")
    _require(definition["execution_boundary"]["apply_performed"] is False and definition["execution_boundary"]["cloud_operations"] == [] and definition["execution_boundary"]["credentials_created"] is False and definition["execution_boundary"]["master_runsheet_modified"] is False and definition["execution_boundary"]["later_operations_enabled"] is False, "execution boundary drift")
    return {"schema": SCHEMA, "definition_digest": definition["definition_digest"], "status": definition["status"], "operation_id": OPERATION_ID, "project_id": PROJECT_ID, "bucket": BUCKET, "run_prefix": RUN_PREFIX, "gcs_only_account": GCS_ONLY_ACCOUNT, "wif_principal": WIF_PRINCIPAL, "cloud_operations": [], "apply_performed": False}


def validate_approval(approval: Mapping[str, Any], definition_digest: str) -> dict[str, Any]:
    expected = {"schema", "approval_id", "custody", "operation_id", "scope", "status", "attempt_id", "definition_digest", "prestate_digest", "signed_environment_evidence_digest", "credential_binding_digest", "artifact_digest"}
    _require(set(approval) == expected, "child approval is not closed")
    _require(approval["schema"] == "P5R0DISPATCH050IAMApprovalV1" and approval["approval_id"] == "P5-MASTER-001/APPROVAL-050-IAM" and approval["custody"] == "self_custodied" and approval["operation_id"] == OPERATION_ID and approval["scope"] == [OPERATION_ID], "child approval scope drift")
    _require(approval["status"] == "approved_single_operation_pending_apply", "child approval is not ready")
    _require(isinstance(approval["attempt_id"], str) and ATTEMPT_RE.fullmatch(approval["attempt_id"]), "child approval attempt identity is invalid")
    _is_digest(approval["definition_digest"], "approval definition digest")
    _require(approval["definition_digest"] == definition_digest, "approval definition binding drift")
    _is_digest(approval["prestate_digest"], "approval prestate digest")
    _is_digest(approval["signed_environment_evidence_digest"], "signed-environment evidence digest")
    _is_digest(approval["credential_binding_digest"], "credential binding digest")
    _require(approval["artifact_digest"] == _digest_without(approval, "artifact_digest"), "approval digest mismatch")
    return dict(approval)


def _load_approval_and_prestate() -> tuple[dict[str, Any], dict[str, Any]]:
    approval = _load_canonical_artifact(DEFAULT_APPROVAL, "IAM child approval")
    prestate_artifact = _load_canonical_artifact(DEFAULT_PRESTATE, "IAM expected prestate")
    _require(set(prestate_artifact) == {"schema", "state", "artifact_digest"}, "expected prestate artifact is not closed")
    expected = _validate_state(prestate_artifact["state"])
    _require(prestate_artifact["schema"] == "P5R0DISPATCH050IAMExpectedPrestateArtifactV1", "expected prestate artifact schema drift")
    _require(approval["prestate_digest"] == expected["state_digest"], "approval/prestate artifact binding drift")
    return approval, expected


def validate_prestate(observed: Mapping[str, Any], expected: Mapping[str, Any]) -> dict[str, Any]:
    """Require fresh observed IAM state to equal the approved versioned prestate."""
    checked_observed = _validate_state(observed)
    checked_expected = _validate_state(expected)
    _require(checked_observed == checked_expected, "fresh IAM prestate drift")
    return checked_observed


def _has_binding(bindings: list[dict[str, Any]], expected: dict[str, Any]) -> bool:
    return expected in bindings


def validate_poststate(state: Mapping[str, Any], expected_prestate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Require exact reviewed grants, no public access, and GCS-only identity."""
    checked = _validate_state(state)
    expected = _validate_state(expected_prestate) if expected_prestate is not None else None
    bucket_bindings = checked["bucket_policy"]["bindings"]
    _require(checked["bucket"] == {"name": BUCKET, "project_id": PROJECT_ID, "uniform_bucket_level_access": True, "public_access_prevention": "inherited"}, "poststate bucket visibility drift")
    if expected is not None:
        _require(checked["bucket"] == expected["bucket"], "poststate bucket visibility changed from prestate")
    exact_grant = {"member": f"serviceAccount:{GCS_ONLY_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}
    _require(_has_binding(bucket_bindings, exact_grant), "poststate exact bucket grant missing")
    _require(not any(item["member"] in {"allUsers", "allAuthenticatedUsers"} for item in bucket_bindings), "poststate public principal present")
    _require(not any(item["member"] == f"serviceAccount:{EXISTING_ACCOUNT}" and item["role"] == BROAD_ROLE for item in bucket_bindings), "poststate broad objectAdmin remains")
    _require(not any(item["member"] == STALE_WIF_PRINCIPAL and item["role"] == STALE_WIF_ROLE for item in bucket_bindings), "poststate stale WIF grant remains")
    _require(not any(item["member"] == WIF_PRINCIPAL for item in bucket_bindings), "poststate WIF principal has direct bucket access")
    target = checked["target_account"]
    _require(target == {"email": GCS_ONLY_ACCOUNT, "exists": True, "has_key_material": False, "project_roles": []}, "poststate GCS-only account drift")
    target_policy = checked["target_account_policy"]
    _require(target_policy is not None and target_policy["bindings"] == [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}], "poststate token-creator binding drift")
    role = checked["custom_role"]
    _require(role["exists"] is True and role["title"] == CUSTOM_ROLE_TITLE and role["stage"] == CUSTOM_ROLE_STAGE and role["permissions"] == list(CUSTOM_ROLE_PERMISSIONS), "poststate custom role drift")
    _require(checked["existing_account"]["email"] == EXISTING_ACCOUNT and checked["existing_account"]["has_key_material"] is False and "roles/cloudkms.signerVerifier" in checked["existing_account"]["project_roles"], "poststate KMS authority drift")
    if expected is not None:
        _require(checked["existing_account"] == expected["existing_account"], "poststate existing account drift")
        _require(checked["existing_account_policy"] == expected["existing_account_policy"], "poststate existing account policy drift")
    return checked


def _version_value(value: Mapping[str, Any] | None) -> dict[str, str] | None:
    if value is None:
        return None
    if "etag" in value and "fingerprint" in value:
        present = [(field, value[field]) for field in ("etag", "fingerprint") if value[field] is not None]
        _require(len(present) == 1 and isinstance(present[0][1], str) and bool(present[0][1]), "IAM role must contain exactly one version")
        return {"field": present[0][0], "value": present[0][1]}
    field, version = _version(value, "IAM policy")
    return {"field": field, "value": version}


def _desired_requests(definition: Mapping[str, Any], prestate: Mapping[str, Any]) -> dict[str, Any]:
    exact_grant = {"member": f"serviceAccount:{GCS_ONLY_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}
    token_grant = {"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}
    removals = [
        {"member": f"serviceAccount:{EXISTING_ACCOUNT}", "role": BROAD_ROLE, "condition": None},
        {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}},
    ]
    requests = {
        "custom_role": {"schema": "P5R0DISPATCH050CustomRoleUpdateV1", "resource": CUSTOM_ROLE, "expected_version": _version_value(prestate["custom_role"] if prestate["custom_role"]["exists"] else None), "expected_absent": not prestate["custom_role"]["exists"], "title": definition["custom_role"]["title"], "stage": definition["custom_role"]["stage"], "permissions": list(CUSTOM_ROLE_PERMISSIONS)},
        "bucket_policy": {"schema": "P5R0DISPATCH050BucketPolicyUpdateV1", "bucket": BUCKET, "expected_version": _version_value(prestate["bucket_policy"]), "expected_absent": False, "add_bindings": [exact_grant], "remove_bindings": removals, "public_principals_allowed": False},
        "target_account_policy": {"schema": "P5R0DISPATCH050ServiceAccountPolicyUpdateV1", "service_account": GCS_ONLY_ACCOUNT, "expected_version": _version_value(prestate["target_account_policy"]), "expected_absent": prestate["target_account_policy"] is None, "replace_bindings": [token_grant], "public_principals_allowed": False},
    }
    for request in requests.values():
        request["request_digest"] = _digest({key: item for key, item in request.items() if key != "request_digest"})
    return requests


def _validate_requests(requests: Mapping[str, Any], prestate: Mapping[str, Any]) -> None:
    _require(set(requests) == {"custom_role", "bucket_policy", "target_account_policy"}, "IAM mutation request set is not closed")
    for request in requests.values():
        _require(request.get("request_digest") == _digest({key: item for key, item in request.items() if key != "request_digest"}), "IAM mutation request digest drift")
    role = requests["custom_role"]
    _require(set(role) == {"schema", "resource", "expected_version", "expected_absent", "title", "stage", "permissions", "request_digest"}, "custom role request is not closed")
    _require(role["schema"] == "P5R0DISPATCH050CustomRoleUpdateV1" and role["resource"] == CUSTOM_ROLE and role["title"] == CUSTOM_ROLE_TITLE and role["stage"] == CUSTOM_ROLE_STAGE and role["permissions"] == list(CUSTOM_ROLE_PERMISSIONS), "custom role request drift")
    _require(role["expected_version"] == _version_value(prestate["custom_role"] if prestate["custom_role"]["exists"] else None) and role["expected_absent"] is (not prestate["custom_role"]["exists"]), "custom role request precondition drift")
    _require(role["title"] == "P5 R0 operation 4 bundle writer" and role["stage"] == "GA", "custom role metadata drift")
    bucket = requests["bucket_policy"]
    _require(set(bucket) == {"schema", "bucket", "expected_version", "expected_absent", "add_bindings", "remove_bindings", "public_principals_allowed", "request_digest"}, "bucket policy request is not closed")
    _require(bucket["schema"] == "P5R0DISPATCH050BucketPolicyUpdateV1" and bucket["bucket"] == BUCKET and bucket["expected_version"] == _version_value(prestate["bucket_policy"]) and bucket["expected_absent"] is False, "bucket policy request precondition drift")
    _require(bucket["public_principals_allowed"] is False, "bucket public access boundary drift")
    _require(bucket["add_bindings"] == [{"member": f"serviceAccount:{GCS_ONLY_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}], "bucket grant request drift")
    _require(bucket["remove_bindings"] == [{"member": f"serviceAccount:{EXISTING_ACCOUNT}", "role": BROAD_ROLE, "condition": None}, {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}}], "bucket removal request drift")
    target = requests["target_account_policy"]
    _require(set(target) == {"schema", "service_account", "expected_version", "expected_absent", "replace_bindings", "public_principals_allowed", "request_digest"}, "target policy request is not closed")
    _require(target["schema"] == "P5R0DISPATCH050ServiceAccountPolicyUpdateV1" and target["service_account"] == GCS_ONLY_ACCOUNT and target["expected_version"] == _version_value(prestate["target_account_policy"]), "target policy request precondition drift")
    _require(target["expected_absent"] is (prestate["target_account_policy"] is None) and target["public_principals_allowed"] is False, "target policy absence boundary drift")
    _require(target["replace_bindings"] == [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}], "token creator request drift")


def build_receipt(prestate: Mapping[str, Any], poststate: Mapping[str, Any]) -> dict[str, Any]:
    checked_pre = _validate_state(prestate)
    checked_post = _validate_state(poststate)
    _require(checked_post["target_account_policy"] is not None, "receipt target policy is missing")
    receipt = {
        "schema": "P5R0DISPATCH050IAMReceiptV1",
        "project_id": PROJECT_ID,
        "bucket": BUCKET,
        "service_account": GCS_ONLY_ACCOUNT,
        "bucket_visibility": dict(checked_post["bucket"]),
        "wif_principal": WIF_PRINCIPAL,
        "role": CUSTOM_ROLE,
        "role_title": CUSTOM_ROLE_TITLE,
        "role_stage": CUSTOM_ROLE_STAGE,
        "role_permissions": list(CUSTOM_ROLE_PERMISSIONS),
        "condition_title": EXACT_CONDITION_TITLE,
        "condition_expression": EXACT_CONDITION,
        "prestate_digest": checked_pre["state_digest"],
        "poststate_digest": checked_post["state_digest"],
        "prestate_versions": {"bucket_policy": _version_value(checked_pre["bucket_policy"]), "existing_account_policy": _version_value(checked_pre["existing_account_policy"]), "target_account_policy": _version_value(checked_pre["target_account_policy"]), "custom_role": _version_value(checked_pre["custom_role"] if checked_pre["custom_role"]["exists"] else None)},
        "poststate_versions": {"bucket_policy": _version_value(checked_post["bucket_policy"]), "existing_account_policy": _version_value(checked_post["existing_account_policy"]), "target_account_policy": _version_value(checked_post["target_account_policy"]), "custom_role": _version_value(checked_post["custom_role"] if checked_post["custom_role"]["exists"] else None)},
    }
    return {**receipt, "receipt_digest": _digest(receipt)}


class IAMExecutor(Protocol):
    """The only mutation/read interface accepted by the runner."""

    def describe_prestate(self) -> Mapping[str, Any]: ...
    def ensure_service_account(self, email: str) -> None: ...
    def apply_custom_role(self, request: Mapping[str, Any]) -> None: ...
    def update_bucket_policy(self, request: Mapping[str, Any]) -> None: ...
    def update_target_account_policy(self, request: Mapping[str, Any]) -> None: ...
    def describe_poststate(self) -> Mapping[str, Any]: ...
    def restore_target_account_policy(self, request: Mapping[str, Any]) -> None: ...
    def restore_bucket_policy(self, request: Mapping[str, Any]) -> None: ...
    def restore_custom_role(self, request: Mapping[str, Any]) -> None: ...


def _append_event(path: Path, body: Mapping[str, Any], previous: str | None) -> dict[str, Any]:
    event = {**dict(body), "previous_event_digest": previous}
    event["event_digest"] = _digest(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(canonical_bytes(event) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return event


def _ledger_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    previous: str | None = None
    records = []
    for line in path.read_bytes().splitlines():
        record = json.loads(line)
        _require(record.get("previous_event_digest") == previous, "IAM ledger chain drift")
        _require(record.get("event_digest") == _digest({key: item for key, item in record.items() if key != "event_digest"}), "IAM ledger digest drift")
        records.append(record)
        previous = record["event_digest"]
    return records


def execute_provisioning(*, executor: IAMExecutor, definition_path: Path = DEFAULT_DEFINITION, ledger_path: Path = DEFAULT_LEDGER) -> dict[str, Any]:
    """Run one canonical approved IAM attempt through an injected executor."""
    definition = _load_json(Path(definition_path))
    checked_definition = validate_definition(Path(definition_path))
    approval, expected = _load_approval_and_prestate()
    approval_checked = validate_approval(approval, checked_definition["definition_digest"])
    _require(approval_checked["prestate_digest"] == expected["state_digest"], "approval prestate binding drift")
    ledger = Path(ledger_path)
    _require(not _ledger_records(ledger), "IAM attempt already exists; retry is disabled")
    requests = _desired_requests(definition, expected)
    _validate_requests(requests, expected)
    previous: str | None = None
    common = {"schema": "P5R0DISPATCH050IAMLedgeEventV1", "operation_id": OPERATION_ID, "attempt_id": approval_checked["attempt_id"], "definition_digest": checked_definition["definition_digest"], "prestate_digest": expected["state_digest"], "later_operations_enabled": False, "cloud_operations": ["iam.service_account_create", "iam.custom_role_update", "iam.bucket_policy_update", "iam.service_account_policy_update", "iam.poststate_describe"], "redacted": True}
    started = _append_event(ledger, {**common, "kind": "run_started", "mutations_performed": False}, previous)
    previous = started["event_digest"]
    mutation_started = False
    phase = "prestate_describe"
    try:
        observed = normalize_prestate(executor.describe_prestate())
        validate_prestate(observed, expected)
        prestate_event = _append_event(ledger, {**common, "kind": "prestate_verified", "prestate_state_digest": observed["state_digest"], "mutations_performed": False}, previous)
        previous = prestate_event["event_digest"]
        phase = "ensure_service_account"
        mutation_started = True
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
        verified = _append_event(ledger, {**common, "kind": "poststate_verified", "poststate_digest": poststate["state_digest"], "receipt": receipt, "mutations_performed": True}, previous)
        stopped = _append_event(ledger, {**common, "kind": "run_stopped", "status": "verified", "verified_event_digest": verified["event_digest"], "rollback_status": "not_required_verified", "receipt": receipt, "mutations_performed": True}, verified["event_digest"])
        return {"status": "verified", "operation_id": OPERATION_ID, "attempt_id": approval_checked["attempt_id"], "prestate_digest": expected["state_digest"], "poststate_digest": poststate["state_digest"], "receipt": receipt, "ledger_head_digest": stopped["event_digest"], "mutations_performed": True, "later_operations_enabled": False}
    except Exception as exc:
        rollback_status = "not_applicable_no_mutation"
        if mutation_started:
            try:
                current = normalize_prestate(executor.describe_poststate())
                executor.restore_target_account_policy({"schema": "P5R0DISPATCH050ServiceAccountPolicyRestoreV1", "service_account": GCS_ONLY_ACCOUNT, "expected_version": _version_value(current["target_account_policy"]), "expected_absent": current["target_account_policy"] is None, "restore_state": expected["target_account_policy"]})
                executor.restore_bucket_policy({"schema": "P5R0DISPATCH050BucketPolicyRestoreV1", "bucket": BUCKET, "expected_version": _version_value(current["bucket_policy"]), "expected_absent": False, "restore_state": expected["bucket_policy"]})
                executor.restore_custom_role({"schema": "P5R0DISPATCH050CustomRoleRestoreV1", "resource": CUSTOM_ROLE, "expected_version": _version_value(current["custom_role"] if current["custom_role"]["exists"] else None), "expected_absent": not expected["custom_role"]["exists"], "restore_state": expected["custom_role"]})
                restored = normalize_prestate(executor.describe_poststate())
                _require(restored == expected, "IAM rollback prestate mismatch")
                rollback_status = "rolled_back_verified"
            except Exception:
                rollback_status = "rollback_failed_manual_review"
        stopped = _append_event(ledger, {**common, "kind": "run_stopped", "status": "failed_closed", "failed_phase": phase, "error_type": type(exc).__name__, "rollback_status": rollback_status, "mutations_performed": mutation_started}, previous)
        return {"status": "failed_closed", "operation_id": OPERATION_ID, "attempt_id": approval_checked["attempt_id"], "ledger_head_digest": stopped["event_digest"], "mutations_performed": mutation_started, "rollback_status": rollback_status, "later_operations_enabled": False}


__all__ = ["DEFAULT_APPROVAL", "DEFAULT_DEFINITION", "DEFAULT_LEDGER", "DEFAULT_PRESTATE", "GCS_ONLY_ACCOUNT", "IAMExecutor", "IAMProvisioningError", "OPERATION_ID", "build_receipt", "execute_provisioning", "normalize_prestate", "validate_approval", "validate_definition", "validate_poststate", "validate_prestate"]



@dataclass(frozen=True)
class InjectedSignedEnvironmentCredential:
    """Opaque readiness metadata for a credential injected by signed execution.

    The access token is deliberately not represented here.  The external
    signed-environment executor owns the token and supplies only this
    non-exporting handle/metadata to the reviewed backend.  This prevents the
    repository runner from discovering ADC or handling key material.
    """

    evidence_digest: str
    target_service_account: str
    expires_at: int
    packet_digest: str | None = None
    provider: str | None = None
    image_digest: str | None = None
    audience: str | None = None
    authority_binding_digest: str | None = None
    principal: str | None = None
    target_resource: str | None = None
    attestation_digest: str | None = None
    attestation_signature: str | None = None
    attestation_claims: Mapping[str, Any] | None = None
    token_present: bool = True
    exported: bool = False
    contains_key_material: bool = False
    ambient_adc: bool = False
    source: str = "signed_environment_injected"
    # Opaque verifier-owned handle; token bytes never enter this object.
    transport: Any = None


class ReviewedIAMBackend(Protocol):
    """Explicit signed-environment backend; every call receives the credential."""

    reviewed: bool
    target_service_account: str
    custom_role: str
    uses_adc: bool
    direct_gcloud: bool

    def verify_signed_environment_credential(self, credential: InjectedSignedEnvironmentCredential) -> bool: ...

    def describe_prestate(self, credential: InjectedSignedEnvironmentCredential) -> Mapping[str, Any]: ...
    def ensure_service_account(self, credential: InjectedSignedEnvironmentCredential, email: str) -> None: ...
    def apply_custom_role(self, credential: InjectedSignedEnvironmentCredential, request: Mapping[str, Any]) -> None: ...
    def update_bucket_policy(self, credential: InjectedSignedEnvironmentCredential, request: Mapping[str, Any]) -> None: ...
    def update_target_account_policy(self, credential: InjectedSignedEnvironmentCredential, request: Mapping[str, Any]) -> None: ...
    def describe_poststate(self, credential: InjectedSignedEnvironmentCredential) -> Mapping[str, Any]: ...
    def restore_target_account_policy(self, credential: InjectedSignedEnvironmentCredential, request: Mapping[str, Any]) -> None: ...
    def restore_bucket_policy(self, credential: InjectedSignedEnvironmentCredential, request: Mapping[str, Any]) -> None: ...
    def restore_custom_role(self, credential: InjectedSignedEnvironmentCredential, request: Mapping[str, Any]) -> None: ...



def _require_request_version(value: Any, *, absent: bool, label: str) -> None:
    if absent:
        _require(value is None, f"{label} absence precondition drift")
        return
    _require(isinstance(value, Mapping) and set(value) == {"field", "value"} and value["field"] in {"etag", "fingerprint"} and isinstance(value["value"], str) and bool(value["value"]), f"{label} version precondition is missing or ambiguous")


class ReviewedIAMExecutorAdapter:
    """Concrete IAMExecutor adapter for one reviewed signed-environment path.

    This adapter has no cloud SDK or subprocess dependency.  It forwards only
    the narrow IAMExecutor protocol to an explicitly reviewed backend and
    passes the injected credential on every call.  The existing
    ``execute_provisioning`` function therefore remains the sole owner of the
    exact apply order, receipt verification, reverse rollback, and no-retry
    ledger semantics.
    """

    def __init__(
        self,
        *,
        backend: ReviewedIAMBackend,
        credential: InjectedSignedEnvironmentCredential | None,
        target_service_account: str = GCS_ONLY_ACCOUNT,
        custom_role: str = CUSTOM_ROLE,
        clock: Any = __import__("time").time,
    ) -> None:
        self._backend = backend
        self._credential = credential
        self._clock = clock
        _require(target_service_account == GCS_ONLY_ACCOUNT, "IAM target service account precondition is absent or incorrect")
        _require(custom_role == CUSTOM_ROLE, "IAM custom-role precondition is absent or incorrect")
        _require(getattr(backend, "reviewed", False) is True, "reviewed IAM backend is required")
        _require(getattr(backend, "uses_adc", False) is False, "ambient ADC is forbidden")
        _require(getattr(backend, "direct_gcloud", False) is False, "direct unreviewed gcloud is forbidden")
        _require(hasattr(backend, "target_service_account") and getattr(backend, "target_service_account") == target_service_account, "backend target account precondition is absent or drifted")
        _require(hasattr(backend, "custom_role") and getattr(backend, "custom_role") == custom_role, "backend custom-role precondition is absent or drifted")
        self._validate_credential()

    @property
    def credential(self) -> InjectedSignedEnvironmentCredential | None:
        """Return the opaque, non-secret credential metadata for a verifier."""
        return self._credential

    def _validate_credential(self) -> None:
        credential = self._credential
        _require(credential is not None, "signed-environment credential is required")
        _require(credential.source == "signed_environment_injected", "credential source is not the reviewed signed environment")
        _require(credential.target_service_account == GCS_ONLY_ACCOUNT, "credential target account drift")
        _is_digest(credential.evidence_digest, "signed-environment evidence digest")
        _require(credential.token_present is True, "signed-environment credential is absent")
        _require(credential.exported is False and credential.contains_key_material is False and credential.ambient_adc is False, "credential handling crosses the no-key/no-ADC boundary")
        _require(credential.expires_at > int(self._clock()), "signed-environment credential is expired")
        if getattr(self._backend, "requires_explicit_credential_transport", False):
            transport = credential.transport
            _require(callable(getattr(transport, "is_registered", None)) and transport.is_registered(), "verifier-owned credential transport is required")
            _require(getattr(transport, "evidence_digest", None) == credential.evidence_digest and getattr(transport, "target_service_account", None) == credential.target_service_account and getattr(transport, "expires_at", None) == credential.expires_at, "credential transport binding mismatch")

    def validate_credential_binding(self, expected: Mapping[str, str]) -> None:
        """Require exact reviewed provenance and backend cryptographic verification."""
        self._validate_credential()
        credential = self._credential
        _require(credential.packet_digest == expected["packet_digest"], "credential packet provenance drift")
        _require(credential.evidence_digest == expected["evidence_digest"], "credential evidence digest is not approved")
        _require(credential.provider == WIF_PROVIDER and credential.image_digest == WIF_IMAGE_DIGEST and credential.audience == STS_AUDIENCE, "credential signed-environment provenance drift")
        _require(credential.authority_binding_digest == AUTHORITY_BINDING_DIGEST, "credential authority binding drift")
        _require(credential.principal == WIF_PRINCIPAL and credential.target_resource == f"projects/{PROJECT_ID}/serviceAccounts/{GCS_ONLY_ACCOUNT}", "credential capability binding drift")
        _is_digest(credential.attestation_digest, "attestation evidence digest")
        _require(isinstance(credential.attestation_signature, str) and bool(credential.attestation_signature) and isinstance(credential.attestation_claims, Mapping), "credential attestation proof is absent")
        _require(credential.attestation_claims.get("aud") == STS_AUDIENCE and credential.attestation_claims.get("submods.container.image_digest") == WIF_IMAGE_DIGEST, "credential attestation claims drift")
        verifier = getattr(self._backend, "verify_signed_environment_credential", None)
        _require(callable(verifier) and verifier(credential) is True, "signed-environment credential cryptographic verification failed")

    def _call(self, method: str, *args: Any) -> Any:
        self._validate_credential()
        return getattr(self._backend, method)(self._credential, *args)

    def describe_prestate(self) -> Mapping[str, Any]:
        return self._call("describe_prestate")

    def ensure_service_account(self, email: str) -> None:
        _require(email == GCS_ONLY_ACCOUNT, "attempted service-account target drift")
        self._call("ensure_service_account", email)

    def apply_custom_role(self, request: Mapping[str, Any]) -> None:
        _require(request.get("resource") == CUSTOM_ROLE, "attempted custom-role target drift")
        _require(set(request) == {"schema", "resource", "expected_version", "expected_absent", "title", "stage", "permissions", "request_digest"}, "custom-role request is incomplete")
        _require(request["schema"] == "P5R0DISPATCH050CustomRoleUpdateV1" and request["title"] == CUSTOM_ROLE_TITLE and request["stage"] == CUSTOM_ROLE_STAGE and request["permissions"] == list(CUSTOM_ROLE_PERMISSIONS), "custom-role request is not exact")
        _require_request_version(request["expected_version"], absent=request["expected_absent"], label="custom-role")
        _require(request["request_digest"] == _digest({key: item for key, item in request.items() if key != "request_digest"}), "custom-role request digest drift")
        self._call("apply_custom_role", request)

    def update_bucket_policy(self, request: Mapping[str, Any]) -> None:
        _require(request.get("bucket") == BUCKET, "attempted bucket target drift")
        _require(set(request) == {"schema", "bucket", "expected_version", "expected_absent", "add_bindings", "remove_bindings", "public_principals_allowed", "request_digest"}, "bucket policy request is incomplete")
        _require(request["schema"] == "P5R0DISPATCH050BucketPolicyUpdateV1" and request["expected_absent"] is False and request["public_principals_allowed"] is False, "bucket policy request precondition drift")
        _require_request_version(request["expected_version"], absent=False, label="bucket policy")
        _require(request["add_bindings"] == [{"member": f"serviceAccount:{GCS_ONLY_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}], "bucket grant request is not exact")
        _require(request["remove_bindings"] == [{"member": f"serviceAccount:{EXISTING_ACCOUNT}", "role": BROAD_ROLE, "condition": None}, {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}}], "bucket removal request is not exact")
        _require(request["request_digest"] == _digest({key: item for key, item in request.items() if key != "request_digest"}), "bucket request digest drift")
        self._call("update_bucket_policy", request)

    def update_target_account_policy(self, request: Mapping[str, Any]) -> None:
        _require(request.get("service_account") == GCS_ONLY_ACCOUNT, "attempted target policy account drift")
        _require(set(request) == {"schema", "service_account", "expected_version", "expected_absent", "replace_bindings", "public_principals_allowed", "request_digest"}, "target policy request is incomplete")
        _require(request["schema"] == "P5R0DISPATCH050ServiceAccountPolicyUpdateV1" and request["expected_absent"] in {True, False} and request["public_principals_allowed"] is False, "target policy request precondition drift")
        _require_request_version(request["expected_version"], absent=request["expected_absent"], label="target policy")
        _require(request["replace_bindings"] == [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}], "token-creator request is not exact")
        _require(request["request_digest"] == _digest({key: item for key, item in request.items() if key != "request_digest"}), "target policy request digest drift")
        self._call("update_target_account_policy", request)

    def describe_poststate(self) -> Mapping[str, Any]:
        return self._call("describe_poststate")

    def restore_target_account_policy(self, request: Mapping[str, Any]) -> None:
        _require(request.get("service_account") == GCS_ONLY_ACCOUNT, "attempted target rollback account drift")
        _require(set(request) == {"schema", "service_account", "expected_version", "expected_absent", "restore_state"} and request["schema"] == "P5R0DISPATCH050ServiceAccountPolicyRestoreV1", "target rollback request is incomplete")
        _require_request_version(request["expected_version"], absent=request["expected_absent"], label="target rollback")
        self._call("restore_target_account_policy", request)

    def restore_bucket_policy(self, request: Mapping[str, Any]) -> None:
        _require(request.get("bucket") == BUCKET, "attempted bucket rollback target drift")
        _require(set(request) == {"schema", "bucket", "expected_version", "expected_absent", "restore_state"} and request["schema"] == "P5R0DISPATCH050BucketPolicyRestoreV1", "bucket rollback request is incomplete")
        _require_request_version(request["expected_version"], absent=False, label="bucket rollback")
        self._call("restore_bucket_policy", request)

    def restore_custom_role(self, request: Mapping[str, Any]) -> None:
        _require(request.get("resource") == CUSTOM_ROLE, "attempted custom-role rollback target drift")
        _require(set(request) == {"schema", "resource", "expected_version", "expected_absent", "restore_state"} and request["schema"] == "P5R0DISPATCH050CustomRoleRestoreV1", "custom-role rollback request is incomplete")
        if request["expected_absent"]:
            if request["expected_version"] is not None:
                _require_request_version(request["expected_version"], absent=False, label="custom-role rollback current version")
        else:
            _require_request_version(request["expected_version"], absent=False, label="custom-role rollback")
        self._call("restore_custom_role", request)



__all__ = [
    *__all__,
    "InjectedSignedEnvironmentCredential",
    "ReviewedIAMBackend",
    "ReviewedIAMExecutorAdapter",
]
