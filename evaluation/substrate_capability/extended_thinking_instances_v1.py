"""Seeded synthetic instance families for the P3 extended-thinking evaluation."""
from __future__ import annotations

import random

BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]
DIM_TYPES = ["pred", "coord:r", "coord:c"]
DIM_TYPES_VALUE = ["pred", "coord:r", "coord:c", "val"]
TETROMINOS = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
)
PENTOMINOS = (
    ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2)),
)
DIHEDRAL = {(1, 0, 0, 1), (0, -1, 1, 0), (-1, 0, 0, -1),
            (0, 1, -1, 0), (-1, 0, 0, 1), (1, 0, 0, -1),
            (0, 1, 1, 0), (0, -1, -1, 0)}


def _normalise(points):
    mr = min(r for r, _ in points)
    mc = min(c for _, c in points)
    return sorted((r - mr, c - mc) for r, c in points)


def _transform(points, kind, k=1):
    return _normalise([_raw_transform_point(r, c, kind, k) for r, c in points])


def _raw_transform_point(r, c, kind, k=1):
        if kind == "rotation90":
            for _ in range(k % 4):
                r, c = c, -r
        elif kind == "reflection_r":
            r = -r
        elif kind == "reflection_c":
            c = -c
        return r, c


def _rows(points, colour=None):
    if colour is None:
        return [["cell", r, c] for r, c in points]
    return [["cell", r, c, colour] for r, c in points]


def _expanded_base(rng):
    candidates = [shape for shape in TETROMINOS + PENTOMINOS
                  if any(_transform(shape, kind, k) != _normalise(shape)
                         for kind, k in (("rotation90", 1), ("rotation90", 2),
                                         ("rotation90", 3), ("reflection_r", 1),
                                         ("reflection_c", 1)))]
    shape = rng.choice(candidates)
    base = [(2 * r + dr, 2 * c + dc) for r, c in shape for dr in (0, 1) for dc in (0, 1)]
    return shape, base


def family_a(seed: int) -> dict:
    """A grain ladder case: the exact transform fails, grain one recovers it."""
    rng = random.Random(int(seed))
    shape, base = _expanded_base(rng)
    held_options = [("rotation90", k) for k in (1, 2, 3)]
    held_options.extend((kind, 1) for kind in ("reflection_r", "reflection_c"))
    held_options = [(kind, k) for kind, k in held_options
                    if _transform(base, kind, k) != _normalise(base)]
    held_kind, k = rng.choice(held_options)
    goal = set(_transform(base, held_kind, k))
    raw_transformed = [_raw_transform_point(r, c, held_kind, k) for r, c in base]
    mr = min(r for r, _ in raw_transformed)
    mc = min(c for _, c in raw_transformed)

    # Remove one or two subcells while retaining every coarse block. This makes
    # full-resolution equality fail while grain-one requantisation is unchanged.
    block_ids = list(shape)
    rng.shuffle(block_ids)
    for br, bc in block_ids[:rng.randint(1, 2)]:
        cell = rng.choice(((0, 0), (0, 1), (1, 0), (1, 1)))
        point = (2 * br + cell[0], 2 * bc + cell[1])
        raw_point = _raw_transform_point(*point, held_kind, k)
        transformed_point = (raw_point[0] - mr, raw_point[1] - mc)
        goal.discard(transformed_point)

    return {"family": "A", "seed": int(seed), "base": _rows(base),
            "goal": _rows(sorted(goal)), "dim_types": DIM_TYPES,
            "transform": {"kind": held_kind, "k": k},
            "expected_winner": "dim_grain"}


def family_b(seed: int) -> dict:
    """A full-rank non-dihedral integer-linear generator discovery case."""
    rng = random.Random(int(seed))
    mats = [m for m in ((a, b, c, d) for a in range(-2, 3) for b in range(-2, 3)
                        for c in range(-2, 3) for d in range(-2, 3))
            if abs(m[0] * m[3] - m[1] * m[2]) == 1 and m not in DIHEDRAL]
    matrix = rng.choice(mats)
    points = [(row[1], row[2]) for row in BASE]
    transformed = _normalise([(matrix[0] * r + matrix[1] * c,
                               matrix[2] * r + matrix[3] * c) for r, c in points])
    return {"family": "B", "seed": int(seed), "base": [list(x) for x in BASE],
            "goal": _rows(transformed, "red"), "dim_types": DIM_TYPES_VALUE,
            "matrix": list(matrix), "expected_winner": "gen_linear"}


def control_a(seed: int, count: int | None = None) -> dict:
    rng = random.Random(int(seed))
    held = family_a(seed)
    n = int(count if count is not None else len(held["goal"]))
    coords = rng.sample([(r, c) for r in range(12) for c in range(12)], n)
    return {"family": "control_a", "seed": int(seed), "base": held["base"], "goal": _rows(coords),
            "dim_types": DIM_TYPES, "expected_winner": "quantum"}


def control_b_value_noise(seed: int) -> dict:
    rng = random.Random(int(seed))
    palette = ["blue", "green", "yellow", "purple", "orange", "cyan", "magenta",
               "black", "white", "brown", "pink", "gray"]
    colours = rng.sample(palette, len(BASE))
    goal = [["cell", row[1], row[2], colours[i]] for i, row in enumerate(BASE)]
    return {"family": "control_b_value_noise", "seed": int(seed), "base": [list(x) for x in BASE],
            "goal": goal, "dim_types": DIM_TYPES_VALUE, "expected_winner": "quantum"}


def control_b_quadratic(seed: int) -> dict:
    goal = [["cell", r, c + r * r, v] for _, r, c, v in BASE]
    return {"family": "control_b_quadratic", "seed": int(seed), "goal": goal, "base": [list(x) for x in BASE],
            "dim_types": DIM_TYPES_VALUE, "expected_winner": "quantum"}


def draw(family: str, seed: int) -> dict:
    if family == "A": return family_a(seed)
    if family == "B": return family_b(seed)
    if family == "control_a": return control_a(seed)
    if family == "control_b_value_noise": return control_b_value_noise(seed)
    if family == "control_b_quadratic": return control_b_quadratic(seed)
    raise ValueError(f"unknown extended-thinking family: {family}")
