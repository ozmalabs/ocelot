from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.rs069_change_plan import load_plan
from services.p5_r0_evaluator.deploy.rs069r18r12_operation_3 import (
    ACCEPTANCE_CONTRACT,
    APPROVAL_ID,
    APPROVAL_SCHEMA,
    BINDING_SCHEMA,
    DEFAULT_APPROVAL,
    DEFAULT_BINDING,
    DEFAULT_DEPENDENCY_LEDGER,
    DEFAULT_LEDGER,
    DEFAULT_PROPOSAL,
    DEFAULT_REQUEST,
    LATER_OPERATION_IDS,
    OPERATION_ID,
    RS069R18R12Blocked,
    _load_r18r10_dependency,
    execute_operation_3,
    validate_operation_3_bindings,
)

ROOT = Path(__file__).resolve().parents[3]


def _binding(proposal: dict) -> dict:
    authority = deepcopy(proposal["authority"])
    claims = deepcopy(proposal["bound_claims"])
    public_key_digest = authority["public_key_digest"]
    body = {
        "schema": "P5R0KMSAuthorityBindingV1",
        "authority_id": authority["authority_id"],
        "key_id": authority["key_id"],
        "kms_key_version": proposal["kms"]["key_version"],
        "public_key_digest": public_key_digest,
        "purpose": "p5-r0-production-authority",
    }
    kms = {
        "key_version": proposal["kms"]["key_version"],
        "public_key": authority["public_key"],
        "public_key_digest": public_key_digest,
        "authority_binding": {**body, "binding_digest": sha256(body)},
    }
    artifact = {
        "schema": BINDING_SCHEMA,
        "classification": "repository_review_only_non_release",
        "status": "reviewed_local_binding_pending_signed_environment_approval",
        "proposal_digest": sha256(proposal),
        "proposal_state": "BLOCKED",
        "proposal_status": proposal["status"],
        "binding_scope": [OPERATION_ID],
        "authority": authority,
        "kms": kms,
        "environment": {
            "provider": authority["transport_attestation"]["provider"],
            "audience": authority["transport_attestation"]["audience"],
            "event": authority["transport_attestation"]["event"],
            "claims": claims["claims"],
            "claim_paths": claims["claim_paths"],
        },
    }
    return {**artifact, "artifact_digest": sha256(artifact)}


def _approval(plan: dict, proposal: dict, binding: dict, dependency: dict, request: dict) -> dict:
    artifact = {
        "schema": APPROVAL_SCHEMA,
        "acceptance_contract": ACCEPTANCE_CONTRACT,
        "approval_id": APPROVAL_ID,
        "status": "approved_single_operation_pending_review",
        "operation_id": OPERATION_ID,
        "operation_order": 3,
        "scope": [OPERATION_ID],
        "attempt_id": "rs069r18r12-op3-20260919-a1b2c3d4",
        "plan_digest": sha256(plan),
        "dependency_ledger_head_digest": dependency["ledger_head_digest"],
        "dependency_verified_event_digest": dependency["verified_event_digest"],
        "dependency_poststate_digest": dependency["poststate_digest"],
        "proposal_digest": sha256(proposal),
        "binding_artifact_digest": binding["artifact_digest"],
        "authority_binding_digest": binding["kms"]["authority_binding"]["binding_digest"],
        "request_digest": request["request_digest"],
        "unsigned_lock_digest": request["unsigned_lock_digest"],
        "attestation": {"status": "deferred", "deferred_to": "RS-080", "asserted": False},
        "later_operations": [{"id": item, "enabled": False} for item in LATER_OPERATION_IDS],
        "cloud_operations": [],
        "signature_present": False,
        "production_promotable": False,
        "master_approved": True,
        "user_approved": True,
        "approved": True,
        "enabled": True,
    }
    return {**artifact, "artifact_digest": sha256(artifact)}


def _write_canonical(path: Path, value: dict) -> None:
    path.write_bytes(canonical_bytes(value))


def _artifacts() -> tuple[dict, dict, dict, dict, dict, dict]:
    plan = load_plan(ROOT / "services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json")
    request = parse_canonical(DEFAULT_REQUEST.read_bytes())
    proposal = parse_canonical(DEFAULT_PROPOSAL.read_bytes())
    binding = _binding(proposal)
    dependency = _load_r18r10_dependency(DEFAULT_DEPENDENCY_LEDGER)
    approval = _approval(plan, proposal, binding, dependency, request)
    return plan, request, proposal, binding, approval, dependency


def test_default_attempt_fails_closed_without_creating_r18r12_ledger(tmp_path):
    with pytest.raises(RS069R18R12Blocked, match="R18R12 binding artifact is unavailable"):
        execute_operation_3(repository_root=ROOT, binding_path=tmp_path / "missing-binding.json", approval_path=tmp_path / "missing-approval.json", apply_enabled=True, ledger_path=tmp_path / DEFAULT_LEDGER.name)
    assert not (tmp_path / DEFAULT_LEDGER.name).exists()


def test_valid_packet_writes_only_four_local_review_events(tmp_path):
    plan, request, proposal, binding, approval, _ = _artifacts()
    paths = {name: tmp_path / f"{name}.json" for name in ("plan", "request", "proposal", "binding", "approval")}
    _write_canonical(paths["plan"], plan)
    _write_canonical(paths["request"], request)
    _write_canonical(paths["proposal"], proposal)
    _write_canonical(paths["binding"], binding)
    _write_canonical(paths["approval"], approval)
    ledger = tmp_path / DEFAULT_LEDGER.name
    before_dependency = DEFAULT_DEPENDENCY_LEDGER.read_bytes()

    result = execute_operation_3(
        repository_root=ROOT,
        plan_path=paths["plan"], request_path=paths["request"], proposal_path=paths["proposal"],
        binding_path=paths["binding"], approval_path=paths["approval"], ledger_path=ledger,
        dependency_ledger_path=DEFAULT_DEPENDENCY_LEDGER, apply_enabled=True,
    )

    assert result["status"] == "verified_repository_binding_review_only"
    assert result["cloud_operations"] == []
    assert result["mutations_performed"] is False
    assert result["signature_present"] is False
    assert result["production_promotable"] is False
    assert result["attestation"] == {"status": "deferred", "deferred_to": "RS-080", "asserted": False}
    records = [parse_canonical(line) for line in ledger.read_bytes().splitlines()]
    assert [record["kind"] for record in records] == ["run_started", "dependency_verified", "binding_verified", "run_stopped"]
    assert all(record["cloud_operations"] == [] and record["mutations_performed"] is False for record in records)
    assert records[-1]["later_operations_skipped"] == list(LATER_OPERATION_IDS)
    assert DEFAULT_DEPENDENCY_LEDGER.read_bytes() == before_dependency


def test_exact_digests_and_source_provenance_are_required():
    plan, request, proposal, binding, approval, dependency = _artifacts()
    checked = validate_operation_3_bindings(plan=plan, request=request, proposal=proposal, binding=binding, approval=approval, dependency=dependency)
    assert checked["plan_digest"] == sha256(plan)
    assert checked["proposal_digest"] == sha256(proposal)
    assert checked["request_digest"] == "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d"
    assert checked["unsigned_lock_digest"] == "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"
    assert binding["proposal_state"] == "BLOCKED"


def test_tampered_request_binding_or_blocked_approval_fails_closed(tmp_path):
    plan, request, proposal, binding, approval, dependency = _artifacts()
    tampered_request = deepcopy(request)
    tampered_request["unsigned_lock"]["classification"] = "altered"
    with pytest.raises(RS069R18R12Blocked, match="exact unsigned lock request validation failed"):
        validate_operation_3_bindings(plan=plan, request=tampered_request, proposal=proposal, binding=binding, approval=approval, dependency=dependency)

    tampered_binding = deepcopy(binding)
    tampered_binding["proposal_digest"] = "sha256:" + "0" * 64
    tampered_binding["artifact_digest"] = sha256({key: value for key, value in tampered_binding.items() if key != "artifact_digest"})
    with pytest.raises(RS069R18R12Blocked, match="proposal provenance drift"):
        validate_operation_3_bindings(plan=plan, request=request, proposal=proposal, binding=tampered_binding, approval=approval, dependency=dependency)

    blocked = deepcopy(approval)
    blocked["status"] = "blocked_pending_signed_environment_approval"
    blocked["artifact_digest"] = sha256({key: value for key, value in blocked.items() if key != "artifact_digest"})
    with pytest.raises(RS069R18R12Blocked, match="approval is missing or blocked"):
        validate_operation_3_bindings(plan=plan, request=request, proposal=proposal, binding=binding, approval=blocked, dependency=dependency)
    assert not list(tmp_path.iterdir())


def test_scope_attestation_signature_and_promotion_drift_are_rejected():
    plan, request, proposal, binding, approval, dependency = _artifacts()
    for field, value, message in (
        ("scope", [OPERATION_ID, LATER_OPERATION_IDS[0]], "approval scope drift"),
        ("attestation", {"status": "verified", "deferred_to": None, "asserted": True}, "attestation or downstream boundary drift"),
        ("signature_present", True, "local-only boundary"),
        ("production_promotable", True, "local-only boundary"),
    ):
        drifted = deepcopy(approval)
        drifted[field] = value
        drifted["artifact_digest"] = sha256({key: item for key, item in drifted.items() if key != "artifact_digest"})
        with pytest.raises(RS069R18R12Blocked, match=message):
            validate_operation_3_bindings(plan=plan, request=request, proposal=proposal, binding=binding, approval=drifted, dependency=dependency)


def test_wrong_dependency_path_or_replay_is_rejected(tmp_path):
    plan, request, proposal, binding, approval, dependency = _artifacts()
    paths = {name: tmp_path / f"{name}.json" for name in ("plan", "request", "proposal", "binding", "approval")}
    for name, value in (("plan", plan), ("request", request), ("proposal", proposal), ("binding", binding), ("approval", approval)):
        _write_canonical(paths[name], value)
    bad_kwargs = dict(repository_root=ROOT, plan_path=paths["plan"], request_path=paths["request"], proposal_path=paths["proposal"], binding_path=paths["binding"], approval_path=paths["approval"], dependency_ledger_path=ROOT / "var/p5-r0-rs069/operation-2-ledger.jsonl", ledger_path=tmp_path / DEFAULT_LEDGER.name, apply_enabled=True)
    with pytest.raises(RS069R18R12Blocked, match="immutable canonical ledger"):
        execute_operation_3(**bad_kwargs)

    ledger = tmp_path / DEFAULT_LEDGER.name
    kwargs = {**bad_kwargs, "dependency_ledger_path": DEFAULT_DEPENDENCY_LEDGER, "ledger_path": ledger}
    execute_operation_3(**kwargs)
    before = ledger.read_bytes()
    with pytest.raises(RS069R18R12Blocked, match="already has an attempt"):
        execute_operation_3(**kwargs)
    assert ledger.read_bytes() == before


def test_forbidden_signature_material_and_proposal_drift_are_rejected():
    plan, request, proposal, binding, approval, dependency = _artifacts()
    forbidden = deepcopy(binding)
    forbidden["signature"] = None
    forbidden["artifact_digest"] = sha256({key: value for key, value in forbidden.items() if key != "artifact_digest"})
    with pytest.raises(RS069R18R12Blocked, match="binding artifact is not closed"):
        validate_operation_3_bindings(plan=plan, request=request, proposal=proposal, binding=forbidden, approval=approval, dependency=dependency)

    blocked_source = deepcopy(proposal)
    blocked_source["state_proposed"] = "APPROVED"
    with pytest.raises(RS069R18R12Blocked, match="required blocked source"):
        validate_operation_3_bindings(plan=plan, request=request, proposal=blocked_source, binding=binding, approval=approval, dependency=dependency)
