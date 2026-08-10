"""Variadic-children rendering through the Rust `Render` engine, migrated.

The render benches (tests/test_renderer.py, tests/test_graph_renderer.py,
tests/test_teach_lua_renderer.py) all exercise templates with a VARIADIC
`items` slot — a slot bound to the ORDERED LIST of a source term's tuple
children (Times/Plus/Cat items), then either:

  * Join-ed (concatenate each child's render with a separator), e.g.
      Times -> "(a * b * ...)"  via  Join(" * ", Slot("items"))
  * Nth-indexed (binary access into them), e.g. the x86_64 renderer's
      Render(Nth(Slot("items"), 0)) / Render(Nth(Slot("items"), 1)).

Before this commit the Rust `Render` arm bound each binding-pattern name to
a SINGLE `child.<name>` neighbour, so a variadic field silently dropped all
but its first child and Join/Nth saw nothing. The fix:

  * Render binds a name to a `Value::Tuple` of ALL `child.<name>` child
    Nodes (in `index` edge-attr order, mirroring reflect.rs) when the field
    is tuple-shaped (multiple edges, or one carrying an `index` attr);
    a lone unindexed child still binds to a single `Value::Node`; a scalar
    field still binds to the attr value.
  * Join renders any `Value::Node` element it iterates via the active
    `render_lang` (so `Join(sep, Slot("items"))` over the child Nodes
    produces the per-child surface, joined).
  * Nth needs no change: it picks the i-th element of the Tuple (a Node),
    which the enclosing `Render(...)` then renders.

These tests drive the Rust engine directly (WorldAdapter.render -> the Rust
`Render` evaluator), with NO CuriousAgent and NO Python render loop.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate import (Attr, Cat, Eq, Holds, IfThenElse, Join, Lit, Lines,
                       Minus, Nth, Render, Slot, Surface, Times, Var)
from substrate.world_adapter import WorldAdapter


def _S(payload):
    return Surface(kind="text", payload=payload)


# The subject placeholder the spec layer emits for "value".
def _VALUE():
    return Attr(Var("x"), "value")


# --- a Python-style language with a VARIADIC Times rule -----------------

def _python_with_variadic_times() -> WorldAdapter:
    wa = WorldAdapter()
    wa.install_render_rule("python", "Lit",
                           template=Cat(items=(Slot(name="value"),)),
                           binding_pattern=["value"])
    # Attr(Var("x"), "value") -> the variable name "value".
    wa.install_render_rule("python", "Attr",
                           template=_S("value"),
                           binding_pattern=["node", "key"])
    wa.install_render_rule("python", "Eq",
                           template=Cat(items=(_S("("), Render(term=Slot(name="a")),
                                               _S(" == "), Render(term=Slot(name="b")),
                                               _S(")"))),
                           binding_pattern=["a", "b"])
    wa.install_render_rule("python", "Minus",
                           template=Cat(items=(_S("("), Render(term=Slot(name="a")),
                                               _S(" - "), Render(term=Slot(name="b")),
                                               _S(")"))),
                           binding_pattern=["a", "b"])
    # The variadic case: Times -> "(a * b * ...)" via Join over the items list.
    wa.install_render_rule("python", "Times",
                           template=Cat(items=(
                               _S("("),
                               Join(separator=_S(" * "), items=Slot(name="items")),
                               _S(")"))),
                           binding_pattern=["items"])
    # Holds(concept, node, node2) -> "concept(node)"
    wa.install_render_rule("python", "Holds",
                           template=Cat(items=(Slot(name="concept"), _S("("),
                                               Render(term=Slot(name="node")), _S(")"))),
                           binding_pattern=["concept", "node", "node2"])
    wa.install_render_rule("python", "IfThenElse",
                           template=Cat(items=(_S("("), Render(term=Slot(name="then")),
                                               _S(" if "), Render(term=Slot(name="cond")),
                                               _S(" else "), Render(term=Slot(name="other")),
                                               _S(")"))),
                           binding_pattern=["cond", "then", "other"])
    return wa


def test_join_renders_two_variadic_children():
    """The core fix: a 2-item Times renders all its children, not just the
    first. Without the variadic binding this returned "(2)" (first child
    only); with it, "(2 * 3)"."""
    wa = _python_with_variadic_times()
    assert wa.render(Times(items=(Lit(2), Lit(3))), "python") == "(2 * 3)"


def test_join_renders_three_variadic_children_in_index_order():
    """3+ items confirm the Tuple binding is ordered by the `index`
    edge-attr (reflect.rs parity), and Join walks all of them."""
    wa = _python_with_variadic_times()
    assert wa.render(Times(items=(Lit(2), Lit(3), Lit(5))), "python") \
        == "(2 * 3 * 5)"


def test_join_renders_nested_children():
    """Join must RENDER each child (not stringify it): the children here are
    themselves compound terms that recurse through other rules."""
    wa = _python_with_variadic_times()
    out = wa.render(Times(items=(Minus(a=Lit(7), b=Lit(2)), Lit(4))), "python")
    assert out == "((7 - 2) * 4)"


def test_factorial_body_renders_through_variadic_times():
    """End-to-end: the canonical factorial body. The Times arm is the
    variadic Join path; everything else is the single-child path. This is
    the headline shape from tests/test_renderer.py, rendered by the Rust
    engine."""
    wa = _python_with_variadic_times()
    term = IfThenElse(
        cond=Eq(a=_VALUE(), b=Lit(0)),
        then=Lit(1),
        other=Times(items=(
            _VALUE(),
            Holds(concept="factorial",
                  node=Minus(a=_VALUE(), b=Lit(1)),
                  node2=None))))
    out = wa.render(term, "python")
    assert out == "(1 if (value == 0) else (value * factorial((value - 1))))"


# --- single-child fields are unaffected by the variadic change ----------

def test_single_child_binding_still_works():
    """Regression: Eq/Minus bind single children (no `index` attr) to a lone
    Value::Node, exactly as before — the variadic path only triggers on
    tuple-shaped fields."""
    wa = _python_with_variadic_times()
    assert wa.render(Eq(a=Lit(5), b=Lit(0)), "python") == "(5 == 0)"
    assert wa.render(Minus(a=Lit(3), b=Lit(1)), "python") == "(3 - 1)"
    assert wa.render(Eq(a=Lit(5), b=Minus(a=Lit(3), b=Lit(1))), "python") \
        == "(5 == (3 - 1))"


# --- Nth indexes the variadic Tuple (the x86_64 renderer's access path) --

def _lang_with_nth_times() -> WorldAdapter:
    """A toy 'asm-ish' language whose Times rule uses Nth for binary access
    into the variadic items — the exact shape seed_x86_64_renderer uses
    (Render(Nth(Slot("items"), 0)) / Render(Nth(Slot("items"), 1)))."""
    wa = WorldAdapter()
    wa.install_render_rule("asmish", "Lit",
                           template=Cat(items=(_S("$"), Slot(name="value"))),
                           binding_pattern=["value"])
    wa.install_render_rule("asmish", "Times",
                           template=Lines(items=(
                               Render(term=Nth(items=Slot(name="items"), index=0)),
                               _S("    push"),
                               Render(term=Nth(items=Slot(name="items"), index=1)),
                               _S("    pop"),
                               _S("    imul"),
                           )),
                           binding_pattern=["items"])
    return wa


def test_nth_indexes_variadic_tuple():
    """Nth picks the i-th child Node from the variadic Tuple; the enclosing
    Render renders it. Index 0 -> first child, index 1 -> second child, in
    `index` order."""
    wa = _lang_with_nth_times()
    out = wa.render(Times(items=(Lit(2), Lit(3))), "asmish")
    expected = "$2\n    push\n$3\n    pop\n    imul"
    assert out == expected


def test_nth_respects_child_index_order():
    """Distinct literals confirm Nth(0) and Nth(1) map to the source's
    first/second tuple children, not insertion happenstance."""
    wa = _lang_with_nth_times()
    out = wa.render(Times(items=(Lit(11), Lit(22))), "asmish")
    assert out.startswith("$11\n")
    assert "$22\n" in out


# --- a render gap with a variadic head still degrades to None -----------

def test_variadic_head_with_no_rule_is_a_render_gap():
    wa = WorldAdapter()
    wa.install_language("python")     # no Times rule
    assert wa.render(Times(items=(Lit(2), Lit(3))), "python") is None