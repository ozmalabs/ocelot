"""Phase 7 — capability extensions in `substrate_rs.ext`.

Covers the gap-closers: set algebra (Union/Intersect/Difference/MapSet),
edge-attr DSL access (Edges/EdgeAttr), and observability counters.
"""
from __future__ import annotations

import pytest


srs = pytest.importorskip("substrate_rs")
ext = pytest.importorskip("substrate_rs.ext")


@pytest.fixture
def s():
    return srs.Substrate()


# --- Set algebra ---


def test_union_dedupes(s):
    a = srs.SetT(items=(srs.Lit(1), srs.Lit(2), srs.Lit(3)))
    b = srs.SetT(items=(srs.Lit(3), srs.Lit(4)))
    result = s.evaluate(ext.Union(a, b))
    assert result == frozenset({1, 2, 3, 4})


def test_intersect(s):
    a = srs.SetT(items=(srs.Lit(1), srs.Lit(2), srs.Lit(3)))
    b = srs.SetT(items=(srs.Lit(2), srs.Lit(3), srs.Lit(4)))
    result = s.evaluate(ext.Intersect(a, b))
    assert result == frozenset({2, 3})


def test_difference(s):
    a = srs.SetT(items=(srs.Lit(1), srs.Lit(2), srs.Lit(3)))
    b = srs.SetT(items=(srs.Lit(2), srs.Lit(3)))
    result = s.evaluate(ext.Difference(a, b))
    assert result == frozenset({1})


def test_mapset_squares(s):
    # {n*n for n in {1,2,3}} = {1, 4, 9}
    src = srs.SetT(items=(srs.Lit(1), srs.Lit(2), srs.Lit(3)))
    sq = srs.Times(items=(srs.Var("n"), srs.Var("n")))
    result = s.evaluate(ext.MapSet(src, "n", sq))
    assert result == frozenset({1, 4, 9})


# --- Edges + EdgeAttr ---


def test_edges_and_edge_attr_sum():
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Cell", var="src"),
        edge_type="connects",
        tgt=srs.NodePattern(type="Cell", var="tgt"),
        where=None, weight=None,
        provenance="test:cell_connects",
    ))
    a = s.add_node("Cell")
    b = s.add_node("Cell")
    c = s.add_node("Cell")
    s.add_edge(a, "connects", b, {"weight": 0.7})
    s.add_edge(a, "connects", c, {"weight": 0.3})

    # Sum(Edges(me, 'connects'), e, EdgeAttr(e, 'weight'))  → 1.0
    edges = ext.Edges(srs.Var("me"), "connects")
    sum_w = srs.Sum(edges, "e", ext.EdgeAttr(srs.Var("e"), "weight"))
    result = s.evaluate(sum_w, {"me": a})
    assert result == pytest.approx(1.0)


def test_edge_attr_default_to_none(s):
    """EdgeAttr on a missing edge handle returns None — never panics."""
    bogus_edge = srs.Lit("not-a-tuple")
    result = s.evaluate(ext.EdgeAttr(bogus_edge, "weight"))
    assert result is None


# --- Counters / observability ---


def test_counters_track_node_inserts():
    s = srs.Substrate()
    s.add_node("Alpha")
    s.add_node("Alpha")
    s.add_node("Beta")
    snap = ext.counters(s)
    assert snap["nodes_inserted_total"] == 3
    assert snap["nodes_inserted_by_type"]["Alpha"] == 2
    assert snap["nodes_inserted_by_type"]["Beta"] == 1
    # Live ρ = 3 nodes + 0 edges.
    assert snap["rho_g_size"] == 3


def test_counters_track_admissibility_outcomes():
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="A", var="src"),
        edge_type="e",
        tgt=srs.NodePattern(type="A", var="tgt"),
        where=None, weight=None,
        provenance="test:a_e_a",
    ))
    a = s.add_node("A")
    b = s.add_node("A")
    s.add_edge(a, "e", b)  # Admits
    # Bogus type — Type-2 rejection.
    bogus = s.add_node("BogusType")
    with pytest.raises(srs.InadmissibleEdge):
        s.add_edge(a, "e", bogus)
    snap = ext.counters(s)
    assert snap["admissibility_checks_total"] == 2
    assert snap["rejections_type2"] == 1
    assert snap["rejections_type1"] == 0
    # Production hit count by its provenance label.
    assert snap["production_admits"].get("test:a_e_a") == 1


def test_counters_track_cache_hit_rate():
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Cell", var="src"),
        edge_type="adj",
        tgt=srs.NodePattern(type="Cell", var="tgt"),
        where=None, weight=None,
        provenance="test:cell_adj",
    ))
    a = s.add_node("Cell")
    b = s.add_node("Cell")
    s.add_edge(a, "adj", b)
    # Force two Neighbours probes on the same key — the second should
    # hit the per-eval cache.
    # The cache is per top-level evaluate() call, so wrap two
    # Neighbours probes in a single Term that triggers both.
    nb = srs.Neighbours(srs.Var("me"), "adj")
    count = srs.Plus(items=(srs.Count(nb), srs.Count(nb)))
    s.evaluate(count, {"me": a})
    snap = ext.counters(s)
    rates = ext.cache_hit_rate(snap)
    # The second Neighbours(...) should hit. With 1 hit + 1 miss the
    # rate is 0.5.
    assert snap["cache_neighbours_hits"] >= 1
    assert snap["cache_neighbours_misses"] >= 1
    assert 0.0 < rates["neighbours"] <= 1.0


def test_counters_clear():
    s = srs.Substrate()
    s.add_node("X")
    snap_before = ext.counters(s)
    assert snap_before["nodes_inserted_total"] == 1
    ext.counters_clear(s)
    snap_after = ext.counters(s)
    assert snap_after["nodes_inserted_total"] == 0
