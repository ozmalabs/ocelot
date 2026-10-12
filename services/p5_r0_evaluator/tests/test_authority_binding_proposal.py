from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.p0a.canonical import canonical_bytes
from services.p5_r0_evaluator.deploy.authority_binding_proposal import (
    DEFAULT_LOCK_REQUEST,
    DEFAULT_PROPOSAL,
    DEFAULT_REQUEST_TEMPLATE,
    DEFAULT_WIP_POLICY,
    REVIEW_AUTHORITY_ID,
    REVIEW_PROVIDER,
    AuthorityBindingProposalValidationError,
    validate_proposal,
    validate_request_template,
)


def _load() -> dict:
    return json.loads(DEFAULT_PROPOSAL.read_text())


def _load_wip() -> dict:
    return json.loads(DEFAULT_WIP_POLICY.read_text())


def test_review_only_proposal_is_canonical_and_blocked():
    assert DEFAULT_PROPOSAL.read_bytes() == canonical_bytes(_load())
    report = validate_proposal()
    assert report["key_id"] == "p5-v3-authority"
    assert report["authority_id"] == REVIEW_AUTHORITY_ID
    assert report["public_key_digest"] == "sha256:c498dbc2447b36d42840ef25705d6b3a3a1f9ff0d54fd3fa012c1f9c52ff9cbb"
    assert report["authority_id_resolved"] is True
    assert report["wip_policy_digest"].startswith("sha256:")
    assert report["signed_environment_approval_required"] is True
    assert report["signature_present"] is False
    assert report["production_promotable"] is False


def test_canonical_wip_policy_is_rerunnable_and_complete():
    assert DEFAULT_WIP_POLICY.read_bytes() == canonical_bytes(_load_wip())
    policy = _load_wip()
    assert set(policy["mapping"]) >= {
        "attribute.debug_state", "attribute.tee", "attribute.hardware_model",
        "attribute.secure_boot", "attribute.workload", "attribute.image_digest",
        "attribute.project_id", "attribute.project_number", "attribute.zone", "google.subject",
    }
    assert set(policy["condition"]) >= {"audience", "issuer", "subject_prefix", "image_digest", "project_id", "project_number", "zone", "debug_state", "tee", "hardware_model", "secure_boot", "workload"}
    assert policy["boundaries"] == {"apply_performed": False, "cloud_operations": [], "generated_lock_request_modified": False, "signed_environment_approval_required": True, "signature_present": False}


def test_frozen_lock_request_is_not_modified():
    proposal = _load()
    request = json.loads(DEFAULT_LOCK_REQUEST.read_text())
    assert proposal["generated_request"]["request_digest"] == request["request_digest"]
    assert proposal["generated_request"]["unsigned_lock_digest"] == request["unsigned_lock_digest"]
    assert proposal["generated_request"]["authority_binding_digest"] is None
    assert request["kms"]["key_version"] is None
    assert proposal["generated_request"]["unchanged"] is True


def test_wrong_review_authority_id_fails_closed(tmp_path: Path):
    proposal = _load()
    proposal["authority"]["authority_id"] = "self-custodied/ocelot-proof/p5-r0/evaluator/wrong-key"
    path = tmp_path / "proposal.json"
    path.write_bytes(canonical_bytes(proposal))
    with pytest.raises(AuthorityBindingProposalValidationError, match="authority ID"):
        validate_proposal(path)


def test_wrong_review_authority_key_fails_closed(tmp_path: Path):
    proposal = _load()
    proposal["authority"]["key_id"] = "p5-timing-bridge"
    path = tmp_path / "proposal.json"
    path.write_bytes(canonical_bytes(proposal))
    with pytest.raises(AuthorityBindingProposalValidationError, match="key ID"):
        validate_proposal(path)


def test_wip_mapping_omission_fails_closed(tmp_path: Path):
    policy = _load_wip()
    del policy["mapping"]["attribute.debug_state"]
    path = tmp_path / "wip-policy.json"
    path.write_bytes(canonical_bytes(policy))
    with pytest.raises(AuthorityBindingProposalValidationError, match="attribute mapping"):
        validate_proposal(wip_policy=path)


def test_provider_and_token_audience_confusion_fails_closed(tmp_path: Path):
    policy = _load_wip()
    policy["bound_claims"]["values"]["audience"] = REVIEW_PROVIDER
    path = tmp_path / "wip-policy.json"
    path.write_bytes(canonical_bytes(policy))
    with pytest.raises(AuthorityBindingProposalValidationError, match="separate from the provider"):
        validate_proposal(wip_policy=path)


def test_signature_or_approval_cannot_be_promoted(tmp_path: Path):
    proposal = _load()
    proposal["signing"]["signature_present"] = True
    path = tmp_path / "proposal.json"
    path.write_bytes(canonical_bytes(proposal))
    with pytest.raises(AuthorityBindingProposalValidationError, match="signing boundary"):
        validate_proposal(path)


def test_observed_wip_policy_drift_is_retained_as_a_blocker(tmp_path: Path):
    proposal = _load()
    proposal["observed_wip_provider"]["attribute_mapping"]["attribute.debug_state"] = "assertion.dbgstat"
    path = tmp_path / "proposal.json"
    path.write_bytes(canonical_bytes(proposal))
    with pytest.raises(AuthorityBindingProposalValidationError, match="WIP observation"):
        validate_proposal(path)



def test_observed_wip_mapping_value_tampering_fails_closed(tmp_path: Path):
    proposal = _load()
    proposal["observed_wip_provider"]["attribute_mapping"]["attribute.image_digest"] = "assertion.submods.gce.zone"
    path = tmp_path / "proposal.json"
    path.write_bytes(canonical_bytes(proposal))
    with pytest.raises(AuthorityBindingProposalValidationError, match="WIP observation mapping"):
        validate_proposal(path)


def test_observed_wip_condition_tampering_fails_closed(tmp_path: Path):
    proposal = _load()
    proposal["observed_wip_provider"]["attribute_condition"] += " && assertion.iss == 'tampered'"
    path = tmp_path / "proposal.json"
    path.write_bytes(canonical_bytes(proposal))
    with pytest.raises(AuthorityBindingProposalValidationError, match="WIP observation condition"):
        validate_proposal(path)



def test_tracked_rs068_request_template_is_reproducible_and_marker_only():
    assert DEFAULT_REQUEST_TEMPLATE.read_bytes() == canonical_bytes(json.loads(DEFAULT_REQUEST_TEMPLATE.read_text()))
    report = validate_request_template()
    assert report == {
        "schema": "P5R0RS068AuthorityBindingRequestV1",
        "status": "blocked_pending_signed_environment_approval",
        "authority_binding_present": False,
        "approval_present": False,
        "signature_present": False,
        "production_promotable": False,
    }
    request = json.loads(DEFAULT_REQUEST_TEMPLATE.read_text())
    assert all(value.startswith("REQUIRED_INPUT:") for value in request["authority"].values())
    assert request["boundaries"]["cloud_operations"] == []


def test_tracked_rs068_request_rejects_authority_promotion(tmp_path: Path):
    request = json.loads(DEFAULT_REQUEST_TEMPLATE.read_text())
    request["authority"]["public_key"] = "locally-invented-key"
    path = tmp_path / "request.json"
    path.write_bytes(canonical_bytes(request))
    with pytest.raises(AuthorityBindingProposalValidationError, match="required-input marker"):
        validate_request_template(path)


def test_tracked_rs068_request_rejects_lock_or_source_drift(tmp_path: Path):
    request = json.loads(DEFAULT_REQUEST_TEMPLATE.read_text())
    request["lock_request"]["authority_binding_digest"] = "sha256:" + "a" * 64
    path = tmp_path / "request.json"
    path.write_bytes(canonical_bytes(request))
    with pytest.raises(AuthorityBindingProposalValidationError, match="lock request commitment"):
        validate_request_template(path)
