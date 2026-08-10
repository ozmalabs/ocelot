"""Representation theory — groups acting by matrices.

The bridge from the group floor to the linear-algebra floor: a representation
ρ: G → GL(V) sends each group element to an invertible matrix, respecting the
product (ρ(gh)=ρ(g)ρ(h)). It is a homomorphism into matrices — so it sits on
BOTH floors at once. Each generator gets a matrix (stored in the graph); ρ of a
word is the product of its letters' matrices. A map is a genuine representation
iff it kills the relators (ρ(r)=I), and the CHARACTER χ(g)=trace ρ(g) is the
invariant that, in full representation theory, lets element-counts and structure
be read off without enumerating the group.
"""
from __future__ import annotations

from substrate_rs import _native

_TYPES = ("Representation", "GenRep", "MEntry")
_EDGES = ("maps", "mentry")


def new_graph():
    """A native substrate carrying a permissive grammar for the representation
    schema (Representation/GenRep/MEntry linked by maps/mentry)."""
    g = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for e in _EDGES:
                g.add_production({
                    "src": {"type": a, "var": "s"}, "edge_type": e,
                    "tgt": {"type": b, "var": "t"}, "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "representation"})
    return g


def _ident(n):
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def _matmul(a, b):
    n, k, m = len(a), len(b), len(b[0])
    return [[sum(a[i][p] * b[p][j] for p in range(k)) for j in range(m)]
            for i in range(n)]


def representation(graph, name: str, gen_matrices: dict) -> int:
    """Store a representation: a Representation node and, per generator, a
    GenRep node carrying the symbol and its matrix (entries as MEntry nodes)."""
    dim = len(next(iter(gen_matrices.values())))
    rid = graph.add_node("Representation", {"id": f"rep_{name}", "dim": dim})
    for sym, mat in gen_matrices.items():
        gr = graph.add_node("GenRep", {"id": f"{name}_{sym}", "symbol": sym})
        graph.add_edge(rid, "maps", gr, {})
        for i, row in enumerate(mat):
            for j, v in enumerate(row):
                e = graph.add_node("MEntry", {"row": i, "col": j, "value": v})
                graph.add_edge(gr, "mentry", e, {})
    return rid


def _gen_matrix(graph, rep, sym: str):
    dim = graph.node(rep)["attrs"]["dim"]
    for gr in graph.neighbours(rep, "maps"):
        if graph.node(gr)["attrs"]["symbol"] == sym:
            mat = [[0] * dim for _ in range(dim)]
            for me in graph.neighbours(gr, "mentry"):
                a = graph.node(me)["attrs"]
                mat[a["row"]][a["col"]] = a["value"]
            return mat
    raise KeyError(sym)


def rho(graph, rep, word: str):
    """ρ(word): the product of the generators' matrices (identity for ε)."""
    dim = graph.node(rep)["attrs"]["dim"]
    m = _ident(dim)
    for sym in word:
        m = _matmul(m, _gen_matrix(graph, rep, sym))
    return m


def is_representation(graph, rep, relators: list[str]) -> bool:
    """A genuine representation respects the relations: ρ(r) = I for every
    relator r (so equal group elements get equal matrices)."""
    dim = graph.node(rep)["attrs"]["dim"]
    I = _ident(dim)
    return all(rho(graph, rep, r) == I for r in relators)


def character(graph, rep, word: str):
    """χ(g) = trace ρ(g) — the class function at the heart of the theory."""
    m = rho(graph, rep, word)
    return sum(m[i][i] for i in range(len(m)))
