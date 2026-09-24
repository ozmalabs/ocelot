"""Equation solving — algebra by REWRITING, on the engine.

A linear equation in one unknown is solved the way a student is taught: do the
same operation to both sides to peel the operations off the unknown until it
stands alone. That's term rewriting — the substrate's own foundation. The
equation is an expression graph (Op / Const / Unknown nodes, each marked whether
its subtree contains the unknown), and graph-resident rewrite rules invert the
outermost operation on the unknown's side, applying its inverse to the other
side, to a fixed point ``x = <constant expression>``. The rules ARE the algebra;
Python only builds the graph and evaluates the final constant side.

Runs on the Rust-native rule engine (``substrate_rs`` ``Substrate.add_rule`` +
``run_rules``) — the graph-resident rules are installed and driven to a fixed
point in Rust. No Python rule engine.

Scope: linear, the unknown appearing once (the common case, and the shape the
HLE control/Sylvester-style problems reduce to). x-on-both-sides needs a collect
step; nonlinear needs more — both return None here (an honest miss).
"""
from __future__ import annotations

from fractions import Fraction

from substrate_rs import And, Attr, Eq, Lit, Var, _native

# (op on the unknown's side, which child holds x) → (inverse op, its operands).
# Operands are drawn from R (current other side), and the non-x sibling.
_INV = {
    ("+", "L"): ("-", ("R", "B")), ("+", "R"): ("-", ("R", "A")),
    ("-", "L"): ("+", ("R", "B")), ("-", "R"): ("-", ("A", "R")),
    ("*", "L"): ("/", ("R", "B")), ("*", "R"): ("/", ("R", "A")),
    ("/", "L"): ("*", ("R", "B")), ("/", "R"): ("/", ("A", "R")),
}

_TYPES = ("Eq", "Op", "Unknown", "Const")
_EDGES = ("lhs", "rhs", "left", "right")


def _new_graph():
    """A substrate carrying a permissive grammar for the expression-graph
    schema (Eq/Op/Unknown/Const linked by lhs/rhs/left/right). The Rust
    engine checks Γ-admissibility on every add; these open productions admit
    exactly the shapes `_build` and the rewrite rules construct."""
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
                    "provenance": "equation",
                })
    return g


def _attrs(graph, node) -> dict:
    return graph.node(node)["attrs"]


def _build(graph, expr, unknown: str) -> int:
    """An expression (number | unknown | (op, a, b)) → an expression graph,
    each node tagged ``has_x`` (1 iff its subtree contains the unknown)."""
    if isinstance(expr, str) and expr == unknown:
        return graph.add_node("Unknown", {"has_x": 1})
    if isinstance(expr, (int, float, Fraction)):
        # Store the value as a string: the Rust substrate's attr Values are
        # int/float/str/bool and would coerce a Fraction to f64, losing
        # exactness. No rule inspects `value` (rules only read has_x/op), so
        # it round-trips losslessly as text; _eval parses it back.
        return graph.add_node(
            "Const", {"value": str(Fraction(expr)), "has_x": 0})
    op, a, b = expr
    A, B = _build(graph, a, unknown), _build(graph, b, unknown)
    hx = 1 if (_attrs(graph, A)["has_x"] or _attrs(graph, B)["has_x"]) else 0
    node = graph.add_node("Op", {"op": op, "has_x": hx})
    graph.add_edge(node, "left", A, {})
    graph.add_edge(node, "right", B, {})
    return node


def _solve_rules() -> list:
    """Swap (keep the unknown on the left) + the eight peel rules (one per
    operation × side): invert the outermost op on the unknown's side, applying
    its inverse to the other side, constructing the new other-side expression.
    Each rule is a dict in the wire format ``Substrate.add_rule`` parses."""
    rules = [{
        "name": "swap",
        "match": [["E", "lhs", "L"], ["E", "rhs", "R"]],
        "where": And(items=(Eq(a=Attr(Var("L"), "has_x"), b=Lit(0)),
                            Eq(a=Attr(Var("R"), "has_x"), b=Lit(1)))).to_dict(),
        "effects": [["del_edge", "E", "lhs", "L"],
                    ["del_edge", "E", "rhs", "R"],
                    ["add_edge", "E", "lhs", "R"],
                    ["add_edge", "E", "rhs", "L"]],
    }]
    for (op, side), (inv, (l, r)) in _INV.items():
        xchild, other = ("A", "B") if side == "L" else ("B", "A")
        rules.append({
            "name": f"peel_{op}_{side}",
            "match": [["E", "lhs", "O"], ["O", "left", "A"],
                      ["O", "right", "B"], ["E", "rhs", "R"]],
            "where": And(items=(
                Eq(a=Attr(Var("O"), "op"), b=Lit(op)),
                Eq(a=Attr(Var(xchild), "has_x"), b=Lit(1)),
                Eq(a=Attr(Var(other), "has_x"), b=Lit(0)),
                # only peel when the OTHER side is x-free, so the unknown
                # stays isolated (x-on-both-sides → no peel)
                Eq(a=Attr(Var("R"), "has_x"), b=Lit(0)))).to_dict(),
            "effects": [["del_edge", "E", "lhs", "O"],
                        ["add_edge", "E", "lhs", xchild],   # unknown's subtree
                        ["add_node", "NR", "Op", {"op": inv, "has_x": 0}],
                        ["add_edge", "NR", "left", l],
                        ["add_edge", "NR", "right", r],
                        ["del_edge", "E", "rhs", "R"],
                        ["add_edge", "E", "rhs", "NR"],
                        ["del_node", "O"]],
        })
    return rules


def _eval(graph, node) -> Fraction:
    """Evaluate a constant expression subtree (no unknown left)."""
    a = _attrs(graph, node)
    if "value" in a:
        return Fraction(a["value"])
    L = _eval(graph, graph.neighbours(node, "left")[0])
    R = _eval(graph, graph.neighbours(node, "right")[0])
    return {"+": L + R, "-": L - R, "*": L * R, "/": L / R}[a["op"]]


def solve_for(lhs, rhs, unknown: str = "x"):
    """Solve ``lhs = rhs`` for ``unknown`` by rewriting to a fixed point; returns
    the value (int when integral, else a Fraction), or None if it can't isolate
    the unknown (out of scope: nonlinear / unknown on both sides)."""
    g = _new_graph()
    E = g.add_node("Eq", {})
    g.add_edge(E, "lhs", _build(g, lhs, unknown), {})
    g.add_edge(E, "rhs", _build(g, rhs, unknown), {})
    for rule in _solve_rules():
        g.add_rule(rule)
    g.run_rules(100000)
    g.add_node("NativeEquationSolveReceipt", {
        "schema": "native_equation_solve_receipt_v1",
        "cluster": "equation.solve_for",
        "provenance": "native_rule_readback:equation_isolation",
        "native_rule": "equation_isolation_native_rules",
        "native_steps": ["build_equation", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    lhs_node = g.neighbours(E, "lhs")[0]
    if g.node(lhs_node)["type"] != "Unknown":
        return None                                         # couldn't isolate
    val = _eval(g, g.neighbours(E, "rhs")[0])
    return int(val) if val.denominator == 1 else val
