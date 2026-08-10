"""Conway's Game of Life as a (G, Γ) domain.

State is encoded structurally as node type:
- ``AliveCell`` / ``DeadCell`` are the two cell types
- ``adjacent_to`` edges link a cell to each of its (≤ 8) Moore-neighbours

The Γ describes which ``transitions_to`` edges are admissible. A cell's next
state is computed by probing: ask C which of ``transitions_to AliveCell`` or
``transitions_to DeadCell`` is admissible given the source cell's current
type and the alive-neighbour count. The transition operation never commits
``transitions_to`` edges — it uses C as an oracle and then mutates types
atomically.
"""
from __future__ import annotations

from typing import Iterable

from substrate import (
    And,
    Attr,
    ConsistencyChecker,
    Count,
    Eq,
    Filter,
    Grammar,
    In,
    Lit,
    Neighbours,
    NodeID,
    NodePattern,
    Not,
    Or,
    Production,
    SetT,
    Substrate,
    Term,
    TypeOf,
    TypedGraph,
    Var,
)


ALIVE = "AliveCell"
DEAD = "DeadCell"
ADJACENT = "adjacent_to"
TRANSITIONS_TO = "transitions_to"


def _alive_neighbour_count(src_var: str) -> Term:
    """Count of adjacent_to neighbours whose type is AliveCell."""
    return Count(Filter(
        source=Neighbours(Var(src_var), edge_type=ADJACENT),
        var_name="n",
        predicate=Eq(TypeOf(Var("n")), Lit(ALIVE)),
    ))


def life_like_grammar(birth: set[int], survival: set[int], name: str = "LifeLike") -> Grammar:
    """Build a Γ for any Bn/Sn Life-like CA. Conway is `{3}, {2, 3}`."""
    nbrs = _alive_neighbour_count("src")
    birth_set = SetT(items=tuple(Lit(n) for n in sorted(birth)))
    survival_set = SetT(items=tuple(Lit(n) for n in sorted(survival)))
    b_label = "".join(str(n) for n in sorted(birth)) or "_"
    s_label = "".join(str(n) for n in sorted(survival)) or "_"
    return Grammar([
        Production(
            src=NodePattern(DEAD, "src"),
            edge_type=TRANSITIONS_TO,
            tgt=NodePattern(ALIVE, "tgt"),
            where=In(nbrs, birth_set),
            provenance=f"{name}:B{b_label}",
        ),
        Production(
            src=NodePattern(ALIVE, "src"),
            edge_type=TRANSITIONS_TO,
            tgt=NodePattern(ALIVE, "tgt"),
            where=In(nbrs, survival_set),
            provenance=f"{name}:S{s_label}",
        ),
        Production(
            src=NodePattern(ALIVE, "src"),
            edge_type=TRANSITIONS_TO,
            tgt=NodePattern(DEAD, "tgt"),
            where=Not(In(nbrs, survival_set)),
            provenance=f"{name}:die",
        ),
        Production(
            src=NodePattern(DEAD, "src"),
            edge_type=TRANSITIONS_TO,
            tgt=NodePattern(DEAD, "tgt"),
            where=Not(In(nbrs, birth_set)),
            provenance=f"{name}:stay_dead",
        ),
    ])


def conway_grammar() -> Grammar:
    return life_like_grammar({3}, {2, 3}, name="Conway")


def highlife_grammar() -> Grammar:
    """B36/S23 — Conway + an extra birth condition on 6 neighbours."""
    return life_like_grammar({3, 6}, {2, 3}, name="HighLife")


def day_and_night_grammar() -> Grammar:
    """B3678/S34678 — self-complementary (alive/dead symmetric beyond a density flip)."""
    return life_like_grammar({3, 6, 7, 8}, {3, 4, 6, 7, 8}, name="DayAndNight")


def seeds_grammar() -> Grammar:
    """B2/S — every alive cell dies; explosive growth from any seed."""
    return life_like_grammar({2}, set(), name="Seeds")


def replicator_grammar() -> Grammar:
    """B1357/S1357 — every pattern eventually replicates."""
    return life_like_grammar({1, 3, 5, 7}, {1, 3, 5, 7}, name="Replicator")


RULE_PRESETS: dict[str, "callable[[], Grammar]"] = {  # type: ignore
    "Conway": conway_grammar,
    "HighLife": highlife_grammar,
    "DayAndNight": day_and_night_grammar,
    "Seeds": seeds_grammar,
    "Replicator": replicator_grammar,
}


def make_substrate(grammar_fn=conway_grammar) -> Substrate:
    g = TypedGraph()
    c = ConsistencyChecker(grammar_fn())
    return Substrate(graph=g, checker=c)


def swap_grammar(s: Substrate, new_grammar: Grammar) -> None:
    """Replace Γ on a live substrate. No state copy, no retraining."""
    s.checker.grammar = new_grammar


def encode_board(s: Substrate, board: list[list[int]]) -> dict[tuple[int, int], NodeID]:
    rows = len(board)
    cols = len(board[0])
    cells: dict[tuple[int, int], NodeID] = {}
    # Phase 0 didn't gate adjacency / cell-creation through Γ, so we use the
    # graph's internal API here. Domain-level admissibility lives in the
    # transitions_to grammar; structural encoding is a substrate-level concern.
    g = s.graph
    for r in range(rows):
        for c in range(cols):
            cell_type = ALIVE if board[r][c] else DEAD
            cells[(r, c)] = g._insert_node(cell_type, {"row": r, "col": c})
    for r in range(rows):
        for c in range(cols):
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        g._insert_edge(cells[(r, c)], ADJACENT, cells[(nr, nc)])
    return cells


def decode_board(s: Substrate, rows: int, cols: int) -> list[list[int]]:
    board = [[0] * cols for _ in range(rows)]
    for n in s.nodes(ALIVE):
        board[n.attrs["row"]][n.attrs["col"]] = 1
    for n in s.nodes(DEAD):
        board[n.attrs["row"]][n.attrs["col"]] = 0
    return board


def _cell_iter(s: Substrate) -> Iterable[NodeID]:
    for n in s.nodes(ALIVE):
        yield n.id
    for n in s.nodes(DEAD):
        yield n.id


def step(s: Substrate) -> int:
    """Advance one generation. Returns the number of cells that changed state.

    For each cell, probe Γ-admissibility against AliveCell and DeadCell
    targets; exactly one should be admissible under B3/S23. Collect all
    decisions first, then apply atomically. The step-local cache is held only
    during the decision phase — the apply phase mutates types and must not
    serve stale neighbour-typing.
    """
    decisions: list[tuple[NodeID, str]] = []
    with s.step_cache():
        for cell_id in list(_cell_iter(s)):
            next_type: str | None = None
            for candidate in (ALIVE, DEAD):
                if s.is_edge_admissible(cell_id, TRANSITIONS_TO, candidate):
                    next_type = candidate
                    break
            if next_type is None:
                raise RuntimeError(f"No admissible next-state for cell {cell_id} — Γ incomplete")
            decisions.append((cell_id, next_type))
    changed = 0
    for cell_id, new_type in decisions:
        if s.node(cell_id).type != new_type:
            s.set_type(cell_id, new_type)
            changed += 1
    return changed
