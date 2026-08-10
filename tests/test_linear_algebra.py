"""Tests for the linear-algebra floor — matrices over the number floor.

A matrix lives in the graph (Matrix + Entry nodes); operations read it and
compute. The determinant is RECURSIVE (Laplace expansion → it sits on the
recursion floor). Validated against hand-computable values.
"""
from __future__ import annotations

from domains import linear_algebra as la


def _g():
    return la.new_graph()


def test_determinant_recursive_laplace():
    g = _g()
    assert la.determinant(g, la.make_matrix(g, "A", [[1, 2], [3, 4]])) == -2
    # 3x3 by recursive cofactor expansion
    assert la.determinant(g, la.make_matrix(g, "C", [[1, 2, 3], [4, 5, 6], [7, 8, 10]])) == -3
    # identity has determinant 1, at any size
    I3 = la.make_matrix(g, "I", [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert la.determinant(g, I3) == 1


def test_matmul_and_trace():
    g = _g()
    A = la.make_matrix(g, "A", [[1, 2], [3, 4]])
    B = la.make_matrix(g, "B", [[5, 6], [7, 8]])
    assert la.read(g, la.matmul(g, "AB", A, B)) == [[19, 22], [43, 50]]
    assert la.trace(g, A) == 5


def test_solve_linear_system_cramer():
    # A x = b by Cramer's rule (reusing the engine determinant)
    assert la.solve_linear_system([[2, 1], [1, 3]], [5, 10]) == [1, 3]
    assert la.solve_linear_system([[1, 1, 1], [0, 2, 5], [2, 5, -1]],
                                  [6, -4, 27]) == [5, 3, -2]
    assert la.solve_linear_system([[1, 2], [2, 4]], [3, 6]) is None   # singular


def test_invertibility_and_rank():
    g = _g()
    A = la.make_matrix(g, "A", [[1, 2], [3, 4]])       # det -2 ≠ 0
    D = la.make_matrix(g, "D", [[1, 2], [2, 4]])       # rows dependent
    assert la.is_invertible(g, A) is True
    assert la.is_invertible(g, D) is False
    assert la.rank(g, A) == 2
    assert la.rank(g, D) == 1
    assert la.rank(g, la.make_matrix(g, "C", [[1, 2, 3], [4, 5, 6], [7, 8, 10]])) == 3
