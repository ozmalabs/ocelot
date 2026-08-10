"""Phase 7d — namespace import + backtracking search.

Two follow-ons that close the remaining gap-analysis items.

* **Namespace import** — `import_grammar(s, grammar_json, namespace='ns')`
  pulls a published grammar into the substrate with every node-type,
  edge-type, and provenance prefixed by `ns:`. Two same-named types
  from different modules can now coexist.
* **Backtracking search** — `search_count` / `search_count_general` /
  `search_sum` provide the recursive DFS shape from
  `domains/graph_rewrite.py`, but driven by graph-resident Terms
  evaluated through the Rust engine. Used by subgroup enumeration,
  Knuth–Bendix, low-index-subgroup search, anything that needs to
  enumerate assignments.
"""
from __future__ import annotations

import pytest


srs = pytest.importorskip("substrate_rs")
ext = pytest.importorskip("substrate_rs.ext")


# --- Namespace import ----------------------------------------------------


def _chess_grammar_json() -> dict:
    """A small "chess" grammar — Pawn / Square / on_square. Built via
    a temporary substrate so we get the wire format right, then
    imported into another substrate under a namespace."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Pawn", var="p"),
        edge_type="on_square",
        tgt=srs.NodePattern(type="Square", var="sq"),
        where=None, weight=None,
        provenance="chess:pawn_placement",
    ))
    return s.grammar_to_json()


def _go_grammar_json() -> dict:
    """A 'go' grammar that uses a same-named type (Square) — would
    collide without namespacing."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Stone", var="st"),
        edge_type="on_square",
        tgt=srs.NodePattern(type="Square", var="sq"),
        where=None, weight=None,
        provenance="go:stone_placement",
    ))
    return s.grammar_to_json()


def test_import_grammar_prefixes_types():
    s = srs.Substrate()
    n = ext.import_grammar(s, _chess_grammar_json(), namespace="chess")
    assert n == 1
    g = s.grammar_to_json()
    # Every type carries the namespace prefix.
    assert g["productions"][0]["src"]["type"] == "chess:Pawn"
    assert g["productions"][0]["tgt"]["type"] == "chess:Square"
    assert g["productions"][0]["edge_type"] == "chess:on_square"
    # Provenance is double-prefixed (namespace:original-provenance) so
    # diagnostics retain the import-time origin.
    assert g["productions"][0]["provenance"].startswith("chess:")


def test_two_namespaces_coexist_without_collision():
    """Two grammars sharing the type name 'Square' — namespaced
    import keeps them distinct in the merged Γ."""
    s = srs.Substrate()
    ext.import_grammar(s, _chess_grammar_json(), namespace="chess")
    ext.import_grammar(s, _go_grammar_json(), namespace="go")
    g = s.grammar_to_json()
    types_seen = set()
    for p in g["productions"]:
        types_seen.add(p["src"]["type"])
        types_seen.add(p["tgt"]["type"])
    assert {"chess:Pawn", "chess:Square", "go:Stone", "go:Square"} <= types_seen


def test_import_grammar_rejects_bad_namespace():
    s = srs.Substrate()
    with pytest.raises(ValueError):
        ext.import_grammar(s, _chess_grammar_json(), namespace="")
    with pytest.raises(ValueError):
        ext.import_grammar(s, _chess_grammar_json(), namespace="bad:ns")


def test_already_namespaced_types_pass_through():
    """A type that already contains `:` is treated as
    already-namespaced and left unchanged."""
    s = srs.Substrate()
    # Manually build a grammar JSON with a pre-namespaced type.
    grammar = {
        "productions": [{
            "src": {"type": "shared:Token", "var": "t"},
            "edge_type": "lex",
            "tgt": {"type": "Symbol", "var": "s"},
            "where": None,
            "weight": None,
            "provenance": "test",
        }]
    }
    ext.import_grammar(s, grammar, namespace="lex")
    g = s.grammar_to_json()
    p = g["productions"][0]
    # Already-namespaced "shared:Token" survives; bare "Symbol" gets
    # "lex:" prefix; the edge_type "lex" also gets the prefix.
    assert p["src"]["type"] == "shared:Token"
    assert p["tgt"]["type"] == "lex:Symbol"
    assert p["edge_type"] == "lex:lex"


def test_namespaced_type_helper():
    assert ext.namespaced_type("phys", "Particle") == "phys:Particle"
    # Already-namespaced types pass through unchanged.
    assert ext.namespaced_type("phys", "math:Number") == "math:Number"


def test_imported_grammar_works_with_namespaced_nodes():
    """End-to-end: import a grammar, insert namespaced nodes, edge
    admits."""
    s = srs.Substrate()
    ext.import_grammar(s, _chess_grammar_json(), namespace="chess")
    p = s.add_node(ext.namespaced_type("chess", "Pawn"))
    sq = s.add_node(ext.namespaced_type("chess", "Square"))
    # The edge type also got namespaced — use the prefixed name.
    s.add_edge(p, "chess:on_square", sq)
    assert s.has_edge(p, "chess:on_square", sq)


# --- Backtracking search -------------------------------------------------


def _build_three_coloring_substrate(n: int) -> tuple[srs.Substrate, list]:
    """Build a graph with `n` vertices each linked to a fixed set of
    colour nodes via `adjacent_to`. The search task: assign each
    vertex one of 3 colours such that no two adjacent vertices share
    a colour. Edge graph: a triangle (n=3, every vertex adjacent to
    every other) — has 6 valid 3-colourings (3! orderings of the
    3 colours).
    """
    s = srs.Substrate()
    # Permissive grammar so we can build the graph freely.
    for et in ("adjacent_to", "could_be", "is_color"):
        s.add_production(srs.Production(
            src=srs.NodePattern(type="V", var="src"),
            edge_type=et,
            tgt=srs.NodePattern(type="C", var="tgt"),
            where=None, weight=None,
            provenance=f"perm:V_{et}_C",
        ))
        s.add_production(srs.Production(
            src=srs.NodePattern(type="V", var="src"),
            edge_type=et,
            tgt=srs.NodePattern(type="V", var="tgt"),
            where=None, weight=None,
            provenance=f"perm:V_{et}_V",
        ))
    colors = [s.add_node("C", {"name": c}) for c in ("R", "G", "B")]
    vertices = [s.add_node("V", {"id": i}) for i in range(n)]
    # Every vertex 'could_be' every colour (the candidate set).
    for v in vertices:
        for c in colors:
            s.add_edge(v, "could_be", c)
    # Triangle adjacency.
    for i, vi in enumerate(vertices):
        for j, vj in enumerate(vertices):
            if i != j:
                s.add_edge(vi, "adjacent_to", vj)
    return s, vertices


def test_search_count_three_coloring_triangle():
    """Classic counting: 3-colour a triangle, the answer is 6
    (the 3! orderings of the 3 colours). The search assigns
    `is_color` edges per the assign_edge protocol."""
    s, _vertices = _build_three_coloring_substrate(n=3)
    # open_term: vertices that don't yet have an is_color assignment.
    # Express as: Filter(nodes(V), v, Not(Exists(Neighbours(v, 'is_color'), c, Lit(True))))
    # Simpler: use NodesWhere via attr — but here we don't have an attr.
    # Use a direct shape with Exists.
    all_v = srs.Filter(
        source=ext.NodesWhere("V", "id", srs.Lit(0)),  # placeholder
        var_name="v",
        predicate=srs.Lit(True),
    )
    # Instead let's use a simpler open_term: NodesWhere only finds
    # indexed nodes, but we haven't declared an index. Use SetT of
    # explicit IDs — but the search needs a Term that recomputes each
    # iteration. Build it with Filter over a known source.
    #
    # Use this: open = {v : v in V-type AND v has no is_color edge}
    # — express via Filter+Exists.
    v_in_v = srs.Var("v")
    has_color = srs.Exists(
        source=srs.Neighbours(v_in_v, "is_color"),
        var_name="c",
        predicate=srs.Lit(True),
    )
    # We need the set of all V-typed nodes. There's no direct
    # `Nodes("V")` Term, so back-fill it via NodesWhere with an
    # index. Declare the index once.
    ext.declare_attr_index(s, "V", "id")
    # Build the set of all V-typed nodes by unioning the per-id sets.
    # Simpler: declare attr index on `id`, then `NodesWhere("V", "id", n)`
    # for each n. But that requires knowing how many vertices. Let's
    # just enumerate via the nodes(...) substrate API and bake them as
    # SetT items (the Term has to be re-evaluable, but the source set
    # only loses items as the search proceeds, never gains).
    v_ids = s.nodes("V")
    all_v_set = srs.SetT(items=tuple(srs.Lit(v) for v in []))  # placeholder
    # Use a different shape: open_term = NodesWhere on all 3 ids,
    # unioned. Cleaner: write a tiny helper grammar.
    #
    # Simplest correct shape: open_term = Filter(<all V-nodes>, v, Not(has_color))
    # where <all V-nodes> is a graph-resident set. Use SetT of node-id Lits.
    all_v_term = srs.SetT(items=tuple(srs.Lit(v) for v in v_ids))
    open_term = srs.Filter(
        source=all_v_term,
        var_name="v",
        predicate=srs.Not(has_color),
    )
    # options_term: colours not assigned to any adjacent vertex.
    # Express as: Filter(Lit(all colours), c, Not(Exists(Neighbours(?item-equivalent), …)))
    # The search loops over the "item" being decided in Python so we
    # can pass it in env. Here we approximate by passing options =
    # all colours, and using fail_term to detect conflicts.
    color_ids = s.nodes("C")
    options_term = srs.SetT(items=tuple(srs.Lit(c) for c in color_ids))
    # fail_term: there exists some adjacent pair of vertices sharing
    # an is_color assignment. Express via Filter+Exists nesting.
    #     Exists(V, v1, Exists(Neighbours(v1, 'adjacent_to'), v2,
    #         Exists(Neighbours(v1, 'is_color'), c,
    #             In(c, Neighbours(v2, 'is_color')))))
    fail_term = srs.Exists(
        source=all_v_term,
        var_name="v1",
        predicate=srs.Exists(
            source=srs.Neighbours(srs.Var("v1"), "adjacent_to"),
            var_name="v2",
            predicate=srs.Exists(
                source=srs.Neighbours(srs.Var("v1"), "is_color"),
                var_name="c",
                predicate=srs.In(srs.Var("c"), srs.Neighbours(srs.Var("v2"), "is_color")),
            ),
        ),
    )
    count = ext.search_count(
        s,
        open_term=open_term,
        options_term=options_term,
        assign_edge="is_color",
        fail_term=fail_term,
    )
    assert count == 6


def test_search_count_general_with_assign_edge_apply():
    """Same triangle, same answer (6), but via `search_count_general`
    + the `assign_edge_apply` callback factory — the more general
    surface that lets callers plug in any apply step.
    """
    s, _vs = _build_three_coloring_substrate(n=3)
    v_in_v = srs.Var("v")
    has_color = srs.Exists(
        source=srs.Neighbours(v_in_v, "is_color"),
        var_name="c",
        predicate=srs.Lit(True),
    )
    v_ids = s.nodes("V")
    all_v_term = srs.SetT(items=tuple(srs.Lit(v) for v in v_ids))
    open_term = srs.Filter(
        source=all_v_term,
        var_name="v",
        predicate=srs.Not(has_color),
    )
    c_ids = s.nodes("C")
    options_term = srs.SetT(items=tuple(srs.Lit(c) for c in c_ids))
    fail_term = srs.Exists(
        source=all_v_term,
        var_name="v1",
        predicate=srs.Exists(
            source=srs.Neighbours(srs.Var("v1"), "adjacent_to"),
            var_name="v2",
            predicate=srs.Exists(
                source=srs.Neighbours(srs.Var("v1"), "is_color"),
                var_name="c",
                predicate=srs.In(srs.Var("c"), srs.Neighbours(srs.Var("v2"), "is_color")),
            ),
        ),
    )
    count = ext.search_count_general(
        s,
        open_term=open_term,
        options_term=options_term,
        apply_option=ext.assign_edge_apply("is_color"),
        fail_term=fail_term,
    )
    assert count == 6


def test_search_sum_total_assignments():
    """search_sum: like search_count but sums a value-term per leaf
    instead of counting. Sum 1 per leaf — should equal the count."""
    s, _vs = _build_three_coloring_substrate(n=3)
    v_in_v = srs.Var("v")
    has_color = srs.Exists(
        source=srs.Neighbours(v_in_v, "is_color"),
        var_name="c",
        predicate=srs.Lit(True),
    )
    v_ids = s.nodes("V")
    all_v_term = srs.SetT(items=tuple(srs.Lit(v) for v in v_ids))
    open_term = srs.Filter(
        source=all_v_term,
        var_name="v",
        predicate=srs.Not(has_color),
    )
    c_ids = s.nodes("C")
    options_term = srs.SetT(items=tuple(srs.Lit(c) for c in c_ids))
    fail_term = srs.Exists(
        source=all_v_term,
        var_name="v1",
        predicate=srs.Exists(
            source=srs.Neighbours(srs.Var("v1"), "adjacent_to"),
            var_name="v2",
            predicate=srs.Exists(
                source=srs.Neighbours(srs.Var("v1"), "is_color"),
                var_name="c",
                predicate=srs.In(srs.Var("c"), srs.Neighbours(srs.Var("v2"), "is_color")),
            ),
        ),
    )
    total = ext.search_sum(
        s,
        open_term=open_term,
        options_term=options_term,
        apply_option=ext.assign_edge_apply("is_color"),
        value_term=srs.Lit(1),
        fail_term=fail_term,
    )
    assert total == 6
