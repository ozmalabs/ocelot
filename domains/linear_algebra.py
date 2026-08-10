"""Linear algebra — matrices over the number floor, a new structural floor.

Number gave magnitude; groups/rings gave structure; this floor is the one a
large share of mathematics (and of HLE) is phrased in: matrices, determinants,
rank, invertibility — the arithmetic of linear maps over a field. A matrix lives
in the graph (a Matrix node with Entry nodes carrying row/col/value); the
operations read it off the graph and compute — the same computational shape as
the group-theory algorithms (KB / Todd–Coxeter) over graph-resident data.

The determinant is computed by RECURSIVE Laplace (cofactor) expansion — an
(n×n) determinant is a signed sum of (n−1)×(n−1) determinants — so this floor
sits directly on the recursion floor: a structure reduced to its base (the 1×1
determinant) by recursing on size.
"""
from __future__ import annotations

from substrate_rs import _native

_TYPES = ("Matrix", "Entry", "MatMul")
_EDGES = ("entry", "lhs", "rhs", "out", "used_with")


def new_graph():
    """A native substrate carrying a permissive grammar for the matrix schema
    (Matrix/Entry/MatMul linked by entry/lhs/rhs/out/used_with). The Rust engine
    checks Γ-admissibility on every add; these open productions admit the shapes
    `make_matrix` and `matmul` construct."""
    g = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for e in _EDGES:
                g.add_production({
                    "src": {"type": a, "var": "s"}, "edge_type": e,
                    "tgt": {"type": b, "var": "t"}, "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "linear_algebra"})
    return g


def make_matrix(graph, name: str, rows: list[list]) -> int:
    """Store a matrix in the graph: a Matrix node + an Entry node per cell
    (row, col, value). Returns the Matrix node id."""
    nr, nc = len(rows), (len(rows[0]) if rows else 0)
    mid = graph.add_node("Matrix", {"id": f"mat_{name}", "n_rows": nr, "n_cols": nc})
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            e = graph.add_node("Entry", {"id": f"{name}_{i}_{j}",
                                         "row": i, "col": j, "value": v})
            graph.add_edge(mid, "entry", e, {})
    return mid


def read(graph, M) -> list[list]:
    """Reconstruct the matrix as a grid of values from the graph."""
    a = graph.node(M)["attrs"]
    nr, nc = a["n_rows"], a["n_cols"]
    grid = [[None] * nc for _ in range(nr)]
    for tgt in graph.neighbours(M, "entry"):
        ea = graph.node(tgt)["attrs"]
        grid[ea["row"]][ea["col"]] = ea["value"]
    return grid


def _determinant_grid(grid: list[list]):
    """det = Σ over permutations σ of sgn(σ)·∏_i M[i][σ(i)] — Leibniz's formula,
    ridden on the SEARCH LAYER. The permutations are enumerated by backtracking
    (assign each Row a distinct Col; a column reused twice is pruned), and the
    signed product is a graph-resident Term (``Prod`` of the chosen entries times
    the inversion-parity sign) summed over the leaves by the native ``Substrate.search``.
    (Laplace's recursion and Leibniz's sum are the same determinant — this one
    rides the engine rather than Python recursion.)"""
    from substrate_rs import (And, Attr, Count, Eq, Exists, Filter, Gt, IfThenElse,
                              InNeighbours, Lit, Lt, Mod, Neighbours, Pick, Prod,
                              Sum, Times, Var, _native)

    n = len(grid)
    if n == 0:
        return 1

    # Native substrate with a permissive grammar for the determinant schema.
    g = _native.Substrate()
    _T = ("Matrix", "Entry", "Rows", "Cols", "Row", "Col")
    for a in _T:
        for b in _T:
            for e in ("entry", "row", "col", "pick"):
                g.add_production({
                    "src": {"type": a, "var": "s"}, "edge_type": e,
                    "tgt": {"type": b, "var": "t"}, "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "det"})
    Ms = g.add_node("Matrix", {"n_rows": n, "n_cols": n})
    for i in range(n):
        for j in range(n):
            g.add_edge(Ms, "entry", g.add_node(
                "Entry", {"row": i, "col": j, "value": grid[i][j]}), {})
    rows_anchor = g.add_node("Rows", {})
    cols_anchor = g.add_node("Cols", {})
    for i in range(n):
        g.add_edge(rows_anchor, "row", g.add_node("Row", {"idx": i}), {})
    for j in range(n):
        g.add_edge(cols_anchor, "col", g.add_node("Col", {"idx": j}), {})

    entries = Neighbours(Var("Ms"), "entry")
    all_rows = Neighbours(Var("rows_anchor"), "row")

    def colidx(rv):                                 # column σ assigned to row rv
        return Attr(Pick(Neighbours(Var(rv), "pick")), "idx")

    def entry_val(rv):                              # M[rv][σ(rv)]
        e = Pick(Filter(entries, "e", And(items=(
            Eq(a=Attr(Var("e"), "row"), b=Attr(Var(rv), "idx")),
            Eq(a=Attr(Var("e"), "col"), b=colidx(rv))))))
        return Attr(e, "value")

    product = Prod(source=all_rows, var_name="r", value=entry_val("r"))
    inversions = Sum(source=all_rows, var_name="r1", value=Count(Filter(
        all_rows, "r2", And(items=(
            Gt(a=Attr(Var("r2"), "idx"), b=Attr(Var("r1"), "idx")),
            Lt(a=colidx("r2"), b=colidx("r1")))))))
    sgn = IfThenElse(cond=Eq(a=Mod(a=inversions, b=Lit(2)), b=Lit(0)),
                     then=Lit(1), other=Lit(-1))
    value_term = Times(items=(sgn, product))

    open_term = Filter(all_rows, "r",
                       Eq(a=Count(Neighbours(Var("r"), "pick")), b=Lit(0)))
    options_term = Neighbours(Var("cols_anchor"), "col")
    fail_term = Exists(Neighbours(Var("cols_anchor"), "col"), "c",
                       Gt(a=Count(InNeighbours(Var("c"), "pick")), b=Lit(1)))
    # Leibniz's signed sum over permutations, enumerated by the Rust-native
    # backtracking search (graph-resident strategy Terms; assign each Row a Col,
    # prune a reused Col, sum the signed product over the leaves).
    return g.search(open_term.to_dict(), options_term.to_dict(), "pick",
                    fail_term.to_dict(), value_term.to_dict(), None,
                    {"Ms": Ms, "rows_anchor": rows_anchor,
                     "cols_anchor": cols_anchor})


def determinant(graph, M):
    """det(M), read off the graph and computed on the search layer (Leibniz)."""
    return _determinant_grid(read(graph, M))


def trace(graph, M):
    """tr(M) = Σ of the diagonal — a graph-resident Term-tree (Sum over the
    entries with row==col), evaluated by the engine, not Python arithmetic."""
    from substrate_rs import Attr, Eq, Filter, Neighbours, Sum, Var
    term = Sum(Filter(Neighbours(Var("x"), "entry"), "e",
                      Eq(a=Attr(Var("e"), "row"), b=Attr(Var("e"), "col"))),
               "e", Attr(Var("e"), "value"))
    return term.evaluate({"x": M}, graph)


def matmul(graph, name: str, A, B) -> int:
    """A·B, computed ON THE ENGINE: a result Matrix of zero cells plus a graph-
    resident accumulation rule the engine runs to a fixpoint — for matching an
    a-entry (row i, col k), a b-entry (row k, col j) and the result cell (i, j),
    add a·b into the cell, each (a,b) product consumed once via a ``used_with``
    marker. The arithmetic is a ``Plus``/``Times`` Term; Python only turns the
    crank. Markers + the linking MatMul node are removed afterwards."""
    from substrate_rs import (And, Attr, Eq, In, Neighbours, Not, Plus,
                              Times, Var)

    a, b = read(graph, A), read(graph, B)
    nr, nc = len(a), (len(b[0]) if b else 0)
    C = make_matrix(graph, name, [[0] * nc for _ in range(nr)])
    m = graph.add_node("MatMul", {"id": f"mm_{name}"})
    graph.add_edge(m, "lhs", A, {})
    graph.add_edge(m, "rhs", B, {})
    graph.add_edge(m, "out", C, {})
    # The accumulation rule, run to a fixed point on the Rust-native engine: for
    # an a-entry (i,k), b-entry (k,j) and result cell (i,j) not yet paired, add
    # a·b into the cell and mark the (a,b) product consumed via `used_with`.
    acc = Plus(items=(Attr(Var("p"), "value"),
                      Times(items=(Attr(Var("a"), "value"),
                                   Attr(Var("b"), "value")))))
    rule = {
        "name": f"matmul_{name}",
        "match": [["m", "lhs", "A"], ["A", "entry", "a"],
                  ["m", "rhs", "B"], ["B", "entry", "b"],
                  ["m", "out", "C"], ["C", "entry", "p"]],
        "where": And(items=(
            Eq(a=Attr(Var("a"), "col"), b=Attr(Var("b"), "row")),
            Eq(a=Attr(Var("p"), "row"), b=Attr(Var("a"), "row")),
            Eq(a=Attr(Var("p"), "col"), b=Attr(Var("b"), "col")),
            Not(arg=In(member=Var("b"),
                       container=Neighbours(Var("a"), "used_with"))))).to_dict(),
        "effects": [["set_attr", "p", "value", {"__term__": acc.to_dict()}],
                    ["add_edge", "a", "used_with", "b"]],
    }
    idx = graph.add_rule(rule)
    while graph.apply_rule_once(idx):   # run only this rule to a fixed point
        pass
    for ea in list(graph.neighbours(A, "entry")):   # clean up the scratch markers
        for uw in list(graph.neighbours(ea, "used_with")):
            graph.remove_edge(ea, "used_with", uw)
    graph.remove_node(m)
    return C


def is_invertible(graph, M) -> bool:
    """Over a field, M is invertible iff det(M) ≠ 0."""
    return determinant(graph, M) != 0


def rank(graph, M) -> int:
    """rank(M) = the largest r for which some r×r submatrix has nonzero
    determinant. Each minor's determinant is computed on the engine
    (``_determinant_grid``); the choice of which r rows and columns to take is a
    mechanical enumeration over the candidates."""
    import itertools

    grid = read(graph, M)
    nr, nc = len(grid), (len(grid[0]) if grid else 0)
    for r in range(min(nr, nc), 0, -1):
        for rs in itertools.combinations(range(nr), r):
            for cs in itertools.combinations(range(nc), r):
                if _determinant_grid([[grid[i][j] for j in cs] for i in rs]) != 0:
                    return r
    return 0


def solve_linear_system(A: list[list], b: list):
    """Solve the square system A x = b by CRAMER'S RULE, reusing the engine
    determinant: x_i = det(A_i)/det(A), where A_i is A with column i replaced by
    b. Returns the exact solution vector (ints / Fractions), or None if det(A)=0
    (no unique solution — singular) or A isn't square."""
    from fractions import Fraction

    n = len(A)
    if n == 0 or any(len(row) != n for row in A) or len(b) != n:
        return None
    det_a = _determinant_grid(A)
    if det_a == 0:
        return None
    out = []
    for i in range(n):
        a_i = [row[:i] + [b[r]] + row[i + 1:] for r, row in enumerate(A)]
        x = Fraction(_determinant_grid(a_i)) / Fraction(det_a)
        out.append(int(x) if x.denominator == 1 else x)
    return out
