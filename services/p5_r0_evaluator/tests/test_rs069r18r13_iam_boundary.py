from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from evaluation.p0a.canonical import sha256
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import (
    BROAD_ROLE,
    BUCKET,
    CUSTOM_ROLE,
    EXACT_CONDITION,
    EXACT_CONDITION_TITLE,
    GCS_ONLY_ACCOUNT,
    STALE_WIF_PRINCIPAL,
    STALE_WIF_ROLE,
    TOKEN_CREATOR,
    WIF_PRINCIPAL,
    WIF_PROVIDER,
    WIF_IMAGE_DIGEST,
    STS_AUDIENCE,
    AUTHORITY_BINDING_DIGEST,
    InjectedSignedEnvironmentCredential,
    IAMProvisioningError,
    ReviewedIAMExecutorAdapter,
    normalize_prestate,
)
from services.p5_r0_evaluator.credential_evidence import (
    CredentialEvidenceError,
    VerifiedCredentialReadinessEvidence,
    _commitment,
    build_verified_credential_readiness_evidence,
)
from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.confidential_space import ConfidentialSpaceAdapter, FederatedAccessToken
from services.p5_r0_evaluator.deploy.signed_environment_process import validate_short_lived_capability
from services.p5_r0_evaluator.tests.test_confidential_space import FakeSource, FakeVerifier, _claims, _config
from services.p5_r0_evaluator.deploy import rs069r18r13_iam_boundary as boundary
from services.p5_r0_evaluator.deploy.rs069r18r13_iam_boundary import (
    APPROVAL_DIGEST,
    CREDENTIAL_DIGEST,
    OLD_PACKET_DIGEST,
    PACKET_DIGEST,
    GCS_DEFINITION_DIGEST,
    IAMBoundaryError,
    execute_reviewed_iam,
    transition_credential_readiness,
    validate_iam_boundary,
)


class Backend:
    reviewed = True
    target_service_account = GCS_ONLY_ACCOUNT
    custom_role = CUSTOM_ROLE
    uses_adc = False
    direct_gcloud = False

    def __init__(self, *, prestate=None, poststate=None, fail_at=None):
        self.calls = []
        self.credential = None
        self.prestate = copy.deepcopy(prestate)
        self.poststate = copy.deepcopy(poststate)
        self.fail_at = fail_at
        self.requests = {}

    def _record(self, name, credential, *args):
        self.calls.append(name)
        if self.fail_at == name or (isinstance(self.fail_at, tuple) and name in self.fail_at):
            raise RuntimeError(name)
        self.credential = credential
        return args

    def verify_signed_environment_credential(self, credential):
        return getattr(self, "credential_verified", True)

    def describe_prestate(self, credential):
        self._record("describe_prestate", credential)
        return copy.deepcopy(self.prestate) if self.prestate is not None else {"state_digest": "sha256:" + "a" * 64}

    def ensure_service_account(self, credential, email):
        self._record("ensure_service_account", credential, email)

    def apply_custom_role(self, credential, request):
        self.requests["custom_role"] = copy.deepcopy(request)
        self._record("apply_custom_role", credential, request)

    def update_bucket_policy(self, credential, request):
        self.requests["bucket_policy"] = copy.deepcopy(request)
        self._record("update_bucket_policy", credential, request)

    def update_target_account_policy(self, credential, request):
        self.requests["target_account_policy"] = copy.deepcopy(request)
        self._record("update_target_account_policy", credential, request)

    def describe_poststate(self, credential):
        self._record("describe_poststate", credential)
        if self.poststate is None:
            return {"state_digest": "sha256:" + "b" * 64}
        return copy.deepcopy(self.prestate if self.fail_at == "poststate_drift" or (isinstance(self.fail_at, tuple) and "poststate_drift" in self.fail_at) else self.poststate)

    def restore_target_account_policy(self, credential, request):
        self._record("restore_target_account_policy", credential, request)

    def restore_bucket_policy(self, credential, request):
        self._record("restore_bucket_policy", credential, request)

    def restore_custom_role(self, credential, request):
        self._record("restore_custom_role", credential, request)


def credential(**overrides):
    values = {
        "evidence_digest": "sha256:" + "c" * 64,
        "target_service_account": GCS_ONLY_ACCOUNT,
        "expires_at": 2_000_000_000,
        "packet_digest": PACKET_DIGEST,
        "provider": WIF_PROVIDER,
        "image_digest": WIF_IMAGE_DIGEST,
        "audience": STS_AUDIENCE,
        "authority_binding_digest": AUTHORITY_BINDING_DIGEST,
        "principal": WIF_PRINCIPAL,
        "target_resource": f"projects/ocelot-proof/serviceAccounts/{GCS_ONLY_ACCOUNT}",
        "attestation_digest": "sha256:" + "d" * 64,
        "attestation_signature": "signed-attestation-proof",
        "attestation_claims": {"aud": STS_AUDIENCE, "submods.container.image_digest": WIF_IMAGE_DIGEST},
    }
    values.update(overrides)
    return InjectedSignedEnvironmentCredential(**values)


def test_new_boundary_binds_current_evidence_and_preserves_old_packet():
    report = validate_iam_boundary()
    assert report["packet_digest"] == PACKET_DIGEST
    assert report["approval_digest"] == APPROVAL_DIGEST
    assert report["old_packet_digest"] == OLD_PACKET_DIGEST
    assert report["service_account"] == GCS_ONLY_ACCOUNT
    assert report["ready_for_executor"] is False
    assert report["mutations_performed"] is False
    assert report["applied_state"] is False
    assert any("credential" in item for item in report["unresolved"])


def test_current_boundary_cannot_be_executed_without_external_prerequisites():
    with pytest.raises(IAMBoundaryError, match="signed credential and enabled approval"):
        execute_reviewed_iam(executor=None)  # type: ignore[arg-type]


def test_executor_gate_requires_sealed_evidence_even_if_report_is_ready(monkeypatch):
    monkeypatch.setattr(boundary, "validate_iam_boundary", lambda **_: _ready_report())
    with pytest.raises(IAMBoundaryError, match="verifier-owned credential evidence"):
        execute_reviewed_iam(executor=None)  # type: ignore[arg-type]


    with pytest.raises(IAMProvisioningError, match="signed-environment credential is required"):
        ReviewedIAMExecutorAdapter(backend=Backend(), credential=None)


def test_adapter_rejects_wrong_account_or_unreviewed_backend():
    with pytest.raises(IAMProvisioningError, match="target service account precondition"):
        ReviewedIAMExecutorAdapter(backend=Backend(), credential=credential(), target_service_account="wrong@example.com")
    backend = Backend()
    backend.direct_gcloud = True
    with pytest.raises(IAMProvisioningError, match="direct unreviewed gcloud"):
        ReviewedIAMExecutorAdapter(backend=backend, credential=credential())


def test_adapter_rejects_missing_target_or_role_backend_preconditions():
    class MissingBackend:
        reviewed = True
        uses_adc = False
        direct_gcloud = False

    with pytest.raises(IAMProvisioningError, match="backend target account precondition"):
        ReviewedIAMExecutorAdapter(backend=MissingBackend(), credential=credential())

    class MissingRoleBackend(MissingBackend):
        target_service_account = GCS_ONLY_ACCOUNT

    with pytest.raises(IAMProvisioningError, match="backend custom-role precondition"):
        ReviewedIAMExecutorAdapter(backend=MissingRoleBackend(), credential=credential())


def test_adapter_forwards_only_exact_targets_and_credential_on_each_call():
    backend = Backend()
    injected = credential()
    adapter = ReviewedIAMExecutorAdapter(backend=backend, credential=injected, clock=lambda: 1_000)
    adapter.describe_prestate()
    adapter.ensure_service_account(GCS_ONLY_ACCOUNT)
    role_request = {"schema": "P5R0DISPATCH050CustomRoleUpdateV1", "resource": CUSTOM_ROLE, "expected_version": None, "expected_absent": True, "title": "P5 R0 operation 4 bundle writer", "stage": "GA", "permissions": ["storage.objects.create", "storage.objects.get"]}
    role_request["request_digest"] = sha256(role_request)
    bucket_request = {"schema": "P5R0DISPATCH050BucketPolicyUpdateV1", "bucket": BUCKET, "expected_version": {"field": "etag", "value": "bucket-etag"}, "expected_absent": False, "add_bindings": [{"member": f"serviceAccount:{GCS_ONLY_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}], "remove_bindings": [{"member": f"serviceAccount:p5-evaluator@ocelot-proof.iam.gserviceaccount.com", "role": BROAD_ROLE, "condition": None}, {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}}], "public_principals_allowed": False}
    bucket_request["request_digest"] = sha256(bucket_request)
    target_request = {"schema": "P5R0DISPATCH050ServiceAccountPolicyUpdateV1", "service_account": GCS_ONLY_ACCOUNT, "expected_version": None, "expected_absent": True, "replace_bindings": [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}], "public_principals_allowed": False}
    target_request["request_digest"] = sha256(target_request)
    adapter.apply_custom_role(role_request)
    adapter.update_bucket_policy(bucket_request)
    adapter.update_target_account_policy(target_request)
    adapter.describe_poststate()
    adapter.restore_target_account_policy({"schema": "P5R0DISPATCH050ServiceAccountPolicyRestoreV1", "service_account": GCS_ONLY_ACCOUNT, "expected_version": {"field": "etag", "value": "target"}, "expected_absent": False, "restore_state": {}})
    adapter.restore_bucket_policy({"schema": "P5R0DISPATCH050BucketPolicyRestoreV1", "bucket": BUCKET, "expected_version": {"field": "etag", "value": "bucket"}, "expected_absent": False, "restore_state": {}})
    adapter.restore_custom_role({"schema": "P5R0DISPATCH050CustomRoleRestoreV1", "resource": CUSTOM_ROLE, "expected_version": None, "expected_absent": True, "restore_state": {}})
    assert backend.calls == [
        "describe_prestate",
        "ensure_service_account",
        "apply_custom_role",
        "update_bucket_policy",
        "update_target_account_policy",
        "describe_poststate",
        "restore_target_account_policy",
        "restore_bucket_policy",
        "restore_custom_role",
    ]
    assert backend.credential is injected


def test_adapter_fails_closed_on_expired_or_exported_credential():
    with pytest.raises(IAMProvisioningError, match="expired"):
        ReviewedIAMExecutorAdapter(backend=Backend(), credential=credential(expires_at=10), clock=lambda: 11)
    with pytest.raises(IAMProvisioningError, match="no-key/no-ADC"):
        ReviewedIAMExecutorAdapter(backend=Backend(), credential=credential(exported=True))



def test_adapter_requires_exact_approved_provenance_and_backend_cryptographic_verification():
    backend = Backend()
    injected = credential()
    adapter = ReviewedIAMExecutorAdapter(backend=backend, credential=injected, clock=lambda: 1_000)
    adapter.validate_credential_binding({"evidence_digest": injected.evidence_digest, "packet_digest": PACKET_DIGEST})
    backend.credential_verified = False
    with pytest.raises(IAMProvisioningError, match="cryptographic verification"):
        adapter.validate_credential_binding({"evidence_digest": injected.evidence_digest, "packet_digest": PACKET_DIGEST})
    backend.credential_verified = True
    with pytest.raises(IAMProvisioningError, match="approved"):
        adapter.validate_credential_binding({"evidence_digest": "sha256:" + "e" * 64, "packet_digest": PACKET_DIGEST})


def test_adapter_rejects_incomplete_desired_bucket_contract():
    adapter = ReviewedIAMExecutorAdapter(backend=Backend(), credential=credential(), clock=lambda: 1_000)
    with pytest.raises(IAMProvisioningError, match="incomplete"):
        adapter.update_bucket_policy({"bucket": BUCKET})



def _local_states():
    raw = json.loads(boundary.DEFAULT_PRESTATE.read_text())["state"]
    prestate = normalize_prestate(raw)
    post_raw = copy.deepcopy(prestate)
    post_raw["bucket_policy"] = {"etag": "bucket-etag-after", "bindings": [{"member": f"serviceAccount:{GCS_ONLY_ACCOUNT}", "role": CUSTOM_ROLE, "condition": {"title": EXACT_CONDITION_TITLE, "expression": EXACT_CONDITION}}]}
    post_raw["target_account"] = {"email": GCS_ONLY_ACCOUNT, "exists": True, "has_key_material": False, "project_roles": []}
    post_raw["target_account_policy"] = {"etag": "target-policy-etag-after", "bindings": [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}]}
    post_raw["custom_role"] = {"name": CUSTOM_ROLE, "exists": True, "etag": "role-etag-after", "fingerprint": None, "title": "P5 R0 operation 4 bundle writer", "stage": "GA", "permissions": ["storage.objects.create", "storage.objects.get"]}
    return prestate, normalize_prestate({key: value for key, value in post_raw.items() if key != "state_digest"})


def _ready_report():
    return {"ready_for_executor": True, "packet_digest": PACKET_DIGEST, "approval_digest": APPROVAL_DIGEST, "credential_binding_digest": CREDENTIAL_DIGEST, "prestate_state_digest": boundary.PRESTATE_STATE_DIGEST}


def _ready_evidence():
    return _sealed_credential_fixture()[1]


def test_reviewed_boundary_success_forwards_closed_requests_and_receipt(tmp_path, monkeypatch):
    prestate, poststate = _local_states()
    backend = Backend(prestate=prestate, poststate=poststate)
    injected = credential(evidence_digest=CREDENTIAL_DIGEST)
    adapter = ReviewedIAMExecutorAdapter(backend=backend, credential=injected, clock=lambda: 1_000)
    monkeypatch.setattr(boundary, "validate_iam_boundary", lambda **_: _ready_report())
    result = boundary.execute_reviewed_iam(executor=adapter, ledger_path=tmp_path / "r18r13.jsonl", credential_evidence=_ready_evidence())
    assert result["status"] == "verified"
    assert result["mutations_performed"] is True
    assert backend.calls == ["describe_prestate", "ensure_service_account", "apply_custom_role", "update_bucket_policy", "update_target_account_policy", "describe_poststate"]
    assert backend.requests["bucket_policy"]["add_bindings"][0]["condition"]["expression"] == EXACT_CONDITION
    assert backend.requests["bucket_policy"]["expected_version"] == {"field": "etag", "value": "CEg="}
    assert backend.requests["custom_role"]["expected_absent"] is True
    assert backend.requests["target_account_policy"]["expected_absent"] is True
    assert backend.requests["bucket_policy"]["remove_bindings"] == [{"member": "serviceAccount:p5-evaluator@ocelot-proof.iam.gserviceaccount.com", "role": BROAD_ROLE, "condition": None}, {"member": STALE_WIF_PRINCIPAL, "role": STALE_WIF_ROLE, "condition": {"expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/v3/')"}}]
    assert backend.requests["target_account_policy"]["replace_bindings"] == [{"member": WIF_PRINCIPAL, "role": TOKEN_CREATOR, "condition": None}]
    assert result["receipt"]["service_account"] == GCS_ONLY_ACCOUNT


def test_reviewed_boundary_partial_failure_rolls_back_and_disables_retry(tmp_path, monkeypatch):
    prestate, poststate = _local_states()
    backend = Backend(prestate=prestate, poststate=poststate, fail_at="poststate_drift")
    adapter = ReviewedIAMExecutorAdapter(backend=backend, credential=credential(evidence_digest=CREDENTIAL_DIGEST), clock=lambda: 1_000)
    monkeypatch.setattr(boundary, "validate_iam_boundary", lambda **_: _ready_report())
    ledger = tmp_path / "r18r13.jsonl"
    result = boundary.execute_reviewed_iam(executor=adapter, ledger_path=ledger, credential_evidence=_ready_evidence())
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    assert backend.calls[-5:] == ["describe_poststate", "restore_target_account_policy", "restore_bucket_policy", "restore_custom_role", "describe_poststate"]
    with pytest.raises(IAMBoundaryError, match="retry is disabled"):
        boundary.execute_reviewed_iam(executor=adapter, ledger_path=ledger, credential_evidence=_ready_evidence())


def test_reviewed_boundary_ambiguity_enters_manual_review(tmp_path, monkeypatch):
    prestate, poststate = _local_states()
    backend = Backend(prestate=prestate, poststate=poststate, fail_at=("poststate_drift", "restore_bucket_policy"))
    adapter = ReviewedIAMExecutorAdapter(backend=backend, credential=credential(evidence_digest=CREDENTIAL_DIGEST), clock=lambda: 1_000)
    monkeypatch.setattr(boundary, "validate_iam_boundary", lambda **_: _ready_report())
    result = boundary.execute_reviewed_iam(executor=adapter, ledger_path=tmp_path / "r18r13.jsonl", credential_evidence=_ready_evidence())
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rollback_failed_manual_review"
    assert result["later_operations_enabled"] is False



def test_boundary_reloads_and_rejects_tampered_historical_packet(tmp_path, monkeypatch):
    historical = tmp_path / "historical.json"
    value = json.loads((boundary.REPOSITORY_ROOT / "services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json").read_text())
    value["status"] = "tampered"
    historical.write_text(json.dumps(value))
    original_resolve = boundary._resolve

    def resolve(path, label, root):
        if label == "historical superseded packet":
            return historical
        return original_resolve(path, label, root)

    monkeypatch.setattr(boundary, "_resolve", resolve)
    with pytest.raises(IAMBoundaryError, match="historical superseded packet digest mismatch"):
        validate_iam_boundary()



def _sealed_credential_fixture():
    expected = {
        "packet_digest": PACKET_DIGEST,
        "evidence_digest": digest("signed-environment-evidence"),
        "provider": WIF_PROVIDER,
        "image_digest": WIF_IMAGE_DIGEST,
        "audience": STS_AUDIENCE,
        "principal": WIF_PRINCIPAL,
        "target_resource": f"projects/ocelot-proof/serviceAccounts/{GCS_ONLY_ACCOUNT}",
        "authority_binding_digest": AUTHORITY_BINDING_DIGEST,
        "service_account": GCS_ONLY_ACCOUNT,
        "capability_binding_digest": GCS_DEFINITION_DIGEST,
    }
    config, _ = _config()
    config = replace(config, wip_provider=WIF_PROVIDER, image_digest=WIF_IMAGE_DIGEST, attestation_audience=STS_AUDIENCE, capability_service_account=GCS_ONLY_ACCOUNT, clock=lambda: 1_000)
    sts = type("FixtureSTS", (), {"exchange": lambda self, **_: FederatedAccessToken("federated", 1_200)})()
    factory = type("FixtureCapabilities", (), {"build": lambda self, token: type("Capabilities", (), {"credentials_expires_at": token.expires_at})()})()
    adapter = ConfidentialSpaceAdapter(config, source=FakeSource(), verifier=FakeVerifier(_claims(config)), sts=sts, capability_factory=factory, service_factory=lambda _capabilities: object())
    adapter.activate_attested_service()
    receipt = validate_short_lived_capability(FederatedAccessToken("federated", 1_200), FederatedAccessToken("capability", 1_150), source_token_digest=digest("federated"), capability_binding_digest=expected["capability_binding_digest"], service_account=GCS_ONLY_ACCOUNT, now=1_000)
    injected = credential(evidence_digest=expected["evidence_digest"], packet_digest=expected["packet_digest"], provider=expected["provider"], image_digest=expected["image_digest"], audience=expected["audience"], authority_binding_digest=expected["authority_binding_digest"], target_service_account=GCS_ONLY_ACCOUNT, expires_at=1_150, attestation_claims={"aud": STS_AUDIENCE, "submods.container.image_digest": WIF_IMAGE_DIGEST})
    executor = ReviewedIAMExecutorAdapter(backend=Backend(), credential=injected, clock=lambda: 1_000)
    evidence = build_verified_credential_readiness_evidence(adapter=adapter, executor=executor, capability_receipt=receipt, now=1_000)
    return expected, evidence, adapter, executor, receipt


def test_credential_readiness_is_derived_from_sealed_adapter_evidence():
    report = validate_iam_boundary()
    assert report["credential_readiness"] == "unresolved"
    assert report["credential_ready"] is False

    expected, evidence, _adapter, _executor, _receipt = _sealed_credential_fixture()
    assert isinstance(evidence, VerifiedCredentialReadinessEvidence)
    assert transition_credential_readiness("unresolved", "unresolved", credential_evidence=None, now=1_000) == "unresolved"
    assert transition_credential_readiness("unresolved", "verified", credential_evidence=evidence, now=1_000) == "verified"
    with pytest.raises(IAMBoundaryError, match="cannot regress"):
        transition_credential_readiness("verified", "unresolved", credential_evidence=None, now=1_000)


def test_credential_readiness_rejects_forged_boolean_mapping_and_lookalike():
    expected, evidence, _adapter, _executor, _receipt = _sealed_credential_fixture()
    with pytest.raises(TypeError):
        transition_credential_readiness("unresolved", "verified", credential=evidence, provenance_verified=True, now=1_000)  # type: ignore[call-arg]
    with pytest.raises(IAMBoundaryError, match="verifier-owned"):
        transition_credential_readiness("unresolved", "verified", credential_evidence=dict(evidence.__dict__), now=1_000)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="verifier-created"):
        VerifiedCredentialReadinessEvidence(**evidence.__dict__)
    with pytest.raises(TypeError):
        build_verified_credential_readiness_evidence(adapter=_adapter, executor=_executor, capability_receipt=_sealed_credential_fixture()[4], expected={}, now=1_000)  # type: ignore[call-arg]


def test_recomputed_object_new_copy_and_subclass_evidence_have_no_verifier_identity():
    _expected, evidence, _adapter, _executor, _receipt = _sealed_credential_fixture()
    values = {field: getattr(evidence, field) for field in evidence.__dataclass_fields__}
    values["provider"] = "wrong-provider"
    values["seal_digest"] = _commitment(values)
    forged = object.__new__(VerifiedCredentialReadinessEvidence)
    for field, value in values.items():
        object.__setattr__(forged, field, value)
    with pytest.raises(IAMBoundaryError, match="verifier-issued"):
        transition_credential_readiness("unresolved", "verified", credential_evidence=forged, now=1_000)

    with pytest.raises(IAMBoundaryError, match="verifier-issued"):
        transition_credential_readiness("unresolved", "verified", credential_evidence=copy.copy(evidence), now=1_000)

    class EvidenceSubclass(VerifiedCredentialReadinessEvidence):
        pass

    subclass = object.__new__(EvidenceSubclass)
    for field in evidence.__dataclass_fields__:
        object.__setattr__(subclass, field, getattr(evidence, field))
    with pytest.raises(IAMBoundaryError, match="verifier-owned"):
        transition_credential_readiness("unresolved", "verified", credential_evidence=subclass, now=1_000)


def test_registered_receipt_rejects_mutation_and_reseal_before_executor_verification():
    _expected, _evidence, adapter, executor, receipt = _sealed_credential_fixture()
    from services.p5_r0_evaluator.deploy.signed_environment_process import _receipt_commitment

    object.__setattr__(receipt, "service_account", "attacker@example.com")
    values = {field: getattr(receipt, field) for field in receipt.__dataclass_fields__}
    values["seal_digest"] = _receipt_commitment(values)
    object.__setattr__(receipt, "seal_digest", values["seal_digest"])
    with pytest.raises(CredentialEvidenceError, match="verifier-issued"):
        build_verified_credential_readiness_evidence(adapter=adapter, executor=executor, capability_receipt=receipt, now=1_000)
    assert executor._backend.calls == []


def test_registered_evidence_rejects_mutation_and_reseal_before_executor_calls(tmp_path, monkeypatch):
    _expected, evidence, _source_adapter, _source_executor, _receipt = _sealed_credential_fixture()
    object.__setattr__(evidence, "audience", "https://attacker.example")
    values = {field: getattr(evidence, field) for field in evidence.__dataclass_fields__}
    values["seal_digest"] = _commitment(values)
    object.__setattr__(evidence, "seal_digest", values["seal_digest"])

    backend = Backend()
    executor = ReviewedIAMExecutorAdapter(backend=backend, credential=credential(evidence_digest=CREDENTIAL_DIGEST), clock=lambda: 1_000)
    monkeypatch.setattr(boundary, "validate_iam_boundary", lambda **_: _ready_report())
    with pytest.raises(IAMBoundaryError, match="verifier-issued"):
        boundary.execute_reviewed_iam(executor=executor, ledger_path=tmp_path / "mutated.jsonl", credential_evidence=evidence)
    assert backend.calls == []


def test_execute_rejects_recomputed_forged_evidence_before_executor_calls(tmp_path, monkeypatch):
    _expected, evidence, _source_adapter, _source_executor, _receipt = _sealed_credential_fixture()
    values = {field: getattr(evidence, field) for field in evidence.__dataclass_fields__}
    values["audience"] = "https://attacker.example"
    values["seal_digest"] = _commitment(values)
    forged = object.__new__(VerifiedCredentialReadinessEvidence)
    for field, value in values.items():
        object.__setattr__(forged, field, value)
    backend = Backend()
    executor = ReviewedIAMExecutorAdapter(backend=backend, credential=credential(evidence_digest=CREDENTIAL_DIGEST), clock=lambda: 1_000)
    monkeypatch.setattr(boundary, "validate_iam_boundary", lambda **_: _ready_report())
    with pytest.raises(IAMBoundaryError, match="verifier-issued"):
        boundary.execute_reviewed_iam(executor=executor, ledger_path=tmp_path / "forged.jsonl", credential_evidence=forged)
    assert backend.calls == []


def _tamper(evidence, **changes):
    forged = object.__new__(type(evidence))
    values = {field: getattr(evidence, field) for field in evidence.__dataclass_fields__}
    values.update(changes)
    for field, value in values.items():
        object.__setattr__(forged, field, value)
    return forged


def test_registered_evidence_is_rejected_after_expiry():
    _expected, evidence, _adapter, _executor, _receipt = _sealed_credential_fixture()
    with pytest.raises(IAMBoundaryError, match="expired or not source-bounded"):
        transition_credential_readiness("unresolved", "verified", credential_evidence=evidence, now=1_120)


@pytest.mark.parametrize("field, value", [
    ("packet_digest", digest("stale-packet")),
    ("provider", "wrong-provider"),
    ("image_digest", digest("stale-image")),
    ("audience", "https://stale.example"),
    ("authority_binding_digest", digest("stale-authority")),
    ("service_account", "wrong@example.com"),
    ("capability_binding_digest", digest("stale-capability")),
    ("expires_at", 1_020),
    ("source_expires_at", 5_001),
    ("source_token_digest", digest("wrong-source")),
])
def test_credential_readiness_rejects_stale_or_mismatched_sealed_evidence(field, value):
    expected, evidence, _adapter, _executor, _receipt = _sealed_credential_fixture()
    forged = _tamper(evidence, **{field: value})
    with pytest.raises(IAMBoundaryError, match="verifier-issued"):
        transition_credential_readiness("unresolved", "verified", credential_evidence=forged, now=1_000)


def test_evidence_factory_requires_real_adapter_receipts_and_never_calls_iam_mutations():
    expected, evidence, adapter, executor, receipt = _sealed_credential_fixture()
    backend = executor._backend
    with pytest.raises(Exception, match="sealed capability receipt"):
        build_verified_credential_readiness_evidence(adapter=adapter, executor=executor, capability_receipt=type("LookalikeReceipt", (), evidence.__dict__)(), now=1_000)
    wrong_executor = ReviewedIAMExecutorAdapter(backend=Backend(), credential=credential(provider="wrong-provider"), clock=lambda: 1_000)
    with pytest.raises(Exception, match="reviewed IAM credential verifier did not validate the source"):
        build_verified_credential_readiness_evidence(adapter=adapter, executor=wrong_executor, capability_receipt=receipt, now=1_000)
    assert backend.calls == []
