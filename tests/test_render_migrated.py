"""Graph-resident renderer, migrated — the agent PRODUCES surface from a source
Term via graph-resident RenderRules, on the seed-booted WorldAdapter with no
CuriousAgent. This is the reply/production half of language.

What makes it a real migration (not a mechanical mirror): the render ENGINE was
the deferred "Phase 6" — the Rust `Render` evaluator was a stub (returned None,
a render gap). The jabberwock built it via its self-modification keystone
(tools/jabberwock_build_render.py: guarded edit -> cargo check -> rollback-safe
-> rebuild). Now `Render` dispatches per source-Term head to the Language's
RenderRule, binds the rule's binding_pattern slots to the source's children
(child.<name> edges or scalar attrs), and EvalSubgraphs the template — nested
Render(Slot) sub-terms recurse. Pure graph composition; no Python engine.

WorldAdapter surface (mechanical): install_language / install_render_rule write
graph data; render(source, language) stores the source as a Term subgraph and
evaluates the Rust Render engine.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate import Cat, Surface, Slot, Render, Eq, Lit, Minus, IfThenElse
from substrate.world_adapter import WorldAdapter


def _S(payload):
    return Surface(kind="text", payload=payload)


def _adapter_with_python_rules():
    wa = WorldAdapter()
    wa.install_render_rule("python", "Lit",
                           template=Cat(items=(Slot(name="value"),)),
                           binding_pattern=["value"])
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
    wa.install_render_rule("python", "IfThenElse",
                           template=Cat(items=(_S("("), Render(term=Slot(name="then")),
                                               _S(" if "), Render(term=Slot(name="cond")),
                                               _S(" else "), Render(term=Slot(name="other")),
                                               _S(")"))),
                           binding_pattern=["cond", "then", "other"])
    return wa


# --- graph residence ----------------------------------------------------

def test_language_node_lives_in_the_graph():
    wa = WorldAdapter()
    nid = wa.install_language("python")
    assert wa.s.node(nid)["type"] == "Language"
    assert wa.s.node(nid)["attrs"]["name"] == "python"
    # idempotent
    assert wa.install_language("python") == nid


def test_install_render_rule_writes_to_graph():
    wa = _adapter_with_python_rules()
    eq_rules = wa.render_rules_for("python", "Eq")
    assert len(eq_rules) == 1
    rid = eq_rules[0]
    assert wa.s.node(rid)["type"] == "RenderRule"
    assert len(wa.inner.neighbours(rid, "template")) == 1


# --- the Rust render engine (the jabberwock's Phase-6 build) -------------

def test_engine_renders_simple_equality():
    wa = _adapter_with_python_rules()
    assert wa.render(Eq(a=Lit(5), b=Lit(0)), "python") == "(5 == 0)"


def test_engine_renders_nested_arithmetic_recursively():
    wa = _adapter_with_python_rules()
    assert wa.render(Minus(a=Lit(3), b=Lit(1)), "python") == "(3 - 1)"
    # Eq with a Minus subtree — recursion through two heads.
    assert wa.render(Eq(a=Lit(5), b=Minus(a=Lit(3), b=Lit(1))), "python") \
        == "(5 == (3 - 1))"


def test_engine_renders_if_then_else_recursively():
    wa = _adapter_with_python_rules()
    out = wa.render(
        IfThenElse(cond=Eq(a=Lit(5), b=Lit(0)), then=Lit(1),
                   other=Minus(a=Lit(3), b=Lit(1))), "python")
    assert out == "(1 if (5 == 0) else (3 - 1))"


def test_render_gap_returns_none_for_unknown_head():
    """No RenderRule for a head -> a render gap (None), not a crash."""
    wa = WorldAdapter()
    wa.install_language("python")          # language exists, but no rules
    assert wa.render(Lit(7), "python") is None
