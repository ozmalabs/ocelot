from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.p0a.canonical import sha256
from services.p5_r0_evaluator.deploy.iam_predecessor import issue_verified_iam_predecessor
from services.p5_r0_evaluator.deploy import confidential_space_bootstrap as cs

ROOT = Path(__file__).resolve().parents[3]
DEFINITION = ROOT / "services/p5_r0_evaluator/deploy/approval-021-confidential-space-bootstrap-definition-v1.json"


def _predecessor():
    receipt = {"schema": "P5R0APPROVAL023IAMReceiptV1", "operation_id": "provision_gcs_only_iam_boundary", "prestate_digest": "sha256:" + "3" * 64, "service_account": cs.CAPABILITY_SERVICE_ACCOUNT, "custom_role": cs.CUSTOM_ROLE, "wif_principal": "principalSet://test", "condition_expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/p5-r0/operation-4/rs069r18r13-op4-04a98e3e/')", "credentials_exported": False, "keys_created": False}
    receipt["receipt_digest"] = sha256(receipt)
    return issue_verified_iam_predecessor(
        result={"status": "verified", "operation_id": "provision_gcs_only_iam_boundary", "attempt_id": "dispatch082-iam-20260920-a7f4c2d9", "poststate_digest": "sha256:" + "a" * 64, "ledger_head_digest": "sha256:" + "1" * 64, "receipt": receipt, "mutations_performed": True, "later_operations_enabled": False},
        evidence_digest="sha256:" + "4" * 64,
    )


def _definition() -> dict:
    return json.loads(DEFINITION.read_text())


def _approval(definition: dict) -> dict:
    value = {"schema": cs.APPROVAL_SCHEMA, "approval_id": cs.APPROVAL_ID, "status": "approved_single_attempt_pending_apply", "attempt_id": cs.ATTEMPT_ID, "single_attempt": True, "retry_allowed": False, "verifier_issued": True, "definition_digest": definition["definition_digest"], "image_digest": cs.IMAGE_DIGEST, "wip_provider": cs.WIP_PROVIDER, "token_audience": cs.TOKEN_AUDIENCE, "iam_poststate_digest": "sha256:" + "a" * 64, "live_bindings_digest": "sha256:" + "b" * 64}
    return {**value, "approval_digest": sha256(value)}


def _request():
    return cs._request(_definition(), _approval(_definition()))


def _bindings(request):
    return {"iam_poststate_digest": request["iam_poststate_digest"], "wip_poststate_digest": request["live_bindings_digest"], "iam_capability_service_account": cs.CAPABILITY_SERVICE_ACCOUNT, "iam_custom_role": cs.CUSTOM_ROLE, "iam_token_creator_role": "roles/iam.serviceAccountTokenCreator", "iam_direct_bucket_access": False, "wip_provider": cs.WIP_PROVIDER, "token_audience": cs.TOKEN_AUDIENCE, "claim_paths": dict(cs.EXPECTED_CLAIM_PATHS)}


def _prestate(request=None):
    request = request or _request()
    return {"project_id": cs.PROJECT_ID, "zone": cs.ZONE, "vm_name": cs.VM_NAME, "instance_exists": False, "external_ip": False, **_bindings(request)}


def _poststate(request=None):
    request = request or _request()
    return {"project_id": cs.PROJECT_ID, "zone": cs.ZONE, "vm_name": cs.VM_NAME, "instance_exists": True, "machine_type": cs.MACHINE_TYPE, "confidential_compute_type": "SEV", "secure_boot": True, "vtpm": True, "external_ip": False, "image_reference": cs.IMAGE_REFERENCE, "image_digest": cs.IMAGE_DIGEST, "service_account": cs.CAPABILITY_SERVICE_ACCOUNT, "host_mounts": [], "privileged": False, "seccomp": "default-deny-reviewed-profile", "network": "none", "pull": "never", **request["container_closure"], **_bindings(request)}


def _evidence(request, *, mutate: str | None = None):
    value = {"schema": cs.EVIDENCE_SCHEMA, "status": "attested", "source": "verified_confidential_space_launcher", "attestation_verified": True, "request_digest": sha256(request), "approval_digest": request["approval_digest"], "vm_name": request["vm_name"], "image_digest": request["image_digest"], "wip_provider": request["wip_provider"], "token_audience": request["token_audience"], "iam_poststate_digest": request["iam_poststate_digest"], "live_bindings_digest": request["live_bindings_digest"], "policy_digest": request["definition_digest"], "claim_paths_digest": request["claim_paths_digest"], "token_digest": "sha256:" + "c" * 64, "claims_digest": "sha256:" + "d" * 64, "nonce_digest": "sha256:" + "e" * 64}
    if mutate:
        value[mutate] = "wrong"
    return {**value, "evidence_digest": sha256(value)}


def _source(*, fail: bool = False, mutate: str | None = None):
    def capture(request):
        if fail:
            raise RuntimeError("launcher")
        return cs._issue_verifier_evidence(_evidence(request, mutate=mutate))
    return cs.VerifierOwnedLauncherEvidenceSource(capture)


class FakeBackend:
    reviewed = True
    direct_gcloud = False
    uses_adc = False

    def __init__(self, *, fail: str | None = None):
        self.fail = fail
        self.calls: list[str] = []
        self.created = False

    def describe_prestate(self, request):
        self.calls.append("prestate")
        return _prestate(request)

    def create_instance(self, request):
        self.calls.append("create")
        if self.fail == "create":
            raise RuntimeError("create")
        if self.fail == "create_ambiguous":
            self.created = True
            raise RuntimeError("transport after create")
        self.created = True

    def describe_poststate(self, request):
        self.calls.append("poststate")
        if self.fail == "poststate":
            return {**_poststate(request), "external_ip": True}
        return _poststate(request)

    def delete_instance(self, request):
        self.calls.append("delete")
        if self.fail == "delete":
            raise RuntimeError("delete")
        self.created = False


def _write_approval(tmp_path: Path) -> Path:
    path = tmp_path / "approval.json"
    path.write_text(json.dumps(_approval(_definition())))
    return path


def _reviewed(backend, *, source=None):
    return cs.ReviewedConfidentialSpaceBackend(backend, launcher_source=source or _source())


def test_definition_is_closed_blocked_and_exactly_bound():
    result = cs.validate_definition(DEFINITION)
    assert result["status"] == "blocked_pending_fresh_live_bindings_and_child_approval"
    assert result["image_reference"] == cs.IMAGE_REFERENCE
    assert result["wip_provider"] == cs.WIP_PROVIDER
    assert result["token_audience"] == cs.TOKEN_AUDIENCE
    assert result["cloud_operations"] == []
    assert result["apply_performed"] is False


def test_definition_rejects_security_or_binding_drift(tmp_path):
    for field, value, message in (("image", {"reference": "tag", "digest": cs.IMAGE_DIGEST, "remote_digest_verified": True, "source_path": "x"}, "image binding"), ("target", {**_definition()["target"], "external_ip": True}, "target drift"), ("wip", {**_definition()["wip"], "token_audience": cs.WIP_PROVIDER}, "WIP binding"), ("container_closure", {**_definition()["container_closure"], "privileged": True}, "container closure")):
        value_doc = _definition()
        value_doc[field] = value
        value_doc["definition_digest"] = sha256({k: v for k, v in value_doc.items() if k != "definition_digest"})
        path = tmp_path / f"{field}.json"
        path.write_text(json.dumps(value_doc))
        with pytest.raises(cs.BootstrapError, match=message):
            cs.validate_definition(path)


def test_claim_path_values_and_rendered_metadata_are_exact(tmp_path):
    metadata = cs.render_metadata(DEFINITION)
    assert f"tee-image-reference={cs.IMAGE_REFERENCE}" in metadata
    assert "tee-env-P5R0_WIP_PROVIDER=" + cs.WIP_PROVIDER in metadata
    assert "tee-env-P5R0_ATTESTATION_AUDIENCE=https://sts.googleapis.com" in metadata
    assert "tee-env-P5R0_CLAIM_IMAGE_DIGEST=submods.container.image_digest" in metadata
    value = _definition()
    value["wip"]["claim_paths"]["image_digest"] = "image"
    value["definition_digest"] = sha256({k: v for k, v in value.items() if k != "definition_digest"})
    path = tmp_path / "claim-drift.json"
    path.write_text(json.dumps(value))
    with pytest.raises(cs.BootstrapError, match="claim-path"):
        cs.validate_definition(path)


def test_future_launch_command_is_hardened_and_carries_rendered_policy():
    argv = cs.future_launch_command(DEFINITION)
    assert "--shielded-secure-boot" in argv
    assert "--shielded-vtpm" in argv
    assert "--network-interface=network=default,subnet=default,no-address" in argv
    assert "--confidential-compute-type=SEV" in argv
    assert f"--service-account={cs.CAPABILITY_SERVICE_ACCOUNT}" in argv
    assert any(item.startswith("--metadata=^|^") and "rendered-p5-r0-confidential-space-evaluator.metadata" in item for item in argv)


def test_missing_external_approval_fails_before_backend_or_ledger(tmp_path):
    backend = FakeBackend()
    with pytest.raises(cs.BootstrapError, match="approval"):
        cs.execute_bootstrap(backend=_reviewed(backend), approval_path=tmp_path / "missing.json", definition_path=DEFINITION, ledger_path=tmp_path / "ledger.jsonl", iam_predecessor=_predecessor())
    assert backend.calls == []
    assert not (tmp_path / "ledger.jsonl").exists()


def test_success_is_ordered_one_shot_and_redacted(tmp_path):
    backend = FakeBackend()
    result = cs.execute_bootstrap(backend=_reviewed(backend), approval_path=_write_approval(tmp_path), definition_path=DEFINITION, ledger_path=tmp_path / "ledger.jsonl", iam_predecessor=_predecessor())
    assert result["status"] == "verified"
    assert result["receipt"]["launcher_evidence_digest"].startswith("sha256:")
    assert result["receipt"]["attestation_claimed"] is True
    assert backend.calls == ["prestate", "create", "poststate"]
    ledger = (tmp_path / "ledger.jsonl").read_text()
    assert "verified" in ledger
    assert "token" not in ledger.lower()
    assert "nonce" not in ledger.lower()


def test_forged_or_unbound_launcher_evidence_fails_closed_and_rolls_back(tmp_path):
    backend = FakeBackend()
    result = cs.execute_bootstrap(backend=_reviewed(backend, source=_source(mutate="image_digest")), approval_path=_write_approval(tmp_path), definition_path=DEFINITION, ledger_path=tmp_path / "ledger.jsonl", iam_predecessor=_predecessor())
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    assert backend.calls == ["prestate", "create", "poststate", "delete", "prestate"]


def test_post_create_evidence_failure_rolls_back_and_is_not_retryable(tmp_path):
    backend = FakeBackend()
    approval = _write_approval(tmp_path)
    ledger = tmp_path / "ledger.jsonl"
    result = cs.execute_bootstrap(backend=_reviewed(backend, source=_source(fail=True)), approval_path=approval, definition_path=DEFINITION, ledger_path=ledger, iam_predecessor=_predecessor())
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    with pytest.raises(cs.BootstrapError, match="retry is disabled"):
        cs.execute_bootstrap(backend=_reviewed(FakeBackend()), approval_path=approval, definition_path=DEFINITION, ledger_path=ledger, iam_predecessor=_predecessor())


def test_ambiguous_create_is_reobserved_and_rolled_back(tmp_path):
    backend = FakeBackend(fail="create_ambiguous")
    result = cs.execute_bootstrap(backend=_reviewed(backend), approval_path=_write_approval(tmp_path), definition_path=DEFINITION, ledger_path=tmp_path / "ledger.jsonl", iam_predecessor=_predecessor())
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    assert backend.calls == ["prestate", "create", "poststate", "delete", "prestate"]


def test_rollback_failure_is_manual_review_and_no_retry(tmp_path):
    backend = FakeBackend(fail="delete")
    result = cs.execute_bootstrap(backend=_reviewed(backend, source=_source(fail=True)), approval_path=_write_approval(tmp_path), definition_path=DEFINITION, ledger_path=tmp_path / "ledger.jsonl", iam_predecessor=_predecessor())
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rollback_failed_manual_review"


def test_approval_live_binding_digests_are_required_in_observations(tmp_path):
    backend = FakeBackend()
    original = backend.describe_prestate
    backend.describe_prestate = lambda request: {**original(request), "iam_poststate_digest": "sha256:" + "f" * 64}  # type: ignore[method-assign]
    result = cs.execute_bootstrap(backend=_reviewed(backend), approval_path=_write_approval(tmp_path), definition_path=DEFINITION, ledger_path=tmp_path / "ledger.jsonl", iam_predecessor=_predecessor())
    assert result["status"] == "failed_closed"
    assert backend.calls == ["prestate"]


def test_unreviewed_or_ambient_backend_is_rejected():
    backend = FakeBackend()
    backend.direct_gcloud = True
    with pytest.raises(cs.BootstrapError, match="direct gcloud"):
        cs.ReviewedConfidentialSpaceBackend(backend, launcher_source=_source())
    backend.direct_gcloud = False
    backend.uses_adc = True
    with pytest.raises(cs.BootstrapError, match="ambient ADC"):
        cs.ReviewedConfidentialSpaceBackend(backend, launcher_source=_source())


@pytest.mark.parametrize("field,value", [("external_ip", True), ("host_mounts", ["/host:/guest"]), ("privileged", True), ("seccomp", "unconfined"), ("filesystem", "rw"), ("runtime_digest", "sha256:" + "f" * 64), ("closure_digest", "sha256:" + "f" * 64)])
def test_poststate_rejects_container_or_network_escape(field, value):
    post = _poststate()
    post[field] = value
    with pytest.raises(cs.BootstrapError, match=f"(?:poststate|container closure) drift: {field}"):
        cs._validate_poststate(post, _request())



def test_alternate_ledger_path_cannot_retry_same_approval_attempt(tmp_path):
    approval = _write_approval(tmp_path)
    first = cs.execute_bootstrap(backend=_reviewed(FakeBackend()), approval_path=approval, definition_path=DEFINITION, ledger_path=tmp_path / "ledger-a.jsonl", iam_predecessor=_predecessor())
    assert first["status"] == "verified"
    second_backend = FakeBackend()
    with pytest.raises(cs.BootstrapError, match="retry is disabled"):
        cs.execute_bootstrap(backend=_reviewed(second_backend), approval_path=approval, definition_path=DEFINITION, ledger_path=tmp_path / "ledger-b.jsonl", iam_predecessor=_predecessor())
    assert second_backend.calls == []


def test_launcher_evidence_wrapper_cannot_be_constructed_by_callers():
    with pytest.raises(TypeError, match="only be issued"):
        cs.VerifierIssuedLauncherEvidence(object(), {})


def test_wip_binding_digest_mismatch_stops_before_create(tmp_path):
    backend = FakeBackend()
    original = backend.describe_prestate
    backend.describe_prestate = lambda request: {**original(request), "wip_poststate_digest": "sha256:" + "f" * 64}  # type: ignore[method-assign]
    result = cs.execute_bootstrap(backend=_reviewed(backend), approval_path=_write_approval(tmp_path), definition_path=DEFINITION, ledger_path=tmp_path / "ledger.jsonl", iam_predecessor=_predecessor())
    assert result["status"] == "failed_closed"
    assert backend.calls == ["prestate"]
