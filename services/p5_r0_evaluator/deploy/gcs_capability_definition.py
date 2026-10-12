"""Validate the repository-only DISPATCH-049 GCS capability definition.

The validator binds the desired least-privilege IAM/WIF boundary to the
reviewed Confidential Space credential path and the exact R18R13 bundle.  It
never calls cloud APIs, creates credentials, invokes KMS, uploads objects, or
changes the P5 master runsheet.
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
DEFAULT_DEFINITION = Path(__file__).with_name("gcs-capability-definition.json")
SCHEMA = "P5R0DISPATCH049GCSCapabilityDefinitionV1"
PROJECT_ID = "ocelot-proof"
PROJECT_NUMBER = "141633828616"
BUCKET = "p5-evaluator-ocelot-proof-141633828616"
PREFIX = "p5-r0/operation-4"
RUN_ID = "rs069r18r13-op4-04a98e3e"
SERVICE_ACCOUNT = "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com"
EXISTING_ACCOUNT = "p5-evaluator@ocelot-proof.iam.gserviceaccount.com"
OBSERVED_ACCOUNT = EXISTING_ACCOUNT
WIP_PROVIDER = "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production"
IMAGE_DIGEST = "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c"
WIF_PRINCIPAL = f"principalSet://iam.googleapis.com/projects/{PROJECT_NUMBER}/locations/global/workloadIdentityPools/p5-cs-pool/attribute.image_digest/{IMAGE_DIGEST}"
R18R12_OPERATION = "bind_self_custodied_authority_and_kms"
R18R13_OPERATION = "ingest_generated_bundle_to_gcs"
OBJECT_IDS = (
    "bundle_input_manifest", "control_commitment", "evaluator_contract",
    "lock_signing_request", "manifest", "policy", "private_store",
    "provenance", "split", "task_set", "worker_contract",
)
R18R12_LEDGER_HEAD = "sha256:30a59807d8dbf7aa2529d4efab406b4dcd5e87597442be71045827c816833329"
R18R12_VERIFIED_EVENT = "sha256:bbb534870778e46c38c6e0fc03dbc36f47f5f78c6127b12ef2e8557877f0a727"
R18R12_APPROVAL = "sha256:cfa0b7cc40f288282fdb432538460fc65cc4b0c8d3d247c73786fd4fa5cc9dd0"
R18R12_BINDING = "sha256:c8e186d51eb0dcce6d3b2db4939f0e62af69ee88fc5ada19c4ad8c878245fd61"
SOURCE_PACKET_DIGEST = "sha256:a8c313f6e5b775b4ba48a8e8ff4cc5e2561c560930c4e89ec2e9666fb509c447"
ATTRIBUTE_MAPPING = {
    "google.subject": "assertion.sub",
    "attribute.image_digest": "assertion.submods.container.image_digest",
    "attribute.project_number": "assertion.submods.gce.project_number",
    "attribute.project_id": "assertion.submods.gce.project_id",
    "attribute.zone": "assertion.submods.gce.zone",
    "attribute.debug_state": "assertion.dbgstat",
    "attribute.tee": "assertion.swname",
    "attribute.hardware_model": "assertion.hwmodel",
    "attribute.secure_boot": "assertion.secboot",
    "attribute.workload": "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD",
    "attribute.confidential_space_smoke": "assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
}
ATTRIBUTE_CONDITION_TERMS = (
    "assertion.aud == 'https://sts.googleapis.com'",
    "assertion.iss == 'https://confidentialcomputing.googleapis.com'",
    "assertion.sub.startsWith('https://www.googleapis.com/compute/v1/projects/ocelot-proof/zones/us-east1-b/instances/')",
    f"assertion.submods.container.image_digest == '{IMAGE_DIGEST}'",
    f"assertion.submods.gce.project_number == '{PROJECT_NUMBER}'",
    f"assertion.submods.gce.project_id == '{PROJECT_ID}'",
    "assertion.submods.gce.zone == 'us-east1-b'",
    "assertion.dbgstat == 'disabled-since-boot'",
    "assertion.swname == 'CONFIDENTIAL_SPACE'",
    "assertion.hwmodel == 'GCP_AMD_SEV'",
    "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD == 'evaluator'",
    "assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE == '0'",
    "assertion.secboot == true",
)


class GCSCapabilityDefinitionError(ValueError):
    """The DISPATCH-049 definition is malformed or crosses its no-apply boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GCSCapabilityDefinitionError(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise GCSCapabilityDefinitionError(f"invalid JSON: {path}") from exc
    _require(isinstance(value, dict), "definition root must be an object")
    return value


def _canonical_load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical(path.read_bytes())
    except Exception as exc:
        raise GCSCapabilityDefinitionError(f"{label} is unavailable or not canonical") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return sha256({key: item for key, item in value.items() if key != field})


def _digest(value: Any) -> str:
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _is_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None, f"{label} is not a digest")


def _resolve(root: Path, relative: str, label: str) -> Path:
    _require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), f"{label} must be relative")
    path = (root / relative).resolve()
    _require(root in path.parents and path.is_file(), f"{label} is missing")
    return path


def _validate_dependency(definition: Mapping[str, Any], root: Path) -> None:
    dependency = definition["dependency"]
    _require(dependency["operation_id"] == R18R12_OPERATION and dependency["required_terminal_status"] == "verified_repository_binding_review_only", "R18R12 dependency identity drift")
    binding_path = _resolve(root, dependency["binding_review_path"], "R18R12 binding review")
    binding = _canonical_load(binding_path, "R18R12 binding review")
    _require(binding["artifact_digest"] == dependency["binding_review_digest"] == R18R12_BINDING, "R18R12 binding digest drift")
    _require(binding["artifact_digest"] == _digest_without(binding, "artifact_digest"), "R18R12 binding artifact is not self-digested")
    _require(binding["status"] == "reviewed_local_binding_pending_signed_environment_approval", "R18R12 binding status drift")
    approval_path = _resolve(root, dependency["approval_path"], "R18R12 approval")
    approval = _canonical_load(approval_path, "R18R12 approval")
    _require(approval["artifact_digest"] == dependency["approval_digest"] == R18R12_APPROVAL, "R18R12 approval digest drift")
    _require(approval["artifact_digest"] == _digest_without(approval, "artifact_digest"), "R18R12 approval is not self-digested")
    _require(approval["operation_id"] == R18R12_OPERATION and approval["enabled"] is True, "R18R12 approval scope drift")
    ledger_path = _resolve(root, dependency["ledger_path"], "R18R12 ledger")
    records = [_canonical_load_line(line, "R18R12 ledger") for line in ledger_path.read_bytes().splitlines()]
    _require(len(records) == 4, "R18R12 ledger event count drift")
    _require(records[-1]["event_digest"] == dependency["ledger_head_digest"] == R18R12_LEDGER_HEAD, "R18R12 ledger head drift")
    _require(records[2]["event_digest"] == dependency["verified_event_digest"] == R18R12_VERIFIED_EVENT, "R18R12 verified event drift")
    _require(records[-1]["status"] == "verified_repository_binding_review_only" and records[-1]["later_operations_enabled"] is False, "R18R12 is not a verified repository-only dependency")


def _canonical_load_line(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical(raw)
    except Exception as exc:
        raise GCSCapabilityDefinitionError(f"{label} is malformed") from exc
    _require(isinstance(value, dict), f"{label} event must be an object")
    _require(value.get("event_digest") == _digest_without(value, "event_digest"), f"{label} event digest drift")
    return value


def _validate_objects(definition: Mapping[str, Any], root: Path) -> None:
    artifacts = definition["artifacts"]
    source = _load(_resolve(root, artifacts["source_packet_path"], "source packet"))
    _require(source["packet_digest"] == artifacts["source_packet_digest"] == SOURCE_PACKET_DIGEST, "source packet digest drift")
    _require(source["status"] == "reviewed_candidate_binding_pending_credential_and_iam", "source packet was promoted")
    _require(source["destination"]["project_id"] == PROJECT_ID and source["destination"]["bucket"] == BUCKET, "source packet destination drift")
    _require(source["destination"]["prefix"] == PREFIX and source["destination"]["run_id"] == RUN_ID, "source packet namespace drift")

    index_path = _resolve(root, artifacts["artifact_index_path"], "artifact index")
    index = _canonical_load(index_path, "artifact index")
    _require(index["index_digest"] == artifacts["artifact_index_digest"], "artifact index digest drift")
    checked = validate_artifact_commitments(index, root / "var/p5-r0-diagnostic-inputs")
    objects = artifacts["objects"]
    _require(len(objects) == 11 and tuple(item["id"] for item in objects) == OBJECT_IDS, "exact 11-object order drift")
    source_objects = {item["object_id"]: item for item in source["objects"]}
    for item in objects:
        _require(set(item) == {"id", "suffix", "private", "artifact_digest", "file_digest", "expected_generation"}, f"object record is not closed: {item.get('id')}")
        source_item = source_objects.get(item["id"])
        _require(source_item is not None, f"object missing from source packet: {item['id']}")
        _require(item["suffix"] == source_item["object_suffix"] and item["private"] == source_item["private"], f"object suffix/private drift: {item['id']}")
        _require(item["artifact_digest"] == source_item["artifact_digest"] and item["file_digest"] == source_item["file_digest"], f"object digest drift: {item['id']}")
        _require(item["expected_generation"] == 0 and source_item["generation_precondition"] == {"kind": "if_absent_or_exact_generation", "expected_generation": 0}, f"generation-0 precondition drift: {item['id']}")
        index_item = index["artifacts"][item["id"]]
        _require(index_item["digest"] == item["artifact_digest"] and index_item["file_digest"] == item["file_digest"], f"artifact index binding drift: {item['id']}")
        _require(checked[item["id"]]["file_digest"] == item["file_digest"], f"local file digest drift: {item['id']}")
        _is_digest(item["artifact_digest"], f"{item['id']}.artifact_digest")
        _is_digest(item["file_digest"], f"{item['id']}.file_digest")


def _validate_implementation_bindings(definition: Mapping[str, Any], root: Path) -> None:
    for binding in definition["implementation_bindings"]:
        path = _resolve(root, binding["path"], "implementation binding")
        text = path.read_text(encoding="utf-8")
        for symbol in binding["symbols"]:
            method = symbol.rsplit(".", 1)[-1]
            _require(re.search(rf"def\s+{re.escape(method)}\s*\(", text) is not None, f"implementation symbol missing: {symbol}")
        fragments = {
            "services/p5_r0_evaluator/confidential_space.py": (
                "CONFIDENTIAL_SPACE_LAUNCHER_SOCKET", "class GoogleSTSClient", "class CapabilityFactory",
                "IAMCredentialsAccessTokenFactory", "GCSStore(",
            ),
            "services/p5_r0_evaluator/timing_bridge_auth.py": (
                "class IAMCredentialsAccessTokenFactory", ":generateAccessToken", "_federated_token_is_valid",
            ),
            "services/p5_r0_evaluator/store.py": (
                "class GCSStore", "explicit federated GCS client", "if_generation_match=0",
            ),
        }
        for fragment in fragments.get(binding["path"], ()):
            _require(fragment in text, f"credential/store source binding drift: {fragment}")


def validate_definition(path: Path = DEFAULT_DEFINITION, repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    definition = _load(Path(path))
    expected = {"schema", "classification", "status", "operation", "dependency", "destination", "wif_binding", "capability_service_account", "iam", "credential_source", "artifacts", "implementation_bindings", "observed_state", "apply_boundary", "definition_digest"}
    _require(set(definition) == expected, "definition fields are not closed")
    _require(definition["schema"] == SCHEMA and definition["classification"] == "repository_definition_only_non_release", "definition identity drift")
    _require(definition["status"] == "blocked_pending_reviewed_iam_and_confidential_space_credential", "definition must remain blocked")
    _require(definition["definition_digest"] == _digest_without(definition, "definition_digest"), "definition digest mismatch")

    operation = definition["operation"]
    _require(operation == {"id": R18R13_OPERATION, "order": 4, "scope": [R18R13_OPERATION], "depends_on": [R18R12_OPERATION], "later_operations_enabled": False, "allowed_actions": ["gcs.create_only_or_exact_generation_match"], "forbidden_actions": ["gcs.list", "gcs.delete", "gcs.overwrite", "credential_generation"], "cloud_operations": [], "mutations_performed": False}, "operation boundary drift")
    _validate_dependency(definition, root)

    destination = definition["destination"]
    _require(destination == {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER, "bucket": BUCKET, "prefix": PREFIX, "run_id": RUN_ID, "namespace": f"gs://{BUCKET}/{PREFIX}/{RUN_ID}/{{object_suffix}}", "visibility": {"required": "private", "uniform_bucket_level_access": True, "public_access_prevention": "inherited", "public_principals_allowed": False, "private_truth_suffix": "private-truth/case-store.json", "worker_public_output": False}}, "destination boundary drift")

    wif = definition["wif_binding"]
    _require(wif["provider"] == WIP_PROVIDER and wif["principal"] == WIF_PRINCIPAL and wif["attribute"] == "image_digest" and wif["image_digest"] == IMAGE_DIGEST, "exact WIF principal drift")
    _require(wif["attribute_mapping"] == ATTRIBUTE_MAPPING, "WIF attribute mapping drift")
    _require(wif["attribute_condition_terms"] == list(ATTRIBUTE_CONDITION_TERMS), "WIF attribute condition drift")

    account = definition["capability_service_account"]
    _require(account == {"email": SERVICE_ACCOUNT, "resource": f"projects/{PROJECT_ID}/serviceAccounts/{SERVICE_ACCOUNT}"}, "capability service-account drift")
    iam = definition["iam"]
    _require(iam["state"] == "desired_not_applied" and iam["public_principals_allowed"] is False, "IAM state was promoted")
    writer = iam["bucket_writer"]
    _require(writer == {"role": f"projects/{PROJECT_ID}/roles/p5R0Operation4BundleWriterV1", "permissions": ["storage.objects.create", "storage.objects.get"], "member": f"serviceAccount:{SERVICE_ACCOUNT}", "condition_title": "p5_r0_r18r13_op4_exact_run", "condition_expression": f"resource.name.startsWith('projects/_/buckets/{BUCKET}/objects/{PREFIX}/{RUN_ID}/')", "forbidden_permissions": ["storage.objects.list", "storage.objects.delete", "storage.objects.update"]}, "custom writer IAM drift")
    _require(iam["remove_broad_grant"] == {"member": f"serviceAccount:{EXISTING_ACCOUNT}", "role": "roles/storage.objectAdmin", "required": True}, "objectAdmin removal boundary drift")
    _require(iam["token_creator"] == {"member": WIF_PRINCIPAL, "role": "roles/iam.serviceAccountTokenCreator", "resource": f"projects/{PROJECT_ID}/serviceAccounts/{SERVICE_ACCOUNT}"}, "token-creator boundary drift")

    credential = definition["credential_source"]
    _require(credential == {"status": "required_but_not_injected", "origin": "Confidential Space only", "launcher_socket": "/run/container_launcher/teeserver.sock", "attestation_issuer": "https://confidentialcomputing.googleapis.com", "attestation_audience": "https://sts.googleapis.com", "wif_provider": WIP_PROVIDER, "sts_endpoint": "https://sts.googleapis.com/v1/token", "iam_credentials_endpoint": f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{SERVICE_ACCOUNT}:generateAccessToken", "iam_credentials_method": "generateAccessToken", "target_service_account": SERVICE_ACCOUNT, "delivery": "injected short-lived access token to the explicit GCS client", "expiry": "bounded by federated source expiry and 3600 seconds", "ambient_credentials_allowed": False, "service_account_key_allowed": False, "credential_export_allowed": False, "adc_discovery_allowed": False}, "credential-source boundary drift")

    _require(definition["observed_state"] == {"project": {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER, "lifecycle_state": "ACTIVE"}, "bucket": {"exists": True, "project_id": PROJECT_ID, "uniform_bucket_level_access": True, "public_access_prevention": "inherited", "public_principals_observed": False, "wif_roles": ["roles/storage.objectUser"], "wif_principal": "principalSet://iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/attribute.image_digest/sha256:0a42a061ac593c7dd4e21e90fab7b8bb62d1836666e5507549fb4194b18dcca7", "wif_condition": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}, "capability_service_account": {"exists": True, "email": OBSERVED_ACCOUNT, "bucket_roles": ["roles/storage.objectAdmin"], "service_account_roles": ["roles/iam.workloadIdentityUser"], "token_creator_observed": False}, "observed_wif_principal": "principalSet://iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/attribute.image_digest/sha256:0a42a061ac593c7dd4e21e90fab7b8bb62d1836666e5507549fb4194b18dcca7", "observed_wif_condition": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')", "object_probe": {"count": 11, "http_404_count": 11, "generation_observed": False}, "cloud_mutations_observed_by_packet": []}, "observed-vs-desired state drift")
    _require(definition["apply_boundary"] == {"apply_performed": False, "cloud_operations": [], "credentials_created": False, "credentials_exported": False, "credential_injected": False, "kms_called": False, "gcs_called": False, "master_runsheet_modified": False, "later_operations_enabled": False, "required_later_boundary": "Apply IAM/WIF/token-creator through reviewed IaC, re-observe exact state, inject only an expiring Confidential Space-derived token, then obtain a fresh child approval before one operation-4 attempt."}, "apply boundary drift")
    _validate_objects(definition, root)
    _validate_implementation_bindings(definition, root)
    return {"schema": SCHEMA, "definition_digest": definition["definition_digest"], "status": definition["status"], "project_id": PROJECT_ID, "bucket": BUCKET, "run_id": RUN_ID, "wif_principal": WIF_PRINCIPAL, "object_count": 11, "generation_precondition": 0, "r18r12_dependency": R18R12_OPERATION, "cloud_operations": [], "apply_performed": False}


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the repository-only DISPATCH-049 GCS capability definition")
    parser.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
    args = parser.parse_args(argv)
    print(json.dumps(validate_definition(args.definition), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())


__all__ = ["DEFAULT_DEFINITION", "GCSCapabilityDefinitionError", "validate_definition"]
