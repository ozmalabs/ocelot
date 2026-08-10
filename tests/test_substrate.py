"""Phase 0 acceptance tests for the (G, Γ) substrate."""
from __future__ import annotations

import random

import pytest

from substrate import (
    And,
    Attr,
    ConsistencyChecker,
    Count,
    Eq,
    Filter,
    Grammar,
    In,
    InadmissibleEdge,
    Lit,
    Neighbours,
    NodePattern,
    Not,
    Or,
    Production,
    SetT,
    Substrate,
    TypedGraph,
    Var,
    term_from_subgraph,
    term_to_subgraph,
    uniform_weight,
    weighted_walk,
)


# --- helpers ---


def _make_substrate(productions=()):
    g = TypedGraph()
    gamma = Grammar(productions)
    c = ConsistencyChecker(gamma)
    return Substrate(graph=g, checker=c), g, gamma


# --- DSL evaluation ---


def test_dsl_lit_var_eq():
    s, g, _ = _make_substrate()
    nid = g._insert_node("Cell", {"state": "alive"})
    assert Lit(7).evaluate({}, g) == 7
    assert Var("x").evaluate({"x": 7}, g) == 7
    assert Eq(Lit(2), Lit(2)).evaluate({}, g) is True
    assert Eq(Attr(Var("c"), "state"), Lit("alive")).evaluate({"c": nid}, g) is True


def test_dsl_set_in_count():
    _, g, _ = _make_substrate()
    s_term = SetT(items=(Lit(1), Lit(2), Lit(3)))
    assert s_term.evaluate({}, g) == frozenset({1, 2, 3})
    assert In(Lit(2), s_term).evaluate({}, g) is True
    assert In(Lit(5), s_term).evaluate({}, g) is False
    assert Count(s_term).evaluate({}, g) == 3


def test_dsl_neighbours_filter():
    _, g, _ = _make_substrate()
    a = g._insert_node("Cell", {"state": "alive"})
    b = g._insert_node("Cell", {"state": "dead"})
    c = g._insert_node("Cell", {"state": "alive"})
    g._insert_edge(a, "adjacent_to", b)
    g._insert_edge(a, "adjacent_to", c)
    alive_neighbours = Filter(
        source=Neighbours(Var("src"), edge_type="adjacent_to"),
        var_name="n",
        predicate=Eq(Attr(Var("n"), "state"), Lit("alive")),
    )
    result = alive_neighbours.evaluate({"src": a}, g)
    assert result == frozenset({c})


def test_dsl_and_or_not():
    _, g, _ = _make_substrate()
    assert And(items=(Lit(True), Lit(True))).evaluate({}, g) is True
    assert And(items=(Lit(True), Lit(False))).evaluate({}, g) is False
    assert Or(items=(Lit(False), Lit(True))).evaluate({}, g) is True
    assert Not(Lit(False)).evaluate({}, g) is True


# --- Axiom 3: Term ↔ G-subgraph round-trip ---


def test_term_roundtrip_simple():
    _, g, _ = _make_substrate()
    t = Eq(Lit(7), Var("x"))
    root = term_to_subgraph(t, g)
    t2 = term_from_subgraph(g, root)
    assert t == t2


def test_term_roundtrip_complex():
    _, g, _ = _make_substrate()
    t = In(
        Count(Filter(
            source=Neighbours(Var("src"), edge_type="adjacent_to"),
            var_name="n",
            predicate=Eq(Attr(Var("n"), "state"), Lit("alive")),
        )),
        SetT(items=(Lit(2), Lit(3))),
    )
    root = term_to_subgraph(t, g)
    t2 = term_from_subgraph(g, root)
    assert t == t2


# --- Axiom 3: Γ ↔ G-subgraph round-trip ---


def test_grammar_roundtrip():
    g = TypedGraph()
    stay_alive = Production(
        src=NodePattern("Cell", "src"),
        edge_type="transitions_to",
        tgt=NodePattern("Cell", "tgt"),
        where=And(items=(
            Eq(Attr(Var("src"), "state"), Lit("alive")),
            Eq(Attr(Var("tgt"), "state"), Lit("alive")),
            In(
                Count(Filter(
                    source=Neighbours(Var("src"), edge_type="adjacent_to"),
                    var_name="n",
                    predicate=Eq(Attr(Var("n"), "state"), Lit("alive")),
                )),
                SetT(items=(Lit(2), Lit(3))),
            ),
        )),
        provenance="conway:stay_alive",
    )
    gamma = Grammar([stay_alive])
    root = gamma.to_subgraph(g)
    gamma2 = Grammar.from_subgraph(g, root)
    assert len(gamma2.productions) == 1
    p = gamma2.productions[0]
    assert p.src == stay_alive.src
    assert p.tgt == stay_alive.tgt
    assert p.edge_type == stay_alive.edge_type
    assert p.where == stay_alive.where
    assert p.provenance == stay_alive.provenance


def test_grammar_json_roundtrip():
    from substrate import grammar_from_json, grammar_to_json
    stay_alive = Production(
        src=NodePattern("Cell", "src"),
        edge_type="transitions_to",
        tgt=NodePattern("Cell", "tgt"),
        where=And(items=(
            Eq(Attr(Var("src"), "state"), Lit("alive")),
            In(
                Count(Filter(
                    source=Neighbours(Var("src"), edge_type="adjacent_to"),
                    var_name="n",
                    predicate=Eq(Attr(Var("n"), "state"), Lit("alive")),
                )),
                SetT(items=(Lit(2), Lit(3))),
            ),
        )),
        provenance="conway:stay_alive",
    )
    gamma = Grammar([stay_alive])
    js = grammar_to_json(gamma)
    gamma2 = grammar_from_json(js)
    assert len(gamma2.productions) == 1
    p = gamma2.productions[0]
    assert p.src == stay_alive.src
    assert p.tgt == stay_alive.tgt
    assert p.edge_type == stay_alive.edge_type
    assert p.where == stay_alive.where
    assert p.provenance == stay_alive.provenance


# --- Π writes go through C ---


# --- weighted productions (Theorem D) ---


def test_weight_arithmetic_evaluates():
    from substrate import Div, IfThenElse, Lit, Minus, Plus, Sum, Times, Var
    _, g, _ = _make_substrate()
    assert Plus(items=(Lit(2), Lit(3), Lit(5))).evaluate({}, g) == 10
    assert Minus(Lit(7), Lit(2)).evaluate({}, g) == 5
    assert Times(items=(Lit(3), Lit(4))).evaluate({}, g) == 12
    assert Div(Lit(10), Lit(4)).evaluate({}, g) == 2.5
    assert IfThenElse(Lit(True), Lit(99), Lit(1)).evaluate({}, g) == 99
    assert IfThenElse(Lit(False), Lit(99), Lit(1)).evaluate({}, g) == 1


def test_sum_reduces_over_set():
    from substrate import Attr, Lit, Sum, Var
    _, g, _ = _make_substrate()
    a = g._insert_node("Piece", {"value": 1})
    b = g._insert_node("Piece", {"value": 3})
    c = g._insert_node("Piece", {"value": 5})
    # bind set in env, sum Attr(var, "value") over it
    s_term = Sum(
        source=Var("pieces"),
        var_name="p",
        value=Attr(Var("p"), "value"),
    )
    assert s_term.evaluate({"pieces": frozenset({a, b, c})}, g) == 9


def test_admissible_moves_returns_weighted_candidates():
    from substrate import Attr, IfThenElse, Lit, Plus, Var
    capture_bonus = Production(
        src=NodePattern("Piece", "p"),
        edge_type="moves_to",
        tgt=NodePattern("Square", "s"),
        # weight: base 1.0 + 100 if the square has occupant=True
        weight=Plus(items=(
            Lit(1.0),
            IfThenElse(Attr(Var("s"), "occupied"), Lit(100.0), Lit(0.0)),
        )),
        provenance="chess-toy:capture-bonus",
    )
    s, g, _ = _make_substrate([capture_bonus])
    piece = s.add_node("Piece", {})
    moves = s.admissible_moves(
        piece, "moves_to",
        candidates=[("Square", {"occupied": False}),
                    ("Square", {"occupied": True})],
    )
    weights = {a["occupied"]: w for _, a, w in moves}
    assert weights == {False: 1.0, True: 101.0}


def test_grammar_with_weight_roundtrips_json():
    from substrate import IfThenElse, Lit, Plus, grammar_from_json, grammar_to_json
    prod = Production(
        src=NodePattern("Piece", "p"),
        edge_type="moves_to",
        tgt=NodePattern("Square", "s"),
        weight=Plus(items=(Lit(1.0), IfThenElse(Lit(True), Lit(50.0), Lit(0.0)))),
        provenance="weighted:trivial",
    )
    g0 = Grammar([prod])
    j = grammar_to_json(g0)
    g1 = grammar_from_json(j)
    assert g1.productions[0].weight == prod.weight
    assert g1.productions[0].provenance == prod.provenance


def test_inadmissible_edge_raises():
    encode = Production(
        src=NodePattern("Cell", "s"),
        edge_type="adjacent_to",
        tgt=NodePattern("Cell", "t"),
        provenance="encode:adjacency",
    )
    s, g, _ = _make_substrate([encode])
    a = s.add_node("Cell", {"state": "alive"})
    b = s.add_node("Cell", {"state": "dead"})
    # admitted by `encode` production
    s.add_edge(a, "adjacent_to", b)
    # not admitted: edge_type mismatch
    with pytest.raises(InadmissibleEdge):
        s.add_edge(a, "transitions_to", b)


def test_transform_rolls_back_on_failure():
    encode = Production(
        src=NodePattern("Cell", "s"),
        edge_type="adjacent_to",
        tgt=NodePattern("Cell", "t"),
        provenance="encode:adjacency",
    )
    s, g, _ = _make_substrate([encode])
    a = s.add_node("Cell", {})
    b = s.add_node("Cell", {})
    n_before = g.node_count()
    e_before = g.edge_count()
    with pytest.raises(InadmissibleEdge):
        with s.transform() as tx:
            tx.add_edge(a, "adjacent_to", b)  # admitted
            tx.add_edge(a, "transitions_to", b)  # rejected → rollback
    assert g.node_count() == n_before
    assert g.edge_count() == e_before


# --- Weighted walker ---


def test_weighted_walker_respects_existing_edges():
    encode = Production(
        src=NodePattern("Cell", "s"),
        edge_type="adjacent_to",
        tgt=NodePattern("Cell", "t"),
        provenance="encode:adjacency",
    )
    s, g, _ = _make_substrate([encode])
    a = s.add_node("Cell", {})
    b = s.add_node("Cell", {})
    c = s.add_node("Cell", {})
    s.add_edge(a, "adjacent_to", b)
    s.add_edge(b, "adjacent_to", c)
    result = weighted_walk(s, a, n_walks=50, walk_length=2, seed=1337)
    # Every walk from a must reach b on step 1 and c on step 2 (deterministic in this DAG)
    assert result.visits.get(b, 0) == 50
    assert result.visits.get(c, 0) == 50


# --- Phase 0 acceptance: 32×32 board byte-identical round-trip ---


def _encoding_productions():
    return [
        Production(
            src=NodePattern("Cell", "s"),
            edge_type="adjacent_to",
            tgt=NodePattern("Cell", "t"),
            provenance="encode:adjacency",
        ),
    ]


def _encode_board(board: list[list[int]], s: Substrate) -> dict[tuple[int, int], "NodeID"]:
    cells: dict[tuple[int, int], NodeID] = {}
    rows = len(board)
    cols = len(board[0])
    for r in range(rows):
        for c in range(cols):
            cells[(r, c)] = s.add_node("Cell", {
                "row": r,
                "col": c,
                "state": "alive" if board[r][c] else "dead",
            })
    for r in range(rows):
        for c in range(cols):
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        s.add_edge(cells[(r, c)], "adjacent_to", cells[(nr, nc)])
    return cells


def _decode_board(s: Substrate, rows: int, cols: int) -> list[list[int]]:
    board = [[0] * cols for _ in range(rows)]
    for cell_node in s.nodes("Cell"):
        r = cell_node.attrs["row"]
        c = cell_node.attrs["col"]
        board[r][c] = 1 if cell_node.attrs["state"] == "alive" else 0
    return board


def test_board_32x32_roundtrip_byte_identical():
    rng = random.Random(42)
    original = [[rng.randint(0, 1) for _ in range(32)] for _ in range(32)]
    s, g, _ = _make_substrate(_encoding_productions())
    _encode_board(original, s)
    decoded = _decode_board(s, 32, 32)
    assert decoded == original


def test_board_roundtrip_preserves_adjacency_count():
    rng = random.Random(7)
    board = [[rng.randint(0, 1) for _ in range(16)] for _ in range(16)]
    s, g, _ = _make_substrate(_encoding_productions())
    cells = _encode_board(board, s)
    # corner cell has 3 neighbours
    assert sum(1 for _ in s.neighbours(cells[(0, 0)], "adjacent_to")) == 3
    # edge cell has 5
    assert sum(1 for _ in s.neighbours(cells[(0, 5)], "adjacent_to")) == 5
    # interior cell has 8
    assert sum(1 for _ in s.neighbours(cells[(5, 5)], "adjacent_to")) == 8
