"""Probability — finite probability spaces, on the counting/arithmetic floor.

A finite probability space is a set of weighted outcomes; an event is a subset;
P(event) is the share of weight it carries. Everything is exact (Fraction) —
no floating point — because finite probability is just counting over the number
floor. The space lives in the graph (a Space node with weighted Outcome nodes);
the measures read it and compute. Conditional probability, expectation, and
independence all fall out of the one ratio P = weight(event)/weight(space).
"""
from __future__ import annotations

from substrate_rs import (Attr, Div, Filter, In, Lit, Neighbours, SetT, Sum,
                          Var, _native)

_TYPES = ("Space", "Outcome")
_EDGES = ("outcome",)

_OUT = Neighbours(Var("x"), "outcome")            # the space's outcomes
_TOTAL = Sum(_OUT, "o", Attr(Var("o"), "weight"))  # total weight (a Term)


def new_graph():
    """A native substrate carrying a permissive grammar for the probability-space
    schema (Space linked to weighted Outcome nodes)."""
    g = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for e in _EDGES:
                g.add_production({
                    "src": {"type": a, "var": "s"}, "edge_type": e,
                    "tgt": {"type": b, "var": "t"}, "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "probability"})
    return g


def _eval(term, space, graph):
    return term.evaluate({"x": space}, graph)


def make_space(graph, name: str, outcomes: dict) -> int:
    """Store a finite space: ``outcomes`` maps label → (value, weight) (value is
    the number a random variable reads; weight defaults to 1 = uniform)."""
    sid = graph.add_node("Space", {"id": f"space_{name}"})
    for label, spec in outcomes.items():
        value, weight = (spec if isinstance(spec, tuple) else (spec, 1))
        o = graph.add_node("Outcome", {"id": f"{name}_{label}", "label": label,
                                       "value": value, "weight": weight})
        graph.add_edge(sid, "outcome", o, {})
    return sid


def _outcomes(graph, space) -> dict:
    out = {}
    for t in graph.neighbours(space, "outcome"):
        a = graph.node(t)["attrs"]
        out[a["label"]] = (a["value"], a["weight"])
    return out


def prob(graph, space, event: set):
    """P(event) — a graph-resident Term-tree the engine evaluates:
        Sum(weight over outcomes whose label ∈ event) / Sum(weight over all).
    The reasoning is the DSL expression, not Python arithmetic."""
    in_event = In(member=Attr(Var("o"), "label"),
                  container=SetT(items=tuple(Lit(lbl) for lbl in event)))
    term = Div(a=Sum(Filter(_OUT, "o", in_event), "o", Attr(Var("o"), "weight")),
               b=_TOTAL)
    return _eval(term, space, graph)


def conditional(graph, space, A: set, B: set):
    """P(A | B) = P(A∩B) / P(B)."""
    return prob(graph, space, A & B) / prob(graph, space, B)


def expectation(graph, space):
    """E[X] = Σ value·weight / Σ weight — as a Term-tree over the outcomes."""
    from substrate_rs import Times
    term = Div(a=Sum(_OUT, "o", Times(items=(Attr(Var("o"), "value"),
                                             Attr(Var("o"), "weight")))),
               b=_TOTAL)
    return _eval(term, space, graph)


def independent(graph, space, A: set, B: set) -> bool:
    """A ⟂ B iff P(A∩B) = P(A)·P(B)."""
    return prob(graph, space, A & B) == prob(graph, space, A) * prob(graph, space, B)
