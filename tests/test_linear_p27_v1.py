from evaluation.process_mastery.linear_p27_v1 import (
    ARMS, FAMILIES, TRAIN_DRAWS, _panel_worlds, _train_arm, allocation,
)


def test_p27_seed_matrices_are_exact_and_disjoint():
    development = allocation("development")
    heldout = allocation("heldout")
    assert development["arms"] == list(ARMS)
    assert development["families"] == list(FAMILIES)
    assert heldout["test_worlds_per_family"] == 200
    assert heldout["validation_worlds_per_family"] == 200
    assert heldout["integrity_control_count"] == 100
    dev = {seed for row in development["families_allocation"]
        for key in ("training_world_seeds", "test_world_seeds", "validation_world_seeds")
        for seed in row[key]}
    hold = {seed for row in heldout["families_allocation"]
        for key in ("training_world_seeds", "test_world_seeds", "validation_world_seeds")
        for seed in row[key]}
    assert not dev & hold
    assert all(row["training_draws"] == list(TRAIN_DRAWS)
               for row in heldout["families_allocation"])


def test_generated_p27_panels_match_declared_seeds_and_transferable_effect():
    for split in ("development", "heldout"):
        plan = allocation(split)
        for family_row in plan["families_allocation"]:
            panel_split = "development" if split == "development" else "heldout"
            worlds = _panel_worlds(family=family_row["family"], split=panel_split,
                seed=family_row["test_pool_seed"], draws=family_row["test_draws"])
            realized = [int(world["world_id"].split(":")[-2]) for world in worlds]
            assert realized == family_row["test_world_seeds"]
            assert len({world["expected_after_value"] for world in worlds}) == 1
            assert all(world["draw"] % 6 == 3 for world in worlds)


def test_native_process_search_arm_preserves_nonactionable_checkpoints():
    plan = allocation("development")
    family = plan["families_allocation"][0]
    result = _train_arm(family=family["family"], arm="process_search_only",
        training_seed=family["training_pool_seed"], world_allocation_sha256="a" * 64)
    assert [row["checkpoint"] for row in result["checkpoints"]] == ["g0", "g1", "g2", "g3"]
    assert len(result["search_rows"]) == 4
    assert result["approval_count"] == 0
    assert result["world_receipt_count"] == 0
    assert all(row["attempts_added"] <= 1 for row in result["search_rows"])
    assert all(not cp["actionable"] for cp in result["checkpoints"])


def test_evidence_selection_arm_uses_same_pool_and_exact_receipts():
    plan = allocation("development")
    family = plan["families_allocation"][0]
    result = _train_arm(family=family["family"], arm="evidence_selection_only",
        training_seed=family["training_pool_seed"], world_allocation_sha256="b" * 64)
    assert result["baseline_receipts"]
    assert len(result["training_opportunity_ids"]) == 4 * len(
        __import__("evaluation.process_mastery.evidence_search_worlds",
            fromlist=["generate_evidence_search_pool"]).generate_evidence_search_pool(
                split="train", draws=(13,), seed=family["training_pool_seed"],
                family=family["family"]).task_pool()[0]["evidence_opportunities"])
    selected = [row for row in result["selection_rows"] if row.get("receipt_event_id")]
    assert len(selected) == 4
    assert result["approval_count"] == 0
    assert result["world_receipt_count"] == 0
