"""Fail-closed validator for the RS-069R17 operation-2 approval packet.

This module validates repository-local review material only.  It does not
apply WIP/IAM state, call cloud tooling, or authorize a mutation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import sha256

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REQUEST = Path(__file__).with_name("rs-069r17-operation-2-approval-request.json")
PLAN_PATH = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json"
REMEDIATION_PATH = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs-068-wip-policy-remediation.json"
TEMPLATE_PATH = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/wip-provider-policy.cel.tmpl"
CANDIDATE_PATH = REPOSITORY_ROOT / "var/p5-r0-rs069r1/candidate-image-binding.json"
PRIOR_APPROVAL_PATH = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs-069r6-operation-1-approval-request.json"

OPERATION_ID = "correct_wip_provider_claim_mapping"
LATER_OPERATION_IDS = (
    "bind_self_custodied_authority_and_kms",
    "ingest_generated_bundle_to_gcs",
    "configure_cloud_run_and_confidential_space",
    "prepare_supervisor_and_run_request",
    "cleanup_or_rollback",
)
DIGEST_FIELDS = (
    "wip_policy_template_digest",
    "candidate_image_digest",
    "provider_resource_digest",
    "sts_audience_digest",
    "zone_digest",
    "claim_paths_digest",
)


class RS069R17ApprovalError(ValueError):
    """The operation-2 packet is malformed, widened, or approval-enabled."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RS069R17ApprovalError(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RS069R17ApprovalError(f"cannot load {path}") from exc
    _require(isinstance(value, dict), f"{path} must contain an object")
    return value


def _file_digest(path: Path) -> str:
    return "sha256:" + __import__("hashlib").sha256(path.read_bytes()).hexdigest()


def _plan_scope_digest(plan: Mapping[str, Any]) -> str:
    return sha256({key: value for key, value in plan.items() if key != "approval_gate_records"})


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71 and all(c in "0123456789abcdef" for c in value[7:])


def load_request(path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    return _load(Path(path))


def validate_request(request: Mapping[str, Any], *, repository_root: Path = REPOSITORY_ROOT) -> str:
    """Validate the exact blocked review packet and return its scope digest."""
    root = Path(repository_root).resolve()
    expected_fields = {
        "schema", "classification", "status", "master_run", "runsheet_item", "request_id",
        "request_scope_digest", "scope", "typed_plan_binding", "prior_approval_context",
        "operation_1_context", "target", "required_inputs", "desired_state", "preconditions",
        "rollback_rules", "stop_rules", "approval", "later_operations", "workflow",
        "forbidden_operations", "proposed_state",
    }
    _require(set(request) == expected_fields, "request top-level fields are not closed")
    _require(request["schema"] == "P5R0RS069R17Operation2ApprovalRequestV1", "request schema drift")
    _require(request["classification"] == "repository_definition_only_review_request", "request classification drift")
    _require(request["status"] == "blocked_pending_explicit_operation_2_approval", "request is not blocked")
    _require(request["master_run"] == "P5-MASTER-001" and request["runsheet_item"] == "RS-069R17", "request identity drift")
    _require(request["request_id"] == "RS-069R17-OP2-REVIEW-ONLY", "request id drift")

    plan = _load(root / "services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json")
    typed = request["typed_plan_binding"]
    _require(set(typed) == {"plan_path", "plan_digest", "plan_scope_digest", "operation_id", "operation_order", "dependency_ids", "input_digest_map", "approval_gate"}, "typed plan binding is not closed")
    _require(typed["plan_path"] == "services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json", "typed plan path drift")
    _require(typed["plan_digest"] == sha256(plan), "current typed plan digest mismatch")
    _require(typed["plan_scope_digest"] == _plan_scope_digest(plan), "typed plan scope digest mismatch")
    _require(typed["operation_id"] == OPERATION_ID and typed["operation_order"] == 2 and typed["dependency_ids"] == ["bind_candidate_image_digest"], "operation identity/order drift")
    op2 = next(op for op in plan["operations"] if op["id"] == OPERATION_ID)
    typed_record = next(record for record in plan["operation_records"] if record["operation_id"] == OPERATION_ID)
    gate_record = next(record for record in plan["approval_gate_records"] if record["operation_id"] == OPERATION_ID)
    expected_input_map = {item["name"]: item["value"] for item in op2["immutable_digests"]}
    _require(typed["input_digest_map"] == expected_input_map == typed_record["input_digest_map"] == gate_record["input_digest_map"], "typed operation-2 input map drift")
    _require(typed["approval_gate"] == {"master_approved": False, "user_approved": False, "approved": False, "enabled": False, "approval_record_ref": None, "approval_record_digest": None}, "typed approval boundary drift")

    scope = request["scope"]
    _require(scope == [OPERATION_ID], "operation scope widened")
    _require(request["target"] == {
        "project_id": "ocelot-proof", "region": "us-east1", "repository": "p5-cs",
        "repository_observation": "read_only_existing_repository",
        "provider_resource": None,
    }, "corrected p5-cs target or provider binding drift")

    candidate = _load(root / "var/p5-r0-rs069r1/candidate-image-binding.json")
    _require(request["operation_1_context"] == {
        "binding_path": "var/p5-r0-rs069r1/candidate-image-binding.json",
        "candidate_image_digest": candidate["candidate"]["image_digest"],
        "remote_digest_verified": True,
        "remote_provenance_verified": None,
        "immutable_verified": None,
        "target_reference": candidate["candidate"]["target_artifact_registry"]["reference"],
        "target_repository": "p5-cs",
        "later_operations_skipped": True,
    }, "operation-1 context drift")

    remediation = _load(root / "services/p5_r0_evaluator/deploy/rs-068-wip-policy-remediation.json")
    desired = request["desired_state"]
    _require(set(desired) == {"remediation_path", "remediation_digest", "template_path", "template_digest", "mapping", "condition", "mapping_digest", "condition_digest", "mapping_condition_digest"}, "desired state fields are not closed")
    _require(desired["remediation_path"] == "services/p5_r0_evaluator/deploy/rs-068-wip-policy-remediation.json", "remediation path drift")
    _require(desired["remediation_digest"] == sha256(remediation), "WIP remediation digest drift")
    _require(desired["template_path"] == "services/p5_r0_evaluator/deploy/wip-provider-policy.cel.tmpl", "WIP template path drift")
    _require(desired["template_digest"] == _file_digest(root / desired["template_path"]), "WIP template digest drift")
    _require(desired["mapping"] == remediation["mapping"] and desired["condition"] == remediation["condition"], "desired mapping or condition drift")
    _require(desired["mapping_digest"] == sha256(remediation["mapping"]), "mapping digest drift")
    _require(desired["condition_digest"] == sha256(remediation["condition"]), "condition digest drift")
    _require(desired["mapping_condition_digest"] == sha256({"mapping": remediation["mapping"], "condition": remediation["condition"]}), "mapping/condition digest drift")

    required = request["required_inputs"]
    _require(set(required) == set(DIGEST_FIELDS) | {"wip_provider_resource", "wip_token_audience", "claim_paths", "attested_project_zone_and_image"}, "required input set widened or narrowed")
    _require(required["wip_provider_resource"] == {"value": None, "source": "REQUIRED_INPUT:canonical reviewed WIP provider resource", "format": "//iam.googleapis.com/projects/{number}/locations/global/workloadIdentityPools/{pool}/providers/{provider}", "secret": False}, "provider input must remain unresolved")
    _require(required["wip_token_audience"] == {"value": "https://sts.googleapis.com", "source": "services/p5_r0_evaluator/deploy/rs-068-authority-binding-request.json", "format": "HTTPS audience", "secret": False}, "audience drift")
    _require(required["claim_paths"]["value"] == op2["exact_required_inputs"][2]["value"] and required["claim_paths"]["secret"] is False, "claim-path map drift")
    _require(required["attested_project_zone_and_image"]["value"] is None and required["attested_project_zone_and_image"]["secret"] is False, "attested claim input must remain unresolved")
    _require(required["candidate_image_digest"]["value"] == candidate["candidate"]["image_digest"], "candidate digest drift")
    _require(required["wip_policy_template_digest"]["value"] == desired["template_digest"], "template input digest drift")
    _require(required["claim_paths_digest"]["value"] == "sha256:c74680dc29fd2d16b74c4e8e9e918b98bc9ad3fe0aba2f7cacd730ea2f31f092", "claim-path digest drift")
    _require(required["sts_audience_digest"]["value"] == "sha256:bea837e48bc096387db88f6ec11441669756e8877fdac28f86fb86d2ef3be89c", "audience digest drift")
    for name in DIGEST_FIELDS:
        if name in {"provider_resource_digest", "zone_digest"}:
            _require(required[name]["value"] is None, f"unresolved boundary changed: {name}")
        else:
            _require(_is_digest(required[name]["value"]), f"resolved digest missing: {name}")

    for field in ("preconditions", "rollback_rules", "stop_rules", "forbidden_operations"):
        _require(isinstance(request[field], list) and request[field] and all(isinstance(value, str) and value for value in request[field]), f"{field} is incomplete")
    _require(request["approval"] == {"approval_id": None, "master_approved": False, "user_approved": False, "approved": False, "enabled": False, "required_text": "Master/security explicitly approves this exact RS-069R17 operation-2 packet; prior operation-1 approval is not reusable."}, "explicit approval boundary drift")
    _require(len(request["later_operations"]) == len(LATER_OPERATION_IDS), "later operation count drift")
    _require(tuple(item["id"] for item in request["later_operations"]) == LATER_OPERATION_IDS and all(item["enabled"] is False for item in request["later_operations"]), "later operation enabled or reordered")
    _require(request["workflow"] == {"apply_interface": "approved IaC workflow only", "commands": [], "direct_cloud_mutations": False, "mutations_performed": False, "wip_mutation_performed": False, "iam_mutation_performed": False, "later_operations_enabled": False}, "workflow crosses mutation boundary")
    _require(request["proposed_state"] == {"operation_2": "blocked_pending_explicit_approval", "wip_provider_state": "unchanged", "iam_state": "unchanged", "later_operations": "disabled", "master_decision": "pending"}, "proposed state drift")

    scope_without_digest = {key: value for key, value in request.items() if key != "request_scope_digest"}
    _require(request["request_scope_digest"] == sha256(scope_without_digest), "request scope digest mismatch")
    return request["request_scope_digest"]


__all__ = ["DEFAULT_REQUEST", "RS069R17ApprovalError", "load_request", "validate_request"]
