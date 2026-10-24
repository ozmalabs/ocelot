"""P23.02 finite effect reachability and qualification feasibility checks."""
from __future__ import annotations

import json
from pathlib import Path

from evaluation.process_mastery.search_feasibility_audit import (
    _checkpoint,
    audit_d4_checkpoint,
    audit_loopover_checkpoint,
    classify_goal_pair,
)


ROOT = Path(__file__).resolve().parents[1]


def _load_parent(path: str):
    return _checkpoint(json.loads((ROOT / path).read_text()))


def _load_d4_generation_zero():
    roots = json.loads((ROOT / "evaluation/process_mastery/results/"
        "p22_four_arm_checkpoint_roots_d4_0520.json").read_text())
    return roots["arms"]["invention_only"]["generation_zero_checkpoint"]


def test_d4_closure_has_eight_effects():
    checkpoint = _load_parent(
        "evaluation/process_mastery/results/"
        "p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json")
    report = audit_d4_checkpoint(checkpoint)
    assert report["closure_size"] == 8
    assert len(set(map(tuple, report["closure_effects"]))) == 8
    assert len(report["remaining_novel_nonidentity_effects"]) == 3
    assert report["identity_effect"] not in report["remaining_novel_nonidentity_effects"]
    assert report["heldout_accessed"] is False
    assert report["agent_graph_mutated"] is False

    # The frozen generation-zero state has the same finite closure, while its
    # novelty inventory remains root-specific.
    generation_zero = audit_d4_checkpoint(_load_d4_generation_zero(),
        task_checkpoint=checkpoint)
    assert generation_zero["closure_size"] == 8
    assert generation_zero["remaining_novel_nonidentity_effects"] != \
        report["remaining_novel_nonidentity_effects"]


def test_each_remaining_effect_has_feasibility_record():
    checkpoint = _load_parent(
        "evaluation/process_mastery/results/"
        "p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json")
    report = audit_d4_checkpoint(checkpoint)
    records = {tuple(row["effect"]): row for row in report["records"]}
    remaining = set(map(tuple, report["remaining_novel_nonidentity_effects"]))
    assert set(records) == remaining
    for effect in remaining:
        row = records[effect]
        assert row["is_identity"] is False
        assert row["is_active_or_adopted"] is False
        assert row["native_qualification"] == \
            "NOT_ESTABLISHED_REQUIRES_NATIVE_VERIFIED_TRIALS"
        assert row["qualification_feasibility"] in {
            "FINITE_WITNESS_FOUND",
            "NO_ADMISSIBLE_TRAINING_GOAL_PAIR_WITHIN_REGISTERED_CONTEXT",
            "UNKNOWN_OUTSIDE_BOUND",
            "UNKNOWN_NO_DISTINCT_NOVEL_TRAINING_GOAL_PAIR",
        }
        assert sum(row["goal_pair_status_counts"].values()) == \
            len(row["goal_pair_records"])
        if row["witness"]:
            assert row["witness"]["source_training_task"] != \
                row["witness"]["independent_training_task"]
            assert row["witness"]["status"] == "FINITE_WITNESS_FOUND"


def test_guard_failure_not_unreachable_claim():
    result = classify_goal_pair(effect_reachable=True, guard_passes=False,
        precondition_passes=True, source_novel=True, child_novel=True)
    assert result == "REJECTED_BY_NAMED_PREDICATE:guard_mismatch"
    assert "UNREACHABLE" not in result
    assert classify_goal_pair(effect_reachable=False, guard_passes=False,
        precondition_passes=False, source_novel=False, child_novel=False) == \
        "UNKNOWN_OUTSIDE_BOUND"


def test_bounded_loopover_reports_unknown_beyond_bound():
    checkpoint = _load_parent(
        "evaluation/process_mastery/results/"
        "p22_training_panel_registered_root_loopover_g1_0924_0926_ticks60_depth3.json")
    report = audit_loopover_checkpoint(checkpoint, max_depth=0, max_nodes=100)
    assert report["max_depth"] == 0
    assert report["unknown_goal_count"] > 0
    assert any(row["status"] == "UNKNOWN_OUTSIDE_BOUND"
               for row in report["training_goal_witnesses"])
    assert all(row["status"] != "UNREACHABLE"
               for row in report["training_goal_witnesses"])
    assert report["heldout_accessed"] is False
