"""Fail-closed RS-069 IaC apply gate and append-only operation ledger.

The checked-in RS-069 plan is deliberately a repository definition with
unresolved production inputs.  This runner is the only entry point for an
approved apply attempt.  It validates the canonical plan and its RS-063/RS-068
inputs, verifies the approval recorded in the master runsheet, and stops at the
first unsatisfied operation precondition.  It does not infer production values,
invoke gcloud, call KMS/GCS/FreeTSA, deploy, start a VM, invoke a supervisor, or
execute tasks.  A future mutation-capable extension must be represented by a
new reviewed plan and operation handler; this runner will not execute commands
embedded in the current review-only plan.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.authority_binding_proposal import validate_proposal
from services.p5_r0_evaluator.deploy.bundle_definition import (
    load_definition as load_bundle_definition,
    validate_bundle_definition,
)
from services.p5_r0_evaluator.deploy.definition import (
    load_definition as load_native_definition,
    validate_definition,
)
from services.p5_r0_evaluator.deploy.execution_request import (
    load_definition as load_execution_request,
    validate_execution_request,
)
from services.p5_r0_evaluator.deploy.rs069_change_plan import (
    DEFAULT_PLAN,
    load_plan,
    validate_plan,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUNSHEET = REPOSITORY_ROOT / "docs/research/engine_substrate/P5_MASTER_RUNSHEET.md"
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-ledger.jsonl"
DEFAULT_CANDIDATE_BINDING = REPOSITORY_ROOT / "var/p5-r0-rs069r1/candidate-image-binding.json"
DEFAULT_APPROVAL_REQUEST = REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs-069r6-operation-1-approval-request.json"
_OPERATION_IDS = (
    "bind_candidate_image_digest",
    "correct_wip_provider_claim_mapping",
    "bind_self_custodied_authority_and_kms",
    "ingest_generated_bundle_to_gcs",
    "configure_cloud_run_and_confidential_space",
    "prepare_supervisor_and_run_request",
    "cleanup_or_rollback",
)
_RUNSHEET_APPROVAL = "Master explicitly approved the reviewed RS-069R6 operation-1 request for the p5-cs candidate binding."
_DEFAULT_APPROVAL_ID = "P5-MASTER-001/APPROVAL-002-RS069R6-OP1"


def _affirmative_runsheet_approval_present(text: str) -> bool:
    """Recognize an approval record, not a quoted required-text field."""
    return any(
        line.lstrip().startswith(_RUNSHEET_APPROVAL) or f"| {_RUNSHEET_APPROVAL}" in line
        for line in text.splitlines()
    )


class RS069ApplyBlocked(RuntimeError):
    """The approved attempt cannot safely proceed."""


class RS069Operation1Failure(RS069ApplyBlocked):
    """A redacted, ledger-safe failure from the operation-1 handler."""

    def __init__(self, code: str, *, command: list[str], exit_code: int, details: Mapping[str, Any] | None = None):
        super().__init__(code)
        self.code = code
        self.command = list(command)
        self.exit_code = exit_code
        self.details = dict(details or {})


_GCLOUD = Path("/home/matt/google-cloud-sdk/bin/gcloud")
_PODMAN = "podman"


def _command_result(command: list[str], *, cwd: Path, input_text: str | None = None, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            env=dict(env) if env is not None else None,
        )
    except OSError as exc:
        raise RS069Operation1Failure("runner_command_unavailable", command=command, exit_code=127) from exc


def _stderr_class(stderr: str) -> str:
    text = stderr.lower()
    for marker, label in (
        ("unauthorized", "unauthorized"),
        ("authentication", "authentication_error"),
        ("manifest", "manifest_error"),
        ("connection", "connection_error"),
        ("network", "network_error"),
        ("digest", "digest_reference_error"),
    ):
        if marker in text:
            return label
    return "unclassified_command_error"


def _operation_1(
    binding: Mapping[str, Any],
    *,
    repository_root: Path,
) -> dict[str, Any]:
    """Build, publish, and independently re-observe only the candidate image.

    All cloud-facing commands live here and are fixed by the reviewed binding;
    no command is accepted from the plan or from shell input.  Credentials are
    held only in a temporary podman auth file and are removed before return.
    """
    build = binding["build"]
    candidate = binding["candidate"]
    target = candidate["target_artifact_registry"]
    local_reference = candidate["local_image_reference"].split("@", 1)[0]
    target_reference = target["reference"]
    expected_digest = candidate["image_digest"]
    expected_image_id = candidate["image_id"]
    if (
        not _valid_digest(expected_digest)
        or not _valid_digest(expected_image_id)
        or type(target["registry_digest_verified"]) is not bool
        or type(target["push_performed"]) is not bool
    ):
        raise RS069Operation1Failure("candidate_digest_or_publication_flag_invalid", command=[], exit_code=78)
    policy = build["policy"]
    if policy != {"network": "none", "pull": "never", "runtime": "crun"}:
        raise RS069Operation1Failure("build_policy_mismatch", command=[], exit_code=78)
    if not Path(_GCLOUD).is_file() or not os.access(_GCLOUD, os.X_OK):
        raise RS069Operation1Failure("verification_tool_unavailable", command=[str(_GCLOUD)], exit_code=127)

    context = (repository_root / build["context_path"]).resolve()
    containerfile = (repository_root / "var/p5-r0-native-stage-v3-clean-rebuild/context/Containerfile").resolve()
    if not context.is_dir() or repository_root not in context.parents or not containerfile.is_file() or repository_root not in containerfile.parents:
        raise RS069Operation1Failure("locked_build_context_unavailable", command=[], exit_code=66)

    build_command = [
        _PODMAN, "build", "--pull=never", "--network=none", "--runtime=crun",
        "--file", str(containerfile), "--tag", local_reference, str(context),
    ]
    inspect_command = [_PODMAN, "image", "inspect", local_reference, "--format", "{{.Id}} {{.Digest}}"]
    if not target["registry_digest_verified"]:
        build_result = _command_result(build_command, cwd=repository_root)
        if build_result.returncode != 0:
            raise RS069Operation1Failure("candidate_build_failed", command=build_command, exit_code=build_result.returncode)
    inspect_result = _command_result(inspect_command, cwd=repository_root)
    if inspect_result.returncode != 0:
        raise RS069Operation1Failure("candidate_inspect_failed", command=inspect_command, exit_code=inspect_result.returncode)
    observed = inspect_result.stdout.strip().split()
    if (
        len(observed) != 2
        or not _valid_digest(observed[0])
        or not _valid_digest(observed[1])
        or observed[0] != expected_image_id
        or observed[1] != expected_digest
    ):
        raise RS069Operation1Failure(
            "local_digest_mismatch",
            command=inspect_command,
            exit_code=65,
            details={"expected_local_digest": expected_digest, "observed_local_digest": observed[-1] if observed else None},
        )

    provenance = dict(binding["provenance"])
    recorded_provenance = build["provenance_digest"]
    provenance_without_digest = dict(provenance)
    provenance_without_digest.pop("provenance_digest", None)
    if sha256(provenance_without_digest) != recorded_provenance or provenance.get("image_manifest_digest") != expected_digest:
        raise RS069Operation1Failure("local_provenance_mismatch", command=[], exit_code=65)

    auth_dir = Path(tempfile.mkdtemp(prefix="rs069-auth-", dir=repository_root / "var"))
    auth_path = auth_dir / "config.json"
    auth_env = os.environ.copy()
    auth_env["DOCKER_CONFIG"] = str(auth_dir)
    auth_env["REGISTRY_AUTH_FILE"] = str(auth_path)
    auth_env["PATH"] = str(_GCLOUD.parent) + os.pathsep + auth_env.get("PATH", "")
    push_attempted = False
    try:
        configure_command = [str(_GCLOUD), "auth", "configure-docker", "us-east1-docker.pkg.dev", "--quiet"]
        configure_result = _command_result(configure_command, cwd=repository_root, env=auth_env)
        if configure_result.returncode != 0 or not auth_path.is_file():
            raise RS069Operation1Failure("registry_authentication_failed", command=configure_command, exit_code=configure_result.returncode or 1)

        push_command = [_PODMAN, "push", "--authfile", str(auth_path), local_reference, target_reference]
        describe_command = [
            str(_GCLOUD), "artifacts", "docker", "images", "describe", target_reference,
            f"--project={target['project_id']}", "--format=value(image_summary.digest)",
        ]
        remote_probe = _command_result(describe_command, cwd=repository_root, env=auth_env)
        remote_digest = remote_probe.stdout.strip() if remote_probe.returncode == 0 else ""
        if remote_digest and not _valid_digest(remote_digest):
            raise RS069Operation1Failure("remote_digest_format_invalid", command=describe_command, exit_code=65, details={"observed_remote_digest": remote_digest})
        if remote_digest and remote_digest != expected_digest:
            raise RS069Operation1Failure(
                "remote_digest_mismatch",
                command=describe_command,
                exit_code=65,
                details={"expected_remote_digest": expected_digest, "observed_remote_digest": remote_digest, "push_attempted": False},
            )
        if not remote_digest:
            push_attempted = True
            push_result = _command_result(push_command, cwd=repository_root, env=auth_env)
            if push_result.returncode != 0:
                raise RS069Operation1Failure("registry_push_failed", command=push_command, exit_code=push_result.returncode, details={"push_attempted": True, "mutation_observed": False, "stderr_class": _stderr_class(push_result.stderr)})
            remote_probe = _command_result(describe_command, cwd=repository_root, env=auth_env)
            if remote_probe.returncode != 0:
                raise RS069Operation1Failure(
                    "remote_digest_verification_failed",
                    command=describe_command,
                    exit_code=remote_probe.returncode,
                    details={"push_attempted": True, "mutation_observed": True},
                )
            remote_digest = remote_probe.stdout.strip()
            if not _valid_digest(remote_digest):
                raise RS069Operation1Failure("remote_digest_format_invalid", command=describe_command, exit_code=65, details={"observed_remote_digest": remote_digest})
        if remote_digest != expected_digest:
            raise RS069Operation1Failure(
                "remote_digest_mismatch",
                command=describe_command,
                exit_code=65,
                details={"expected_remote_digest": expected_digest, "observed_remote_digest": remote_digest, "push_attempted": push_attempted},
            )
    finally:
        shutil.rmtree(auth_dir, ignore_errors=True)

    return {
        "build_command": build_command,
        "inspect_command": inspect_command,
        "configure_command": configure_command,
        "push_command": push_command,
        "describe_command": describe_command,
        "local_digest": expected_digest,
        "remote_digest": expected_digest,
        "remote_digest_verified": True,
        "remote_digest_evidence": {
            "method": "artifact_registry_digest_describe",
            "observed_digest": expected_digest,
        },
        "provenance_digest": recorded_provenance,
        "local_provenance_verified": True,
        "remote_provenance_verified": None,
        "remote_provenance_evidence": None,
        "immutable_verified": None,
        "immutability_evidence": None,
        "push_performed": push_attempted or bool(target["push_performed"]),
    }


def _write_verified_binding(path: Path, binding: Mapping[str, Any], verification: Mapping[str, Any]) -> None:
    updated = json.loads(json.dumps(binding))
    target = updated["candidate"]["target_artifact_registry"]
    target["push_performed"] = True
    target["registry_digest_verified"] = True
    target["remote_digest"] = verification["remote_digest"]
    target["remote_provenance_verified"] = verification["remote_provenance_verified"]
    target["remote_provenance_evidence"] = verification["remote_provenance_evidence"]
    target["immutable_verified"] = verification["immutable_verified"]
    target["immutability_evidence"] = verification["immutability_evidence"]
    updated["evidence_interpretation"] = {
        "immutable_verified": verification["immutable_verified"],
        "immutability_evidence": verification["immutability_evidence"],
        "local_provenance_verified": verification["local_provenance_verified"],
        "remote_digest_evidence": verification["remote_digest_evidence"],
        "remote_digest_verified": verification["remote_digest_verified"],
        "remote_provenance_evidence": verification["remote_provenance_evidence"],
        "remote_provenance_verified": verification["remote_provenance_verified"],
    }
    updated["status"] = "verified_registry_digest_pending_master_review"
    updated["classification"] = "review_only_registry_bound_non_production"
    payload = canonical_bytes(updated)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=path.name + ".", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_REMOTE_PROVENANCE_SCHEMA = "P5R0RS069RemoteProvenanceEvidenceV1"
_REMOTE_IMMUTABILITY_SCHEMA = "P5R0RS069RemoteImmutabilityEvidenceV1"
_REMOTE_PROVENANCE_SOURCE = "artifact_registry_provenance_lookup"
_REMOTE_IMMUTABILITY_SOURCE = "artifact_registry_immutability_observation"
# R15 has no authenticated runner-owned remote evidence source.  This remains
# explicitly unavailable until a reviewed runner boundary supplies one.
_AUTHENTICATED_REMOTE_PROVENANCE_SOURCE: str | None = None
_AUTHENTICATED_REMOTE_IMMUTABILITY_SOURCE: str | None = None


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None


def _canonical_value_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _valid_verification_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def _validate_canonical_remote_evidence(
    evidence: Mapping[str, Any],
    *,
    schema: str,
    source_kind: str,
    image_digest: str,
    expected_operation_id: str | None,
    expected_request_digest: str | None,
    expected_source_resource: str,
) -> None:
    """Validate an embedded, self-digesting remote observation record.

    A digest here is an integrity check over canonical bytes, not an
    authenticity claim.  Authenticity still requires the independently
    operated remote boundary; this validator therefore only admits a positive
    claim when every binding supplied by that boundary is present and exact.
    """
    evidence_fields = {"schema", "evidence_digest", "record"}
    record_fields = {
        "operation_id", "request_digest", "image_digest", "observed_digest",
        "source", "command", "verification_timestamp", "record_digest",
    }
    source_fields = {"kind", "resource"}
    command_fields = {"name", "argv", "digest"}
    if not isinstance(evidence, Mapping) or set(evidence) != evidence_fields or evidence.get("schema") != schema:
        raise ValueError("evidence schema")
    record = evidence.get("record")
    if not isinstance(record, Mapping) or set(record) != record_fields:
        raise ValueError("evidence record schema")
    if expected_operation_id is None or expected_request_digest is None:
        raise ValueError("evidence request binding unavailable")
    if record["operation_id"] != expected_operation_id or record["request_digest"] != expected_request_digest:
        raise ValueError("evidence operation/request binding")
    if (
        not isinstance(record["operation_id"], str)
        or not _DIGEST_RE.fullmatch(record["request_digest"])
        or not _DIGEST_RE.fullmatch(record["image_digest"])
        or not _DIGEST_RE.fullmatch(record["observed_digest"])
        or record["image_digest"] != image_digest
        or record["observed_digest"] != image_digest
        or not _valid_verification_timestamp(record["verification_timestamp"])
    ):
        raise ValueError("evidence digest or timestamp binding")

    source = record["source"]
    if (
        not isinstance(source, Mapping)
        or set(source) != source_fields
        or source["kind"] != source_kind
        or not isinstance(source["resource"], str)
        or not source["resource"]
        or source["resource"] != expected_source_resource
    ):
        raise ValueError("evidence source identity")

    command = record["command"]
    if (
        not isinstance(command, Mapping)
        or set(command) != command_fields
        or command["name"] != source_kind
        or not isinstance(command["argv"], list)
        or not command["argv"]
        or not all(isinstance(item, str) and item for item in command["argv"])
        or not _DIGEST_RE.fullmatch(command["digest"])
        or command["digest"] != _canonical_value_digest(command["argv"])
        or expected_source_resource not in command["argv"]
        or image_digest not in command["argv"]
    ):
        raise ValueError("evidence command identity")

    record_without_digest = {key: value for key, value in record.items() if key != "record_digest"}
    if record["record_digest"] != _canonical_value_digest(record_without_digest):
        raise ValueError("evidence record digest")
    outer_without_digest = {"schema": evidence["schema"], "record": dict(record)}
    if evidence["evidence_digest"] != _canonical_value_digest(outer_without_digest):
        raise ValueError("evidence digest")


def _validate_remote_evidence_claim(
    target: Mapping[str, Any],
    image_digest: str,
    *,
    expected_operation_id: str | None = None,
    expected_request_digest: str | None = None,
) -> tuple[Any, Any]:
    """Reject positive remote claims unless canonical evidence verifies fully."""
    remote_provenance = target.get("remote_provenance_verified")
    remote_evidence = target.get("remote_provenance_evidence")
    if remote_provenance is not None and type(remote_provenance) is not bool:
        raise RS069ApplyBlocked("RS-069R15 remote provenance state is invalid")
    if remote_provenance is True:
        if _AUTHENTICATED_REMOTE_PROVENANCE_SOURCE is None:
            raise RS069ApplyBlocked(
                "RS-069R15 remote provenance positive claim rejected: no authenticated runner-owned source"
            )
        try:
            _validate_canonical_remote_evidence(
                remote_evidence,
                schema=_REMOTE_PROVENANCE_SCHEMA,
                source_kind=_AUTHENTICATED_REMOTE_PROVENANCE_SOURCE,
                image_digest=image_digest,
                expected_operation_id=expected_operation_id,
                expected_request_digest=expected_request_digest,
                expected_source_resource=target["reference"],
            )
        except (KeyError, TypeError, ValueError):
            raise RS069ApplyBlocked("remote provenance claim lacks corresponding evidence") from None
    elif remote_evidence is not None:
        raise RS069ApplyBlocked("remote provenance evidence exists without a verified claim")

    immutable = target.get("immutable_verified")
    immutability_evidence = target.get("immutability_evidence")
    if immutable is not None and type(immutable) is not bool:
        raise RS069ApplyBlocked("RS-069R15 immutability state is invalid")
    if immutable is True:
        if _AUTHENTICATED_REMOTE_IMMUTABILITY_SOURCE is None:
            raise RS069ApplyBlocked(
                "RS-069R15 remote immutability positive claim rejected: no authenticated runner-owned source"
            )
        try:
            _validate_canonical_remote_evidence(
                immutability_evidence,
                schema=_REMOTE_IMMUTABILITY_SCHEMA,
                source_kind=_AUTHENTICATED_REMOTE_IMMUTABILITY_SOURCE,
                image_digest=image_digest,
                expected_operation_id=expected_operation_id,
                expected_request_digest=expected_request_digest,
                expected_source_resource=target["reference"],
            )
        except (KeyError, TypeError, ValueError):
            raise RS069ApplyBlocked("remote immutability claim lacks an observation") from None
    if immutable is not True and immutability_evidence is not None:
        raise RS069ApplyBlocked("immutability evidence exists without an observed claim")
    return remote_provenance, immutable


def _raw_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RS069ApplyBlocked(f"{label} is unavailable or malformed") from exc
    if not isinstance(value, dict):
        raise RS069ApplyBlocked(f"{label} must be an object")
    return value


def _load_candidate_binding(
    path: Path,
    repository_root: Path,
    *,
    evidence_request_digest: str | None = None,
) -> dict[str, Any]:
    """Consume and validate the RS-069R1 review-only image binding.

    This is an input-integrity check only.  It never treats a local manifest as
    registry publication or production provenance, and it never performs a
    registry/cloud operation.
    """
    try:
        binding = parse_canonical(Path(path).read_bytes())
    except Exception as exc:
        raise RS069ApplyBlocked("RS-069R1 candidate binding is unavailable or not canonical") from exc
    if binding.get("schema") != "P5R0RS069R1CandidateImageBindingV1":
        raise RS069ApplyBlocked("RS-069R1 candidate binding schema drift")
    if binding.get("status") not in {"blocked_pending_master_review", "verified_registry_digest_pending_master_review"} or binding.get("classification") not in {"review_only_local_candidate_non_production", "review_only_registry_bound_non_production"}:
        raise RS069ApplyBlocked("RS-069R1 candidate binding is not review-only")
    try:
        relative = Path(binding["artifact"]["path"])
        if relative.is_absolute() or (repository_root / relative).resolve() != Path(path).resolve():
            raise RS069ApplyBlocked("RS-069R1 artifact path drift")
        candidate = binding["candidate"]
        target = candidate["target_artifact_registry"]
        image_digest = candidate["image_digest"]
        target_repository = target["repository"]
        target_reference = target["reference"]
        digest_values = (
            image_digest,
            candidate["image_id"],
            candidate["image_manifest_digest"],
            binding["build"]["image_id"],
            binding["build"]["image_manifest_digest"],
            binding["build"]["provenance_digest"],
            binding["closure"]["image_digest"],
            binding["closure"]["closure_digest"],
        )
        if (
            not all(_valid_digest(value) for value in digest_values)
            or (target.get("remote_digest") is not None and not _valid_digest(target["remote_digest"]))
        ):
            raise RS069ApplyBlocked("RS-069R1 candidate or remote digest is invalid")
        expected_reference = f"{target['region']}-docker.pkg.dev/{target['project_id']}/{target_repository}/{target['image']}@{image_digest}"
        if (
            target["project_id"] != "ocelot-proof"
            or target["region"] != "us-east1"
            or target_repository != "p5-cs"
            or target["image"] != "evaluator"
            or target_reference != expected_reference
        ):
            raise RS069ApplyBlocked("RS-069R1 target image binding drift")
        if type(target["registry_digest_verified"]) is not bool or type(target["push_performed"]) is not bool:
            raise RS069ApplyBlocked("RS-069R1 registry boundary flags must be booleans")
        if candidate["image_manifest_digest"] != image_digest:
            raise RS069ApplyBlocked("RS-069R1 registry boundary drift")
        if target["registry_digest_verified"] and target.get("remote_digest") != image_digest:
            raise RS069ApplyBlocked("RS-069R1 verified remote digest drift")
        remote_provenance, immutable = _validate_remote_evidence_claim(
            target,
            image_digest,
            expected_operation_id="bind_candidate_image_digest",
            expected_request_digest=evidence_request_digest,
        )
        interpretation = binding.get("evidence_interpretation")
        if not isinstance(interpretation, Mapping) or set(interpretation) != {
            "immutable_verified", "immutability_evidence", "local_provenance_verified",
            "remote_digest_evidence", "remote_digest_verified", "remote_provenance_evidence",
            "remote_provenance_verified",
        }:
            raise RS069ApplyBlocked("RS-069R15 evidence interpretation is missing or not closed")
        digest_evidence = interpretation["remote_digest_evidence"]
        strict_boolean_fields = (
            "local_provenance_verified", "remote_digest_verified",
        )
        if any(type(interpretation[field]) is not bool for field in strict_boolean_fields):
            raise RS069ApplyBlocked("RS-069R15 evidence booleans must be booleans")
        for nullable_field in ("remote_provenance_verified", "immutable_verified"):
            if interpretation[nullable_field] is not None and type(interpretation[nullable_field]) is not bool:
                raise RS069ApplyBlocked("RS-069R15 evidence booleans must be booleans or null")
        if not isinstance(digest_evidence, Mapping) or set(digest_evidence) != {"method", "observed_digest"}:
            raise RS069ApplyBlocked("RS-069R15 evidence digest is missing or not closed")
        if not _valid_digest(digest_evidence["observed_digest"]):
            raise RS069ApplyBlocked("RS-069R15 evidence digest is invalid")
        if (
            interpretation["local_provenance_verified"] is not True
            or interpretation["remote_digest_verified"] is not target["registry_digest_verified"]
            or interpretation["remote_provenance_verified"] is not remote_provenance
            or interpretation["remote_provenance_evidence"] != target.get("remote_provenance_evidence")
            or interpretation["immutable_verified"] is not immutable
            or interpretation["immutability_evidence"] != target.get("immutability_evidence")
            or digest_evidence["method"] != "artifact_registry_digest_describe"
            or digest_evidence["observed_digest"] != target.get("remote_digest")
        ):
            raise RS069ApplyBlocked("RS-069R15 evidence interpretation is inconsistent")
        if target["registry_digest_verified"] and interpretation["remote_digest_verified"] is not True:
            raise RS069ApplyBlocked("RS-069R15 remote digest verification is missing")
        closure = binding["closure"]
        if closure["image_digest"] != image_digest or closure["closure_digest"] != "sha256:4f49f208c6e65d87c5c50b90a316a1314298719425dde0858d66b33ceabed5c3":
            raise RS069ApplyBlocked("RS-069R1 closure binding drift")
        required = binding["iac_input_commitment"]["required_inputs"]
        if binding["iac_input_commitment"]["operation_id"] != "bind_candidate_image_digest":
            raise RS069ApplyBlocked("RS-069R1 operation binding drift")
        if binding["iac_input_commitment"]["commitment_digest"] != sha256(required):
            raise RS069ApplyBlocked("RS-069R1 IaC commitment digest drift")
        if required != {
            "candidate_image_digest": image_digest,
            "image_provenance_digest": binding["build"]["provenance_digest"],
            "image_reference": target_reference,
            "target_project_id": target["project_id"],
            "target_region": target["region"],
            "target_repository": target_repository,
        }:
            raise RS069ApplyBlocked("RS-069R1 IaC required inputs drift")
        provenance = binding["provenance"]
        validation = binding["validation"]
        for section, fields in (
            (provenance, ("dirty_worktree", "registry_push_performed")),
            (validation, (
                "closure_recomputed", "image_id_matches_build_result",
                "production_promotable", "registry_push_performed",
                "target_reference_derived_from_reviewed_project_region_repository",
            )),
        ):
            if any(type(section[field]) is not bool for field in fields):
                raise RS069ApplyBlocked("RS-069R15 evidence booleans must be booleans")
    except (KeyError, TypeError, ValueError) as exc:
        raise RS069ApplyBlocked("RS-069R1 candidate binding is malformed") from exc
    return {
        "path": str(Path(path)),
        "binding_digest": sha256(binding),
        "image_digest": image_digest,
        "closure_digest": closure["closure_digest"],
        "registry_digest_verified": target["registry_digest_verified"],
        "remote_provenance_verified": remote_provenance,
        "immutable_verified": immutable,
        "push_performed": target["push_performed"],
        "production_promotable": binding["validation"]["production_promotable"],
    }


def _load_approval_request(
    path: Path,
    *,
    candidate_info: Mapping[str, Any],
    approval_id: str,
    runsheet_text: str,
) -> dict[str, Any]:
    """Validate the canonical R6 request before any ledger or cloud boundary.

    The request is the authoritative local approval artifact.  A runsheet
    sentence alone must never authorize operation 1, and a pending request
    must not coexist with the affirmative approval literal.
    """
    try:
        request = parse_canonical(path.read_bytes())
    except Exception as exc:
        raise RS069ApplyBlocked("RS-069R6 approval request is unavailable or not canonical") from exc
    expected_fields = {
        "approval", "bound_candidate", "classification", "forbidden_operations",
        "master_run", "prior_attempt", "request_id", "runsheet_item", "status",
        "target", "workflow",
    }
    if set(request) != expected_fields:
        raise RS069ApplyBlocked("RS-069R6 approval request fields are not closed")
    approval = request["approval"]
    if not isinstance(approval, Mapping) or set(approval) != {
        "approval_id", "approved", "master_approved", "required_text", "scope", "user_approved",
    }:
        raise RS069ApplyBlocked("RS-069R6 approval record fields are not closed")
    if approval_id != _DEFAULT_APPROVAL_ID or approval["approval_id"] != _DEFAULT_APPROVAL_ID:
        raise RS069ApplyBlocked("approval id is not the new RS-069R6 operation-1 approval")
    if approval["required_text"] != _RUNSHEET_APPROVAL:
        raise RS069ApplyBlocked("RS-069R6 approval literal does not match the runner")
    if approval["scope"] != ["bind_candidate_image_digest"]:
        raise RS069ApplyBlocked("RS-069R6 approval scope is not operation 1 only")
    flags = (approval["approved"], approval["master_approved"], approval["user_approved"])
    if not all(type(value) is bool for value in flags) or len(set(flags)) != 1:
        raise RS069ApplyBlocked("RS-069R6 approval flags are inconsistent")
    enabled = flags[0]
    workflow = request["workflow"]
    if not isinstance(workflow, Mapping) or set(workflow) != {
        "apply_interface", "commands", "execute_operation_1", "later_operations_enabled", "mutations_performed",
    }:
        raise RS069ApplyBlocked("RS-069R6 workflow fields are not closed")
    if workflow["execute_operation_1"] is not enabled or workflow["later_operations_enabled"] is not False or workflow["mutations_performed"] is not False or workflow["commands"] != []:
        raise RS069ApplyBlocked("RS-069R6 operation flags or mutation boundary are inconsistent")
    if request["master_run"] != "P5-MASTER-001" or request["runsheet_item"] != "RS-069R6":
        raise RS069ApplyBlocked("RS-069R6 approval identity drift")
    if request["status"] != ("approved_pending_operation_1" if enabled else "blocked_pending_new_master_approval"):
        raise RS069ApplyBlocked("RS-069R6 approval status does not match its flags")
    if enabled and not _affirmative_runsheet_approval_present(runsheet_text):
        raise RS069ApplyBlocked("approved RS-069R6 request is missing the exact runsheet approval literal")
    if not enabled and _affirmative_runsheet_approval_present(runsheet_text):
        raise RS069ApplyBlocked("pending RS-069R6 request conflicts with affirmative runsheet approval text")

    target = request["target"]
    bound = request["bound_candidate"]
    if not isinstance(target, Mapping) or target.get("repository") != "p5-cs" or target.get("region") != "us-east1" or target.get("project_id") != "ocelot-proof" or target.get("image") != "evaluator":
        raise RS069ApplyBlocked("RS-069R6 target binding drift")
    if not isinstance(bound, Mapping) or bound.get("binding_digest") != candidate_info["binding_digest"] or bound.get("candidate_image_digest") != candidate_info["image_digest"] or bound.get("closure_digest") != candidate_info["closure_digest"]:
        raise RS069ApplyBlocked("RS-069R6 candidate binding digest drift")
    expected_reference = f"{target['region']}-docker.pkg.dev/{target['project_id']}/{target['repository']}/{target['image']}@{bound['candidate_image_digest']}"
    if bound.get("reference") != expected_reference or bound.get("push_performed") is not False or bound.get("registry_digest_verified") is not False or bound.get("production_promotable") is not False:
        raise RS069ApplyBlocked("RS-069R6 candidate publication boundary drift")
    if request["prior_attempt"] != {
        "approval_id": "P5-MASTER-001/APPROVAL-001",
        "status": "failed_closed",
        "success_reused": False,
    }:
        raise RS069ApplyBlocked("RS-069R6 prior approval reuse boundary drift")
    return {
        "approval_request_digest": sha256(request),
        "approval_id": approval["approval_id"],
        "scope": list(approval["scope"]),
        "approved": enabled,
    }


def _approval_record(runsheet: Path, approval_id: str) -> dict[str, Any]:
    try:
        text = runsheet.read_text()
    except OSError as exc:
        raise RS069ApplyBlocked("master runsheet is unavailable") from exc
    if approval_id != _DEFAULT_APPROVAL_ID:
        raise RS069ApplyBlocked("approval id is not the new RS-069R6 operation-1 approval")
    if approval_id not in text:
        raise RS069ApplyBlocked("new RS-069R6 operation-1 approval record is not present in the master runsheet")
    return {
        "approval_id": approval_id,
        "master_run": "P5-MASTER-001",
        "runsheet_item": "RS-069R6",
        "scope": ["bind_candidate_image_digest"],
        "approval_text_verified": _affirmative_runsheet_approval_present(text),
        "runsheet_digest": _raw_digest(runsheet),
    }


def _append_only_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    previous: str | None = None
    try:
        lines = path.read_bytes().splitlines()
    except OSError as exc:
        raise RS069ApplyBlocked("operation ledger cannot be read") from exc
    for number, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RS069ApplyBlocked(f"operation ledger is malformed at line {number}") from exc
        if not isinstance(record, dict):
            raise RS069ApplyBlocked(f"operation ledger record is not an object at line {number}")
        if record.get("previous_event_digest") != previous:
            raise RS069ApplyBlocked(f"operation ledger hash chain is broken at line {number}")
        event_digest = record.get("event_digest")
        if not isinstance(event_digest, str):
            raise RS069ApplyBlocked(f"operation ledger event digest is missing at line {number}")
        expected = sha256({key: value for key, value in record.items() if key != "event_digest"})
        if event_digest != expected:
            raise RS069ApplyBlocked(f"operation ledger event digest mismatch at line {number}")
        previous = event_digest
        records.append(record)
    return records


def _write_event(path: Path, record: Mapping[str, Any], previous: str | None) -> dict[str, Any]:
    body = dict(record)
    body["previous_event_digest"] = previous
    body["event_digest"] = sha256(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = canonical_bytes(body) + b"\n"
    try:
        with path.open("ab") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise RS069ApplyBlocked("operation ledger append failed") from exc
    return body


def _validate_supporting_definitions(root: Path) -> dict[str, Any]:
    """Validate supporting definitions without treating blocked reports as passes."""
    try:
        native = validate_definition(load_native_definition(root / "services/p5_r0_evaluator/deploy/p5-r0-native-deployment.json"), repository_root=root)
        bundle = validate_bundle_definition(load_bundle_definition(root / "services/p5_r0_evaluator/deploy/p5-r0-production-bundle.json"), repository_root=root)
        request = validate_execution_request(
            load_execution_request(root / "services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json"),
            repository_root=root,
        )
        proposal = validate_proposal(
            root / "var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json",
            root / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json",
            root / "services/p5_r0_evaluator/deploy/rs-068-wip-policy-remediation.json",
        )
    except Exception as exc:
        raise RS069ApplyBlocked("supporting RS-040/RS-060/RS-063/RS-068 validation failed") from exc
    return {
        "RS-040": {"ready": native.ready, "definition_digest": native.definition_digest},
        "RS-060": {"ready": bundle.ready, "definition_digest": bundle.definition_digest},
        "RS-063": {"ready": request.ready, "definition_digest": request.definition_digest},
        "RS-068": {
            "status": proposal["status"],
            "authority_id_resolved": proposal["authority_id_resolved"],
            "production_promotable": proposal["production_promotable"],
            "signature_present": proposal["signature_present"],
        },
    }


def _first_blocked_operation(plan: Mapping[str, Any], unresolved: list[str]) -> tuple[Mapping[str, Any], list[str]]:
    operations = plan.get("operations")
    if not isinstance(operations, list) or tuple(item.get("id") for item in operations) != _OPERATION_IDS:
        raise RS069ApplyBlocked("RS-069 operation ids are not closed")
    first_id = _OPERATION_IDS[0]
    missing = [item for item in unresolved if item.startswith(first_id + ".")]
    return operations[0], missing


def apply(
    *,
    repository_root: Path = REPOSITORY_ROOT,
    plan_path: Path = DEFAULT_PLAN,
    runsheet_path: Path = DEFAULT_RUNSHEET,
    ledger_path: Path = DEFAULT_LEDGER,
    candidate_binding_path: Path | None = DEFAULT_CANDIDATE_BINDING,
    approval_request_path: Path = DEFAULT_APPROVAL_REQUEST,
    approval_id: str = _DEFAULT_APPROVAL_ID,
    execute_operation_1: bool = False,
) -> dict[str, Any]:
    """Run preflight, or explicitly execute only the approved operation 1."""
    root = Path(repository_root).resolve()
    if Path.cwd().resolve() != root:
        raise RS069ApplyBlocked("runner must be invoked with repository root as pwd")
    plan = load_plan(Path(plan_path))
    report = validate_plan(plan, repository_root=root)
    if tuple(report.operation_ids) != _OPERATION_IDS:
        raise RS069ApplyBlocked("RS-069 operation ids are not closed")
    approval = _approval_record(Path(runsheet_path), approval_id)
    supporting = _validate_supporting_definitions(root)
    if candidate_binding_path is not None:
        try:
            approval_request_digest = sha256(parse_canonical(Path(approval_request_path).read_bytes()))
        except Exception:
            approval_request_digest = None
        supporting["RS-069R1"] = _load_candidate_binding(
            Path(candidate_binding_path), root, evidence_request_digest=approval_request_digest
        )
    candidate_info = supporting.get("RS-069R1")
    if candidate_info is None:
        raise RS069ApplyBlocked("RS-069R6 approval requires the reviewed candidate binding")
    approval_request = _load_approval_request(
        Path(approval_request_path),
        candidate_info=candidate_info,
        approval_id=approval_id,
        runsheet_text=Path(runsheet_path).read_text(),
    )
    if not approval_request["approved"]:
        raise RS069ApplyBlocked("RS-069R6 operation-1 approval is not enabled")
    approval["approval_request_digest"] = approval_request["approval_request_digest"]
    records = _append_only_records(Path(ledger_path))
    previous = records[-1]["event_digest"] if records else None
    plan_digest = report.plan_digest
    mode = "operation_1" if execute_operation_1 else "preflight"
    binding_digest = candidate_info.get("binding_digest") if candidate_info else None
    attempt_id = f"rs069-{mode}-{plan_digest.removeprefix('sha256:')[:16]}"

    # Exact repeat of a previously stopped attempt is a rerunnable no-op.  The
    # mode and binding digest are part of the idempotency boundary so a prior
    # review-only stop cannot suppress the explicitly approved operation 1.
    if (
        records
        and records[-1].get("kind") == "run_stopped"
        and records[-1].get("plan_digest") == plan_digest
        and records[-1].get("approval") == approval
        and records[-1].get("runner_mode") == mode
        and records[-1].get("candidate_binding_digest") == binding_digest
        and (not execute_operation_1 or "verified_event_digest" in records[-1])
    ):
        return {
            "status": "no_op",
            "attempt_id": records[-1].get("attempt_id", attempt_id),
            "plan_digest": plan_digest,
            "ledger_path": str(Path(ledger_path)),
            "ledger_digest": _raw_digest(Path(ledger_path)),
            "operation_ids": list(_OPERATION_IDS),
            "cloud_operations": records[-1].get("cloud_operations", []),
            "mutations_performed": records[-1].get("mutations_performed", False),
            "rollback_status": records[-1].get("rollback_status", "not_applicable_no_mutation"),
        }

    start = _write_event(
        Path(ledger_path),
        {
            "schema": "P5R0RS069OperationLedgerEventV1",
            "kind": "run_started",
            "attempt_id": attempt_id,
            "runner_mode": mode,
            "candidate_binding_digest": binding_digest,
            "plan_digest": plan_digest,
            "approval": approval,
            "operation_ids": list(_OPERATION_IDS),
            "supporting_definition_status": supporting,
            "pwd": str(Path.cwd()),
            "cloud_operations": [],
            "mutations_performed": False,
        },
        previous,
    )
    previous = start["event_digest"]
    operation = plan["operations"][0]

    if execute_operation_1:
        try:
            if candidate_binding_path is None or candidate_info is None:
                raise RS069ApplyBlocked("operation 1 requires the reviewed candidate binding")
            binding = parse_canonical(Path(candidate_binding_path).read_bytes())
            verification = _operation_1(binding, repository_root=root)
            if not candidate_info["registry_digest_verified"]:
                _write_verified_binding(Path(candidate_binding_path), binding, verification)
            success = _write_event(
                Path(ledger_path),
                {
                    "schema": "P5R0RS069OperationLedgerEventV1",
                    "kind": "operation_verified",
                    "attempt_id": attempt_id,
                    "runner_mode": mode,
                    "candidate_binding_digest": binding_digest,
                    "plan_digest": plan_digest,
                    "operation_id": operation["id"],
                    "operation_order": operation["order"],
                    "operation_ids_closed": True,
                    "idempotency_key": operation["rerunnable"]["idempotency_key"].replace("{candidate_image_digest}", verification["remote_digest"]),
                    "preconditions": {"dependencies_satisfied": True, "inputs_resolved": True, "approval_present": True, "remote_state_verified": True},
                    "verification": {
                        key: value
                        for key, value in verification.items()
                        if key.endswith("digest")
                        or key.endswith("verified")
                        or key == "push_performed"
                        or key.endswith("_evidence")
                    },
                    "commands": {key: ["<temporary-auth-file>" if "rs069-auth-" in item else item for item in value] for key, value in verification.items() if key.endswith("command")},
                    "later_operations_skipped": list(_OPERATION_IDS[operation["order"]:]),
                    "rollback_status": "not_required_verified",
                    "cloud_operations": ["artifact_registry_push", "artifact_registry_digest_describe"],
                    "mutations_performed": True,
                },
                previous,
            )
            stopped = _write_event(
                Path(ledger_path),
                {
                    "schema": "P5R0RS069OperationLedgerEventV1",
                    "kind": "run_stopped",
                    "attempt_id": attempt_id,
                    "runner_mode": mode,
                    "candidate_binding_digest": binding_digest,
                    "plan_digest": plan_digest,
                    "approval": approval,
                    "stopped_after_operation_id": operation["id"],
                    "verified_event_digest": success["event_digest"],
                    "rollback_status": "not_required_verified",
                    "cloud_operations": ["artifact_registry_push", "artifact_registry_digest_describe"],
                    "mutations_performed": True,
                    "claim_boundary": "Only operation 1 registry binding was executed; operations 2-7 were skipped; no signed execution or release claim.",
                },
                success["event_digest"],
            )
            return {
                "status": "verified",
                "attempt_id": attempt_id,
                "plan_digest": plan_digest,
                "ledger_path": str(Path(ledger_path)),
                "ledger_digest": _raw_digest(Path(ledger_path)),
                "operation_ids": list(_OPERATION_IDS),
                "verified_operation_id": operation["id"],
                "remote_digest": verification["remote_digest"],
                "remote_digest_verified": verification["remote_digest_verified"],
                "provenance_digest": verification["provenance_digest"],
                "local_provenance_verified": verification["local_provenance_verified"],
                "remote_provenance_verified": verification["remote_provenance_verified"],
                "immutable_verified": verification["immutable_verified"],
                "cloud_operations": ["artifact_registry_push", "artifact_registry_digest_describe"],
                "mutations_performed": True,
                "rollback_status": "not_required_verified",
                "stop_event_digest": stopped["event_digest"],
            }
        except (RS069Operation1Failure, RS069ApplyBlocked, OSError, ValueError) as exc:
            if isinstance(exc, RS069Operation1Failure):
                code = exc.code
                exit_code = exc.exit_code
                command = exc.command
                details = exc.details
            else:
                code = "operation_1_precondition_failure"
                exit_code = 2
                command = []
                details = {}
            safe_command = ["<temporary-auth-file>" if "rs069-auth-" in item else item for item in command]
            mutation = bool(details.get("mutation_observed"))
            push_attempted = bool(details.get("push_attempted"))
            rollback_status = "manual_review_required_no_rollback" if push_attempted else "not_applicable_no_mutation"
            failure = _write_event(
                Path(ledger_path),
                {
                    "schema": "P5R0RS069OperationLedgerEventV1",
                    "kind": "operation_failed_closed",
                    "attempt_id": attempt_id,
                    "runner_mode": mode,
                    "candidate_binding_digest": binding_digest,
                    "plan_digest": plan_digest,
                    "operation_id": operation["id"],
                    "operation_order": operation["order"],
                    "operation_ids_closed": True,
                    "preconditions": {"dependencies_satisfied": True, "inputs_resolved": False, "approval_present": True, "remote_state_verified": False},
                    "error": {"code": code, "redacted": True, "exit_code": exit_code, "command": safe_command, "details": details, "later_operations_skipped": list(_OPERATION_IDS[operation["order"]:])},
                    "rollback_status": rollback_status,
                    "cloud_operations": ["artifact_registry_push"] if push_attempted else [],
                    "mutations_performed": mutation,
                },
                previous,
            )
            stopped = _write_event(
                Path(ledger_path),
                {
                    "schema": "P5R0RS069OperationLedgerEventV1",
                    "kind": "run_stopped",
                    "attempt_id": attempt_id,
                    "runner_mode": mode,
                    "candidate_binding_digest": binding_digest,
                    "plan_digest": plan_digest,
                    "approval": approval,
                    "stopped_after_operation_id": operation["id"],
                    "failure_event_digest": failure["event_digest"],
                    "rollback_status": rollback_status,
                    "cloud_operations": ["artifact_registry_push"] if push_attempted else [],
                    "mutations_performed": mutation,
                    "claim_boundary": "Operation 1 failed closed; operations 2-7 were skipped; no signed execution or release claim.",
                },
                failure["event_digest"],
            )
            return {
                "status": "failed_closed",
                "attempt_id": attempt_id,
                "plan_digest": plan_digest,
                "ledger_path": str(Path(ledger_path)),
                "ledger_digest": _raw_digest(Path(ledger_path)),
                "operation_ids": list(_OPERATION_IDS),
                "failed_operation_id": operation["id"],
                "failure_event_digest": failure["event_digest"],
                "stop_event_digest": stopped["event_digest"],
                "cloud_operations": ["artifact_registry_push"] if mutation else [],
                "mutations_performed": mutation,
                "rollback_status": "manual_review_required_no_rollback" if mutation else "not_applicable_no_mutation",
                "exit_code": exit_code,
            }

    missing = [item for item in report.unresolved_inputs if item.startswith(operation["id"] + ".")]
    if not missing:
        missing = [f"{operation['id']}.operation_1_execution_disabled"]
    failure = _write_event(
        Path(ledger_path),
        {
            "schema": "P5R0RS069OperationLedgerEventV1",
            "kind": "operation_failed_closed",
            "attempt_id": attempt_id,
            "runner_mode": mode,
            "candidate_binding_digest": binding_digest,
            "plan_digest": plan_digest,
            "operation_id": operation["id"],
            "operation_order": operation["order"],
            "operation_ids_closed": True,
            "idempotency_key": operation["rerunnable"]["idempotency_key"],
            "preconditions": {"dependencies_satisfied": True, "inputs_resolved": False, "approval_present": True, "remote_state_verified": False},
            "error": {"code": "required_inputs_unresolved", "redacted": True, "missing_input_names": missing, "later_operations_skipped": list(_OPERATION_IDS[operation["order"]:])},
            "rollback_status": "not_applicable_no_mutation",
            "cloud_operations": [],
            "mutations_performed": False,
        },
        previous,
    )
    stopped = _write_event(
        Path(ledger_path),
        {
            "schema": "P5R0RS069OperationLedgerEventV1",
            "kind": "run_stopped",
            "attempt_id": attempt_id,
            "runner_mode": mode,
            "candidate_binding_digest": binding_digest,
            "plan_digest": plan_digest,
            "approval": approval,
            "stopped_after_operation_id": operation["id"],
            "failure_event_digest": failure["event_digest"],
            "rollback_status": "not_applicable_no_mutation",
            "cloud_operations": [],
            "mutations_performed": False,
            "claim_boundary": "No cloud mutation, signature, ingestion, activation, supervisor evidence, task result, or release claim.",
        },
        failure["event_digest"],
    )
    return {
        "status": "failed_closed",
        "attempt_id": attempt_id,
        "plan_digest": plan_digest,
        "ledger_path": str(Path(ledger_path)),
        "ledger_digest": _raw_digest(Path(ledger_path)),
        "operation_ids": list(_OPERATION_IDS),
        "failed_operation_id": operation["id"],
        "failed_operation_order": operation["order"],
        "failure_event_digest": failure["event_digest"],
        "stop_event_digest": stopped["event_digest"],
        "cloud_operations": [],
        "mutations_performed": False,
        "rollback_status": "not_applicable_no_mutation",
    }


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the fail-closed RS-069 IaC apply gate")
    parser.add_argument("command", choices=("apply",))
    parser.add_argument("--approval-id", default=_DEFAULT_APPROVAL_ID)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--runsheet", type=Path, default=DEFAULT_RUNSHEET)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--candidate-binding", type=Path, default=DEFAULT_CANDIDATE_BINDING)
    parser.add_argument("--approval-request", type=Path, default=DEFAULT_APPROVAL_REQUEST)
    parser.add_argument("--execute-operation-1", action="store_true", help="execute only the approved candidate image registry binding")
    args = parser.parse_args(argv)
    try:
        result = apply(
            repository_root=args.repository_root,
            plan_path=args.plan,
            runsheet_path=args.runsheet,
            ledger_path=args.ledger,
            candidate_binding_path=args.candidate_binding,
            approval_request_path=args.approval_request,
            approval_id=args.approval_id,
            execute_operation_1=args.execute_operation_1,
        )
    except (RS069ApplyBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": "redacted_precondition_failure", "error_type": type(exc).__name__}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 2 if result["status"] == "failed_closed" else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())


__all__ = ["DEFAULT_LEDGER", "RS069ApplyBlocked", "apply"]
