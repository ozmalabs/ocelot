"""Graph-resident renderer engine — migrated from test_graph_renderer.py.

test_graph_renderer.py exercises the Phase 6.1 graph-resident renderer
engine through the CuriousAgent surface.  This twin covers the same
functional ground using the seed-booted WorldAdapter with no CuriousAgent.

Coverage map (1:1):

  test_language_node_lives_in_the_graph
      -> covered (and deepened) by test_render_migrated.py.
         Repeated here for self-contained coverage; uses WorldAdapter.

  test_install_render_rule_writes_to_graph
      -> covered by test_render_migrated.py.
         Repeated here for self-contained coverage.

  test_engine_renders_simple_equality
  test_engine_renders_nested_arithmetic_recursively
  test_engine_renders_if_then_else_recursively
      -> all covered in test_render_migrated.py; repeated here.

  test_render_gap_returns_none_for_unhandled_head
      -> covered in test_render_migrated.py; repeated here.

  test_x86_64_renderer_emits_recursive_factorial_assembly
      -> fully migrated: WorldAdapter.seed_x86_64_renderer() +
         WorldAdapter._spec_to_term() (extended with Holds) +
         WorldAdapter.render().  Output is a plain string instead of
         the {"kind","payload"} dict that CuriousAgent.render_in_graph
         returned; all assembly-surface assertions are identical.

  test_parent_lang_inheritance
      -> fully migrated: WorldAdapter.install_language(parent_lang=...)
         stores a parent_lang graph edge; WorldAdapter.render() walks the
         parent chain at the Python boundary when the Rust engine returns
         None for the named language (the Rust Render evaluator only
         checks the immediate language's has_rule edges; the Python-level
         walk produces the same fallback semantics as CuriousAgent._rules_for).

TRIMMED (3 tests) — CuriousAgent impasse + teacher machinery:

  test_render_gap_spawns_impasse_with_diagnostic_attrs
      Needs render_in_graph() to record an Impasse node with
      reason="render_gap" attrs, queried via impasses().  This is the
      CuriousAgent impasse-recording + SOAR-impasse machinery; the
      WorldAdapter's render() returns None on a gap but does not create
      Impasse nodes (that is an agent decision, not a world-adapter I/O
      translation).

  test_render_gap_resolved_through_learn_from_teacher
      Needs learn_from_teacher() dispatching a "rule" entry into
      install_render_rule.  This is the CuriousAgent Frame/Mt absorption
      loop; the WorldAdapter has no learn_from_teacher method.

  test_render_gap_resolves_through_self_teacher_via_reflex
      Needs set_self_teacher() + master_tick() impasse-reflex spawn +
      drain_all_taught_threads().  All three belong to the CuriousAgent
      autonomous self-teaching loop; the WorldAdapter master_tick exists
      but carries no impasse-resolver reflex.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate import (Cat, Eq, IfThenElse, Lit, Minus, Render, Slot,
                       Surface, Times)
from substrate.world_adapter import WorldAdapter


def _S(payload):
    return Surface(kind="text", payload=payload)


def _adapter_with_python_rules():
    """WorldAdapter with the same rules _mk_python_agent_with_basic_rules
    installed in the original test."""
    wa = WorldAdapter()
    wa.install_render_rule("python", "Lit",
                           template=Cat(items=(Slot(name="value"),)),
                           binding_pattern=["value"])
    wa.install_render_rule("python", "Eq",
                           template=Cat(items=(
                               _S("("), Render(term=Slot(name="a")),
                               _S(" == "), Render(term=Slot(name="b")),
                               _S(")"))),
                           binding_pattern=["a", "b"])
    wa.install_render_rule("python", "Minus",
                           template=Cat(items=(
                               _S("("), Render(term=Slot(name="a")),
                               _S(" - "), Render(term=Slot(name="b")),
                               _S(")"))),
                           binding_pattern=["a", "b"])
    wa.install_render_rule("python", "IfThenElse",
                           template=Cat(items=(
                               _S("("), Render(term=Slot(name="then")),
                               _S(" if "), Render(term=Slot(name="cond")),
                               _S(" else "), Render(term=Slot(name="other")),
                               _S(")"))),
                           binding_pattern=["cond", "then", "other"])
    return wa


# --- graph residence (mirrors test_language_node_lives_in_the_graph) ------

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


# --- the Rust render engine -----------------------------------------------

def test_engine_renders_simple_equality():
    wa = _adapter_with_python_rules()
    assert wa.render(Eq(a=Lit(5), b=Lit(0)), "python") == "(5 == 0)"


def test_engine_renders_nested_arithmetic_recursively():
    wa = _adapter_with_python_rules()
    assert wa.render(Minus(a=Lit(3), b=Lit(1)), "python") == "(3 - 1)"


def test_engine_renders_if_then_else_recursively():
    wa = _adapter_with_python_rules()
    out = wa.render(
        IfThenElse(cond=Eq(a=Lit(5), b=Lit(0)), then=Lit(1),
                   other=Minus(a=Lit(3), b=Lit(1))), "python")
    assert out == "(1 if (5 == 0) else (3 - 1))"


def test_render_gap_returns_none_for_unhandled_head():
    wa = _adapter_with_python_rules()
    # Times has no rule installed -> render gap -> None
    assert wa.render(Times(items=(Lit(2), Lit(3))), "python") is None


# --- x86_64 renderer (migrated from test_x86_64_renderer_emits_...) ------

def test_x86_64_renderer_emits_recursive_factorial_assembly():
    """seed_x86_64_renderer() installs the renderer as graph data on the
    WorldAdapter; _spec_to_term converts the factorial spec to a Term
    (including the Holds recursive-call node); render() evaluates the Rust
    Render engine over the result.  Output is a plain string (not the
    {"kind","payload"} dict CuriousAgent.render_in_graph returned)."""
    wa = WorldAdapter()
    wa.seed_x86_64_renderer()
    spec = ["IfThenElse", ["Eq", "value", 0], 1,
            ["Times", "value",
             ["Holds", "factorial", ["Minus", "value", 1]]]]
    term = wa._spec_to_term(spec)
    out = wa.render(term, "x86_64")
    assert out is not None
    # Same assembly-surface assertions as the original test.
    assert "movq %rdi, %rax" in out          # subject (value)
    assert "cmpq %rcx, %rax" in out          # base-case compare
    assert "sete %al" in out
    assert "testq %rax, %rax" in out         # branch on cond
    assert "pushq %rdi" in out               # recursion save
    assert "call factorial" in out           # the recursion itself
    assert "popq %rdi" in out                # recursion restore
    assert "imulq %rcx, %rax" in out         # the multiply
    assert ".Lelse" in out
    assert ".Lend" in out


# --- parent_lang inheritance (migrated from test_parent_lang_inheritance) --

def test_parent_lang_inheritance():
    """install_language(parent_lang=...) stores a parent_lang graph edge;
    render() walks the chain at the Python boundary when the Rust engine
    finds no rule in the named language.  The child language inherits the
    base's Lit + Eq rules and renders correctly even though it has no
    rules of its own."""
    wa = WorldAdapter()
    wa.install_language("base")
    wa.install_language("child", parent_lang="base")
    wa.install_render_rule(
        "base", "Lit",
        template=Cat(items=(Slot(name="value"),)),
        binding_pattern=["value"])
    wa.install_render_rule(
        "base", "Eq",
        template=Cat(items=(
            Render(term=Slot(name="a")),
            _S(" EQ "),
            Render(term=Slot(name="b")),
        )),
        binding_pattern=["a", "b"])
    out = wa.render(Eq(a=Lit(1), b=Lit(2)), "child")
    assert out == "1 EQ 2"


# --- render-gap -> impasse / teacher resolution (migrated) ---------------

from substrate import Times  # noqa: E402

_TIMES_RULE_SPEC = {
    "language": "python", "head": "Times", "binding_pattern": ["items"],
    "template": ["Cat", ["Surface", "text", "("],
                 ["Join", ["Surface", "text", " * "], ["Slot", "items"]],
                 ["Surface", "text", ")"]],
}


def test_render_gap_spawns_impasse_with_diagnostic_attrs():
    wa = _adapter_with_python_rules()      # has Lit/Eq/Minus/IfThenElse, NOT Times
    out = wa.render_in_graph(Times(items=(Lit(2), Lit(3))), "python")
    assert out is None
    gaps = [i for i in wa.impasses()
            if wa.s.node(i)["attrs"].get("reason") == "render_gap"]
    assert len(gaps) == 1
    a = wa.s.node(gaps[0])["attrs"]
    assert a["render_gap_head"] == "Times"
    assert a["render_gap_lang"] == "python"
    assert "Times in python" in a["question"]


def test_render_gap_resolved_through_learn_from_teacher():
    wa = _adapter_with_python_rules()
    assert wa.render_in_graph(Times(items=(Lit(2), Lit(3))), "python") is None
    wa.learn_from_teacher("how do I render Times in python?",
                          {"answer": None, "learn": [{"rule": _TIMES_RULE_SPEC}]})
    out = wa.render_in_graph(Times(items=(Lit(2), Lit(3))), "python")
    assert out == {"kind": "text", "payload": "(2 * 3)"}


def test_render_gap_resolves_through_self_teacher_via_reflex():
    wa = _adapter_with_python_rules()
    wa.set_self_teacher(lambda q: {"answer": None,
                                   "learn": [{"rule": _TIMES_RULE_SPEC}]})
    assert wa.render_in_graph(Times(items=(Lit(2), Lit(3))), "python") is None
    wa.master_tick()
    wa.drain_all_taught_threads(timeout=2.0)
    out = wa.render_in_graph(Times(items=(Lit(2), Lit(3))), "python")
    assert out == {"kind": "text", "payload": "(2 * 3)"}
