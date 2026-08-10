"""Conway's Game of Life — Rust-backed parallel of `domains/conway.py`.

Same (G, Γ) shape: ``AliveCell`` / ``DeadCell`` nodes, ``adjacent_to``
edges, four productions over `transitions_to` (B3/S23 by default). The
step function probes each cell against Γ-admissibility and applies the
type flip atomically.

Differences from the Python original:

* The substrate is built on `substrate_rs.Substrate`, so admissibility
  checks + Term evaluation run in Rust.
* There is no `step_cache()` context manager — the Rust engine scopes
  its per-eval cache to a single `evaluate()` call automatically.
* Adjacency / cell-creation here goes through the proper Γ-grammar
  rather than reaching into a private `_insert_*` API. We declare a
  "structural" production for `adjacent_to` so the encode pass uses Π
  cleanly. (The Python version reaches into `g._insert_edge` because
  Phase 0 didn't gate structural edges through Γ; we don't carry that
  shortcut forward.)
"""
from __future__ import annotations

from typing import Iterable

import substrate_rs as srs


ALIVE = "AliveCell"
DEAD = "DeadCell"
ADJACENT = "adjacent_to"
TRANSITIONS_TO = "transitions_to"


def _alive_neighbour_count_term(src_var: str) -> srs.Term:
    return srs.Count(srs.Filter(
        source=srs.Neighbours(srs.Var(src_var), edge_type=ADJACENT),
        var_name="n",
        predicate=srs.Eq(srs.TypeOf(srs.Var("n")), srs.Lit(ALIVE)),
    ))


def make_substrate(birth=(3,), survival=(2, 3), name: str = "Conway") -> srs.Substrate:
    """Build a Substrate for any Bn/Sn life-like CA. Conway is `{3}, {2, 3}`."""
    s = srs.Substrate()
    nbrs = _alive_neighbour_count_term("src")
    birth_set = srs.SetT(items=tuple(srs.Lit(n) for n in sorted(birth)))
    survival_set = srs.SetT(items=tuple(srs.Lit(n) for n in sorted(survival)))
    b_label = "".join(str(n) for n in sorted(birth)) or "_"
    s_label = "".join(str(n) for n in sorted(survival)) or "_"

    productions = [
        # B birth: DeadCell with alive_n ∈ B transitions to AliveCell.
        srs.Production(
            src=srs.NodePattern(type=DEAD, var="src"),
            edge_type=TRANSITIONS_TO,
            tgt=srs.NodePattern(type=ALIVE, var="tgt"),
            where=srs.In(nbrs, birth_set),
            provenance=f"{name}:B{b_label}",
        ),
        # S survival: AliveCell with alive_n ∈ S stays alive.
        srs.Production(
            src=srs.NodePattern(type=ALIVE, var="src"),
            edge_type=TRANSITIONS_TO,
            tgt=srs.NodePattern(type=ALIVE, var="tgt"),
            where=srs.In(nbrs, survival_set),
            provenance=f"{name}:S{s_label}",
        ),
        # Die: AliveCell with alive_n ∉ S dies.
        srs.Production(
            src=srs.NodePattern(type=ALIVE, var="src"),
            edge_type=TRANSITIONS_TO,
            tgt=srs.NodePattern(type=DEAD, var="tgt"),
            where=srs.Not(srs.In(nbrs, survival_set)),
            provenance=f"{name}:die",
        ),
        # Stay dead: DeadCell with alive_n ∉ B stays dead.
        srs.Production(
            src=srs.NodePattern(type=DEAD, var="src"),
            edge_type=TRANSITIONS_TO,
            tgt=srs.NodePattern(type=DEAD, var="tgt"),
            where=srs.Not(srs.In(nbrs, birth_set)),
            provenance=f"{name}:stay_dead",
        ),
        # Structural production for adjacency — both directions covered by
        # the symmetry of the cell type and edge type.
        srs.Production(
            src=srs.NodePattern(type=ALIVE, var="src"),
            edge_type=ADJACENT,
            tgt=srs.NodePattern(type=ALIVE, var="tgt"),
            where=None,
            provenance=f"{name}:adj_AA",
        ),
        srs.Production(
            src=srs.NodePattern(type=ALIVE, var="src"),
            edge_type=ADJACENT,
            tgt=srs.NodePattern(type=DEAD, var="tgt"),
            where=None,
            provenance=f"{name}:adj_AD",
        ),
        srs.Production(
            src=srs.NodePattern(type=DEAD, var="src"),
            edge_type=ADJACENT,
            tgt=srs.NodePattern(type=ALIVE, var="tgt"),
            where=None,
            provenance=f"{name}:adj_DA",
        ),
        srs.Production(
            src=srs.NodePattern(type=DEAD, var="src"),
            edge_type=ADJACENT,
            tgt=srs.NodePattern(type=DEAD, var="tgt"),
            where=None,
            provenance=f"{name}:adj_DD",
        ),
    ]
    for p in productions:
        s.add_production(p)
    return s


def encode_board(s: srs.Substrate, board: list[list[int]]) -> dict[tuple[int, int], srs.NodeID]:
    rows = len(board)
    cols = len(board[0])
    cells: dict[tuple[int, int], srs.NodeID] = {}
    for r in range(rows):
        for c in range(cols):
            cell_type = ALIVE if board[r][c] else DEAD
            cells[(r, c)] = s.add_node(cell_type, {"row": r, "col": c})
    for r in range(rows):
        for c in range(cols):
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        s.add_edge(cells[(r, c)], ADJACENT, cells[(nr, nc)])
    return cells


def decode_board(s: srs.Substrate, rows: int, cols: int) -> list[list[int]]:
    board = [[0] * cols for _ in range(rows)]
    for nid in s.nodes(ALIVE):
        attrs = s.node(nid)["attrs"]
        board[attrs["row"]][attrs["col"]] = 1
    for nid in s.nodes(DEAD):
        attrs = s.node(nid)["attrs"]
        board[attrs["row"]][attrs["col"]] = 0
    return board


def _cell_iter(s: srs.Substrate) -> Iterable[srs.NodeID]:
    yield from s.nodes(ALIVE)
    yield from s.nodes(DEAD)


def step(s: srs.Substrate) -> int:
    """Advance one generation. Returns the number of cells that changed.

    Same shape as the Python `domains.conway.step`: collect every
    cell's next-type by probing Γ admissibility, then apply the type
    flips atomically.
    """
    decisions: list[tuple[srs.NodeID, str]] = []
    cells = list(_cell_iter(s))
    for cell_id in cells:
        next_type: str | None = None
        for candidate in (ALIVE, DEAD):
            if s.is_edge_admissible(cell_id, TRANSITIONS_TO, candidate):
                next_type = candidate
                break
        if next_type is None:
            raise RuntimeError(
                f"No admissible next-state for cell {cell_id} — Γ incomplete"
            )
        decisions.append((cell_id, next_type))
    changed = 0
    for cell_id, new_type in decisions:
        if s.node(cell_id)["type"] != new_type:
            s.set_type(cell_id, new_type)
            changed += 1
    return changed


# --- Reference patterns for the bench / parity tests ---

def r_pentomino_board(rows: int = 30, cols: int = 30) -> list[list[int]]:
    """The classic R-pentomino — chaotic for ~1000 generations.
    Useful for benchmarks because it exercises every Γ branch."""
    board = [[0] * cols for _ in range(rows)]
    cr, cc = rows // 2, cols // 2
    # R-pentomino shape:  .##
    #                     ##.
    #                     .#.
    cells = [(cr, cc), (cr, cc + 1), (cr + 1, cc - 1), (cr + 1, cc), (cr + 2, cc)]
    for r, c in cells:
        if 0 <= r < rows and 0 <= c < cols:
            board[r][c] = 1
    return board


def glider_board(rows: int = 30, cols: int = 30) -> list[list[int]]:
    """A glider in the upper-left — moves SE at c/4. Simpler than the
    R-pentomino so the bench can compare 'cheap' steps too."""
    board = [[0] * cols for _ in range(rows)]
    cells = [(1, 2), (2, 3), (3, 1), (3, 2), (3, 3)]
    for r, c in cells:
        if 0 <= r < rows and 0 <= c < cols:
            board[r][c] = 1
    return board
