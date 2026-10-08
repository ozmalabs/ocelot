"""Validate the versioned, read-only RS-069R18R13-IAM preparation packet.

This module is preparation-only.  It never calls cloud APIs, obtains
credentials, invokes gcloud, mutates IAM/GCS, creates accounts/roles/keys, or
claims an applied state.  It supersedes the rigid DISPATCH-050/APPROVAL-050
identity for local prestate and child-approval validation while preserving the
DISPATCH-050 definition and its exact operation boundary.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEFINITION = Path(__file__).with_name("rs069r18r13-iam-provisioning-definition-v1.json")
DEFAULT_PACKET = Path(__file__).with_name("rs069r18r13-gcs-boundary-packet-v1.json")
DEFAULT_CAPABILITY = Path(__file__).with_name("gcs-capability-definition.json")
DEFAULT_AUTHORITY = Path(__file__).with_name("rs-069r18r12-binding-review.json")
DEFAULT_R18R12_APPROVAL = Path(__file__).with_name("rs-069r18r12-operation-3-approval.json")
DEFAULT_R18R12_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-3-r18r12-ledger.jsonl"
DEFAULT_R18R10_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-2-r18r10-ledger.jsonl"
DEFAULT_PRESTATE = REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json"
DEFAULT_CREDENTIAL = REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-credential-binding-evidence-v1.json"
DEFAULT_APPROVAL = Path(__file__).with_name("rs-069r18r13-iam-approval-v2.json")

OPERATION_ID = "provision_gcs_only_iam_boundary"
APPROVAL_ID = "P5-MASTER-001/APPROVAL-012-RS069R18R13-IAM"
MASTER_APPROVAL_ID = "P5-MASTER-001/APPROVAL-012"
PARENT_APPROVAL_ID = "P5-MASTER-001/APPROVAL-011"
ATTEMPT_RE = re.compile(r"^dispatch050-iam-r18r13-[a-z0-9][a-z0-9-]{7,63}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
DEFINITION_DIGEST = "sha256:817ce6cff5f25487ba131a2d587fbcd489a52245e3a8173aa6320862ed49ce25"
PACKET_DIGEST = "sha256:a8c313f6e5b775b4ba48a8e8ff4cc5e2561c560930c4e89ec2e9666fb509c447"
CAPABILITY_DIGEST = "sha256:705c5323a8bf8f300547d2051cf128825b03e0415c334dd452cd4e9db0280ee2"
AUTHORITY_DIGEST = "sha256:c8e186d51eb0dcce6d3b2db4939f0e62af69ee88fc5ada19c4ad8c878245fd61"
AUTHORITY_BINDING_DIGEST = "sha256:9837a8f8e5f214a474f685e259f0acb1d6b6fff4b02d9ebbc3919fbf1e7c13e6"
R18R12_APPROVAL_DIGEST = "sha256:cfa0b7cc40f288282fdb432538460fc65cc4b0c8d3d247c73786fd4fa5cc9dd0"
R18R12_LEDGER_HEAD = "sha256:30a59807d8dbf7aa2529d4efab406b4dcd5e87597442be71045827c816833329"
R18R12_VERIFIED = "sha256:bbb534870778e46c38c6e0fc03dbc36f47f5f78c6127b12ef2e8557877f0a727"
R18R10_LEDGER_HEAD = "sha256:7ccf71443129e799837f085de3252a33d6e5fa7d3f4d5d3cca4e754192bbda8d"
R18R10_VERIFIED = "sha256:42ed5a997d9fdd87e674fe1b1771115f11662277619b813eba6035c0a8624cac"
R18R10_POSTSTATE = "sha256:9a7fcde1498606c60ab06e83a91eb3ba1712f8da6cdb554ca4cb02f3c2060ff7"


class IAMPreparationError(ValueError):
    """The local preparation packet is malformed or not admissible."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IAMPreparationError(message)


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return sha256({key: item for key, item in value.items() if key != field})


def _is_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None, f"{label} is not a digest")


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise IAMPreparationError(f"{label} is unavailable or invalid JSON") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _load_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical(path.read_bytes())
    except Exception as exc:
        raise IAMPreparationError(f"{label} is unavailable or not canonical") from exc
    return value


def _load_self_digested_json(path: Path, label: str, field: str) -> dict[str, Any]:
    value = _load_json(path, label)
    supplied = value.get(field)
    _is_digest(supplied, f"{label}.{field}")
    _require(supplied == _digest_without(value, field), f"{label} digest mismatch")
    return value


def _load_self_digested_canonical(path: Path, label: str, field: str) -> dict[str, Any]:
    value = _load_canonical(path, label)
    supplied = value.get(field)
    _is_digest(supplied, f"{label}.{field}")
    _require(supplied == _digest_without(value, field), f"{label} digest mismatch")
    return value


def _versioned_policy(value: Any, label: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} is malformed")
    fields = [field for field in ("etag", "fingerprint") if field in value and value[field] is not None]
    _require(len(fields) == 1 and isinstance(value[fields[0]], str) and value[fields[0]], f"{label} must have exactly one non-empty etag or fingerprint")
    _require(isinstance(value.get("bindings"), list), f"{label} bindings are malformed")
    return dict(value)


def _validate_state(state: Mapping[str, Any]) -> None:
    _require(state.get("schema") == "P5R0RS069R18R13IAMStateV2", "IAM prestate schema drift")
    _require(state.get("project") == {"project_id": "ocelot-proof", "project_number": "141633828616", "lifecycle_state": "ACTIVE"}, "project observation drift")
    _versioned_policy(state.get("project_policy"), "project IAM policy")
    _require(state.get("bucket", {}).get("name") == "p5-evaluator-ocelot-proof-141633828616", "bucket identity drift")
    _versioned_policy(state.get("bucket_policy"), "bucket IAM policy")
    existing = state.get("existing_account")
    _require(existing == {"email":"p5-evaluator@ocelot-proof.iam.gserviceaccount.com","exists":True,"unique_id":"107880936272403811527","user_managed_key_count":0,"key_material_status":"no_user_managed_keys_observed","project_roles":["roles/cloudkms.signerVerifier"]}, "existing service-account state drift")
    _versioned_policy(state.get("existing_account_policy"), "existing service-account IAM policy")
    target = state.get("target_account")
    _require(target == {"email":"p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com","exists":False,"unique_id":None,"user_managed_key_count":None,"key_material_status":"not_applicable_absent","project_roles":[]}, "target service-account state drift")
    _require(state.get("target_account_policy") is None, "absent target account has a policy")
    role = state.get("custom_role")
    _require(role == {"name":"projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1","exists":False,"etag":None,"fingerprint":None,"title":None,"stage":None,"permissions":[]}, "custom-role state drift")
    _is_digest(state.get("state_digest"), "prestate state_digest")
    _require(state["state_digest"] == _digest_without(state, "state_digest"), "prestate state digest mismatch")


def _validate_prestate(path: Path) -> dict[str, Any]:
    value = _load_self_digested_canonical(path, "IAM prestate artifact", "artifact_digest")
    _require(value.get("schema") == "P5R0RS069R18R13IAMPrestateArtifactV2", "IAM prestate artifact schema drift")
    capture = value.get("capture")
    _require(isinstance(capture, Mapping) and capture.get("fresh") is True and capture.get("read_only") is True and capture.get("cloud_operations") == [] and capture.get("mutations_performed") is False and capture.get("applied_state") is False, "prestate capture crosses the apply boundary")
    _require(isinstance(capture.get("capture_id"), str) and capture["capture_id"], "prestate capture identity missing")
    _validate_state(value["state"])
    return value


def _validate_credential(path: Path) -> dict[str, Any]:
    value = _load_self_digested_canonical(path, "credential evidence", "artifact_digest")
    _require(value.get("schema") == "P5R0RS069R18R13CredentialBindingEvidenceV1", "credential evidence schema drift")
    _require(value.get("operation_id") == OPERATION_ID and value.get("signed_environment_status") == "required_but_not_injected", "credential evidence status drift")
    _require(value.get("credential_created") is False and value.get("credential_exported") is False and value.get("credential_injected") is False and value.get("cloud_operations") == [], "credential evidence crosses the apply boundary")
    _require(value.get("evidence", {}).get("signed_environment_evidence_digest") is None and value["evidence"].get("token_present") is False, "credential evidence falsely asserts readiness")
    _require(value.get("source_definition_digest") == DEFINITION_DIGEST and value.get("packet_digest") == PACKET_DIGEST and value.get("capability_definition_digest") == CAPABILITY_DIGEST, "credential source digest drift")
    return value


def _validate_source_files(definition_path: Path, packet_path: Path, capability_path: Path) -> None:
    definition = _load_self_digested_json(definition_path, "IAM definition", "definition_digest")
    _require(definition["definition_digest"] == DEFINITION_DIGEST, "IAM definition digest drift")
    _require(definition["operation"]["id"] == OPERATION_ID and definition["operation"]["scope"] == [OPERATION_ID] and definition["operation"]["later_operations_enabled"] is False and definition["operation"]["mutations_performed"] is False, "IAM operation scope drift")
    _require(definition["execution_boundary"]["apply_performed"] is False and definition["execution_boundary"]["cloud_operations"] == [] and definition["execution_boundary"]["credentials_created"] is False, "IAM definition apply boundary drift")
    packet = _load_self_digested_json(packet_path, "GCS boundary packet", "packet_digest")
    _require(packet["packet_digest"] == PACKET_DIGEST and packet["operation"]["later_operations_enabled"] is False and packet["operation"]["mutations_performed"] is False, "GCS packet boundary drift")
    capability = _load_self_digested_json(capability_path, "GCS capability definition", "definition_digest")
    _require(capability["definition_digest"] == CAPABILITY_DIGEST and capability["status"] == "blocked_pending_reviewed_iam_and_confidential_space_credential" and capability["iam"]["state"] == "desired_not_applied", "GCS capability boundary drift")


def _validate_dependency_ledger(path: Path) -> dict[str, str]:
    lines = path.read_bytes().splitlines()
    _require(len(lines) == 4, "R18R12 ledger event count drift")
    previous = None
    records = []
    for raw in lines:
        record = parse_canonical(raw)
        _require(record.get("previous_event_digest") == previous, "R18R12 ledger chain drift")
        _require(record.get("event_digest") == _digest_without(record, "event_digest"), "R18R12 event digest drift")
        records.append(record)
        previous = record["event_digest"]
    _require(records[-1]["event_digest"] == R18R12_LEDGER_HEAD and records[2]["event_digest"] == R18R12_VERIFIED, "R18R12 ledger identity drift")
    _require(records[-1].get("status") == "verified_repository_binding_review_only" and records[-1].get("later_operations_enabled") is False and records[-1].get("mutations_performed") is False, "R18R12 terminal boundary drift")
    return {"ledger_head_digest": R18R12_LEDGER_HEAD, "verified_event_digest": R18R12_VERIFIED, "approval_digest": R18R12_APPROVAL_DIGEST}


def _validate_r18r10_ledger(path: Path) -> None:
    expected = (
        "sha256:55b0d94b709edf6e0500bb7210b4a03cc3f4de666f937e7db776ff6007fd0572",
        "sha256:16e0232d6761e03ecbfac9c141c0ea19ba9b52b6f5068cbb679cf6cdfaebdd60",
        R18R10_VERIFIED,
        R18R10_LEDGER_HEAD,
    )
    lines = path.read_bytes().splitlines()
    _require(len(lines) == 4, "R18R10 ledger event count drift")
    previous = None
    records = []
    for raw in lines:
        record = parse_canonical(raw)
        _require(record.get("previous_event_digest") == previous, "R18R10 ledger chain drift")
        _require(record.get("event_digest") == _digest_without(record, "event_digest"), "R18R10 event digest drift")
        records.append(record)
        previous = record["event_digest"]
    _require(tuple(record["event_digest"] for record in records) == expected, "R18R10 ledger identity drift")
    _require(records[2].get("kind") == "operation_verified" and records[2].get("poststate_digest") == R18R10_POSTSTATE and records[2].get("mutations_performed") is True, "R18R10 verified poststate drift")
    _require(records[3].get("kind") == "run_stopped" and records[3].get("status") == "verified" and records[3].get("rollback_status") == "not_required_verified", "R18R10 terminal boundary drift")


def _validate_approval(path: Path, prestate: Mapping[str, Any], credential: Mapping[str, Any], dependency: Mapping[str, str], definition_path: Path) -> dict[str, Any]:
    value = _load_self_digested_canonical(path, "IAM child approval", "artifact_digest")
    _require(value.get("schema") == "P5R0RS069R18R13IAMApprovalV2" and value.get("approval_id") == APPROVAL_ID and value.get("master_approval_id") == MASTER_APPROVAL_ID and value.get("parent_approval_id") == PARENT_APPROVAL_ID, "APPROVAL-012 child identity drift")
    _require(value.get("operation_id") == OPERATION_ID and value.get("operation_order") == 0 and value.get("scope") == [OPERATION_ID], "child approval operation scope drift")
    _require(isinstance(value.get("attempt_id"), str) and ATTEMPT_RE.fullmatch(value["attempt_id"]) is not None, "child approval attempt identity invalid")
    _require(value.get("definition_digest") == DEFINITION_DIGEST and value.get("packet_digest") == PACKET_DIGEST and value.get("capability_definition_digest") == CAPABILITY_DIGEST, "child approval source digest drift")
    _require(value.get("prestate_artifact_digest") == prestate["artifact_digest"] and value.get("prestate_state_digest") == prestate["state"]["state_digest"], "child approval prestate binding drift")
    _require(value.get("credential_binding_digest") == credential["artifact_digest"], "child approval credential binding drift")
    _require(value.get("authority_artifact_digest") == AUTHORITY_DIGEST and value.get("authority_binding_digest") == AUTHORITY_BINDING_DIGEST and value.get("r18r12_approval_digest") == dependency["approval_digest"], "child approval authority binding drift")
    _require(value.get("r18r12_ledger_head_digest") == dependency["ledger_head_digest"] and value.get("r18r12_verified_event_digest") == dependency["verified_event_digest"] and value.get("r18r10_ledger_head_digest") == R18R10_LEDGER_HEAD and value.get("r18r10_verified_event_digest") == R18R10_VERIFIED and value.get("r18r10_poststate_digest") == R18R10_POSTSTATE, "child approval dependency drift")
    _require(value.get("approved") is True and value.get("master_approved") is True and value.get("user_approved") is True and value.get("enabled") is False, "child approval readiness flags drift")
    _require(value.get("mutations_performed") is False and value.get("applied_state") is False and value.get("credentials_created") is False and value.get("cloud_operations") == [] and value.get("production_promotable") is False and value.get("signature_present") is False, "child approval crosses the no-apply boundary")
    return value


def validate_preparation(*, definition_path: Path = DEFAULT_DEFINITION, packet_path: Path = DEFAULT_PACKET, capability_path: Path = DEFAULT_CAPABILITY, authority_path: Path = DEFAULT_AUTHORITY, r18r12_approval_path: Path = DEFAULT_R18R12_APPROVAL, r18r12_ledger_path: Path = DEFAULT_R18R12_LEDGER, prestate_path: Path = DEFAULT_PRESTATE, credential_path: Path = DEFAULT_CREDENTIAL, approval_path: Path = DEFAULT_APPROVAL) -> dict[str, Any]:
    _validate_source_files(definition_path, packet_path, capability_path)
    authority = _load_self_digested_canonical(authority_path, "R18R12 authority binding", "artifact_digest")
    _require(authority["artifact_digest"] == AUTHORITY_DIGEST and authority.get("status") == "reviewed_local_binding_pending_signed_environment_approval", "authority binding drift")
    _require(authority["kms"]["authority_binding"]["binding_digest"] == AUTHORITY_BINDING_DIGEST, "authority KMS binding drift")
    dependency = _validate_dependency_ledger(r18r12_ledger_path)
    _validate_r18r10_ledger(DEFAULT_R18R10_LEDGER)
    unresolved: list[str] = []
    try:
        prior = _load_self_digested_canonical(r18r12_approval_path, "R18R12 approval", "artifact_digest")
        _require(prior["artifact_digest"] == R18R12_APPROVAL_DIGEST, "R18R12 approval digest drift")
    except IAMPreparationError as exc:
        unresolved.append(str(exc))
    prestate = _validate_prestate(prestate_path)
    credential = _validate_credential(credential_path)
    approval = _validate_approval(approval_path, prestate, credential, dependency, definition_path)
    unresolved.extend(prestate.get("unresolved", []))
    unresolved.extend(credential.get("unresolved", []))
    unresolved.extend(approval.get("unresolved", []))
    unresolved.append("The packet's credential_binding.service_account is p5-evaluator@..., while the target capability and IAM definition require p5-r0-gcs-only@...; packet integrity does not resolve this semantic mismatch.")
    return {"schema":"P5R0RS069R18R13IAMPreparationReportV1","operation_id":OPERATION_ID,"approval_id":approval["approval_id"],"attempt_id":approval["attempt_id"],"definition_digest":DEFINITION_DIGEST,"packet_digest":PACKET_DIGEST,"capability_definition_digest":CAPABILITY_DIGEST,"prestate_artifact_digest":prestate["artifact_digest"],"prestate_state_digest":prestate["state"]["state_digest"],"credential_binding_digest":credential["artifact_digest"],"authority_artifact_digest":AUTHORITY_DIGEST,"authority_binding_digest":AUTHORITY_BINDING_DIGEST,"cloud_operations":[],"mutations_performed":False,"applied_state":False,"ready_for_executor":False,"child_approval_enabled":approval["enabled"],"unresolved":sorted(set(unresolved))}


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Validate read-only RS-069R18R13-IAM preparation")
    parser.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--capability", type=Path, default=DEFAULT_CAPABILITY)
    parser.add_argument("--authority", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--r18r12-approval", type=Path, default=DEFAULT_R18R12_APPROVAL)
    parser.add_argument("--r18r12-ledger", type=Path, default=DEFAULT_R18R12_LEDGER)
    parser.add_argument("--prestate", type=Path, default=DEFAULT_PRESTATE)
    parser.add_argument("--credential", type=Path, default=DEFAULT_CREDENTIAL)
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    args = parser.parse_args()
    print(json.dumps(validate_preparation(definition_path=args.definition, packet_path=args.packet, capability_path=args.capability, authority_path=args.authority, r18r12_approval_path=args.r18r12_approval, r18r12_ledger_path=args.r18r12_ledger, prestate_path=args.prestate, credential_path=args.credential, approval_path=args.approval), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

__all__ = ["DEFAULT_APPROVAL", "DEFAULT_CREDENTIAL", "DEFAULT_PRESTATE", "IAMPreparationError", "validate_preparation"]
