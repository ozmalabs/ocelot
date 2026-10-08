"""Fail-closed RS-069R18R11 operation-3 repository preflight.

This module is the reviewed local boundary for
``bind_self_custodied_authority_and_kms``.  It consumes only canonical,
operation-scoped artifacts and the immutable verified R18R10 ledger.  It
prepares and records a repository-only authority/KMS binding; it never calls
KMS, gcloud, GCS, STS, Confidential Space, a signer, or a deployment tool.
The frozen unsigned lock request is validated but never modified.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.authority_binding import (
    AuthorityBindingValidationError,
    validate_candidate_binding,
)
from services.p5_r0_evaluator.deploy.authority_binding_proposal import (
    REVIEW_AUTHORITY_ID,
    REVIEW_AUDIENCE,
    REVIEW_KEY_ID,
    REVIEW_KMS_KEY_VERSION,
    REVIEW_PROVIDER,
    REVIEW_PUBLIC_KEY_DIGEST,
)
from services.p5_r0_evaluator.deploy.kms_lock_signing import (
    KMSLockSigningValidationError,
    validate_unsigned_request,
)
from services.p5_r0_evaluator.deploy.rs069_change_plan import (
    DEFAULT_PLAN,
    REPOSITORY_ROOT,
    load_plan,
    validate_plan,
)

OPERATION_ID = "bind_self_custodied_authority_and_kms"
OPERATION_ORDER = 3
DEPENDENCY_ID = "correct_wip_provider_claim_mapping"
LATER_OPERATION_IDS = (
    "ingest_generated_bundle_to_gcs",
    "configure_cloud_run_and_confidential_space",
    "prepare_supervisor_and_run_request",
    "cleanup_or_rollback",
)
_R18R10_LATER_OPERATION_IDS = (OPERATION_ID,) + LATER_OPERATION_IDS
DEFAULT_REQUEST = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json"
DEFAULT_BINDING = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs-069r18r11-binding-inputs.json"
DEFAULT_APPROVAL = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs-069r18r11-operation-3-approval.json"
DEFAULT_DEPENDENCY_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-2-r18r10-ledger.jsonl"
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-3-r18r11-ledger.jsonl"
APPROVAL_ID = "P5-MASTER-001/APPROVAL-008-RS069R18R11"
APPROVAL_SCHEMA = "P5R0RS069R18R11ApprovalArtifactV1"
ACCEPTANCE_CONTRACT = "P5R0RS069R18R11Operation3AcceptanceV1"
BINDING_SCHEMA = "P5R0RS069R18R11BindingInputsV1"
LEDGER_SCHEMA = "P5R0RS069R18R11Operation3LedgerEventV1"
_ATTESTATION_DEFERRED = {"status": "deferred", "deferred_to": "RS-080", "asserted": False}
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ATTEMPT_RE = re.compile(r"^rs069r18r11-op3-[a-z0-9][a-z0-9-]{7,63}$")
_EXPECTED_UNSIGNED_LOCK_DIGEST = "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"
_EXPECTED_REQUEST_DIGEST = "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d"
_EXPECTED_R18R10_POSTSTATE = "sha256:9a7fcde1498606c60ab06e83a91eb3ba1712f8da6cdb554ca4cb02f3c2060ff7"
_EXPECTED_R18R10_EVENTS = (
    "sha256:55b0d94b709edf6e0500bb7210b4a03cc3f4de666f937e7db776ff6007fd0572",
    "sha256:16e0232d6761e03ecbfac9c141c0ea19ba9b52b6f5068cbb679cf6cdfaebdd60",
    "sha256:42ed5a997d9fdd87e674fe1b1771115f11662277619b813eba6035c0a8624cac",
    "sha256:7ccf71443129e799837f085de3252a33d6e5fa7d3f4d5d3cca4e754192bbda8d",
)
_HISTORICAL_LEDGER_NAMES = {
    "operation-2-ledger.jsonl",
    "operation-2-r18r8-ledger.jsonl",
    "operation-2-r18r9-ledger.jsonl",
}


class RS069Operation3Blocked(RuntimeError):
    """The one approved operation-3 attempt cannot safely proceed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RS069Operation3Blocked(message)


def _digest(value: Any) -> str:
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None


def _load_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        return parse_canonical(path.read_bytes())
    except Exception as exc:
        raise RS069Operation3Blocked(f"{label} is unavailable or not canonical") from exc


def _artifact_digest(artifact: Mapping[str, Any], field: str = "artifact_digest") -> str:
    supplied = artifact.get(field)
    _require(_is_digest(supplied), f"{field} is missing or unresolved")
    _require(supplied == _digest({key: value for key, value in artifact.items() if key != field}), f"{field} mismatch")
    return supplied


def _reject_forbidden_material(value: Any, label: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            _require(not any(marker in lowered for marker in ("private", "secret", "signature")), f"{label} contains forbidden {key}")
            _reject_forbidden_material(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden_material(item, f"{label}[{index}]")


def _validate_plan_binding(plan: Mapping[str, Any], repository_root: Path) -> str:
    try:
        report = validate_plan(plan, repository_root=repository_root)
    except Exception as exc:
        raise RS069Operation3Blocked("RS-069 plan validation failed") from exc
    _require(tuple(report.operation_ids)[OPERATION_ORDER - 1] == OPERATION_ID, "operation-3 plan ordering drift")
    operation = plan["operations"][OPERATION_ORDER - 1]
    _require(operation["id"] == OPERATION_ID, "operation-3 identity drift")
    _require(operation["order"] == OPERATION_ORDER and operation["depends_on"] == [DEPENDENCY_ID], "operation-3 dependency drift")
    _require(operation["mutation_boundary"] == {"mode": "review_only_no_execution", "apply_interface": "approved signed-environment workflow only", "commands": [], "direct_cloud_mutations": False}, "operation-3 mutation boundary drift")
    _require(all(item["value"] is None for item in operation["exact_required_inputs"]), "operation-3 plan inputs were silently resolved")
    _require(operation["immutable_digests"][:2] == [
        {"name": "unsigned_lock_digest", "value": _EXPECTED_UNSIGNED_LOCK_DIGEST, "source": "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json", "classification": "diagnostic_input"},
        {"name": "lock_request_digest", "value": _EXPECTED_REQUEST_DIGEST, "source": "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json", "classification": "diagnostic_input"},
    ], "operation-3 unsigned-request commitments drift")
    record = next(item for item in plan["operation_records"] if item["operation_id"] == OPERATION_ID)
    _require(record["dependency_ids"] == [DEPENDENCY_ID] and record["enabled"] is False and record["commands"] == [], "operation-3 typed state is enabled or widened")
    _require(record["preconditions"] == {"dependencies_satisfied": False, "inputs_resolved": False, "approval_present": False, "remote_state_verified": False}, "operation-3 precondition state drift")
    _require(record["postconditions"] == {"desired_state_match": False, "rendered": False, "mutation_performed": False}, "operation-3 postcondition state drift")
    return report.plan_digest


def _load_r18r10_dependency(path: Path) -> dict[str, Any]:
    _require(path.resolve() == DEFAULT_DEPENDENCY_LEDGER.resolve(), "R18R10 dependency ledger is not the immutable canonical ledger")
    _require(path.name not in _HISTORICAL_LEDGER_NAMES, "historical ledger is not a dependency authorization")
    try:
        raw_lines = path.read_bytes().splitlines()
    except OSError as exc:
        raise RS069Operation3Blocked("verified R18R10 dependency ledger is unavailable") from exc
    _require(len(raw_lines) == 4, "R18R10 dependency ledger does not contain the verified four-event record")
    records: list[dict[str, Any]] = []
    previous: str | None = None
    for raw in raw_lines:
        record = parse_canonical(raw)
        _require(record.get("previous_event_digest") == previous, "R18R10 dependency chain drift")
        event_digest = record.get("event_digest")
        _require(event_digest == _digest({key: value for key, value in record.items() if key != "event_digest"}), "R18R10 dependency event digest drift")
        records.append(record)
        previous = event_digest
    _require(tuple(record["event_digest"] for record in records) == _EXPECTED_R18R10_EVENTS, "R18R10 dependency evidence is not the reviewed immutable record")
    _require(all(record.get("operation_id") == DEPENDENCY_ID for record in records), "R18R10 dependency operation drift")
    verified = records[2]
    stopped = records[3]
    _require(verified["kind"] == "operation_verified" and verified["operation_order"] == 2, "R18R10 operation was not verified")
    _require(verified["poststate_digest"] == _EXPECTED_R18R10_POSTSTATE and verified["mutations_performed"] is True, "R18R10 poststate verification drift")
    _require(stopped["kind"] == "run_stopped" and stopped["status"] == "verified" and stopped["rollback_status"] == "not_required_verified", "R18R10 terminal state is not verified")
    _require(stopped["verified_event_digest"] == verified["event_digest"], "R18R10 terminal verification binding drift")
    _require(stopped["later_operations_skipped"] == list(_R18R10_LATER_OPERATION_IDS), "R18R10 downstream boundary drift")
    return {"ledger_head_digest": stopped["event_digest"], "verified_event_digest": verified["event_digest"], "poststate_digest": verified["poststate_digest"]}


def _validate_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    _require(set(binding) == {"schema", "classification", "authority", "kms", "environment", "artifact_digest"}, "R18R11 binding artifact is not closed")
    _require(binding["schema"] == BINDING_SCHEMA and binding["classification"] == "diagnostic_unsigned_non_release", "R18R11 binding artifact identity drift")
    _artifact_digest(binding)
    _reject_forbidden_material(binding, "binding")
    authority = binding["authority"]
    kms = binding["kms"]
    environment = binding["environment"]
    try:
        validate_candidate_binding(authority, kms, environment)
    except (AuthorityBindingValidationError, TypeError) as exc:
        raise RS069Operation3Blocked("R18R11 authority/KMS binding validation failed") from exc
    _require(authority["authority_id"] == REVIEW_AUTHORITY_ID and authority["key_id"] == REVIEW_KEY_ID, "reviewed authority/KMS commitments drift")
    _require(authority["public_key_digest"] == REVIEW_PUBLIC_KEY_DIGEST and kms["public_key_digest"] == REVIEW_PUBLIC_KEY_DIGEST, "reviewed authority/KMS commitments drift")
    _require(kms["key_version"] == REVIEW_KMS_KEY_VERSION, "reviewed authority/KMS commitments drift")
    transport = authority["transport_attestation"]
    _require(transport == {
        "schema": "P5R0AuthorityTransportV1",
        "provider": REVIEW_PROVIDER,
        "audience": REVIEW_AUDIENCE,
        "event": "confidential_space_attestation",
    }, "R18R11 transport binding drift")
    claims = environment["claims"]
    _require(claims["project_id"] == "ocelot-proof" and claims["project_number"] == "141633828616", "R18R11 project binding drift")
    _require(kms["key_version"].startswith("projects/ocelot-proof/"), "R18R11 KMS project binding drift")
    return {
        "artifact_digest": binding["artifact_digest"],
        "authority_id": authority["authority_id"],
        "key_id": authority["key_id"],
        "kms_key_version_digest": _digest(kms["key_version"]),
        "public_key_digest": kms["public_key_digest"],
        "transport_digest": _digest(transport),
        "authority_binding_digest": kms["authority_binding"]["binding_digest"],
    }


def _validate_approval(approval: Mapping[str, Any], *, plan_digest: str, dependency: Mapping[str, Any], binding: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    expected_fields = {
        "schema", "acceptance_contract", "approval_id", "status", "operation_id", "operation_order", "scope", "attempt_id",
        "plan_digest", "dependency_ledger_head_digest", "binding_artifact_digest", "authority_binding_digest",
        "request_digest", "unsigned_lock_digest", "attestation", "later_operations", "master_approved", "user_approved", "approved", "enabled", "artifact_digest",
    }
    _require(set(approval) == expected_fields, "R18R11 approval artifact is not closed")
    _require(approval["schema"] == APPROVAL_SCHEMA and approval["acceptance_contract"] == ACCEPTANCE_CONTRACT, "R18R11 approval identity drift")
    _require(approval["approval_id"] == APPROVAL_ID and approval["status"] == "approved_single_operation_pending_apply", "R18R11 approval is not the separately reviewed approval")
    _require(approval["operation_id"] == OPERATION_ID and approval["operation_order"] == OPERATION_ORDER and approval["scope"] == [OPERATION_ID], "R18R11 approval scope drift")
    _require(isinstance(approval["attempt_id"], str) and _ATTEMPT_RE.fullmatch(approval["attempt_id"]) is not None, "R18R11 attempt identity is invalid")
    _require(approval["plan_digest"] == plan_digest, "R18R11 plan digest binding drift")
    _require(approval["dependency_ledger_head_digest"] == dependency["ledger_head_digest"], "R18R10 dependency head binding drift")
    _require(approval["binding_artifact_digest"] == binding["artifact_digest"] and approval["authority_binding_digest"] == binding["authority_binding_digest"], "R18R11 binding digest drift")
    _require(approval["request_digest"] == request["request_digest"] == _EXPECTED_REQUEST_DIGEST and approval["unsigned_lock_digest"] == request["unsigned_lock_digest"] == _EXPECTED_UNSIGNED_LOCK_DIGEST, "unsigned request digest binding drift")
    _require(approval["attestation"] == _ATTESTATION_DEFERRED, "R18R11 must not fabricate attestation")
    _require(approval["later_operations"] == [{"id": item, "enabled": False} for item in LATER_OPERATION_IDS], "downstream operation enablement drift")
    flags = (approval["master_approved"], approval["user_approved"], approval["approved"], approval["enabled"])
    _require(all(type(flag) is bool for flag in flags) and all(flags), "R18R11 approval is not enabled for exactly one operation")
    approval_digest = _artifact_digest(approval)
    return {"approval_id": approval["approval_id"], "approval_digest": approval_digest, "attempt_id": approval["attempt_id"]}


def validate_operation_3_bindings(*, plan: Mapping[str, Any], request: Mapping[str, Any], binding: Mapping[str, Any], approval: Mapping[str, Any], dependency: Mapping[str, Any], repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    """Validate already-loaded review artifacts without performing an effect."""
    root = Path(repository_root).resolve()
    plan_digest = _validate_plan_binding(plan, root)
    try:
        request_report = validate_unsigned_request(request)
    except (KMSLockSigningValidationError, TypeError, KeyError) as exc:
        raise RS069Operation3Blocked("exact unsigned lock request validation failed") from exc
    _require(request_report.request_digest == _EXPECTED_REQUEST_DIGEST and request_report.unsigned_lock_digest == _EXPECTED_UNSIGNED_LOCK_DIGEST, "unsigned request commitments drift")
    dependency_info = dict(dependency)
    _require(dependency_info == {"ledger_head_digest": dependency_info.get("ledger_head_digest"), "verified_event_digest": dependency_info.get("verified_event_digest"), "poststate_digest": dependency_info.get("poststate_digest")}, "dependency record is not closed")
    for field in dependency_info:
        _require(_is_digest(dependency_info[field]), f"dependency {field} is unresolved")
    binding_info = _validate_binding(binding)
    approval_info = _validate_approval(approval, plan_digest=plan_digest, dependency=dependency_info, binding=binding_info, request=request)
    return {
        "plan_digest": plan_digest,
        "request_digest": request_report.request_digest,
        "unsigned_lock_digest": request_report.unsigned_lock_digest,
        "dependency": dependency_info,
        "binding": binding_info,
        "approval": approval_info,
        "later_operations_enabled": False,
        "cloud_operations": [],
        "signature_present": False,
        "production_promotable": False,
    }


def _ledger_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    previous: str | None = None
    for line_number, raw in enumerate(path.read_bytes().splitlines(), start=1):
        try:
            record = parse_canonical(raw)
        except Exception as exc:
            raise RS069Operation3Blocked(f"R18R11 ledger is malformed at line {line_number}") from exc
        _require(record.get("previous_event_digest") == previous, "R18R11 ledger chain drift")
        _require(record.get("event_digest") == _digest({key: value for key, value in record.items() if key != "event_digest"}), "R18R11 ledger digest drift")
        records.append(record)
        previous = record["event_digest"]
    return records


def _append_event(path: Path, record: Mapping[str, Any], previous: str | None) -> dict[str, Any]:
    body = dict(record)
    body["previous_event_digest"] = previous
    body["event_digest"] = _digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(canonical_bytes(body) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return body


def execute_operation_3(*, repository_root: Path = REPOSITORY_ROOT, plan_path: Path = DEFAULT_PLAN, request_path: Path = DEFAULT_REQUEST, binding_path: Path = DEFAULT_BINDING, approval_path: Path = DEFAULT_APPROVAL, dependency_ledger_path: Path = DEFAULT_DEPENDENCY_LEDGER, ledger_path: Path = DEFAULT_LEDGER, apply_enabled: bool = False, plan: Mapping[str, Any] | None = None, request: Mapping[str, Any] | None = None, binding: Mapping[str, Any] | None = None, approval: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run exactly one local R18R11 gate; no cloud or signer boundary exists."""
    _require(apply_enabled is True, "operation-3 execution requires explicit --execute-operation-3")
    _require(all(value is None for value in (plan, request, binding, approval)), "caller mappings are not authentication artifacts")
    root = Path(repository_root).resolve()
    _require(Path.cwd().resolve() == root, "R18R11 runner must be invoked from repository root")
    try:
        loaded_plan = load_plan(Path(plan_path))
    except Exception as exc:
        raise RS069Operation3Blocked("RS-069 plan is unavailable or malformed") from exc
    loaded_request = _load_canonical(Path(request_path), "unsigned lock request")
    loaded_binding = _load_canonical(Path(binding_path), "R18R11 binding artifact")
    loaded_approval = _load_canonical(Path(approval_path), "R18R11 approval artifact")
    dependency = _load_r18r10_dependency(Path(dependency_ledger_path))
    checked = validate_operation_3_bindings(plan=loaded_plan, request=loaded_request, binding=loaded_binding, approval=loaded_approval, dependency=dependency, repository_root=root)
    ledger = Path(ledger_path).resolve()
    _require(ledger.name == DEFAULT_LEDGER.name and ledger not in {root / name for name in _HISTORICAL_LEDGER_NAMES}, "R18R11 ledger path is not distinct from historical ledgers")
    records = _ledger_records(ledger)
    _require(not records, "R18R11 already has an attempt; retry is disabled")
    attempt = checked["approval"]["attempt_id"]
    previous: str | None = None
    common = {"schema": LEDGER_SCHEMA, "acceptance_contract": ACCEPTANCE_CONTRACT, "operation_id": OPERATION_ID, "operation_order": OPERATION_ORDER, "scope": [OPERATION_ID], "later_operations_enabled": False, "cloud_operations": [], "mutations_performed": False, "signature_present": False, "production_promotable": False, "attempt_id": attempt}
    started = _append_event(ledger, {**common, "kind": "run_started", "plan_digest": checked["plan_digest"], "approval_digest": checked["approval"]["approval_digest"], "request_digest": checked["request_digest"], "unsigned_lock_digest": checked["unsigned_lock_digest"]}, previous)
    previous = started["event_digest"]
    dependency_event = _append_event(ledger, {**common, "kind": "dependency_verified", "dependency_ledger_head_digest": checked["dependency"]["ledger_head_digest"], "dependency_verified_event_digest": checked["dependency"]["verified_event_digest"], "dependency_poststate_digest": checked["dependency"]["poststate_digest"]}, previous)
    previous = dependency_event["event_digest"]
    binding_event = _append_event(ledger, {**common, "kind": "binding_verified", "binding_artifact_digest": checked["binding"]["artifact_digest"], "authority_binding_digest": checked["binding"]["authority_binding_digest"], "public_key_digest": checked["binding"]["public_key_digest"], "transport_digest": checked["binding"]["transport_digest"], "kms_key_version_digest": checked["binding"]["kms_key_version_digest"]}, previous)
    previous = binding_event["event_digest"]
    stopped = _append_event(ledger, {**common, "kind": "run_stopped", "status": "verified_repository_binding_review_only", "verified_event_digest": binding_event["event_digest"], "rollback_status": "not_required_no_mutation", "later_operations_skipped": list(LATER_OPERATION_IDS), "attestation": _ATTESTATION_DEFERRED}, previous)
    return {"status": stopped["status"], "operation_id": OPERATION_ID, "attempt_id": attempt, "ledger_path": str(ledger), "ledger_head_digest": stopped["event_digest"], "cloud_operations": [], "mutations_performed": False, "signature_present": False, "production_promotable": False, "later_operations_enabled": False}


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local-only reviewed RS-069R18R11 operation-3 gate")
    parser.add_argument("--execute-operation-3", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--binding", type=Path, default=DEFAULT_BINDING)
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    parser.add_argument("--dependency-ledger", type=Path, default=DEFAULT_DEPENDENCY_LEDGER)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args(argv)
    try:
        result = execute_operation_3(repository_root=REPOSITORY_ROOT, plan_path=args.plan, request_path=args.request, binding_path=args.binding, approval_path=args.approval, dependency_ledger_path=args.dependency_ledger, ledger_path=args.ledger, apply_enabled=args.execute_operation_3)
    except RS069Operation3Blocked as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = [
    "ACCEPTANCE_CONTRACT", "APPROVAL_ID", "APPROVAL_SCHEMA", "DEFAULT_APPROVAL", "DEFAULT_BINDING", "DEFAULT_DEPENDENCY_LEDGER", "DEFAULT_LEDGER", "DEFAULT_REQUEST", "LATER_OPERATION_IDS", "OPERATION_ID", "OPERATION_ORDER", "RS069Operation3Blocked", "execute_operation_3", "validate_operation_3_bindings",
]
