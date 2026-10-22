import pytest

from evaluation.process_mastery.native_world_comparators import NativeWorldAdapter
from evaluation.process_mastery.puzzle_worlds import sliding_moves, tool_goal_task
from tests.test_cognition_multistep_planner_migrated import _graph_planner, _run_to_fixpoint


def _one_move_sliding_task():
    goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)
    perm = sliding_moves()["swap_5_8"]
    initial = tuple(goal[perm.index(i)] for i in range(9))
    return {"family": "sliding_3x3", "seed": 71, "initial_state": initial,
            "goal_state": goal, "primitive_affordances": sliding_moves()}


def test_equal_primitive_access():
    world = NativeWorldAdapter.from_task(_one_move_sliding_task(), world_id="paired-1")
    baseline_access = world.primitive_access()
    learned_access = world.primitive_access()
    assert baseline_access == learned_access
    assert baseline_access["legal_actions"] == ("swap_2_5", "swap_4_5", "swap_5_8")


def test_illegal_sliding_move_rejected():
    world = NativeWorldAdapter.from_task(_one_move_sliding_task())
    with pytest.raises(ValueError, match="illegal"):
        world.transition(world.state, "swap_0_8")


def test_observed_receipt_matches_world():
    world = NativeWorldAdapter.from_task(_one_move_sliding_task(), world_id="world-9")
    receipt = world.transition(world.state, "swap_5_8")
    assert receipt["observed_state"] == world.goal
    assert world.verify_receipt(receipt)
    tampered = {**receipt, "observed_state": world.state}
    assert not world.verify_receipt(tampered)


def test_finite_tool_legality_depends_on_state():
    task = tool_goal_task(83)
    task["legal_actions_by_state"] = {",".join(map(str, task["initial_state"])): ["tool_left"]}
    world = NativeWorldAdapter.from_task(task)
    assert world.legal_actions(world.state) == ("tool_left",)
    with pytest.raises(ValueError, match="illegal"):
        world.transition(world.state, "tool_middle")


def test_world_adapter_present_even_for_unsolvable_instance():
    world = NativeWorldAdapter.from_task({
        "family": "sliding_3x3", "seed": 73,
        "initial_state": (2, 1, 3, 4, 5, 6, 7, 8, 0),
        "goal_state": (1, 2, 3, 4, 5, 6, 7, 8, 0),
        "primitive_affordances": sliding_moves()})
    assert world.primitive_access()["world_id"] == "sliding_3x3:73"
    assert len(world.primitive_access()["legal_actions"]) == 2


def test_primitive_search_executes_real_path():
    world = NativeWorldAdapter.from_task(_one_move_sliding_task(), world_id="search-path")
    transitions = []
    for action in world.legal_actions(world.state):
        state = world._apply(world.state, action)
        transitions.append(("s0", action, "goal" if state == world.goal else f"dead:{action}", 2))
    planner, request, _ = _graph_planner(transitions, required_horizon=1.0)
    planner.inner.set_attr(request, "model_complete", 1.0)
    _run_to_fixpoint(planner)
    assert planner.s.node(request)["attrs"]["status"] == "solved"
    candidate = planner.inner.neighbours(request, "has_imagined_plan_candidate")[0]
    arrival = planner.inner.neighbours(candidate, "has_terminal_path_arrival")[0]
    action = planner.s.node(arrival)["attrs"]["action_key"]
    receipt = world.transition(world.state, action)
    assert receipt["observed_state"] == world.goal
    assert world.verify_receipt(receipt)


def test_failed_search_not_missing_adapter():
    world = NativeWorldAdapter.from_task({
        "family": "sliding_3x3", "seed": 79,
        "initial_state": (2, 1, 3, 4, 5, 6, 7, 8, 0),
        "goal_state": (1, 2, 3, 4, 5, 6, 7, 8, 0),
        "primitive_affordances": sliding_moves()})
    transitions = [("s0", action, f"dead:{action}", 2)
                   for action in world.legal_actions(world.state)]
    planner, request, _ = _graph_planner(transitions, required_horizon=1.0)
    planner.inner.set_attr(request, "model_complete", 1.0)
    _run_to_fixpoint(planner)
    assert world.primitive_access()["world_id"] == "sliding_3x3:79"
    assert planner.s.node(request)["attrs"]["status"] == "exhausted"
    assert planner.s.node(request)["attrs"].get("terminal_reason") != "missing_adapter"
