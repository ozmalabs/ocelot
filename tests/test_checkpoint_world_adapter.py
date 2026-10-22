from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter,
)
from evaluation.process_mastery.harness import Agent
from tests.test_open_process_search import _compose


def _adapter():
    agent = Agent(track_i=False)
    return agent, CheckpointWorldAdapter(agent.native, primitive_work_ceiling=8)


def _checkpoints(agent, *, full_work=2, ancestor_work=2):
    left, right = [1, 0, 2, 3], [0, 2, 1, 3]
    full = CheckpointExpression("full-g1", "ancestor", "expr-full",
                                tuple(_compose(agent, left, right)), full_work)
    ancestor = CheckpointExpression("ancestor", "ancestor", "expr-ancestor",
                                    tuple(left), ancestor_work)
    return full, ancestor


def test_all_arms_same_world_and_compute():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent)
    adaptive = CheckpointExpression("adaptive", "ancestor", "expr-adaptive",
                                    full.params, 2)
    invention = CheckpointExpression("invention", "ancestor", "expr-invention",
                                     full.params, 2)
    worlds = [{"world_id": f"world-{i}", "initial_state": [0, 1, 2, 3],
               "goal_state": [1, 2, 0, 3]} for i in range(3)]
    result = adapter.compare((ancestor, adaptive, invention, full), worlds)
    assert result["same_worlds"]
    assert result["efficiency_comparable"]
    assert all([x["world_id"] for x in row["outcomes"]] == [row["world_id"]] * 4
               for row in result["rows"])


def test_changed_active_expression_changes_scored_result():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent)
    world = {"world_id": "same", "initial_state": [0, 1, 2, 3],
             "goal_state": [1, 2, 0, 3]}
    assert adapter.score(full, **world)["score"] == 1
    assert adapter.score(ancestor, **world)["score"] == 0


def test_p22_state_perturbation_changes_execution():
    agent, adapter = _adapter()
    full, _ancestor = _checkpoints(agent)
    base = {"world_id": "same-world", "initial_state": [0, 1, 2, 3],
            "goal_state": [1, 2, 0, 3]}
    perturbed = {**base, "initial_state": [3, 2, 1, 0]}
    assert adapter.score(full, **base)["result_state"] == base["goal_state"]
    assert adapter.score(full, **perturbed)["result_state"] != perturbed["goal_state"]


def test_checkpoint_restore_no_state_leak():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent)
    initial = [0, 1, 2, 3]
    world = {"world_id": "isolated", "initial_state": initial,
             "goal_state": [1, 2, 0, 3]}
    first = adapter.score(full, **world)
    second = adapter.score(full, **world)
    assert first == second
    assert initial == [0, 1, 2, 3]
