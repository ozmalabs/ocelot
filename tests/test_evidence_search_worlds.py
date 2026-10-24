from __future__ import annotations

import pytest

from evaluation.process_mastery.evidence_search_worlds import (
    EFFORT_CEILINGS, EvidenceSearchPool, generate_evidence_search_pool,
    search_cost_curve, selector_views,
)


def test_pool_identity_shared_across_selectors():
    pool = generate_evidence_search_pool(split="train", draws=range(12), seed=911)
    arms = selector_views(pool)
    ids = {arm: tuple(row["world_id"] for row in rows) for arm, rows in arms.items()}
    assert ids["residual"] == ids["fixed"] == ids["random"]
    assert arms["residual"] == arms["fixed"] == arms["random"]
    assert pool.pool_sha256 == generate_evidence_search_pool(
        split="train", draws=range(12), seed=911).pool_sha256


def test_goal_not_active_operator_function():
    pool = generate_evidence_search_pool(split="development", draws=range(30), seed=2026)
    for task in pool.opportunities:
        one_step = {int(mapping[str(task["initial_state"])])
                    for mapping in task["primitive_affordances"].values()}
        assert task["goal_state"] not in one_step


def test_finite_space_reports_exhaustion():
    task = {"world_id": "dead-end", "initial_state": 0, "goal_state": 3,
        "primitive_affordances": {"a": {"0": 1}, "b": {"0": 2}},
        "transition_model": ()}
    report = search_cost_curve(task, ceilings=(1, 2, 4, 8))
    assert report["finite_space_exhausted"] is True
    assert report["finite_space_exhaustion_work"] == 2
    assert report["attempts"] == 2
    assert [row["effort_ceiling"] for row in report["effort_curve"]] == [1, 2, 4, 8]


def test_all_search_costs_and_failures_counted():
    task = {"world_id": "mixed", "initial_state": 0, "goal_state": 3,
        "primitive_affordances": {"a": {}, "b": {}},
        "transition_model": ((0, "a", 1), (1, "a", 3))}
    report = search_cost_curve(task, ceilings=(1, 2, 4, 8))
    assert report["attempts"] == 6
    assert report["unique_effect_coverage"] > 0
    assert report["failed_or_invalid_attempts"] == 5
    assert all(row["attempts"] <= row["effort_ceiling"] for row in report["effort_curve"])


def test_no_heldout_task_used_for_selection():
    heldout = generate_evidence_search_pool(split="heldout", draws=range(6))
    assert set(row["world_id"] for row in heldout.opportunities).isdisjoint(
        row["world_id"] for row in generate_evidence_search_pool(
            split="train", draws=range(6)).opportunities)
    with pytest.raises(ValueError, match="selector access is forbidden"):
        selector_views(heldout)
    assert all("solvable" not in row and "witness" not in row
               for row in heldout.task_pool())


def test_scorer_only_solvability_and_structural_strata_are_separate():
    pool = generate_evidence_search_pool(split="train", draws=range(12))
    labels = {row["world_id"]: row for row in pool.scorer_only}
    assert {row["relation_class"] for row in pool.scorer_only} == {
        "latent", "repeated", "irrelevant", "transferable", "unlearnable", "partial"}
    assert {row["family"] for row in pool.opportunities} == {
        "cyclic_relation", "branching_relation"}
    assert any(not row["solvable"] for row in pool.scorer_only)
    assert set(labels) == {row["world_id"] for row in pool.opportunities}
    assert all("solvable" not in row and "relation_class" not in row
               for row in pool.opportunities)


def test_repeated_and_transferable_relations_are_world_owned():
    pool = generate_evidence_search_pool(split="train", draws=range(24), seed=77)
    repeated = [row for row in pool.scorer_only if row["relation_class"] == "repeated"]
    assert len({row["relation_signature"] for row in repeated
                if row["world_id"].split(":")[1] == "cyclic_relation"}) == 1
    transferable = [row for row in pool.opportunities if row["draw"] % 6 == 3]
    assert {row["family"] for row in transferable} == {
        "cyclic_relation", "branching_relation"}
    for task in transferable:
        initial = task["initial_state"]
        state_count = 7 if task["family"] == "cyclic_relation" else 9
        assert task["primitive_affordances"]["act_0"][str(initial)] == (initial + 1) % state_count


def test_cost_curve_uses_fixed_geometric_effort_ceilings():
    assert EFFORT_CEILINGS == (1, 2, 4, 8, 16, 32, 64)
    with pytest.raises(ValueError, match="strictly increasing"):
        search_cost_curve({"world_id": "x", "initial_state": 0, "goal_state": 1,
            "primitive_affordances": {"a": {}}, "transition_model": ()}, ceilings=(2, 1))
