from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import services.p5_r0_evaluator.deploy.iam_capability_provisioning as iam
from evaluation.p0a.canonical import sha256
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import (
    BROAD_ROLE,
    CUSTOM_ROLE,
    DEFAULT_DEFINITION,
    EXACT_CONDITION,
    EXACT_CONDITION_TITLE,
    GCS_ONLY_ACCOUNT,
    IAMProvisioningError,
    OPERATION_ID,
    STALE_WIF_PRINCIPAL,
    STALE_WIF_ROLE,
    TOKEN_CREATOR,
    WIF_PRINCIPAL,
    execute_provisioning,
    normalize_prestate,
    validate_definition,
    validate_poststate,
    validate_prestate,
)

ROOT = Path(__file__).resolve().parents[3]


def _binding(member: str, role: str, condition=None):
    return {"member": member, "role": role, "condition": condition}


def _raw_prestate():
    return {
        "project": {"project_id": "ocelot-proof", "project_number": "141633828616"},
        "bucket": {"name": "p5-evaluator-ocelot-proof-141633828616", "project_id": "ocelot-proof", "uniform_bucket_level_access": True, "public_access_prevention": "inherited"},
        "bucket_policy": {"etag": "bucket-etag-before", "bindings": [
            _binding("serviceAccount:p5-evaluator@ocelot-proof.iam.gserviceaccount.com", BROAD_ROLE),
            _binding(STALE_WIF_PRINCIPAL, STALE_WIF_ROLE, {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}),
        ]},
        "existing_account": {"email": "p5-evaluator@ocelot-proof.iam.gserviceaccount.com", "exists": True, "has_key_material": False, "project_roles": ["roles/cloudkms.signerVerifier"]},
        "existing_account_policy": {"fingerprint": "existing-policy-fingerprint", "bindings": [_binding(STALE_WIF_PRINCIPAL, "roles/iam.workloadIdentityUser")]},
        "target_account": {"email": GCS_ONLY_ACCOUNT, "exists": False, "has_key_material": False, "project_roles": []},
        "target_account_policy": None,
        "custom_role": {"name": CUSTOM_ROLE, "exists": False, "etag": None, "fingerprint": None, "title": None, "stage": None, "permissions": []},
    }


def _prestate():
    return normalize_prestate(_raw_prestate())


def _poststate():
    raw = _raw_prestate()
    raw["bucket_policy"] = {"etag": "bucket-etag-after", "bindings": [
        _binding("serviceAccount:unrelated@example.iam.gserviceaccount.com", "roles/storage.objectViewer"),
        _binding("serviceAccount:" + GCS_ONLY_ACCOUNT, CUSTOM_ROLE, {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}),
    ]}
    raw["target_account"] = {"email": GCS_ONLY_ACCOUNT, "exists": True, "has_key_material": False, "project_roles": []}
    raw["target_account_policy"] = {"etag": "target-policy-etag-after", "bindings": [_binding(WIF_PRINCIPAL, TOKEN_CREATOR)]}
    raw["custom_role"] = {"name": CUSTOM_ROLE, "exists": True, "etag": "role-etag-after", "fingerprint": None, "title": "P5 R0 operation 4 bundle writer", "stage": "GA", "permissions": ["storage.objects.create", "storage.objects.get"]}
    return normalize_prestate(raw)


def _approval(prestate):
    value = {
        "schema": "P5R0DISPATCH050IAMApprovalV1",
        "approval_id": "P5-MASTER-001/APPROVAL-050-IAM",
        "custody": "self_custodied",
        "operation_id": OPERATION_ID,
        "scope": [OPERATION_ID],
        "status": "approved_single_operation_pending_apply",
        "attempt_id": "dispatch050-iam-20260919-a1b2c3d4",
        "definition_digest": validate_definition()["definition_digest"],
        "prestate_digest": prestate["state_digest"],
        "signed_environment_evidence_digest": "sha256:" + "a" * 64,
        "credential_binding_digest": "sha256:" + "b" * 64,
    }
    return {**value, "artifact_digest": sha256(value)}


def _write_artifacts(tmp_path, prestate):
    approval = _approval(prestate)
    approval_path = tmp_path / "rs069r18r13-iam-approval.json"
    prestate_path = tmp_path / "rs069r18r13-iam-expected-prestate.json"
    approval_path.write_text(json.dumps(approval))
    prestate_artifact = {"schema": "P5R0DISPATCH050IAMExpectedPrestateArtifactV1", "state": prestate}
    prestate_artifact["artifact_digest"] = sha256(prestate_artifact)
    prestate_path.write_text(json.dumps(prestate_artifact))
    return approval_path, prestate_path


class FakeExecutor:
    def __init__(self, prestate, poststate, *, fail_at=None):
        self.prestate = copy.deepcopy(prestate)
        self.poststate = copy.deepcopy(poststate)
        self.fail_at = fail_at
        self.calls = []
        self.requests = {}

    def _maybe_fail(self, name):
        self.calls.append(name)
        if self.fail_at == name or (isinstance(self.fail_at, tuple) and name in self.fail_at):
            raise RuntimeError(name)

    def describe_prestate(self):
        self.calls.append("describe_prestate")
        return copy.deepcopy(self.prestate)

    def ensure_service_account(self, email):
        self._maybe_fail("ensure_service_account")

    def apply_custom_role(self, request):
        self.requests["custom_role"] = copy.deepcopy(request)
        self._maybe_fail("apply_custom_role")

    def update_bucket_policy(self, request):
        self.requests["bucket_policy"] = copy.deepcopy(request)
        self._maybe_fail("update_bucket_policy")

    def update_target_account_policy(self, request):
        self.requests["target_account_policy"] = copy.deepcopy(request)
        self._maybe_fail("update_target_account_policy")

    def describe_poststate(self):
        self.calls.append("describe_poststate")
        return copy.deepcopy(self.prestate if (self.fail_at == "poststate_drift" or isinstance(self.fail_at, tuple) and "poststate_drift" in self.fail_at) else self.poststate)

    def restore_target_account_policy(self, request):
        self.requests["restore_target_account_policy"] = copy.deepcopy(request)
        self._maybe_fail("restore_target_account_policy")

    def restore_bucket_policy(self, request):
        self.requests["restore_bucket_policy"] = copy.deepcopy(request)
        self._maybe_fail("restore_bucket_policy")

    def restore_custom_role(self, request):
        self.requests["restore_custom_role"] = copy.deepcopy(request)
        self._maybe_fail("restore_custom_role")


def test_definition_is_blocked_and_binds_separate_gcs_only_identity():
    report = validate_definition()
    assert report["gcs_only_account"] == GCS_ONLY_ACCOUNT
    assert report["wif_principal"] == WIF_PRINCIPAL
    assert report["cloud_operations"] == []
    assert report["apply_performed"] is False


def test_definition_rejects_custom_role_or_exact_prefix_drift(tmp_path):
    value = json.loads(DEFAULT_DEFINITION.read_text())
    value["custom_role"]["permissions"].append("storage.objects.delete")
    value["definition_digest"] = sha256({key: item for key, item in value.items() if key != "definition_digest"})
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(value))
    with pytest.raises(IAMProvisioningError, match="custom role drift"):
        validate_definition(path)


def test_prestate_requires_versioned_etag_or_fingerprint_and_binds_digest():
    prestate = _prestate()
    assert prestate["bucket_policy"]["etag"] == "bucket-etag-before"
    assert prestate["existing_account_policy"]["fingerprint"] == "existing-policy-fingerprint"
    validate_prestate(prestate, copy.deepcopy(prestate))
    broken = copy.deepcopy(prestate)
    broken["bucket_policy"].pop("etag")
    with pytest.raises(IAMProvisioningError, match="exactly one etag or fingerprint"):
        validate_prestate(broken, prestate)
    drifted = copy.deepcopy(prestate)
    drifted["bucket_policy"]["etag"] = "different-etag"
    drifted["state_digest"] = sha256({key: item for key, item in drifted.items() if key != "state_digest"})
    with pytest.raises(IAMProvisioningError, match="fresh IAM prestate drift"):
        validate_prestate(drifted, prestate)


def test_poststate_requires_exact_grant_token_creator_and_no_broad_or_public_access():
    poststate = _poststate()
    checked = validate_poststate(poststate)
    assert checked["custom_role"]["permissions"] == ["storage.objects.create", "storage.objects.get"]
    public = copy.deepcopy(poststate)
    public["bucket_policy"]["bindings"].append(_binding("allUsers", "roles/storage.objectViewer"))
    public = normalize_prestate({key: item for key, item in public.items() if key != "state_digest"})
    with pytest.raises(IAMProvisioningError, match="public principal"):
        validate_poststate(public)


def test_successful_apply_is_ordered_verified_and_non_cloud_local(tmp_path):
    prestate = _prestate()
    executor = FakeExecutor(prestate, _poststate())
    approval_path, prestate_path = _write_artifacts(tmp_path, prestate)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    try:
        result = iam.execute_provisioning(executor=executor, ledger_path=tmp_path / "iam.jsonl")
    finally:
        monkeypatch.undo()
    assert result["status"] == "verified"
    assert result["mutations_performed"] is True
    assert result["later_operations_enabled"] is False
    assert result["receipt"]["service_account"] == GCS_ONLY_ACCOUNT
    assert result["receipt"]["wif_principal"] == WIF_PRINCIPAL
    assert result["receipt"]["condition_expression"] == EXACT_CONDITION
    assert executor.requests["bucket_policy"]["expected_version"] == {"field": "etag", "value": "bucket-etag-before"}
    assert executor.requests["bucket_policy"]["remove_bindings"][0]["role"] == BROAD_ROLE
    assert executor.requests["target_account_policy"]["replace_bindings"] == [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}]
    assert executor.calls == ["describe_prestate", "ensure_service_account", "apply_custom_role", "update_bucket_policy", "update_target_account_policy", "describe_poststate"]


def test_poststate_failure_rolls_back_in_reverse_and_records_failed_closed(tmp_path):
    prestate = _prestate()
    executor = FakeExecutor(prestate, _poststate(), fail_at="poststate_drift")
    ledger = tmp_path / "iam.jsonl"
    approval_path, prestate_path = _write_artifacts(tmp_path, prestate)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    try:
        result = iam.execute_provisioning(executor=executor, ledger_path=ledger)
    finally:
        monkeypatch.undo()
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    assert executor.calls[-5:] == ["describe_poststate", "restore_target_account_policy", "restore_bucket_policy", "restore_custom_role", "describe_poststate"]
    records = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert records[-1]["rollback_status"] == "rolled_back_verified"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    try:
        with pytest.raises(IAMProvisioningError, match="retry is disabled"):
            iam.execute_provisioning(executor=executor, ledger_path=ledger)
    finally:
        monkeypatch.undo()


def test_rollback_failure_is_manual_review_and_no_retry(tmp_path):
    prestate = _prestate()
    executor = FakeExecutor(prestate, _poststate(), fail_at=("poststate_drift", "restore_bucket_policy"))
    approval_path, prestate_path = _write_artifacts(tmp_path, prestate)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    try:
        result = iam.execute_provisioning(executor=executor, ledger_path=tmp_path / "iam.jsonl")
    finally:
        monkeypatch.undo()
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rollback_failed_manual_review"



def test_apply_requires_canonical_approval_and_prestate_artifacts(tmp_path):
    prestate = _prestate()
    executor = FakeExecutor(prestate, _poststate())
    approval = tmp_path / "rs069r18r13-iam-approval.json"
    prestate_path = tmp_path / "rs069r18r13-iam-expected-prestate.json"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    try:
        with pytest.raises(IAMProvisioningError, match="invalid JSON"):
            iam.execute_provisioning(executor=executor, ledger_path=tmp_path / "iam.jsonl")
    finally:
        monkeypatch.undo()



def test_poststate_preserves_existing_kms_authority_and_policy():
    prestate = _prestate()
    poststate = _poststate()
    validate_poststate(poststate, prestate)
    drifted = copy.deepcopy(poststate)
    drifted["existing_account"]["project_roles"] = []
    drifted = normalize_prestate({key: item for key, item in drifted.items() if key != "state_digest"})
    with pytest.raises(IAMProvisioningError, match="KMS authority drift|existing account drift"):
        validate_poststate(drifted, prestate)
    drifted = copy.deepcopy(poststate)
    drifted["existing_account_policy"]["bindings"] = []
    drifted = normalize_prestate({key: item for key, item in drifted.items() if key != "state_digest"})
    with pytest.raises(IAMProvisioningError, match="existing account policy drift"):
        validate_poststate(drifted, prestate)



def test_operation4_cloud_run_template_matches_reviewed_namespace_and_zone():
    template = (ROOT / "services/p5_r0_evaluator/deploy/cloud-run.yaml").read_text()
    assert "serviceAccountName: p5-r0-gcs-only@PROJECT_ID.iam.gserviceaccount.com" in template
    assert "value: p5-evaluator-ocelot-proof-141633828616" in template
    assert "value: p5-r0/operation-4/rs069r18r13-op4-04a98e3e/" in template
    assert "zones/us-east1-b/instances/" in template
    assert "value: //iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production" in template
    assert "value: us-east1" in template



def test_normalization_preserves_bucket_visibility_and_poststate_rejects_drift():
    raw = _raw_prestate()
    raw["bucket"]["uniform_bucket_level_access"] = False
    observed = normalize_prestate(raw)
    assert observed["bucket"]["uniform_bucket_level_access"] is False
    with pytest.raises(IAMProvisioningError, match="fresh IAM prestate drift"):
        validate_prestate(observed, _prestate())

    post = _poststate()
    post_raw = {key: value for key, value in post.items() if key != "state_digest"}
    post_raw["bucket"]["public_access_prevention"] = "enforced"
    drifted_post = normalize_prestate(post_raw)
    with pytest.raises(IAMProvisioningError, match="poststate bucket visibility drift"):
        validate_poststate(drifted_post)


def test_poststate_requires_exact_custom_role_metadata():
    raw = _poststate()
    raw = {key: value for key, value in raw.items() if key != "state_digest"}
    raw["custom_role"]["title"] = "different title"
    with pytest.raises(IAMProvisioningError, match="custom role metadata drift"):
        normalize_prestate(raw)


class AccountCreationPersistsExecutor(FakeExecutor):
    """Model creation succeeding before a later operation fails; no auto-delete is allowed."""

    def ensure_service_account(self, email):
        self._maybe_fail("ensure_service_account")
        created = copy.deepcopy(self.prestate)
        created["target_account"] = {"email": GCS_ONLY_ACCOUNT, "exists": True, "has_key_material": False, "project_roles": []}
        created["target_account_policy"] = {"etag": "created-target-policy", "bindings": []}
        self.poststate = created


def test_created_account_partial_failure_is_manual_review_and_not_retryable(tmp_path):
    prestate = _prestate()
    executor = AccountCreationPersistsExecutor(prestate, _poststate(), fail_at="apply_custom_role")
    approval_path, prestate_path = _write_artifacts(tmp_path, prestate)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    ledger = tmp_path / "iam-created-account.jsonl"
    try:
        result = iam.execute_provisioning(executor=executor, ledger_path=ledger)
    finally:
        monkeypatch.undo()
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rollback_failed_manual_review"
    assert result["mutations_performed"] is True
    records = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert records[-1]["failed_phase"] == "custom_role"
    assert records[-1]["rollback_status"] == "rollback_failed_manual_review"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    try:
        with pytest.raises(IAMProvisioningError, match="retry is disabled"):
            iam.execute_provisioning(executor=executor, ledger_path=ledger)
    finally:
        monkeypatch.undo()



@pytest.mark.parametrize("failed_phase,ledger_phase", [("apply_custom_role", "custom_role"), ("update_bucket_policy", "bucket_policy"), ("update_target_account_policy", "target_account_policy")])
def test_policy_and_role_partial_failures_rollback_and_disable_retry(tmp_path, failed_phase, ledger_phase):
    prestate = _prestate()
    executor = FakeExecutor(prestate, _poststate(), fail_at=failed_phase)
    approval_path, prestate_path = _write_artifacts(tmp_path, prestate)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    ledger = tmp_path / f"iam-{failed_phase}.jsonl"
    try:
        result = iam.execute_provisioning(executor=executor, ledger_path=ledger)
    finally:
        monkeypatch.undo()
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rollback_failed_manual_review"
    assert result["mutations_performed"] is True
    terminal = json.loads(ledger.read_text().splitlines()[-1])
    assert terminal["failed_phase"] == ledger_phase
    assert terminal["rollback_status"] == "rollback_failed_manual_review"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(iam, "DEFAULT_APPROVAL", approval_path)
    monkeypatch.setattr(iam, "DEFAULT_PRESTATE", prestate_path)
    try:
        with pytest.raises(IAMProvisioningError, match="retry is disabled"):
            iam.execute_provisioning(executor=executor, ledger_path=ledger)
    finally:
        monkeypatch.undo()
