from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter,
)
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world, generate_loopover_world, p22_seed,
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


def test_d4_worlds_are_fixed_across_checkpoints_and_not_answer_leaking():
    train = generate_d4_world(split="train", draw=4)
    repeated = generate_d4_world(split="train", draw=4)
    heldout = generate_d4_world(split="heldout", draw=4)
    assert train == repeated
    assert train["world_id"] == agent_view(train)["world_id"]
    assert "hidden_transform_order" not in agent_view(train)
    assert "hidden_target_params" not in agent_view(train)
    assert train["seed"] != heldout["seed"]
    assert p22_seed(family_code=2, split="train", draw=4) == train["seed"]


def test_d4_goal_matches_native_process_composition():
    agent, adapter = _adapter()
    world = generate_d4_world(split="train", draw=9)
    first, second = world["hidden_transform_order"]
    left = world["held_processes"][first]
    right = world["held_processes"][second]
    composed = agent.native.evaluate(
        {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
         "b": {"type": "Var", "name": "b"}}, {"a": left, "b": right})
    checkpoint = CheckpointExpression("d4-composed", "ancestor", "d4-expression",
                                      tuple(composed), 2)
    scored = adapter.score(checkpoint, world_id=world["world_id"],
                           initial_state=world["initial_state"],
                           goal_state=world["goal_state"])
    assert scored["score"] == 1


def test_loopover_goal_matches_native_process_composition():
    agent, adapter = _adapter()
    world = generate_loopover_world(split="train", draw=11)
    first, second = world["hidden_transform_order"]
    composed = agent.native.evaluate(
        {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
         "b": {"type": "Var", "name": "b"}},
        {"a": world["held_processes"][first],
         "b": world["held_processes"][second]})
    checkpoint = CheckpointExpression("loopover-composed", "ancestor",
                                      "loopover-expression", tuple(composed), 2)
    scored = adapter.score(checkpoint, world_id=world["world_id"],
                           initial_state=world["initial_state"],
                           goal_state=world["goal_state"])
    assert scored["score"] == 1
    assert len(world["initial_state"]) == 9
