"""Validate the local-only RS-069R18R13 GCS boundary packet.

This validator reads repository artifacts only. It never calls the cloud SDK,
creates credentials, mutates IAM/GCS, or changes the master runsheet.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.controlled_run_materializer import validate_artifact_commitments

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PACKET = Path(__file__).with_name("rs069r18r13-gcs-boundary-packet-v1.json")
PACKET_SCHEMA = "P5R0RS069R18R13GCSBoundaryPacketV1"
PROJECT_ID = "ocelot-proof"
BUCKET = "p5-evaluator-ocelot-proof-141633828616"
CAPABILITY_SERVICE_ACCOUNT = "p5-evaluator@ocelot-proof.iam.gserviceaccount.com"
PREFIX = "p5-r0/operation-4"
RUN_ID = "rs069r18r13-op4-04a98e3e"
NAMESPACE_FORMULA = "gs://{bucket}/{prefix}/{run_id}/{object_suffix}"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
OBJECT_ID_ORDER = (
    "bundle_input_manifest", "control_commitment", "evaluator_contract",
    "lock_signing_request", "manifest", "policy", "private_store",
    "provenance", "split", "task_set", "worker_contract",
)


class GCSBoundaryPacketError(ValueError):
    """The review-only packet is malformed or crosses its mutation boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GCSBoundaryPacketError(message)


def _digest(value: Any) -> str:
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return _digest({key: item for key, item in value.items() if key != field})


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise GCSBoundaryPacketError(f"packet is not valid JSON: {path}") from exc
    _require(isinstance(value, dict), "packet root must be an object")
    return value


def _is_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None, f"{label} is not a digest")


def validate_packet(path: Path = DEFAULT_PACKET, repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    """Validate packet closure, local artifact commitments, and no-apply claims."""
    root = Path(repository_root).resolve()
    packet = _load(Path(path))
    expected = {
        "schema", "packet_version", "classification", "status", "approval_context",
        "operation", "destination", "credential_binding", "current_state", "desired_iam",
        "artifact_binding", "objects", "read_only_evidence", "apply_plan", "packet_digest",
    }
    _require(set(packet) == expected, "packet fields are not closed")
    _require(packet["schema"] == PACKET_SCHEMA and packet["packet_version"] == 1, "packet identity drift")
    _require(packet["classification"] == "repository_review_only_non_release", "packet classification crosses release boundary")
    _require(packet["status"] == "reviewed_candidate_binding_pending_credential_and_iam", "packet status is not blocked pending prerequisites")
    _require(packet["packet_digest"] == _digest_without(packet, "packet_digest"), "packet digest mismatch")

    approval = packet["approval_context"]
    _require(approval == {
        "master_run": "P5-MASTER-001",
        "broad_approval_id": "P5-MASTER-001/APPROVAL-011",
        "operation_id": "ingest_generated_bundle_to_gcs",
        "operation_order": 4,
        "child_approval_present": False,
        "child_approval_id": None,
        "master_runsheet_modified": False,
    }, "approval context drift")

    operation = packet["operation"]
    _require(operation == {
        "id": "ingest_generated_bundle_to_gcs",
        "order": 4,
        "scope": ["ingest_generated_bundle_to_gcs"],
        "allowed_actions": ["gcs.create_only_or_exact_generation_match"],
        "forbidden_actions": ["gcs.list", "gcs.delete", "gcs.overwrite", "credential_generation"],
        "later_operations_enabled": False,
        "cloud_operations_performed": [],
        "mutations_performed": False,
    }, "operation boundary drift")

    destination = packet["destination"]
    _require(destination["project_id"] == PROJECT_ID and destination["bucket"] == BUCKET, "candidate project or bucket drift")
    _require(destination["prefix"] == PREFIX and destination["run_id"] == RUN_ID, "destination namespace drift")
    _require(destination["namespace_formula"] == NAMESPACE_FORMULA, "namespace formula drift")
    _require(destination["bucket_project_binding"] == {"bucket": BUCKET, "project_id": PROJECT_ID, "observed_match": True}, "bucket project binding drift")
    _require(destination["visibility"] == {
        "default": "private",
        "uniform_bucket_level_access": True,
        "public_access_prevention": "inherited",
        "public_principals_observed": False,
        "private_truth_object": "private",
        "worker_public_output": False,
    }, "visibility boundary drift")
    _require(destination["selected_from_candidate_only"] is True and destination["read_only_confirmed"] is True, "destination is not read-only confirmed")

    credential = packet["credential_binding"]
    _require(credential["service_account"] == CAPABILITY_SERVICE_ACCOUNT, "capability account drift")
    _require(credential["binding"] == "injected_reviewed_execution_path_only", "credential binding drift")
    _require(credential["local_credential_material"] is False and credential["credential_created"] is False and credential["credential_injected"] is False, "credential boundary drift")
    _require(credential["status"] == "missing_reviewed_execution_credential", "credential status must remain unresolved")
    _require(credential["token_source"] == "signed-environment STS token exchanged through IAM Credentials generateAccessToken for the exact capability service account", "token source drift")
    _require(credential["missing_facts"] == [
        "exact reviewed signed-environment WIF principal/attestation binding",
        "short-lived execution token injected by the reviewed execution path",
        "roles/iam.serviceAccountTokenCreator grant for that exact principal",
    ], "missing credential facts drift")

    state = packet["current_state"]
    _require(state["project"] == {"project_id": PROJECT_ID, "project_number": "141633828616", "lifecycle_state": "ACTIVE"}, "project observation drift")
    _require(state["bucket"]["name"] == BUCKET and state["bucket"]["project_id"] == PROJECT_ID and state["bucket"]["uniform_bucket_level_access"] is True, "bucket observation drift")
    _require(state["service_account"]["email"] == CAPABILITY_SERVICE_ACCOUNT and state["service_account"]["project_id"] == PROJECT_ID, "service-account observation drift")
    _require(state["iam"]["bucket_capability_account_roles"] == ["roles/storage.objectAdmin"], "current bucket IAM observation drift")
    _require(state["iam"]["service_account_roles"] == ["roles/iam.workloadIdentityUser"], "current service-account IAM observation drift")
    _require(state["iam"]["project_roles"] == ["roles/cloudkms.signerVerifier"], "current project IAM observation drift")
    _require(state["iam"]["operation4_narrow_grant_observed"] is False and state["iam"]["public_principals_observed"] is False, "current IAM boundary drift")

    desired = packet["desired_iam"]
    _require(desired["status"] == "desired_not_applied", "desired IAM was incorrectly marked applied")
    _require(desired["apply_performed"] is False and desired["cloud_operations"] == [], "desired IAM crosses apply boundary")
    _require(desired["bucket_writer"]["principal"] == f"serviceAccount:{CAPABILITY_SERVICE_ACCOUNT}", "desired bucket principal drift")
    _require(desired["bucket_writer"]["permissions"] == ["storage.objects.create", "storage.objects.get"], "desired bucket permissions are not narrow")
    _require(desired["bucket_writer"]["condition"]["expression"] == f"resource.name.startsWith('projects/_/buckets/{BUCKET}/objects/{PREFIX}/{RUN_ID}/')", "desired prefix condition drift")
    _require(desired["remove_current_broad_grant"] == {"role": "roles/storage.objectAdmin", "principal": f"serviceAccount:{CAPABILITY_SERVICE_ACCOUNT}", "required": True, "applied": False}, "broad grant remediation drift")
    _require(desired["token_creator"]["role"] == "roles/iam.serviceAccountTokenCreator" and desired["token_creator"]["principal"] is None and desired["token_creator"]["applied"] is False, "token creator binding must remain unresolved and unapplied")

    artifact = packet["artifact_binding"]
    index_path = root / artifact["index_path"]
    _require(index_path.resolve() == (root / "var/p5-r0-diagnostic-inputs/artifact-index.json").resolve(), "artifact index path drift")
    index = _load(index_path)
    _require(index["index_digest"] == artifact["index_digest"], "artifact index digest drift")
    request = _load(root / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json")
    _require(request["request_digest"] == artifact["request_digest"], "unsigned request digest drift")
    _require(request["unsigned_lock_digest"] == artifact["unsigned_lock_digest"], "unsigned lock digest drift")
    checked = validate_artifact_commitments(index, root / "var/p5-r0-diagnostic-inputs")
    _require(artifact["request_digest"] == "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d", "request commitment drift")
    _require(artifact["private_truth"] == {"object_suffix": "private-truth/case-store.json", "private": True, "worker_public_output": False}, "private truth binding drift")

    objects = packet["objects"]
    _require(isinstance(objects, list) and len(objects) == 11, "packet must contain exactly 11 objects")
    _require([item["object_id"] for item in objects] == list(OBJECT_ID_ORDER), "object order drift")
    for item in objects:
        _require(set(item) == {"object_id", "local_artifact_path", "object_suffix", "object_name", "private", "artifact_digest", "file_digest", "observed", "generation_precondition"}, f"object record is not closed: {item.get('object_id')}")
        source = index["artifacts"][item["object_id"]]
        _require(item["local_artifact_path"] == source["path"] and item["artifact_digest"] == source["digest"] and item["file_digest"] == source["file_digest"] and item["private"] == source["private"], f"artifact binding drift: {item['object_id']}")
        _require(checked[item["object_id"]]["file_digest"] == item["file_digest"], f"local file digest drift: {item['object_id']}")
        _require(item["object_name"] == f"{PREFIX}/{RUN_ID}/{item['object_suffix']}", f"object name drift: {item['object_id']}")
        _require(item["observed"] == {"status": "absent", "probe_http_status": 404, "generation": None}, f"object observation drift: {item['object_id']}")
        _require(item["generation_precondition"] == {"kind": "if_absent_or_exact_generation", "expected_generation": 0}, f"generation precondition drift: {item['object_id']}")
        _is_digest(item["artifact_digest"], f"{item['object_id']}.artifact_digest")
        _is_digest(item["file_digest"], f"{item['object_id']}.file_digest")

    evidence = packet["read_only_evidence"]
    _require(evidence["sdk_path"] == "/home/matt/google-cloud-sdk/bin/gcloud" and evidence["sdk_version"] == "Google Cloud SDK 585.0.0", "SDK evidence drift")
    _require(evidence["all_commands_read_only"] is True and evidence["cloud_mutation_commands"] == [], "read-only evidence boundary drift")
    _require(evidence["object_probe_count"] == 11 and evidence["object_probe_404_count"] == 11, "object probe coverage drift")
    probes = evidence["object_probes"]
    _require(isinstance(probes, list) and len(probes) == 11, "exact object probe evidence is incomplete")
    _require([probe["object_id"] for probe in probes] == list(OBJECT_ID_ORDER), "object probe order drift")
    for probe, item in zip(probes, objects):
        expected_uri = f"gs://{BUCKET}/{item['object_name']}"
        expected_command = f"/home/matt/google-cloud-sdk/bin/gcloud storage objects describe {expected_uri} --format=json"
        _require(probe == {"object_id": item["object_id"], "object_name": item["object_name"], "command": expected_command, "exit": 1, "http_status": 404, "generation": None}, f"exact object probe drift: {item['object_id']}")
    _require(evidence["active_caller"] == "hrdwrbob@gmail.com", "caller observation drift")

    plan = packet["apply_plan"]
    _require(plan["status"] == "conditional_not_executed" and plan["one_operation_id"] == "ingest_generated_bundle_to_gcs", "apply plan status drift")
    _require(plan["preconditions"] == [
        "separate reviewed IaC change applies and re-observes the narrow IAM proposal",
        "exact signed-environment WIF principal and short-lived token are injected; no key file is created",
        "fresh read-only probes confirm the same bucket/project, private visibility, and all 11 expected generations",
        "new exact child approval for APPROVAL-011 is present and packet digests are unchanged",
    ], "apply plan preconditions drift")
    _require(plan["steps"] == [
        "invoke only the reviewed operation-4 adapter with the injected capability token",
        "GET each exact object name without listing; require 404 -> generation 0 or exact observed positive generation",
        "create only absent objects with ifGenerationMatch=0 and verify bytes/digest by GET",
        "append the dedicated operation-4 ledger and stop; keep all later operations disabled",
    ], "apply plan steps drift")
    _require(plan["forbidden"] == ["gcloud direct mutation", "credential generation or key creation", "object listing", "object deletion", "overwrite", "downstream operation enablement"], "apply plan forbidden actions drift")
    _require(plan["execution_evidence"] == {"upload_performed": False, "ledger_event": False, "remote_generations": None, "remote_digests": None}, "apply plan evidence drift")
    _require(plan["required_authenticated_receipt"] == {
        "project_id": PROJECT_ID,
        "bucket": BUCKET,
        "capability_service_account": CAPABILITY_SERVICE_ACCOUNT,
        "per_object_fields": ["bucket", "project_id", "object_name", "generation", "remote_checksum", "private_visibility"],
        "must_be_verified_before_success": True,
    }, "authenticated receipt contract drift")

    return {
        "schema": packet["schema"],
        "packet_digest": packet["packet_digest"],
        "status": packet["status"],
        "project_id": PROJECT_ID,
        "bucket": BUCKET,
        "run_id": RUN_ID,
        "object_count": len(objects),
        "expected_generation": 0,
        "cloud_operations": [],
        "mutations_performed": False,
        "child_approval_present": False,
    }


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local-only RS-069R18R13 GCS boundary packet")
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    args = parser.parse_args(argv)
    print(json.dumps(validate_packet(args.packet), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())


__all__ = ["DEFAULT_PACKET", "GCSBoundaryPacketError", "PACKET_SCHEMA", "validate_packet"]
