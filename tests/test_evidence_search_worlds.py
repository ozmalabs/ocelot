from __future__ import annotations

import pytest

from evaluation.process_mastery.evidence_search_worlds import (
    EFFORT_CEILINGS, EvidenceSearchPool, EvidenceSearchWorld, generate_evidence_search_pool,
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
    with pytest.raises(TypeError):
        pool.opportunities[0]["goal_state"] = -1


def test_goal_not_active_operator_function():
    pool = generate_evidence_search_pool(split="development", draws=range(30), seed=2026)
    for task, world_model in zip(pool.opportunities, pool.scorer_only):
        start = tuple(task["initial_state"])
        one_step = set()
        for permutation in world_model["action_effects"].values():
            target = [None] * len(start)
            for source, destination in enumerate(permutation):
                target[destination] = start[source]
            one_step.add(tuple(target))
        assert task["goal_state"] not in one_step
        assert "transition_model" not in task and "action_effects" not in task
        assert all("after_value" not in opportunity
                   for opportunity in task["evidence_opportunities"])


def test_finite_space_reports_exhaustion():
    task = {"world_id": "dead-end", "initial_state": (0, 1), "goal_state": (1, 0),
        "primitive_affordances": ("a", "b")}
    world_model = {"action_effects": {}}
    report = search_cost_curve(task, world_model=world_model, ceilings=(1, 2, 4, 8))
    assert report["finite_space_exhausted"] is True
    assert report["finite_space_exhaustion_work"] == 2
    assert report["attempts"] == 2
    assert [row["effort_ceiling"] for row in report["effort_curve"]] == [1, 2, 4, 8]


def test_all_search_costs_and_failures_counted():
    task = {"world_id": "mixed", "initial_state": (0, 1), "goal_state": (1, 0),
        "primitive_affordances": ("a", "b")}
    world_model = {"action_effects": {"a": (1, 0), "b": (0, 1)}}
    report = search_cost_curve(task, world_model=world_model, ceilings=(1, 2, 4, 8))
    assert report["attempts"] == 8
    assert report["unique_effect_coverage"] > 0
    assert report["failed_or_invalid_attempts"] < 8
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
    assert all("transition_model" not in row for row in heldout.task_pool())


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
    transferable = [(task, scorer) for task, scorer in zip(pool.opportunities, pool.scorer_only)
                   if task["draw"] % 6 == 3]
    assert {task["family"] for task, _scorer in transferable} == {
        "cyclic_relation", "branching_relation"}
    for task, scorer in transferable:
        initial = tuple(task["initial_state"])
        state_count = 7 if task["family"] == "cyclic_relation" else 9
        permutation = scorer["action_effects"]["act_0"]
        rotated = [None] * len(initial)
        for source, destination in enumerate(permutation):
            rotated[destination] = initial[source]
        assert tuple(rotated) == tuple(initial[(index - 1) % state_count]
                                        for index in range(state_count))


def test_world_receipt_boundary_hides_outcome_until_execution():
    pool = generate_evidence_search_pool(split="train", draws=(0,), seed=321)
    task = pool.task_pool()[0]
    world_model = pool.scorer_only[0]
    opportunity = task["evidence_opportunities"][0]
    world = EvidenceSearchWorld(task, world_model)
    assert "after_value" not in opportunity
    receipt = world.execute(opportunity)
    assert receipt.status == "observed" and receipt.action_authorized
    assert receipt.before_value == opportunity["before_value"]
    assert world.verify_receipt(receipt)
    assert not world.verify_receipt(object())


def test_cost_curve_uses_fixed_geometric_effort_ceilings():
    assert EFFORT_CEILINGS == (1, 2, 4, 8, 16, 32, 64)
    with pytest.raises(ValueError, match="strictly increasing"):
        search_cost_curve({"world_id": "x", "initial_state": (0, 1), "goal_state": (1, 0),
            "primitive_affordances": ("a",)}, world_model={"action_effects": {}},
            ceilings=(2, 1))
