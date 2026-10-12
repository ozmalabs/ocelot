"""Local-only RS-063 signed-environment execution request.

This module validates a canonical request that binds the frozen RS-062
artifact index and unsigned KMS lock-signing request to the existing RS-040
native closure, RS-060 bundle contract, and deployment renderer.  It never
calls cloud APIs, KMS, GCS, Confidential Space, FreeTSA, a supervisor, or a
task runner.  The checked-in request is intentionally blocked pending master
approval and reviewed controlled-run/environment bindings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from evaluation.p5_r0.diagnostic_generator import (
    DEFAULT_SEED,
    DEFAULT_SPLIT_SEED,
    GENERATOR_VERSION,
    build_diagnostic_artifacts,
)
from services.p5_r0_evaluator.deploy.definition import (
    DEFAULT_DEFINITION as RS040_DEFINITION,
    validate_definition as validate_rs040_definition,
    load_definition as load_rs040_definition,
)
from services.p5_r0_evaluator.deploy.bundle_definition import (
    DEFAULT_DEFINITION as RS060_DEFINITION,
    validate_bundle_definition as validate_rs060_definition,
    load_definition as load_rs060_definition,
)
from services.p5_r0_evaluator.deployments import render_deployment


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEFINITION = Path(__file__).with_name("p5-r0-signed-environment-execution-request.json")
digest = sha256
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_FORBIDDEN_MUTATIONS = {
    "gcloud mutation",
    "VM creation",
    "KMS signing",
    "GCS upload",
    "secret access",
    "FreeTSA call",
    "task submission",
    "deployment",
}
_EXPECTED_SOURCE_PATHS = {
    "canonical_protocol": "evaluation/p0a/canonical.py",
    "deployment_renderer": "services/p5_r0_evaluator/deployments.py",
    "diagnostic_domain_cards": "evaluation/p5_r0/domain_cards.py",
    "diagnostic_fixture_generator": "evaluation/p5_r0/fixture_generator.py",
    "diagnostic_generator": "evaluation/p5_r0/diagnostic_generator.py",
    "diagnostic_mechanics": "evaluation/p5_r0/mechanics.py",
    "diagnostic_protocol": "evaluation/p5_r0/protocol.py",
    "diagnostic_repair": "evaluation/p5_r0/repair.py",
    "diagnostic_split": "evaluation/p5_r0/split.py",
    "native_closure_builder": "evaluation/p5_r0/rebuild.py",
    "native_closure_spec": "evaluation/p5_r0/native.py",
    "native_containerfile": "evaluation/p5_r0/Containerfile.v3",
    "native_evaluator": "evaluation/p5_r0/evaluator.py",
    "native_receipts": "evaluation/p5_r0/receipts.py",
    "native_rollback": "evaluation/p5_r0/rollback.py",
    "native_runner": "evaluation/p5_r0/runner.py",
    "native_supervisor": "evaluation/p0a/supervisor.py",
    "native_worker": "evaluation/p5_r0/native_worker.py",
    "native_worker_entrypoint": "evaluation/p5_r0/native_worker_entrypoint_v3.py",
    "request_authority_client": "services/p5_r0_evaluator/client.py",
    "request_validator": "services/p5_r0_evaluator/deploy/execution_request.py",
    "rs040_definition": "services/p5_r0_evaluator/deploy/p5-r0-native-deployment.json",
    "rs040_validator": "services/p5_r0_evaluator/deploy/definition.py",
    "rs060_definition": "services/p5_r0_evaluator/deploy/p5-r0-production-bundle.json",
    "rs060_production_runner": "services/p5_r0_evaluator/production_runner.py",
    "rs060_validator": "services/p5_r0_evaluator/deploy/bundle_definition.py",
}
_DIAGNOSTIC_ARTIFACT_PATHS = {
    "split": "public/split.json",
    "manifest": "public/manifest.json",
    "private_store": "private-truth/case-store.json",
    "worker_contract": "public/worker-contract.json",
    "evaluator_contract": "public/evaluator-contract.json",
    "policy": "public/policy.json",
    "task_set": "public/task-set.json",
    "control_commitment": "public/control-commitment.json",
    "lock_signing_request": "public/lock-signing-request.json",
    "bundle_input_manifest": "public/production-bundle-input-manifest.json",
    "provenance": "public/generator-provenance.json",
}
_DIAGNOSTIC_SELF_DIGEST_FIELDS = {
    "split": "split_digest",
    "manifest": "manifest_digest",
    "private_store": "store_digest",
    "worker_contract": "digest",
    "evaluator_contract": "digest",
    "policy": None,
    "task_set": "task_set_digest",
    "control_commitment": "commitment_digest",
    "lock_signing_request": "request_digest",
    "bundle_input_manifest": "manifest_digest",
    "provenance": None,
}
_REQUIRED_NULL_PATHS = (
    "target_environment.image.reference",
    "target_environment.image.digest",
    "target_environment.base_image_digest",
    "target_environment.runtime_digest",
    "target_environment.resource_profile_digest",
    "target_environment.seccomp_digest",
    "target_environment.allowed_syscalls_digest",
    "target_environment.closure_digest",
    "kms_lock_signing.key_version",
    "kms_lock_signing.authority_binding_digest",
    "iam_wip_bridge_commitments.project_id",
    "iam_wip_bridge_commitments.project_number",
    "iam_wip_bridge_commitments.wip_provider",
    "iam_wip_bridge_commitments.capability_service_account",
    "iam_wip_bridge_commitments.gcs_service_account",
    "iam_wip_bridge_commitments.kms_service_account",
    "iam_wip_bridge_commitments.bridge_endpoint",
    "iam_wip_bridge_commitments.bridge_service_account",
    "iam_wip_bridge_commitments.bridge_audience",
    "ingestion_plan.destination.bucket",
    "ingestion_plan.destination.prefix",
)


class ExecutionRequestValidationError(ValueError):
    """The RS-063 request or one of its local inputs is malformed."""


class ExecutionRequestBlockedError(ExecutionRequestValidationError):
    """The request is valid but approval or production inputs are absent."""


@dataclass(frozen=True)
class ExecutionRequestReport:
    ready: bool
    status: str
    missing_preconditions: tuple[str, ...]
    definition_digest: str
    artifact_digests: tuple[tuple[str, str], ...]
    cloud_operations: tuple[str, ...]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutionRequestValidationError(message)


def _is_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} is not a sha256 digest")
    return value


def _path(value: Mapping[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ExecutionRequestValidationError(f"missing required field: {dotted}")
        current = current[part]
    return current


def _resolve_candidate(repository_root: Path, value: Any, label: str) -> Path:
    _require(isinstance(value, str) and value and not Path(value).is_absolute(), f"{label} must be repository-relative")
    root = repository_root.resolve()
    resolved = (root / value).resolve()
    _require(root in resolved.parents, f"{label} escapes the repository: {value}")
    return resolved


def _resolve(repository_root: Path, value: Any, label: str) -> Path:
    resolved = _resolve_candidate(repository_root, value, label)
    _require(resolved.is_file(), f"{label} is missing: {value}")
    return resolved


def _load_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        return parse_canonical(path.read_bytes())
    except Exception as exc:
        raise ExecutionRequestValidationError(f"{label} is not canonical JSON") from exc


def _validate_sources(definition: Mapping[str, Any], repository_root: Path) -> None:
    sources = definition.get("source_files")
    digests = definition.get("source_verification_digests")
    _require(isinstance(sources, Mapping) and dict(sources) == _EXPECTED_SOURCE_PATHS, "source file map drift")
    _require(isinstance(digests, Mapping) and set(digests) == set(_EXPECTED_SOURCE_PATHS), "source digest map is missing or not closed")
    for key, relative in _EXPECTED_SOURCE_PATHS.items():
        path = _resolve(repository_root, relative, f"source_files.{key}")
        _require(digests.get(key) == sha256(path.read_bytes()), f"source content drift: {key}")
        _is_digest(digests.get(key), f"source_digests.{key}")
    _require(sources.get("rs040_definition") == _EXPECTED_SOURCE_PATHS["rs040_definition"], "RS-040 source drift")
    _require(sources.get("rs060_definition") == _EXPECTED_SOURCE_PATHS["rs060_definition"], "RS-060 source drift")
    _require(sources.get("deployment_renderer") == _EXPECTED_SOURCE_PATHS["deployment_renderer"], "deployment renderer source drift")
    _require(callable(render_deployment), "deployment renderer is unavailable")
    rs040 = load_rs040_definition(repository_root / sources["rs040_definition"])
    rs040_report = validate_rs040_definition(rs040, repository_root=repository_root)
    _require(not rs040_report.ready, "RS-040 unexpectedly claims production readiness")
    rs060 = load_rs060_definition(repository_root / sources["rs060_definition"])
    rs060_report = validate_rs060_definition(rs060, repository_root=repository_root)
    _require(not rs060_report.ready, "RS-060 unexpectedly claims production readiness")


def _reproducible_diagnostic_index(artifacts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for name, relative in _DIAGNOSTIC_ARTIFACT_PATHS.items():
        value = artifacts[name]
        file_digest = sha256(canonical_bytes(dict(value)))
        self_digest_field = _DIAGNOSTIC_SELF_DIGEST_FIELDS[name]
        records[name] = {
            "path": "var/p5-r0-diagnostic-inputs/" + relative,
            "digest": value.get(self_digest_field) if self_digest_field else file_digest,
            "file_digest": file_digest,
            "private": name == "private_store",
        }
    index: dict[str, Any] = {
        "schema": "P5R0DiagnosticArtifactIndexV1",
        "classification": "diagnostic_generated_non_release",
        "root": "var/p5-r0-diagnostic-inputs",
        "private_truth_path": "private-truth/case-store.json",
        "artifacts": records,
        "private_truth": {"worker_public_output": False, "disposable_var_only": True},
        "production_outputs_created": False,
        "cloud_operations": [],
        "claim_boundary": "Artifact inventory only; no signed execution evidence.",
    }
    index["manifest_digest"] = artifacts["manifest"]["manifest_digest"]
    index["private_store_digest"] = artifacts["private_store"]["store_digest"]
    index["task_set_digest"] = artifacts["task_set"]["task_set_digest"]
    index["control_commitment_digest"] = artifacts["control_commitment"]["commitment_digest"]
    index["unsigned_lock_digest"] = artifacts["lock_signing_request"]["unsigned_lock_digest"]
    index["index_digest"] = digest(index)
    return index


def _validate_generation_contract(definition: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    generation = definition.get("diagnostic_generation")
    _require(isinstance(generation, Mapping), "diagnostic generation contract is missing")
    _require(generation.get("generator") == "evaluation.p5_r0.diagnostic_generator.build_diagnostic_artifacts", "diagnostic generator binding drift")
    _require(generation.get("version") == GENERATOR_VERSION, "diagnostic generator version drift")
    _require(generation.get("seed") == DEFAULT_SEED and generation.get("split_seed") == DEFAULT_SPLIT_SEED, "diagnostic generator seed drift")
    _require(generation.get("output_root") == "var/p5-r0-diagnostic-inputs", "diagnostic output root drift")
    _require(generation.get("private_truth") == "generated in memory or disposable var only; never committed", "private truth custody drift")
    artifacts = build_diagnostic_artifacts(seed=generation["seed"], split_seed=generation["split_seed"])
    expected_index = _reproducible_diagnostic_index(artifacts)
    commitments = generation.get("expected_commitments")
    _require(commitments == {
        "manifest_digest": expected_index["manifest_digest"],
        "private_store_digest": expected_index["private_store_digest"],
        "task_set_digest": expected_index["task_set_digest"],
        "control_commitment_digest": expected_index["control_commitment_digest"],
        "unsigned_lock_digest": expected_index["unsigned_lock_digest"],
        "index_digest": expected_index["index_digest"],
    }, "diagnostic generated commitments drift")
    return artifacts, expected_index


def _validate_authority_contract(definition: Mapping[str, Any], artifacts: Mapping[str, Mapping[str, Any]]) -> None:
    contract = definition.get("authority_contract")
    _require(contract == {
        "authority_mode": "self_custodied_diagnostic",
        "external_authority_required": True,
        "external_authority_semantics": "supplied trust-binding gate, not an independent evaluator requirement",
        "independent_evaluator_required": False,
        "signed_confidential_space_execution_required": True,
    }, "authority mode or policy semantics drift")
    _require(artifacts["control_commitment"].get("authorization") == "self_custodied_diagnostic_authorization", "generated authority mode drift")
    _require(artifacts["policy"].get("external_authority_required") is True, "inherited external-authority gate drift")


def _validate_artifacts(definition: Mapping[str, Any], repository_root: Path) -> tuple[tuple[str, str], ...]:
    generated, expected_index = _validate_generation_contract(definition)
    _validate_authority_contract(definition, generated)
    index_path = _resolve_candidate(repository_root, definition["input_locations"]["artifact_index"], "input_locations.artifact_index")
    index = _load_canonical(index_path, "artifact index") if index_path.is_file() else expected_index
    _require(index == expected_index, "artifact index is not reproducible from the committed generator contract")
    _require(index.get("schema") == "P5R0DiagnosticArtifactIndexV1", "artifact index schema drift")
    _require(index.get("classification") == "diagnostic_generated_non_release", "artifact index classification drift")
    _require(index.get("production_outputs_created") is False and index.get("cloud_operations") == [], "artifact index release boundary drift")
    _require(index.get("root") == "var/p5-r0-diagnostic-inputs", "artifact index root drift")
    _require(index.get("index_digest") == digest({key: value for key, value in index.items() if key != "index_digest"}), "artifact index digest mismatch")

    artifacts = index.get("artifacts")
    _require(isinstance(artifacts, Mapping), "artifact index artifact map is missing")
    expected_bindings = definition.get("artifact_bindings")
    _require(expected_bindings == artifacts, "artifact bindings drift from generated index")
    object_plan = definition.get("ingestion_plan", {}).get("objects")
    _require(isinstance(object_plan, list), "GCS object plan is missing")
    planned = {item.get("name"): item for item in object_plan if isinstance(item, Mapping)}
    _require(set(planned) == set(artifacts), "GCS object plan names drift from generated index")
    for name, record in artifacts.items():
        item = planned[name]
        _require(item.get("local_path") == record.get("path") and item.get("digest") == record.get("digest") and item.get("file_digest") == record.get("file_digest") and item.get("private") == record.get("private"), f"GCS object binding drift: {name}")
        _require(item.get("object_suffix") == record.get("path").split("var/p5-r0-diagnostic-inputs/", 1)[-1], f"GCS object suffix drift: {name}")
    commitments = definition.get("generated_commitments")
    _require(isinstance(commitments, Mapping), "generated commitments are missing")
    for key in ("manifest_digest", "private_store_digest", "task_set_digest", "control_commitment_digest", "unsigned_lock_digest", "index_digest"):
        _require(commitments.get(key) == index.get(key), f"generated commitment drift: {key}")

    checked: list[tuple[str, str]] = [("artifact-index", index["index_digest"])]
    for name, record in artifacts.items():
        _require(isinstance(record, Mapping), f"artifact record is malformed: {name}")
        artifact_path = _resolve_candidate(repository_root, record.get("path"), f"artifact_bindings.{name}.path")
        raw_digest = sha256(artifact_path.read_bytes()) if artifact_path.is_file() else record.get("file_digest")
        _require(raw_digest == record.get("file_digest"), f"artifact file digest mismatch: {name}")
        _is_digest(record.get("digest"), f"artifact digest: {name}")
        _require(record == expected_index["artifacts"][name], f"generated artifact commitment drift: {name}")
        checked.append((name, record["digest"]))

    request_path = _resolve_candidate(repository_root, definition["input_locations"]["lock_signing_request"], "input_locations.lock_signing_request")
    request = _load_canonical(request_path, "KMS lock-signing request") if request_path.is_file() else generated["lock_signing_request"]
    _require(request.get("schema") == "P5R0KMSLockSigningRequestV1", "KMS request schema drift")
    _require(request.get("classification") == "diagnostic_unsigned_non_release", "KMS request classification drift")
    _require(request.get("status") == "pending_reviewed_authority_and_kms", "KMS request status drift")
    _require(request.get("non_release") is True, "KMS request must be non-release")
    unsigned = request.get("unsigned_lock")
    _require(isinstance(unsigned, Mapping), "unsigned lock is missing")
    _require(unsigned.get("signature") is None and unsigned.get("authority_digest") is None and unsigned.get("kms_authority_binding_digest") is None, "unsigned lock contains production authority material")
    expected_unsigned_digest = sha256({key: value for key, value in unsigned.items() if key not in {"lock_digest", "signature"}})
    _require(unsigned.get("lock_digest") == expected_unsigned_digest, "unsigned lock digest mismatch")
    _require(request.get("unsigned_lock_digest") == unsigned.get("lock_digest"), "unsigned lock commitment drift")
    _require(request.get("kms") == {
        "required": True,
        "operation": "sign_exact_lock_digest_in_reviewed_signed_environment",
        "key_version": None,
        "authority_binding_digest": None,
        "signature_present": False,
    }, "KMS request operation must remain unsigned")
    _require(request.get("production_signature_created") is False and request.get("cloud_operations") == [], "KMS request release boundary drift")
    _require(artifacts["lock_signing_request"]["digest"] == request["request_digest"], "KMS request artifact digest drift")
    if request_path.is_file():
        _require(artifacts["lock_signing_request"]["file_digest"] == sha256(request_path.read_bytes()), "KMS request file digest drift")
    else:
        _require(request == generated["lock_signing_request"], "generated KMS request commitment drift")
    _require(commitments["unsigned_lock_digest"] == request["unsigned_lock_digest"], "unsigned lock generated commitment drift")
    return tuple(sorted(checked))


def _validate_static(definition: Mapping[str, Any], repository_root: Path) -> None:
    expected_fields = {
        "schema", "classification", "status", "master_run", "runsheet_item", "canonical_digest",
        "source_files", "source_verification_digests", "input_locations", "artifact_bindings", "generated_commitments", "diagnostic_generation", "authority_contract", "target_environment", "kms_lock_signing", "ingestion_plan",
        "iam_wip_bridge_commitments", "run_order", "preconditions", "commands", "apply_plan",
        "claim_boundary",
    }
    _require(set(definition) == expected_fields, "execution request fields are not closed")
    _require(definition.get("schema") == "P5R0SignedEnvironmentExecutionRequestV1", "execution request schema drift")
    _require(definition.get("classification") == "repository_definition_only", "execution request classification drift")
    _require(definition.get("status") == "blocked_pending_approval", "execution request must remain blocked_pending_approval")
    _require(definition.get("master_run") == "P5-MASTER-001" and definition.get("runsheet_item") == "RS-063", "run identity drift")
    _require(definition.get("canonical_digest") == {"algorithm": "sha256", "encoding": "canonical-json", "implementation": "evaluation.p0a.canonical.digest"}, "canonical digest contract drift")
    _validate_sources(definition, repository_root)

    locations = definition.get("input_locations")
    _require(locations == {
        "artifact_index": "var/p5-r0-diagnostic-inputs/artifact-index.json",
        "lock_signing_request": "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json",
    }, "execution input locations drift")
    for path in locations.values():
        _require(isinstance(path, str) and not Path(path).is_absolute(), "execution input path must be relative")

    target = definition.get("target_environment")
    _require(isinstance(target, Mapping), "target environment is missing")
    _require(target.get("kind") == "Confidential Space", "target environment kind drift")
    _require(target.get("renderer") == "services.p5_r0_evaluator.deployments.render_deployment", "renderer binding drift")
    _require(target.get("native_definition") == "services/p5_r0_evaluator/deploy/p5-r0-native-deployment.json", "native definition binding drift")
    _require(target.get("image") == {"reference": None, "digest": None, "repository": "p5-cs", "required_inputs": ["reviewed RS-040 image reference", "reviewed RS-040 image digest"]}, "target image must remain unresolved with the reviewed repository")
    _require(target.get("base_image_digest") is None and target.get("runtime_digest") is None and target.get("resource_profile_digest") is None, "target production digests must remain unresolved")
    _require(target.get("seccomp_digest") is None and target.get("allowed_syscalls_digest") is None and target.get("closure_digest") is None, "target closure digests must remain unresolved")
    closure = target.get("closure_contract")
    _require(closure == {
        "runtime": {"name": "crun", "path": "/usr/bin/crun"},
        "execution": {"network": "none", "pull": "never", "entrypoint": "/runtime/p5_r0_worker", "user": "65532:65532", "filesystem": "read-only", "capabilities": "drop-all", "no_new_privileges": True, "namespaces": ["pid=private", "ipc=private", "uts=private"]},
        "resource_profile": {"steps": 8, "frame_bytes": 65536, "wall_seconds": 3, "memory_mb": 512, "cpu": 1, "pids": 32},
        "seccomp": {"profile_path": "/usr/share/containers/seccomp.json", "default_action": "SCMP_ACT_ERRNO"},
        "host_closure_definition": "services/p5_r0_evaluator/deploy/p5-r0-native-deployment.json",
        "digests_required_from_reviewed_RS-040": ["runtime_digest", "resource_profile_digest", "seccomp_digest", "allowed_syscalls_digest", "closure_digest", "host_digests", "argv_digest"],
    }, "closure contract drift")

    kms = definition.get("kms_lock_signing")
    _require(kms == {
        "request_only": True,
        "operation": "sign_exact_lock_digest_in_reviewed_signed_environment",
        "request_path": "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json",
        "unsigned_lock_digest": "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df",
        "key_version": None,
        "authority_binding_digest": None,
        "signature": None,
        "signature_present": False,
        "kms_call_performed": False,
    }, "KMS signing operation must be request-only")

    ingestion = definition.get("ingestion_plan")
    _require(isinstance(ingestion, Mapping), "ingestion plan is missing")
    _require(ingestion.get("mode") == "review_only_no_upload", "ingestion plan must be review-only")
    _require(ingestion.get("destination") == {"type": "gcs_object_boundary", "bucket": None, "prefix": None, "required_inputs": ["reviewed GCS bucket", "reviewed object prefix"]}, "GCS destination must remain unresolved")
    _require(ingestion.get("upload_performed") is False and ingestion.get("durable_ingestion_verified") is False, "GCS ingestion must not have occurred")
    _require(isinstance(ingestion.get("objects"), list) and len(ingestion["objects"]) == 11, "GCS object plan must cover every generated artifact")
    _require(ingestion.get("private_truth_boundary") == {"source": "private-truth/case-store.json", "object_visibility": "private", "worker_public_output": False, "durable_store_required": True}, "private truth boundary drift")

    commitments = definition.get("iam_wip_bridge_commitments")
    _require(isinstance(commitments, Mapping), "IAM/WIP/bridge commitments are missing")
    for dotted in _REQUIRED_NULL_PATHS:
        _require(_path(definition, dotted) is None, f"production value must remain null: {dotted}")
    _require(commitments.get("required") is True and commitments.get("reviewed") is False, "IAM commitments must remain unreviewed")
    _require(commitments.get("fixed_contracts") == {"issuer": "https://confidentialcomputing.googleapis.com", "attestation_audience": "https://sts.googleapis.com", "tee": "CONFIDENTIAL_SPACE", "hardware_model": "GCP_AMD_SEV", "secure_boot": True, "workload": "evaluator", "confidential_space_smoke": False}, "fixed Confidential Space contract drift")
    _require(commitments.get("bridge_call_performed") is False and commitments.get("wip_condition_verified") is False and commitments.get("iam_grants_verified") is False, "IAM/WIP/bridge evidence must be absent")

    run_order = definition.get("run_order")
    _require(isinstance(run_order, list) and [step.get("id") for step in run_order] == ["validate_inputs", "master_approval", "complete_reviewed_bindings", "render_local_artifacts", "approve_kms_request", "kms_sign", "durable_gcs_ingestion", "confidential_space_activation", "supervisor_execution", "task_execution", "evidence_seal"], "run order drift")
    for step in run_order:
        _require(isinstance(step.get("mutating"), bool) and step.get("enabled") is False, f"run-order step must be disabled: {step.get('id')}")
    _require(definition.get("preconditions") == {
        "artifact_index_digest_verified": True,
        "unsigned_kms_request_digest_verified": True,
        "reviewed_RS040_inputs": False,
        "reviewed_RS060_inputs": False,
        "reviewed_deployment_policy": False,
        "reviewed_authority_and_kms_binding": False,
        "master_approval": False,
        "real_kms_signature": False,
        "durable_gcs_ingestion": False,
        "confidential_space_activation": False,
        "authenticated_supervisor_evidence": False,
        "task_execution": False,
    }, "precondition state drift")

    commands = definition.get("commands")
    _require(commands == {
        "validate": "PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request validate --allow-blocked",
        "audit": "PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request audit --allow-blocked --output var/p5-r0-rs063-execution-request-audit.json",
    }, "local command contract drift")
    apply_plan = definition.get("apply_plan")
    _require(isinstance(apply_plan, Mapping), "apply plan is missing")
    _require(apply_plan.get("mode") == "review_only_no_execution" and apply_plan.get("commands") == [] and apply_plan.get("approval_required") is True and apply_plan.get("mutations_performed") is False, "apply plan is executable")
    forbidden = apply_plan.get("forbidden_operations")
    _require(isinstance(forbidden, list) and _FORBIDDEN_MUTATIONS.issubset(forbidden), "forbidden-operation boundary drift")
    _require(definition.get("claim_boundary") == "Local RS-063 request only; no KMS signature, durable ingestion, Confidential Space activation, supervisor evidence, task execution, production authority, or result claim.", "claim boundary drift")


def load_definition(path: Path = DEFAULT_DEFINITION) -> dict[str, Any]:
    try:
        return parse_canonical(Path(path).read_bytes())
    except Exception as exc:
        raise ExecutionRequestValidationError("execution request cannot be loaded as canonical JSON") from exc


def validate_execution_request(definition: Mapping[str, Any], *, repository_root: Path = REPOSITORY_ROOT, require_approval: bool = False) -> ExecutionRequestReport:
    _validate_static(definition, Path(repository_root).resolve())
    checked = _validate_artifacts(definition, Path(repository_root).resolve())
    missing = tuple(key for key, value in definition["preconditions"].items() if value is False)
    report = ExecutionRequestReport(
        ready=False,
        status="blocked_pending_approval",
        missing_preconditions=missing,
        definition_digest=digest(dict(definition)),
        artifact_digests=checked,
        cloud_operations=(),
    )
    if require_approval:
        raise ExecutionRequestBlockedError("RS-063 remains blocked_pending_approval: " + ", ".join(missing))
    return report


def _audit_payload(report: ExecutionRequestReport) -> dict[str, Any]:
    return {
        "schema": "P5R0SignedEnvironmentExecutionRequestAuditV1",
        "status": report.status,
        "ready": report.ready,
        "missing_preconditions": list(report.missing_preconditions),
        "definition_digest": report.definition_digest,
        "artifact_digests": dict(report.artifact_digests),
        "cloud_operations": list(report.cloud_operations),
        "mutations_performed": False,
        "claim_boundary": "No KMS signature, durable ingestion, Confidential Space activation, supervisor evidence, task execution, production authority, or result claim exists.",
    }


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate the local-only RS-063 signed-environment execution request")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "audit"):
        command = subparsers.add_parser(name)
        command.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
        command.add_argument("--allow-blocked", action="store_true")
    subparsers.choices["audit"].add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        definition = load_definition(args.definition)
        report = validate_execution_request(definition, require_approval=not args.allow_blocked)
        payload = _audit_payload(report)
        if args.command == "audit":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(canonical_bytes(payload))
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 0 if args.allow_blocked else 2
    except (ExecutionRequestValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"RS-063 validation blocked: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    return _cli(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
