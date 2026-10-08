from __future__ import annotations

import ast
import copy
import dataclasses
import json
import os
import time
from pathlib import Path

import pytest

from evaluation.p0a.canonical import sha256
from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.credential_evidence import (
    VerifiedCredentialReadinessEvidence,
    _commitment,
    _register_credential_evidence,
    _EVIDENCE_SEAL,
)
from services.p5_r0_evaluator.deploy import iam_capability_provisioning as iam
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import InjectedSignedEnvironmentCredential
from services.p5_r0_evaluator.deploy import reviewed_iam_backend as boundary

ROOT = Path(__file__).resolve().parents[3]


def _prestate() -> dict:
    artifact = json.loads((ROOT / "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json").read_text())
    return iam.normalize_prestate(artifact["state"])


def _poststate() -> dict:
    value = _prestate()
    value["bucket_policy"] = {
        "etag": "after-bucket",
        "bindings": [
            item for item in value["bucket_policy"]["bindings"]
            if not ((item["member"] == f"serviceAccount:{iam.EXISTING_ACCOUNT}" and item["role"] == iam.BROAD_ROLE) or (item["member"] == iam.STALE_WIF_PRINCIPAL and item["role"] == iam.STALE_WIF_ROLE))
        ] + [{"member": f"serviceAccount:{iam.GCS_ONLY_ACCOUNT}", "role": iam.CUSTOM_ROLE, "condition": {"title": iam.EXACT_CONDITION_TITLE, "expression": iam.EXACT_CONDITION}}],
    }
    value["target_account"] = {"email": iam.GCS_ONLY_ACCOUNT, "exists": True, "has_key_material": False, "project_roles": []}
    value["target_account_policy"] = {"etag": "after-target", "bindings": [{"member": iam.WIF_PRINCIPAL, "role": iam.TOKEN_CREATOR, "condition": None}]}
    value["custom_role"] = {"name": iam.CUSTOM_ROLE, "exists": True, "etag": "after-role", "fingerprint": None, "title": iam.CUSTOM_ROLE_TITLE, "stage": iam.CUSTOM_ROLE_STAGE, "permissions": list(iam.CUSTOM_ROLE_PERMISSIONS)}
    return iam.normalize_prestate({key: item for key, item in value.items() if key != "state_digest"})


def _prerequisites():
    now = int(time.time())
    evidence_digest = digest("signed-environment-evidence")
    evidence_values = {
        "packet_digest": boundary.CHILD_PACKET_DIGEST,
        "signed_environment_evidence_digest": evidence_digest,
        "provider": iam.WIF_PROVIDER,
        "image_digest": iam.WIF_IMAGE_DIGEST,
        "audience": iam.STS_AUDIENCE,
        "principal": iam.WIF_PRINCIPAL,
        "target_resource": f"projects/{iam.PROJECT_ID}/serviceAccounts/{iam.GCS_ONLY_ACCOUNT}",
        "authority_binding_digest": boundary.AUTHORITY_BINDING_DIGEST,
        "service_account": iam.GCS_ONLY_ACCOUNT,
        "attestation_binding_digest": digest("attestation-binding"),
        "capability_binding_digest": digest("capability-binding"),
        "source_token_digest": digest("source-token"),
        "capability_token_digest": digest("capability-token"),
        "attestation_expires_at": now + 600,
        "source_expires_at": now + 500,
        "expires_at": now + 300,
    }
    evidence_values["seal_digest"] = _commitment(evidence_values)
    evidence = _register_credential_evidence(VerifiedCredentialReadinessEvidence(**evidence_values, _seal=_EVIDENCE_SEAL))
    credential = InjectedSignedEnvironmentCredential(
        evidence_digest=evidence_digest,
        target_service_account=iam.GCS_ONLY_ACCOUNT,
        expires_at=now + 300,
        packet_digest=boundary.CHILD_PACKET_DIGEST,
        provider=iam.WIF_PROVIDER,
        image_digest=iam.WIF_IMAGE_DIGEST,
        audience=iam.STS_AUDIENCE,
        authority_binding_digest=boundary.AUTHORITY_BINDING_DIGEST,
        principal=iam.WIF_PRINCIPAL,
        target_resource=f"projects/{iam.PROJECT_ID}/serviceAccounts/{iam.GCS_ONLY_ACCOUNT}",
        attestation_digest=digest("attestation"),
        attestation_signature="attestation-signature",
        attestation_claims={"aud": iam.STS_AUDIENCE, "submods.container.image_digest": iam.WIF_IMAGE_DIGEST},
    )
    approval = boundary._issue_verified_iam_child_approval(
        packet_digest=boundary.CHILD_PACKET_DIGEST,
        attempt_id=boundary.ATTEMPT_ID,
        prestate_digest=_prestate()["state_digest"],
        credential_evidence_digest=evidence_digest,
        authority_binding_digest=boundary.AUTHORITY_BINDING_DIGEST,
        issued_at=now - 1,
        expires_at=now + 300,
    )
    verifier = boundary._issue_verified_signature_verifier()
    return {"credential": credential, "credential_evidence": evidence, "child_approval": approval, "signature_verifier": verifier}


class FakeCredentialBackend:
    reviewed = True
    uses_adc = False
    direct_gcloud = False


def _executor(backend, **kwargs):
    return boundary.ReviewedFixedCommandExecutor(backend=backend, **_prerequisites(), **kwargs)


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def run(self, argv):
        self.calls.append(tuple(argv))
        value = self.responses.get(tuple(argv), {"ok": True})
        if isinstance(value, boundary.CommandResult):
            return value
        return boundary.CommandResult(0, json.dumps(value), "")


class TransactionBackend:
    reviewed = True
    uses_adc = False
    direct_gcloud = False

    def __init__(self, *, poststate=None, fail_at=None, rollback_fail=False):
        self.pre = _prestate()
        self.post = poststate or _poststate()
        self.fail_at = fail_at
        self.rollback_fail = rollback_fail
        self.calls = []
        self.expected = None

    def bind_expected_prestate(self, expected):
        self.expected = copy.deepcopy(expected)

    def validate_credential_binding(self, expected):
        self.credential_binding = dict(expected)

    def _call(self, name):
        self.calls.append(name)
        if self.fail_at == name:
            raise RuntimeError(name)

    def describe_prestate(self):
        self._call("describe_prestate")
        return copy.deepcopy(self.pre)

    def ensure_service_account(self, email):
        self._call("ensure_service_account")

    def apply_custom_role(self, request=None):
        self._call("apply_custom_role")

    def update_bucket_policy(self, request=None):
        self._call("update_bucket_policy")

    def update_target_account_policy(self, request=None):
        self._call("update_target_account_policy")

    def describe_poststate(self):
        self._call("describe_poststate")
        if self.fail_at == "poststate_drift":
            return copy.deepcopy(self.pre)
        return copy.deepcopy(self.post)

    def restore_target_account_policy(self, request=None):
        self._call("restore_target_account_policy")
        if self.rollback_fail:
            raise RuntimeError("rollback target")

    def restore_bucket_policy(self, request=None):
        self._call("restore_bucket_policy")
        if self.rollback_fail:
            raise RuntimeError("rollback bucket")

    def restore_custom_role(self, request=None):
        self._call("restore_custom_role")
        if self.rollback_fail:
            raise RuntimeError("rollback role")


def _minimal_role_response():
    return {"etag": "role-before", "title": iam.CUSTOM_ROLE_TITLE, "stage": iam.CUSTOM_ROLE_STAGE, "includedPermissions": list(iam.CUSTOM_ROLE_PERMISSIONS)}


def test_every_production_command_is_absolute_fixed_and_shell_free():
    tree = ast.parse((ROOT / "services/p5_r0_evaluator/deploy/reviewed_iam_backend.py").read_text())
    assert not any(isinstance(node, ast.Call) and any(keyword.arg == "shell" and getattr(keyword.value, "value", None) is True for keyword in node.keywords) for node in ast.walk(tree))
    assert boundary.GCLOUD == "/home/matt/google-cloud-sdk/bin/gcloud"
    assert all(argv[0] == boundary.GCLOUD for argv in boundary.ALLOWLIST.values())
    assert all("sh" not in argv and "bash" not in argv for argv in boundary.ALLOWLIST.values())
    assert all("--format=json" in argv or "--quiet" in argv for argv in boundary.ALLOWLIST.values())
    with pytest.raises(boundary.ReviewedIAMError, match="allowlist"):
        boundary.SubprocessGcloudRunner().run([boundary.GCLOUD, "iam", "roles", "delete", "arbitrary-role"])


def test_optional_reads_require_explicit_not_found():
    runner = FakeRunner({boundary.allowlisted_argv("target_describe"): boundary.CommandResult(1, "", "PERMISSION_DENIED")})
    backend = boundary.FixedCommandIAMBackend(runner=runner)
    with pytest.raises(boundary.ReviewedIAMError, match="fixed gcloud operation failed"):
        backend._run("target_describe", optional=True)


def test_command_allowlist_cannot_be_mutated():
    with pytest.raises(TypeError):
        boundary.ALLOWLIST["arbitrary"] = (boundary.GCLOUD, "arbitrary")


def test_existing_target_policy_version_drift_stops_before_binding():
    expected = _prestate()
    expected["target_account"] = {"email": iam.GCS_ONLY_ACCOUNT, "exists": True, "has_key_material": False, "project_roles": []}
    expected["target_account_policy"] = {"etag": "approved-etag", "bindings": []}
    expected = iam.normalize_prestate({key: value for key, value in expected.items() if key != "state_digest"})
    current = copy.deepcopy(expected)
    current["target_account_policy"]["etag"] = "drifted-etag"
    current = iam.normalize_prestate({key: value for key, value in current.items() if key != "state_digest"})
    backend = boundary.FixedCommandIAMBackend(runner=FakeRunner({}))
    backend.bind_expected_prestate(expected)
    backend._current = lambda: current
    with pytest.raises(boundary.ReviewedIAMError, match="etag/fingerprint drift"):
        backend.update_target_account_policy()


def test_rest_backend_replaced_by_fixed_command_backend_without_adc_or_export():
    assert not hasattr(boundary, "GoogleIamRestBackend")
    runner = boundary.SubprocessGcloudRunner()
    assert runner.uses_adc is False
    assert runner.exports_credentials is False
    assert runner.creates_keys is False


def test_fixed_backend_reads_closed_state_and_checks_exact_versions():
    responses = {
        boundary.allowlisted_argv("project_describe"): {"projectId": iam.PROJECT_ID, "projectNumber": iam.PROJECT_NUMBER},
        boundary.allowlisted_argv("bucket_describe"): {"project": iam.PROJECT_ID, "iamConfiguration": {"uniformBucketLevelAccess": {"enabled": True}, "publicAccessPrevention": "inherited"}},
        boundary.allowlisted_argv("project_policy"): {"etag": "project", "bindings": [{"role": "roles/cloudkms.signerVerifier", "members": [f"serviceAccount:{iam.EXISTING_ACCOUNT}"]}]},
        boundary.allowlisted_argv("bucket_policy"): {"etag": "CEg=", "bindings": []},
        boundary.allowlisted_argv("existing_describe"): {"email": iam.EXISTING_ACCOUNT},
        boundary.allowlisted_argv("existing_keys"): [],
        boundary.allowlisted_argv("existing_policy"): {"etag": "BwZbrD_Tby0=", "bindings": []},
        boundary.allowlisted_argv("target_describe"): boundary.CommandResult(1, "", "NOT_FOUND"),
        boundary.allowlisted_argv("role_describe"): boundary.CommandResult(1, "", "NOT_FOUND"),
    }
    runner = FakeRunner(responses)
    backend = boundary.FixedCommandIAMBackend(runner=runner)
    observed = backend.describe_prestate()
    assert observed["bucket_policy"]["etag"] == "CEg="
    assert observed["existing_account_policy"]["etag"] == "BwZbrD_Tby0="
    assert observed["target_account"]["exists"] is False
    assert set(runner.calls) == set(responses)


def test_precondition_drift_stops_before_mutation(tmp_path):
    backend = TransactionBackend()
    drifted = copy.deepcopy(backend.pre)
    drifted["bucket_policy"]["etag"] = "drifted"
    drifted = iam.normalize_prestate({key: value for key, value in drifted.items() if key != "state_digest"})
    with pytest.raises(iam.IAMProvisioningError, match="fresh IAM prestate drift"):
        iam.validate_prestate(drifted, _prestate())
    assert backend.calls == []


def test_executor_precondition_drift_records_no_mutation(tmp_path):
    class DriftBackend(TransactionBackend):
        def describe_prestate(self):
            self._call("describe_prestate")
            drifted = copy.deepcopy(self.pre)
            drifted["bucket_policy"]["etag"] = "drifted"
            return iam.normalize_prestate({key: value for key, value in drifted.items() if key != "state_digest"})

    backend = DriftBackend()
    result = _executor(backend).apply(ledger_path=tmp_path / "drift.jsonl")
    assert result["status"] == "failed_closed"
    assert result["mutations_performed"] is False
    assert backend.calls == ["describe_prestate"]


def test_exact_poststate_rejects_unreviewed_bucket_binding():
    post = _poststate()
    post["bucket_policy"]["bindings"].append({"member": "serviceAccount:unreviewed@example.com", "role": "roles/storage.objectViewer", "condition": None})
    post = iam.normalize_prestate({key: value for key, value in post.items() if key != "state_digest"})
    with pytest.raises(boundary.ReviewedIAMError, match="bucket policy is not exact"):
        boundary._exact_poststate(post, _prestate())
def test_success_has_exact_receipt_and_no_downstream(tmp_path):
    backend = TransactionBackend()
    result = _executor(backend).apply(ledger_path=tmp_path / "iam.jsonl")
    assert result["status"] == "verified"
    assert result["receipt"]["private"] is True
    assert result["receipt"]["service_account"] == iam.GCS_ONLY_ACCOUNT
    assert result["later_operations_enabled"] is False
    assert backend.calls == ["describe_prestate", "ensure_service_account", "apply_custom_role", "update_bucket_policy", "update_target_account_policy", "describe_poststate"]


def test_poststate_failure_rolls_back_in_reviewed_order(tmp_path):
    backend = TransactionBackend(fail_at="poststate_drift")
    ledger = tmp_path / "iam.jsonl"
    result = _executor(backend).apply(ledger_path=ledger)
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rolled_back_verified"
    assert backend.calls[-4:] == ["restore_target_account_policy", "restore_bucket_policy", "restore_custom_role", "describe_poststate"]
    records = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert records[-1]["rollback_receipt"]["verified"] is True
    assert records[-1]["later_operations_enabled"] is False
def test_rollback_failure_requires_manual_review(tmp_path):
    backend = TransactionBackend(fail_at="poststate_drift", rollback_fail=True)
    result = _executor(backend).apply(ledger_path=tmp_path / "iam.jsonl")
    assert result["status"] == "failed_closed"
    assert result["rollback_status"] == "rollback_failed_manual_review"
    assert result["manual_review_required"] is True


def test_failure_before_first_mutation_is_conservative_and_reobserves(tmp_path):
    backend = TransactionBackend(fail_at="ensure_service_account")
    result = _executor(backend).apply(ledger_path=tmp_path / "before-mutation.jsonl")
    # The call was attempted, so mutation state is not reported as safely
    # absent.  The fresh reobserve proves the fake backend remained at prestate,
    # allowing rollback to be skipped without claiming a clean call boundary.
    assert result["mutations_performed"] is True
    # The fake backend reports a changed poststate after the call failed; the
    # boundary therefore keeps the attempt in manual review rather than
    # claiming that no mutation occurred.
    assert result["rollback_status"] == "rollback_failed_manual_review"
    assert result["manual_review_required"] is True
    assert "restore_target_account_policy" in backend.calls


def test_fixed_backend_rollback_refuses_versioned_bucket_drift():
    expected = _prestate()
    current = copy.deepcopy(expected)
    current["bucket_policy"]["etag"] = "concurrent-etag"
    current = iam.normalize_prestate({key: value for key, value in current.items() if key != "state_digest"})
    backend = boundary.FixedCommandIAMBackend(runner=FakeRunner({}))
    backend.bind_expected_prestate(expected)
    backend._current = lambda: current
    with pytest.raises(boundary.ReviewedIAMError, match="version/state drift"):
        backend.restore_bucket_policy()


def test_one_attempt_ledger_rejects_retry(tmp_path):
    ledger = tmp_path / "iam.jsonl"
    _executor(TransactionBackend()).apply(ledger_path=ledger)
    with pytest.raises(boundary.ReviewedIAMError, match="retry is disabled"):
        _executor(TransactionBackend()).apply(ledger_path=ledger)


def test_raw_and_normalized_prestate_digests_are_distinct_and_bound():
    artifact = json.loads((ROOT / "var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json").read_text())
    assert artifact["artifact_digest"] == sha256({key: value for key, value in artifact.items() if key != "artifact_digest"})
    raw = artifact["state"]
    assert raw["state_digest"] == sha256({key: value for key, value in raw.items() if key != "state_digest"})
    normalized = iam.normalize_prestate(raw)
    assert normalized["state_digest"] == boundary.PRESTATE_NORMALIZED_DIGEST
    assert normalized["state_digest"] != raw["state_digest"]


def test_packet_digest_is_immutable_not_caller_recomputed(tmp_path):
    packet = json.loads(boundary.DEFAULT_PACKET.read_text())
    packet["attempt_id"] = "dispatch082-iam-forged"
    packet["artifact_digest"] = sha256({key: value for key, value in packet.items() if key != "artifact_digest"})
    path = tmp_path / "forged-packet.json"
    path.write_text(json.dumps(packet))
    with pytest.raises(boundary.ReviewedIAMError, match="reviewed APPROVAL-023 packet"):
        boundary._load_packet(path)


def test_no_credential_export_or_key_creation_is_representable():
    packet = boundary._load_packet()
    assert packet["apply_contract"]["credential_export"] is False
    assert packet["apply_contract"]["service_account_keys"] is False
    assert packet["later_operations_enabled"] is False
    source = (ROOT / "services/p5_r0_evaluator/deploy/reviewed_iam_backend.py").read_text()
    assert "os.environ.copy" not in source
    assert 'env = {"PATH": "/usr/bin:/bin"' in source
    assert "credential" in source
    assert "create-key" not in source



def test_apply_requires_verifier_owned_prerequisites_before_ledger(tmp_path):
    backend = TransactionBackend()
    with pytest.raises(boundary.ReviewedIAMError, match="signed-environment credential object"):
        boundary.ReviewedFixedCommandExecutor(backend=backend).apply(ledger_path=tmp_path / "blocked.jsonl")
    assert not (tmp_path / "blocked.jsonl").exists()
    assert backend.calls == []


def test_unsigned_or_self_digested_child_approval_is_rejected(tmp_path):
    prerequisites = _prerequisites()
    forged = prerequisites["child_approval"].as_public_dict()
    forged["approval_digest"] = digest({key: value for key, value in forged.items() if key != "approval_digest"})
    with pytest.raises(boundary.ReviewedIAMError, match="verifier-issued"):
        boundary.ReviewedFixedCommandExecutor(
            backend=TransactionBackend(),
            credential=prerequisites["credential"],
            credential_evidence=prerequisites["credential_evidence"],
            child_approval=forged,  # type: ignore[arg-type]
            signature_verifier=prerequisites["signature_verifier"],
        ).apply(ledger_path=tmp_path / "forged.jsonl")


def test_child_approval_binds_attempt_prestate_evidence_and_authority(tmp_path):
    prerequisites = _prerequisites()
    wrong = boundary._issue_verified_iam_child_approval(
        packet_digest=boundary.CHILD_PACKET_DIGEST,
        attempt_id=boundary.ATTEMPT_ID,
        prestate_digest=digest("wrong-prestate"),
        credential_evidence_digest=prerequisites["credential_evidence"].signed_environment_evidence_digest,
        authority_binding_digest=boundary.AUTHORITY_BINDING_DIGEST,
        issued_at=int(time.time()) - 1,
        expires_at=int(time.time()) + 300,
    )
    with pytest.raises(boundary.ReviewedIAMError, match="prestate binding"):
        boundary.ReviewedFixedCommandExecutor(
            backend=TransactionBackend(),
            credential=prerequisites["credential"],
            credential_evidence=prerequisites["credential_evidence"],
            child_approval=wrong,
            signature_verifier=prerequisites["signature_verifier"],
        ).apply(ledger_path=tmp_path / "wrong-binding.jsonl")


def test_direct_runner_rejects_ambient_or_missing_credential():
    runner = boundary.SubprocessGcloudRunner()
    with pytest.raises(boundary.ReviewedIAMError, match="signed-environment credential"):
        runner.run(boundary.allowlisted_argv("project_describe"))


def test_rollback_receipt_records_fresh_observations_not_old_restoration_claim(tmp_path):
    backend = TransactionBackend(fail_at="poststate_drift")
    ledger = tmp_path / "rollback.jsonl"
    result = _executor(backend).apply(ledger_path=ledger)
    receipt = json.loads(ledger.read_text().splitlines()[-1])["rollback_receipt"]
    assert result["rollback_status"] == "rolled_back_verified"
    assert receipt["schema"] == "P5R0APPROVAL023IAMRollbackReceiptV2"
    assert receipt["restored_state_digest"] is not None
    assert set(receipt["restored_resource_digests"]) == {"target_account", "bucket_policy", "custom_role"}
    assert "restored_versions" in receipt
    assert "restored_digest" not in receipt


def test_cli_apply_is_blocked_without_exporting_verifier_objects(tmp_path, capsys):
    assert boundary._cli(["apply", "--ledger", str(tmp_path / "cli.jsonl")]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "blocked_missing_verifier_prerequisites"
    assert output["applied_state"] is False
    assert not (tmp_path / "cli.jsonl").exists()



def test_explicit_transport_reaches_fixed_subprocess_without_ambient_state(monkeypatch):
    prerequisites = _prerequisites()
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"verifier-owned-short-lived-token")
    transport = boundary.issue_verifier_credential_transport(
        evidence_digest=prerequisites["credential"].evidence_digest,
        target_service_account=iam.GCS_ONLY_ACCOUNT,
        expires_at=prerequisites["credential"].expires_at,
        token_fd=read_fd,
        packet_digest=prerequisites["credential"].packet_digest,
    )
    credential = dataclasses.replace(prerequisites["credential"], transport=transport)
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return boundary.CommandResult(0, "{}", "")

    monkeypatch.setattr(boundary.subprocess, "run", fake_run)
    try:
        result = boundary.SubprocessGcloudRunner().run(boundary.allowlisted_argv("project_describe"), credential=credential)
    finally:
        os.close(read_fd)
        os.close(write_fd)
    assert result.returncode == 0
    assert captured["kwargs"]["env"] == {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
    assert captured["kwargs"]["pass_fds"] == (read_fd,)
    assert any(item == f"--access-token-file=/proc/self/fd/{read_fd}" for item in captured["argv"])
    assert all("verifier-owned-short-lived-token" not in str(value) for value in captured.values())


def test_transport_mismatch_is_rejected_before_subprocess(monkeypatch):
    prerequisites = _prerequisites()
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"mismatch-token")
    transport = boundary.issue_verifier_credential_transport(
        evidence_digest=digest("wrong-evidence"),
        target_service_account=iam.GCS_ONLY_ACCOUNT,
        expires_at=prerequisites["credential"].expires_at,
        token_fd=read_fd,
        packet_digest=prerequisites["credential"].packet_digest,
    )
    credential = dataclasses.replace(prerequisites["credential"], transport=transport)
    monkeypatch.setattr(boundary.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("subprocess must not run"))
    try:
        with pytest.raises(boundary.ReviewedIAMError, match="transport binding mismatch"):
            boundary.SubprocessGcloudRunner().run(boundary.allowlisted_argv("project_describe"), credential=credential)
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_signed_approval_rejects_forged_signature_even_with_recomputed_digest(tmp_path):
    prerequisites = _prerequisites()
    forged = boundary._issue_verified_iam_child_approval(
        packet_digest=boundary.CHILD_PACKET_DIGEST,
        attempt_id=boundary.ATTEMPT_ID,
        prestate_digest=_prestate()["state_digest"],
        credential_evidence_digest=prerequisites["credential_evidence"].signed_environment_evidence_digest,
        authority_binding_digest=boundary.AUTHORITY_BINDING_DIGEST,
        issued_at=int(time.time()) - 1,
        expires_at=int(time.time()) + 300,
        signature="not-a-verifier-signature",
    )
    with pytest.raises(boundary.ReviewedIAMError, match="signature verification failed"):
        prerequisites["child_approval"] = forged
        boundary.ReviewedFixedCommandExecutor(backend=TransactionBackend(), **prerequisites).apply(ledger_path=tmp_path / "forged-signature.jsonl")


def test_effectful_exception_with_unobservable_remote_state_requires_manual_review(tmp_path):
    class UnknownBackend(TransactionBackend):
        def describe_poststate(self):
            self._call("describe_poststate")
            raise RuntimeError("remote state unavailable")

    result = _executor(UnknownBackend(fail_at="ensure_service_account")).apply(ledger_path=tmp_path / "unknown.jsonl")
    assert result["status"] == "failed_closed"
    assert result["manual_review_required"] is True
    assert result["rollback_status"] == "rollback_failed_manual_review"
    assert result["later_operations_enabled"] is False
