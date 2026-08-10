"""Phase 6.6 (migrated) — TEACH a 4th language (Lua) entirely through the
autonomous loop, with NO CuriousAgent. The agent is the seed-booted WorldAdapter
(substrate + graph data); Lua lands purely as graph data (a Language node +
RenderRule nodes) absorbed through the self-teacher / render-gap resolution loop.

Coverage map (1:1 with tests/test_teach_lua_renderer.py):

  test_teach_lua_factorial_through_autonomous_loop
    → test_teach_lua_factorial_through_autonomous_loop_migrated
      Same flow: start with Python+Rust seeded, no Lua; iterate
      render_in_graph → drain_all_taught_threads until the render
      converges.  Asserts the rendered Lua factorial matches the
      expected idiomatic form — identical coverage to the original.

  test_lua_language_lives_purely_as_graph_data
    → test_lua_language_lives_purely_as_graph_data_migrated
      Same assertion: after the loop, a Language node exists for 'lua'
      and it carries at least 7 has_rule edges.  The mind_graph.out_edges
      call from the original is replaced by wa.inner.neighbours (the same
      graph query, different surface — no coverage reduction).

Migration notes:
  - CuriousAgent() → WorldAdapter()
  - seed_python_renderer() / seed_rust_renderer() → wa.seed_python_renderer()
    / wa.seed_rust_renderer() (new WorldAdapter methods, identical rule set)
  - set_self_teacher(fn) → wa.set_self_teacher(fn) (new method)
  - _spec_to_term(FACT_SPEC) → wa._spec_to_term(FACT_SPEC)
    (_spec_to_term now handles Holds as well as math ops)
  - render_in_graph(term, "lua") → wa.render_in_graph(term, "lua")
    (new method: walks term tree for missing heads before calling the Rust
    Render engine; on gap records a pending question for the teacher)
  - master_tick() → wa.master_tick() (already present)
  - drain_all_taught_threads(timeout) → wa.drain_all_taught_threads(timeout)
    (new method: calls the teacher synchronously per pending gap, absorbs
    rules via install_render_rule / _spec_to_renderer_term)
  - language("lua") → wa.language("lua") (new read-only query method)
  - mind_graph.out_edges(lua, "has_rule") → wa.inner.neighbours(lua, "has_rule")
    (same graph query, same coverage)

No trimmed tests. Both original tests are fully covered.
"""
from __future__ import annotations

import re

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter

FACT_SPEC = [
    "IfThenElse",
    ["Eq", "value", 0],
    1,
    ["Times", "value", ["Holds", "factorial", ["Minus", "value", 1]]],
]

# The teacher knows Lua. These are rule SPECS keyed by source-Term head.
# They land in the graph through drain_all_taught_threads's "rule" branch.
LUA_RULES: dict = {
    "Lit": {
        "language": "lua",
        "head": "Lit",
        "binding_pattern": ["value"],
        "template": ["Cat", ["Slot", "value"]],
    },
    "Var": {
        "language": "lua",
        "head": "Var",
        "binding_pattern": ["name"],
        "template": ["Cat", ["Slot", "name"]],
    },
    "Attr": {
        "language": "lua",
        "head": "Attr",
        # spec convention: Attr(Var("x"), "value") emits the literal "value"
        "binding_pattern": ["node", "key"],
        "template": ["Cat", ["Slot", "key"]],
    },
    "Eq": {
        "language": "lua",
        "head": "Eq",
        "binding_pattern": ["a", "b"],
        "template": ["Cat",
                     ["Surface", "text", "("],
                     ["Render", ["Slot", "a"]],
                     ["Surface", "text", " == "],
                     ["Render", ["Slot", "b"]],
                     ["Surface", "text", ")"]],
    },
    "Times": {
        "language": "lua",
        "head": "Times",
        "binding_pattern": ["items"],
        "template": ["Cat",
                     ["Surface", "text", "("],
                     ["Join", ["Surface", "text", " * "],
                              ["Slot", "items"]],
                     ["Surface", "text", ")"]],
    },
    "Minus": {
        "language": "lua",
        "head": "Minus",
        "binding_pattern": ["a", "b"],
        "template": ["Cat",
                     ["Surface", "text", "("],
                     ["Render", ["Slot", "a"]],
                     ["Surface", "text", " - "],
                     ["Render", ["Slot", "b"]],
                     ["Surface", "text", ")"]],
    },
    "Holds": {
        "language": "lua",
        "head": "Holds",
        "binding_pattern": ["concept", "node", "node2"],
        "template": ["Cat",
                     ["Slot", "concept"],
                     ["Surface", "text", "("],
                     ["Render", ["Slot", "node"]],
                     ["Surface", "text", ")"]],
    },
    # Lua's distinctive surface: `(if X then Y else Z end)` — different
    # from Python's `Y if X else Z` and Rust's `if X { Y } else { Z }`.
    "IfThenElse": {
        "language": "lua",
        "head": "IfThenElse",
        "binding_pattern": ["cond", "then", "other"],
        "template": ["Cat",
                     ["Surface", "text", "(if "],
                     ["Render", ["Slot", "cond"]],
                     ["Surface", "text", " then "],
                     ["Render", ["Slot", "then"]],
                     ["Surface", "text", " else "],
                     ["Render", ["Slot", "other"]],
                     ["Surface", "text", " end)"]],
    },
}


def test_teach_lua_factorial_through_autonomous_loop_migrated():
    wa = WorldAdapter()
    wa.seed_python_renderer()
    wa.seed_rust_renderer()
    # NO Lua seeded. The adapter doesn't know anything about Lua. The
    # self-teacher does.

    def lua_teacher(q: str):
        m = re.search(r"render_gap:(\w+) in lua", q)
        if m is None:
            return None
        head = m.group(1)
        spec = LUA_RULES.get(head)
        if spec is None:
            return None
        return {"answer": None, "learn": [{"rule": spec}]}

    wa.set_self_teacher(lua_teacher)

    # Iterate: render → if gap → tick → drain → try again. Bounded by
    # number of rules, so 20 iterations is generous.
    term = wa._spec_to_term(FACT_SPEC)
    rendered = None
    for _ in range(20):
        rendered = wa.render_in_graph(term, "lua")
        if rendered is not None:
            break
        wa.master_tick()
        wa.drain_all_taught_threads(timeout=2.0)

    assert rendered is not None, "Lua never converged after 20 iterations"
    # Idiomatic Lua factorial body — the substrate produced this without
    # any Python knowing what Lua looks like.
    expected = ("(if (value == 0) then 1 "
                "else (value * factorial((value - 1))) end)")
    assert rendered["payload"] == expected


def test_lua_language_lives_purely_as_graph_data_migrated():
    # After the loop runs, all the Lua state is graph-resident: one
    # Language node and a small fleet of RenderRule nodes. The substrate
    # didn't gain any new Python attributes about Lua — Lua exists ONLY
    # in the graph the adapter introspects.
    wa = WorldAdapter()
    wa.seed_python_renderer()

    def lua_teacher(q: str):
        m = re.search(r"render_gap:(\w+) in lua", q)
        if m is None:
            return None
        return {"answer": None,
                "learn": [{"rule": LUA_RULES.get(m.group(1))}]}

    wa.set_self_teacher(lua_teacher)
    term = wa._spec_to_term(FACT_SPEC)
    for _ in range(20):
        if wa.render_in_graph(term, "lua") is not None:
            break
        wa.master_tick()
        wa.drain_all_taught_threads(timeout=2.0)

    # Lua exists as a graph node now (wa.language() is the read-only query;
    # the original used a.language() backed by CuriousAgent._language_nodes).
    lua = wa.language("lua")
    assert lua is not None
    # And carries the seven rules factorial actually reaches: IfThenElse,
    # Eq, Attr, Lit, Times, Holds, Minus. (Var is in LUA_RULES but unused —
    # Attr emits the literal "value" so the renderer never descends to
    # the Var child. That's a Phase 6.4 render-gap accurate observation:
    # coverage is exactly what the source Term-tree exercises.)
    # wa.inner.neighbours replaces a.mind_graph.out_edges(lua, "has_rule"):
    # same graph query, no coverage reduction.
    rules = list(wa.inner.neighbours(lua, "has_rule"))
    assert len(rules) >= 7, f"expected at least 7 Lua rules, got {len(rules)}"
