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


def test_weighted_walk_path_logweight_is_label_bias_free():
    """GAMMA_SEARCH_COMPLETENESS_FIXES.md Bug 1, the discriminating test.

    Two graphs, same RAW weight (8.0) on "the same" edge, differing ONLY in
    how many sibling outgoing edges compete at that fork: `lo_s` has one
    outgoing edge (branching factor 1); `hi_s` has the identical weight-8.0
    edge plus two low-weight distractors (branching factor 3). Whenever a
    walk actually takes the weight-8.0 edge, the FIXED, correctly-composed
    quantity (`path_logweights`, a raw un-normalized log-weight sum, per
    the Carre/Mohri semiring identity `domains/fovea_bridge.py` already
    uses for one hop) must read IDENTICALLY in both graphs — it depends
    only on the weight of the edge actually traversed, never on how many
    alternatives existed at the fork.

    The OLD (pre-fix) shape this replaces — chaining LOCALLY renormalized
    per-step draw probabilities and summing their logs, exactly
    `weighted_walk`'s per-step `rng.choices` distribution if naively reused
    as a path score — is exactly the CRF "label bias" problem (Lafferty/
    McCallum/Pereira 2001): it is computed here for the SAME realised hop
    for contrast, and is strictly more negative (a lower, worse-looking
    score) for the high-branching graph even though the raw weight
    actually taken is identical. This is the discrepancy the fix exists to
    avoid reproducing in any future best-path consumer.
    """
    import math

    encode = Production(
        src=NodePattern("Cell", "s"),
        edge_type="adjacent_to",
        tgt=NodePattern("Cell", "t"),
        provenance="encode:adjacency",
    )

    TARGET_W = 8.0
    DISTRACTOR_W = 1.0

    # --- low-branching graph: one outgoing edge, weight 8.0 ---
    s_lo, g_lo, _ = _make_substrate([encode])
    lo_s = s_lo.add_node("Cell", {})
    lo_t = s_lo.add_node("Cell", {})
    s_lo.add_edge(lo_s, "adjacent_to", lo_t)

    def lo_weight(sub, src, edge):
        return TARGET_W

    # --- high-branching graph: the SAME weight-8.0 edge, plus two
    # low-weight distractor siblings at the same fork ---
    s_hi, g_hi, _ = _make_substrate([encode])
    hi_s = s_hi.add_node("Cell", {})
    hi_t = s_hi.add_node("Cell", {})
    hi_d1 = s_hi.add_node("Cell", {})
    hi_d2 = s_hi.add_node("Cell", {})
    s_hi.add_edge(hi_s, "adjacent_to", hi_t)
    s_hi.add_edge(hi_s, "adjacent_to", hi_d1)
    s_hi.add_edge(hi_s, "adjacent_to", hi_d2)

    def hi_weight(sub, src, edge):
        return TARGET_W if edge.tgt == hi_t else DISTRACTOR_W

    result_lo = weighted_walk(s_lo, lo_s, n_walks=200, walk_length=1,
                              weight_fn=lo_weight, seed=2024)
    result_hi = weighted_walk(s_hi, hi_s, n_walks=200, walk_length=1,
                              weight_fn=hi_weight, seed=2024)

    target_logw = math.log(TARGET_W)

    # Every walk in the low-branching graph took the only edge, at weight 8.0.
    lo_hits = [lw for lw in result_lo.path_logweights if lw == pytest.approx(target_logw)]
    assert len(lo_hits) == 200

    # At least some walks in the high-branching graph also took the
    # weight-8.0 edge (overwhelmingly likely at 8:1:1 odds, n=200).
    hi_hits = [lw for lw in result_hi.path_logweights if lw == pytest.approx(target_logw)]
    assert len(hi_hits) > 0

    # THE FIX: whenever the SAME raw-weight edge is taken, the recorded
    # path_logweight is IDENTICAL regardless of branching factor at the
    # fork -- not merely close, exactly equal (both are exactly log(8.0),
    # a deterministic function of the one edge actually traversed).
    assert hi_hits[0] == pytest.approx(lo_hits[0])
    assert hi_hits[0] == pytest.approx(target_logw)

    # THE BUG this replaces, shown by direct construction (not exercised by
    # weighted_walk any more): a locally-renormalized composition of the
    # SAME realised hop is branching-factor-DEPENDENT -- label bias, exactly
    # as the CRF literature predicts. The low-branching fork has only one
    # candidate, so its local probability is 1.0 (log 0.0); the
    # high-branching fork's local probability for the identical edge is
    # diluted by its two siblings.
    old_style_local_logprob_lo = math.log(TARGET_W / TARGET_W)
    old_style_local_logprob_hi = math.log(TARGET_W / (TARGET_W + DISTRACTOR_W + DISTRACTOR_W))
    assert old_style_local_logprob_lo != pytest.approx(old_style_local_logprob_hi)
    assert old_style_local_logprob_hi < old_style_local_logprob_lo
    # The fixed, raw-weight composition does NOT reproduce that gap:
    assert lo_hits[0] == pytest.approx(hi_hits[0])


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
