import pytest

from services.p5_r0_evaluator.canonical import digest

from services.p5_r0_evaluator.deploy.iam_predecessor import (
    IAMPredecessorError,
    issue_verified_iam_predecessor,
    validate_verified_iam_predecessor,
)


def _result(**overrides):
    value = {
        "status": "verified",
        "operation_id": "provision_gcs_only_iam_boundary",
        "attempt_id": "dispatch082-iam-20260920-a7f4c2d9",
        "poststate_digest": "sha256:" + "a" * 64,
        "ledger_head_digest": "sha256:" + "b" * 64,
        "mutations_performed": True,
        "later_operations_enabled": False,
        "receipt": {
            "schema": "P5R0APPROVAL023IAMReceiptV1",
            "operation_id": "provision_gcs_only_iam_boundary",
            "prestate_digest": "sha256:" + "d" * 64,
            "service_account": "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com",
            "custom_role": "projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1",
            "wif_principal": "principalSet://test",
            "condition_expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/p5-r0/operation-4/rs069r18r13-op4-04a98e3e/')",
            "credentials_exported": False,
            "keys_created": False,
        },
    }
    value.update(overrides)
    value["receipt"]["receipt_digest"] = digest({key: item for key, item in value["receipt"].items() if key != "receipt_digest"})
    return value


def test_only_verified_success_result_can_issue_predecessor():
    predecessor = issue_verified_iam_predecessor(result=_result(), evidence_digest="sha256:" + "e" * 64)
    assert validate_verified_iam_predecessor(predecessor, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9") is predecessor
    assert predecessor.receipt_digest == _result()["receipt"]["receipt_digest"]
    assert predecessor.ledger_head_digest == "sha256:" + "b" * 64


@pytest.mark.parametrize("value", [None, {}, {"status": "verified", "receipt_digest": "sha256:" + "c" * 64}, "sha256:" + "c" * 64])
def test_plain_or_declarative_values_cannot_satisfy_predecessor_gate(value):
    with pytest.raises(IAMPredecessorError):
        validate_verified_iam_predecessor(value, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9")


def test_failed_or_unknown_iam_result_cannot_issue_predecessor():
    with pytest.raises(IAMPredecessorError):
        issue_verified_iam_predecessor(result=_result(status="failed_closed", mutations_performed=True), evidence_digest="sha256:" + "e" * 64)
    with pytest.raises(IAMPredecessorError):
        issue_verified_iam_predecessor(result=_result(status="failed_closed", mutations_performed=True, rollback_status="rollback_failed_manual_review"), evidence_digest="sha256:" + "e" * 64)


def test_copied_or_mutated_predecessor_is_rejected():
    predecessor = issue_verified_iam_predecessor(result=_result(), evidence_digest="sha256:" + "e" * 64)
    copied = predecessor.as_public_dict()
    with pytest.raises(IAMPredecessorError):
        validate_verified_iam_predecessor(copied, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9")
    object.__setattr__(predecessor, "receipt_digest", "sha256:" + "f" * 64)
    with pytest.raises(IAMPredecessorError):
        validate_verified_iam_predecessor(predecessor, operation_id="provision_gcs_only_iam_boundary", attempt_id="dispatch082-iam-20260920-a7f4c2d9")
