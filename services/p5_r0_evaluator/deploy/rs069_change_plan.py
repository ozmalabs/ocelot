"""Fail-closed local validator for the RS-069 review-only IaC change plan.

The plan is declarative review material.  This module only reads repository
files and validates shape, ordering, digest bindings, approval barriers, and
claim boundaries.  It never invokes gcloud, cloud SDKs, KMS, GCS, WIP,
Confidential Space, FreeTSA, a supervisor, or a task runner.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, sha256

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PLAN = Path(__file__).with_name("rs-069-iac-change-plan.json")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED_INPUT_RE = re.compile(r"^REQUIRED_INPUT:")
_OPERATION_IDS = (
    "bind_candidate_image_digest",
    "correct_wip_provider_claim_mapping",
    "bind_self_custodied_authority_and_kms",
    "ingest_generated_bundle_to_gcs",
    "configure_cloud_run_and_confidential_space",
    "prepare_supervisor_and_run_request",
    "cleanup_or_rollback",
)
_OPERATION_FIELDS = {
    "id", "order", "depends_on", "desired_state_operation", "exact_required_inputs",
    "preconditions", "expected_postconditions", "immutable_digests", "approval_gate",
    "stop_conditions", "rollback_conditions", "rerunnable", "mutation_boundary",
}
_REQUIRED_INPUT_FIELDS = {"name", "value", "source", "format", "secret"}
_DIGEST_FIELDS = {"name", "value", "source", "classification"}
_TOP_LEVEL_FIELDS = {
    "schema", "classification", "status", "master_run", "runsheet_item", "objective",
    "canonical_digest", "authority_contract", "source_bindings", "read_only_inventory",
    "unknown_value_policy", "operations", "operation_records", "approval_gate_records",
    "gcs_object_records", "confidential_space_activation", "global_preconditions",
    "rerun_contract", "apply_plan", "local_validation", "claim_boundary",
}
_TYPED_OPERATION_FIELDS = {
    "schema", "operation_id", "dependency_ids", "input_digest_map", "preconditions",
    "postconditions", "approval_record_ref", "approval_record_digest", "idempotency_key",
    "drift_policy", "rollback_policy", "enabled", "commands", "resource_state",
}
_RESOURCE_STATE_FIELDS = {"addresses", "ownership", "desired_attributes", "observed_fingerprints", "state_backend", "change_policy"}
_APPROVAL_FIELDS = {
    "schema", "operation_id", "plan_digest", "input_digest_map", "approval_record_ref",
    "approval_record_digest", "master_approved", "user_approved", "approved", "enabled",
}
_OBJECT_FIELDS = {
    "schema", "object_id", "local_artifact_path", "object_suffix", "private", "artifact_digest",
    "file_digest", "destination", "ownership", "mode", "generation_precondition", "upload_state",
    "upload_performed",
}
_ACTIVATION_FIELDS = {"schema", "operation_id", "state", "approved", "enabled", "transition_order", "transitions", "digest_bindings", "equality_bindings", "attestation", "capabilities"}
_TRANSITION_FIELDS = {"from", "to", "enabled"}
_ACTIVATION_DIGEST_KEYS = (
    "candidate_image_digest",
    "provider_resource_digest",
    "sts_audience_digest",
    "project_digest",
    "zone_digest",
    "claim_paths_digest",
    "attestation_evidence_digest",
    "capability_grants_digest",
)
_ACTIVATION_BINDING_PATHS = {
    "candidate_image_digest": (
        "bind_candidate_image_digest.candidate_image_digest",
        "correct_wip_provider_claim_mapping.candidate_image_digest",
        "configure_cloud_run_and_confidential_space.candidate_image_digest",
    ),
    "provider_resource_digest": (
        "correct_wip_provider_claim_mapping.provider_resource_digest",
    ),
    "sts_audience_digest": (
        "correct_wip_provider_claim_mapping.sts_audience_digest",
    ),
    "project_digest": (
        "bind_candidate_image_digest.target_project_digest",
        "configure_cloud_run_and_confidential_space.project_digest",
    ),
    "zone_digest": (
        "correct_wip_provider_claim_mapping.zone_digest",
        "configure_cloud_run_and_confidential_space.zone_digest",
    ),
    "claim_paths_digest": (
        "correct_wip_provider_claim_mapping.claim_paths_digest",
    ),
    "attestation_evidence_digest": (
        "prepare_supervisor_and_run_request.attestation_evidence_digest",
    ),
    "capability_grants_digest": (
        "configure_cloud_run_and_confidential_space.capability_grants_digest",
    ),
}
_ACTIVATION_INPUT_BINDINGS = {
    "candidate_image_digest": (
        ("bind_candidate_image_digest", "candidate_image_digest", "digest"),
        ("configure_cloud_run_and_confidential_space", "candidate_image_digest", "digest"),
    ),
    "provider_resource_digest": (("correct_wip_provider_claim_mapping", "wip_provider_resource", "hash"),),
    "sts_audience_digest": (("correct_wip_provider_claim_mapping", "wip_token_audience", "hash"),),
    "project_digest": (
        ("bind_candidate_image_digest", "target_project_id", "hash"),
        ("configure_cloud_run_and_confidential_space", "project_id", "hash"),
    ),
    "zone_digest": (
        ("correct_wip_provider_claim_mapping", "attested_project_zone_and_image", "hash"),
        ("configure_cloud_run_and_confidential_space", "zone", "hash"),
    ),
    "claim_paths_digest": (("correct_wip_provider_claim_mapping", "claim_paths", "hash"),),
    "attestation_evidence_digest": (("prepare_supervisor_and_run_request", "signed_environment_approval", "hash"),),
    "capability_grants_digest": (),
}
_FORBIDDEN_MUTATION_TERMS = (
    "gcloud mutation", "kms signing", "gcs upload", "gcs delete", "cloud run deploy",
    "vm creation", "iam alteration", "wip/provider mutation", "image push",
    "credential generation", "freetsa call", "supervisor invocation", "task execution",
)


class RS069ValidationError(ValueError):
    """The RS-069 plan is malformed, incomplete, or crosses its boundary."""


@dataclass(frozen=True)
class RS069ValidationReport:
    ready: bool
    status: str
    plan_digest: str
    operation_ids: tuple[str, ...]
    unresolved_inputs: tuple[str, ...]
    cloud_operations: tuple[str, ...]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RS069ValidationError(message)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RS069ValidationError(f"{label} cannot be loaded as JSON") from exc
    _require(isinstance(value, dict), f"{label} root must be an object")
    return value


def _is_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} is not a sha256 digest")


def _is_allowed_unresolved(value: Any) -> bool:
    return value is None or (isinstance(value, str) and _REQUIRED_INPUT_RE.fullmatch(value) is not None)


def _validate_required_input(item: Mapping[str, Any], path: str) -> None:
    _require(set(item) == _REQUIRED_INPUT_FIELDS, f"{path} fields are not closed")
    _require(isinstance(item["name"], str) and item["name"], f"{path}.name is missing")
    _require(isinstance(item["source"], str) and item["source"], f"{path}.source is missing")
    _require(isinstance(item["format"], str) and item["format"], f"{path}.format is missing")
    _require(isinstance(item["secret"], bool) and item["secret"] is False, f"{path}.secret must be false")
    value = item["value"]
    if value is None or (isinstance(value, str) and _REQUIRED_INPUT_RE.fullmatch(value) is not None):
        return
    if "digest" in item["name"] or "digest" in item["format"]:
        _is_digest(value, f"{path}.value")


def _validate_operation(operation: Mapping[str, Any], expected_order: int, seen: set[str]) -> None:
    operation_id = operation.get("id")
    _require(set(operation) == _OPERATION_FIELDS, f"operation {operation_id!r} fields are not closed")
    _require(operation_id in _OPERATION_IDS, f"unknown operation id: {operation_id}")
    _require(operation_id not in seen, f"duplicate operation id: {operation_id}")
    seen.add(operation_id)
    _require(operation.get("order") == expected_order, f"operation order drift: {operation_id}")
    _require(isinstance(operation.get("depends_on"), list), f"dependencies missing: {operation_id}")
    for dependency in operation["depends_on"]:
        _require(dependency in _OPERATION_IDS and dependency != operation_id, f"invalid dependency in {operation_id}: {dependency}")
    _require(isinstance(operation.get("desired_state_operation"), str) and operation["desired_state_operation"], f"desired state missing: {operation_id}")
    required_inputs = operation.get("exact_required_inputs")
    _require(isinstance(required_inputs, list) and required_inputs, f"required inputs missing: {operation_id}")
    input_names: set[str] = set()
    for index, item in enumerate(required_inputs):
        _require(isinstance(item, Mapping), f"required input is not an object: {operation_id}[{index}]")
        _validate_required_input(item, f"operations.{operation_id}.exact_required_inputs[{index}]")
        _require(item["name"] not in input_names, f"duplicate required input: {operation_id}.{item['name']}")
        input_names.add(item["name"])
    if operation_id in {"bind_candidate_image_digest", "configure_cloud_run_and_confidential_space"}:
        repository_inputs = [item for item in required_inputs if item["name"] == "target_repository"]
        _require(len(repository_inputs) == 1 and repository_inputs[0]["value"] == "p5-cs", f"reviewed repository drift: {operation_id}")
    for field in ("preconditions", "expected_postconditions", "stop_conditions", "rollback_conditions"):
        values = operation.get(field)
        _require(isinstance(values, list) and values and all(isinstance(value, str) and value for value in values), f"{field} missing: {operation_id}")
    immutable = operation.get("immutable_digests")
    _require(isinstance(immutable, list) and immutable, f"immutable digests missing: {operation_id}")
    for index, item in enumerate(immutable):
        _require(isinstance(item, Mapping) and set(item) == _DIGEST_FIELDS, f"digest record fields are not closed: {operation_id}[{index}]")
        _require(isinstance(item["name"], str) and item["name"], f"digest name missing: {operation_id}[{index}]")
        _require(isinstance(item["source"], str) and item["source"], f"digest source missing: {operation_id}[{index}]")
        _require(item["classification"] in {"diagnostic_input", "production_input", "source_binding", "derived_after_approval"}, f"digest classification invalid: {operation_id}[{index}]")
        if item["value"] is not None:
            _is_digest(item["value"], f"operations.{operation_id}.immutable_digests[{index}].value")
    _require(isinstance(operation.get("approval_gate"), str) and "APPROVAL_REQUIRED:" in operation["approval_gate"], f"approval gate missing: {operation_id}")
    rerunnable = operation.get("rerunnable")
    _require(isinstance(rerunnable, Mapping) and set(rerunnable) == {"idempotency_key", "existing_match", "drift", "writes"}, f"rerunnable contract is not closed: {operation_id}")
    _require(all(isinstance(rerunnable[key], str) and rerunnable[key] for key in rerunnable), f"rerunnable contract incomplete: {operation_id}")
    _require("no-op" in rerunnable["existing_match"] and "fail closed" in rerunnable["drift"], f"rerunnable semantics incomplete: {operation_id}")
    boundary = operation.get("mutation_boundary")
    _require(isinstance(boundary, Mapping) and set(boundary) == {"mode", "apply_interface", "commands", "direct_cloud_mutations"}, f"mutation boundary is not closed: {operation_id}")
    _require(boundary["mode"] == "review_only_no_execution" and boundary["commands"] == [] and boundary["direct_cloud_mutations"] is False, f"operation is executable: {operation_id}")
    _require(isinstance(boundary["apply_interface"], str) and boundary["apply_interface"], f"apply interface missing: {operation_id}")


def _approval_scope_digest(plan: Mapping[str, Any]) -> str:
    # Approval records are excluded only to avoid a self-referential digest.  All
    # other plan fields are authoritative scope: changing operation prose,
    # exact inputs, typed desired state, activation, inventory, rerun policy, or
    # the review-only apply boundary invalidates every approval record.
    scope = {key: value for key, value in plan.items() if key != "approval_gate_records"}
    return sha256(scope)


def _validate_typed_state(plan: Mapping[str, Any], repository_root: Path) -> None:
    records = plan.get("operation_records")
    _require(isinstance(records, list) and len(records) == len(_OPERATION_IDS), "typed operation record count drift")
    legacy_by_id = {operation["id"]: operation for operation in plan["operations"]}
    typed_by_id: dict[str, Mapping[str, Any]] = {}
    expected_plan_digest = _approval_scope_digest(plan)
    for record in records:
        operation_id = record.get("operation_id") if isinstance(record, Mapping) else None
        _require(isinstance(record, Mapping) and set(record) == _TYPED_OPERATION_FIELDS, f"typed operation record is not closed: {operation_id}")
        _require(record["schema"] == "P5R0RS069OperationRecordV1", f"typed operation schema drift: {operation_id}")
        _require(operation_id in _OPERATION_IDS and operation_id not in typed_by_id, f"typed operation id drift: {operation_id}")
        typed_by_id[operation_id] = record
        legacy = legacy_by_id[operation_id]
        _require(record["dependency_ids"] == legacy["depends_on"], f"typed dependency drift: {operation_id}")
        expected_inputs = {item["name"]: item["value"] for item in legacy["immutable_digests"]}
        _require(record["input_digest_map"] == expected_inputs, f"typed input digest map drift: {operation_id}")
        for name, value in record["input_digest_map"].items():
            if value is not None:
                _is_digest(value, f"typed input digest {operation_id}.{name}")
        _require(set(record["preconditions"]) == {"dependencies_satisfied", "inputs_resolved", "approval_present", "remote_state_verified"}, f"typed preconditions are not closed: {operation_id}")
        _require(set(record["postconditions"]) == {"desired_state_match", "rendered", "mutation_performed"}, f"typed postconditions are not closed: {operation_id}")
        _require(all(isinstance(value, bool) and value is False for value in record["preconditions"].values()), f"typed preconditions must remain blocked: {operation_id}")
        _require(all(isinstance(value, bool) and value is False for value in record["postconditions"].values()), f"typed postconditions must remain unclaimed: {operation_id}")
        _require(record["approval_record_ref"] is None and record["approval_record_digest"] is None, f"typed approval must remain absent: {operation_id}")
        _require(record["idempotency_key"] == legacy["rerunnable"]["idempotency_key"], f"typed idempotency drift: {operation_id}")
        _require(record["drift_policy"] == "fail_closed" and record["rollback_policy"] == "no_mutation_without_approval", f"typed rerun policy drift: {operation_id}")
        _require(record["enabled"] is False and record["commands"] == [], f"typed operation is executable: {operation_id}")
        resource = record["resource_state"]
        _require(isinstance(resource, Mapping) and set(resource) == _RESOURCE_STATE_FIELDS, f"resource state is not closed: {operation_id}")
        _require(isinstance(resource["addresses"], list) and resource["addresses"] and all(isinstance(value, str) and value.startswith("rs069.") for value in resource["addresses"]), f"resource addresses missing: {operation_id}")
        _require(resource["ownership"] == "rs-069", f"resource ownership drift: {operation_id}")
        _require(resource["observed_fingerprints"] == {}, f"remote state must remain unobserved: {operation_id}")
        _require(resource["state_backend"] == {"kind": "repository_only", "location": None, "lock_required": True}, f"state backend drift: {operation_id}")
        _require(resource["change_policy"] == {"create": "create_only", "update": "generation_checked", "delete": "forbidden"}, f"change policy drift: {operation_id}")
    _require(tuple(typed_by_id) == _OPERATION_IDS, "typed operation reorder detected")

    approvals = plan.get("approval_gate_records")
    _require(isinstance(approvals, list) and len(approvals) == len(_OPERATION_IDS), "approval gate record count drift")
    approval_ids: list[str] = []
    approval_by_id: dict[str, Mapping[str, Any]] = {}
    for record in approvals:
        operation_id = record.get("operation_id") if isinstance(record, Mapping) else None
        _require(isinstance(record, Mapping) and set(record) == _APPROVAL_FIELDS, f"approval gate record is not closed: {operation_id}")
        _require(record["schema"] == "P5R0RS069ApprovalGateV1", f"approval gate schema drift: {operation_id}")
        _require(operation_id in _OPERATION_IDS and operation_id not in approval_ids, f"approval gate operation drift: {operation_id}")
        approval_ids.append(operation_id)
        approval_by_id[operation_id] = record
        _require(record["plan_digest"] == expected_plan_digest, f"approval plan digest mismatch: {operation_id}")
        _is_digest(record["plan_digest"], f"approval plan digest {operation_id}")
        _require(record["input_digest_map"] == typed_by_id[operation_id]["input_digest_map"], f"approval input digest mismatch: {operation_id}")
        _require(record["approval_record_ref"] is None and record["approval_record_digest"] is None, f"approval record must remain absent: {operation_id}")
        _require(record["master_approved"] is False and record["user_approved"] is False and record["approved"] is False and record["enabled"] is False, f"approval gate is enabled: {operation_id}")
    _require(tuple(approval_ids) == _OPERATION_IDS, "approval gate reorder detected")

    objects = plan.get("gcs_object_records")
    _require(isinstance(objects, list) and len(objects) == 11, "GCS object record count drift")
    index_path = repository_root / plan["source_bindings"]["artifact_index"]
    index = _load_json(index_path, "artifact index")
    artifacts = index.get("artifacts")
    _require(isinstance(artifacts, Mapping) and len(artifacts) == 11, "artifact index object count drift")
    seen_objects: set[str] = set()
    expected_object_order = tuple(artifacts)
    actual_object_order = tuple(record.get("object_id") if isinstance(record, Mapping) else None for record in objects)
    _require(actual_object_order == expected_object_order, "GCS object record order drift")
    for number, record in enumerate(objects):
        object_id = record.get("object_id") if isinstance(record, Mapping) else number
        _require(isinstance(record, Mapping) and set(record) == _OBJECT_FIELDS, f"GCS object record is not closed: {object_id}")
        _require(record["schema"] == "P5R0RS069GCSObjectRecordV1", f"GCS object schema drift: {object_id}")
        _require(record["object_id"] in artifacts and record["object_id"] not in seen_objects, f"GCS object identity drift: {object_id}")
        seen_objects.add(record["object_id"])
        expected = artifacts[record["object_id"]]
        _require(record["local_artifact_path"] == expected["path"], f"GCS local path drift: {object_id}")
        _require(record["object_suffix"] == expected["path"].split("var/p5-r0-diagnostic-inputs/", 1)[1], f"GCS object suffix drift: {object_id}")
        _require(record["private"] is expected["private"] and record["artifact_digest"] == expected["digest"] and record["file_digest"] == expected["file_digest"], f"GCS object digest/visibility drift: {object_id}")
        _require(record["destination"] == {"bucket": None, "prefix": None, "run_id": None}, f"GCS destination must remain unresolved: {object_id}")
        _require(record["ownership"] == "rs-069" and record["mode"] == "create_only_or_exact_generation_match", f"GCS ownership/mode drift: {object_id}")
        _require(record["generation_precondition"] == {"kind": "if_absent_or_exact_generation", "expected_generation": None}, f"GCS generation policy drift: {object_id}")
        _require(record["upload_state"] == "not_uploaded" and record["upload_performed"] is False, f"GCS upload boundary drift: {object_id}")
        path = repository_root / record["local_artifact_path"]
        _require(path.is_file() and sha256(path.read_bytes()) == record["file_digest"], f"GCS file digest drift: {object_id}")
    _require(seen_objects == set(artifacts), "GCS object set drift")

    activation = plan.get("confidential_space_activation")
    _require(isinstance(activation, Mapping) and set(activation) == _ACTIVATION_FIELDS, "Confidential Space activation record is not closed")
    _require(activation["schema"] == "P5R0RS069ConfidentialSpaceActivationV1" and activation["operation_id"] == "configure_cloud_run_and_confidential_space", "activation binding drift")
    _require(activation["state"] == "blocked" and activation["approved"] is False and activation["enabled"] is False, "activation must remain blocked")
    _require(activation["transition_order"] == ["blocked", "approved", "attestation_verified", "capabilities_activated"], "activation transition order drift")
    expected_transitions = [("blocked", "approved"), ("approved", "attestation_verified"), ("attestation_verified", "capabilities_activated"), ("blocked", "failed_closed"), ("approved", "failed_closed"), ("attestation_verified", "failed_closed")]
    _require(isinstance(activation["transitions"], list) and len(activation["transitions"]) == len(expected_transitions), "activation transition count drift")
    for transition, expected in zip(activation["transitions"], expected_transitions):
        _require(set(transition) == _TRANSITION_FIELDS and (transition["from"], transition["to"]) == expected and transition["enabled"] is False, "activation transition skip or enablement detected")
    _require(set(activation["digest_bindings"]) == set(_ACTIVATION_DIGEST_KEYS) | {"artifact_index_digest"}, "activation digest bindings are not closed")
    for name, value in activation["digest_bindings"].items():
        if value is not None:
            _is_digest(value, f"activation digest {name}")
    _require(activation["digest_bindings"]["artifact_index_digest"] == plan["read_only_inventory"]["generated_bundle"]["artifact_index_digest"], "activation artifact digest drift")
    _require(activation["equality_bindings"] == {key: list(paths) for key, paths in _ACTIVATION_BINDING_PATHS.items()}, "activation equality binding paths drift")
    for binding_name, paths in _ACTIVATION_BINDING_PATHS.items():
        activation_value = activation["digest_bindings"][binding_name]
        for path in paths:
            operation_id, input_name = path.split(".", 1)
            _require(operation_id in typed_by_id, f"activation binding operation missing: {path}")
            operation_value = typed_by_id[operation_id]["input_digest_map"].get(input_name)
            _require(operation_value == activation_value, f"activation digest binding mismatch: {binding_name} -> {path}")
            approval_value = approval_by_id[operation_id]["input_digest_map"].get(input_name)
            _require(approval_value == activation_value, f"activation approval binding mismatch: {binding_name} -> {path}")
        for operation_id, input_name, mode in _ACTIVATION_INPUT_BINDINGS[binding_name]:
            required_inputs_by_name = {
                item["name"]: item["value"]
                for item in legacy_by_id[operation_id]["exact_required_inputs"]
            }
            _require(input_name in required_inputs_by_name, f"activation input binding missing: {operation_id}.{input_name}")
            required_value = required_inputs_by_name[input_name]
            if _is_allowed_unresolved(required_value):
                expected_value = None
            elif mode == "digest":
                expected_value = required_value
            else:
                expected_value = sha256(canonical_bytes(required_value))
            _require(activation_value == expected_value, f"activation input digest mismatch: {binding_name} -> {operation_id}.{input_name}")
    _require(activation["attestation"] == {"present": False, "verified": False, "evidence_ref": None, "evidence_digest": None}, "attestation must remain absent")
    _require(activation["capabilities"] == {"activated": False, "grants": [], "grant_digest": None}, "capabilities must remain inactive")


def _validate_inventory(plan: Mapping[str, Any], repository_root: Path) -> None:
    inventory = plan["read_only_inventory"]
    _require(inventory.get("classification") == "read_only_local_inventory_non_production", "inventory classification drift")
    _require(inventory.get("production_claim") is False and inventory.get("cloud_operations") == [], "inventory crosses production boundary")
    index_path = repository_root / plan["source_bindings"]["artifact_index"]
    index = _load_json(index_path, "artifact index")
    expected_index_digest = inventory["generated_bundle"]["artifact_index_digest"]
    actual_index_digest = sha256({key: value for key, value in index.items() if key != "index_digest"})
    _require(index.get("index_digest") == expected_index_digest == actual_index_digest, "artifact index digest drift")
    generated = inventory["generated_bundle"]
    for field in ("artifact_index_digest", "manifest_digest", "private_store_digest", "task_set_digest", "control_commitment_digest", "unsigned_lock_digest"):
        _is_digest(generated[field], f"read_only_inventory.generated_bundle.{field}")
    _require(index.get("manifest_digest") == generated["manifest_digest"], "manifest digest drift")
    _require(index.get("private_store_digest") == generated["private_store_digest"], "private store digest drift")
    _require(index.get("task_set_digest") == generated["task_set_digest"], "task set digest drift")
    _require(index.get("control_commitment_digest") == generated["control_commitment_digest"], "control commitment digest drift")
    _require(index.get("unsigned_lock_digest") == generated["unsigned_lock_digest"], "unsigned lock digest drift")
    observations = inventory.get("local_closure_observations")
    _require(isinstance(observations, list) and observations, "local closure observations missing")
    for index_number, observation in enumerate(observations):
        _require(set(observation) == {"source", "classification", "image_digest", "runtime_digest", "seccomp_digest", "closure_digest", "usable_as_production_input"}, f"closure observation fields are not closed: {index_number}")
        _require(observation["classification"] == "workspace_only_preflight" and observation["usable_as_production_input"] is False, f"closure observation crossed production boundary: {index_number}")
        for field in ("image_digest", "seccomp_digest", "closure_digest"):
            _is_digest(observation[field], f"closure observation {index_number}.{field}")
        if observation["runtime_digest"] is not None:
            _is_digest(observation["runtime_digest"], f"closure observation {index_number}.runtime_digest")
        path = repository_root / observation["source"]
        _require(path.is_file(), f"closure observation missing: {observation['source']}")
        source = _load_json(path, observation["source"])
        _require(source.get("image_digest") == observation["image_digest"], f"closure image observation drift: {index_number}")
        _require(source.get("seccomp_digest") == observation["seccomp_digest"], f"closure seccomp observation drift: {index_number}")
        _require(source.get("closure_digest") == observation["closure_digest"], f"closure digest observation drift: {index_number}")
        if observation["runtime_digest"] is not None:
            _require(source.get("runtime_digest") == observation["runtime_digest"], f"closure runtime observation drift: {index_number}")


def _validate_no_commands(plan: Mapping[str, Any]) -> None:
    apply_plan = plan["apply_plan"]
    _require(apply_plan.get("mode") == "review_only_no_execution", "apply mode is not review-only")
    _require(apply_plan.get("commands") == [] and apply_plan.get("mutations_performed") is False and apply_plan.get("direct_gcloud_mutations") is False, "apply plan contains executable or performed mutations")
    _require(apply_plan.get("approval_required") is True, "apply plan lacks approval gate")
    forbidden = apply_plan.get("forbidden_operations")
    _require(isinstance(forbidden, list), "forbidden mutation boundary is incomplete")
    forbidden_lower = {str(term).lower() for term in forbidden}
    _require(all(term in forbidden_lower for term in _FORBIDDEN_MUTATION_TERMS), "forbidden mutation boundary is incomplete")
    _require(isinstance(apply_plan.get("approved_apply_interface"), str) and _REQUIRED_INPUT_RE.match(apply_plan["approved_apply_interface"]), "approved apply interface must remain unresolved")
    for operation in plan["operations"]:
        _require(operation["mutation_boundary"]["commands"] == [], f"operation embeds commands: {operation['id']}")
    serialized = json.dumps(plan, sort_keys=True).lower()
    _require("gcloud " not in serialized.replace("gcloud mutation", ""), "executable gcloud command text is embedded")


def _validate_static(plan: Mapping[str, Any], repository_root: Path) -> None:
    _require(set(plan) == _TOP_LEVEL_FIELDS, "RS-069 plan fields are not closed")
    _require(plan["schema"] == "P5R0RS069IaCChangePlanV1", "RS-069 schema drift")
    _require(plan["classification"] == "repository_definition_only" and plan["status"] == "blocked_pending_master_approval", "RS-069 must remain blocked")
    _require(plan["master_run"] == "P5-MASTER-001" and plan["runsheet_item"] == "RS-069", "RS-069 identity drift")
    _require(plan["authority_contract"] == {
        "custody": "self_custodied",
        "authority_mode": "self_custodied_diagnostic",
        "signed_environment": "Confidential Space",
        "independent_evaluator_required": False,
        "independent_evaluator_claim": False,
        "external_authority_required": True,
        "approval_source": "master_approval_and_verified_confidential_space_attestation",
        "production_promotion_allowed": False,
    }, "authority contract drift")
    _require(plan["global_preconditions"]["repository_root"] == str(repository_root), "repository boundary drift")
    _require(plan["global_preconditions"]["pwd_verified"] is True, "pwd was not verified")
    _require(plan["global_preconditions"]["master_approval"] is False and plan["global_preconditions"]["confidential_space_approval"] is False, "plan is not approval-blocked")
    _require(plan["global_preconditions"]["cloud_operations_performed"] is False and plan["global_preconditions"]["task_execution_performed"] is False, "plan claims cloud or task execution")
    _require(plan["unknown_value_policy"]["allowed_unresolved_values"] == [None, "REQUIRED_INPUT:*"] , "unknown-value policy drift")
    _require(plan["rerun_contract"]["approval"] == "all mutation-capable transitions are disabled until explicit master approval", "approval rerun contract drift")
    _require(plan["local_validation"]["module"] == "services.p5_r0_evaluator.deploy.rs069_change_plan", "validator binding drift")
    _require(isinstance(plan["claim_boundary"], str) and "independent evaluator claim" in plan["claim_boundary"], "claim boundary drift")
    source_bindings = plan["source_bindings"]
    _require(isinstance(source_bindings, Mapping) and source_bindings, "source bindings missing")
    for name, relative in source_bindings.items():
        _require(isinstance(name, str) and isinstance(relative, str) and not Path(relative).is_absolute(), f"source binding is not repository-relative: {name}")
        _require((repository_root / relative).is_file(), f"source binding missing: {name}")


def _validate_order(plan: Mapping[str, Any]) -> tuple[str, ...]:
    operations = plan["operations"]
    _require(isinstance(operations, list) and len(operations) == len(_OPERATION_IDS), "operation count drift")
    seen: set[str] = set()
    ids: list[str] = []
    for expected_order, operation in enumerate(operations, start=1):
        _require(isinstance(operation, Mapping), f"operation {expected_order} is not an object")
        _validate_operation(operation, expected_order, seen)
        ids.append(operation["id"])
    _require(tuple(ids) == _OPERATION_IDS, "operation order drift")
    for operation in operations:
        for dependency in operation["depends_on"]:
            _require(ids.index(dependency) < ids.index(operation["id"]), f"dependency is not ordered: {operation['id']} depends on {dependency}")
    return tuple(ids)


def validate_plan(plan: Mapping[str, Any], *, repository_root: Path = REPOSITORY_ROOT) -> RS069ValidationReport:
    root = Path(repository_root).resolve()
    _validate_static(plan, root)
    operation_ids = _validate_order(plan)
    _validate_inventory(plan, root)
    _validate_no_commands(plan)
    _validate_typed_state(plan, root)
    unresolved: list[str] = []
    for operation in plan["operations"]:
        for item in operation["exact_required_inputs"]:
            if _is_allowed_unresolved(item["value"]):
                unresolved.append(f"{operation['id']}.{item['name']}")
        for item in operation["immutable_digests"]:
            if item["value"] is None:
                unresolved.append(f"{operation['id']}.immutable_digests.{item['name']}")
    return RS069ValidationReport(
        ready=False,
        status=plan["status"],
        plan_digest=sha256(dict(plan)),
        operation_ids=operation_ids,
        unresolved_inputs=tuple(unresolved),
        cloud_operations=(),
    )


def load_plan(path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    return _load_json(Path(path), "RS-069 plan")


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local-only RS-069 IaC change plan")
    parser.add_argument("command", choices=("validate",))
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    args = parser.parse_args(argv)
    try:
        report = validate_plan(load_plan(args.plan))
    except RS069ValidationError as exc:
        print(f"RS-069 validation blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ready": report.ready, "status": report.status, "plan_digest": report.plan_digest, "operation_ids": report.operation_ids, "unresolved_inputs": report.unresolved_inputs, "cloud_operations": report.cloud_operations}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = ["DEFAULT_PLAN", "RS069ValidationError", "RS069ValidationReport", "load_plan", "validate_plan"]
