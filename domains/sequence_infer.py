"""Inverse inference, mode 2 — HYPOTHESIS SEARCH for a generating recurrence.

Given a sequence, recover the rule R with s[n] = R(...). Unlike the cellular
automaton (whose rule the data fixes outright), a recurrence is found by SEARCH:
enumerate candidate rules from a hypothesis space, and keep those that, run
forward from the first terms, reproduce the whole sequence.

Each candidate rule is a graph-resident Term-tree over the sequence (which lives
in the graph as ``Pos`` nodes carrying ``idx``/``value``); ``s[n-k]`` is a
``Pick``/``Filter`` lookup, so even self-referential (Hofstadter-style) indices
like ``s[n - s[n-1] - 1]`` are expressible. Testing a candidate = evaluating its
Term to generate each next term and comparing to the data; the engine runs the
rule, Python only enumerates candidates and turns the generation crank.
"""
from __future__ import annotations

from substrate import (Attr, Eq, Filter, Lit, Minus, Neighbours, Pick, Plus,
                       Times, TypedGraph, Var)


def _seq_at(idx_term):
    """s[idx] as a Term: the value of the Pos node whose ``idx`` equals idx_term."""
    return Attr(Pick(Filter(Neighbours(Var("seq"), "pos"), "p",
                            Eq(a=Attr(Var("p"), "idx"), b=idx_term))), "value")


def _back(k):                                       # s[n-k]
    return _seq_at(Minus(a=Var("n"), b=Lit(k)))


def _affine1(a, c):
    return (Plus(items=(Times(items=(Lit(a), _back(1))), Lit(c))), 1,
            f"s[n] = {_lin(a, 's[n-1]')}{_const(c)}".replace("+ -", "- "))


def _linear2(a, b, c):
    return (Plus(items=(Times(items=(Lit(a), _back(1))),
                        Times(items=(Lit(b), _back(2))), Lit(c))), 2,
            f"s[n] = {_lin(a, 's[n-1]')} + {_lin(b, 's[n-2]')}{_const(c)}"
            .replace("+ -", "- "))


def _hofstadter(p, q, c1, c2):
    idx1 = Minus(a=Minus(a=Var("n"), b=_back(p)), b=Lit(c1))
    idx2 = Minus(a=Minus(a=Var("n"), b=_back(q)), b=Lit(c2))
    return (Plus(items=(_seq_at(idx1), _seq_at(idx2))), 2,
            f"s[n] = s[n - s[n-{p}] - {c1}] + s[n - s[n-{q}] - {c2}]")


def _lin(coef, term):
    if coef == 1:
        return term
    if coef == -1:
        return f"-{term}"
    return f"{coef}*{term}"


def _const(c):
    return "" if c == 0 else f" + {c}"


def _candidates():
    """The hypothesis space, simplest first: depth-1 affine, depth-2 linear,
    then self-referential (Hofstadter) index-shift rules."""
    for a in (1, -1, 2, 0):
        for c in (0, 1, -1, 2, -2):
            yield _affine1(a, c)
    for a in (1, 0, -1, 2):
        for b in (1, -1, 2, 0):
            for c in (0, 1, -1):
                yield _linear2(a, b, c)
    for p in (1, 2):
        for q in (1, 2):
            for c1 in (1, 0, 2):
                for c2 in (1, 0, 2):
                    yield _hofstadter(p, q, c1, c2)


def _fits(rule, n_init, seq) -> bool:
    """Seed the first ``n_init`` terms, then GENERATE the rest by evaluating the
    rule Term over the graph-resident sequence; True iff it matches everywhere."""
    g = TypedGraph()
    anchor = g._insert_node("Seq", {"id": "seq"})
    for i in range(1, n_init + 1):
        g._insert_edge(anchor, "pos", g._insert_node(
            "Pos", {"id": f"p{i}", "idx": i, "value": seq[i - 1]}))
    env = {"seq": anchor, "_resolve_concept": lambda n: None}
    for n in range(n_init + 1, len(seq) + 1):
        try:
            v = rule.evaluate({**env, "n": n}, g)
        except Exception:
            return False
        if v != seq[n - 1]:
            return False
        g._insert_edge(anchor, "pos", g._insert_node(
            "Pos", {"id": f"p{n}", "idx": n, "value": v}))
    return True


def infer_recurrence(seq: list[int]) -> str | None:
    """The simplest hypothesis-space rule that regenerates ``seq`` (or None).
    The search tries candidates simplest-first and returns the first that fits."""
    for rule, n_init, desc in _candidates():
        if len(seq) > n_init and _fits(rule, n_init, seq):
            return desc
    return None


def predict_next(seq: list[int]):
    """The next term of ``seq``: infer its recurrence (the simplest fitting
    rule), then evaluate that rule Term for index n+1 over the graph-resident
    sequence. None if no rule in the hypothesis space fits."""
    for rule, n_init, _ in _candidates():
        if len(seq) > n_init and _fits(rule, n_init, seq):
            g = TypedGraph()
            anchor = g._insert_node("Seq", {"id": "seq"})
            for i in range(1, len(seq) + 1):
                g._insert_edge(anchor, "pos", g._insert_node(
                    "Pos", {"id": f"p{i}", "idx": i, "value": seq[i - 1]}))
            env = {"seq": anchor, "n": len(seq) + 1,
                   "_resolve_concept": lambda n: None}
            try:
                return rule.evaluate(env, g)
            except Exception:
                return None
    return None
