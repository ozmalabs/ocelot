import pytest

from evaluation.process_mastery.improvement_estimand import (
    paired_generation_deltas, summarize_family, validate_efficiency_match,
)


def _rows(scores, *, work=5):
    rows = []
    for generation, (candidate, ancestor) in enumerate(scores, 1):
        for world in ("w1", "w2", "w3"):
            rows.extend([
                {"family": "perm", "generation": generation, "world_id": world,
                 "goal_id": f"{world}:fixed-goal", "arm": "full",
                 "score": candidate, "primitive_work": work},
                {"family": "perm", "generation": generation, "world_id": world,
                 "goal_id": f"{world}:fixed-goal", "arm": "unchanged",
                 "score": ancestor, "primitive_work": work},
            ])
    return rows


def test_ceiling_flat_is_zero_improvement():
    result = summarize_family(_rows([(1, 1), (1, 1), (1, 1)]), family="perm",
                              bootstrap_draws=200)
    assert result["paired_gain_by_generation"] == [0, 0, 0]
    assert result["final_paired_gain"] == 0
    assert result["generation_slope"] == 0
    assert result["generation_slope_one_sided_99_lower"] == 0


def test_ancestor_same_worlds():
    rows = _rows([(0.8, 0.5), (0.7, 0.5), (0.9, 0.5)])
    deltas = paired_generation_deltas(rows)
    assert set(deltas[("perm", 1)]) == {"w1", "w2", "w3"}
    assert list(deltas[("perm", 1)].values()) == pytest.approx([0.3] * 3)


def test_generation_not_goal_parameter():
    rows = _rows([(0.5, 0.5), (0.5, 0.5), (0.5, 0.5)])
    for world in ("w1", "w2", "w3"):
        goals = {r["goal_id"] for r in rows if r["world_id"] == world}
        assert goals == {f"{world}:fixed-goal"}


def test_cost_mismatch_blocks_efficiency_claim():
    rows = _rows([(0.6, 0.5)] * 3)
    matched, _ = validate_efficiency_match(rows)
    assert matched
    rows[0]["primitive_work"] += 1
    matched, receipt = validate_efficiency_match(rows)
    assert not matched
    assert receipt["reason"] == "cost_mismatch"


def test_pair_cluster_preserved():
    rows = _rows([(0.4, 0.2), (0.6, 0.2), (0.8, 0.2)])
    result = summarize_family(rows, family="perm", bootstrap_draws=300, seed=4)
    assert result["world_clusters"] == 3
    assert result["bootstrap_unit"] == "world_id_cluster"
    assert result["paired_gain_by_generation"] == pytest.approx([0.2, 0.4, 0.6])
    assert result["generation_slope"] == pytest.approx(0.2)
