"""Deterministic, offline RS-062 diagnostic input generation.

This module composes the frozen P5-R0 split, fixture, worker/evaluator, policy,
and RS-060 task-set contracts.  It writes only disposable diagnostic inputs;
it never talks to cloud services, obtains secrets, or creates a production
signature.  The generated task-set's ``authorized`` field is the exact frozen
commitment shape, while the adjacent authorization/control commitment makes
its self-custodied diagnostic-only meaning explicit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256 as canonical_digest
from evaluation.p5_r0.domain_cards import create_domain_cards
from evaluation.p5_r0.fixture_generator import build_private_manifest, validate_manifest_integrity
from evaluation.p5_r0.protocol import P5R0Error, digest
from evaluation.p5_r0.repair import V3_CONTROL_IDS, repair_policy
from services.p5_r0_evaluator.input_builder import input_builder_binding
from services.p5_r0_evaluator.time_seed import time_seed_algorithm_binding
from evaluation.p5_r0.split import build_split_commitment, validate_split_commitment


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPOSITORY_ROOT / "var" / "p5-r0-diagnostic-inputs"
GENERATOR_VERSION = "P5R0DiagnosticInputGeneratorV1"
DEFAULT_SEED = "p5-r0-diagnostic-seed-v1"
DEFAULT_SPLIT_SEED = "p5-r0-v2"
MASTER_RUN = "P5-MASTER-001"
RUNSHEET_ITEM = "RS-062"


class DiagnosticGenerationError(ValueError):
    """A deterministic diagnostic input could not be constructed safely."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticGenerationError(message)


def _stable_signer(seed: str) -> Ed25519PrivateKey:
    # This key signs only the frozen domain-card fixture required by the
    # existing generator. It is deliberately not emitted or used for a lock.
    key_material = hashlib.sha256((GENERATOR_VERSION + "\0" + seed).encode("utf-8")).digest()
    return Ed25519PrivateKey.from_private_bytes(key_material)


def _worker_contract() -> dict[str, Any]:
    value = {
        "schema": "P5R0WorkerContractV3",
        "task_schema": "P5R0WorkerTaskV3",
        "reply_schema": "P5R0WorkerReplyV3",
        "control_null_action": "worker_reply_only",
        "control_metadata_public": True,
        "private_fields_forbidden": [
            "truth", "target_action", "secret_seed", "private_domain_family", "split"
        ],
    }
    value["digest"] = digest(value)
    return value


def _evaluator_contract() -> dict[str, Any]:
    value = {
        "schema": "P5R0EvaluatorContractV3",
        "episode_reset_policy": "fresh_case",
        "session_state": "declared_persistent_namespace",
        "namespace_isolation": "per_domain",
    }
    value["digest"] = digest(value)
    return value


def _task_set(
    manifest: Mapping[str, Any],
    split: Mapping[str, Any],
    policy: Mapping[str, Any],
    worker: Mapping[str, Any],
    evaluator: Mapping[str, Any],
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "P5R0TaskSetCommitmentV1",
        "manifest_digest": manifest["manifest_digest"],
        "case_index_digest": manifest["index_digest"],
        "split_digest": split["split_digest"],
        "policy_digest": digest(dict(policy)),
        "worker_contract_digest": worker["digest"],
        "evaluator_contract_digest": evaluator["digest"],
        "task_count": 144,
        "control_ids": list(V3_CONTROL_IDS),
        # Required by the frozen RS-060 task-set contract. Its diagnostic-only
        # interpretation is bound in the adjacent authorization commitment.
        "authorized": True,
    }
    value["task_set_digest"] = digest(value)
    return value


def _control_commitment(
    *,
    seed: str,
    split: Mapping[str, Any],
    policy: Mapping[str, Any],
    task_set: Mapping[str, Any],
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "P5R0DiagnosticControlCommitmentV1",
        "master_run": MASTER_RUN,
        "runsheet_item": RUNSHEET_ITEM,
        "authorization": "self_custodied_diagnostic_authorization",
        "non_release": True,
        "signed_execution_required": True,
        "generator": {"version": GENERATOR_VERSION, "seed": seed, "split_seed": split["seed"]},
        "split_digest": split["split_digest"],
        "policy_digest": digest(dict(policy)),
        "task_set_digest": task_set["task_set_digest"],
        "control_ids": list(task_set["control_ids"]),
        "control_count": len(task_set["control_ids"]),
        "claim_boundary": "Controls are commitments for one self-custodied diagnostic; no signed execution evidence exists.",
    }
    value["commitment_digest"] = digest(value)
    return value


def _unsigned_lock_request(
    *,
    seed: str,
    split: Mapping[str, Any],
    manifest: Mapping[str, Any],
    worker: Mapping[str, Any],
    evaluator: Mapping[str, Any],
    policy: Mapping[str, Any],
    task_set: Mapping[str, Any],
    input_builder: Mapping[str, Any],
    time_seed_algorithm: Mapping[str, Any],
) -> dict[str, Any]:
    # This is intentionally not accepted as P5R0ProductionLockV1: reviewed
    # authority/KMS commitments and the production signature are absent.
    unsigned_lock: dict[str, Any] = {
        "schema": "P5R0ProductionLockV1",
        "classification": "diagnostic_unsigned_kms_request",
        "non_release": True,
        "manifest_digest": manifest["manifest_digest"],
        "index_digest": manifest["index_digest"],
        "truth_digest": manifest["truth_digest"],
        "store_digest": manifest["store_digest"],
        "authority_digest": None,
        "kms_authority_binding_digest": None,
        "worker_contract_digest": worker["digest"],
        "evaluator_contract_digest": evaluator["digest"],
        "policy_digest": digest(dict(policy)),
        "task_set_digest": task_set["task_set_digest"],
        "input_builder_binding": dict(input_builder),
        "time_seed_algorithm_binding": dict(time_seed_algorithm),
        "lock_digest": "",
        "signature": None,
    }
    unsigned_lock["lock_digest"] = canonical_digest(
        {key: value for key, value in unsigned_lock.items() if key not in {"lock_digest", "signature"}}
    )
    request: dict[str, Any] = {
        "schema": "P5R0KMSLockSigningRequestV1",
        "classification": "diagnostic_unsigned_non_release",
        "status": "pending_reviewed_authority_and_kms",
        "non_release": True,
        "generator": {"version": GENERATOR_VERSION, "seed": seed, "split_seed": split["seed"]},
        "production_lock_schema": "P5R0ProductionLockV1",
        "unsigned_lock": unsigned_lock,
        "unsigned_lock_digest": unsigned_lock["lock_digest"],
        "kms": {
            "required": True,
            "operation": "sign_exact_lock_digest_in_reviewed_signed_environment",
            "key_version": None,
            "authority_binding_digest": None,
            "signature_present": False,
        },
        "production_signature_created": False,
        "cloud_operations": [],
        "claim_boundary": "No production authority, KMS signature, release lock, or signed execution evidence was created.",
    }
    request["request_digest"] = digest(request)
    return request


def _bundle_input_manifest(
    *,
    seed: str,
    split: Mapping[str, Any],
    manifest: Mapping[str, Any],
    worker: Mapping[str, Any],
    evaluator: Mapping[str, Any],
    policy: Mapping[str, Any],
    task_set: Mapping[str, Any],
    control: Mapping[str, Any],
    lock_request: Mapping[str, Any],
    input_builder: Mapping[str, Any],
    time_seed_algorithm: Mapping[str, Any],
) -> dict[str, Any]:
    policy_digest = digest(dict(policy))
    artifact_paths = {
        "split": "public/split.json",
        "manifest": "public/manifest.json",
        "private_store": "private-truth/case-store.json",
        "worker_contract": "public/worker-contract.json",
        "evaluator_contract": "public/evaluator-contract.json",
        "policy": "public/policy.json",
        "task_set": "public/task-set.json",
        "control_commitment": "public/control-commitment.json",
        "lock_signing_request": "public/lock-signing-request.json",
    }
    value: dict[str, Any] = {
        "schema": "P5R0DiagnosticBundleInputManifestV1",
        "classification": "diagnostic_generated_non_release",
        "status": "generated_pending_signed_execution",
        "generator": {"version": GENERATOR_VERSION, "seed": seed, "split_seed": split["seed"]},
        "master_run": MASTER_RUN,
        "runsheet_item": RUNSHEET_ITEM,
        "artifact_paths": artifact_paths,
        "commitments": {
            "split_digest": split["split_digest"],
            "manifest_digest": manifest["manifest_digest"],
            "index_digest": manifest["index_digest"],
            "truth_digest": manifest["truth_digest"],
            "store_digest": manifest["store_digest"],
            "worker_contract_digest": worker["digest"],
            "evaluator_contract_digest": evaluator["digest"],
            "policy_digest": policy_digest,
            "task_set_digest": task_set["task_set_digest"],
            "control_commitment_digest": control["commitment_digest"],
            "unsigned_lock_digest": lock_request["unsigned_lock_digest"],
            "authority_digest": None,
            "kms_authority_binding_digest": None,
            "production_lock_digest": None,
            "input_builder_binding_digest": input_builder["binding_digest"],
            "time_seed_algorithm_binding_digest": time_seed_algorithm["binding_digest"],
            "input_builder_source_digest": input_builder["source_digest"],
            "time_seed_algorithm_source_digest": time_seed_algorithm["source_digest"],
        },
        "private_truth_custody": {
            "root": "private-truth/",
            "disposable_var_only": True,
            "worker_public_output": False,
            "signed_environment_required_for_release": True,
        },
        "production_outputs_created": False,
        "cloud_operations": [],
        "no_go_until": "signed_confidential_space_execution",
        "claim_boundary": "Generated self-custodied diagnostic inputs only; not production authority, task release, signature, or execution evidence.",
    }
    value["manifest_digest"] = digest(value)
    return value


def build_diagnostic_artifacts(*, seed: str = DEFAULT_SEED, split_seed: str = DEFAULT_SPLIT_SEED) -> dict[str, dict[str, Any]]:
    """Build all diagnostic objects without writing files or using external services."""
    _require(isinstance(seed, str) and seed, "diagnostic seed must be non-empty")
    _require(isinstance(split_seed, str) and split_seed, "split seed must be non-empty")
    split = build_split_commitment(seed=split_seed)
    validate_split_commitment(split)
    signer = _stable_signer(seed)
    cards = create_domain_cards(
        signer,
        authority_id="p5-r0-diagnostic-domain-card-authority",
        key_id="p5-r0-diagnostic-domain-card-key",
    )
    manifest, private_store = build_private_manifest(split, cards)
    input_builder = input_builder_binding(REPOSITORY_ROOT)
    time_seed_algorithm = time_seed_algorithm_binding(REPOSITORY_ROOT)
    manifest["input_builder_binding"] = input_builder
    manifest["time_seed_algorithm_binding"] = time_seed_algorithm
    manifest["manifest_digest"] = digest({key: value for key, value in manifest.items() if key != "manifest_digest"})
    validate_manifest_integrity(manifest, private_store)
    worker = _worker_contract()
    evaluator = _evaluator_contract()
    policy = repair_policy(contrast_matrix=split["contrast_matrix"])
    task_set = _task_set(manifest, split, policy, worker, evaluator)
    control = _control_commitment(seed=seed, split=split, policy=policy, task_set=task_set)
    lock_request = _unsigned_lock_request(
        seed=seed,
        split=split,
        manifest=manifest,
        worker=worker,
        evaluator=evaluator,
        policy=policy,
        task_set=task_set,
        input_builder=input_builder,
        time_seed_algorithm=time_seed_algorithm,
    )
    bundle_manifest = _bundle_input_manifest(
        seed=seed,
        split=split,
        manifest=manifest,
        worker=worker,
        evaluator=evaluator,
        policy=policy,
        task_set=task_set,
        control=control,
        lock_request=lock_request,
        input_builder=input_builder,
        time_seed_algorithm=time_seed_algorithm,
    )
    provenance = {
        "schema": "P5R0DiagnosticGeneratorProvenanceV1",
        "generator": {"version": GENERATOR_VERSION, "seed": seed, "split_seed": split_seed},
        "master_run": MASTER_RUN,
        "runsheet_item": RUNSHEET_ITEM,
        "frozen_contracts": {
            "split": "evaluation.p5_r0.split.build_split_commitment",
            "manifest": "evaluation.p5_r0.fixture_generator.build_private_manifest",
            "policy": "evaluation.p5_r0.repair.repair_policy",
            "worker_contract": "P5R0WorkerContractV3",
            "evaluator_contract": "P5R0EvaluatorContractV3",
            "task_set": "P5R0TaskSetCommitmentV1",
        },
        "manifest_digest": manifest["manifest_digest"],
        "private_store_digest": private_store["store_digest"],
        "task_set_digest": task_set["task_set_digest"],
        "control_commitment_digest": control["commitment_digest"],
        "unsigned_lock_digest": lock_request["unsigned_lock_digest"],
        "input_builder_binding": input_builder,
        "time_seed_algorithm_binding": time_seed_algorithm,
        "input_builder_source_digest": input_builder["source_digest"],
        "time_seed_algorithm_source_digest": time_seed_algorithm["source_digest"],
        "diagnostic_signer": "deterministic domain-card fixture signer only; not production authority or KMS",
        "claim_boundary": "Generation is not signed-environment execution evidence.",
    }
    return {
        "split": split,
        "manifest": manifest,
        "private_store": private_store,
        "worker_contract": worker,
        "evaluator_contract": evaluator,
        "policy": policy,
        "task_set": task_set,
        "control_commitment": control,
        "lock_signing_request": lock_request,
        "bundle_input_manifest": bundle_manifest,
        "provenance": provenance,
    }


def _relative_to_root(path: Path, repository_root: Path) -> str:
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as exc:
        raise DiagnosticGenerationError("diagnostic output must be under the repository var/ root") from exc


def _write_canonical(path: Path, value: Mapping[str, Any], *, private: bool = False) -> str:
    raw = canonical_bytes(dict(value))
    # Round-trip before touching disk; this catches accidental non-canonical
    # output and keeps the file digest equal to the object digest.
    parsed = parse_canonical(raw)
    _require(parsed == dict(value), f"canonical round-trip failed for {path}")
    if path.exists():
        path.chmod(0o600)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o400 if private else 0o444)
    return canonical_digest(dict(value))


def write_diagnostic_bundle(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    seed: str = DEFAULT_SEED,
    split_seed: str = DEFAULT_SPLIT_SEED,
    repository_root: Path = REPOSITORY_ROOT,
    enforce_var_root: bool = True,
) -> dict[str, Any]:
    """Write a deterministic diagnostic bundle and return its artifact index."""
    root = Path(output_root).resolve()
    repo = Path(repository_root).resolve()
    if enforce_var_root:
        try:
            relative = root.relative_to(repo / "var")
        except ValueError as exc:
            raise DiagnosticGenerationError("output root must be under repository var/") from exc
        _require(relative.parts and "diagnostic" in root.name.lower(), "output root must be clearly labeled diagnostic")
    artifacts = build_diagnostic_artifacts(seed=seed, split_seed=split_seed)
    public_names = {
        "split": "public/split.json",
        "manifest": "public/manifest.json",
        "worker_contract": "public/worker-contract.json",
        "evaluator_contract": "public/evaluator-contract.json",
        "policy": "public/policy.json",
        "task_set": "public/task-set.json",
        "control_commitment": "public/control-commitment.json",
        "lock_signing_request": "public/lock-signing-request.json",
        "bundle_input_manifest": "public/production-bundle-input-manifest.json",
        "provenance": "public/generator-provenance.json",
    }
    index: dict[str, Any] = {
        "schema": "P5R0DiagnosticArtifactIndexV1",
        "classification": "diagnostic_generated_non_release",
        "root": _relative_to_root(root, repo),
        "private_truth_path": "private-truth/case-store.json",
        "artifacts": {},
        "private_truth": {"worker_public_output": False, "disposable_var_only": True},
        "production_outputs_created": False,
        "cloud_operations": [],
        "claim_boundary": "Artifact inventory only; no signed execution evidence.",
    }
    for name, relative in public_names.items():
        path = root / relative
        file_digest = _write_canonical(path, artifacts[name])
        self_digest_field = {
            "split": "split_digest",
            "manifest": "manifest_digest",
            "worker_contract": "digest",
            "evaluator_contract": "digest",
            "policy": None,
            "task_set": "task_set_digest",
            "control_commitment": "commitment_digest",
            "lock_signing_request": "request_digest",
            "bundle_input_manifest": "manifest_digest",
            "provenance": None,
        }[name]
        object_digest = artifacts[name].get(self_digest_field) if self_digest_field else file_digest
        index["artifacts"][name] = {
            "path": _relative_to_root(path, repo),
            "digest": object_digest,
            "file_digest": file_digest,
            "private": False,
        }
    private_path = root / "private-truth/case-store.json"
    private_file_digest = _write_canonical(private_path, artifacts["private_store"], private=True)
    index["artifacts"]["private_store"] = {
        "path": _relative_to_root(private_path, repo),
        "digest": artifacts["private_store"]["store_digest"],
        "file_digest": private_file_digest,
        "private": True,
    }
    index["manifest_digest"] = artifacts["manifest"]["manifest_digest"]
    index["private_store_digest"] = artifacts["private_store"]["store_digest"]
    index["task_set_digest"] = artifacts["task_set"]["task_set_digest"]
    index["control_commitment_digest"] = artifacts["control_commitment"]["commitment_digest"]
    index["unsigned_lock_digest"] = artifacts["lock_signing_request"]["unsigned_lock_digest"]
    index["index_digest"] = digest(index)
    _write_canonical(root / "artifact-index.json", index)
    return index


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate offline RS-062 P5-R0 diagnostic inputs")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--split-seed", default=DEFAULT_SPLIT_SEED)
    args = parser.parse_args(argv)
    try:
        index = write_diagnostic_bundle(args.output_root, seed=args.seed, split_seed=args.split_seed)
        print(json.dumps(index, sort_keys=True, separators=(",", ":")))
        return 0
    except (DiagnosticGenerationError, P5R0Error, OSError, ValueError) as exc:
        print(f"RS-062 diagnostic generation blocked: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    return _cli(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
