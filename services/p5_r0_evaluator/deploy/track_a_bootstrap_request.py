"""Local-only APPROVAL-016/DISPATCH-071 bootstrap request validator.

This module prepares and validates one canonical, non-executable Track A
Confidential Space bootstrap request.  It binds only reviewed repository
artifacts and read-only inventory.  It never invokes gcloud, a launcher, STS,
IAM Credentials, KMS, GCS, timing, a VM, or a task runner.

The effectful runner is intentionally separate from this module: it consumes
this canonical packet only through its verifier-owned loader and fixed
Confidential Space factory.  This module itself remains local-only and never
invokes gcloud, a launcher, STS, IAM Credentials, KMS, GCS, timing, a VM, or a
task runner.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical
from services.p5_r0_evaluator.canonical import digest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REQUEST = Path(__file__).with_name("p5-r0-track-a-bootstrap-request.json")
CANDIDATE = REPOSITORY_ROOT / "var/p5-r0-rs069r1/candidate-image-binding.json"
ARTIFACT_INDEX = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/artifact-index.json"
MANIFEST = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/manifest.json"
WORKER_CONTRACT = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/worker-contract.json"
AUTHORITY_PROPOSAL = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json"
GCS_DEFINITION = Path(__file__).with_name("gcs-capability-definition.json")
IAM_PACKET = Path(__file__).with_name("rs069r18r13-iam-boundary-packet-v2.json")
IAM_PRESTATE = REPOSITORY_ROOT / "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json"
CLOSURE_SOURCE = REPOSITORY_ROOT / "var/p5-r0-rs069r1/candidate-image-binding.json"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PROVIDER_RE = re.compile(
    r"^//iam\.googleapis\.com/projects/(?P<number>[0-9]+)/locations/global/"
    r"workloadIdentityPools/(?P<pool>[a-z0-9-]+)/providers/(?P<provider>[a-z0-9-]+)$"
)

APPROVAL_ID = "P5-MASTER-001/APPROVAL-016"
DISPATCH_ID = "P5-MASTER-001/DISPATCH-071"
ATTEMPT_ID = "P5-MASTER-001/APPROVAL-016/DISPATCH-071/ATTEMPT-001"
OPERATION_ID = "bootstrap_signed_environment_credentials"

FORBIDDEN_OPERATIONS = (
    "timing",
    "task_issuance",
    "native_execution",
    "kms_result_signing",
    "gcs_publication",
    "retry",
)


class BootstrapRequestError(ValueError):
    """A bootstrap request is malformed, stale, or not fail-closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BootstrapRequestError(message)


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - exercised through the CLI
        raise BootstrapRequestError(f"{label} is not JSON") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _digest(value: Any, label: str) -> str:
    result = digest(value)
    _require(_DIGEST_RE.fullmatch(result) is not None, f"{label} digest is malformed")
    return result


def _source_digest(path: Path) -> str:
    return _digest(parse_canonical(path.read_bytes()), str(path))


def _build_request() -> dict[str, Any]:
    candidate = _load(CANDIDATE, "candidate image binding")
    index = _load(ARTIFACT_INDEX, "diagnostic artifact index")
    manifest = _load(MANIFEST, "Track A manifest")
    worker = _load(WORKER_CONTRACT, "worker contract")
    authority_proposal = _load(AUTHORITY_PROPOSAL, "authority proposal")
    gcs = _load(GCS_DEFINITION, "GCS capability definition")
    iam = _load(IAM_PACKET, "IAM packet")
    prestate = _load(IAM_PRESTATE, "IAM prestate")

    target = candidate["candidate"]["target_artifact_registry"]
    candidate_digest = candidate["candidate"]["image_digest"]
    candidate_reference = target["reference"]
    closure = candidate["closure"]
    _require(candidate_digest == closure["image_digest"], "candidate and closure image digests differ")
    _require(candidate_digest == target["remote_digest"], "candidate and remote registry digests differ")
    _require(candidate_reference.endswith("@" + candidate_digest), "candidate reference is not immutable")
    _require(target["project_id"] == "ocelot-proof" and target["project_number"] == "141633828616", "candidate project binding drift")
    _require(target["region"] == "us-east1" and target["repository"] == "p5-cs", "candidate registry binding drift")
    _require(closure["closure_digest"] == "sha256:4f49f208c6e65d87c5c50b90a316a1314298719425dde0858d66b33ceabed5c3", "candidate closure drift")

    authority = authority_proposal["authority"]
    kms = authority_proposal["kms"]
    transport = authority["transport_attestation"]
    claims = authority_proposal["bound_claims"]["claims"]
    _require(transport["provider"] == gcs["wif_binding"]["provider"], "WIP provider binding drift")
    _require(transport["audience"] == "https://sts.googleapis.com", "WIP audience drift")
    _require(claims["image_digest"] == candidate_digest, "attested image claim drift")
    _require(claims["project_id"] == target["project_id"] and claims["project_number"] == target["project_number"], "attested project claim drift")
    _require(claims["zone"] == "us-east1-b", "attested zone drift")
    _require(_PROVIDER_RE.fullmatch(transport["provider"]) is not None, "WIP provider is not canonical")

    first_case = manifest["case_index"][0]
    selection = {
        "schema": "P5R0TrackAMVPSelectionV1",
        "lock_digest": index["unsigned_lock_digest"],
        "manifest_digest": index["manifest_digest"],
        "worker_contract_digest": worker["digest"],
        "case_id": first_case["case_id"],
        "case_digest": first_case["case_digest"],
        "ordinal": first_case["ordinal"],
        "arm": "cold_reset",
        "control_id": "illegal_action",
        "task_schema": "P5R0WorkerTaskV3",
    }
    selection["selection_digest"] = _digest(selection, "Track A selection")

    input_commitments = {
        "schema": "P5R0TrackAInputCommitmentsV1",
        "artifact_index_digest": index["index_digest"],
        "manifest_digest": index["manifest_digest"],
        "private_store_digest": index["private_store_digest"],
        "worker_contract_digest": index["artifacts"]["worker_contract"]["digest"],
        "task_set_digest": index["task_set_digest"],
        "control_commitment_digest": index["control_commitment_digest"],
        "policy_digest": index["artifacts"]["policy"]["digest"],
        "unsigned_lock_digest": index["unsigned_lock_digest"],
        "private_store_path": index["private_truth_path"],
        "private_store_is_private": True,
        "worker_public_output": False,
        "input_builder_binding_digest": manifest["input_builder_binding"]["binding_digest"],
        "time_seed_algorithm_binding_digest": manifest["time_seed_algorithm_binding"]["binding_digest"],
    }
    input_commitments["commitment_digest"] = _digest(input_commitments, "Track A input commitments")

    # The local closure is exact and digest-bound, but its image reference is
    # the local OCI reference.  The remote Artifact Registry reference is bound
    # separately; reconciliation is an explicit external blocker, not inferred.
    closure_binding = {
        "schema": "P5R0TrackAClosureBindingReferenceV1",
        "source_path": "var/p5-r0-rs069r1/candidate-image-binding.json",
        "closure_digest": closure["closure_digest"],
        "image_digest": candidate_digest,
        "candidate_image_reference": candidate_reference,
        "closure_image_reference": closure["image_reference"],
        "runtime_digest": closure["runtime_digest"],
        "seccomp_digest": closure["seccomp_digest"],
        "allowed_syscalls_digest": closure["allowed_syscalls_digest"],
        "argv_digest": closure["argv_digest"],
        "worker_digest": closure["worker_digest"],
        "limits": closure["limits"],
        "network": closure["network"],
        "pull": closure["pull"],
        "runtime": closure["runtime"],
    }
    closure_binding["binding_digest"] = _digest(closure_binding, "closure binding")

    capability = gcs["capability_service_account"]
    request = {
        "schema": "P5R0TrackABootstrapRequestV1",
        "classification": "repository_preparation_only_non_release",
        "status": "blocked_pending_reviewed_effectful_bootstrap_runner",
        "master_run": "P5-MASTER-001",
        "approval": {
            "approval_id": APPROVAL_ID,
            "dispatch_id": DISPATCH_ID,
            "attempt_id": ATTEMPT_ID,
            "single_attempt": True,
            "retry_allowed": False,
            "scope": ["prelaunch_provisioning", "confidential_space_attestation", "capability_activation", "verifier_owned_bootstrap_evidence"],
            "user_approved_scope": "one reviewed Track A Confidential Space bootstrap attempt",
        },
        "operation": {
            "id": OPERATION_ID,
            "order": 1,
            "scope": [OPERATION_ID],
            "effectful_runner_present": False,
            "cloud_operations": [],
            "mutations_performed": False,
            "credentials_exported": False,
            "forbidden_operations": list(FORBIDDEN_OPERATIONS),
        },
        "candidate": {
            "image_reference": candidate_reference,
            "image_digest": candidate_digest,
            "project_id": target["project_id"],
            "project_number": target["project_number"],
            "region": target["region"],
            "repository": target["repository"],
            "remote_digest_verified": target["registry_digest_verified"],
            "remote_provenance_verified": target["remote_provenance_verified"],
            "binding_path": "var/p5-r0-rs069r1/candidate-image-binding.json",
        },
        "environment": {
            "zone": claims["zone"],
            "tee": claims["tee"],
            "hardware_model": claims["hardware_model"],
            "secure_boot": claims["secure_boot"],
            "debug_state": claims["debug_state"],
            "workload": claims["workload"],
            "issuer": claims["issuer"],
            "smoke": claims["smoke"],
            "wip_provider": transport["provider"],
            "wip_token_audience": transport["audience"],
            "claim_paths": authority_proposal["bound_claims"]["claim_paths"],
            "attestation_subject_prefix": claims.get("subject_prefix"),
        },
        "closure": closure_binding,
        "track_a": {
            "selection": selection,
            "input_commitments": input_commitments,
            "selection_source": "derived from the canonical generated manifest and worker contract; no task is issued",
            "task_execution_enabled": False,
            "timing_enabled": False,
            "result_gates_enabled": False,
        },
        "authority": {
            "schema": authority["schema"],
            "authority_id": authority["authority_id"],
            "key_id": authority["key_id"],
            "public_key": authority["public_key"],
            "public_key_digest": authority["public_key_digest"],
            "kms_key_version": kms["key_version"],
            "transport_binding_digest": _digest(transport, "KMS transport binding"),
            "authority_binding_digest": None,
            "authority_binding_status": "review_proposal_only_not_materialized",
        },
        "capability": {
            "service_account": capability["email"],
            "service_account_resource": capability["resource"],
            "bucket": gcs["destination"]["bucket"],
            "prefix": gcs["destination"]["prefix"],
            "run_id": gcs["destination"]["run_id"],
            "gcs_operations_enabled": False,
        },
        "current_inventory": {
            "source_prestate": "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json",
            "prestate_artifact_digest": prestate["artifact_digest"],
            "project_active": prestate["state"]["project"]["lifecycle_state"] == "ACTIVE",
            "target_service_account_exists": prestate["state"]["target_account"]["exists"],
            "custom_role_exists": prestate["state"]["custom_role"]["exists"],
            "current_wif_mapping_is_exact": False,
            "current_iam_is_least_privilege": False,
            "current_attestation_verified": False,
            "current_credentials_injected": False,
            "current_gcs_objects_published": False,
            "current_gcs_packet_status": gcs["status"],
            "current_iam_packet_status": iam["status"],
        },
        "reviewed_boundary": {
            "module": "services/p5_r0_evaluator/deploy/signed_environment_credentials.py",
            "function": "bootstrap_credentials",
            "reviewed_effectful_runner": False,
            "adapter_required": True,
            "adapter_factory_present": False,
            "cli_invocation": None,
            "reason": "The function consumes verifier-issued external objects and a real ConfidentialSpaceAdapter; no reviewed production adapter factory or bootstrap CLI exists.",
        },
        "local_validation": {
            "module": "services.p5_r0_evaluator.deploy.track_a_bootstrap_request",
            "invocation": "PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.track_a_bootstrap_request validate",
            "cloud_operations": [],
        },
        "blockers": [
            "no reviewed effectful Track A bootstrap runner or production adapter factory exists",
            "candidate closure uses a local OCI reference and has not been externally reconciled to the registry reference",
            "WIP/provider current mapping is incomplete and desired exact mapping is not applied",
            "target GCS-only capability account/custom role/token-creator binding are absent in fresh prestate",
            "no verifier-issued child approval/evidence object is present for this exact request",
            "authority binding digest is not materialized; proposal remains unsigned/review-only",
            "no real Google-signed Confidential Space attestation or short-lived capability credential exists",
        ],
        "claim_boundary": "Preparation only; no attestation, credentials, timing, task, native execution, KMS result signature, GCS publication, or result evidence is claimed.",
        "source_bindings": {
            "candidate": "var/p5-r0-rs069r1/candidate-image-binding.json",
            "artifact_index": "var/p5-r0-diagnostic-inputs/artifact-index.json",
            "manifest": "var/p5-r0-diagnostic-inputs/public/manifest.json",
            "worker_contract": "var/p5-r0-diagnostic-inputs/public/worker-contract.json",
            "authority_proposal": "var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json",
            "gcs_definition": "services/p5_r0_evaluator/deploy/gcs-capability-definition.json",
            "iam_packet": "services/p5_r0_evaluator/deploy/rs069r18r13-iam-boundary-packet-v2.json",
            "iam_prestate": "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json",
        },
    }
    request["request_digest"] = _digest(request, "bootstrap request")
    return request


def validate_request(path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    expected = _build_request()
    actual = _load(Path(path), "bootstrap request")
    _require(actual == expected, "bootstrap request does not match current reviewed source bindings")
    _require(actual["approval"]["approval_id"] == APPROVAL_ID, "approval binding drift")
    _require(actual["approval"]["attempt_id"] == ATTEMPT_ID and actual["approval"]["single_attempt"] is True, "attempt binding drift")
    _require(actual["operation"]["cloud_operations"] == [] and actual["operation"]["mutations_performed"] is False, "request crossed cloud boundary")
    _require(actual["operation"]["forbidden_operations"] == list(FORBIDDEN_OPERATIONS), "forbidden operation boundary drift")
    _require(actual["authority"]["authority_binding_digest"] is None, "unmaterialized authority binding was promoted")
    _require(actual["reviewed_boundary"]["reviewed_effectful_runner"] is False, "effectful runner claim was promoted")
    _require(actual["status"] == "blocked_pending_reviewed_effectful_bootstrap_runner", "request is not blocked")
    return {"schema": actual["schema"], "status": actual["status"], "request_digest": actual["request_digest"], "cloud_operations": []}


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local-only APPROVAL-016/DISPATCH-071 Track A bootstrap request")
    parser.add_argument("command", choices=("prepare", "validate"))
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        print(canonical_bytes(_build_request()).decode("utf-8"))
        return 0
    print(json.dumps(validate_request(args.request), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = ["BootstrapRequestError", "DEFAULT_REQUEST", "validate_request"]
