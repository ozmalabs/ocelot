from copy import deepcopy

import pytest

from services.p5_r0_evaluator.deploy.definition import (
    DEFAULT_DEFINITION,
    DefinitionBlockedError,
    DefinitionValidationError,
    load_definition,
    validate_definition,
)


def test_checked_in_definition_is_explicit_but_blocked_until_reviewed_inputs_exist():
    definition = load_definition(DEFAULT_DEFINITION)
    report = validate_definition(definition)

    assert report.ready is False
    assert "controlled_run_bindings.image_digest" in report.missing_inputs
    assert definition["native_closure"]["runtime"]["name"] == "crun"
    assert definition["native_closure"]["execution"]["network"] == "none"
    assert definition["native_closure"]["execution"]["pull"] == "never"
    assert definition["native_closure"]["resource_profile"] == {
        "steps": 8,
        "frame_bytes": 65536,
        "wall_seconds": 3,
        "memory_mb": 512,
        "cpu": 1,
        "pids": 32,
        "digest": "from:controlled_run_bindings.resource_profile_digest",
    }
    assert definition["apply_plan"]["commands"] == []



def test_reviewed_repository_drift_is_rejected():
    definition = deepcopy(load_definition())
    definition["controlled_run_bindings"]["artifact_registry_repository"] = "p5"
    with pytest.raises(DefinitionValidationError, match="reviewed existing target"):
        validate_definition(definition)


def test_complete_validation_is_blocked_without_controlled_run_bindings():
    with pytest.raises(DefinitionBlockedError, match="reviewed run/environment bindings"):
        validate_definition(load_definition(), require_complete=True)


def test_placeholders_are_rejected_even_when_the_definition_shape_is_valid():
    definition = deepcopy(load_definition())
    definition["controlled_run_bindings"]["image_digest"] = "sha256:REPLACE_EXACT_64_HEX_DIGEST"

    with pytest.raises(DefinitionValidationError, match="unresolved placeholder"):
        validate_definition(definition)


def test_invalid_supplied_digest_is_rejected():
    definition = deepcopy(load_definition())
    definition["controlled_run_bindings"]["runtime_digest"] = "sha256:not-a-digest"

    with pytest.raises(DefinitionValidationError, match="invalid controlled-run binding digest"):
        validate_definition(definition)


    definition = deepcopy(load_definition())
    definition["native_closure"]["argv"]["flags"][4] = "--network=host"

    with pytest.raises(DefinitionValidationError, match="native argv flags drift"):
        validate_definition(definition)


def test_host_closure_path_drift_is_rejected():
    definition = deepcopy(load_definition())
    definition["native_closure"]["host_closure"]["host_kill"] = "evaluation/p5_r0/runner.py"

    with pytest.raises(DefinitionValidationError, match="host closure path drift"):
        validate_definition(definition)


def test_apply_plan_has_no_executable_cloud_command():
    definition = load_definition()
    assert definition["apply_plan"]["commands"] == []
    assert not any("gcloud" in command.lower() for command in definition["apply_plan"]["commands"])
    assert "gcloud mutation" in definition["apply_plan"]["forbidden_operations"]
