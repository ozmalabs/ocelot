"""Phase-6 acceptance: the Rust engine matches Python substrate semantics
across the operations exercised by `test_substrate.py`.

These aren't strict drop-in tests (the Rust Substrate doesn't yet expose
a separately-addressable TypedGraph the way Python does), but they cover
the same evaluation surface — Lit/Var/Eq/Filter/Neighbours/Count, edge
admissibility, weighted productions, persistence round-trip, concept
recursion via Holds — so a passing test here demonstrates the engine
ships with parity behaviour. Strict-drop-in tests come in Phase 8.
"""
from __future__ import annotations

import importlib

import pytest


srs = pytest.importorskip("substrate_rs")


@pytest.fixture
def s():
    return srs.Substrate()


# --- DSL evaluation ---


def test_lit_evaluates(s):
    assert s.evaluate(srs.Lit(7)) == 7


def test_var_lookup(s):
    assert s.evaluate(srs.Var("x"), {"x": 42}) == 42


def test_eq_attr_filter(s):
    nid = s.add_node("Cell", {"state": "alive"})
    assert (
        s.evaluate(srs.Eq(srs.Attr(srs.Var("c"), "state"), srs.Lit("alive")), {"c": nid})
        is True
    )


def test_set_in_count(s):
    set_t = srs.SetT(items=(srs.Lit(1), srs.Lit(2), srs.Lit(3)))
    assert s.evaluate(set_t) == frozenset({1, 2, 3})
    assert s.evaluate(srs.In(srs.Lit(2), set_t)) is True
    assert s.evaluate(srs.In(srs.Lit(5), set_t)) is False
    assert s.evaluate(srs.Count(set_t)) == 3


def test_neighbours_filter(s):
    # We need a grammar that admits Cell -[adjacent_to]-> Cell to test
    # edge insertion + Neighbours traversal in one shot.
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Cell", var="src"),
        edge_type="adjacent_to",
        tgt=srs.NodePattern(type="Cell", var="tgt"),
        where=None, weight=None,
        provenance="test:cell_adj",
    ))
    a = s.add_node("Cell", {"state": "alive"})
    b = s.add_node("Cell", {"state": "dead"})
    c = s.add_node("Cell", {"state": "alive"})
    s.add_edge(a, "adjacent_to", b)
    s.add_edge(a, "adjacent_to", c)
    alive_neighbours = srs.Filter(
        source=srs.Neighbours(srs.Var("src"), edge_type="adjacent_to"),
        var_name="n",
        predicate=srs.Eq(srs.Attr(srs.Var("n"), "state"), srs.Lit("alive")),
    )
    result = s.evaluate(alive_neighbours, {"src": a})
    assert result == frozenset({c})


# --- Grammar admissibility ---


def test_inadmissible_edge_raises():
    s = srs.Substrate()
    # No production at all — every edge is Type-2 (vocab absent).
    a = s.add_node("Alpha")
    b = s.add_node("Beta")
    with pytest.raises(srs.InadmissibleEdge):
        s.add_edge(a, "links_to", b)


def test_weighted_production_default_weight():
    """Per Paper §1.2 (Definition 2), weight defaults to 1.0. Verify the
    admissible_moves API surfaces this."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="A", var="src"),
        edge_type="e",
        tgt=srs.NodePattern(type="B", var="tgt"),
        where=None, weight=None,  # default 1.0
        provenance="test:default_w",
    ))
    a = s.add_node("A")
    moves = s.admissible_moves(a, "e", [("B", None)])
    assert len(moves) == 1
    _, _, w = moves[0]
    assert w == pytest.approx(1.0)


def test_weighted_production_with_explicit_weight():
    """Two productions on the same triple — weights add."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="A", var="src"),
        edge_type="e",
        tgt=srs.NodePattern(type="B", var="tgt"),
        where=None, weight=None,  # default 1.0
        provenance="test:w1",
    ))
    s.add_production(srs.Production(
        src=srs.NodePattern(type="A", var="src"),
        edge_type="e",
        tgt=srs.NodePattern(type="B", var="tgt"),
        where=None, weight=srs.Lit(2.5),
        provenance="test:w2",
    ))
    a = s.add_node("A")
    moves = s.admissible_moves(a, "e", [("B", None)])
    assert len(moves) == 1
    assert moves[0][2] == pytest.approx(3.5)


# --- Persistence round-trip ---


def test_graph_round_trip_via_dict(s):
    s.add_production(srs.Production(
        src=srs.NodePattern(type="X", var="src"),
        edge_type="e",
        tgt=srs.NodePattern(type="X", var="tgt"),
        where=None, weight=None,
        provenance="test:x_e_x",
    ))
    a = s.add_node("X", {"label": "alpha"})
    b = s.add_node("X", {"label": "beta"})
    s.add_edge(a, "e", b)

    dump = s.graph_to_dict()

    s2 = srs.Substrate()
    s2.graph_from_dict(dump)
    assert s2.node_count() == 2
    assert s2.edge_count() == 1
    # NodeIDs preserved
    assert s2.node(a)["attrs"]["label"] == "alpha"


# --- Holds: graph-resident concept recursion ---


def test_holds_concept_resolves():
    """is_positive(x) := if x == 0 then 0 else 1 — recursion bottoms
    via a base-case IfThenElse, the Holds Term does the dispatch."""
    s = srs.Substrate()
    s.define_concept(
        "is_positive",
        srs.IfThenElse(
            cond=srs.Eq(srs.Var("x"), srs.Lit(0)),
            then=srs.Lit(0),
            other=srs.Lit(1),
        ),
    )
    res_pos = s.evaluate(srs.Holds(concept="is_positive", node=srs.Lit(5)))
    res_zero = s.evaluate(srs.Holds(concept="is_positive", node=srs.Lit(0)))
    assert res_pos == 1
    assert res_zero == 0


# --- Transaction rollback ---


def test_transaction_rollback_on_exception():
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="A", var="src"),
        edge_type="e",
        tgt=srs.NodePattern(type="A", var="tgt"),
        where=None, weight=None,
        provenance="test:a_e_a",
    ))
    n_before = s.node_count()
    with pytest.raises(srs.InadmissibleEdge):
        with s.transform() as tx:
            a = tx.add_node("A")
            b = tx.add_node("A")
            tx.add_edge(a, "e", b)
            # Force a rollback — vocab Type-2 since "Bogus" type
            # isn't in the grammar.
            c = tx.add_node("Bogus")
            tx.add_edge(a, "links", c)  # raises InadmissibleEdge
    assert s.node_count() == n_before


# --- Term equality / hash for caching ---


def test_term_equality_is_structural():
    t1 = srs.Filter(
        source=srs.Neighbours(srs.Var("x"), "adj"),
        var_name="n",
        predicate=srs.Eq(srs.Var("n"), srs.Lit(0)),
    )
    t2 = srs.Filter(
        source=srs.Neighbours(srs.Var("x"), "adj"),
        var_name="n",
        predicate=srs.Eq(srs.Var("n"), srs.Lit(0)),
    )
    assert t1 == t2
    assert hash(t1) == hash(t2)
