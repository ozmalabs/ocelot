"""APPROVAL-021 reviewed Confidential Space VM/bootstrap boundary.

This module validates a blocked, repository-only definition and exposes an
injected-IaC runner. It never imports a cloud SDK, invokes gcloud, creates
credentials, or launches a VM. A future approved orchestrator supplies a
reviewed VM backend and a verifier-owned launcher evidence source; the runner
then owns exact prestate/poststate/rollback, one-shot evidence, and no-retry
ledger semantics.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol

from evaluation.p0a.canonical import canonical_bytes, sha256
from services.p5_r0_evaluator.deploy.iam_predecessor import VerifiedIAMPredecessor, load_verified_iam_predecessor, validate_verified_iam_predecessor

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEFINITION = Path(__file__).with_name("approval-021-confidential-space-bootstrap-definition-v1.json")
DEFAULT_APPROVAL = REPOSITORY_ROOT / "var/p5-r0-rs069/approval-021-confidential-space-approval.json"
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/approval-021-confidential-space-bootstrap-ledger.jsonl"
SCHEMA = "P5R0APPROVAL021ConfidentialSpaceBootstrapDefinitionV1"
APPROVAL_SCHEMA = "P5R0APPROVAL021ConfidentialSpaceBootstrapApprovalV1"
LEDGER_SCHEMA = "P5R0APPROVAL021ConfidentialSpaceBootstrapLedgerEventV1"
EVIDENCE_SCHEMA = "P5R0StartupAttestationEvidenceV1"
OPERATION_ID = "bootstrap_confidential_space_vm"
APPROVAL_ID = "P5-MASTER-001/APPROVAL-021"
ATTEMPT_ID = "approval021-cs-vm-001"
PROJECT_ID = "ocelot-proof"
PROJECT_NUMBER = "141633828616"
REGION = "us-east1"
ZONE = "us-east1-b"
VM_NAME = "p5-r0-confidential-space-evaluator"
MACHINE_TYPE = "n2d-standard-2"
IMAGE_DIGEST = "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c"
IMAGE_REFERENCE = f"us-east1-docker.pkg.dev/{PROJECT_ID}/p5-cs/evaluator@{IMAGE_DIGEST}"
WIP_PROVIDER = "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production"
TOKEN_AUDIENCE = "https://sts.googleapis.com"
CAPABILITY_SERVICE_ACCOUNT = "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com"
CUSTOM_ROLE = "projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1"
WIF_PRINCIPAL = "principalSet://iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/attribute.image_digest/" + IMAGE_DIGEST.removeprefix("sha256:")
EXPECTED_CLAIM_PATHS = {
    "audience": "aud", "nonce": "eat_nonce", "issued_at": "iat", "expires_at": "exp",
    "issuer": "iss", "subject": "sub", "image_digest": "submods.container.image_digest",
    "project_number": "submods.gce.project_number", "project_id": "submods.gce.project_id",
    "zone": "submods.gce.zone", "debug_state": "dbgstat", "tee": "swname",
    "hardware_model": "hwmodel", "secure_boot": "secboot",
    "workload": "submods.container.env.P5R0_EXPECTED_WORKLOAD",
    "smoke": "submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
}
RUNTIME_DIGEST = "sha256:bd8ad7e7798edd5a857476c33bbef463b8b60ca2db43d7feb77698a703060c84"
SECCOMP_DIGEST = "sha256:cc374cf23846ce1f62f4dc807a8e2b8673c783c6f56cb475467621035d281e6c"
ALLOWED_SYSCALLS_DIGEST = "sha256:f7aa546b7b880ed6ba2ee4ec1bdf3c3d554204aff22c5bf08e11c9e273e5147d"
CLOSURE_DIGEST = "sha256:4f49f208c6e65d87c5c50b90a316a1314298719425dde0858d66b33ceabed5c3"
ARGV_DIGEST = "sha256:dd7f904e77834b2cbcde1996e549c336b8b31fc9c9cacd40a5b3b424107dae21"
RESOURCE_PROFILE_DIGEST = "sha256:113b8d7763e70dce6f9b7697459a14ae46180cd478a38f76b962414eb03d63c6"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class BootstrapError(ValueError):
    """The definition, approval, backend observation, or rollback is unsafe."""


class BootstrapBlocked(BootstrapError):
    """A local definition is valid but an external prerequisite is absent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BootstrapError(message)


def _digest(value: Any) -> str:
    return sha256(value if isinstance(value, dict) else canonical_bytes(value))


def _is_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} must be a sha256 digest")
    return value


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise BootstrapError(f"{label} is unavailable or invalid JSON") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _definition_digest(value: Mapping[str, Any]) -> str:
    return _digest({key: item for key, item in value.items() if key != "definition_digest"})


def _closed(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    _require(set(value) == expected, f"{label} fields are not closed")


def _metadata_arg(vm_name: str) -> str:
    metadata_file = f"rendered-{vm_name}.metadata"
    return "--metadata=^|^$(awk 'BEGIN { sep=\"\" } /^[[:space:]]*#/ || NF == 0 { next } { key=$1; sub(/^[^=]*/, \"\"); printf \"%s%s=%s\", sep, key, $0; sep=\"|\" }' " + metadata_file + ")"


def _launch_argv(definition: Mapping[str, Any]) -> tuple[str, ...]:
    target = definition["target"]
    return (
        "gcloud", "compute", "instances", "create", target["vm_name"],
        f"--project={target['project_id']}", f"--zone={target['zone']}",
        f"--machine-type={target['machine_type']}", "--confidential-compute-type=SEV",
        "--maintenance-policy=TERMINATE", "--image-family=confidential-space",
        "--image-project=confidential-space-images", "--shielded-secure-boot", "--shielded-vtpm",
        "--network-interface=network=default,subnet=default,no-address",
        f"--service-account={target['service_account']}",
        "--scopes=https://www.googleapis.com/auth/cloud-platform",
        _metadata_arg(target["vm_name"]),
    )


def render_metadata(definition_path: Path = DEFAULT_DEFINITION) -> str:
    """Render only non-secret Confidential Space metadata; never applies it."""
    definition = _load_json(Path(definition_path), "APPROVAL-021 definition")
    validate_definition(Path(definition_path))
    image = definition["image"]
    wip = definition["wip"]
    values = {
        "P5R0_ATTESTATION_AUDIENCE": wip["token_audience"], "P5R0_WIP_PROVIDER": wip["provider"],
        "P5R0_EXPECTED_PROJECT_NUMBER": wip["project_number"], "P5R0_EXPECTED_PROJECT_ID": wip["project_id"],
        "P5R0_EXPECTED_ZONE": wip["zone"], "P5R0_EXPECTED_IMAGE_DIGEST": image["digest"],
        "P5R0_ATTESTATION_ISSUER": wip["issuer"], "P5R0_EXPECTED_DEBUG_STATE": wip["debug_state"],
        "P5R0_EXPECTED_TEE": wip["tee"], "P5R0_EXPECTED_HARDWARE_MODEL": wip["hardware_model"],
        "P5R0_EXPECTED_WORKLOAD": wip["workload"], "P5R0_EXPECTED_SECURE_BOOT": "true",
        "P5R0_CONFIDENTIAL_SPACE_SMOKE": wip["smoke"], "P5R0_CAPABILITY_SERVICE_ACCOUNT": definition["iam"]["capability_service_account"],
        "P5R0_RUNTIME_DIGEST": definition["container_closure"]["runtime_digest"],
        "P5R0_RESOURCE_PROFILE_DIGEST": definition["container_closure"]["resource_profile_digest"],
        "P5R0_POLICY_DIGEST": definition["definition_digest"], "P5R0_ATTESTATION_SUBJECT_PREFIX": wip["subject_prefix"],
        "P5R0_CLOSURE_JSON": json.dumps(definition["container_closure"], sort_keys=True, separators=(",", ":")),
    }
    suffixes = {"audience": "AUDIENCE", "nonce": "NONCE", "issued_at": "ISSUED_AT", "expires_at": "EXPIRES_AT", "issuer": "ISSUER", "subject": "SUBJECT", "image_digest": "IMAGE_DIGEST", "project_number": "PROJECT_NUMBER", "project_id": "PROJECT_ID", "zone": "ZONE", "debug_state": "DEBUG_STATE", "tee": "TEE", "hardware_model": "HARDWARE_MODEL", "secure_boot": "SECURE_BOOT", "workload": "WORKLOAD", "smoke": "SMOKE"}
    values.update({f"P5R0_CLAIM_{suffixes[key]}": value for key, value in wip["claim_paths"].items()})
    lines = ["# Review-only rendered Confidential Space VM metadata.", f"tee-image-reference={image['reference']}", "tee-container-log-redirect=true"]
    lines.extend(f"tee-env-{key}={values[key]}" for key in sorted(values))
    return "\n".join(lines) + "\n"


def validate_definition(path: Path = DEFAULT_DEFINITION) -> dict[str, Any]:
    definition = _load_json(Path(path), "APPROVAL-021 definition")
    _closed(definition, {"schema", "version", "classification", "status", "approval_context", "operation", "target", "image", "wip", "iam", "container_closure", "prestate_contract", "apply_order", "rollback", "poststate", "execution_boundary", "future_commands", "definition_digest"}, "definition")
    _require(definition["schema"] == SCHEMA and definition["version"] == 1 and definition["classification"] == "repository_definition_only_non_release" and definition["status"] == "blocked_pending_fresh_live_bindings_and_child_approval", "definition identity/status drift")
    _is_digest(definition["definition_digest"], "definition digest")
    _require(definition["definition_digest"] == _definition_digest(definition), "definition digest mismatch")
    _require(definition["approval_context"] == {"approval_id": APPROVAL_ID, "single_attempt": True, "retry_allowed": False, "master_runsheet_modified": False, "cloud_operations": [], "attestation_claimed": False}, "approval boundary drift")
    operation = definition["operation"]
    _closed(operation, {"id", "scope", "order", "later_operations_enabled", "cloud_operations", "mutations_performed", "credentials_exported", "forbidden_operations"}, "operation")
    _require(operation["id"] == OPERATION_ID and operation["scope"] == [OPERATION_ID] and operation["order"] == 1 and operation["later_operations_enabled"] is False and operation["cloud_operations"] == [] and operation["mutations_performed"] is False and operation["credentials_exported"] is False, "operation boundary drift")
    _require(operation["forbidden_operations"] == ["retry", "attestation_fabrication", "credential_export", "timing", "task_issuance", "native_execution", "kms_result_signing", "gcs_publication"], "forbidden operation drift")
    target = definition["target"]
    _require(target == {"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER, "region": REGION, "zone": ZONE, "vm_name": VM_NAME, "machine_type": MACHINE_TYPE, "confidential_compute_type": "SEV", "secure_boot": True, "vtpm": True, "external_ip": False, "network": "default", "service_account": CAPABILITY_SERVICE_ACCOUNT}, "target drift")
    image = definition["image"]
    _require(image == {"reference": IMAGE_REFERENCE, "digest": IMAGE_DIGEST, "remote_digest_verified": True, "source_path": "var/p5-r0-rs069r1/candidate-image-binding.json"} and image["reference"].endswith("@" + image["digest"]), "image binding drift")
    wip = definition["wip"]
    _require(wip["provider"] == WIP_PROVIDER and wip["token_audience"] == TOKEN_AUDIENCE and wip["provider"] != wip["token_audience"] and wip["issuer"] == "https://confidentialcomputing.googleapis.com" and wip["subject_prefix"] == f"https://www.googleapis.com/compute/v1/projects/{PROJECT_ID}/zones/{ZONE}/instances/" and wip["image_digest"] == IMAGE_DIGEST and wip["project_id"] == PROJECT_ID and wip["project_number"] == PROJECT_NUMBER and wip["zone"] == ZONE and wip["debug_state"] == "disabled-since-boot" and wip["tee"] == "CONFIDENTIAL_SPACE" and wip["hardware_model"] == "GCP_AMD_SEV" and wip["secure_boot"] is True and wip["workload"] == "evaluator" and wip["smoke"] == "0", "WIP binding drift")
    _require(wip["claim_paths"] == EXPECTED_CLAIM_PATHS, "WIP claim-path values drift")
    iam = definition["iam"]
    _require(iam["capability_service_account"] == CAPABILITY_SERVICE_ACCOUNT and iam["custom_role"] == CUSTOM_ROLE and iam["wif_principal"] == WIF_PRINCIPAL and iam["token_creator_role"] == "roles/iam.serviceAccountTokenCreator" and iam["direct_bucket_access"] is False and iam["fresh_poststate_required"] is True, "IAM boundary drift")
    closure = definition["container_closure"]
    _require(closure == {"runtime": "crun", "network": "none", "pull": "never", "host_mounts": [], "privileged": False, "seccomp": "default-deny-reviewed-profile", "capabilities": "drop-all", "user": "65532:65532", "filesystem": "read-only", "pids_limit": 32, "memory_limit": "512Mi", "cpu_limit": "1", "runtime_digest": RUNTIME_DIGEST, "seccomp_digest": SECCOMP_DIGEST, "allowed_syscalls_digest": ALLOWED_SYSCALLS_DIGEST, "closure_digest": CLOSURE_DIGEST, "argv_digest": ARGV_DIGEST, "resource_profile_digest": RESOURCE_PROFILE_DIGEST}, "container closure drift")
    _require(definition["prestate_contract"] == {"schema": "P5R0APPROVAL021ConfidentialSpaceVMPrestateV1", "required": ["project", "zone", "vm_name", "instance", "iam_poststate", "wip_poststate"], "expected": {"instance_exists": False, "external_ip": False}, "fresh_capture_required": True, "capture_read_only": True, "ambiguous_state": "manual_review_no_retry"}, "prestate contract drift")
    _require(definition["apply_order"] == ["validate_definition_and_external_child_approval", "capture_fresh_read_only_prestate", "create_exact_shielded_confidential_space_vm", "capture_exact_poststate", "capture_one_shot_redacted_launcher_evidence", "verify_poststate_and_receipt"], "apply order drift")
    _require(definition["rollback"] == {"required_on_any_post_create_failure": True, "action": "delete_only_the_created_vm_then_reobserve", "if_delete_fails": "manual_review_no_retry", "if_account_or_network_state_is_ambiguous": "manual_review_no_retry"}, "rollback contract drift")
    _require(definition["execution_boundary"] == {"apply_performed": False, "cloud_operations": [], "credentials_created_or_exported": False, "attestation_claimed": False, "master_runsheet_modified": False, "later_operations_enabled": False}, "execution boundary drift")
    commands = definition["future_commands"]
    _require(commands["future_apply"].startswith("PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.confidential_space_bootstrap apply") and tuple(commands["future_launch_template"]) == _launch_argv(definition), "future command drift")
    return {"schema": SCHEMA, "definition_digest": definition["definition_digest"], "status": definition["status"], "operation_id": OPERATION_ID, "image_reference": IMAGE_REFERENCE, "wip_provider": WIP_PROVIDER, "token_audience": TOKEN_AUDIENCE, "cloud_operations": [], "apply_performed": False}


def load_approval(path: Path, *, definition: Mapping[str, Any]) -> dict[str, Any]:
    approval = _load_json(Path(path), "APPROVAL-021 child approval")
    _closed(approval, {"schema", "approval_id", "status", "attempt_id", "single_attempt", "retry_allowed", "verifier_issued", "definition_digest", "image_digest", "wip_provider", "token_audience", "iam_poststate_digest", "live_bindings_digest", "approval_digest"}, "child approval")
    _require(approval["schema"] == APPROVAL_SCHEMA and approval["approval_id"] == APPROVAL_ID and approval["status"] == "approved_single_attempt_pending_apply" and approval["single_attempt"] is True and approval["retry_allowed"] is False and approval["verifier_issued"] is True, "child approval identity/status drift")
    _require(approval["attempt_id"] == ATTEMPT_ID and approval["definition_digest"] == definition["definition_digest"] and approval["image_digest"] == IMAGE_DIGEST and approval["wip_provider"] == WIP_PROVIDER and approval["token_audience"] == TOKEN_AUDIENCE, "child approval binding drift")
    _is_digest(approval["iam_poststate_digest"], "IAM poststate digest")
    _is_digest(approval["live_bindings_digest"], "live bindings digest")
    _require(approval["approval_digest"] == _digest({key: item for key, item in approval.items() if key != "approval_digest"}), "child approval digest mismatch")
    return approval


class VMBackend(Protocol):
    reviewed: bool
    direct_gcloud: bool
    uses_adc: bool

    def describe_prestate(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def create_instance(self, request: Mapping[str, Any]) -> None: ...
    def describe_poststate(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def delete_instance(self, request: Mapping[str, Any]) -> None: ...


_EVIDENCE_ISSUE_TOKEN = object()


@dataclass(frozen=True, init=False)
class VerifierIssuedLauncherEvidence:
    """Immutable, redacted evidence issued only by the verifier-source wrapper."""
    snapshot: Mapping[str, Any]
    _original_digest: str

    def __init__(self, token: object, snapshot: Mapping[str, Any]):
        if token is not _EVIDENCE_ISSUE_TOKEN:
            raise TypeError("launcher evidence can only be issued by the verifier boundary")
        frozen = MappingProxyType(dict(snapshot))
        object.__setattr__(self, "snapshot", frozen)
        object.__setattr__(self, "_original_digest", _digest(dict(frozen)))


class VerifierOwnedLauncherEvidenceSource:
    """Adapter for the real launcher/JWT verifier; it never returns token bytes."""

    def __init__(self, capture: Callable[[Mapping[str, Any]], "VerifierIssuedLauncherEvidence"]):
        _require(callable(capture), "verifier launcher capture is required")
        self._capture = capture

    def capture(self, request: Mapping[str, Any]) -> "VerifierIssuedLauncherEvidence":
        evidence = self._capture(request)
        _require(type(evidence) is VerifierIssuedLauncherEvidence, "launcher source returned non-verifier evidence")
        return evidence


def _issue_verifier_evidence(value: Mapping[str, Any]) -> VerifierIssuedLauncherEvidence:
    return VerifierIssuedLauncherEvidence(_EVIDENCE_ISSUE_TOKEN, value)


class ReviewedConfidentialSpaceBackend:
    """Narrow adapter for an externally reviewed VM/IaC backend and verifier source."""

    def __init__(self, backend: VMBackend, *, launcher_source: VerifierOwnedLauncherEvidenceSource):
        _require(getattr(backend, "reviewed", False) is True, "reviewed VM backend is required")
        _require(getattr(backend, "direct_gcloud", False) is False, "direct gcloud backend is forbidden")
        _require(getattr(backend, "uses_adc", False) is False, "ambient ADC backend is forbidden")
        for name in ("describe_prestate", "create_instance", "describe_poststate", "delete_instance"):
            _require(callable(getattr(backend, name, None)), f"VM backend method missing: {name}")
        _require(type(launcher_source) is VerifierOwnedLauncherEvidenceSource, "verifier-owned launcher evidence source is required")
        self._backend = backend
        self._launcher_source = launcher_source

    def describe_prestate(self, request: Mapping[str, Any]) -> Mapping[str, Any]: return self._backend.describe_prestate(request)
    def create_instance(self, request: Mapping[str, Any]) -> None: self._backend.create_instance(request)
    def describe_poststate(self, request: Mapping[str, Any]) -> Mapping[str, Any]: return self._backend.describe_poststate(request)
    def delete_instance(self, request: Mapping[str, Any]) -> None: self._backend.delete_instance(request)
    def capture_launcher_evidence(self, request: Mapping[str, Any]) -> VerifierIssuedLauncherEvidence: return self._launcher_source.capture(request)


class AttemptLedger:
    """Create-only ledger; a reserved attempt can never be retried."""
    def __init__(self, path: Path, *, identity_path: Path):
        self.path = Path(path).resolve()
        self.identity_path = Path(identity_path).resolve()
        _require(self.path.name.endswith(".jsonl"), "bootstrap ledger must be JSONL")
        self._reserved = False
        self._closed = False
        self._binding: tuple[str, str] | None = None

    def _append(self, event: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as stream:
            stream.write(canonical_bytes(dict(event)) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())

    def reserve(self, approval_digest: str, definition_digest: str) -> None:
        if self._reserved or self.path.exists() or self.identity_path.exists():
            raise BootstrapError("bootstrap attempt already exists; retry is disabled")
        _is_digest(approval_digest, "approval digest")
        _is_digest(definition_digest, "definition digest")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.identity_path.parent.mkdir(parents=True, exist_ok=True)
        record = {"schema": LEDGER_SCHEMA, "kind": "reserved", "attempt_id": ATTEMPT_ID, "approval_digest": approval_digest, "definition_digest": definition_digest, "cloud_operations": [], "credentials_exported": False}
        try:
            with self.identity_path.open("xb") as identity:
                identity.write(canonical_bytes(record))
            with self.path.open("xb") as stream:
                stream.write(canonical_bytes(record) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise BootstrapError("bootstrap attempt already exists; retry is disabled") from exc
        self._reserved = True
        self._binding = (approval_digest, definition_digest)

    def close(self, status: str, *, approval_digest: str, definition_digest: str, **extra: Any) -> None:
        if not self._reserved or self._closed or self._binding != (approval_digest, definition_digest):
            raise BootstrapError("bootstrap ledger is not open for this attempt")
        self._append({"schema": LEDGER_SCHEMA, "kind": "stopped", "attempt_id": ATTEMPT_ID, "status": status, "approval_digest": approval_digest, "definition_digest": definition_digest, "cloud_operations": [], "credentials_exported": False, **extra})
        self._closed = True


def _request(definition: Mapping[str, Any], approval: Mapping[str, Any]) -> dict[str, Any]:
    target = definition["target"]
    wip = definition["wip"]
    closure = definition["container_closure"]
    return {"operation_id": OPERATION_ID, "attempt_id": ATTEMPT_ID, "approval_digest": approval["approval_digest"], "definition_digest": definition["definition_digest"], "project_id": target["project_id"], "project_number": target["project_number"], "region": target["region"], "zone": target["zone"], "vm_name": target["vm_name"], "machine_type": target["machine_type"], "confidential_compute_type": target["confidential_compute_type"], "secure_boot": target["secure_boot"], "vtpm": target["vtpm"], "external_ip": target["external_ip"], "network": target["network"], "service_account": target["service_account"], "image_reference": definition["image"]["reference"], "image_digest": definition["image"]["digest"], "wip_provider": wip["provider"], "token_audience": wip["token_audience"], "claim_paths": dict(wip["claim_paths"]), "claim_paths_digest": _digest(wip["claim_paths"]), "container_closure": dict(closure), "iam_poststate_digest": approval["iam_poststate_digest"], "live_bindings_digest": approval["live_bindings_digest"], "launch_argv": list(_launch_argv(definition))}


def _validate_bindings(value: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    checked = dict(value)
    _require(checked.get("iam_poststate_digest") == request["iam_poststate_digest"] and checked.get("wip_poststate_digest") == request["live_bindings_digest"], "fresh IAM/WIP binding digest drift")
    _require(checked.get("iam_capability_service_account") == request["service_account"] and checked.get("iam_custom_role") == CUSTOM_ROLE and checked.get("iam_token_creator_role") == "roles/iam.serviceAccountTokenCreator" and checked.get("iam_direct_bucket_access") is False, "fresh IAM binding is not exact")
    _require(checked.get("wip_provider") == request["wip_provider"] and checked.get("token_audience") == request["token_audience"] and checked.get("claim_paths") == request["claim_paths"], "fresh WIP binding is not exact")
    return checked


def _validate_prestate(observed: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(observed)
    _require(value.get("project_id") == request["project_id"] and value.get("zone") == request["zone"] and value.get("vm_name") == request["vm_name"], "VM prestate identity drift")
    _require(value.get("instance_exists") is False and value.get("external_ip") is False, "VM prestate is not the approved absent/no-external-IP state")
    return _validate_bindings(value, request)


def _validate_poststate(observed: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(observed)
    expected = {"project_id": request["project_id"], "zone": request["zone"], "vm_name": request["vm_name"], "instance_exists": True, "machine_type": request["machine_type"], "confidential_compute_type": "SEV", "secure_boot": True, "vtpm": True, "external_ip": False, "image_reference": request["image_reference"], "image_digest": request["image_digest"], "service_account": request["service_account"], "host_mounts": [], "privileged": False, "seccomp": "default-deny-reviewed-profile", "network": "none", "pull": "never"}
    for key, expected_value in expected.items():
        _require(value.get(key) == expected_value, f"VM poststate drift: {key}")
    for key, expected_value in request["container_closure"].items():
        _require(value.get(key) == expected_value, f"container closure drift: {key}")
    return _validate_bindings(value, request)


def _validate_evidence(evidence: VerifierIssuedLauncherEvidence, request: Mapping[str, Any]) -> dict[str, Any]:
    _require(type(evidence) is VerifierIssuedLauncherEvidence, "verifier-issued launcher evidence is required")
    value = dict(evidence.snapshot)
    _closed(value, {"schema", "status", "source", "attestation_verified", "request_digest", "approval_digest", "vm_name", "image_digest", "wip_provider", "token_audience", "iam_poststate_digest", "live_bindings_digest", "policy_digest", "claim_paths_digest", "token_digest", "claims_digest", "nonce_digest", "evidence_digest"}, "launcher evidence")
    _require(evidence._original_digest == _digest(value), "launcher evidence was mutated or resealed")
    _require(value["schema"] == EVIDENCE_SCHEMA and value["status"] == "attested" and value["source"] == "verified_confidential_space_launcher" and value["attestation_verified"] is True, "launcher evidence is not verified")
    for field in ("token_digest", "claims_digest", "nonce_digest"):
        _is_digest(value[field], f"launcher evidence {field}")
    for field in ("request_digest", "approval_digest", "image_digest", "wip_provider", "token_audience", "iam_poststate_digest", "live_bindings_digest", "policy_digest", "claim_paths_digest"):
        expected = {"request_digest": _digest(request), "approval_digest": request["approval_digest"], "image_digest": request["image_digest"], "wip_provider": request["wip_provider"], "token_audience": request["token_audience"], "iam_poststate_digest": request["iam_poststate_digest"], "live_bindings_digest": request["live_bindings_digest"], "policy_digest": request["definition_digest"], "claim_paths_digest": request["claim_paths_digest"]}[field]
        _require(value.get(field) == expected, f"launcher evidence binding drift: {field}")
    _require(value["vm_name"] == request["vm_name"] and value["evidence_digest"] == _digest({key: item for key, item in value.items() if key != "evidence_digest"}), "launcher evidence digest/binding drift")
    return value


def _rollback(backend: ReviewedConfidentialSpaceBackend, request: Mapping[str, Any], *, create_succeeded: bool, create_attempted: bool) -> str:
    if create_succeeded:
        try:
            backend.delete_instance(request)
            _validate_prestate(backend.describe_prestate(request), request)
            return "rolled_back_verified"
        except Exception:
            return "rollback_failed_manual_review"
    if create_attempted:
        try:
            observed = backend.describe_poststate(request)
            exists = observed.get("instance_exists")
            if exists is True:
                backend.delete_instance(request)
                _validate_prestate(backend.describe_prestate(request), request)
                return "rolled_back_verified"
            if exists is False:
                return "not_applicable_no_create"
        except Exception:
            pass
        return "rollback_failed_manual_review"
    return "not_applicable_no_create"


def execute_bootstrap(*, backend: ReviewedConfidentialSpaceBackend, approval_path: Path = DEFAULT_APPROVAL, definition_path: Path = DEFAULT_DEFINITION, ledger_path: Path = DEFAULT_LEDGER, iam_predecessor: VerifiedIAMPredecessor | None = None, iam_ledger_path: Path | None = None, iam_root_verifier: Any = None, iam_packet_digest: str | None = None, iam_prestate_digest: str | None = None, iam_evidence_digest: str | None = None) -> dict[str, Any]:
    definition = _load_json(Path(definition_path), "APPROVAL-021 definition")
    checked = validate_definition(Path(definition_path))
    approval = load_approval(Path(approval_path), definition=definition)
    try:
        if iam_ledger_path is not None:
            _require(iam_root_verifier is not None and all(isinstance(value, str) and value for value in (iam_packet_digest, iam_prestate_digest, iam_evidence_digest)), "trusted IAM root and exact packet/prestate/evidence bindings are required")
            iam_predecessor = load_verified_iam_predecessor(
                ledger_path=Path(iam_ledger_path), operation_id="provision_gcs_only_iam_boundary",
                attempt_id="dispatch082-iam-20260920-a7f4c2d9", trusted_verifier=iam_root_verifier,
                packet_digest=iam_packet_digest, prestate_digest=iam_prestate_digest, evidence_digest=iam_evidence_digest,
            )
        validate_verified_iam_predecessor(iam_predecessor, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9", trusted_verifier=iam_root_verifier, packet_digest=iam_packet_digest, prestate_digest=iam_prestate_digest, evidence_digest=iam_evidence_digest)
    except Exception as exc:
        raise BootstrapBlocked("verified IAM ledger/receipt predecessor is required before VM bootstrap") from exc
    _require(approval["iam_poststate_digest"] == iam_predecessor.poststate_digest, "IAM approval digest does not match verified IAM receipt")
    ledger = AttemptLedger(Path(ledger_path), identity_path=Path(approval_path).with_name(f".{ATTEMPT_ID}.lock"))
    request = _request(definition, approval)
    ledger.reserve(approval["approval_digest"], checked["definition_digest"])
    create_attempted = False
    create_succeeded = False
    phase = "prestate"
    try:
        prestate = _validate_prestate(backend.describe_prestate(request), request)
        phase = "create"
        create_attempted = True
        backend.create_instance(request)
        create_succeeded = True
        phase = "poststate"
        poststate = _validate_poststate(backend.describe_poststate(request), request)
        phase = "launcher_evidence"
        evidence = _validate_evidence(backend.capture_launcher_evidence(request), request)
        receipt = {"schema": "P5R0APPROVAL021ConfidentialSpaceBootstrapReceiptV1", "operation_id": OPERATION_ID, "attempt_id": ATTEMPT_ID, "definition_digest": checked["definition_digest"], "approval_digest": approval["approval_digest"], "prestate_digest": _digest(prestate), "poststate_digest": _digest(poststate), "iam_poststate_digest": request["iam_poststate_digest"], "iam_receipt_digest": iam_predecessor.receipt_digest, "iam_ledger_head_digest": iam_predecessor.ledger_head_digest, "live_bindings_digest": request["live_bindings_digest"], "launcher_evidence_digest": evidence["evidence_digest"], "rollback_status": "not_required_verified", "attestation_claimed": True}
        receipt["receipt_digest"] = _digest(receipt)
        ledger.close("verified", approval_digest=approval["approval_digest"], definition_digest=checked["definition_digest"], receipt_digest=receipt["receipt_digest"], phase=phase, rollback_status="not_required_verified", attestation_claimed=True)
        return {"status": "verified", "receipt": receipt, "future_launch_command": list(_launch_argv(definition))}
    except Exception as exc:
        rollback_status = _rollback(backend, request, create_succeeded=create_succeeded, create_attempted=create_attempted)
        ledger.close("failed_closed", approval_digest=approval["approval_digest"], definition_digest=checked["definition_digest"], failed_phase=phase, error_type=type(exc).__name__, rollback_status=rollback_status, attestation_claimed=False)
        return {"status": "failed_closed", "failed_phase": phase, "rollback_status": rollback_status, "attestation_claimed": False}


def future_launch_command(definition_path: Path = DEFAULT_DEFINITION) -> tuple[str, ...]:
    definition = _load_json(Path(definition_path), "APPROVAL-021 definition")
    validate_definition(Path(definition_path))
    return _launch_argv(definition)


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local-only APPROVAL-021 Confidential Space bootstrap definition")
    parser.add_argument("command", choices=("validate", "render", "apply"))
    parser.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args(argv)
    if args.command == "validate":
        print(json.dumps(validate_definition(args.definition), sort_keys=True))
        return 0
    if args.command == "render":
        print(json.dumps({"metadata": render_metadata(args.definition), "launch_argv": list(future_launch_command(args.definition)), "mutations_performed": False, "cloud_operations": []}, sort_keys=True))
        return 0
    raise BootstrapBlocked("effectful apply requires an explicitly injected reviewed backend; this CLI never launches a VM")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = ["APPROVAL_ID", "APPROVAL_SCHEMA", "ATTEMPT_ID", "BootstrapBlocked", "BootstrapError", "CAPABILITY_SERVICE_ACCOUNT", "CUSTOM_ROLE", "DEFAULT_APPROVAL", "DEFAULT_DEFINITION", "DEFAULT_LEDGER", "EXPECTED_CLAIM_PATHS", "IMAGE_DIGEST", "IMAGE_REFERENCE", "OPERATION_ID", "ReviewedConfidentialSpaceBackend", "VerifierIssuedLauncherEvidence", "VerifierOwnedLauncherEvidenceSource", "VMBackend", "execute_bootstrap", "future_launch_command", "load_approval", "render_metadata", "validate_definition"]
