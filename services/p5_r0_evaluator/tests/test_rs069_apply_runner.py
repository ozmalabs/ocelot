from __future__ import annotations

from pathlib import Path
import socket

import pytest

import services.p5_r0_evaluator.deploy.rs069_apply_runner as runner

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.rs069_apply_runner import (
    DEFAULT_APPROVAL_REQUEST,
    RS069ApplyBlocked,
    _DEFAULT_APPROVAL_ID,
    _RUNSHEET_APPROVAL,
    _load_approval_request,
    _load_candidate_binding,
    _validate_remote_evidence_claim,
    _write_verified_binding,
    apply,
)

ROOT = Path(__file__).resolve().parents[3]
RUNSHEET = ROOT / "docs/research/engine_substrate/P5_MASTER_RUNSHEET.md"
CANDIDATE = ROOT / "var/p5-r0-rs069r1/candidate-image-binding.json"


def _digest(value):
    return sha256(canonical_bytes(value))


def _remote_evidence(*, schema, source_kind, image_digest, request_digest, resource):
    argv = [source_kind, resource, image_digest]
    record = {
        "operation_id": "bind_candidate_image_digest",
        "request_digest": request_digest,
        "image_digest": image_digest,
        "observed_digest": image_digest,
        "source": {"kind": source_kind, "resource": resource},
        "command": {"name": source_kind, "argv": argv, "digest": _digest(argv)},
        "verification_timestamp": "2026-09-19T12:34:56Z",
        "record_digest": None,
    }
    record["record_digest"] = _digest({key: value for key, value in record.items() if key != "record_digest"})
    evidence = {"schema": schema, "evidence_digest": None, "record": record}
    evidence["evidence_digest"] = _digest({"schema": schema, "record": record})
    return evidence


def test_corrected_candidate_binding_preserves_r14_digest_and_separates_evidence():
    binding = _load_candidate_binding(CANDIDATE, ROOT)
    raw = parse_canonical(CANDIDATE.read_bytes())
    target = raw["candidate"]["target_artifact_registry"]
    interpretation = raw["evidence_interpretation"]

    assert binding["image_digest"] == "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c"
    assert binding["registry_digest_verified"] is True
    assert binding["push_performed"] is True
    assert binding["production_promotable"] is False
    assert binding["remote_provenance_verified"] is None
    assert binding["immutable_verified"] is None
    assert target["remote_digest"] == binding["image_digest"]
    assert interpretation["local_provenance_verified"] is True
    assert interpretation["remote_digest_verified"] is True
    assert interpretation["remote_provenance_verified"] is None
    assert interpretation["immutable_verified"] is None


def test_verified_projection_keeps_local_and_remote_digest_evidence_separate(tmp_path):
    binding = parse_canonical(CANDIDATE.read_bytes())
    digest = binding["candidate"]["image_digest"]
    verification = {
        "remote_digest": digest,
        "remote_digest_verified": True,
        "remote_digest_evidence": {"method": "artifact_registry_digest_describe", "observed_digest": digest},
        "provenance_digest": binding["build"]["provenance_digest"],
        "local_provenance_verified": True,
        "remote_provenance_verified": None,
        "remote_provenance_evidence": None,
        "immutable_verified": None,
        "immutability_evidence": None,
    }
    output = tmp_path / "candidate-image-binding.json"
    _write_verified_binding(output, binding, verification)
    projected = parse_canonical(output.read_bytes())
    assert projected["evidence_interpretation"]["local_provenance_verified"] is True
    assert projected["evidence_interpretation"]["remote_digest_verified"] is True
    assert projected["candidate"]["target_artifact_registry"]["remote_provenance_verified"] is None
    assert projected["candidate"]["target_artifact_registry"]["immutable_verified"] is None


def test_r6_request_is_stale_against_corrected_r14_binding_and_fails_closed():
    request = parse_canonical(DEFAULT_APPROVAL_REQUEST.read_bytes())
    candidate = _load_candidate_binding(CANDIDATE, ROOT)
    assert request["status"] == "approved_pending_operation_1"
    assert request["approval"]["approval_id"] == _DEFAULT_APPROVAL_ID
    assert request["approval"]["required_text"] == _RUNSHEET_APPROVAL
    assert request["approval"]["scope"] == ["bind_candidate_image_digest"]
    assert request["workflow"]["execute_operation_1"] is True
    assert request["workflow"]["later_operations_enabled"] is False
    assert request["workflow"]["mutations_performed"] is False
    assert request["bound_candidate"]["binding_digest"] != candidate["binding_digest"]
    assert request["target"]["repository"] == "p5-cs"


def test_stale_approval_cannot_authorize_corrected_binding():
    candidate = _load_candidate_binding(CANDIDATE, ROOT)
    with pytest.raises(RS069ApplyBlocked, match="candidate binding digest drift"):
        _load_approval_request(
            DEFAULT_APPROVAL_REQUEST,
            candidate_info=candidate,
            approval_id=_DEFAULT_APPROVAL_ID,
            runsheet_text=RUNSHEET.read_text(),
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda request: request["approval"].update(required_text="wrong literal"), "literal"),
        (lambda request: request["approval"].update(approval_id="P5-MASTER-001/APPROVAL-001"), "approval id"),
        (lambda request: request["bound_candidate"].update(binding_digest="sha256:" + "0" * 64), "candidate binding digest"),
        (lambda request: request["approval"].update(scope=["bind_candidate_image_digest", "correct_wip_provider_claim_mapping"]), "scope"),
        (lambda request: request["workflow"].update(later_operations_enabled=True), "flags or mutation"),
        (lambda request: request["approval"].update(user_approved=False), "flags are inconsistent"),
    ],
)
def test_adversarial_approval_boundary_mismatches_fail_closed(tmp_path, change, message):
    # Reapply the mutation to a fresh copy so each case stays isolated and canonical.
    mutated = parse_canonical(DEFAULT_APPROVAL_REQUEST.read_bytes())
    candidate = _load_candidate_binding(CANDIDATE, ROOT)
    mutated["bound_candidate"].update(
        binding_digest=candidate["binding_digest"],
        candidate_image_digest=candidate["image_digest"],
        closure_digest=candidate["closure_digest"],
        push_performed=True,
        registry_digest_verified=True,
        production_promotable=False,
    )
    change(mutated)
    path = tmp_path / "approval-request.json"
    path.write_bytes(canonical_bytes(mutated))

    with pytest.raises(RS069ApplyBlocked, match=message):
        _load_approval_request(
            path,
            candidate_info=candidate,
            approval_id=_DEFAULT_APPROVAL_ID,
            runsheet_text=RUNSHEET.read_text(),
        )


def test_affirmative_runsheet_literal_cannot_override_pending_request(tmp_path):
    request = parse_canonical(DEFAULT_APPROVAL_REQUEST.read_bytes())
    request["approval"].update(approved=False, master_approved=False, user_approved=False)
    request["workflow"]["execute_operation_1"] = False
    request["status"] = "blocked_pending_new_master_approval"
    path = tmp_path / "approval-request.json"
    path.write_bytes(canonical_bytes(request))
    candidate = _load_candidate_binding(CANDIDATE, ROOT)

    with pytest.raises(RS069ApplyBlocked, match="affirmative runsheet"):
        _load_approval_request(
            path,
            candidate_info=candidate,
            approval_id=_DEFAULT_APPROVAL_ID,
            runsheet_text=RUNSHEET.read_text() + "\n" + _RUNSHEET_APPROVAL + "\n",
        )


def test_remote_provenance_claim_without_lookup_evidence_is_rejected(tmp_path):
    value = parse_canonical(CANDIDATE.read_bytes())
    value["artifact"]["path"] = "candidate-image-binding.json"
    target = value["candidate"]["target_artifact_registry"]
    target["remote_provenance_verified"] = True
    target.pop("remote_provenance_evidence", None)
    value["evidence_interpretation"]["remote_provenance_verified"] = True
    value["evidence_interpretation"]["remote_provenance_evidence"] = None
    path = tmp_path / "candidate-image-binding.json"
    path.write_bytes(canonical_bytes(value))

    with pytest.raises(RS069ApplyBlocked, match="remote provenance positive claim rejected: no authenticated runner-owned source"):
        _load_candidate_binding(path, tmp_path)


def test_immutability_claim_without_observation_is_rejected(tmp_path):
    value = parse_canonical(CANDIDATE.read_bytes())
    value["artifact"]["path"] = "candidate-image-binding.json"
    value["candidate"]["target_artifact_registry"]["immutable_verified"] = True
    value["evidence_interpretation"]["immutable_verified"] = True
    path = tmp_path / "candidate-image-binding.json"
    path.write_bytes(canonical_bytes(value))

    with pytest.raises(RS069ApplyBlocked, match="remote immutability positive claim rejected: no authenticated runner-owned source"):
        _load_candidate_binding(path, tmp_path)


def test_fabricated_positive_remote_provenance_shape_is_rejected():
    image_digest = "sha256:" + "1" * 64
    target = {
        "reference": "us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator@" + image_digest,
        "remote_provenance_verified": True,
        "remote_provenance_evidence": {
            "evidence_digest": "sha256:" + "2" * 64,
            "image_digest": image_digest,
            "lookup": "fabricated-attestation-lookup",
        },
    }
    with pytest.raises(RS069ApplyBlocked, match="remote provenance positive claim rejected: no authenticated runner-owned source"):
        _validate_remote_evidence_claim(target, image_digest, expected_operation_id="bind_candidate_image_digest", expected_request_digest="sha256:" + "3" * 64)


def test_fabricated_positive_remote_immutability_shape_is_rejected():
    image_digest = "sha256:" + "1" * 64
    target = {
        "reference": "us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator@" + image_digest,
        "immutable_verified": True,
        "immutability_evidence": {"method": "independent-policy-observation", "observed_digest": image_digest},
    }
    with pytest.raises(RS069ApplyBlocked, match="remote immutability positive claim rejected: no authenticated runner-owned source"):
        _validate_remote_evidence_claim(target, image_digest, expected_operation_id="bind_candidate_image_digest", expected_request_digest="sha256:" + "3" * 64)


@pytest.mark.parametrize("mismatch", ["observed_digest", "command", "request_digest"])
def test_remote_positive_evidence_mismatches_fail_closed(mismatch):
    image_digest = "sha256:" + "1" * 64
    request_digest = "sha256:" + "3" * 64
    resource = "us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator@" + image_digest
    evidence = _remote_evidence(
        schema="P5R0RS069RemoteProvenanceEvidenceV1",
        source_kind="artifact_registry_provenance_lookup",
        image_digest=image_digest,
        request_digest=request_digest,
        resource=resource,
    )
    if mismatch == "observed_digest":
        evidence["record"]["observed_digest"] = "sha256:" + "4" * 64
    elif mismatch == "command":
        evidence["record"]["command"]["argv"][1] = "wrong-resource"
    else:
        evidence["record"]["request_digest"] = "sha256:" + "4" * 64

    target = {
        "reference": resource,
        "remote_provenance_verified": True,
        "remote_provenance_evidence": evidence,
    }
    with pytest.raises(RS069ApplyBlocked, match="remote provenance positive claim rejected: no authenticated runner-owned source"):
        _validate_remote_evidence_claim(
            target,
            image_digest,
            expected_operation_id="bind_candidate_image_digest",
            expected_request_digest=request_digest,
        )


def test_valid_digest_bound_remote_provenance_evidence_is_rejected_without_runner_source():
    image_digest = "sha256:" + "1" * 64
    request_digest = "sha256:" + "3" * 64
    resource = "us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator@" + image_digest
    evidence = _remote_evidence(
        schema="P5R0RS069RemoteProvenanceEvidenceV1",
        source_kind="artifact_registry_provenance_lookup",
        image_digest=image_digest,
        request_digest=request_digest,
        resource=resource,
    )
    target = {
        "reference": resource,
        "remote_provenance_verified": True,
        "remote_provenance_evidence": evidence,
    }
    with pytest.raises(RS069ApplyBlocked, match="remote provenance positive claim rejected"):
        _validate_remote_evidence_claim(
            target,
            image_digest,
            expected_operation_id="bind_candidate_image_digest",
            expected_request_digest=request_digest,
        )


def test_non_boolean_caller_value_cannot_promote_remote_claim():
    image_digest = "sha256:" + "1" * 64
    target = {
        "reference": "us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator@" + image_digest,
        "remote_provenance_verified": 1,
        "remote_provenance_evidence": None,
    }
    with pytest.raises(RS069ApplyBlocked, match="remote provenance state is invalid"):
        _validate_remote_evidence_claim(target, image_digest)


def test_valid_digest_bound_remote_immutability_evidence_is_rejected_without_runner_source():
    image_digest = "sha256:" + "1" * 64
    request_digest = "sha256:" + "3" * 64
    resource = "us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator@" + image_digest
    evidence = _remote_evidence(
        schema="P5R0RS069RemoteImmutabilityEvidenceV1",
        source_kind="artifact_registry_immutability_observation",
        image_digest=image_digest,
        request_digest=request_digest,
        resource=resource,
    )
    target = {
        "reference": resource,
        "immutable_verified": True,
        "immutability_evidence": evidence,
    }
    with pytest.raises(RS069ApplyBlocked, match="remote immutability positive claim rejected"):
        _validate_remote_evidence_claim(
            target,
            image_digest,
            expected_operation_id="bind_candidate_image_digest",
            expected_request_digest=request_digest,
        )


def test_evidence_record_digest_mismatch_fails_closed():
    image_digest = "sha256:" + "1" * 64
    request_digest = "sha256:" + "3" * 64
    resource = "us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator@" + image_digest
    evidence = _remote_evidence(
        schema="P5R0RS069RemoteProvenanceEvidenceV1",
        source_kind="artifact_registry_provenance_lookup",
        image_digest=image_digest,
        request_digest=request_digest,
        resource=resource,
    )
    evidence["evidence_digest"] = "sha256:" + "9" * 64
    target = {
        "reference": resource,
        "remote_provenance_verified": True,
        "remote_provenance_evidence": evidence,
    }
    with pytest.raises(RS069ApplyBlocked, match="remote provenance positive claim rejected: no authenticated runner-owned source"):
        _validate_remote_evidence_claim(
            target,
            image_digest,
            expected_operation_id="bind_candidate_image_digest",
            expected_request_digest=request_digest,
        )



def test_failed_approval_cannot_authorize_corrected_operation(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    with pytest.raises(RS069ApplyBlocked, match="new RS-069R6 operation-1 approval"):
        apply(
            repository_root=ROOT,
            ledger_path=tmp_path / "operation-ledger.jsonl",
            approval_id="P5-MASTER-001/APPROVAL-001",
            execute_operation_1=True,
        )
    assert not (tmp_path / "operation-ledger.jsonl").exists()


def test_pending_request_cannot_start_runner_or_ledger(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    with pytest.raises(RS069ApplyBlocked, match="candidate binding digest drift"):
        apply(repository_root=ROOT, ledger_path=tmp_path / "operation-ledger.jsonl")
    assert not (tmp_path / "operation-ledger.jsonl").exists()



@pytest.mark.parametrize("mutation", ["candidate", "remote", "observed"])
def test_candidate_remote_and_observed_digests_require_strict_sha256(mutation, tmp_path):
    value = parse_canonical(CANDIDATE.read_bytes())
    value["artifact"]["path"] = "candidate-image-binding.json"
    invalid = "sha256:" + "a" * 63
    if mutation == "candidate":
        value["candidate"]["image_digest"] = invalid
    elif mutation == "remote":
        value["candidate"]["target_artifact_registry"]["remote_digest"] = invalid
    else:
        value["evidence_interpretation"]["remote_digest_evidence"]["observed_digest"] = invalid
    path = tmp_path / "candidate-image-binding.json"
    path.write_bytes(canonical_bytes(value))

    with pytest.raises(RS069ApplyBlocked, match="digest"):
        _load_candidate_binding(path, tmp_path)


@pytest.mark.parametrize("section", ["registry", "interpretation", "provenance", "validation"])
def test_publication_and_evidence_flags_require_real_booleans(section, tmp_path):
    value = parse_canonical(CANDIDATE.read_bytes())
    value["artifact"]["path"] = "candidate-image-binding.json"
    if section == "registry":
        value["candidate"]["target_artifact_registry"]["registry_digest_verified"] = 1
    elif section == "interpretation":
        value["evidence_interpretation"]["remote_digest_verified"] = 1
    elif section == "provenance":
        value["provenance"]["dirty_worktree"] = 1
    else:
        value["validation"]["production_promotable"] = 0
    path = tmp_path / "candidate-image-binding.json"
    path.write_bytes(canonical_bytes(value))

    with pytest.raises(RS069ApplyBlocked, match="boolean"):
        _load_candidate_binding(path, tmp_path)


def test_local_validation_and_forged_evidence_have_no_subprocess_or_network_side_effects(tmp_path, monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("cloud or network side effect attempted")

    monkeypatch.setattr(runner.subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    value = parse_canonical(CANDIDATE.read_bytes())
    value["artifact"]["path"] = "candidate-image-binding.json"
    value["candidate"]["target_artifact_registry"]["remote_provenance_verified"] = True
    value["candidate"]["target_artifact_registry"]["remote_provenance_evidence"] = {
        "lookup": "forged-attestation-lookup",
    }
    value["evidence_interpretation"]["remote_provenance_verified"] = True
    value["evidence_interpretation"]["remote_provenance_evidence"] = value["candidate"]["target_artifact_registry"]["remote_provenance_evidence"]
    path = tmp_path / "candidate-image-binding.json"
    path.write_bytes(canonical_bytes(value))

    with pytest.raises(RS069ApplyBlocked, match="positive claim rejected"):
        _load_candidate_binding(path, tmp_path)
    with pytest.raises(RS069ApplyBlocked, match="positive claim rejected"):
        _validate_remote_evidence_claim(
            value["candidate"]["target_artifact_registry"],
            value["candidate"]["image_digest"],
        )
    assert calls == []
