"""Deterministic 2x2x2 cube and 3x3 sliding worlds for PMB family (a).

These are world-side mechanics and score oracles only. Task records expose the
initial state, goal, and primitive affordances; they never expose the scramble
sequence or a solution path.
"""
from __future__ import annotations

import itertools
import random


def _rot90(v, axis, quarter):
    x, y, z = v
    if axis == 0:
        return (x, -z, y) if quarter == 1 else (x, z, -y)
    if axis == 1:
        return (z, y, -x) if quarter == 1 else (-z, y, x)
    return (-y, x, z) if quarter == 1 else (y, -x, z)


_COORDS = tuple(itertools.product((-1, 1), repeat=3))
_NORMALS = tuple(n for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                             (0, -1, 0), (0, 0, 1), (0, 0, -1)))
_STICKERS = tuple((coord, normal) for coord in _COORDS for normal in _NORMALS
                  if sum(abs(a) for a in normal) == 1 and
                  sum(coord[i] * normal[i] for i in range(3)) == 1)
_STICKER_INDEX = {item: i for i, item in enumerate(_STICKERS)}


def cube_moves() -> dict[str, tuple[int, ...]]:
    """Return the twelve quarter turns as old-position -> new-position maps."""
    moves = {}
    for axis, axis_name in enumerate("XYZ"):
        for sign in (-1, 1):
            face = axis_name + ("-" if sign < 0 else "+")
            for direction in (-1, 1):
                name = face + ("'" if direction < 0 else "")
                perm = list(range(len(_STICKERS)))
                quarter = direction
                for i, (coord, normal) in enumerate(_STICKERS):
                    if coord[axis] == sign:
                        new_coord = _rot90(coord, axis, quarter)
                        new_normal = _rot90(normal, axis, quarter)
                        perm[i] = _STICKER_INDEX[(new_coord, new_normal)]
                moves[name] = tuple(perm)
    return moves


def _apply_position_map(state, permutation):
    out = [None] * len(state)
    for old, new in enumerate(permutation):
        out[new] = state[old]
    return tuple(out)


def cube_apply(state, move):
    permutation = cube_moves()[move] if isinstance(move, str) else move
    return _apply_position_map(tuple(state), permutation)


def cube_scramble(seed: int, length: int = 20):
    moves = cube_moves()
    names = sorted(moves)
    rng = random.Random(seed)
    state = tuple(range(24))
    previous_face = None
    for _ in range(length):
        available = [name for name in names if name[:2] != previous_face]
        name = rng.choice(available)
        state = cube_apply(state, moves[name])
        previous_face = name[:2]
    return state


def cube_task(seed: int, length: int = 20):
    return {"family": "cube_2x2x2", "seed": int(seed),
            "initial_state": cube_scramble(seed, length), "goal_state": tuple(range(24)),
            "primitive_affordances": cube_moves()}


def cube_solved(state):
    return tuple(state) == tuple(range(24))


_SLIDE_EDGES = tuple((i, j) for i in range(9) for j in (i + 1, i + 3)
                     if j < 9 and (j == i + 3 or i // 3 == j // 3))


def sliding_moves():
    return {f"swap_{i}_{j}": tuple(j if k == i else i if k == j else k
                                    for k in range(9)) for i, j in _SLIDE_EDGES}


def sliding_apply(state, move):
    """Apply one adjacent transposition; reject it unless it swaps the blank."""
    perm = sliding_moves()[move] if isinstance(move, str) else tuple(move)
    changed = [i for i, target in enumerate(perm) if i != target]
    if len(changed) != 2 or 0 not in (state[changed[0]], state[changed[1]]):
        raise ValueError("illegal sliding move: transposition does not include the blank")
    return _apply_position_map(tuple(state), perm)


def sliding_scramble(seed: int, length: int = 30):
    rng = random.Random(seed)
    state = tuple(range(1, 9)) + (0,)
    previous = None
    moves = sliding_moves()
    for _ in range(length):
        blank = state.index(0)
        options = [(name, perm) for name, perm in moves.items()
                   if blank in [i for i, target in enumerate(perm) if i != target]
                   and name != previous]
        name, perm = rng.choice(options)
        state = sliding_apply(state, perm)
        previous = name
    return state


def sliding_reachable(state, goal=(1, 2, 3, 4, 5, 6, 7, 8, 0)):
    def inversions(values):
        tiles = [x for x in values if x]
        return sum(tiles[i] > tiles[j] for i in range(len(tiles)) for j in range(i + 1, len(tiles)))
    # Odd-width boards are reachable exactly when inversion parity agrees.
    return inversions(state) % 2 == inversions(goal) % 2


def sliding_solved(state):
    return tuple(state) == (1, 2, 3, 4, 5, 6, 7, 8, 0)


def sliding_task(seed: int, length: int = 30):
    return {"family": "sliding_3x3", "seed": int(seed),
            "initial_state": sliding_scramble(seed, length),
            "goal_state": (1, 2, 3, 4, 5, 6, 7, 8, 0),
            "primitive_affordances": sliding_moves()}


def puzzle_panel(family: str, *, first_seed=1_000_000, tasks=200, controls=100):
    """Create fixed-size task/control ID allocations without exposing answers."""
    maker = cube_task if family == "cube_2x2x2" else sliding_task if family == "sliding_3x3" else None
    if maker is None:
        raise ValueError(f"unsupported puzzle family: {family}")
    rows = [maker(first_seed + i) for i in range(tasks)]
    control_rows = []
    for i in range(controls):
        task = maker(first_seed + tasks + i)
        if family == "sliding_3x3":
            task["initial_state"] = (2, 1, 3, 4, 5, 6, 7, 8, 0)
            task["control_status"] = "unreachable" if not sliding_reachable(task["initial_state"]) else "reachable"
        else:
            task["control_status"] = "illegal_action"
            task["requested_action"] = "illegal_face_turn"
        control_rows.append(task)
    return {"family": family, "tasks": rows, "controls": control_rows}
