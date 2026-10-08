from copy import deepcopy
from pathlib import Path

import pytest

from evaluation.p0a.canonical import parse_canonical
from services.p5_r0_evaluator.deploy.bundle_definition import (
    DEFAULT_DEFINITION,
    BundleDefinitionBlockedError,
    BundleDefinitionValidationError,
    _cli,
    load_definition,
    validate_bundle_definition,
)


def test_checked_in_bundle_is_explicit_and_blocked():
    definition = load_definition(DEFAULT_DEFINITION)
    report = validate_bundle_definition(definition)

    assert report.ready is False
    assert report.definition_digest.startswith("sha256:")
    assert "input_locations.manifest" in report.missing_inputs
    assert "input_locations.private_store" in report.missing_inputs
    assert "input_locations.authority_trust_binding" in report.missing_inputs
    assert "expected_commitments.task_set_digest" in report.missing_inputs
    assert all(value is None for value in definition["input_locations"].values())
    assert all(value is None for value in definition["expected_commitments"].values())
    assert definition["blocked_inputs"] == {
        "authorized_tasks": None,
        "candidate_digests": None,
        "private_truth": None,
        "signature_material": None,
        "p5_results": None,
    }


def test_strict_validation_is_blocked_without_reviewed_inputs():
    with pytest.raises(BundleDefinitionBlockedError, match="generated bundle and reviewed environment bindings"):
        validate_bundle_definition(load_definition(), require_complete=True)


def test_definition_digest_is_deterministic():
    first = validate_bundle_definition(load_definition())
    second = validate_bundle_definition(load_definition())
    assert first.definition_digest == second.definition_digest
    assert first.checked_input_digests == second.checked_input_digests == ()


def test_definition_rejects_unknown_fields_and_candidate_inputs():
    definition = deepcopy(load_definition())
    definition["unexpected"] = True
    with pytest.raises(BundleDefinitionValidationError, match="fields are not closed"):
        validate_bundle_definition(definition)

    definition = load_definition()
    definition["blocked_inputs"]["candidate_digests"] = "sha256:" + "0" * 64
    with pytest.raises(BundleDefinitionValidationError, match="blocked controlled-run bindings"):
        validate_bundle_definition(definition)


def test_definition_rejects_absolute_or_missing_input_paths():
    definition = load_definition()
    definition["input_locations"]["manifest"] = "/tmp/manifest.json"
    with pytest.raises(BundleDefinitionValidationError, match="bundle input path is invalid"):
        validate_bundle_definition(definition)

    definition = load_definition()
    definition["input_locations"]["manifest"] = "var/does-not-exist.json"
    definition["expected_commitments"]["manifest_digest"] = "sha256:" + "0" * 64
    with pytest.raises(BundleDefinitionBlockedError):
        validate_bundle_definition(definition, require_complete=True)


def test_prepare_writes_only_a_canonical_blocked_audit(tmp_path: Path, capsys):
    audit = tmp_path / "audit.json"
    assert _cli(["prepare", "--allow-blocked", "--audit-output", str(audit)]) == 0
    payload = parse_canonical(audit.read_bytes())
    assert payload["schema"] == "P5R0BundlePreparationAuditV1"
    assert payload["ready"] is False
    assert payload["production_outputs_created"] is False
    assert payload["cloud_operations"] == []
    assert "No production authority" in payload["claim_boundary"]
    assert "blocked_pending_reviewed_inputs" in capsys.readouterr().out


def test_cli_strict_validation_returns_blocked_exit_code(capsys):
    assert _cli(["validate"]) == 2
    assert "RS-060 validation blocked" in capsys.readouterr().err


def test_apply_plan_and_commands_are_non_mutating():
    definition = load_definition()
    assert definition["apply_plan"]["commands"] == []
    assert not any("gcloud" in command.lower() for command in definition["apply_plan"]["commands"])
    assert all("gcloud" not in command.lower() for command in definition["commands"].values())
    assert definition["assembly"]["writes_controlled_run_inputs"] is False
