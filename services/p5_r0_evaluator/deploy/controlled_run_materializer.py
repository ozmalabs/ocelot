"""Materialize a deterministic, review-only controlled-run manifest.

This module consumes already-generated local review inputs only.  It never
creates signatures, invokes KMS/gcloud/GCS/FreeTSA, uploads, deploys, starts a
supervisor, or executes tasks.  The resulting manifest is a commitment and
pending-work record; it is not a run authorization or execution receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.authority_binding_proposal import validate_proposal
from services.p5_r0_evaluator.deploy.execution_request import (
    load_definition as load_execution_request,
    validate_execution_request,
)
from services.p5_r0_evaluator.deploy.rs069_change_plan import (
    load_plan,
    validate_plan,
)
from services.p5_r0_evaluator.input_builder import validate_input_builder_binding
from services.p5_r0_evaluator.time_seed import time_seed_algorithm_binding

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATED_ROOT = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs"
DEFAULT_RS063 = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json"
DEFAULT_RS068 = DEFAULT_GENERATED_ROOT / "public/rs-068-authority-binding-proposal.json"
DEFAULT_RS069 = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "var/p5-r0-controlled-run/manifest.json"
DEFAULT_CLOSURES = (
    REPOSITORY_ROOT / "var/p5-r0-v3-local-preflight-audit/closure-status.json",
    REPOSITORY_ROOT / "var/p5-r0-v3-complete-local/closure-status.json",
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXPECTED_GENERATOR = {
    "version": "P5R0DiagnosticInputGeneratorV1",
    "seed": "p5-r0-diagnostic-seed-v1",
    "split_seed": "p5-r0-v2",
}
_EXPECTED_GENERATOR_NAME = "evaluation.p5_r0.diagnostic_generator.build_diagnostic_artifacts"
_FORBIDDEN_OPERATIONS = (
    "signature_generation",
    "kms_call",
    "gcloud_call",
    "gcs_upload",
    "freetsa_call",
    "deployment",
    "supervisor_invocation",
    "task_execution",
)


class ControlledRunMaterializationError(ValueError):
    """A local input is malformed, drifted, or crosses the review boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlledRunMaterializationError(message)


def _is_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} is not a sha256 digest")
    return value


def _raw_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical(path.read_bytes())
    except Exception as exc:
        raise ControlledRunMaterializationError(f"{label} is not canonical JSON") from exc
    return value


def _resolve(root: Path, relative: str, label: str) -> Path:
    _require(isinstance(relative, str) and not Path(relative).is_absolute(), f"{label} must be repository-relative")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative).resolve()
    _require(resolved_root in resolved.parents, f"{label} escapes the repository")
    _require(resolved.is_file(), f"{label} is missing: {relative}")
    return resolved


def validate_generator_provenance(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return the exact generator/seed/split provenance."""
    generator = provenance.get("generator")
    _require(generator == _EXPECTED_GENERATOR, "generator or seed algorithm drift")
    _require(provenance.get("schema") == "P5R0DiagnosticGeneratorProvenanceV1", "generator provenance schema drift")
    _require(provenance.get("runsheet_item") == "RS-062", "generator provenance runsheet drift")
    _require(provenance.get("claim_boundary") == "Generation is not signed-environment execution evidence.", "generator claim boundary drift")
    _require(provenance.get("diagnostic_signer") == "deterministic domain-card fixture signer only; not production authority or KMS", "diagnostic signer boundary drift")
    for field in ("manifest_digest", "private_store_digest", "task_set_digest", "unsigned_lock_digest", "control_commitment_digest", "input_builder_source_digest", "time_seed_algorithm_source_digest"):
        _is_digest(provenance.get(field), f"provenance.{field}")
    try:
        builder = validate_input_builder_binding(provenance.get("input_builder_binding"), REPOSITORY_ROOT)
        algorithm = time_seed_algorithm_binding(REPOSITORY_ROOT)
    except Exception as exc:
        raise ControlledRunMaterializationError("source identity commitment drift") from exc
    _require(provenance.get("input_builder_source_digest") == builder["source_digest"], "input-builder source digest drift")
    _require(provenance.get("time_seed_algorithm_binding") == algorithm, "source identity commitment drift: time-seed algorithm binding")
    _require(provenance.get("time_seed_algorithm_source_digest") == algorithm["source_digest"], "time-seed algorithm source digest drift")
    return {
        "generator": {"name": _EXPECTED_GENERATOR_NAME, **dict(generator)},
        "provenance_digest": None,
        "source_schema": provenance["schema"],
        "runsheet_item": provenance["runsheet_item"],
        "diagnostic_signer": provenance["diagnostic_signer"],
        "manifest_digest": provenance["manifest_digest"],
        "private_store_digest": provenance["private_store_digest"],
        "task_set_digest": provenance["task_set_digest"],
        "control_commitment_digest": provenance["control_commitment_digest"],
        "unsigned_lock_digest": provenance["unsigned_lock_digest"],
        "input_builder_binding": builder,
        "time_seed_algorithm_binding": algorithm,
        "input_builder_source_digest": provenance["input_builder_source_digest"],
        "time_seed_algorithm_source_digest": provenance["time_seed_algorithm_source_digest"],
    }


def validate_artifact_commitments(index: Mapping[str, Any], generated_root: Path) -> dict[str, Any]:
    """Recompute every generated artifact's raw digest and validate index bindings."""
    _require(index.get("schema") == "P5R0DiagnosticArtifactIndexV1", "artifact index schema drift")
    _require(index.get("production_outputs_created") is False and index.get("cloud_operations") == [], "artifact index crosses execution boundary")
    artifacts = index.get("artifacts")
    _require(isinstance(artifacts, Mapping) and artifacts, "artifact index is empty")
    expected_index_digest = sha256({key: value for key, value in index.items() if key != "index_digest"})
    _require(index.get("index_digest") == expected_index_digest, "artifact index digest drift")
    result: dict[str, Any] = {}
    for name, record in artifacts.items():
        _require(isinstance(record, Mapping), f"artifact record is malformed: {name}")
        path_text = record.get("path")
        _require(isinstance(path_text, str) and path_text.startswith("var/p5-r0-diagnostic-inputs/"), f"artifact path drift: {name}")
        relative = path_text.split("var/p5-r0-diagnostic-inputs/", 1)[1]
        path = _resolve(generated_root.parent.parent, path_text, f"artifact {name}")
        actual_file_digest = _raw_digest(path)
        _require(actual_file_digest == record.get("file_digest"), f"artifact digest drift: {name}")
        _is_digest(record.get("digest"), f"artifact semantic digest: {name}")
        _require(record.get("private") is ("private-truth/" in relative), f"artifact custody drift: {name}")
        result[name] = {
            "path": path_text,
            "semantic_digest": record["digest"],
            "file_digest": actual_file_digest,
            "private": record["private"],
        }
    for field in ("manifest_digest", "private_store_digest", "task_set_digest", "control_commitment_digest", "unsigned_lock_digest"):
        _is_digest(index.get(field), f"artifact index.{field}")
    _require(index["manifest_digest"] == artifacts["manifest"]["digest"], "manifest commitment drift")
    _require(index["private_store_digest"] == artifacts["private_store"]["digest"], "private store commitment drift")
    _require(index["task_set_digest"] == artifacts["task_set"]["digest"], "task-set commitment drift")
    _require(index["control_commitment_digest"] == artifacts["control_commitment"]["digest"], "control commitment drift")
    lock_request = _load(
        _resolve(generated_root.parent.parent, artifacts["lock_signing_request"]["path"], "lock-signing request"),
        "lock-signing request",
    )
    _require(index["unsigned_lock_digest"] == lock_request.get("unsigned_lock_digest"), "unsigned lock commitment drift")
    return result


def validate_closure_commitments(observations: Sequence[Mapping[str, Any]], repository_root: Path) -> list[dict[str, Any]]:
    """Validate RS-064 workspace-only closure observations and raw file digests."""
    _require(observations and isinstance(observations, Sequence), "RS-064 closure observations are missing")
    result: list[dict[str, Any]] = []
    for number, observation in enumerate(observations):
        _require(isinstance(observation, Mapping), f"closure observation {number} is malformed")
        _require(observation.get("classification") == "workspace_only_preflight" and observation.get("usable_as_production_input") is False, f"closure observation {number} crossed production boundary")
        source = observation.get("source")
        path = _resolve(repository_root, source, f"closure observation {number}")
        value = _load(path, source)
        for field in ("image_digest", "seccomp_digest", "closure_digest"):
            _is_digest(observation.get(field), f"closure observation {number}.{field}")
            _require(value.get(field) == observation[field], f"closure {field} drift: {number}")
        if observation.get("runtime_digest") is not None:
            _is_digest(observation["runtime_digest"], f"closure observation {number}.runtime_digest")
            _require(value.get("runtime_digest") == observation["runtime_digest"], f"closure runtime drift: {number}")
        result.append({
            "source": source,
            "classification": observation["classification"],
            "usable_as_production_input": False,
            "image_digest": observation["image_digest"],
            "runtime_digest": observation.get("runtime_digest"),
            "seccomp_digest": observation["seccomp_digest"],
            "closure_digest": observation["closure_digest"],
            "file_digest": _raw_digest(path),
        })
    return result


def validate_authority_semantics(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Extract authority commitments while rejecting independent-authority claims."""
    authority = proposal.get("authority")
    boundaries = proposal.get("boundaries")
    signing = proposal.get("signing")
    _require(proposal.get("schema") == "P5R0AuthorityBindingProposalV1", "RS-068 proposal schema drift")
    _require(proposal.get("item_id") == "RS-068" and proposal.get("state_proposed") == "BLOCKED", "RS-068 proposal state drift")
    _require(isinstance(authority, Mapping) and authority.get("schema") == "P5R0PublicAuthorityV4", "authority schema drift")
    _require(isinstance(boundaries, Mapping) and boundaries.get("authority_created") is False and boundaries.get("production_promotable") is False, "authority proposal claims promotion")
    _require(isinstance(signing, Mapping) and signing.get("asymmetric_sign_invoked") is False and signing.get("signature_present") is False and signing.get("signature") is None, "authority proposal claims a signature")
    authority_id = authority.get("authority_id")
    _require(isinstance(authority_id, str) and authority_id.startswith("self-custodied/"), "authority is not explicitly self-custodied")
    _require("independent" not in authority_id.lower(), "independent authority claim is forbidden")
    _is_digest(authority.get("public_key_digest"), "authority public-key digest")
    kms = proposal.get("kms")
    _require(isinstance(kms, Mapping) and kms.get("authority_binding") is None, "KMS authority binding was promoted")
    return {
        "authority_id": authority_id,
        "key_id": authority.get("key_id"),
        "authority_schema": authority["schema"],
        "public_key_digest": authority["public_key_digest"],
        "transport_attestation": dict(authority.get("transport_attestation", {})),
        "kms_key_version": kms.get("key_version"),
        "authority_binding_digest": None,
        "signature_present": False,
        "authority_created": False,
        "independent_authority_claim": False,
        "independent_evaluator_required": False,
        "custody": "self_custodied",
    }


def _time_seed_algorithm(repository_root: Path) -> dict[str, Any]:
    source = repository_root / "services/p5_r0_evaluator/time_seed.py"
    _require(source.is_file(), "time-seed implementation is missing")
    algorithm_binding = time_seed_algorithm_binding(repository_root)
    builder_module = __import__("services.p5_r0_evaluator.input_builder", fromlist=["input_builder_binding"])
    builder_binding = validate_input_builder_binding(builder_module.input_builder_binding(repository_root), repository_root)
    return {
        "schema": "P5R0TimeSeedV1",
        "implementation": algorithm_binding["implementation"],
        "version": algorithm_binding["version"],
        "source_path": algorithm_binding["source_path"],
        "source_digest": algorithm_binding["source_digest"],
        "binding_digest": algorithm_binding["binding_digest"],
        "input_builder_binding": builder_binding,
        "algorithm": {
            "timing_record_digest": "sha256(canonical_json(timing_record))",
            "input_seed_digest": "sha256(canonical_json({schema:P5R0TimeSeedV1,timing_record_digest,run_id,namespace,sequence}))",
            "input_digest": "sha256(canonical_json(input_value))",
            "input_value": "input_builder(input_seed_digest)",
            "required_timing_schema": "P5R0IndependentTimingAttestationV3",
            "timing_required_before_seed": True,
            "sequence": "positive integer; starts at 1",
        },
        "public_bindings": ["timing_record_digest", "input_seed_digest", "input_digest", "input_builder_implementation", "input_builder_version", "input_builder_source_digest", "time_seed_algorithm_source_digest"],
        "materializer_status": "disclosed_only_no_timing_record_consumed",
    }


def _commitment(root: Path, path: Path, value: Mapping[str, Any], label: str) -> dict[str, str]:
    return {"path": str(path.resolve().relative_to(root.resolve())), "semantic_digest": sha256(dict(value)), "file_digest": _raw_digest(path), "label": label}


def materialize(
    *,
    repository_root: Path = REPOSITORY_ROOT,
    generated_root: Path = DEFAULT_GENERATED_ROOT,
    rs063_path: Path = DEFAULT_RS063,
    rs068_path: Path = DEFAULT_RS068,
    rs069_path: Path = DEFAULT_RS069,
    closure_paths: Sequence[Path] = DEFAULT_CLOSURES,
) -> dict[str, Any]:
    """Read, validate, and return the canonical review-only run manifest."""
    root = Path(repository_root).resolve()
    generated = Path(generated_root).resolve()
    index_path = generated / "artifact-index.json"
    provenance_path = generated / "public/generator-provenance.json"
    index = _load(index_path, "artifact index")
    provenance = _load(provenance_path, "generator provenance")
    artifact_commitments = validate_artifact_commitments(index, generated)
    provenance_commitment = validate_generator_provenance(provenance)
    provenance_commitment["provenance_digest"] = sha256(provenance)

    execution_request = load_execution_request(Path(rs063_path))
    rs063_report = validate_execution_request(execution_request, repository_root=root)
    authority_proposal = _load(Path(rs068_path), "RS-068 authority proposal")
    rs068_report = validate_proposal(Path(rs068_path), generated / "public/lock-signing-request.json", root / "services/p5_r0_evaluator/deploy/rs-068-wip-policy-remediation.json")
    plan = load_plan(Path(rs069_path))
    rs069_report = validate_plan(plan, repository_root=root)

    closure_observations = plan["read_only_inventory"]["local_closure_observations"]
    closure_commitments = validate_closure_commitments(closure_observations, root)
    authority = validate_authority_semantics(authority_proposal)
    rs063_commitment = _commitment(root, Path(rs063_path), execution_request, "RS-063 execution request")
    rs068_commitment = _commitment(root, Path(rs068_path), authority_proposal, "RS-068 authority proposal")
    rs069_commitment = _commitment(root, Path(rs069_path), plan, "RS-069 typed IaC plan")
    pending_rs069 = [
        {"order": op["order"], "id": op["id"], "approval_gate": op["approval_gate"], "enabled": False}
        for op in plan["operations"]
    ]
    pending_signed = [
        {"id": step["id"], "operation": step["operation"], "enabled": False, "mutating": step["mutating"]}
        for step in execution_request["run_order"] if step["mutating"]
    ]
    manifest: dict[str, Any] = {
        "schema": "P5R0ControlledRunMaterializationManifestV1",
        "classification": "review_only_local_deterministic_non_release",
        "status": "blocked_pending_signed_environment_operations",
        "master_run": "P5-MASTER-001",
        "runsheet_transition_authority": "master_only",
        "materializer": {"implementation": "services.p5_r0_evaluator.deploy.controlled_run_materializer.materialize", "version": "P5R0ControlledRunMaterializerV1"},
        "custody": {
            "all_inputs_project_generated_or_self_custodied": True,
            "generated_artifacts": "project_generated",
            "local_closure_observations": "project_generated_workspace_only_preflight",
            "authority_proposal": "project_self_custodied_review_proposal",
            "request_and_plan": "project_authored_review_contracts",
            "independent_authority_claim": False,
            "independent_evaluator_required": False,
            "external_authority_semantics": "trust-binding gate only; not an independent evaluator requirement",
        },
        "provenance": provenance_commitment,
        "split": {"path": "var/p5-r0-diagnostic-inputs/public/split.json", "seed": "p5-r0-v2", "semantic_digest": index["artifacts"]["split"]["digest"], "file_digest": index["artifacts"]["split"]["file_digest"]},
        "time_seed_algorithm": _time_seed_algorithm(root),
        "input_builder_binding": provenance_commitment["input_builder_binding"],
        "artifact_commitments": {"index_digest": index["index_digest"], "index_file_digest": _raw_digest(index_path), "artifacts": artifact_commitments},
        "closure_commitments": closure_commitments,
        "authority_commitment": authority,
        "source_commitments": {"rs063": rs063_commitment, "rs068": rs068_commitment, "rs069": rs069_commitment},
        "validator_reports": {
            "RS-063": {"status": rs063_report.status, "ready": rs063_report.ready, "definition_digest": rs063_report.definition_digest, "cloud_operations": list(rs063_report.cloud_operations)},
            "RS-068": rs068_report,
            "RS-069": {"status": rs069_report.status, "ready": rs069_report.ready, "plan_digest": rs069_report.plan_digest, "operation_ids": list(rs069_report.operation_ids), "unresolved_inputs": list(rs069_report.unresolved_inputs), "cloud_operations": list(rs069_report.cloud_operations)},
        },
        "signed_environment_operations_pending": {"RS-069": pending_rs069, "RS-063_future_mutating_steps": pending_signed},
        "review_only_boundary": {
            "generated_controlled_run_inputs": True,
            "fabricated_evidence": False,
            "execution_evidence_present": False,
            "signature_generated": False,
            "kms_called": False,
            "gcloud_called": False,
            "gcs_uploaded": False,
            "freetsa_called": False,
            "deployed": False,
            "supervisor_invoked": False,
            "tasks_executed": False,
            "cloud_operations": [],
            "forbidden_operations": list(_FORBIDDEN_OPERATIONS),
            "commands": [],
            "production_promotable": False,
        },
        "proposed_state": "PASS_REVIEW for local materialization only; production execution remains NO_GO/blocked",
        "claim_boundary": "This manifest commits project-generated/self-custodied review inputs only. It is not a signature, authority binding, deployment, upload, supervisor evidence, task execution, or result claim.",
    }
    manifest["manifest_digest"] = sha256(manifest)
    return manifest


def write_manifest(manifest: Mapping[str, Any], output: Path) -> None:
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_bytes(canonical_bytes(dict(manifest)))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize a local deterministic review-only controlled-run manifest")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    args = parser.parse_args(argv)
    try:
        manifest = materialize(repository_root=args.repository_root)
        write_manifest(manifest, args.output)
    except (ControlledRunMaterializationError, OSError, ValueError) as exc:
        print(f"controlled-run materialization blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"output": str(args.output), "manifest_digest": manifest["manifest_digest"], "status": manifest["status"], "cloud_operations": manifest["review_only_boundary"]["cloud_operations"]}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = [
    "ControlledRunMaterializationError",
    "DEFAULT_OUTPUT",
    "materialize",
    "validate_artifact_commitments",
    "validate_authority_semantics",
    "validate_closure_commitments",
    "validate_generator_provenance",
    "write_manifest",
]
