"""Inverse inference, mode 1 — DIRECT RULE EXTRACTION from observed dynamics.

The substrate's nature is to watch a world and recover the rule behind it (it
has discovered Galileo's law, momentum conservation, causal structure this way).
Here the world is an elementary cellular automaton and the rule is its Wolfram
code: each cell's next state is a deterministic function of its 3-cell
neighbourhood, so the 8 neighbourhood patterns (indexed 4·left+2·self+1·right)
fix an 8-bit code = Σ_i output(i)·2^i.

The evolution is loaded into the graph (Cell nodes carrying a ``state``, each
body cell linked to its three parents in the previous row — this parsing is
interfacing, world→graph). The INFERENCE is graph-resident Term-trees: the
neighbourhood index of a cell, the output read off any cell with that index,
and the code assembled as a Sum. The data uniquely determines the rule, so no
search is needed — the rule is read straight off the transitions.
"""
from __future__ import annotations

from substrate import (Attr, Eq, Exists, Filter, IfThenElse, Lit, Neighbours,
                       Pick, Plus, Pow, Sum, Times, TypedGraph, Var)

FILLED, EMPTY = "█", "░"


def parse_rows(text_rows: list[str]) -> list[list[int]]:
    """A run of █/░ lines → a 0/1 grid (the world, as printed)."""
    return [[1 if ch == FILLED else 0 for ch in row] for row in text_rows]


def load_evolution(graph: TypedGraph, grid: list[list[int]]) -> dict:
    """Put the CA evolution in the graph: a Cell per (row, col) with its
    ``state``; every interior body cell (row ≥ 1, with both horizontal
    neighbours) linked to its three parents in the row above (``pl``/``pc``/
    ``pr``) and collected under a ``Cells`` anchor; plus an ``Index`` anchor
    over the 8 neighbourhood codes 0..7."""
    cells = {}
    for t, row in enumerate(grid):
        for x, v in enumerate(row):
            cells[(t, x)] = graph._insert_node(
                "Cell", {"id": f"c_{t}_{x}", "state": v})
    body = graph._insert_node("Cells", {"id": "body"})
    W = len(grid[0]) if grid else 0
    for t in range(1, len(grid)):
        for x in range(1, W - 1):
            c = cells[(t, x)]
            graph._insert_edge(c, "pl", cells[(t - 1, x - 1)])
            graph._insert_edge(c, "pc", cells[(t - 1, x)])
            graph._insert_edge(c, "pr", cells[(t - 1, x + 1)])
            graph._insert_edge(body, "cell", c)
    idx = graph._insert_node("Index", {"id": "idx"})
    for i in range(8):
        graph._insert_edge(idx, "code",
                           graph._insert_node("Code", {"id": f"k{i}", "value": i}))
    return {"body": body, "idx": idx}


def _state(cell_var: str, rel: str):
    return Attr(Pick(Neighbours(Var(cell_var), rel)), "state")


def _nbhd_index(cell_var: str):
    """The neighbourhood code of a body cell: 4·state(left)+2·state(self)+1·right."""
    return Plus(items=(Times(items=(Lit(4), _state(cell_var, "pl"))),
                       Times(items=(Lit(2), _state(cell_var, "pc"))),
                       _state(cell_var, "pr")))


def wolfram_code_term():
    """The inferred Wolfram code as ONE graph-resident Term: for each code i in
    0..7, read the output of any body cell whose neighbourhood index is i (the
    rule is deterministic, so any witness suffices), and sum output(i)·2^i. A
    neighbourhood never seen in the data is underdetermined — taken here as 0."""
    has_i = Exists(Neighbours(Var("body"), "cell"), "c",
                   Eq(a=_nbhd_index("c"), b=Attr(Var("ix"), "value")))
    output_for_i = IfThenElse(
        cond=has_i,
        then=Attr(Pick(Filter(Neighbours(Var("body"), "cell"), "c",
                              Eq(a=_nbhd_index("c"),
                                 b=Attr(Var("ix"), "value")))), "state"),
        other=Lit(0))
    return Sum(source=Neighbours(Var("idx"), "code"), var_name="ix",
               value=Times(items=(output_for_i,
                                  Pow(a=Lit(2), b=Attr(Var("ix"), "value")))))


def infer_wolfram_code(grid: list[list[int]]) -> int:
    """Infer the elementary-CA Wolfram code from its evolution grid, entirely by
    evaluating the graph-resident inference Term over the loaded world."""
    g = TypedGraph()
    anchors = load_evolution(g, grid)
    return wolfram_code_term().evaluate(
        {"body": anchors["body"], "idx": anchors["idx"],
         "_resolve_concept": lambda n: None}, g)
