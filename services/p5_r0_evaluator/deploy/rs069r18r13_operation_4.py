"""Fail-closed RS-069R18R13 operation-4 ingestion boundary.

This module is deliberately separate from the legacy RS-069 apply runner and
from the R18R10/R18R12 review artifacts.  It consumes a reviewed destination
binding and single-operation approval, validates the immutable local bundle and
prior ledgers, then uses only an explicitly injected ObjectStore.  It never
obtains credentials, lists or deletes objects, changes the master plan, or
approves downstream operations.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.controlled_run_materializer import (
    validate_artifact_commitments,
)
from services.p5_r0_evaluator.deploy.kms_lock_signing import validate_unsigned_request
from services.p5_r0_evaluator.deploy.rs069_change_plan import (
    DEFAULT_PLAN,
    REPOSITORY_ROOT,
    load_plan,
    validate_plan,
)
from services.p5_r0_evaluator.deploy.rs069r18r12_operation_3 import (
    _load_r18r10_dependency,
)
from services.p5_r0_evaluator.interfaces import Object, ObjectStore, StoreError

OPERATION_ID = "ingest_generated_bundle_to_gcs"
OPERATION_ORDER = 4
R18R12_OPERATION_ID = "bind_self_custodied_authority_and_kms"
R18R10_OPERATION_ID = "correct_wip_provider_claim_mapping"
LATER_OPERATION_IDS = (
    "configure_cloud_run_and_confidential_space",
    "prepare_supervisor_and_run_request",
    "cleanup_or_rollback",
)
DEFAULT_ARTIFACT_INDEX = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/artifact-index.json"
DEFAULT_REQUEST = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json"
DEFAULT_R18R12_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-3-r18r12-ledger.jsonl"
DEFAULT_R18R12_APPROVAL = Path(__file__).with_name("rs-069r18r12-operation-3-approval.json")
DEFAULT_CONTRACT = Path(__file__).with_name("rs-069r18r13-operation-4-contract.json")
DEFAULT_BINDING = Path(__file__).with_name("rs-069r18r13-destination-binding.json")
DEFAULT_APPROVAL = Path(__file__).with_name("rs-069r18r13-operation-4-approval.json")
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-4-r18r13-ledger.jsonl"
APPROVAL_ID = "P5-MASTER-001/APPROVAL-010-RS069R18R13"
DISPATCH_ID = "DISPATCH-046"
APPROVAL_SCHEMA = "P5R0RS069R18R13ApprovalArtifactV1"
BINDING_SCHEMA = "P5R0RS069R18R13DestinationBindingV1"
CONTRACT_SCHEMA = "P5R0RS069R18R13Operation4ContractV1"
LEDGER_SCHEMA = "P5R0RS069R18R13LedgerEventV1"
ACCEPTANCE_CONTRACT = "P5R0RS069R18R13Operation4AcceptanceV1"
_NAMESPACE_FORMULA = "gs://{bucket}/{prefix}/{run_id}/{object_suffix}"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$")
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
_RUN_RE = re.compile(r"^rs069r18r13-[a-z0-9][a-z0-9-]{7,63}$")
_ATTEMPT_RE = re.compile(r"^rs069r18r13-op4-[a-z0-9][a-z0-9-]{7,63}$")
_RESERVED_ATTEMPT_IDS = {"rs069r18r13-op4-unresolved"}
_EXPECTED_REQUEST_DIGEST = "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d"
_EXPECTED_UNSIGNED_LOCK_DIGEST = "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"
_EXPECTED_R18R12_EVENTS = (
    "sha256:be2454f56eee8bd89a63241ec761aabb89f2370345bed199c483c308bb4f96c9",
    "sha256:21e8d53aa1c21c651a46f9e608ad10fc1a6f49cdf3ef20c01aebcb70d54522b8",
    "sha256:bbb534870778e46c38c6e0fc03dbc36f47f5f78c6127b12ef2e8557877f0a727",
    "sha256:30a59807d8dbf7aa2529d4efab406b4dcd5e87597442be71045827c816833329",
)


class RS069R18R13Blocked(RuntimeError):
    """The reviewed operation-4 packet or state is inadmissible."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RS069R18R13Blocked(message)


def _is_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} is missing or unresolved")
    return value


def _load_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical(path.read_bytes())
    except Exception as exc:
        raise RS069R18R13Blocked(f"{label} is unavailable or not canonical") from exc
    _require(isinstance(value, dict), f"{label} root must be an object")
    return value


def _digest(value: Any) -> str:
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return sha256({key: item for key, item in value.items() if key != field})


def _resolve(root: Path, value: Any, label: str) -> Path:
    _require(isinstance(value, str) and value and not Path(value).is_absolute(), f"{label} must be repository-relative")
    resolved_root = root.resolve()
    resolved = (resolved_root / value).resolve()
    _require(resolved_root in resolved.parents, f"{label} escapes the repository")
    _require(resolved.is_file(), f"{label} is missing: {value}")
    return resolved


def _validate_contract(contract: Mapping[str, Any]) -> None:
    expected = {
        "schema", "classification", "operation_id", "operation_order", "scope",
        "dependencies", "artifact_index_path", "namespace_formula", "object_policy",
        "generation_policy", "destination_policy", "credential_policy", "ledger_policy",
        "downstream_operations", "unsigned_request_policy", "claim_boundary",
    }
    _require(set(contract) == expected, "R18R13 contract is not closed")
    _require(contract["schema"] == CONTRACT_SCHEMA and contract["classification"] == "repository_review_only_non_release", "R18R13 contract identity drift")
    _require(contract["operation_id"] == OPERATION_ID and contract["operation_order"] == OPERATION_ORDER and contract["scope"] == [OPERATION_ID], "R18R13 contract scope drift")
    _require(contract["dependencies"] == [R18R12_OPERATION_ID] and contract["artifact_index_path"] == "var/p5-r0-diagnostic-inputs/artifact-index.json", "R18R13 dependency or input path drift")
    _require(contract["namespace_formula"] == _NAMESPACE_FORMULA, "R18R13 namespace formula drift")
    _require(contract["object_policy"] == {"count": 11, "order": "artifact-index order", "private_truth_suffix": "private-truth/case-store.json", "private_truth_visibility": "private"}, "R18R13 object policy drift")
    _require(contract["generation_policy"] == {"mode": "create-only-or-exact-generation-match", "missing_generation": 0, "ambiguous_generation": "reject", "drift": "fail_closed"}, "R18R13 generation policy drift")
    _require(contract["destination_policy"] == {"bucket_project_binding": "required", "bucket": "private reviewed bucket", "prefix": "relative reviewed prefix", "run_id": "approved unique canonical run ID", "list": False, "delete": False, "overwrite": False}, "R18R13 destination policy drift")
    _require(contract["credential_policy"] == {"source": "injected reviewed execution path only", "local_credential_material": False, "missing_credentials": "reject"}, "R18R13 credential policy drift")
    _require(contract["ledger_policy"] == {"path": "var/p5-r0-rs069/operation-4-r18r13-ledger.jsonl", "mode": "append_only", "retry": False, "historical_rewrite": False}, "R18R13 ledger policy drift")
    _require(contract["downstream_operations"] == [{"id": item, "enabled": False} for item in LATER_OPERATION_IDS], "R18R13 downstream boundary drift")
    _require(contract["unsigned_request_policy"] == {"request_digest": _EXPECTED_REQUEST_DIGEST, "unsigned_lock_digest": _EXPECTED_UNSIGNED_LOCK_DIGEST, "signature_present": False}, "unsigned request policy drift")
    _require(contract["claim_boundary"] == "One reviewed operation only; no downstream enablement, authority, signature, task execution, or fabricated cloud evidence.", "R18R13 claim boundary drift")


def _validate_plan(plan: Mapping[str, Any], root: Path) -> tuple[str, list[dict[str, Any]]]:
    try:
        report = validate_plan(plan, repository_root=root)
    except Exception as exc:
        raise RS069R18R13Blocked("RS-069 plan validation failed") from exc
    _require(plan.get("status") == "blocked_pending_master_approval", "master RS-069 plan was changed")
    operations = plan.get("operations")
    _require(isinstance(operations, list) and len(operations) >= OPERATION_ORDER, "RS-069 operation list is incomplete")
    operation = operations[OPERATION_ORDER - 1]
    _require(operation.get("id") == OPERATION_ID and operation.get("order") == OPERATION_ORDER, "operation-4 identity drift")
    _require(operation.get("depends_on") == [R18R12_OPERATION_ID], "operation-4 dependency drift")
    required = {item.get("name"): item for item in operation.get("exact_required_inputs", [])}
    _require(required.get("bucket", {}).get("value") is None and required.get("prefix", {}).get("value") is None and required.get("run_id", {}).get("value") is None, "master plan destination inputs were silently resolved")
    _require(required.get("artifact_index", {}).get("value") == "var/p5-r0-diagnostic-inputs/artifact-index.json" and required.get("object_generation_preconditions", {}).get("value") == "create-only-or-exact-generation-match", "operation-4 required inputs drift")
    _require(operation.get("mutation_boundary") == {"mode": "review_only_no_execution", "apply_interface": "approved IaC workflow only", "commands": [], "direct_cloud_mutations": False}, "operation-4 mutation boundary drift")
    typed = next((item for item in plan.get("operation_records", []) if item.get("operation_id") == OPERATION_ID), None)
    _require(isinstance(typed, Mapping) and typed.get("enabled") is False and typed.get("commands") == [], "operation-4 typed state is enabled")
    for later in LATER_OPERATION_IDS:
        item = next((candidate for candidate in plan.get("operation_records", []) if candidate.get("operation_id") == later), None)
        _require(isinstance(item, Mapping) and item.get("enabled") is False, f"downstream operation enabled: {later}")
    records = plan.get("gcs_object_records")
    _require(isinstance(records, list) and len(records) == 11, "canonical GCS object list must contain exactly 11 records")
    for record in records:
        _require(set(record) == {"schema", "object_id", "local_artifact_path", "object_suffix", "private", "artifact_digest", "file_digest", "destination", "ownership", "mode", "generation_precondition", "upload_state", "upload_performed"}, "GCS object record is not closed")
        _require(record["schema"] == "P5R0RS069GCSObjectRecordV1" and record["ownership"] == "rs-069" and record["mode"] == "create_only_or_exact_generation_match", "GCS object record identity drift")
        _require(record["destination"] == {"bucket": None, "prefix": None, "run_id": None} and record["generation_precondition"] == {"kind": "if_absent_or_exact_generation", "expected_generation": None} and record["upload_state"] == "not_uploaded" and record["upload_performed"] is False, "GCS object record crosses execution boundary")
        _is_digest(record["artifact_digest"], f"{record['object_id']}.artifact_digest")
        _is_digest(record["file_digest"], f"{record['object_id']}.file_digest")
    return report.plan_digest, records


def _validate_r18r12(path: Path, approval_path: Path, r18r10: Mapping[str, Any]) -> dict[str, str]:
    _require(path.resolve() == DEFAULT_R18R12_LEDGER.resolve(), "R18R12 dependency is not the canonical terminal ledger")
    raw = path.read_bytes() if path.is_file() else b""
    lines = raw.splitlines()
    _require(len(lines) == 4, "R18R12 dependency ledger must contain exactly four events")
    records: list[dict[str, Any]] = []
    previous: str | None = None
    for line_number, line in enumerate(lines, start=1):
        try:
            record = parse_canonical(line)
        except Exception as exc:
            raise RS069R18R13Blocked(f"R18R12 ledger is not canonical at line {line_number}") from exc
        _require(record.get("previous_event_digest") == previous, "R18R12 ledger chain drift")
        _require(record.get("event_digest") == _digest_without(record, "event_digest"), "R18R12 ledger event digest drift")
        records.append(record)
        previous = record["event_digest"]
    _require(tuple(record["event_digest"] for record in records) == _EXPECTED_R18R12_EVENTS, "R18R12 ledger is not the reviewed immutable record")
    _require(all(record.get("operation_id") == R18R12_OPERATION_ID and record.get("operation_order") == 3 for record in records), "R18R12 operation scope drift")
    terminal = records[-1]
    _require(terminal.get("kind") == "run_stopped" and terminal.get("status") == "verified_repository_binding_review_only" and terminal.get("later_operations_enabled") is False, "R18R12 terminal state is not verified")
    _require(OPERATION_ID in terminal.get("later_operations_skipped", []) and terminal.get("cloud_operations") == [] and terminal.get("mutations_performed") is False, "R18R12 downstream boundary drift")
    prior_approval = _load_canonical(approval_path, "R18R12 approval")
    _require(prior_approval.get("artifact_digest") == _digest_without(prior_approval, "artifact_digest"), "R18R12 approval digest drift")
    _require(prior_approval.get("operation_id") == R18R12_OPERATION_ID and prior_approval.get("scope") == [R18R12_OPERATION_ID] and prior_approval.get("enabled") is True, "R18R12 approval scope drift")
    _require(records[0].get("approval_digest") == prior_approval["artifact_digest"], "R18R12 approval provenance drift")
    _require(records[1].get("dependency_ledger_head_digest") == r18r10["ledger_head_digest"], "R18R10 to R18R12 dependency drift")
    return {"ledger_head_digest": terminal["event_digest"], "verified_event_digest": records[2]["event_digest"], "approval_digest": prior_approval["artifact_digest"], "poststate_digest": r18r10["poststate_digest"]}


def _validate_request(path: Path, root: Path) -> dict[str, Any]:
    _require(path.resolve() == DEFAULT_REQUEST.resolve(), "unsigned request is not the canonical request")
    request = _load_canonical(path, "unsigned request")
    try:
        report = validate_unsigned_request(request)
    except Exception as exc:
        raise RS069R18R13Blocked("exact unsigned request validation failed") from exc
    _require(report.request_digest == _EXPECTED_REQUEST_DIGEST and report.unsigned_lock_digest == _EXPECTED_UNSIGNED_LOCK_DIGEST, "unsigned request digest drift")
    _require(request.get("cloud_operations") == [] and request.get("production_signature_created") is False, "unsigned request crosses the execution boundary")
    return request


def _validate_index(path: Path, root: Path, records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], str]:
    _require(path.resolve() == DEFAULT_ARTIFACT_INDEX.resolve(), "artifact index is not the canonical bundle index")
    index = _load_canonical(path, "artifact index")
    try:
        checked = validate_artifact_commitments(index, root / "var/p5-r0-diagnostic-inputs")
    except Exception as exc:
        raise RS069R18R13Blocked("artifact index or local artifact validation failed") from exc
    artifacts = index.get("artifacts")
    _require(isinstance(artifacts, Mapping) and list(artifacts) == [record["object_id"] for record in records], "canonical bundle object order drift")
    for record in records:
        artifact = artifacts[record["object_id"]]
        _require(artifact.get("path") == record["local_artifact_path"] and artifact.get("digest") == record["artifact_digest"] and artifact.get("file_digest") == record["file_digest"] and artifact.get("private") == record["private"], f"canonical artifact binding drift: {record['object_id']}")
        _require(checked[record["object_id"]]["file_digest"] == record["file_digest"], f"local artifact digest drift: {record['object_id']}")
    return index, index["index_digest"]


def _safe_relative_suffix(value: Any) -> str:
    _require(isinstance(value, str) and value and not value.startswith("/") and "\\" not in value, "object suffix is not a safe relative path")
    parts = value.split("/")
    _require(all(part not in {"", ".", ".."} for part in parts), "object suffix contains an unsafe path segment")
    return value


def _validate_destination(binding: Mapping[str, Any], *, index_digest: str, request: Mapping[str, Any], dependency: Mapping[str, str]) -> dict[str, Any]:
    expected = {"schema", "classification", "status", "operation_id", "operation_order", "scope", "project_id", "bucket", "prefix", "run_id", "namespace_formula", "visibility", "credential_binding", "artifact_index_digest", "unsigned_lock_digest", "dependency_ledger_head_digest", "artifact_digest"}
    _require(set(binding) == expected, "R18R13 destination binding is not closed")
    _require(binding.get("schema") == BINDING_SCHEMA and binding.get("classification") == "repository_review_only_non_release" and binding.get("status") == "reviewed_destination_binding_pending_execution", "R18R13 destination binding identity drift")
    _require(binding.get("operation_id") == OPERATION_ID and binding.get("operation_order") == OPERATION_ORDER and binding.get("scope") == [OPERATION_ID], "R18R13 destination binding scope drift")
    project, bucket, prefix, run_id = binding.get("project_id"), binding.get("bucket"), binding.get("prefix"), binding.get("run_id")
    _require(isinstance(project, str) and _PROJECT_RE.fullmatch(project) is not None, "reviewed project binding is missing or invalid")
    _require(isinstance(bucket, str) and _BUCKET_RE.fullmatch(bucket) is not None, "reviewed bucket binding is missing or invalid")
    _require(isinstance(prefix, str) and prefix and not prefix.startswith("/") and not prefix.endswith("/") and "\\" not in prefix and all(part not in {"", ".", ".."} for part in prefix.split("/")), "reviewed prefix is missing or unsafe")
    _require(isinstance(run_id, str) and _RUN_RE.fullmatch(run_id) is not None, "approved run ID is missing or invalid")
    _require(binding.get("namespace_formula") == _NAMESPACE_FORMULA, "reviewed namespace formula drift")
    _require(binding.get("visibility") == {"default": "private", "private_truth_object": "private", "worker_public_output": False}, "bucket visibility binding drift")
    _require(binding.get("credential_binding") == "injected_reviewed_execution_path_only", "credential binding drift")
    _require(binding.get("artifact_index_digest") == index_digest and binding.get("unsigned_lock_digest") == request["unsigned_lock_digest"], "destination commitment drift")
    _require(binding.get("dependency_ledger_head_digest") == dependency["ledger_head_digest"], "R18R12 destination dependency drift")
    _require(binding.get("artifact_digest") == _digest_without(binding, "artifact_digest"), "destination binding digest drift")
    return {"project_id": project, "bucket": bucket, "prefix": prefix, "run_id": run_id, "namespace_formula": _NAMESPACE_FORMULA}


def _object_commitments(records: Sequence[Mapping[str, Any]], approval_objects: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    _require(len(approval_objects) == len(records), "approved object list count drift")
    result: list[dict[str, Any]] = []
    for record, approved in zip(records, approval_objects):
        _require(set(approved) == {"object_id", "object_suffix", "private", "artifact_digest", "file_digest", "expected_generation"}, "approved object commitment is not closed")
        _require(approved["object_id"] == record["object_id"] and approved["object_suffix"] == record["object_suffix"] and approved["private"] == record["private"] and approved["artifact_digest"] == record["artifact_digest"] and approved["file_digest"] == record["file_digest"], f"approved object drift: {record['object_id']}")
        generation = approved["expected_generation"]
        _require(type(generation) is int and generation >= 0, f"generation precondition is missing or ambiguous: {record['object_id']}")
        _safe_relative_suffix(approved["object_suffix"])
        result.append(dict(approved))
    return result


def _validate_approval(approval: Mapping[str, Any], *, plan_digest: str, dependency: Mapping[str, str], binding: Mapping[str, Any], index: Mapping[str, Any], object_commitments: Sequence[Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    expected = {"schema", "acceptance_contract", "approval_id", "dispatch_id", "status", "operation_id", "operation_order", "scope", "attempt_id", "plan_digest", "r18r12_ledger_head_digest", "r18r12_verified_event_digest", "r18r12_approval_digest", "r18r10_ledger_head_digest", "r18r10_verified_event_digest", "r18r10_poststate_digest", "artifact_index_digest", "object_set_digest", "unsigned_lock_digest", "destination", "objects", "allowed_actions", "forbidden_actions", "later_operations", "cloud_operations", "signature_present", "production_promotable", "master_approved", "user_approved", "approved", "enabled", "artifact_digest"}
    _require(set(approval) == expected, "R18R13 approval artifact is not closed")
    _require(approval.get("schema") == APPROVAL_SCHEMA and approval.get("acceptance_contract") == ACCEPTANCE_CONTRACT and approval.get("approval_id") == APPROVAL_ID and approval.get("dispatch_id") == DISPATCH_ID, "R18R13 approval identity drift")
    _require(approval.get("status") == "approved_single_operation_pending_reviewed_execution" and approval.get("operation_id") == OPERATION_ID and approval.get("operation_order") == OPERATION_ORDER and approval.get("scope") == [OPERATION_ID], "R18R13 approval scope drift")
    _require(isinstance(approval.get("attempt_id"), str) and _ATTEMPT_RE.fullmatch(approval["attempt_id"]) is not None, "R18R13 attempt identity is invalid")
    _require(approval["attempt_id"] not in _RESERVED_ATTEMPT_IDS, "R18R13 attempt identity is unresolved")
    _require(approval.get("plan_digest") == plan_digest, "R18R13 plan digest binding drift")
    for name in ("r18r12_ledger_head_digest", "r18r12_verified_event_digest", "r18r12_approval_digest", "r18r10_ledger_head_digest", "r18r10_verified_event_digest", "r18r10_poststate_digest", "artifact_index_digest", "object_set_digest", "unsigned_lock_digest"):
        _is_digest(approval.get(name), f"approval.{name}")
    _require(approval["r18r12_ledger_head_digest"] == dependency["ledger_head_digest"] and approval["r18r12_verified_event_digest"] == dependency["verified_event_digest"] and approval["r18r12_approval_digest"] == dependency["approval_digest"], "R18R12 approval dependency drift")
    _require(approval["r18r10_ledger_head_digest"] == dependency["r18r10_ledger_head_digest"] and approval["r18r10_verified_event_digest"] == dependency["r18r10_verified_event_digest"] and approval["r18r10_poststate_digest"] == dependency["poststate_digest"], "R18R10 approval dependency drift")
    _require(approval["artifact_index_digest"] == index["index_digest"] and approval["unsigned_lock_digest"] == request["unsigned_lock_digest"], "R18R13 input commitment drift")
    _require(approval.get("destination") == binding, "R18R13 bucket/project binding drift")
    expected_objects = list(object_commitments)
    _require(approval.get("objects") == expected_objects, "R18R13 approved object list drift")
    _require(approval.get("object_set_digest") == _digest(expected_objects), "R18R13 object-set digest drift")
    _require(approval.get("allowed_actions") == ["gcs.create_only_or_exact_generation_match"] and approval.get("forbidden_actions") == ["gcs.list", "gcs.delete", "gcs.overwrite", "credential_generation"], "R18R13 action boundary drift")
    _require(approval.get("later_operations") == [{"id": item, "enabled": False} for item in LATER_OPERATION_IDS], "R18R13 downstream enablement drift")
    _require(approval.get("cloud_operations") == ["gcs.create_only_or_exact_generation_match"] and approval.get("signature_present") is False and approval.get("production_promotable") is False, "R18R13 execution boundary drift")
    flags = (approval.get("master_approved"), approval.get("user_approved"), approval.get("approved"), approval.get("enabled"))
    _require(all(type(flag) is bool for flag in flags) and all(flags), "R18R13 approval is not enabled for exactly one operation")
    _require(approval.get("artifact_digest") == _digest_without(approval, "artifact_digest"), "R18R13 approval digest drift")
    return {"approval_digest": approval["artifact_digest"], "attempt_id": approval["attempt_id"]}


def _ledger_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    previous: str | None = None
    for line_number, raw in enumerate(path.read_bytes().splitlines(), start=1):
        try:
            record = parse_canonical(raw)
        except Exception as exc:
            raise RS069R18R13Blocked(f"R18R13 ledger is malformed at line {line_number}") from exc
        _require(record.get("previous_event_digest") == previous, "R18R13 ledger chain drift")
        _require(record.get("event_digest") == _digest_without(record, "event_digest"), "R18R13 ledger event digest drift")
        records.append(record)
        previous = record["event_digest"]
    return records


def _append_event(path: Path, body: Mapping[str, Any], previous: str | None) -> dict[str, Any]:
    event = dict(body)
    event["previous_event_digest"] = previous
    event["event_digest"] = _digest_without(event, "event_digest")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(canonical_bytes(event) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return event


def _missing(error: Exception) -> bool:
    return isinstance(error, StoreError) and str(error) == "object not found"


def _object_name(destination: Mapping[str, str], suffix: str) -> str:
    return f"{destination['prefix']}/{destination['run_id']}/{suffix}"


def _preflight_store(store: ObjectStore, destination: Mapping[str, str], records: Sequence[Mapping[str, Any]], objects: Sequence[Mapping[str, Any]], root: Path) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for record, commitment in zip(records, objects):
        suffix = _safe_relative_suffix(record["object_suffix"])
        local = _resolve(root, record["local_artifact_path"], f"artifact {record['object_id']}")
        data = local.read_bytes()
        name = _object_name(destination, suffix)
        expected_generation = commitment["expected_generation"]
        try:
            existing = store.get(name)
        except Exception as exc:
            if not _missing(exc):
                raise RS069R18R13Blocked(f"remote read failed for {record['object_id']}") from exc
            _require(expected_generation == 0, f"generation precondition requires an existing object: {record['object_id']}")
            outcomes.append({"object_id": record["object_id"], "object_name": name, "expected_generation": 0, "state": "absent", "data": data, "artifact_digest": record["artifact_digest"], "file_digest": record["file_digest"]})
            continue
        _require(expected_generation > 0, f"generation drift: object was expected absent: {record['object_id']}")
        _require(existing.generation == expected_generation, f"generation drift: {record['object_id']}")
        _require(existing.data == data, f"object digest drift: {record['object_id']}")
        outcomes.append({"object_id": record["object_id"], "object_name": name, "expected_generation": expected_generation, "state": "exact_match", "generation": existing.generation, "data": data, "artifact_digest": record["artifact_digest"], "file_digest": record["file_digest"]})
    return outcomes


def validate_operation_4_packet(*, contract: Mapping[str, Any], plan: Mapping[str, Any], request: Mapping[str, Any], binding: Mapping[str, Any], approval: Mapping[str, Any], r18r12_ledger_path: Path = DEFAULT_R18R12_LEDGER, r18r12_approval_path: Path = DEFAULT_R18R12_APPROVAL, artifact_index_path: Path = DEFAULT_ARTIFACT_INDEX, repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    """Validate all local inputs without touching an object store or ledger."""
    root = Path(repository_root).resolve()
    _validate_contract(contract)
    plan_digest, records = _validate_plan(plan, root)
    request_info = _validate_request(Path(DEFAULT_REQUEST), root)
    _require(request == request_info, "caller-supplied unsigned request is not the canonical request")
    r18r10 = _load_r18r10_dependency(DEFAULT_R18R12_LEDGER.parent / "operation-2-r18r10-ledger.jsonl")
    r18r10_info = {"ledger_head_digest": r18r10["ledger_head_digest"], "verified_event_digest": r18r10["verified_event_digest"], "poststate_digest": r18r10["poststate_digest"]}
    r18r12_info = _validate_r18r12(Path(r18r12_ledger_path), Path(r18r12_approval_path), r18r10_info)
    index, index_digest = _validate_index(Path(artifact_index_path), root, records)
    destination = _validate_destination(binding, index_digest=index_digest, request=request_info, dependency={**r18r12_info, **{f"r18r10_{key}": value for key, value in r18r10_info.items()}})
    object_commitments = _object_commitments(records, approval.get("objects", []))
    approval_info = _validate_approval(approval, plan_digest=plan_digest, dependency={**r18r12_info, "r18r10_ledger_head_digest": r18r10_info["ledger_head_digest"], "r18r10_verified_event_digest": r18r10_info["verified_event_digest"]}, binding=binding, index=index, object_commitments=object_commitments, request=request_info)
    return {"plan_digest": plan_digest, "request_digest": request_info["request_digest"], "unsigned_lock_digest": request_info["unsigned_lock_digest"], "r18r10": r18r10_info, "r18r12": r18r12_info, "index_digest": index_digest, "records": records, "destination": destination, "objects": object_commitments, "approval": approval_info, "later_operations_enabled": False, "cloud_operations": ["gcs.create_only_or_exact_generation_match"]}


def execute_operation_4(*, contract_path: Path = DEFAULT_CONTRACT, plan_path: Path = DEFAULT_PLAN, binding_path: Path = DEFAULT_BINDING, approval_path: Path = DEFAULT_APPROVAL, r18r12_ledger_path: Path = DEFAULT_R18R12_LEDGER, r18r12_approval_path: Path = DEFAULT_R18R12_APPROVAL, artifact_index_path: Path = DEFAULT_ARTIFACT_INDEX, ledger_path: Path = DEFAULT_LEDGER, repository_root: Path = REPOSITORY_ROOT, store: ObjectStore | None = None) -> dict[str, Any]:
    """Execute the one reviewed operation through an injected store only.

    There is intentionally no caller-supplied approval/apply/mutate boolean.
    The checked-in approval artifact and the explicit store injection are the
    only execution gates; a missing store is treated as missing credentials.
    """
    root = Path(repository_root).resolve()
    _require(Path.cwd().resolve() == root, "R18R13 runner must be invoked from repository root")
    _require(store is not None, "reviewed execution path credentials are required")
    _require(Path(ledger_path).name == DEFAULT_LEDGER.name and Path(ledger_path).resolve() != DEFAULT_R18R12_LEDGER.resolve(), "R18R13 ledger path is not the dedicated append-only ledger")
    _require(not _ledger_records(Path(ledger_path)), "R18R13 already has an attempt; retry is disabled")
    contract = _load_canonical(Path(contract_path), "R18R13 contract")
    plan = load_plan(Path(plan_path))
    request = _load_canonical(DEFAULT_REQUEST, "unsigned request")
    binding = _load_canonical(Path(binding_path), "R18R13 destination binding")
    approval = _load_canonical(Path(approval_path), "R18R13 approval")
    checked = validate_operation_4_packet(contract=contract, plan=plan, request=request, binding=binding, approval=approval, r18r12_ledger_path=Path(r18r12_ledger_path), r18r12_approval_path=Path(r18r12_approval_path), artifact_index_path=Path(artifact_index_path), repository_root=root)
    outcomes = _preflight_store(store, checked["destination"], checked["records"], checked["objects"], root)
    common = {"schema": LEDGER_SCHEMA, "acceptance_contract": ACCEPTANCE_CONTRACT, "operation_id": OPERATION_ID, "operation_order": OPERATION_ORDER, "scope": [OPERATION_ID], "attempt_id": checked["approval"]["attempt_id"], "plan_digest": checked["plan_digest"], "approval_digest": checked["approval"]["approval_digest"], "artifact_index_digest": checked["index_digest"], "r18r12_ledger_head_digest": checked["r18r12"]["ledger_head_digest"], "r18r10_ledger_head_digest": checked["r18r10"]["ledger_head_digest"], "later_operations_enabled": False, "cloud_operations": ["gcs.create_only_or_exact_generation_match"], "signature_present": False, "production_promotable": False}
    ledger = Path(ledger_path)
    previous: str | None = None
    started = _append_event(ledger, {**common, "kind": "run_started", "object_count": len(outcomes), "mutations_performed": False}, previous)
    previous = started["event_digest"]
    try:
        verified: list[dict[str, Any]] = []
        for outcome in outcomes:
            if outcome["state"] == "absent":
                created = store.create(outcome["object_name"], outcome["data"])
                _require(isinstance(created, Object) and created.data == outcome["data"] and created.generation > 0, f"created object verification failed: {outcome['object_id']}")
                verified_object = store.get(outcome["object_name"])
                _require(verified_object.data == outcome["data"] and verified_object.generation == created.generation, f"stored object verification failed: {outcome['object_id']}")
                verified.append({"object_id": outcome["object_id"], "object_name": outcome["object_name"], "state": "created", "generation": created.generation, "artifact_digest": outcome["artifact_digest"], "file_digest": outcome["file_digest"]})
            else:
                verified.append({"object_id": outcome["object_id"], "object_name": outcome["object_name"], "state": "exact_match", "generation": outcome["generation"], "artifact_digest": outcome["artifact_digest"], "file_digest": outcome["file_digest"]})
        objects_event = _append_event(ledger, {**common, "kind": "objects_verified", "objects": verified, "mutations_performed": any(item["state"] == "created" for item in verified)}, previous)
        previous = objects_event["event_digest"]
        stopped = _append_event(ledger, {**common, "kind": "run_stopped", "status": "verified_ingest_generated_bundle_to_gcs", "verified_event_digest": objects_event["event_digest"], "rollback_status": "not_required_verified", "mutations_performed": objects_event["mutations_performed"], "later_operations_skipped": list(LATER_OPERATION_IDS)}, previous)
    except Exception as exc:
        _append_event(ledger, {**common, "kind": "run_stopped", "status": "failed_closed_partial_or_unverified", "rollback_status": "not_authorized", "mutations_performed": True, "later_operations_skipped": list(LATER_OPERATION_IDS), "error_type": type(exc).__name__}, previous)
        if isinstance(exc, RS069R18R13Blocked):
            raise
        raise RS069R18R13Blocked("operation-4 execution failed closed") from exc
    return {"status": stopped["status"], "operation_id": OPERATION_ID, "attempt_id": checked["approval"]["attempt_id"], "ledger_path": str(ledger), "ledger_head_digest": stopped["event_digest"], "object_count": len(outcomes), "cloud_operations": common["cloud_operations"], "mutations_performed": stopped["mutations_performed"], "later_operations_enabled": False}


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the reviewed RS-069R18R13 operation-4 ingestion boundary")
    parser.add_argument("--execute-operation-4", action="store_true")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--binding", type=Path, default=DEFAULT_BINDING)
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args(argv)
    if not args.execute_operation_4:
        parser.error("--execute-operation-4 is required")
    try:
        result = execute_operation_4(contract_path=args.contract, binding_path=args.binding, approval_path=args.approval, ledger_path=args.ledger)
    except RS069R18R13Blocked as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = [
    "ACCEPTANCE_CONTRACT", "APPROVAL_ID", "APPROVAL_SCHEMA", "BINDING_SCHEMA", "CONTRACT_SCHEMA",
    "DEFAULT_APPROVAL", "DEFAULT_ARTIFACT_INDEX", "DEFAULT_BINDING", "DEFAULT_CONTRACT", "DEFAULT_LEDGER",
    "DEFAULT_R18R12_APPROVAL", "DEFAULT_R18R12_LEDGER", "DISPATCH_ID", "LATER_OPERATION_IDS", "OPERATION_ID",
    "RS069R18R13Blocked", "execute_operation_4", "validate_operation_4_packet",
]
