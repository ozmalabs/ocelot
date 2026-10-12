"""Local-only RS-060 controlled-run bundle definition and validator.

The checked-in definition is a re-runnable control-plane contract, not a
signed bundle. Project-generated inputs must be bound to reviewed execution
and environment evidence before strict validation can pass. This module never
accesses cloud APIs, credentials, KMS, object stores, containers, or deployment tooling.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from evaluation.p0a.canonical import (
    b64decode,
    canonical_bytes,
    object_hash,
    parse_canonical,
    verify_signature,
)
from evaluation.p5_r0.fixture_generator import validate_manifest_integrity
from evaluation.p5_r0.protocol import P5R0Error, digest, is_digest
from services.p5_r0_evaluator.client import EvaluatorClientError, _validate_authority as validate_service_authority
from services.p5_r0_evaluator.input_builder import validate_input_builder_binding
from services.p5_r0_evaluator.time_seed import time_seed_algorithm_binding


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEFINITION = Path(__file__).with_name("p5-r0-production-bundle.json")
_DIGEST_FIELDS = (
    "manifest_digest",
    "index_digest",
    "truth_digest",
    "store_digest",
    "lock_digest",
    "authority_digest",
    "kms_authority_binding_digest",
    "worker_contract_digest",
    "evaluator_contract_digest",
    "policy_digest",
    "task_set_digest",
    "input_builder_binding_digest",
    "time_seed_algorithm_binding_digest",
)
_INPUT_KEYS = (
    "manifest",
    "private_store",
    "lock",
    "authority_trust_binding",
    "kms_authority_binding",
    "worker_contract",
    "evaluator_contract",
    "policy",
    "task_set",
    "input_builder_binding",
    "time_seed_algorithm_binding",
)


class BundleDefinitionValidationError(ValueError):
    """The repository bundle contract or a project-generated input is malformed."""


class BundleDefinitionBlockedError(BundleDefinitionValidationError):
    """The contract is valid but generated inputs or reviewed bindings are absent."""


@dataclass(frozen=True)
class BundleValidationReport:
    ready: bool
    missing_inputs: tuple[str, ...]
    definition_digest: str
    checked_input_digests: tuple[tuple[str, str], ...] = ()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BundleDefinitionValidationError(message)


def _is_digest(value: Any, label: str) -> str:
    if not is_digest(value):
        raise BundleDefinitionValidationError(f"{label} is not a canonical sha256 digest")
    return value


def _validate_definition_shape(definition: Mapping[str, Any], repository_root: Path) -> None:
    expected = {
        "schema",
        "classification",
        "status",
        "source_files",
        "canonical_digest",
        "input_locations",
        "expected_commitments",
        "blocked_inputs",
        "assembly",
        "commands",
        "apply_plan",
        "claim_boundary",
    }
    _require(set(definition) == expected, "bundle definition fields are not closed")
    _require(definition.get("schema") == "P5R0ProductionBundleDefinitionV1", "bundle definition schema drift")
    _require(definition.get("classification") == "repository_definition_only", "bundle definition classification drift")
    _require(definition.get("status") == "blocked_pending_reviewed_inputs", "bundle definition must remain blocked")

    canonical = definition.get("canonical_digest")
    _require(canonical == {
        "algorithm": "sha256",
        "encoding": "canonical-json",
        "implementation": "evaluation.p0a.canonical.digest",
    }, "canonical digest contract drift")

    source_files = definition.get("source_files")
    _require(isinstance(source_files, Mapping), "bundle source file map is missing")
    for key, relative in source_files.items():
        _require(isinstance(key, str) and isinstance(relative, str), "bundle source file map is malformed")
        path = (repository_root / relative).resolve()
        _require(path.is_file() and repository_root in path.parents, f"bundle source file missing: {key}")

    locations = definition.get("input_locations")
    _require(isinstance(locations, Mapping) and set(locations) == set(_INPUT_KEYS), "bundle input locations are not closed")
    for key, value in locations.items():
        if value is not None:
            _require(isinstance(value, str) and value and not Path(value).is_absolute(), f"bundle input path is invalid: {key}")

    commitments = definition.get("expected_commitments")
    _require(isinstance(commitments, Mapping) and set(commitments) == set(_DIGEST_FIELDS), "bundle commitments are not closed")
    for key, value in commitments.items():
        if value is not None:
            _is_digest(value, f"expected_commitments.{key}")

    blocked = definition.get("blocked_inputs")
    _require(blocked == {
        "authorized_tasks": None,
        "candidate_digests": None,
        "private_truth": None,
        "signature_material": None,
        "p5_results": None,
    }, "blocked controlled-run bindings must remain absent")

    assembly = definition.get("assembly")
    _require(assembly == {
        "mode": "review_only_no_production_outputs",
        "input_order": list(_INPUT_KEYS),
        "output": None,
        "writes_controlled_run_inputs": False,
    }, "bundle assembly contract drift")

    commands = definition.get("commands")
    _require(isinstance(commands, Mapping) and set(commands) == {"prepare", "validate"}, "bundle commands are not closed")
    for command in commands.values():
        _require(isinstance(command, str) and command.startswith("PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.bundle_definition "), "bundle command is not auditable")

    apply_plan = definition.get("apply_plan")
    _require(isinstance(apply_plan, Mapping), "bundle apply plan is missing")
    _require(apply_plan.get("mode") == "review_only_no_execution" and apply_plan.get("commands") == [], "bundle apply plan is executable")
    forbidden = apply_plan.get("forbidden_operations")
    _require(isinstance(forbidden, list) and {
        "gcloud mutation", "deploy", "VM creation", "IAM alteration", "secret access", "external timing endpoint"
    }.issubset(forbidden), "bundle forbidden-operation boundary drift")


def _missing_inputs(definition: Mapping[str, Any]) -> list[str]:
    locations = definition["input_locations"]
    commitments = definition["expected_commitments"]
    missing = [f"input_locations.{key}" for key in _INPUT_KEYS if locations.get(key) is None]
    missing.extend(f"expected_commitments.{key}" for key in _DIGEST_FIELDS if commitments.get(key) is None)
    return missing


def _resolve_input(repository_root: Path, label: str, value: Any) -> Path:
    _require(isinstance(value, str) and value, f"{label} input path is missing")
    relative = Path(value)
    _require(not relative.is_absolute(), f"{label} input path must be repository-relative")
    resolved = (repository_root / relative).resolve()
    _require(repository_root in resolved.parents and resolved.is_file(), f"{label} input file is missing")
    return resolved


def _load_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        return parse_canonical(path.read_bytes())
    except Exception as exc:
        raise BundleDefinitionValidationError(f"{label} is not canonical JSON") from exc


def _validate_authority(authority: Mapping[str, Any]) -> dict[str, Any]:
    try:
        value = validate_service_authority(authority)
    except (EvaluatorClientError, TypeError) as exc:
        raise BundleDefinitionValidationError("authority trust binding is invalid") from exc
    try:
        Ed25519PublicKey.from_public_bytes(b64decode(value["public_key"]))
    except Exception as exc:
        raise BundleDefinitionValidationError("authority public key is invalid") from exc
    return value


def _validate_kms_binding(binding: Mapping[str, Any], authority: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema", "authority_id", "key_id", "kms_key_version", "public_key_digest", "purpose", "binding_digest"
    }
    _require(set(binding) == required, "KMS authority binding is not closed")
    _require(binding.get("schema") == "P5R0KMSAuthorityBindingV1", "KMS authority binding schema drift")
    _require(binding.get("authority_id") == authority.get("authority_id"), "KMS authority authority-id drift")
    _require(binding.get("key_id") == authority.get("key_id"), "KMS authority key-id drift")
    _require(binding.get("public_key_digest") == authority.get("public_key_digest"), "KMS public-key binding drift")
    _require(binding.get("purpose") == "p5-r0-production-authority", "KMS authority purpose drift")
    _require(isinstance(binding.get("kms_key_version"), str) and binding["kms_key_version"].startswith("projects/"), "KMS key version is invalid")
    _require(binding.get("binding_digest") == digest({key: value for key, value in binding.items() if key != "binding_digest"}), "KMS binding digest is invalid")
    return dict(binding)


def _validate_digest_object(value: Mapping[str, Any], label: str, schema: str) -> str:
    _require(value.get("schema") == schema, f"{label} schema drift")
    _require(is_digest(value.get("digest")), f"{label} digest is invalid")
    _require(value["digest"] == digest({key: child for key, child in value.items() if key != "digest"}), f"{label} digest mismatch")
    return value["digest"]


def _validate_policy(policy: Mapping[str, Any]) -> str:
    _require(policy.get("schema") == "P5R0GatePolicyV3", "policy schema drift")
    _require(policy.get("expected_primary_records") == 144 and policy.get("expected_cases") == 48 and policy.get("expected_arms") == 3, "policy cardinality drift")
    _require(policy.get("native_required") is True and policy.get("external_authority_required") is True, "policy authority/native gate drift")
    safeguards = policy.get("safeguards")
    _require(isinstance(safeguards, Mapping) and safeguards.get("confidence_milli_min") == 900 and safeguards.get("held_out_adoption") is False, "policy safeguards drift")
    return digest(dict(policy))


def _validate_task_set(task_set: Mapping[str, Any], commitments: Mapping[str, Any], policy_digest: str, worker_digest: str, evaluator_digest: str) -> str:
    required = {
        "schema", "manifest_digest", "case_index_digest", "split_digest", "policy_digest",
        "worker_contract_digest", "evaluator_contract_digest", "task_count", "control_ids", "authorized", "task_set_digest"
    }
    _require(set(task_set) == required, "task-set commitment is not closed")
    _require(task_set.get("schema") == "P5R0TaskSetCommitmentV1", "task-set schema drift")
    _require(task_set.get("authorized") is True and task_set.get("task_count") == 144, "task-set is not an authorized 144-record commitment")
    _require(isinstance(task_set.get("control_ids"), list) and len(task_set["control_ids"]) == 11, "task-set controls drift")
    _require(task_set.get("policy_digest") == policy_digest, "task-set policy binding drift")
    _require(task_set.get("worker_contract_digest") == worker_digest and task_set.get("evaluator_contract_digest") == evaluator_digest, "task-set contract binding drift")
    expected = digest({key: value for key, value in task_set.items() if key != "task_set_digest"})
    _require(task_set.get("task_set_digest") == expected, "task-set digest mismatch")
    _require(task_set.get("manifest_digest") == commitments["manifest_digest"] and task_set.get("case_index_digest") == commitments["index_digest"], "task-set manifest binding drift")
    return expected


def _validate_complete(definition: Mapping[str, Any], repository_root: Path) -> tuple[tuple[str, str], ...]:
    locations = definition["input_locations"]
    commitments = definition["expected_commitments"]
    paths = {key: _resolve_input(repository_root, f"input_locations.{key}", locations[key]) for key in _INPUT_KEYS}
    values = {key: _load_canonical(paths[key], key) for key in _INPUT_KEYS}

    manifest = values["manifest"]
    private_store = values["private_store"]
    try:
        validate_manifest_integrity(manifest, private_store)
    except (P5R0Error, KeyError, TypeError) as exc:
        raise BundleDefinitionValidationError("manifest/private-store integrity validation failed") from exc
    authority = _validate_authority(values["authority_trust_binding"])
    kms = _validate_kms_binding(values["kms_authority_binding"], authority)
    worker_digest = _validate_digest_object(values["worker_contract"], "worker contract", "P5R0WorkerContractV3")
    evaluator_digest = _validate_digest_object(values["evaluator_contract"], "evaluator contract", "P5R0EvaluatorContractV3")
    policy_digest = _validate_policy(values["policy"])
    task_set_digest = _validate_task_set(values["task_set"], commitments, policy_digest, worker_digest, evaluator_digest)
    try:
        builder_binding = validate_input_builder_binding(values["input_builder_binding"], repository_root)
        algorithm_binding = time_seed_algorithm_binding(repository_root)
    except Exception as exc:
        raise BundleDefinitionValidationError("time-seed source commitment is invalid") from exc
    _require(values["time_seed_algorithm_binding"] == algorithm_binding, "time-seed algorithm binding drift")

    lock = values["lock"]
    required_lock = {
        "schema", "classification", "non_release", "manifest_digest", "index_digest", "truth_digest", "store_digest",
        "authority_digest", "kms_authority_binding_digest", "worker_contract_digest", "evaluator_contract_digest",
        "policy_digest", "task_set_digest", "input_builder_binding", "time_seed_algorithm_binding", "lock_digest", "signature"
    }
    _require(set(lock) == required_lock, "production lock fields are not closed")
    _require(lock.get("schema") == "P5R0ProductionLockV1" and lock.get("classification") == "production_review_required" and lock.get("non_release") is False, "production lock is not review-bound")
    _require(lock.get("lock_digest") == object_hash(lock, "lock_digest", "signature"), "production lock digest mismatch")
    try:
        verify_signature(lock, Ed25519PublicKey.from_public_bytes(b64decode(authority["public_key"])), "lock_digest")
    except Exception as exc:
        raise BundleDefinitionValidationError("production lock signature is invalid") from exc

    actual = {
        "manifest_digest": manifest["manifest_digest"],
        "index_digest": manifest["index_digest"],
        "truth_digest": manifest["truth_digest"],
        "store_digest": manifest["store_digest"],
        "lock_digest": lock["lock_digest"],
        "authority_digest": digest(authority),
        "kms_authority_binding_digest": kms["binding_digest"],
        "worker_contract_digest": worker_digest,
        "evaluator_contract_digest": evaluator_digest,
        "policy_digest": policy_digest,
        "task_set_digest": task_set_digest,
        "input_builder_binding_digest": builder_binding["binding_digest"],
        "time_seed_algorithm_binding_digest": algorithm_binding["binding_digest"],
    }
    for key, expected in commitments.items():
        _require(expected == actual[key], f"expected commitment mismatch: {key}")
    for key in _DIGEST_FIELDS:
        if key in {"input_builder_binding_digest", "time_seed_algorithm_binding_digest"}:
            continue
        _require(lock[key] == actual[key], f"production lock commitment mismatch: {key}")
    _require(lock["input_builder_binding"] == builder_binding and lock["time_seed_algorithm_binding"] == algorithm_binding, "production lock source commitment mismatch")
    return tuple(sorted(actual.items()))


def load_definition(path: Path = DEFAULT_DEFINITION) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleDefinitionValidationError("bundle definition cannot be loaded") from exc
    if not isinstance(value, dict):
        raise BundleDefinitionValidationError("bundle definition root must be an object")
    return value


def validate_bundle_definition(
    definition: Mapping[str, Any],
    *,
    repository_root: Path = REPOSITORY_ROOT,
    require_complete: bool = False,
) -> BundleValidationReport:
    root = Path(repository_root).resolve()
    _validate_definition_shape(definition, root)
    missing = tuple(_missing_inputs(definition))
    checked: tuple[tuple[str, str], ...] = ()
    if not missing:
        checked = _validate_complete(definition, root)
    elif require_complete:
        raise BundleDefinitionBlockedError("generated bundle and reviewed environment bindings are required: " + ", ".join(missing))
    return BundleValidationReport(
        ready=not missing,
        missing_inputs=missing,
        definition_digest=digest(dict(definition)),
        checked_input_digests=checked,
    )


def _audit_payload(report: BundleValidationReport) -> dict[str, Any]:
    return {
        "schema": "P5R0BundlePreparationAuditV1",
        "status": "ready" if report.ready else "blocked_pending_reviewed_inputs",
        "ready": report.ready,
        "missing_inputs": list(report.missing_inputs),
        "definition_digest": report.definition_digest,
        "checked_input_digests": dict(report.checked_input_digests),
        "production_outputs_created": False,
        "cloud_operations": [],
        "claim_boundary": "No production authority, task release, candidate, signature, or P5 result was created.",
    }


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate or audit the local-only RS-060 production bundle definition")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "validate"):
        command = subparsers.add_parser(name)
        command.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
        command.add_argument("--allow-blocked", action="store_true")
    subparsers.choices["prepare"].add_argument("--audit-output", type=Path)
    args = parser.parse_args(argv)
    try:
        definition = load_definition(args.definition)
        report = validate_bundle_definition(definition, require_complete=not args.allow_blocked)
        payload = _audit_payload(report)
        if args.command == "prepare" and args.audit_output is not None:
            args.audit_output.parent.mkdir(parents=True, exist_ok=True)
            args.audit_output.write_bytes(canonical_bytes(payload))
        print(json.dumps(payload, sort_keys=True))
        return 0 if report.ready or args.allow_blocked else 2
    except (BundleDefinitionValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"RS-060 validation blocked: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    return _cli(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
