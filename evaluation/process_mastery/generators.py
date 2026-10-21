"""PMB v1 instance generators (the WORLD side of each task family).

Each generator is deterministic in its seed. Held-out splits use disjoint
seed ranges (see `SPLITS`). The world supplies: the domain's state encoding,
the actions it affords (held processes), and task instances. It never
supplies strategies, inventions or answers.
"""
from __future__ import annotations

import itertools
import random

# Disjoint seed ranges per split. Development runs use "train"; scorecards
# report "heldout" only.
SPLITS = {"train": range(0, 10_000), "heldout": range(1_000_000, 1_010_000)}


def split_seed(split: str, index: int) -> int:
    rng = SPLITS[split]
    if index >= len(rng):
        raise ValueError("split exhausted")
    return rng.start + index


# ---------------------------------------------------------------------------
# Family (a): permutation puzzles — Loopover N x N.
# ---------------------------------------------------------------------------

def loopover_moves(n: int) -> dict[str, tuple[int, ...]]:
    """Held moves of Loopover n x n: each row shifts right (R<i>) and each column
    shifts down (C<j>), plus their undo moves (R<i>', C<j>'). Permutation
    convention: content at position k moves to position p[k]."""
    moves: dict[str, tuple[int, ...]] = {}
    for i in range(n):
        p = list(range(n * n))
        for c in range(n):
            p[i * n + c] = i * n + (c + 1) % n
        moves[f"R{i}"] = tuple(p)
    for j in range(n):
        p = list(range(n * n))
        for r in range(n):
            p[r * n + j] = ((r + 1) % n) * n + j
        moves[f"C{j}"] = tuple(p)
    for name in list(moves):
        p = moves[name]
        inv = [0] * len(p)
        for a, b in enumerate(p):
            inv[b] = a
        moves[name + "'"] = tuple(inv)
    return moves


def move_tree(name: str) -> list:
    """Structured name of a held move: [family, index], e.g. R0' -> ["R'", 0]."""
    fam = name[0] + ("'" if name.endswith("'") else "")
    return [fam, int(name[1:].rstrip("'"))]


def apply_perm(state, p):
    out = [None] * len(state)
    for i, j in enumerate(p):
        out[j] = state[i]
    return out


def parity(state) -> int:
    seen, odd = set(), 0
    for i in range(len(state)):
        if i in seen:
            continue
        j, length = i, 0
        while j not in seen:
            seen.add(j)
            j = state[j]
            length += 1
        odd ^= (length - 1) & 1
    return odd


def loopover_scramble(n: int, seed: int, length: int = 30, want_parity: int | None = None) -> list[int]:
    """A scrambled board: `length` random held moves from the solved board.
    `want_parity` regenerates (deterministically) until the board's parity matches."""
    moves = loopover_moves(n)
    names = sorted(moves)
    attempt = 0
    while True:
        rng = random.Random(seed * 7919 + attempt)
        s = list(range(n * n))
        for _ in range(length):
            s = apply_perm(s, moves[rng.choice(names)])
        if s != list(range(n * n)) and (want_parity is None or parity(s) == want_parity):
            return s
        attempt += 1


# ---------------------------------------------------------------------------
# Family (c): ARC-style grid transformations (dihedral group on a shape).
# ---------------------------------------------------------------------------

D4 = ["identity", "rot90", "rot180", "rot270", "flip_r", "flip_c", "transpose", "anti_transpose"]


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def d4_apply(cells, name):
    f = {
        "identity": lambda r, c: (r, c),
        "rot90": lambda r, c: (c, -r),
        "rot180": lambda r, c: (-r, -c),
        "rot270": lambda r, c: (-c, r),
        "flip_r": lambda r, c: (-r, c),
        "flip_c": lambda r, c: (r, -c),
        "transpose": lambda r, c: (c, r),
        "anti_transpose": lambda r, c: (-c, -r),
    }[name]
    return _norm([f(r, c) for r, c in cells])


def random_shape(rng: random.Random, size: int = 6, box: int = 4):
    """A connected polyomino with no symmetry (so every D4 element is distinct)."""
    while True:
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            nr, nc = r + dr, c + dc
            if 0 <= nr < box and 0 <= nc < box:
                cells.add((nr, nc))
        cells = _norm(cells)
        if len({tuple(d4_apply(cells, g)) for g in D4}) == 8:
            return cells


def d4_task(seed: int):
    """One family-(c) instance: a held base shape and a goal that is one D4 image."""
    rng = random.Random(seed)
    base = random_shape(rng)
    g = rng.choice(D4[1:])
    return {"base": base, "transform": g, "goal": d4_apply(base, g)}


# ---------------------------------------------------------------------------
# Family (b): blicket-detector mechanism discovery.
# ---------------------------------------------------------------------------

def blicket_hypotheses(n_objects: int):
    """The hypothesis space a participant is TOLD about (as in the published
    paradigms): which objects are blickets, and whether the machine needs one
    blicket (disjunctive) or two (conjunctive)."""
    objs = list(range(n_objects))
    out = []
    for k in range(0, n_objects + 1):
        for subset in itertools.combinations(objs, k):
            out.append({"blickets": list(subset), "threshold": 1})
            if k >= 2:
                out.append({"blickets": list(subset), "threshold": 2})
    return out


def blicket_interventions(n_objects: int):
    objs = list(range(n_objects))
    return [list(s) for k in range(1, n_objects + 1) for s in itertools.combinations(objs, k)]


def blicket_task(seed: int, n_objects: int = 4):
    rng = random.Random(seed)
    hyps = blicket_hypotheses(n_objects)
    truth = rng.choice([h for h in hyps if h["blickets"]])
    return {"n_objects": n_objects, "truth": truth}


def blicket_outcome(truth, objects) -> int:
    return int(len(set(truth["blickets"]) & set(objects)) >= truth["threshold"])
