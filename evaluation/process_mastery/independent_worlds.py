"""Independent P22 task worlds whose goal generation omits checkpoint index."""
from __future__ import annotations

import random

from evaluation.process_mastery.generators import loopover_moves


_SPLIT_BLOCK = {"train": 0, "selection": 1, "validation": 2, "heldout": 3}
_D4 = ("identity", "rot90", "rot180", "rot270",
       "flip_r", "flip_c", "transpose", "anti_transpose")


def p22_seed(*, family_code: int, split: str, draw: int) -> int:
    if split not in _SPLIT_BLOCK or draw < 0 or draw >= 1000:
        raise ValueError("unknown split or draw outside its reserved block")
    if family_code <= 0:
        raise ValueError("family_code must be positive")
    return 10_000_000 + 22 * 1_000_000 + family_code * 10_000 + _SPLIT_BLOCK[split] * 1_000 + draw


def _coordinate_map(name: str, size: int) -> tuple[int, ...]:
    last = size - 1
    transforms = {
        "identity": lambda r, c: (r, c),
        "rot90": lambda r, c: (c, last - r),
        "rot180": lambda r, c: (last - r, last - c),
        "rot270": lambda r, c: (last - c, r),
        "flip_r": lambda r, c: (last - r, c),
        "flip_c": lambda r, c: (r, last - c),
        "transpose": lambda r, c: (c, r),
        "anti_transpose": lambda r, c: (last - c, last - r),
    }
    fn = transforms[name]
    mapping = []
    for row in range(size):
        for col in range(size):
            nr, nc = fn(row, col)
            mapping.append(nr * size + nc)
    return tuple(mapping)


def _compose_params(first: tuple[int, ...], second: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(second[first[index]] for index in range(len(first)))


def _apply_params(initial: list[int], params: tuple[int, ...]) -> list[int]:
    result = [None] * len(initial)
    for source, destination in enumerate(params):
        result[destination] = initial[source]
    return result


def generate_loopover_world(*, split: str, draw: int) -> dict:
    """Create a Loopover task from two visible row/column shift primitives."""
    seed = p22_seed(family_code=1, split=split, draw=draw)
    rng = random.Random(seed)
    held_names = ("R0", "C1")
    moves = loopover_moves(3)
    held = {name: tuple(moves[name]) for name in held_names}
    order = held_names if rng.randrange(2) == 0 else tuple(reversed(held_names))
    target = _compose_params(held[order[0]], held[order[1]])
    initial = list(range(9))
    return {"family": "pmb_generated_loopover_v1", "split": split,
            "seed": seed, "draw": draw,
            "world_id": f"p22:loopover:{split}:{draw:04d}",
            "initial_state": initial, "goal_state": _apply_params(initial, target),
            "held_processes": {name: list(params) for name, params in held.items()},
            "hidden_transform_order": list(order),
            "hidden_target_params": list(target), "target_solution_exposed": False}


def generate_d4_world(*, split: str, draw: int) -> dict:
    """Create a 2x2 global-symmetry task from two visible primitive transforms.

    The evaluator record retains the target expression; `agent_view` withholds
    it. The world/goal is stable across checkpoint generations.
    """
    family_code = 2
    seed = p22_seed(family_code=family_code, split=split, draw=draw)
    rng = random.Random(seed)
    held_names = ("rot90", "flip_r")
    target_order = ("rot90", "flip_r") if rng.randrange(2) == 0 else ("flip_r", "rot90")
    held = {name: _coordinate_map(name, 2) for name in held_names}
    # Compose under the same destination-index convention as native ProcessCompose.
    target = _compose_params(held[target_order[0]], held[target_order[1]])
    initial = [0, 1, 2, 3]
    goal = _apply_params(initial, target)
    return {
        "family": "pmb_generated_d4_corner_v1", "split": split, "seed": seed,
        "draw": draw, "world_id": f"p22:d4:{split}:{draw:04d}",
        "initial_state": initial, "goal_state": goal,
        "held_processes": {name: list(params) for name, params in held.items()},
        "hidden_transform_order": list(target_order),
        "hidden_target_params": list(target),
        "target_solution_exposed": False,
    }


def agent_view(world: dict) -> dict:
    return {key: world[key] for key in (
        "family", "split", "seed", "draw", "world_id", "initial_state",
        "goal_state", "held_processes")}
