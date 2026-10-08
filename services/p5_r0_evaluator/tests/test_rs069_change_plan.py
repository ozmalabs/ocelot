from copy import deepcopy

import pytest

from services.p5_r0_evaluator.deploy.rs069_change_plan import (
    DEFAULT_PLAN,
    RS069ValidationError,
    load_plan,
    validate_plan,
    _approval_scope_digest,
)


def _rebind_test_approval_scope(plan):
    digest = _approval_scope_digest(plan)
    for record in plan["approval_gate_records"]:
        record["plan_digest"] = digest


def test_rs069_plan_is_closed_ordered_blocked_and_self_custodied():
    report = validate_plan(load_plan(DEFAULT_PLAN))

    assert report.ready is False
    assert report.status == "blocked_pending_master_approval"
    assert report.cloud_operations == ()
    assert report.operation_ids == (
        "bind_candidate_image_digest",
        "correct_wip_provider_claim_mapping",
        "bind_self_custodied_authority_and_kms",
        "ingest_generated_bundle_to_gcs",
        "configure_cloud_run_and_confidential_space",
        "prepare_supervisor_and_run_request",
        "cleanup_or_rollback",
    )
    plan = load_plan(DEFAULT_PLAN)
    assert next(item["value"] for item in plan["operations"][0]["exact_required_inputs"] if item["name"] == "target_repository") == "p5-cs"
    assert next(item["value"] for item in plan["operations"][4]["exact_required_inputs"] if item["name"] == "target_repository") == "p5-cs"
    assert plan["authority_contract"]["independent_evaluator_claim"] is False
    assert plan["apply_plan"]["commands"] == []
    assert all(operation["mutation_boundary"]["commands"] == [] for operation in plan["operations"])



def test_nonexistent_repository_is_rejected_by_plan():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    for operation in (plan["operations"][0], plan["operations"][4]):
        for item in operation["exact_required_inputs"]:
            if item["name"] == "target_repository":
                item["value"] = "p5"
    with pytest.raises(RS069ValidationError, match="reviewed repository drift"):
        validate_plan(plan)


def test_order_and_dependency_closure_are_required():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["operations"][2]["order"] = 7

    with pytest.raises(RS069ValidationError, match="operation order drift"):
        validate_plan(plan)


def test_plan_cannot_gain_an_executable_operation_command():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["operations"][0]["mutation_boundary"]["commands"] = ["gcloud something"]

    with pytest.raises(RS069ValidationError, match="operation is executable"):
        validate_plan(plan)


def test_plan_cannot_gain_apply_commands():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["apply_plan"]["commands"] = ["apply"]

    with pytest.raises(RS069ValidationError, match="apply plan contains"):
        validate_plan(plan)


def test_independent_evaluator_claim_is_rejected():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["authority_contract"]["independent_evaluator_claim"] = True

    with pytest.raises(RS069ValidationError, match="authority contract drift"):
        validate_plan(plan)


def test_read_only_inventory_digest_drift_is_rejected():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["read_only_inventory"]["generated_bundle"]["artifact_index_digest"] = "sha256:" + "0" * 64

    with pytest.raises(RS069ValidationError, match="artifact index digest drift"):
        validate_plan(plan)



def test_typed_operation_reorder_is_rejected():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["operation_records"][0], plan["operation_records"][1] = plan["operation_records"][1], plan["operation_records"][0]

    with pytest.raises(RS069ValidationError, match="typed dependency drift|typed operation reorder"):
        validate_plan(plan)


def test_approval_digest_mismatch_is_rejected():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["approval_gate_records"][0]["plan_digest"] = "sha256:" + "0" * 64

    with pytest.raises(RS069ValidationError, match="approval plan digest mismatch"):
        validate_plan(plan)


def test_gcs_object_count_and_digest_drift_are_rejected():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["gcs_object_records"].pop()
    _rebind_test_approval_scope(plan)

    with pytest.raises(RS069ValidationError, match="GCS object record count drift"):
        validate_plan(plan)

    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["gcs_object_records"][0]["file_digest"] = "sha256:" + "0" * 64
    _rebind_test_approval_scope(plan)

    with pytest.raises(RS069ValidationError, match="GCS object digest/visibility drift"):
        validate_plan(plan)


def test_confidential_space_activation_transition_skip_is_rejected():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["confidential_space_activation"]["state"] = "capabilities_activated"
    _rebind_test_approval_scope(plan)

    with pytest.raises(RS069ValidationError, match="activation must remain blocked"):
        validate_plan(plan)


def test_typed_enabled_command_or_mutation_is_rejected():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["operation_records"][0]["enabled"] = True
    plan["operation_records"][0]["commands"] = ["mutate"]

    with pytest.raises(RS069ValidationError, match="typed operation is executable"):
        validate_plan(plan)



def test_approval_scope_covers_legacy_operation_behavior_without_rebinding():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["operations"][0]["desired_state_operation"] += " Changed behavior."

    with pytest.raises(RS069ValidationError, match="approval plan digest mismatch"):
        validate_plan(plan)


def test_approval_scope_covers_review_only_apply_boundary_without_rebinding():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["apply_plan"]["forbidden_operations"].append("new mutation")

    with pytest.raises(RS069ValidationError, match="approval plan digest mismatch"):
        validate_plan(plan)


def test_gcs_object_order_is_artifact_index_order_even_after_scope_rebind():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["gcs_object_records"][0], plan["gcs_object_records"][1] = plan["gcs_object_records"][1], plan["gcs_object_records"][0]
    _rebind_test_approval_scope(plan)

    with pytest.raises(RS069ValidationError, match="GCS object record order drift"):
        validate_plan(plan)


@pytest.mark.parametrize("binding_name", [
    "candidate_image_digest",
    "provider_resource_digest",
    "sts_audience_digest",
    "project_digest",
    "zone_digest",
    "claim_paths_digest",
    "attestation_evidence_digest",
    "capability_grants_digest",
])
def test_confidential_space_activation_digest_bindings_are_explicit_and_equal(binding_name):
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["confidential_space_activation"]["digest_bindings"][binding_name] = "sha256:" + "0" * 64
    _rebind_test_approval_scope(plan)

    with pytest.raises(RS069ValidationError, match="activation (digest|approval) binding mismatch"):
        validate_plan(plan)


def test_confidential_space_candidate_digest_input_cannot_diverge_from_activation():
    plan = deepcopy(load_plan(DEFAULT_PLAN))
    plan["operations"][0]["immutable_digests"][1]["value"] = "sha256:" + "1" * 64
    plan["operation_records"][0]["input_digest_map"]["candidate_image_digest"] = "sha256:" + "1" * 64
    plan["approval_gate_records"][0]["input_digest_map"]["candidate_image_digest"] = "sha256:" + "1" * 64
    _rebind_test_approval_scope(plan)

    with pytest.raises(RS069ValidationError, match="activation digest binding mismatch"):
        validate_plan(plan)
