"""Passability-aware spatial routing on the seed-booted WorldAdapter (no
CuriousAgent) — the routing the agent needs for grid worlds (ARC): distances
and first-hops that go AROUND learned walls, not through them.

ARCHITECTURE (the point of this migration): the routing is NOT Python.
  * The DECISION is graph-resident Terms (domains/spatial_routing.py):
    relax_step_term (the monotone Bellman step — what a distance is, which
    neighbour is passable) and passable_hop_term (the hop Argmax). Both are
    evaluated in Rust.
  * The fixpoint ITERATION is the native relax_to_fixpoint primitive (Rust) —
    NOT a Python loop, and NOT the incremental rule engine (whose dirty-bits
    key on matched edge types, not attrs read, so it cannot drive an
    attr-relaxation rule).
  * The adapter does ONLY mechanical I/O: stamp the _dist register, fire the
    Rust driver, evaluate the hop Term, gate on reachability.

A wall is an impassable Boundary (passable=False) that `blocks` the neighbour it
walls off; a cell with no learned boundary blocks nothing (plain adjacency), so
on an untested map this is identical to wall-blind BFS.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world(cells, edges, body_at, walls=()):
    """A spatial world: SpatialLocation cells + adjacency, a Body at `body_at`,
    and optional walls — each (cell, blocked_neighbour) an impassable Boundary
    of `cell` that `blocks` `blocked_neighbour`."""
    g = TypedGraph()
    body = g._insert_node("Body", {})
    nid = {n: g._insert_node("SpatialLocation", {"id": n}) for n in cells}
    for a, b in edges:
        g._insert_edge(nid[a], "adjacent_to", nid[b])
        g._insert_edge(nid[b], "adjacent_to", nid[a])
    for i, (cell, blocked) in enumerate(walls):
        w = g._insert_node("Boundary", {"id": f"wall_{cell}_{blocked}_{i}",
                                        "passable": False})
        g._insert_edge(nid[cell], "bounded_by", w)
        g._insert_edge(w, "blocks", nid[blocked])
    g._insert_edge(body, "at_location", nid[body_at])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _boot(cells, edges, body_at, walls=()):
    wa = WorldAdapter()
    wa.observe_locus(_world(cells, edges, body_at, walls))
    wis = {n: wa._instances[("SpatialLocation", n)] for n in cells}
    return wa, wis


# --- no walls: identical to wall-blind shortest path --------------------

def test_distances_no_walls_are_plain_shortest_path():
    wa, wis = _boot(["A", "B", "C", "D"],
                    [("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")], "A")
    d = wa.passable_distances_to(wis["D"])
    assert d[wis["D"]] == 0.0
    assert d[wis["A"]] == 1.0      # direct A-D edge, no wall
    assert d[wis["C"]] == 1.0


def test_hop_no_walls_takes_the_direct_edge():
    wa, wis = _boot(["A", "B", "C", "D"],
                    [("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")], "A")
    assert wa.plan_passable_step(wis["A"], wis["D"]) == wis["D"]


# --- a wall forces the detour -------------------------------------------

def test_distance_routes_around_a_wall():
    # direct A-D edge exists, but a wall blocks it: A must go A->B->C->D
    wa, wis = _boot(["A", "B", "C", "D"],
                    [("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")], "A",
                    walls=[("A", "D")])
    d = wa.passable_distances_to(wis["D"])
    assert d[wis["D"]] == 0.0
    assert d[wis["C"]] == 1.0
    assert d[wis["B"]] == 2.0
    assert d[wis["A"]] == 3.0      # around the wall, not the blocked direct hop


def test_hop_steps_around_a_wall():
    wa, wis = _boot(["A", "B", "C", "D"],
                    [("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")], "A",
                    walls=[("A", "D")])
    # first hop is B (toward the detour), never D (walled off)
    assert wa.plan_passable_step(wis["A"], wis["D"]) == wis["B"]


# --- walled off entirely: unreachable -----------------------------------

def test_unreachable_through_wall_is_dropped():
    # A's only edge to the rest is to B, but a wall blocks B -> A is isolated
    wa, wis = _boot(["A", "B", "C"],
                    [("A", "B"), ("B", "C")], "A", walls=[("A", "B")])
    d = wa.passable_distances_to(wis["C"])
    assert wis["C"] in d
    assert wis["A"] not in d                      # walled off => not present
    assert wa.plan_passable_step(wis["A"], wis["C"]) is None


# --- the routing lives in the graph, not Python -------------------------

def test_routing_terms_are_graph_resident_and_rust_driven():
    """The relax step + hop are graph-resident Terms; the fixpoint iteration is
    the native relax_to_fixpoint primitive. The adapter holds no routing loop."""
    wa, _ = _boot(["A", "B"], [("A", "B")], "A")
    relax_json, hop_json = wa._routing_terms()
    assert relax_json["type"] == "IfThenElse"     # the Bellman min-step Term
    assert hop_json["type"] == "Argmax"            # the hop choice Term
    assert hasattr(wa.inner, "relax_to_fixpoint")  # the Rust iteration driver
