from copy import deepcopy
from pathlib import Path

import inspect
import pytest

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.rs069_change_plan import load_plan
from services.p5_r0_evaluator.deploy.rs069r18r13_operation_4 import (
    ACCEPTANCE_CONTRACT,
    APPROVAL_ID,
    APPROVAL_SCHEMA,
    BINDING_SCHEMA,
    CONTRACT_SCHEMA,
    DEFAULT_ARTIFACT_INDEX,
    DEFAULT_CONTRACT,
    DEFAULT_LEDGER,
    DEFAULT_R18R12_APPROVAL,
    DEFAULT_R18R12_LEDGER,
    DISPATCH_ID,
    LATER_OPERATION_IDS,
    OPERATION_ID,
    RS069R18R13Blocked,
    execute_operation_4,
    validate_operation_4_packet,
)
from services.p5_r0_evaluator.store import MemoryStore

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json"
REQUEST_PATH = ROOT / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json"


def _digest(value):
    return sha256(value) if isinstance(value, dict) else sha256(canonical_bytes(value))


def _write(path: Path, value: dict) -> None:
    path.write_bytes(canonical_bytes(value))


def _packet(*, generations: list[int | None] | None = None) -> tuple[dict, dict, dict, dict, dict]:
    plan = load_plan(PLAN_PATH)
    request = parse_canonical(REQUEST_PATH.read_bytes())
    index = parse_canonical(DEFAULT_ARTIFACT_INDEX.read_bytes())
    records = plan["gcs_object_records"]
    destination = {
        "schema": BINDING_SCHEMA,
        "classification": "repository_review_only_non_release",
        "status": "reviewed_destination_binding_pending_execution",
        "operation_id": OPERATION_ID,
        "operation_order": 4,
        "scope": [OPERATION_ID],
        "project_id": "reviewed-project",
        "bucket": "reviewed-private-bucket",
        "prefix": "p5-r0/runs",
        "run_id": "rs069r18r13-op4-a1b2c3d4",
        "namespace_formula": "gs://{bucket}/{prefix}/{run_id}/{object_suffix}",
        "visibility": {"default": "private", "private_truth_object": "private", "worker_public_output": False},
        "credential_binding": "injected_reviewed_execution_path_only",
        "artifact_index_digest": index["index_digest"],
        "unsigned_lock_digest": request["unsigned_lock_digest"],
        "dependency_ledger_head_digest": parse_canonical(DEFAULT_R18R12_LEDGER.read_bytes().splitlines()[-1])["event_digest"],
    }
    destination["artifact_digest"] = sha256(destination)
    generations = generations or [0] * len(records)
    objects = [
        {
            "object_id": record["object_id"],
            "object_suffix": record["object_suffix"],
            "private": record["private"],
            "artifact_digest": record["artifact_digest"],
            "file_digest": record["file_digest"],
            "expected_generation": generation,
        }
        for record, generation in zip(records, generations)
    ]
    approval = {
        "schema": APPROVAL_SCHEMA,
        "acceptance_contract": ACCEPTANCE_CONTRACT,
        "approval_id": APPROVAL_ID,
        "dispatch_id": DISPATCH_ID,
        "status": "approved_single_operation_pending_reviewed_execution",
        "operation_id": OPERATION_ID,
        "operation_order": 4,
        "scope": [OPERATION_ID],
        "attempt_id": "rs069r18r13-op4-a1b2c3d4",
        "plan_digest": sha256(plan),
        "r18r12_ledger_head_digest": parse_canonical(DEFAULT_R18R12_LEDGER.read_bytes().splitlines()[-1])["event_digest"],
        "r18r12_verified_event_digest": parse_canonical(DEFAULT_R18R12_LEDGER.read_bytes().splitlines()[-2])["event_digest"],
        "r18r12_approval_digest": parse_canonical(DEFAULT_R18R12_LEDGER.read_bytes().splitlines()[0])["approval_digest"],
        "r18r10_ledger_head_digest": "sha256:7ccf71443129e799837f085de3252a33d6e5fa7d3f4d5d3cca4e754192bbda8d",
        "r18r10_verified_event_digest": "sha256:42ed5a997d9fdd87e674fe1b1771115f11662277619b813eba6035c0a8624cac",
        "r18r10_poststate_digest": "sha256:9a7fcde1498606c60ab06e83a91eb3ba1712f8da6cdb554ca4cb02f3c2060ff7",
        "artifact_index_digest": index["index_digest"],
        "object_set_digest": _digest(objects),
        "unsigned_lock_digest": request["unsigned_lock_digest"],
        "destination": destination,
        "objects": objects,
        "allowed_actions": ["gcs.create_only_or_exact_generation_match"],
        "forbidden_actions": ["gcs.list", "gcs.delete", "gcs.overwrite", "credential_generation"],
        "later_operations": [{"id": item, "enabled": False} for item in LATER_OPERATION_IDS],
        "cloud_operations": ["gcs.create_only_or_exact_generation_match"],
        "signature_present": False,
        "production_promotable": False,
        "master_approved": True,
        "user_approved": True,
        "approved": True,
        "enabled": True,
    }
    approval["artifact_digest"] = sha256(approval)
    contract = parse_canonical(DEFAULT_CONTRACT.read_bytes())
    return plan, request, destination, approval, contract


def _paths(tmp_path: Path, approval: dict, binding: dict) -> dict[str, Path]:
    approval_path = tmp_path / "approval.json"
    binding_path = tmp_path / "binding.json"
    _write(approval_path, approval)
    _write(binding_path, binding)
    return {"approval": approval_path, "binding": binding_path, "ledger": tmp_path / DEFAULT_LEDGER.name}


def _store_for_packet(*, generations: list[int] | None = None) -> MemoryStore:
    store = MemoryStore()
    plan = load_plan(PLAN_PATH)
    for record in plan["gcs_object_records"]:
        path = ROOT / record["local_artifact_path"]
        name = f"p5-r0/runs/rs069r18r13-op4-a1b2c3d4/{record['object_suffix']}"
        store.create(name, path.read_bytes())
    return store


def test_contract_and_packet_bind_exact_canonical_objects_and_dependencies():
    plan, request, binding, approval, contract = _packet()
    checked = validate_operation_4_packet(contract=contract, plan=plan, request=request, binding=binding, approval=approval)
    assert contract["schema"] == CONTRACT_SCHEMA
    assert checked["index_digest"] == "sha256:04a98e3e48685228fd68ea757de276fe1c1a7ce347bd027a2756a48595897768"
    assert len(checked["records"]) == 11
    assert [item["object_id"] for item in checked["records"]] == [item["object_id"] for item in approval["objects"]]
    assert checked["r18r12"]["ledger_head_digest"] == approval["r18r12_ledger_head_digest"]
    assert checked["r18r10"]["ledger_head_digest"] == approval["r18r10_ledger_head_digest"]
    assert checked["later_operations_enabled"] is False


def test_missing_credentials_and_caller_boolean_fail_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    _, _, binding, approval, _ = _packet()
    paths = _paths(tmp_path, approval, binding)
    with pytest.raises(RS069R18R13Blocked, match="credentials"):
        execute_operation_4(binding_path=paths["binding"], approval_path=paths["approval"], ledger_path=paths["ledger"])
    assert not paths["ledger"].exists()
    assert "apply_enabled" not in inspect.signature(execute_operation_4).parameters
    with pytest.raises(RS069R18R13Blocked, match="destination binding identity drift"):
        execute_operation_4(store=MemoryStore(), ledger_path=tmp_path / DEFAULT_LEDGER.name)
    assert not (tmp_path / DEFAULT_LEDGER.name).exists()


def test_valid_execution_creates_exactly_eleven_objects_and_appends_only_local_ledger(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    plan, request, binding, approval, contract = _packet()
    paths = _paths(tmp_path, approval, binding)
    store = MemoryStore()
    result = execute_operation_4(contract_path=DEFAULT_CONTRACT, plan_path=PLAN_PATH, binding_path=paths["binding"], approval_path=paths["approval"], ledger_path=paths["ledger"], store=store)
    assert result["status"] == "verified_ingest_generated_bundle_to_gcs"
    assert result["object_count"] == 11
    assert result["mutations_performed"] is True
    assert result["later_operations_enabled"] is False
    records = [parse_canonical(line) for line in paths["ledger"].read_bytes().splitlines()]
    assert [record["kind"] for record in records] == ["run_started", "objects_verified", "run_stopped"]
    assert all(record["scope"] == [OPERATION_ID] and record["later_operations_enabled"] is False for record in records)
    assert records[1]["mutations_performed"] is True
    assert len(records[1]["objects"]) == 11
    assert all({"generation", "artifact_digest", "file_digest"}.issubset(item) for item in records[1]["objects"])
    assert records[1]["objects"][0]["artifact_digest"] == approval["objects"][0]["artifact_digest"]
    assert records[1]["objects"][0]["file_digest"] == approval["objects"][0]["file_digest"]
    assert records[-1]["later_operations_skipped"] == list(LATER_OPERATION_IDS)
    assert records[1]["objects"][6]["object_id"] == "private_store"
    assert all("list" not in record["cloud_operations"] and "delete" not in record["cloud_operations"] for record in records)
    assert plan["status"] == "blocked_pending_master_approval"
    assert request["unsigned_lock_digest"] == "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"


def test_exact_existing_generations_are_noop_and_replay_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    plan, _, binding, _, contract = _packet(generations=[1] * 11)
    _, request, _, approval, _ = _packet(generations=[1] * 11)
    paths = _paths(tmp_path, approval, binding)
    store = _store_for_packet()
    result = execute_operation_4(contract_path=DEFAULT_CONTRACT, plan_path=PLAN_PATH, binding_path=paths["binding"], approval_path=paths["approval"], ledger_path=paths["ledger"], store=store)
    assert result["mutations_performed"] is False
    before = paths["ledger"].read_bytes()
    with pytest.raises(RS069R18R13Blocked, match="already has an attempt"):
        execute_operation_4(contract_path=DEFAULT_CONTRACT, plan_path=PLAN_PATH, binding_path=paths["binding"], approval_path=paths["approval"], ledger_path=paths["ledger"], store=store)
    assert paths["ledger"].read_bytes() == before


def test_unresolved_attempt_identity_is_not_executable():
    plan, request, binding, approval, contract = _packet()
    approval["attempt_id"] = "rs069r18r13-op4-unresolved"
    approval["artifact_digest"] = sha256({key: value for key, value in approval.items() if key != "artifact_digest"})

    with pytest.raises(RS069R18R13Blocked, match="attempt identity is unresolved"):
        validate_operation_4_packet(contract=contract, plan=plan, request=request, binding=binding, approval=approval)


def test_digest_bucket_project_generation_and_scope_drift_fail_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    plan, request, binding, approval, contract = _packet()
    cases = []
    drift = deepcopy(approval)
    drift["objects"][0]["file_digest"] = "sha256:" + "0" * 64
    drift["object_set_digest"] = _digest(drift["objects"])
    drift["artifact_digest"] = sha256({key: value for key, value in drift.items() if key != "artifact_digest"})
    cases.append((drift, binding, "approved object drift"))
    bad_binding = deepcopy(binding)
    bad_binding["project_id"] = "other-project"
    bad_binding["artifact_digest"] = sha256({key: value for key, value in bad_binding.items() if key != "artifact_digest"})
    bad_approval = deepcopy(approval)
    bad_approval["destination"] = binding
    bad_approval["artifact_digest"] = sha256({key: value for key, value in bad_approval.items() if key != "artifact_digest"})
    cases.append((bad_approval, bad_binding, "bucket/project binding drift"))
    ambiguous = deepcopy(approval)
    ambiguous["objects"][0]["expected_generation"] = None
    ambiguous["object_set_digest"] = _digest(ambiguous["objects"])
    ambiguous["artifact_digest"] = sha256({key: value for key, value in ambiguous.items() if key != "artifact_digest"})
    cases.append((ambiguous, binding, "generation precondition is missing or ambiguous"))
    for bad_approval, bad_binding, message in cases:
        with pytest.raises(RS069R18R13Blocked, match=message):
            validate_operation_4_packet(contract=contract, plan=plan, request=request, binding=bad_binding, approval=bad_approval)
    bad_scope = deepcopy(approval)
    bad_scope["scope"] = [OPERATION_ID, "configure_cloud_run_and_confidential_space"]
    bad_scope["artifact_digest"] = sha256({key: value for key, value in bad_scope.items() if key != "artifact_digest"})
    with pytest.raises(RS069R18R13Blocked, match="approval scope drift"):
        validate_operation_4_packet(contract=contract, plan=plan, request=request, binding=binding, approval=bad_scope)


def test_r18r12_path_and_downstream_contract_are_hard_bound(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    plan, request, binding, approval, contract = _packet()
    with pytest.raises(RS069R18R13Blocked, match="canonical terminal ledger"):
        validate_operation_4_packet(contract=contract, plan=plan, request=request, binding=binding, approval=approval, r18r12_ledger_path=tmp_path / DEFAULT_R18R12_LEDGER.name)
    changed = deepcopy(contract)
    changed["downstream_operations"][0]["enabled"] = True
    with pytest.raises(RS069R18R13Blocked, match="downstream boundary drift"):
        validate_operation_4_packet(contract=changed, plan=plan, request=request, binding=binding, approval=approval)
