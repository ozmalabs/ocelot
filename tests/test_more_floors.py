"""Tests for the gap-filling floors: representation theory, probability,
analysis, topology/geometry. Each grounded over earlier floors (groups +
linear algebra; counting; limits; vectors + reachability)."""
from __future__ import annotations

import math

from domains import analysis as an
from domains import probability as pr
from domains import representation as rep
from domains import topology as tp


# --- representation theory (groups → matrices) ---

def test_representation_and_character():
    g = rep.new_graph()
    R = rep.representation(g, "S3", {
        "a": [[0, 1, 0], [1, 0, 0], [0, 0, 1]],     # (1 2)
        "b": [[1, 0, 0], [0, 0, 1], [0, 1, 0]]})    # (2 3)
    assert rep.is_representation(g, R, ["aa", "bb", "ababab"]) is True
    assert rep.character(g, R, "") == 3             # χ(e) = dim
    assert rep.character(g, R, "a") == 1            # transposition: 1 fixed point
    assert rep.character(g, R, "ab") == 0           # 3-cycle: 0 fixed points
    # a map that breaks a relation is NOT a representation
    bad = rep.representation(g, "bad", {"a": [[1, 0], [0, 1]], "b": [[1, 1], [0, 1]]})
    assert rep.is_representation(g, bad, ["bb"]) is False   # b² ≠ I


# --- probability (finite, exact) ---

def test_probability_die_and_independence():
    # measures are now graph-resident Term-trees (Sum/Filter/Div) → float
    g = pr.new_graph()
    die = pr.make_space(g, "die", {i: (i, 1) for i in range(1, 7)})
    assert pr.prob(g, die, {2, 4, 6}) == 0.5
    assert pr.expectation(g, die) == 3.5
    assert abs(pr.conditional(g, die, {2, 4, 6}, {4, 5, 6}) - 2 / 3) < 1e-9
    coins = pr.make_space(g, "coins", {"HH": 1, "HT": 1, "TH": 1, "TT": 1})
    assert pr.independent(g, coins, {"HH", "HT"}, {"HH", "TH"}) is True
    assert pr.independent(g, coins, {"HH", "HT"}, {"HH", "HT"}) is False


# --- analysis (limits, series, derivative, integral) ---

def test_analysis_limits_and_calculus():
    assert abs(an.limit_of_sequence(lambda n: 1 / n)) < 1e-4
    assert an.converges_to(lambda n: (1 + 1 / n) ** n, math.e)
    assert an.limit_of_sequence(lambda n: float(n)) is None        # diverges
    assert abs(an.series_sum(lambda k: 0.5 ** k) - 1.0) < 1e-6
    assert abs(an.derivative(lambda x: x * x, 3) - 6) < 1e-4
    assert abs(an.integral(lambda x: x * x, 0, 1) - 1 / 3) < 1e-4
    assert abs(an.integral(math.sin, 0, math.pi) - 2) < 1e-3


# --- topology / geometry (reuses vectors + reachability) ---

def test_topology_euler_and_connectedness():
    g = tp.new_graph()
    tet = tp.make_complex(g, "tet", [0, 1, 2, 3],
                          [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
                          [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
    assert tp.euler_characteristic(g, tet) == 2        # sphere
    assert tp.is_connected(g, tet) is True
    disj = tp.make_complex(g, "d", [0, 1, 2, 3], [(0, 1), (2, 3)], [])
    assert tp.connected_components(g, disj) == 2


def test_geometry_reuses_vector_primitives():
    g = tp.new_graph()
    p = g.add_node("P", {"pos": (0.0, 0.0)})
    q = g.add_node("P", {"pos": (3.0, 4.0)})
    b = g.add_node("P", {"pos": (1.0, 0.0)})
    c = g.add_node("P", {"pos": (0.0, 1.0)})
    assert tp.distance_term().evaluate({"p": p, "q": q}, g) == 5.0
    # right angle at p between p→b and p→c  ⇔  Dot = 0
    assert tp.right_angle_term().evaluate({"a": p, "b": b, "c": c}, g) == 0
