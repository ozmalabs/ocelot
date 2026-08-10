#!/usr/bin/env python3
"""Demonstrate the NATIVE `UseTool` Term — a tool call that COMPOSES inside
an engine-evaluated Term-tree.

Today `domains/tool_use.py:use_tool` dispatches a tool at the world-adapter
boundary (Python typecheck -> run -> wrap -> record). This script proves the
NEW path: `TermNode::UseTool { tool, args }` is a first-class Term the Rust
engine evaluates — so a tool call nests INSIDE `Plus` / `IfThenElse` and the
whole tree evaluates natively, with the handler firing from inside
`evaluate()` (not at the Python boundary).

It also shows the honest framing:
  * the engine's first EFFECTFUL boundary Term (calls out to Python),
  * RE-ENTRANT (evaluate -> Python handler under the GIL),
  * errors / missing handlers degrade to a SAFE DEFAULT (Int 0), not a panic.

Run in a fresh process on the rebuilt .so:
    python scripts/use_tool_native.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import substrate_rs as srs
import substrate_rs._native as native

from domains.tool_use import (
    install_tool_use,
    register_real_tools,
    register_native_handlers,
    use_tool,
    use_tool_term,
)

Lit = srs.Lit
Plus = srs.Plus
IfThenElse = srs.IfThenElse


def main() -> int:
    # The native registry is process-global; start clean.
    native.clear_tool_handlers()

    s = srs.Substrate()
    install_tool_use(s)
    ids = register_real_tools(s)
    print(f"registered tools (graph ToolSpecs): {sorted(ids)}")

    # Bridge: register each tool's handler in the Rust UseTool registry,
    # keyed by tool name, so the NATIVE UseTool dispatches to the SAME
    # handlers `use_tool` uses.
    n_reg = register_native_handlers(s, native)
    print(f"native handlers registered: {n_reg} "
          f"(count={native.tool_handler_count()})")

    fires_before = native.tool_fire_count()

    # --- 1. UseTool composed inside Plus -------------------------------------
    # Plus(UseTool("gcd",[Lit 48, Lit 36]), Lit 1) == gcd(48,36)+1 == 12+1 == 13
    term1 = Plus([use_tool_term("gcd", [Lit(48), Lit(36)]), Lit(1)])
    print("\ncomposed term 1:", term1.to_dict())
    r1 = s.evaluate(term1, {})
    print(f"  Plus(UseTool(gcd,48,36), 1) = {r1}   (expect 13)")
    assert r1 == 13, f"expected 13, got {r1!r}"

    # --- 2. UseTool composed inside IfThenElse -------------------------------
    # IfThenElse(UseTool("is_prime",[Lit 97]), Lit 1, Lit 0) == 1 (97 is prime)
    term2 = IfThenElse(use_tool_term("is_prime", [Lit(97)]), Lit(1), Lit(0))
    print("\ncomposed term 2:", term2.to_dict())
    r2 = s.evaluate(term2, {})
    print(f"  IfThenElse(UseTool(is_prime,97), 1, 0) = {r2}   (expect 1)")
    assert r2 == 1, f"expected 1, got {r2!r}"

    # Composite (97 is prime) vs a non-prime to show the branch flips.
    term2b = IfThenElse(use_tool_term("is_prime", [Lit(98)]), Lit(1), Lit(0))
    r2b = s.evaluate(term2b, {})
    print(f"  IfThenElse(UseTool(is_prime,98), 1, 0) = {r2b}   (expect 0)")
    assert r2b == 0, f"expected 0, got {r2b!r}"

    # --- 3. nested composition: factorial inside arithmetic ------------------
    # Plus(UseTool("factorial",[Lit 5]), UseTool("gcd",[Lit 100, Lit 60]))
    #   == 120 + 20 == 140
    term3 = Plus([
        use_tool_term("factorial", [Lit(5)]),
        use_tool_term("gcd", [Lit(100), Lit(60)]),
    ])
    r3 = s.evaluate(term3, {})
    print(f"\n  Plus(factorial(5), gcd(100,60)) = {r3}   (expect 140)")
    assert r3 == 140, f"expected 140, got {r3!r}"

    fires_after = native.tool_fire_count()
    fired = fires_after - fires_before
    print(f"\nhandlers fired from INSIDE evaluate(): {fired}   (expect 5)")
    assert fired == 5, f"expected 5 native fires, got {fired}"
    print("  -> the tool ran NATIVELY (counter incremented inside the Rust "
          "evaluator), not at the world-adapter boundary.")

    # --- 4. safe-default: missing handler / handler error => Int 0 -----------
    # An unknown tool name has no registered handler -> safe default Int(0),
    # not a panic. Composed inside Plus so the tree still evaluates.
    term4 = Plus([use_tool_term("no_such_tool", [Lit(5)]), Lit(7)])
    r4 = s.evaluate(term4, {})
    print(f"\n  Plus(UseTool(no_such_tool,5), 7) = {r4}   "
          f"(expect 7: missing handler -> safe default 0)")
    assert r4 == 7, f"expected 7, got {r4!r}"

    # --- 5. the world-adapter `use_tool` STILL works (shared handlers) -------
    wa = use_tool(s, "gcd", [48, 36])
    print(f"\nworld-adapter use_tool(gcd,48,36) = {wa['value']} "
          f"(typed {wa['value_type']}->{wa['rust_type']}, external={wa['external']})")
    assert wa["ok"] and wa["value"] == 12

    # --- health: native string-returning tool composes too -------------------
    # `upper` is a subprocess tool returning a Str -> Surface(Text). It
    # composes as a UseTool, proving the str return path.
    term_upper = use_tool_term("upper", [Lit("hello")])
    r_up = s.evaluate(term_upper, {})
    print(f"\n  UseTool(upper,'hello') = {r_up!r}   (expect 'HELLO')")
    assert r_up == "HELLO", f"expected 'HELLO', got {r_up!r}"

    print("\nALL DEMO ASSERTIONS PASSED — the tool boundary is now a "
          "first-class Term the engine evaluates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
