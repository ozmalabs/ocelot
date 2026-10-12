from __future__ import annotations

import copy
from pathlib import Path

import pytest

from evaluation.p0a.canonical import sha256
from services.p5_r0_evaluator.deploy.rs069r17_operation_2_approval import (
    DEFAULT_REQUEST,
    RS069R17ApprovalError,
    load_request,
    validate_request,
)

ROOT = Path(__file__).resolve().parents[3]


def _with_scope_digest(request: dict) -> dict:
    request["request_scope_digest"] = sha256({key: value for key, value in request.items() if key != "request_scope_digest"})
    return request


def test_operation_2_packet_is_canonical_review_only_and_binds_current_plan():
    request = load_request(DEFAULT_REQUEST)
    digest = validate_request(request, repository_root=ROOT)

    assert digest == "sha256:30809b70128f994de9a27cf5dfc20bfa3ff63a1c904adbd9903c43a097bace1e"
    assert request["scope"] == ["correct_wip_provider_claim_mapping"]
    assert request["typed_plan_binding"]["operation_order"] == 2
    assert request["target"]["repository"] == "p5-cs"
    assert request["desired_state"]["mapping_condition_digest"] == "sha256:2ac146ae1d83a92bc2a373d8970572849db9ebf848dcec6e888410f13e72575a"
    assert request["workflow"]["commands"] == []
    assert request["workflow"]["mutations_performed"] is False
    assert request["workflow"]["wip_mutation_performed"] is False
    assert request["workflow"]["iam_mutation_performed"] is False
    assert request["approval"]["approved"] is False
    assert request["approval"]["enabled"] is False
    assert all(item["enabled"] is False for item in request["later_operations"])


def test_scope_widening_is_rejected_even_if_request_digest_is_recomputed():
    request = copy.deepcopy(load_request(DEFAULT_REQUEST))
    request["scope"].append("bind_self_custodied_authority_and_kms")
    _with_scope_digest(request)

    with pytest.raises(RS069R17ApprovalError, match="operation scope widened"):
        validate_request(request, repository_root=ROOT)


def test_mapping_drift_is_rejected_even_if_request_digest_is_recomputed():
    request = copy.deepcopy(load_request(DEFAULT_REQUEST))
    request["desired_state"]["mapping"]["attribute.debug_state"] = "assertion.untrusted_debug_state"
    _with_scope_digest(request)

    with pytest.raises(RS069R17ApprovalError, match="desired mapping or condition drift|mapping digest drift"):
        validate_request(request, repository_root=ROOT)


def test_missing_approval_cannot_enable_operation_2():
    request = copy.deepcopy(load_request(DEFAULT_REQUEST))
    request["approval"]["enabled"] = True
    _with_scope_digest(request)

    with pytest.raises(RS069R17ApprovalError, match="explicit approval boundary drift"):
        validate_request(request, repository_root=ROOT)


def test_enabling_later_operation_is_rejected():
    request = copy.deepcopy(load_request(DEFAULT_REQUEST))
    request["later_operations"][0]["enabled"] = True
    request["workflow"]["later_operations_enabled"] = True
    _with_scope_digest(request)

    with pytest.raises(RS069R17ApprovalError, match="later operation enabled or reordered"):
        validate_request(request, repository_root=ROOT)


def test_prior_operation_1_approval_is_context_only():
    request = load_request(DEFAULT_REQUEST)
    prior = request["prior_approval_context"]

    assert prior["approval_id"] == "P5-MASTER-001/APPROVAL-002-RS069R6-OP1"
    assert prior["scope"] == ["bind_candidate_image_digest"]
    assert prior["approved"] is True
    assert prior["reusable_for_operation_2"] is False
    assert request["approval"]["approval_id"] is None
    assert request["approval"]["master_approved"] is False
    assert request["approval"]["user_approved"] is False
