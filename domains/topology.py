"""Topology & geometry — built on existing floors, by design.

This floor crosses over heavily with what the substrate already has:
  * GEOMETRY reuses the DSL's vector primitives — the very ones the vision and
    motor systems use: distance = ‖p−q‖ (Magnitude of VecSub), a right angle is
    a zero Dot product, angle = AngleBetween. So geometric concepts ground as
    Term-trees over point positions, no new machinery.
  * CONNECTEDNESS reuses the reachability recursion (the "reachable_from_zero"
    shape): a space is connected iff every vertex is reachable from one — the
    same backward/forward recursion over a relation.
  * The EULER CHARACTERISTIC V−E+F is pure counting over the number floor; the
    FUNDAMENTAL GROUP of a complex is a finitely-presented group (the FP-group
    floor) — topology feeding back into algebra.

A complex (vertices, edges, faces) lives in the graph; the invariants read it.
Runs on the Rust-native engine (``substrate_rs``): graph ops, Term evaluation,
and the reachability rewrite all execute in Rust. No Python rule engine.
"""
from __future__ import annotations

from substrate_rs import (Attr, Count, Dot, In, Magnitude, Neighbours, Not,
                          Plus, Minus, Var, VecSub, _native)

_TYPES = ("Complex", "Vertex", "Edge", "Face", "FaceRef", "Reach", "P")
_EDGES = ("vertex", "edge", "face", "adj", "reached")


def new_graph():
    """A substrate carrying a permissive grammar for the complex schema. The
    Rust engine checks Γ-admissibility on every add; these open productions
    admit the shapes `make_complex` and the reachability rule construct."""
    g = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for e in _EDGES:
                g.add_production({
                    "src": {"type": a, "var": "s"},
                    "edge_type": e,
                    "tgt": {"type": b, "var": "t"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "topology",
                })
    return g


def make_complex(graph, name: str, vertices, edges, faces=()) -> int:
    """A cell complex in the graph: Vertex/Edge/Face nodes, with vertices linked
    by ``adj`` edges (for reachability) and the counts cached for V−E+F."""
    cid = graph.add_node("Complex", {"id": f"cx_{name}",
                                     "V": len(vertices), "E": len(edges),
                                     "F": len(faces)})
    vid = {}
    for v in vertices:
        n = graph.add_node("Vertex", {"id": f"{name}_v{v}", "label": v})
        vid[v] = n
        graph.add_edge(cid, "vertex", n, {})
    for u, w in edges:
        e = graph.add_node("Edge", {"id": f"{name}_e{u}_{w}"})
        graph.add_edge(cid, "edge", e, {})
        graph.add_edge(vid[u], "adj", vid[w], {})
        graph.add_edge(vid[w], "adj", vid[u], {})
    for f in faces:
        graph.add_node("Face", {"id": f"{name}_f{'_'.join(map(str, f))}"})
        graph.add_edge(cid, "face",
                       graph.add_node("FaceRef", {"cells": list(f)}), {})
    return cid


def euler_characteristic(graph, cx) -> int:
    """χ = V − E + F — a graph-resident Term-tree (Count over the complex's
    vertex / edge / face nodes), evaluated by the engine. 2 for a sphere."""
    term = Plus(items=(Minus(a=Count(Neighbours(Var("x"), "vertex")),
                             b=Count(Neighbours(Var("x"), "edge"))),
                       Count(Neighbours(Var("x"), "face"))))
    return term.evaluate({"x": cx}, graph)


def connected_components(graph, cx) -> int:
    """Number of connected components, by CONSTRUCTING reachability with a
    graph-resident rewrite rule: mark a seed reached, then SPREAD —
        (Reach -reached-> v) ∧ (v -adj-> u) ∧ u not-yet-reached  ⟹  mark u
    — applied to a fixed point by the rewrite engine. (Cyclic reachability needs
    the visited-state that read-only Term-trees can't hold, so it's a
    constructive procedure, not a pure recursion.) Components = seeds needed."""
    verts = list(graph.neighbours(cx, "vertex"))
    reach = graph.add_node("Reach", {"id": f"reach_{cx}"})
    # One rule, applied only to this Reach node via apply_rule_once to a fixed
    # point — run_rules() would also fire any other installed rules.
    spread_idx = graph.add_rule({
        "name": f"spread_{cx}",
        "match": [["R", "reached", "v"], ["v", "adj", "u"]],
        "where": Not(arg=In(member=Var("u"),
                            container=Neighbours(Var("R"), "reached"))).to_dict(),
        "effects": [["add_edge", "R", "reached", "u"]],
    })
    comps, reached = 0, set()
    for start in verts:
        if start in reached:
            continue
        comps += 1
        graph.add_edge(reach, "reached", start, {})
        while graph.apply_rule_once(spread_idx):
            pass
        reached = set(graph.neighbours(reach, "reached"))
    graph.remove_node(reach)
    return comps


def is_connected(graph, cx) -> bool:
    return connected_components(graph, cx) == 1


# --- geometry as Term-trees reusing the DSL's vector primitives ---

def distance_term():
    """‖p − q‖ — Euclidean distance, the same Magnitude/VecSub the vision and
    motor systems use. Evaluate with p, q bound to nodes carrying a ``pos``."""
    return Magnitude(VecSub(a=Attr(Var("p"), "pos"), b=Attr(Var("q"), "pos")))


def right_angle_term():
    """A right angle at a between rays a→b and a→c: their Dot product is 0."""
    return Dot(a=VecSub(a=Attr(Var("b"), "pos"), b=Attr(Var("a"), "pos")),
               b=VecSub(a=Attr(Var("c"), "pos"), b=Attr(Var("a"), "pos")))
