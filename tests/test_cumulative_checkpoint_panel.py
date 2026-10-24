import pytest

from evaluation.process_mastery.cumulative_checkpoint_panel import (
    ablate_component, score_common_world_panel, world_allocation_digest,
)
from evaluation.process_mastery.scheduled_learning_checkpoints import (
    capture_scheduled_checkpoint,
)


WORLD_SHA = "a" * 64


def _sequence(arm, predictions, world_sha=WORLD_SHA):
    seq = []
    parent = None
    for index, name in enumerate(("g0", "g1", "g2", "g3")):
        graph = {"nodes": [{"id": "prediction", "attrs": {
            "p27_component": "learned_distinctions",
            "predictions": predictions[index]}}], "edges": []}
        work = (0, 1000, 2000, 4000)[index]
        counters = {"primitive_work": work, "source_exposure": 0,
            "native_rule_steps": index, "graph_bytes": len(__import__("json").dumps(
                graph, sort_keys=True, separators=(",", ":")).encode()),
            "budget_debits": index, "task_world_accesses": index}
        parent = capture_scheduled_checkpoint(arm=arm, checkpoint=name,
            native_graph=graph, cumulative=counters,
            interval_status="initial" if index == 0 else "progress",
            parent=parent, world_allocation_sha256=world_sha)
        seq.append(parent)
    return tuple(seq)


def test_common_test_worlds_at_each_checkpoint():
    worlds = [{"world_id": "sealed-1", "split": "heldout", "goal_state": [2]},
              {"world_id": "sealed-2", "split": "heldout", "goal_state": [1]}]
    allocation_sha = world_allocation_digest(worlds)
    checkpoints = {arm: _sequence(arm, [[1], [1], [2], [2]], allocation_sha)
        for arm in ("frozen_ancestor", "combined")}
    result = score_common_world_panel(checkpoints=checkpoints, worlds=worlds,
        native_predictor=lambda graph, world: graph["nodes"][0]["attrs"]["predictions"])
    assert result["status"] == "COMPLETED"
    assert len(result["rows"]) == 16
    assert {row["world_id"] for row in result["rows"]} == {"sealed-1", "sealed-2"}
    assert all(row["checkpoint"] in {"g0", "g1", "g2", "g3"} for row in result["rows"])


def test_no_scoring_feedback_into_training_and_missing_output_retained():
    worlds = [{"world_id": "sealed", "split": "validation", "goal_state": [1]},
              {"world_id": "sealed-missing", "split": "validation", "goal_state": [1]}]
    checkpoints = {"combined": _sequence("combined", [[1], [1], [1], [1]],
                                          world_allocation_digest(worlds))}
    result = score_common_world_panel(checkpoints=checkpoints, worlds=worlds,
        native_predictor=lambda graph, world: None if world["world_id"].endswith("missing")
            else graph["nodes"][0]["attrs"]["predictions"])
    missing = [row for row in result["rows"] if row["prediction_missing"]]
    assert len(missing) == 4
    assert all(row["score"] is None for row in missing)
    assert result["score_feedback_to_training"] is False


def test_evicted_content_stays_unavailable_to_prediction_query():
    world = {"world_id": "sealed", "split": "heldout", "goal_state": [1]}
    checkpoints = {"combined": _sequence("combined", [[1], [1], [1], [1]],
                                          world_allocation_digest([world]))}
    seen = []
    result = score_common_world_panel(checkpoints=checkpoints, worlds=[world],
        native_predictor=lambda graph, _world: seen.append(
            graph["nodes"][0]["attrs"].get("prediction")) or
            graph["nodes"][0]["attrs"].get("prediction"))
    assert len(result["rows"]) == 4
    assert seen == [None] * 4


def test_component_ablation_follows_actual_path():
    graph = {"nodes": [
        {"id": "learned", "attrs": {"p27_component": "learned_distinctions",
                                      "prediction": [2]}},
        {"id": "base", "attrs": {"prediction": [1]}},
    ], "edges": [{"from": "learned", "to": "base"}]}
    ablated = ablate_component(graph, "learned_distinctions")
    assert [node["id"] for node in ablated["nodes"]] == ["base"]
    assert ablated["edges"] == []
    assert len(graph["nodes"]) == 2


def test_missing_or_pending_output_retained_and_training_blocked():
    world = {"world_id": "train", "split": "train", "goal_state": [1]}
    checkpoints = {"combined": _sequence("combined", [[1], [1], [1], [1]],
                                          world_allocation_digest([world]))}
    with pytest.raises(ValueError, match="validation or heldout"):
        score_common_world_panel(checkpoints=checkpoints,
            worlds=[world],
            native_predictor=lambda _graph, _world: None)
