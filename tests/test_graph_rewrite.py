"""Tests for graph-resident constructive procedures (graph rewriting).

The capability: the agent holds REWRITE RULES as graph data (a match pattern +
a graph-resident ``where`` Term + an effect that mutates the graph), and an
engine applies them to a fixed point — CONSTRUCTING new graph structure, which
read-only Term-trees cannot. Demonstrated on word reduction: the group relation
becomes a rule, and the engine builds the normal form in the graph.
"""
from __future__ import annotations

from domains import graph_rewrite as gr
from domains import linear_algebra as la
from domains import topology as tp
from substrate import (And, Attr, Count, Eq, Exists, Filter, In, Lit,
                       Neighbours, Not, Plus, Times, TypedGraph, Var)


def _cancel_rule(g):
    # a²=e, b²=e as ONE rule: cancel an adjacent equal-symbol pair, splicing the
    # chain (X -next-> L1 -next-> L2 -next-> Y, symbol L1 == symbol L2)
    return gr.make_rule(
        g, "cancel",
        match_edges=[("X", "next", "L1"), ("L1", "next", "L2"), ("L2", "next", "Y")],
        where=Eq(a=Attr(Var("L1"), "symbol"), b=Attr(Var("L2"), "symbol")),
        effects=[("add_edge", "X", "next", "Y"),
                 ("del_node", "L1"), ("del_node", "L2")])


def test_rule_is_graph_resident():
    g = TypedGraph()
    rid = _cancel_rule(g)
    a = g.node(rid).attrs
    assert a["match"] == [["X", "next", "L1"], ["L1", "next", "L2"], ["L2", "next", "Y"]]
    assert a["where"] is not None and a["effect"][0][0] == "add_edge"


def test_word_reduction_by_running_a_rule():
    g = TypedGraph()
    rule = _cancel_rule(g)
    for spelling, nf in {"aabba": "a", "abba": "", "abab": "abab",
                         "bbbb": "", "aab": "b"}.items():
        head, _ = gr.make_word(g, "w_" + spelling, spelling)
        gr.run(g, [rule])
        assert gr.read_word(g, head) == nf


def test_group_operation_by_rewriting():
    g = TypedGraph()
    rule = _cancel_rule(g)
    head, _ = gr.make_word(g, "prod", "abba")     # ab · ba concatenated
    gr.run(g, [rule])
    assert gr.read_word(g, head) == ""            # = e


# --- richer effects: CONSTRUCT nodes with computed attributes ---

def test_transpose_constructs_entries_with_computed_attrs():
    # a rule that, per source Entry, builds a transposed Entry (row←col, col←row)
    g = TypedGraph()
    M = la.make_matrix(g, "M", [[1, 2, 3], [4, 5, 6]])
    MT = g._insert_node("Matrix", {"id": "MT", "n_rows": 3, "n_cols": 2})
    g._insert_edge(M, "transpose_into", MT)
    rule = gr.make_rule(
        g, "transpose",
        match_edges=[("M", "entry", "e"), ("M", "transpose_into", "T")],
        where=Not(arg=Eq(a=Attr(Var("e"), "done"), b=Lit(1))),
        effects=[("add_node", "t", "Entry", {"row": Attr(Var("e"), "col"),
                                             "col": Attr(Var("e"), "row"),
                                             "value": Attr(Var("e"), "value")}),
                 ("add_edge", "T", "entry", "t"),
                 ("set_attr", "e", "done", 1)])
    assert gr.run(g, [rule]) == 6                  # one construction per entry
    assert la.read(g, MT) == [[1, 4], [2, 5], [3, 6]]


def test_matmul_by_accumulation_rule():
    # matrix multiply as a graph-resident rule: c[i,j] += a[i,k]·b[k,j], each
    # (a,b) product consumed exactly once (marked by a used_with edge)
    g = TypedGraph()
    A = la.make_matrix(g, "A", [[1, 2], [3, 4]])
    B = la.make_matrix(g, "B", [[5, 6], [7, 8]])
    nr, nc = 2, 2
    C = g._insert_node("Matrix", {"id": "C", "n_rows": nr, "n_cols": nc})
    for i in range(nr):
        for j in range(nc):
            g._insert_edge(C, "entry", g._insert_node(
                "Entry", {"id": f"C_{i}_{j}", "row": i, "col": j, "value": 0}))
    m = g._insert_node("MatMul", {"id": "mm"})
    g._insert_edge(m, "lhs", A); g._insert_edge(m, "rhs", B); g._insert_edge(m, "out", C)
    rule = gr.make_rule(
        g, "matmul",
        match_edges=[("m", "lhs", "A"), ("A", "entry", "a"),
                     ("m", "rhs", "B"), ("B", "entry", "b"),
                     ("m", "out", "C"), ("C", "entry", "p")],
        where=And(items=(
            Eq(a=Attr(Var("a"), "col"), b=Attr(Var("b"), "row")),
            Eq(a=Attr(Var("p"), "row"), b=Attr(Var("a"), "row")),
            Eq(a=Attr(Var("p"), "col"), b=Attr(Var("b"), "col")),
            Not(arg=In(member=Var("b"), container=Neighbours(Var("a"), "used_with"))))),
        effects=[("set_attr", "p", "value",
                  Plus(items=(Attr(Var("p"), "value"),
                              Times(items=(Attr(Var("a"), "value"),
                                           Attr(Var("b"), "value")))))),
                 ("add_edge", "a", "used_with", "b")])
    gr.run(g, [rule])
    assert la.read(g, C) == [[19, 22], [43, 50]]


# --- the search layer: graph-resident BACKTRACKING ---

def _count_colorings(edges, vertices, k):
    # Build the complex inline on a TypedGraph — this exercises the Python
    # search layer (gr.search_count), so it stays self-contained rather than
    # importing topology, which now runs on the Rust-native engine.
    g = TypedGraph()
    cx = g._insert_node("Complex", {"id": "cx_g"})
    vid = {}
    for v in vertices:
        n = g._insert_node("Vertex", {"id": f"g_v{v}", "label": v})
        vid[v] = n
        g._insert_edge(cx, "vertex", n)
    for u, w in edges:
        e = g._insert_node("Edge", {"id": f"g_e{u}_{w}"})
        g._insert_edge(cx, "edge", e)
        g._insert_edge(vid[u], "adj", vid[w])
        g._insert_edge(vid[w], "adj", vid[u])
    pal = g._insert_node("Palette", {"id": "pal"})
    for i in range(k):
        g._insert_edge(pal, "color", g._insert_node("Color", {"id": f"c{i}"}))
    open_term = Filter(Neighbours(Var("cx"), "vertex"), "v",
                       Eq(a=Count(Neighbours(Var("v"), "colored")), b=Lit(0)))
    options_term = Neighbours(Var("pal"), "color")
    fail_term = Exists(Neighbours(Var("cx"), "vertex"), "v",
                  Exists(Neighbours(Var("v"), "adj"), "u",
                    Exists(Neighbours(Var("v"), "colored"), "c",
                      In(member=Var("c"),
                         container=Neighbours(Var("u"), "colored")))))
    return gr.search_count(g, open_term, options_term, "colored", fail_term,
                           env={"cx": cx, "pal": pal})


def test_backtracking_search_counts_proper_colorings():
    # the search STRATEGY (open / options / fail) is all graph-resident Terms;
    # the engine just does DFS with undo
    assert _count_colorings([(0, 1), (1, 2), (0, 2)], [0, 1, 2], 3) == 6      # K3
    assert _count_colorings([(0, 1), (1, 2), (2, 3), (3, 0)], [0, 1, 2, 3], 3) == 18  # C4
    assert _count_colorings([(0, 1), (1, 2), (0, 2)], [0, 1, 2], 2) == 0      # χ(K3)=3
    assert _count_colorings([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
                            [0, 1, 2, 3], 3) == 0                              # χ(K4)=4
