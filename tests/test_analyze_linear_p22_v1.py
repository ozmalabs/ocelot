import hashlib
import json

import evaluation.process_mastery.analyze_linear_p22_v1 as analyzer
from evaluation.process_mastery.analyze_linear_p22_v1 import (
    _self_check_payload, analyze, self_check,
)


def test_self_check_exercises_null_timeout_unsafe_and_comparator_disagreement():
    result = self_check()
    assert result["status"] == "PASS"
    assert {"null", "timeout", "unsafe", "comparator_disagreement"}.issubset(
        set(result["cases"]))
    assert "resource_mismatch" in result["cases"]
    assert "selection_split_integrity" in result["cases"]


def test_incomplete_development_rows_are_retained_and_not_imputed():
    payload = _self_check_payload()
    removed = payload["checkpoint_rows"].pop()
    result = analyze(payload)
    assert result["status"] == "DEVELOPMENT_ONLY"
    assert result["counts"]["rows"] == len(payload["checkpoint_rows"])
    assert result["counts"]["missing_rows"] == 1
    assert any("missing_rows:1" == failure for failure in result["failures"])
    assert result["paired_effects"]["status"] == "NOT_ESTABLISHED"
    assert removed["world_id"] in payload["allocation_plan"]["world_ids_by_family"][
        removed["family"]]


def test_heldout_without_preregistration_is_rejected():
    payload = _self_check_payload()
    payload.update(split="heldout", heldout_accessed=True,
                   status="heldout_pending_analysis")
    result = analyze(payload)
    assert result["status"] == "NOT_ESTABLISHED"
    assert "heldout_requires_preregistration" in result["failures"]
    assert result["evidence_class"] == "HELDOUT_INVALID"


def test_full_vs_unchanged_mcnemar_keeps_all_paired_worlds():
    payload = _self_check_payload()
    result = analyze(payload)
    for key, comparison in result["mcnemar"].items():
        assert comparison["paired_worlds"] == 2
        assert comparison["left_only"] == 0
        assert comparison["right_only"] == 0
        assert comparison["p_two_sided"] == 1.0


def test_development_is_not_reported_as_attested_and_split_overlap_fails():
    payload = _self_check_payload()
    clean = analyze(payload)
    assert clean["provenance_status"] == "DEVELOPMENT_ONLY"

    payload["allocation_plan"]["validation_world_ids_by_family"]["d4"][0] = "d4-w0"
    result = analyze(payload)
    assert result["status"] == "DEVELOPMENT_ONLY"
    assert "split_identity_overlap:d4" in result["failures"]


def test_selection_allocation_is_required_and_disjoint():
    payload = _self_check_payload()
    del payload["allocation_plan"]["selection_world_ids_by_family"]
    missing = analyze(payload)
    assert "training_selection_or_validation_allocation_invalid" in missing["failures"]

    payload = _self_check_payload()
    payload["allocation_plan"]["selection_world_ids_by_family"]["d4"][0] = "d4-w0"
    overlap = analyze(payload)
    assert "split_identity_overlap:d4" in overlap["failures"]

    payload = _self_check_payload()
    payload["allocation_plan"]["selection_world_ids_by_family"]["loopover"][0] = "d4-w0"
    cross_family_overlap = analyze(payload)
    assert "allocation_identity_reused_across_families_or_splits" in (
        cross_family_overlap["failures"])


def test_native_learner_budget_and_action_invariants_are_required():
    payload = _self_check_payload()
    row = payload["checkpoint_rows"][0]
    row["primitive_budget_respected"] = False
    row["world_receipts_added"] = 1
    result = analyze(payload)
    assert any(item.startswith("native_primitive_budget_violation:")
               for item in result["failures"])
    assert any(item.startswith("heldout_world_receipt_created:")
               for item in result["failures"])


def test_unmatched_heldout_resources_are_capability_only(tmp_path, monkeypatch):
    payload = _self_check_payload()
    payload["split"] = "heldout"
    payload["heldout_accessed"] = True
    payload["status"] = "heldout_pending_analysis"
    payload["provenance"] = {"runtime_attestation": {
        "status": "ATTESTED", "issues": []}}
    plan = payload["allocation_plan"]
    families = plan["families"]
    panels = {}
    for family_index, family in enumerate(families):
        panels[family] = {}
        for split_index, split_name in enumerate(("heldout", "validation",
                                                  "selection", "training")):
            ids = [f"{family}-{split_name}-{index}" for index in range(200)]
            panels[family][split_name] = ids
            plan[{"heldout": "world_ids_by_family",
                  "validation": "validation_world_ids_by_family",
                  "selection": "selection_world_ids_by_family",
                  "training": "training_world_ids_by_family"}[split_name]][family] = ids
    seed = 0
    for split_name in ("training", "selection", "validation", "heldout"):
        for family in families:
            plan["seeds_by_split_family"][split_name][family] = list(
                range(seed, seed + 200))
            seed += 200

    templates = {(row["family"], row["generation"], row["arm"]): row
                 for row in payload["checkpoint_rows"]}
    rows = []
    for family in families:
        for world_id in panels[family]["heldout"]:
            for generation in plan["generations"]:
                for arm in plan["arms"]:
                    row = dict(templates[(family, generation, arm)])
                    row.update(world_id=world_id,
                        goal_digest=f"goal-{family}-{world_id}",
                        world_digest=f"world-{family}-{world_id}",
                        score=int(arm == "full"))
                    rows.append(row)
    rows[0]["native_rule_steps"] = 1.0
    payload["checkpoint_rows"] = rows
    payload["allocation_sha256"] = "allocation-digest"
    payload["freeze_commit"] = "freeze-commit"
    preregistration = tmp_path / "freeze.json"
    preregistration.write_text(json.dumps({"freeze": {
        "allocation_plan": plan,
        "allocation_sha256": payload["allocation_sha256"],
        "freeze_commit": payload["freeze_commit"],
        "provenance": payload["provenance"]}}), encoding="utf-8")
    payload["preregistration_sha256"] = hashlib.sha256(
        preregistration.read_bytes()).hexdigest()
    monkeypatch.setattr(analyzer, "summarize_families", lambda *args, **kwargs: {
        "status": "PASS", "families": {family: {"registered_criteria": {
            "passed": True}} for family in families}})
    monkeypatch.setattr(analyzer, "_bootstrap_mean_interval",
                        lambda *_args, **_kwargs: [0.0, 0.0])

    result = analyze(payload, preregistration=preregistration)
    assert result["failures"] == []
    assert result["paired_effects"]["score_criteria_pass"] is True
    assert result["paired_effects"]["resource_match_pass"] is False
    assert result["paired_effects"]["registered_phase_pass"] is True
    assert result["paired_effects"]["efficiency_comparable"] is False
    assert result["efficiency_status"] == "NOT_ESTABLISHED"
    assert result["status"] == "PASS"
    assert result["evidence_class"] == "CAPABILITY_ONLY"
