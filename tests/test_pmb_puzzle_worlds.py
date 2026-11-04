"""P10.05 deterministic family-a puzzle mechanics and leakage controls."""
import pytest

from evaluation.process_mastery.puzzle_worlds import (
    cube_apply, cube_moves, cube_solved, cube_task, puzzle_panel,
    sliding_apply, sliding_moves, sliding_reachable, sliding_solved, sliding_task,
    tool_goal_task,
)


def test_cube_moves_and_inverses():
    solved = tuple(range(24))
    moves = cube_moves()
    assert len(moves) == 12
    for name in moves:
        inverse = name + "'" if not name.endswith("'") else name[:-1]
        assert cube_solved(cube_apply(cube_apply(solved, name), inverse))
        assert len(set(moves[name])) == 24


def test_sliding_moves_legal():
    state = (1, 2, 3, 4, 5, 6, 7, 0, 8)
    moves = sliding_moves()
    legal = [name for name, perm in moves.items()
             if 0 in (state[i] for i, target in enumerate(perm) if i != target)]
    assert legal
    assert all(len(sliding_apply(state, move)) == 9 for move in legal)
    illegal = next(name for name in moves if name not in legal)
    with pytest.raises(ValueError, match="illegal sliding move"):
        sliding_apply(state, illegal)


def test_unreachable_control_distinguished():
    panel = puzzle_panel("sliding_3x3", tasks=0, controls=3)
    assert all(row["control_status"] == "unreachable" for row in panel["controls"])
    assert all(not sliding_reachable(row["initial_state"]) for row in panel["controls"])


def test_no_solution_path_ingested():
    for task in (cube_task(17), sliding_task(17), tool_goal_task(17)):
        assert "solution" not in task and "scramble_path" not in task and "moves_to_goal" not in task
        assert task["initial_state"] != task["goal_state"]
    tool = tool_goal_task(17)
    assert not any(perm == tuple(tool["goal_state"]) for perm in tool["primitive_affordances"].values())
    cube_control = puzzle_panel("cube_2x2x2", tasks=0, controls=1)["controls"][0]
    assert cube_control["requested_action"] not in cube_control["primitive_affordances"]


def test_seeded_world_reproducible():
    assert cube_task(901) == cube_task(901)
    assert sliding_task(901) == sliding_task(901)
    assert tool_goal_task(901) == tool_goal_task(901)
    assert puzzle_panel("cube_2x2x2", tasks=2, controls=1) == puzzle_panel(
        "cube_2x2x2", tasks=2, controls=1)
