from dataclasses import asdict, replace
import hashlib
import json

import pytest

import evaluation.process_mastery.linear_p22_v1 as linear_p22_v1
from evaluation.process_mastery.linear_p22_v1 import (
    ARMS, FAMILIES, GENERATIONS, PANEL_SIZE, PREREGISTRATION, PROVENANCE_FILES,
    RESOURCE_FIELDS, _index_manifest, _preflight_checkpoint_resources,
    _hash_files, allocation, self_check,
)
from evaluation.process_mastery.checkpoint_world_adapter import (
    capture_held_process_checkpoint, capture_passive_checkpoint,
    _native_graph_snapshot_digest,
)
from tests.test_open_process_adoption import _agent as adoption_agent
from tests.test_checkpoint_world_adapter import _native_rule_work
from evaluation.process_mastery.generators import SPLITS


def test_allocation_uses_complete_disjoint_split_namespaces():
    plan = allocation()
    from evaluation.process_mastery.independent_worlds import (
        generate_d4_world_v2, generate_loopover_world_v2,
    )
    generators = {"d4": generate_d4_world_v2,
                  "loopover": generate_loopover_world_v2}
    split_ids = {
        "heldout": "world_ids_by_family",
        "validation": "validation_world_ids_by_family",
        "selection": "selection_world_ids_by_family",
        "training": "training_world_ids_by_family",
    }
    split_names = {"training": "train", "selection": "selection",
                   "validation": "validation", "heldout": "heldout"}
    split_draw = {"training": 600, "selection": 0,
                  "validation": 600, "heldout": 0}
    for split, key in split_ids.items():
        for family, generator in generators.items():
            generated = generator(split=split_names[split],
                                   draw=split_draw[split])
            assert plan[key][family][0] == generated["world_id"]
    for family in FAMILIES:
        panels = [plan[key][family] for key in (
            "world_ids_by_family", "validation_world_ids_by_family",
            "selection_world_ids_by_family", "training_world_ids_by_family")]
        assert all(len(panel) == PANEL_SIZE for panel in panels)
        assert all(len(panel) == len(set(panel)) for panel in panels)
        assert all(not (set(panels[left]) & set(panels[right]))
                   for left in range(len(panels)) for right in range(left + 1, len(panels)))
    p22_seeds = {seed for panels in plan["seeds_by_split_family"].values()
                 for family_seeds in panels.values() for seed in family_seeds}
    pmb_v1_seeds = set().union(*(set(values) for values in SPLITS.values()))
    assert len(p22_seeds) == 4 * len(FAMILIES) * PANEL_SIZE
    assert not p22_seeds.intersection(pmb_v1_seeds)


def test_provenance_closure_includes_candidate_and_arm_runner_adapters():
    required = {
        "evaluation/process_mastery/p22_checkpoint_panel.py",
        "evaluation/process_mastery/p22_development.py",
        "scripts/run_p22_development_probe.py",
        "scripts/run_p22_four_arm_development.py",
    }
    assert required.issubset(PROVENANCE_FILES)
    hashes = _hash_files()
    assert all(len(hashes[path]) == 64 for path in required)


def test_runner_self_check_executes_native_adapter_and_controls():
    result = self_check()
    assert result["status"] == "PASS"
    assert result["heldout_accessed"] is False
    assert result["native_process_apply"] == [1, 0, 2, 3]
    assert len(result["structural_controls"]) == 4
    assert result["lineage_tamper_control"]["status"] == "FAIL"
    assert result["manifest_lineage_control"]["checked_parent_links"] == 24
    assert result["manifest_lineage_tamper_control"]["status"] == "FAIL"


def test_heldout_freeze_is_verified_before_learner_or_world_access(monkeypatch):
    def reject_freeze(*_args, **_kwargs):
        raise RuntimeError("freeze rejected")

    def reject_world_access(*_args, **_kwargs):
        pytest.fail("held-out world generator accessed before freeze verification")

    monkeypatch.setattr(linear_p22_v1, "_verify_freeze", reject_freeze)
    monkeypatch.setattr(linear_p22_v1, "Agent", reject_world_access)
    monkeypatch.setattr(linear_p22_v1, "generate_d4_world_v2", reject_world_access)
    monkeypatch.setattr(linear_p22_v1, "generate_loopover_world_v2", reject_world_access)
    with pytest.raises(RuntimeError, match="freeze rejected"):
        linear_p22_v1.run_heldout(preregistration=linear_p22_v1.ROOT / "unused",
                                  requested_hash="0" * 64)


def test_unfrozen_preregistration_is_rejected_before_heldout_access(
        tmp_path, monkeypatch):
    preregistration = tmp_path / PREREGISTRATION
    preregistration.parent.mkdir(parents=True)
    raw = b"# Draft preregistration\nNo machine-readable freeze.\n"
    preregistration.write_bytes(raw)
    monkeypatch.setattr(linear_p22_v1, "ROOT", tmp_path)

    def git_response(args, *, cwd, text):
        if args[:2] == ["git", "status"]:
            return ""
        if args[:2] == ["git", "diff-tree"]:
            return PREREGISTRATION + "\n"
        pytest.fail(f"unexpected git command before freeze parsing: {args}")

    def reject_world_access(*_args, **_kwargs):
        pytest.fail("held-out access occurred before the missing freeze was rejected")

    monkeypatch.setattr(linear_p22_v1.subprocess, "check_output", git_response)
    monkeypatch.setattr(linear_p22_v1, "Agent", reject_world_access)
    monkeypatch.setattr(linear_p22_v1, "generate_d4_world_v2", reject_world_access)
    monkeypatch.setattr(linear_p22_v1, "generate_loopover_world_v2", reject_world_access)

    with pytest.raises(RuntimeError, match="lacks its machine-readable freeze"):
        linear_p22_v1.run_heldout(preregistration=preregistration,
            requested_hash=hashlib.sha256(raw).hexdigest())


def test_manifest_accepts_approved_improvement_and_passive_control_lineages():
    agent = adoption_agent()
    try:
        agent.add_domain("d4", "permutation", [[0, 1, 2, 3]],
                         {"d4": [1, 0, 2, 3]})
        agent.add_domain("loopover", "permutation", [list(range(9))],
                         {"loopover": [1, 0, 2, 3, 4, 5, 6, 7, 8]})
        roots, records = {}, []
        for family, domain in (("d4", "d4"), ("loopover", "loopover")):
            for arm in ARMS:
                root = capture_held_process_checkpoint(agent,
                    agent.schemas(domain)[0], checkpoint_id=f"{family}:{arm}:g0")
                roots[f"{family}:{arm}"] = asdict(root)
                parent = root
                for generation in GENERATIONS:
                    checkpoint = capture_passive_checkpoint(agent,
                        checkpoint_id=f"{family}:{arm}:g{generation}",
                        parent=parent, generation=generation,
                        declared_primitive_work=0)
                    if arm in {"invention_only", "full"}:
                        approval_id, receipt_id = f"approval:{family}:{arm}:{generation}", f"receipt:{family}:{arm}:{generation}"
                        snapshot = json.loads(checkpoint.resource_snapshot_json)
                        payload = {"schema": "p22_native_checkpoint_v1",
                            "checkpoint_id": checkpoint.checkpoint_id,
                            "parent_digest": checkpoint.parent_digest,
                            "generation": checkpoint.generation,
                            "expression_digest": checkpoint.expression_digest,
                            "params": list(checkpoint.params),
                            "primitive_work": checkpoint.declared_primitive_work,
                            "cumulative_primitive_work": checkpoint.cumulative_primitive_work,
                            "resource_snapshot_sha256": snapshot["snapshot_sha256"],
                            "native_graph_snapshot_sha256": _native_graph_snapshot_digest(
                                checkpoint.native_graph_snapshot_json),
                            "approval_id": approval_id, "receipt_id": receipt_id}
                        digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
                            separators=(",", ":")).encode()).hexdigest()
                        checkpoint = replace(checkpoint, checkpoint_digest=digest,
                            approval_id=approval_id, receipt_id=receipt_id)
                    records.append({"family": family, "arm": arm,
                        "generation": generation, "checkpoint": asdict(checkpoint)})
                    parent = checkpoint
        agent.add_domain("d4-alternate", "permutation",
            [[0, 1, 2, 3]], {"alternate": [0, 2, 1, 3]})
        alternate_root = capture_held_process_checkpoint(agent,
            agent.schemas("d4-alternate")[0], checkpoint_id="d4:full:wrong-g0")
        mismatched_roots = dict(roots)
        mismatched_roots["d4:full"] = asdict(alternate_root)
        with pytest.raises(ValueError,
                           match="do not share one generation-zero ancestor process: d4"):
            _index_manifest({"schema": "p22_checkpoint_manifest_v1",
                "ancestors": mismatched_roots, "lineages": records})
        indexed_roots, indexed_lineages = _index_manifest({
            "schema": "p22_checkpoint_manifest_v1", "ancestors": roots,
            "lineages": records})
        assert set(indexed_roots) == {f"{family}:{arm}"
            for family in FAMILIES for arm in ARMS}
        assert len(indexed_lineages) == len(FAMILIES) * len(ARMS) * len(GENERATIONS)
        assert all(checkpoint.approval_id is None and checkpoint.receipt_id is None
            for (family, arm, _generation), checkpoint in indexed_lineages.items()
            if arm in {"unchanged", "adaptive_only"})
        wrong_control = indexed_lineages[("d4", "unchanged", 1)]
        wrong_params = list(wrong_control.params)
        wrong_params[0], wrong_params[1] = wrong_params[1], wrong_params[0]
        resource_snapshot = json.loads(wrong_control.resource_snapshot_json)
        wrong_payload = {"schema": "p22_native_checkpoint_v1",
            "checkpoint_id": wrong_control.checkpoint_id,
            "parent_digest": wrong_control.parent_digest,
            "generation": wrong_control.generation,
            "expression_digest": "changed-expression",
            "params": wrong_params,
            "primitive_work": wrong_control.declared_primitive_work,
            "cumulative_primitive_work": wrong_control.cumulative_primitive_work,
            "resource_snapshot_sha256": resource_snapshot["snapshot_sha256"],
            "native_graph_snapshot_sha256": _native_graph_snapshot_digest(
                wrong_control.native_graph_snapshot_json)}
        wrong_digest = hashlib.sha256(json.dumps(wrong_payload, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        wrong_control = replace(wrong_control,
            expression_digest="changed-expression", params=tuple(wrong_params),
            checkpoint_digest=wrong_digest)
        invalid_records = [dict(record) for record in records]
        for record in invalid_records:
            if (record["family"], record["arm"], record["generation"]) == (
                    "d4", "unchanged", 1):
                record["checkpoint"] = asdict(wrong_control)
        with pytest.raises(ValueError, match="lineage checkpoint digest/generation invalid"):
            _index_manifest({"schema": "p22_checkpoint_manifest_v1",
                "ancestors": roots, "lineages": invalid_records})

        invalid_records = [dict(record) for record in records]
        missing_approval = indexed_lineages[("loopover", "full", 1)]
        snapshot = json.loads(missing_approval.resource_snapshot_json)
        unapproved_payload = {"schema": "p22_native_checkpoint_v1",
            "checkpoint_id": missing_approval.checkpoint_id,
            "parent_digest": missing_approval.parent_digest,
            "generation": missing_approval.generation,
            "expression_digest": missing_approval.expression_digest,
            "params": list(missing_approval.params),
            "primitive_work": missing_approval.declared_primitive_work,
            "cumulative_primitive_work": missing_approval.cumulative_primitive_work,
                "resource_snapshot_sha256": snapshot["snapshot_sha256"],
                "native_graph_snapshot_sha256": _native_graph_snapshot_digest(
                    missing_approval.native_graph_snapshot_json)}
        unapproved_digest = hashlib.sha256(json.dumps(unapproved_payload,
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        missing_approval = replace(missing_approval, approval_id=None,
            receipt_id=None, checkpoint_digest=unapproved_digest)
        for record in invalid_records:
            if (record["family"], record["arm"], record["generation"]) == (
                    "loopover", "full", 1):
                record["checkpoint"] = asdict(missing_approval)
        with pytest.raises(ValueError, match="approved lineage evidence missing"):
            _index_manifest({"schema": "p22_checkpoint_manifest_v1",
                "ancestors": roots, "lineages": invalid_records})
    finally:
        del agent


def test_resource_preflight_rejects_partial_approval_cost_before_holdout():
    agent = adoption_agent()
    try:
        agent.add_domain("d4", "permutation", [[0, 1, 2, 3]],
                         {"d4": [1, 0, 2, 3]})
        agent.s.add_node("OpenProcessAdoptionApproval", {
            "status": "consumed", "approval_kind": "human"})
        root = capture_held_process_checkpoint(agent, agent.schemas("d4")[0],
            checkpoint_id="preflight-root",
            runtime_counters={"native_rule_steps": 10, "native_model_calls": 0,
                "process_peak_rss_bytes": 4096},
            native_rule_work=_native_rule_work(12))
        lineages = {(family, arm, generation): root for family in FAMILIES
                    for arm in ARMS for generation in GENERATIONS}
        freeze = {"checkpoint_wall_time_seconds": {
            f"{family}:{arm}:g{generation}": 0.01 for family in FAMILIES
            for arm in ARMS for generation in GENERATIONS}}
        ceilings = {field: 1_000_000_000 for field in RESOURCE_FIELDS}
        with pytest.raises(RuntimeError,
                           match="not fully measured before holdout: .*:approval_cost"):
            _preflight_checkpoint_resources(freeze, lineages, ceilings)
    finally:
        del agent
