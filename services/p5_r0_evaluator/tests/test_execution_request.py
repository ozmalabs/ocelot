from copy import deepcopy
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

import pytest

from evaluation.p0a.canonical import canonical_bytes, parse_canonical
from services.p5_r0_evaluator.deploy.execution_request import (
    DEFAULT_DEFINITION,
    ExecutionRequestBlockedError,
    ExecutionRequestValidationError,
    _audit_payload,
    _cli,
    load_definition,
    validate_execution_request,
)


def test_checked_in_request_is_canonical_bound_and_blocked():
    raw = DEFAULT_DEFINITION.read_bytes()
    definition = load_definition()
    assert canonical_bytes(definition) == raw

    report = validate_execution_request(definition)
    assert report.ready is False
    assert report.status == "blocked_pending_approval"
    assert report.definition_digest.startswith("sha256:")
    assert report.cloud_operations == ()
    assert report.artifact_digests[0] == (
        "artifact-index",
        "sha256:04a98e3e48685228fd68ea757de276fe1c1a7ce347bd027a2756a48595897768",
    )
    assert definition["kms_lock_signing"]["unsigned_lock_digest"] == (
        "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"
    )
    assert definition["status"] == "blocked_pending_approval"



def test_reviewed_repository_drift_is_rejected():
    definition = deepcopy(load_definition())
    definition["target_environment"]["image"]["repository"] = "p5"
    with pytest.raises(ExecutionRequestValidationError, match="target image must remain unresolved"):
        validate_execution_request(definition)


def test_strict_approval_validation_remains_blocked():
    with pytest.raises(ExecutionRequestBlockedError, match="blocked_pending_approval"):
        validate_execution_request(load_definition(), require_approval=True)


def test_cli_allow_blocked_succeeds_and_strict_cli_returns_blocked(capsys):
    assert _cli(["validate", "--allow-blocked"]) == 0
    assert "blocked_pending_approval" in capsys.readouterr().out

    assert _cli(["validate"]) == 2
    assert "RS-063 validation blocked" in capsys.readouterr().err


def test_audit_is_canonical_and_declares_no_operations(tmp_path: Path):
    output = tmp_path / "rs063-audit.json"
    assert _cli(["audit", "--allow-blocked", "--output", str(output)]) == 0
    payload = parse_canonical(output.read_bytes())
    assert payload["status"] == "blocked_pending_approval"
    assert payload["ready"] is False
    assert payload["cloud_operations"] == []
    assert payload["mutations_performed"] is False


def test_artifact_bindings_reject_digest_drift():
    definition = deepcopy(load_definition())
    definition["artifact_bindings"]["manifest"]["digest"] = "sha256:" + "0" * 64
    with pytest.raises(ExecutionRequestValidationError, match="artifact bindings drift"):
        validate_execution_request(definition)


def test_request_rejects_signature_or_cloud_bound_values():
    definition = deepcopy(load_definition())
    definition["kms_lock_signing"]["signature"] = "unexpected"
    with pytest.raises(ExecutionRequestValidationError, match="KMS signing operation"):
        validate_execution_request(definition)

    definition = deepcopy(load_definition())
    definition["iam_wip_bridge_commitments"]["project_id"] = "observed-project"
    with pytest.raises(ExecutionRequestValidationError, match="must remain null"):
        validate_execution_request(definition)


def test_request_preserves_review_only_mutation_boundary():
    definition = load_definition()
    assert definition["apply_plan"]["commands"] == []
    assert definition["apply_plan"]["mutations_performed"] is False
    assert definition["ingestion_plan"]["upload_performed"] is False
    assert definition["kms_lock_signing"]["kms_call_performed"] is False
    assert all(step["enabled"] is False for step in definition["run_order"])
    assert all(step["mutating"] is False for step in definition["run_order"][:5])
    assert all(step["mutating"] is True for step in definition["run_order"][5:])
    assert set(("gcloud mutation", "VM creation", "KMS signing", "GCS upload", "secret access", "FreeTSA call", "task submission")).issubset(
        set(definition["apply_plan"]["forbidden_operations"])
    )
    assert all("gcloud" not in command.lower() for command in definition["commands"].values())



def _copy_definition_sources_without_var(tmp_path: Path, definition: dict) -> Path:
    source_paths = set(definition["source_files"].values())
    for contract_path in (
        Path("services/p5_r0_evaluator/deploy/p5-r0-native-deployment.json"),
        Path("services/p5_r0_evaluator/deploy/p5-r0-production-bundle.json"),
    ):
        contract = json.loads(contract_path.read_text())
        source_paths.update(value for value in contract["source_files"].values() if not value.startswith("/"))
    source_paths.update(
        {
            "services/p5_r0_evaluator/deploy/p5-r0-native-deployment.json",
            "services/p5_r0_evaluator/deploy/p5-r0-production-bundle.json",
            "services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json",
        }
    )
    for relative in source_paths:
        source = Path(relative)
        if not source.is_file():
            continue
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    # Copy the complete import closure used by the local CLI, but not tests or
    # disposable var/ inputs.  The subprocess below must import these copies.
    for root in (
        Path("evaluation/p0a"),
        Path("evaluation/p5_r0"),
        Path("services/cs_attestation_probe"),
        Path("services/p5_r0_evaluator"),
    ):
        for source in root.rglob("*.py"):
            if "tests" in source.parts:
                continue
            target = tmp_path / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return tmp_path


def test_clean_checkout_without_var_inputs_uses_isolated_subprocess_validator(tmp_path: Path):
    definition = load_definition()
    repository = _copy_definition_sources_without_var(tmp_path / "checkout", definition)
    definition_path = repository / "services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repository)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "services.p5_r0_evaluator.deploy.execution_request",
            "validate",
            "--allow-blocked",
            "--definition",
            str(definition_path),
        ],
        cwd=repository,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["status"] == "blocked_pending_approval"
    assert audit["ready"] is False
    assert audit["cloud_operations"] == []
    assert audit["mutations_performed"] is False
    assert not (repository / "var").exists()


def test_source_content_drift_is_rejected_in_clean_checkout(tmp_path: Path):
    definition = load_definition()
    repository = _copy_definition_sources_without_var(tmp_path / "checkout", definition)
    renderer = repository / definition["source_files"]["deployment_renderer"]
    renderer.write_bytes(renderer.read_bytes() + b"\n")

    with pytest.raises(ExecutionRequestValidationError, match="source content drift: deployment_renderer"):
        validate_execution_request(definition, repository_root=repository)


def test_mechanics_source_content_drift_is_rejected_in_clean_checkout(tmp_path: Path):
    definition = load_definition()
    repository = _copy_definition_sources_without_var(tmp_path / "checkout", definition)
    mechanics = repository / definition["source_files"]["diagnostic_mechanics"]
    mechanics.write_bytes(mechanics.read_bytes() + b"\n")

    with pytest.raises(ExecutionRequestValidationError, match="source content drift: diagnostic_mechanics"):
        validate_execution_request(definition, repository_root=repository)


def test_authority_mode_rejects_independent_evaluator_interpretation():
    definition = deepcopy(load_definition())
    definition["authority_contract"]["external_authority_semantics"] = "independent evaluator required"

    with pytest.raises(ExecutionRequestValidationError, match="authority mode or policy semantics drift"):
        validate_execution_request(definition)


def test_authority_mode_is_explicitly_self_custodied_and_not_evaluator_authority():
    definition = load_definition()
    contract = definition["authority_contract"]
    assert contract["authority_mode"] == "self_custodied_diagnostic"
    assert contract["independent_evaluator_required"] is False
    assert contract["external_authority_required"] is True
    assert "not an independent evaluator requirement" in contract["external_authority_semantics"]
