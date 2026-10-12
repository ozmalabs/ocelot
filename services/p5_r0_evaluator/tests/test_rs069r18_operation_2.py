from __future__ import annotations

import copy
import json
from pathlib import Path
import inspect
from types import SimpleNamespace

import pytest

import services.p5_r0_evaluator.deploy.rs069r18_operation_2 as operation_2

from evaluation.p0a.canonical import canonical_bytes, sha256
from services.p5_r0_evaluator.deploy.authority_binding_proposal import REVIEW_PROVIDER
from services.p5_r0_evaluator.deploy.rs069r17_operation_2_approval import DEFAULT_REQUEST, load_request
from services.p5_r0_evaluator.deploy.rs069r18_operation_2 import (
    LATER_OPERATION_IDS,
    OPERATION_ID,
    RS069Operation2Blocked,
    _EXPECTED_CLAIM_PATHS,
    _condition_expression,
    _desired_state,
    _ledger_event,
    _ledger_records,
    _run_json,
    _run_status,
    _state_from_gcloud,
    _update_command,
    canonical_provider_resource_name,
    execute_operation_2,
    _describe_command,
    build_rollback_command,
    provider_resource_digest,
    validate_operation_2_bindings,
    validate_poststate,
    validate_prestate,
)

ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_DIGEST = "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c"


def _desired():
    return _desired_state(load_request(DEFAULT_REQUEST), CANDIDATE_DIGEST)


def _state(desired, *, fingerprint="etag-before", name=REVIEW_PROVIDER):
    raw = {
        "name": name,
        "attributeMapping": desired["mapping"],
        "attributeCondition": desired["condition_expression"],
    }
    if fingerprint is not None:
        raw["etag"] = fingerprint
    return _state_from_gcloud(raw, REVIEW_PROVIDER)


def _approval_artifact(request, desired, prestate, *, custody="self_custodied", attempt_id="rs069r18r10-op2-20260919-a1b2c3d4"):
    bindings = {
        "operation_id": OPERATION_ID,
        "operation_order": 2,
        "scope": [OPERATION_ID],
        "request_scope_digest": request["request_scope_digest"],
        "plan_digest": request["typed_plan_binding"]["plan_digest"],
        "candidate_image_digest": CANDIDATE_DIGEST,
        "provider_resource_digest": provider_resource_digest(REVIEW_PROVIDER),
        "mapping_digest": desired["mapping_digest"],
        "condition_digest": desired["condition_digest"],
        "mapping_condition_digest": desired["mapping_condition_digest"],
        "expected_prestate_digest": prestate["state_digest"],
        "attempt_id": attempt_id,
    }
    artifact = {
        "schema": "P5R0RS069R18R10ApprovalArtifactV2",
        "acceptance_contract": "P5R0RS069R18R10Operation2AcceptanceV2",
        "approval_id": "P5-MASTER-001/APPROVAL-007-RS069R18R10",
        "custody": custody,
        "status": "approved_single_operation_pending_apply",
        "request_scope_digest": request["request_scope_digest"],
        "bindings": bindings,
        "attestation": {
            "status": "deferred",
            "deferred_to": "RS-080",
            "asserted": False,
        },
    }
    artifact["artifact_digest"] = sha256(artifact)
    return artifact


def test_r18r10_contract_is_distinct_from_immutable_history():
    assert operation_2._APPROVAL_SCHEMA == "P5R0RS069R18R10ApprovalArtifactV2"
    assert operation_2._ACCEPTANCE_CONTRACT == "P5R0RS069R18R10Operation2AcceptanceV2"
    assert operation_2._APPROVAL_ID == "P5-MASTER-001/APPROVAL-007-RS069R18R10"
    assert operation_2.DEFAULT_LEDGER == ROOT / "var/p5-r0-rs069/operation-2-r18r10-ledger.jsonl"
    assert operation_2.DEFAULT_LEDGER not in operation_2._HISTORICAL_LEDGER_PATHS
    assert operation_2._HISTORICAL_LEDGER_PATHS == (
        ROOT / "var/p5-r0-rs069/operation-2-ledger.jsonl",
        ROOT / "var/p5-r0-rs069/operation-2-r18r8-ledger.jsonl",
        ROOT / "var/p5-r0-rs069/operation-2-r18r9-ledger.jsonl",
    )


def test_status_only_update_accepts_empty_or_non_json_success(monkeypatch):
    results = iter([
        SimpleNamespace(returncode=0, stdout="", stderr="provider updated"),
        SimpleNamespace(returncode=0, stdout="not-json", stderr=""),
    ])
    monkeypatch.setattr(operation_2.subprocess, "run", lambda *args, **kwargs: next(results))

    _run_status(["provider-update"], ROOT)
    _run_status(["provider-update"], ROOT)


def test_status_only_update_fails_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr(
        operation_2.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=7, stdout="success-looking-output", stderr="failed"),
    )

    with pytest.raises(RS069Operation2Blocked, match="update command failed with exit 7"):
        _run_status(["provider-update"], ROOT)


def test_r18r7_reconciliation_artifact_is_canonical_and_binds_r18r5():
    path = ROOT / "var/p5-r0-rs069/operation-2-r18r7-read-only-reconciliation.json"
    artifact = operation_2._load_canonical_artifact(path, "R18R7 reconciliation")

    assert artifact["artifact_digest"] == sha256({key: value for key, value in artifact.items() if key != "artifact_digest"})
    assert artifact["bindings"]["r18r5_prestate_state_digest"] == "sha256:66782fd27ef8155a6f373188d25e3bf7d3197dcb2860c5bacd2a3fc904f19f0b"
    assert artifact["bindings"]["r18r5_event_digests"][-1] == artifact["bindings"]["r18r5_ledger_head_digest"]
    assert artifact["evidence"]["current_provider_equals_prestate"] is True
    assert artifact["claim_flags"] == {
        "desired_poststate_not_observed": True,
        "downstream_disabled": True,
        "mutation_not_proven": True,
        "no_retry": True,
        "rollback_not_verified": True,
    }
    assert artifact["ledger_rewritten"] is False


def test_provider_names_normalize_to_one_canonical_form():
    desired = _desired()
    short_name = REVIEW_PROVIDER.removeprefix("//iam.googleapis.com/")

    assert canonical_provider_resource_name(short_name) == REVIEW_PROVIDER
    assert provider_resource_digest(short_name) == provider_resource_digest(REVIEW_PROVIDER)
    state = _state(desired, fingerprint=None, name=short_name)
    assert state["provider_resource"] == REVIEW_PROVIDER
    assert state["etag_unavailable"] is True
    assert state["fingerprint"] is None


def test_missing_etag_uses_exact_observed_state_digest_precondition_without_inventing_one():
    desired = _desired()
    observed = _state(desired, fingerprint=None)

    validate_prestate(observed, copy.deepcopy(observed))
    assert observed["etag_unavailable"] is True
    assert observed["fingerprint"] is None
    assert observed["state_digest"] == observed["configuration_digest"]
    command = _update_command(REVIEW_PROVIDER, desired["mapping"], desired["condition"], None, True)
    assert not any(argument.startswith("--etag=") for argument in command)
    assert "--format=json" not in command


def test_missing_etag_mapping_or_condition_drift_fails_closed():
    desired = _desired()
    expected = _state(desired, fingerprint=None)
    drifted_mapping = copy.deepcopy(desired["mapping"])
    drifted_mapping["attribute.project_id"] = "assertion.other_project"
    observed = _state_from_gcloud(
        {"name": REVIEW_PROVIDER, "attributeMapping": drifted_mapping, "attributeCondition": desired["condition_expression"]},
        REVIEW_PROVIDER,
    )

    with pytest.raises(RS069Operation2Blocked, match="prestate observed state or configuration drift"):
        validate_prestate(observed, expected)

    observed = _state_from_gcloud(
        {"name": REVIEW_PROVIDER, "attributeMapping": desired["mapping"], "attributeCondition": desired["condition_expression"] + " && assertion.extra == 'drift'"},
        REVIEW_PROVIDER,
    )
    with pytest.raises(RS069Operation2Blocked, match="prestate observed state or configuration drift"):
        validate_prestate(observed, expected)


def test_prestate_fingerprint_and_digest_drift_fail_closed():
    desired = _desired()
    state = _state(desired)
    expected = copy.deepcopy(state)
    expected["fingerprint"] = "different-etag"

    with pytest.raises(RS069Operation2Blocked, match="prestate observed state or configuration drift"):
        validate_prestate(state, expected)

    expected = copy.deepcopy(state)
    expected["state_digest"] = "sha256:" + "0" * 64
    with pytest.raises(RS069Operation2Blocked, match="provider state digest drift|provider configuration digest drift"):
        validate_prestate(state, expected)

    expected = copy.deepcopy(state)
    expected["fingerprint"] = "etag-UNRESOLVED"
    with pytest.raises(RS069Operation2Blocked, match="provider state"):
        validate_prestate(state, expected)


def test_mapping_drift_is_rejected_without_remote_call():
    desired = _desired()
    state = _state(desired)
    drifted = copy.deepcopy(desired)
    drifted["mapping"]["attribute.debug_state"] = "assertion.untrusted_debug_state"

    with pytest.raises(RS069Operation2Blocked, match="poststate mapping drift|desired mapping"):
        validate_poststate(state, drifted, REVIEW_PROVIDER)


def test_wrong_provider_project_pool_or_audience_fails_closed():
    wrong_provider = REVIEW_PROVIDER.replace("p5-cs-production", "other-provider")
    with pytest.raises(RS069Operation2Blocked, match="provider/project/pool binding drift"):
        provider_resource_digest(wrong_provider)
    with pytest.raises(RS069Operation2Blocked, match="confused with token audience"):
        provider_resource_digest("https://sts.googleapis.com")
    with pytest.raises(RS069Operation2Blocked, match="provider resource is unresolved"):
        provider_resource_digest(None)  # type: ignore[arg-type]


def test_poststate_condition_digest_and_provider_mismatch_fail_closed():
    desired = _desired()
    state = _state(desired)
    wrong_condition = copy.deepcopy(desired)
    wrong_condition["condition_expression"] = desired["condition_expression"] + " && assertion.extra == 'wrong'"
    wrong_condition["condition_expression_digest"] = sha256(canonical_bytes(wrong_condition["condition_expression"]))

    with pytest.raises(RS069Operation2Blocked, match="poststate condition drift"):
        validate_poststate(state, wrong_condition, REVIEW_PROVIDER)
    with pytest.raises(RS069Operation2Blocked, match="poststate provider drift"):
        validate_poststate(state, desired, REVIEW_PROVIDER.replace("p5-cs-production", "other-provider"))


def test_rollback_uses_typed_oidc_update_runner_without_etag():
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    command = build_rollback_command(REVIEW_PROVIDER, prestate, None, True)

    assert command[0] == "/home/matt/google-cloud-sdk/bin/gcloud"
    assert command[1:5] == ["iam", "workload-identity-pools", "providers", "update-oidc"]
    assert not any(argument.startswith("--etag=") for argument in command)
    assert "--attribute-mapping=" + ",".join(f"{key}={desired['mapping'][key]}" for key in sorted(desired["mapping"])) in command
    assert "--attribute-condition=" + desired["condition_expression"] in command
    assert "--shell" not in command


def test_etag_bearing_oidc_update_fails_closed_until_conditional_api_exists():
    desired = _desired()
    prestate = _state(desired, fingerprint="prestate-etag")

    with pytest.raises(RS069Operation2Blocked, match="etag-bearing state"):
        build_rollback_command(REVIEW_PROVIDER, prestate, "poststate-etag", False)

def test_scope_widening_is_rejected_even_with_local_digest_recalculation():
    request = load_request(DEFAULT_REQUEST)
    request["scope"].append(LATER_OPERATION_IDS[0])
    with pytest.raises(RS069Operation2Blocked, match="operation scope widened"):
        _desired_state(request, CANDIDATE_DIGEST)


def test_later_operations_are_closed_and_disabled():
    request = load_request(DEFAULT_REQUEST)
    assert request["scope"] == [OPERATION_ID]
    assert tuple(item["id"] for item in request["later_operations"]) == LATER_OPERATION_IDS
    assert all(item["enabled"] is False for item in request["later_operations"])
    assert request["workflow"]["later_operations_enabled"] is False


def test_self_custodied_master_approval_is_accepted_without_attestation(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired)
    approval = _approval_artifact(request, desired, prestate)
    approval_path = tmp_path / "approval.json"
    approval_path.write_bytes(canonical_bytes(approval))
    bindings = validate_operation_2_bindings(
        request,
        candidate_image_digest=CANDIDATE_DIGEST,
        provider_resource=REVIEW_PROVIDER,
        attested_claim_record=None,
        approval=None,
        review_state=None,
        claim_artifact_path=None,
        approval_artifact_path=approval_path,
        expected_prestate_digest=prestate["state_digest"],
    )
    assert bindings["approval"]["request_scope_digest"] == request["request_scope_digest"]
    assert bindings["approval"]["plan_digest"] == request["typed_plan_binding"]["plan_digest"]
    assert bindings["approval"]["candidate_image_digest"] == CANDIDATE_DIGEST
    assert bindings["approval"]["provider_resource_digest"] == provider_resource_digest(REVIEW_PROVIDER)
    assert bindings["approval"]["mapping_digest"] == desired["mapping_digest"]
    assert bindings["approval"]["condition_digest"] == desired["condition_digest"]
    assert bindings["attestation"] == {"status": "deferred", "deferred_to": "RS-080", "asserted": False}
    assert bindings["approval_artifact_digest"].startswith("sha256:")


def test_attestation_is_deferred_and_cannot_be_asserted_by_operation_2(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired)
    approval_path = tmp_path / "approval.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, prestate)))
    with pytest.raises(RS069Operation2Blocked, match="attestation is deferred to RS-080"):
        validate_operation_2_bindings(
            request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None,
            approval=None,
            claim_artifact_path=tmp_path / "claim.json",
            approval_artifact_path=approval_path,
            expected_prestate_digest=prestate["state_digest"],
        )


def test_approval_binds_exact_prestate_used_for_rollback(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired)
    approval = _approval_artifact(request, desired, prestate)
    approval["bindings"]["expected_prestate_digest"] = "sha256:" + "0" * 64
    approval["artifact_digest"] = sha256({key: value for key, value in approval.items() if key != "artifact_digest"})
    approval_path = tmp_path / "wrong-prestate.json"
    approval_path.write_bytes(canonical_bytes(approval))

    with pytest.raises(RS069Operation2Blocked, match="approval artifact binding drift"):
        validate_operation_2_bindings(
            request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None,
            approval=None,
            approval_artifact_path=approval_path,
            expected_prestate_digest=prestate["state_digest"],
        )


def test_wrong_approval_or_mapping_digest_fails_closed(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired)
    approval = _approval_artifact(request, desired, prestate)
    approval["bindings"]["candidate_image_digest"] = "sha256:" + "f" * 64
    approval["artifact_digest"] = sha256({key: value for key, value in approval.items() if key != "artifact_digest"})
    approval_path = tmp_path / "wrong-approval.json"
    approval_path.write_bytes(canonical_bytes(approval))
    with pytest.raises(RS069Operation2Blocked, match="approval artifact binding drift"):
        validate_operation_2_bindings(
            request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None, approval=None, approval_artifact_path=approval_path,
            expected_prestate_digest=prestate["state_digest"],
        )

    approval = _approval_artifact(request, desired, prestate)
    approval["bindings"]["mapping_digest"] = "sha256:" + "f" * 64
    approval["artifact_digest"] = sha256({key: value for key, value in approval.items() if key != "artifact_digest"})
    approval_path.write_bytes(canonical_bytes(approval))
    with pytest.raises(RS069Operation2Blocked, match="approval artifact binding drift"):
        validate_operation_2_bindings(
            request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None, approval=None, approval_artifact_path=approval_path,
            expected_prestate_digest=prestate["state_digest"],
        )


def test_unresolved_provider_input_still_fails_before_handler_boundary():
    request = load_request(DEFAULT_REQUEST)
    with pytest.raises(RS069Operation2Blocked, match="provider resource is unresolved"):
        validate_operation_2_bindings(
            request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=None,
            attested_claim_record=None,
            approval=None,
            review_state="master_reviewed",
        )


def test_caller_approval_and_claim_values_are_not_authentication_artifacts():
    request = load_request(DEFAULT_REQUEST)
    with pytest.raises(RS069Operation2Blocked, match="caller-supplied claim record"):
        validate_operation_2_bindings(
            request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
            attested_claim_record={"source": "verified"}, approval={"approved": True}, review_state=None,
            claim_artifact_path=None, approval_artifact_path=None, expected_prestate_digest="sha256:" + "a" * 64,
        )


def test_unresolved_markers_are_rejected_in_mapping_and_condition():
    desired = _desired()
    with pytest.raises(RS069Operation2Blocked, match="desired.mapping"):
        broken = copy.deepcopy(load_request(DEFAULT_REQUEST))
        broken["desired_state"]["mapping"]["attribute.zone"] = "assertion.UNRESOLVED"
        _desired_state(broken, CANDIDATE_DIGEST)
    with pytest.raises(RS069Operation2Blocked, match="provider mapping"):
        _state_from_gcloud({
            "name": REVIEW_PROVIDER, "attributeMapping": {"google.subject": "REQUIRED_INPUT:subject"},
            "attributeCondition": desired["condition_expression"], "etag": "etag-before",
        }, REVIEW_PROVIDER)
    with pytest.raises(RS069Operation2Blocked, match="provider condition"):
        _state_from_gcloud({
            "name": REVIEW_PROVIDER, "attributeMapping": desired["mapping"],
            "attributeCondition": "UNRESOLVED", "etag": "etag-before",
        }, REVIEW_PROVIDER)
    with pytest.raises(RS069Operation2Blocked, match="desired.condition"):
        broken = copy.deepcopy(load_request(DEFAULT_REQUEST))
        broken["desired_state"]["condition"]["zone"] = "assertion.submods.gce.zone == 'REPLACE_ZONE'"
        _desired_state(broken, CANDIDATE_DIGEST)


def test_etag_bearing_rollback_fails_closed_until_conditional_api_exists():
    desired = _desired()
    prestate = _state(desired, fingerprint="prestate-etag")
    restored = _state(desired, fingerprint="new-etag-after-rollback")

    assert restored["configuration_digest"] == prestate["configuration_digest"]
    with pytest.raises(RS069Operation2Blocked, match="etag-bearing state"):
        build_rollback_command(REVIEW_PROVIDER, prestate, restored["fingerprint"], restored["etag_unavailable"])


def test_ledger_records_are_hash_chained_and_redacted(tmp_path):
    path = tmp_path / "operation-2-ledger.jsonl"
    first = _ledger_event(path, {"schema": "test", "kind": "prestate_captured", "redacted": True, "prestate_digest": "sha256:" + "1" * 64}, None)
    second = _ledger_event(path, {"schema": "test", "kind": "run_stopped", "redacted": True, "error": {"code": "mismatch"}}, first["event_digest"])
    records = _ledger_records(path)

    assert [record["event_digest"] for record in records] == [first["event_digest"], second["event_digest"]]
    assert records[1]["previous_event_digest"] == records[0]["event_digest"]
    assert "secret-token" not in path.read_text()


def test_poststate_mismatch_rolls_back_exact_no_etag_prestate(tmp_path, monkeypatch):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, prestate)))
    prestate_path.write_bytes(canonical_bytes(prestate))
    monkeypatch.setattr(operation_2, "validate_request", lambda request: request["request_scope_digest"])
    post_mapping = copy.deepcopy(desired["mapping"])
    post_mapping["attribute.project_id"] = "assertion.drifted_project"
    responses = iter([
        {"name": REVIEW_PROVIDER.removeprefix("//iam.googleapis.com/"), "attributeMapping": prestate["mapping"], "attributeCondition": prestate["condition"]},
        {"name": REVIEW_PROVIDER, "attributeMapping": post_mapping, "attributeCondition": desired["condition_expression"]},
        {"name": REVIEW_PROVIDER, "attributeMapping": prestate["mapping"], "attributeCondition": prestate["condition"]},
    ])
    describe_commands = []
    update_commands = []
    monkeypatch.setattr(operation_2, "_run_json", lambda command, root: (describe_commands.append(command) or next(responses)))
    monkeypatch.setattr(operation_2, "_run_status", lambda command, root: update_commands.append(command))

    result = execute_operation_2(
        request=request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
        attested_claim_record=None, approval=None, expected_prestate=None, repository_root=ROOT,
        ledger_path=tmp_path / "ledger.jsonl", apply_enabled=True, claim_artifact_path=None,
        approval_artifact_path=approval_path, expected_prestate_path=prestate_path,
    )

    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    assert result["mutations_performed"] is True
    records = _ledger_records(tmp_path / "ledger.jsonl")
    assert {record["attempt_id"] for record in records} == {"rs069r18r10-op2-20260919-a1b2c3d4"}
    terminal = records[-1]
    assert terminal["phase_attempts"]["desired_update"][0]["classification"] == "desired_update_succeeded"
    assert terminal["phase_attempts"]["desired_update"][0]["prestate_digest"] == prestate["state_digest"]
    assert terminal["phase_attempts"]["desired_update"][0]["etag_unavailable"] is True
    assert terminal["phase_attempts"]["current_state_describe"][0]["classification"] == "current_state_describe_succeeded"
    drifted_state = _state_from_gcloud(
        {"name": REVIEW_PROVIDER, "attributeMapping": post_mapping, "attributeCondition": desired["condition_expression"]},
        REVIEW_PROVIDER,
    )
    assert terminal["phase_attempts"]["current_state_describe"][0]["state_digest"] == drifted_state["state_digest"]
    assert terminal["phase_attempts"]["rollback_update"][0]["classification"] == "rollback_update_succeeded"
    assert terminal["phase_attempts"]["rollback_update"][0]["current_state_digest"] == drifted_state["state_digest"]
    assert terminal["phase_attempts"]["rollback_update"][0]["rollback_target_configuration_digest"] == prestate["configuration_digest"]
    assert terminal["phase_attempts"]["restored_state_describe"][0]["classification"] == "restored_state_describe_succeeded"
    assert terminal["phase_attempts"]["restored_state_describe"][0]["configuration_digest"] == prestate["configuration_digest"]
    update_commands = [command for command in update_commands if "update-oidc" in command]
    assert len(update_commands) == 2
    assert all(not any(argument.startswith("--etag=") for argument in command) for command in update_commands)




def test_nonzero_update_is_failed_closed_without_retry(tmp_path, monkeypatch):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = operation_2._load_canonical_artifact(
        ROOT / "services/p5_r0_evaluator/deploy/rs-069r18-operation-2-expected-provider-prestate.json",
        "expected prestate",
        allow_unavailable_etag=True,
    )
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, prestate)))
    prestate_path.write_bytes(canonical_bytes(prestate))
    monkeypatch.setattr(operation_2, "validate_request", lambda request: request["request_scope_digest"])
    responses = iter([
        {"name": REVIEW_PROVIDER, "attributeMapping": prestate["mapping"], "attributeCondition": prestate["condition"]},
        {"name": REVIEW_PROVIDER, "attributeMapping": prestate["mapping"], "attributeCondition": prestate["condition"]},
        {"name": REVIEW_PROVIDER, "attributeMapping": prestate["mapping"], "attributeCondition": prestate["condition"]},
    ])
    update_commands = []
    monkeypatch.setattr(operation_2, "_run_json", lambda command, root: next(responses))

    def fail_once(command, root):
        update_commands.append(command)
        if len(update_commands) == 1:
            raise RS069Operation2Blocked("operation-2 update command failed with exit 9")

    monkeypatch.setattr(operation_2, "_run_status", fail_once)
    result = execute_operation_2(
        request=request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
        attested_claim_record=None, approval=None, expected_prestate=None, repository_root=ROOT,
        ledger_path=tmp_path / "ledger.jsonl", apply_enabled=True, claim_artifact_path=None,
        approval_artifact_path=approval_path, expected_prestate_path=prestate_path,
    )

    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    assert len(update_commands) == 2
    assert update_commands.count(_update_command(REVIEW_PROVIDER, desired["mapping"], desired["condition"], None, True)) == 1
    assert result["rollback_error_classification"] is None


def test_rollback_failure_records_redacted_substep_and_classification(tmp_path, monkeypatch):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, prestate)))
    prestate_path.write_bytes(canonical_bytes(prestate))
    monkeypatch.setattr(operation_2, "validate_request", lambda request: request["request_scope_digest"])
    drifted_mapping = copy.deepcopy(desired["mapping"])
    drifted_mapping["attribute.project_id"] = "assertion.drifted_project"
    responses = iter([
        {"name": REVIEW_PROVIDER, "attributeMapping": prestate["mapping"], "attributeCondition": prestate["condition"]},
        {"name": REVIEW_PROVIDER, "attributeMapping": drifted_mapping, "attributeCondition": desired["condition_expression"]},
    ])
    update_commands = []
    monkeypatch.setattr(operation_2, "_run_json", lambda command, root: next(responses))

    def fail_rollback(command, root):
        update_commands.append(command)
        if len(update_commands) == 2:
            raise RS069Operation2Blocked("rollback command failed with exit 11")

    monkeypatch.setattr(operation_2, "_run_status", fail_rollback)
    result = execute_operation_2(
        request=request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
        attested_claim_record=None, approval=None, expected_prestate=None, repository_root=ROOT,
        ledger_path=tmp_path / "ledger.jsonl", apply_enabled=True, claim_artifact_path=None,
        approval_artifact_path=approval_path, expected_prestate_path=prestate_path,
    )

    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rollback_failed_manual_review"
    assert result["rollback_substep"] == "rollback_update"
    assert result["rollback_error_classification"] == "rollback_update_blocked"
    terminal = _ledger_records(tmp_path / "ledger.jsonl")[-1]
    assert terminal["rollback_substep"] == "rollback_update"
    assert terminal["rollback_error"] == {"classification": "rollback_update_blocked", "redacted": True}
    assert "exit 11" not in json.dumps(terminal)


def test_fresh_prestate_drift_stops_before_update(tmp_path, monkeypatch):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    expected = _state(desired, fingerprint=None)
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, expected)))
    prestate_path.write_bytes(canonical_bytes(expected))
    monkeypatch.setattr(operation_2, "validate_request", lambda request: request["request_scope_digest"])
    drifted = copy.deepcopy(desired["mapping"])
    drifted["attribute.zone"] = "assertion.other_zone"
    responses = iter([{"name": REVIEW_PROVIDER, "attributeMapping": drifted, "attributeCondition": expected["condition"]}])
    commands = []
    monkeypatch.setattr(operation_2, "_run_json", lambda command, root: (commands.append(command) or next(responses)))

    result = execute_operation_2(
        request=request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
        attested_claim_record=None, approval=None, expected_prestate=None, repository_root=ROOT,
        ledger_path=tmp_path / "ledger.jsonl", apply_enabled=True, claim_artifact_path=None,
        approval_artifact_path=approval_path, expected_prestate_path=prestate_path,
    )

    assert result["status"] == "failed_closed"
    assert result["mutations_performed"] is False
    assert not any("update" in command for command in commands)


    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired)
    approval = _approval_artifact(request, desired, prestate)
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(approval))
    prestate_path.write_bytes(canonical_bytes(prestate))
    monkeypatch.setattr(operation_2, "validate_request", lambda request: request["request_scope_digest"])
    remote_pre = {
        "name": REVIEW_PROVIDER, "attributeMapping": desired["mapping"],
        "attributeCondition": desired["condition_expression"], "etag": "etag-before",
    }
    remote_post = {
        "name": REVIEW_PROVIDER, "attributeMapping": desired["mapping"],
        "attributeCondition": desired["condition_expression"], "etag": "etag-after",
    }
    responses = iter([remote_pre, {}, remote_post])
    monkeypatch.setattr(operation_2, "_run_json", lambda command, root: next(responses))
    real_ledger_event = operation_2._ledger_event
    def fail_terminal(path, record, previous):
        if record.get("kind") == "run_stopped":
            raise OSError("ledger unavailable")
        return real_ledger_event(path, record, previous)
    monkeypatch.setattr(operation_2, "_ledger_event", fail_terminal)
    result = execute_operation_2(
        request=request, candidate_image_digest=CANDIDATE_DIGEST, provider_resource=REVIEW_PROVIDER,
        attested_claim_record=None, approval=None, expected_prestate=None, repository_root=ROOT,
        ledger_path=tmp_path / "ledger-write-failure.jsonl", apply_enabled=True,
        claim_artifact_path=None, approval_artifact_path=approval_path,
        expected_prestate_path=prestate_path,
    )
    assert result["status"] == "terminal_ledger_write_failed"
    assert result["rollback_status"] == "manual_review_ledger_failure"
    assert result["recovery_marker_written"] is True
    assert result["mutations_performed"] is True
    assert "verified" not in result["status"]


    source = inspect.getsource(_run_json)
    assert "stdin=subprocess.DEVNULL" in source
    assert "shell=True" not in source


    command = _describe_command(REVIEW_PROVIDER)
    assert command[0] == "/home/matt/google-cloud-sdk/bin/gcloud"
    assert command[-1] == "--format=json"
    assert "update" not in command
    assert "--format=json" in command



def test_r18r8_approval_identity_cannot_cross_acceptance_contract(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    approval = _approval_artifact(request, desired, prestate)
    approval["approval_id"] = "P5-MASTER-001/APPROVAL-005-RS069R18R8"
    approval["artifact_digest"] = sha256({key: value for key, value in approval.items() if key != "artifact_digest"})
    approval_path = tmp_path / "r18r8-approval.json"
    approval_path.write_bytes(canonical_bytes(approval))

    with pytest.raises(RS069Operation2Blocked, match="approval artifact identity drift"):
        validate_operation_2_bindings(
            request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None,
            approval=None,
            approval_artifact_path=approval_path,
            expected_prestate_digest=prestate["state_digest"],
        )


def test_r18r10_attempt_identity_is_unique_across_historical_ledgers(tmp_path, monkeypatch):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    attempt_id = "rs069r18r10-op2-20260919-a1b2c3d4"
    historical = tmp_path / "historical-ledger.jsonl"
    _ledger_event(historical, {"schema": "historical", "kind": "run_started", "attempt_id": attempt_id}, None)
    monkeypatch.setattr(operation_2, "_HISTORICAL_LEDGER_PATHS", (historical,))
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, prestate, attempt_id=attempt_id)))
    prestate_path.write_bytes(canonical_bytes(prestate))

    with pytest.raises(RS069Operation2Blocked, match="approval attempt identity was already used"):
        execute_operation_2(
            request=request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None,
            approval=None,
            expected_prestate=None,
            repository_root=ROOT,
            ledger_path=tmp_path / "r18r10-ledger.jsonl",
            apply_enabled=True,
            approval_artifact_path=approval_path,
            expected_prestate_path=prestate_path,
        )


def test_historical_r18r9_attempt_identity_is_rejected_by_r18r10_contract(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    approval_path = tmp_path / "r18r9-approval.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(
        request, desired, prestate, attempt_id="rs069r18r9-op2-20260919-a1b2c3d4"
    )))

    with pytest.raises(RS069Operation2Blocked, match="approval attempt identity is invalid"):
        validate_operation_2_bindings(
            request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None,
            approval=None,
            approval_artifact_path=approval_path,
            expected_prestate_digest=prestate["state_digest"],
        )


def test_historical_r18r9_ledger_is_never_used_as_r18r10_target(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, prestate)))
    prestate_path.write_bytes(canonical_bytes(prestate))

    with pytest.raises(RS069Operation2Blocked, match="historical operation-2 ledger is immutable"):
        execute_operation_2(
            request=request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None,
            approval=None,
            expected_prestate=None,
            repository_root=ROOT,
            ledger_path=operation_2._HISTORICAL_LEDGER_PATHS[2],
            apply_enabled=True,
            approval_artifact_path=approval_path,
            expected_prestate_path=prestate_path,
        )


def test_in_repository_alternate_r18r10_ledger_path_is_rejected(tmp_path):
    request = load_request(DEFAULT_REQUEST)
    desired = _desired()
    prestate = _state(desired, fingerprint=None)
    approval_path = tmp_path / "approval.json"
    prestate_path = tmp_path / "prestate.json"
    approval_path.write_bytes(canonical_bytes(_approval_artifact(request, desired, prestate)))
    prestate_path.write_bytes(canonical_bytes(prestate))
    alternate = ROOT / "var/p5-r0-rs069/operation-2-r18r10-alternate.jsonl"

    with pytest.raises(RS069Operation2Blocked, match="R18R10 ledger path is not canonical"):
        execute_operation_2(
            request=request,
            candidate_image_digest=CANDIDATE_DIGEST,
            provider_resource=REVIEW_PROVIDER,
            attested_claim_record=None,
            approval=None,
            expected_prestate=None,
            repository_root=ROOT,
            ledger_path=alternate,
            apply_enabled=True,
            approval_artifact_path=approval_path,
            expected_prestate_path=prestate_path,
        )
