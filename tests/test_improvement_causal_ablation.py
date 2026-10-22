from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter,
)
from evaluation.process_mastery.harness import Agent
from tests.test_open_process_search import _compose


def test_component_ablation_changes_claimed_path():
    agent = Agent(track_i=False)
    adapter = CheckpointWorldAdapter(agent.native, primitive_work_ceiling=8)
    left, right = [1, 0, 2, 3], [0, 2, 1, 3]
    full = CheckpointExpression("full", "ancestor", "full-expression",
                                tuple(_compose(agent, left, right)), 2)
    ablated = CheckpointExpression("component-ablated", "ancestor", "left-only",
                                   tuple(left), 2)
    world = {"world_id": "causal-control", "initial_state": [0, 1, 2, 3],
             "goal_state": [1, 2, 0, 3]}
    full_result = adapter.score(full, **world)
    ablated_result = adapter.score(ablated, **world)
    assert full_result["score"] == 1
    assert ablated_result["score"] == 0
    assert full_result["expression_digest"] != ablated_result["expression_digest"]
