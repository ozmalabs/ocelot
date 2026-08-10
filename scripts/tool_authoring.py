#!/usr/bin/env python3
"""The agent AUTHORS ITS OWN TOOL BOUNDARIES — live immediately, NO rebuild.

This demonstrates the architectural payoff of the generic native ``UseTool``
Term (``runners/dsl/src/tools.rs``): because ``UseTool { tool, args }``
dispatches GENERICALLY by tool NAME to a process-global handler registry, a
NEW tool the agent didn't have before is just DATA — a typed ``ToolSpec``
graph node + a mechanically-built handler closure. Authoring a tool needs NO
Rust emission and NO recompile.

Flow:
  1. the agent SPECIFIES two NEW tools from its TYPE MODEL (validated):
       * a LIBRARY tool  isqrt:(Int)->Int   via {"module":"math","func":"isqrt"}
       * a PROCESS tool   wordcount:(Str)->Int  via `wc -w` reading stdin
  2. realize_tool wires each handler into BOTH dispatch paths (mechanical).
  3. IMMEDIATELY compose them in NATIVE UseTool Term-trees (same process):
       * Plus(UseTool("isqrt",[16]), 1) == 5
       * the process tool inside a term -> correct typed Int, proof it shelled
  4. select_tool finds the NEW tools by their typed signature (typed+external).
  5. typecheck guard: a wrong-typed arg is rejected.

Run on the already-built .so (NO rebuild):
    python scripts/tool_authoring.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import substrate_rs as srs
import substrate_rs._native as native

from domains.tool_use import (
    install_tool_use,
    select_tool,
    use_tool,
    use_tool_term,
)
from domains.tool_authoring import (
    agent_specify_tool,
    authored_tools,
    realize_tool,
)

Lit = srs.Lit
Plus = srs.Plus


def main() -> int:
    # The native registry is process-global; start clean.
    native.clear_tool_handlers()

    s = native.Substrate()
    install_tool_use(s)   # installs the TYPE MODEL + ToolSpec grammar
    print("type model + tool grammar installed.")

    # --- 1. the agent SPECIFIES two NEW tools from its TYPE MODEL -------------
    # NOTE: neither tool was registered before — the agent authors them now.
    print("\n=== the agent specifies two NEW tool boundaries ===")

    lib_spec = agent_specify_tool(
        s, name="isqrt", input_types=["Int"], output_type="Int",
        kind="library", handler={"module": "math", "func": "isqrt"},
        wrap="graph",
        doc="integer square root (math.isqrt) — agent-authored library tool")
    print("  LIBRARY  isqrt:(Int)->Int  spec:", _brief(lib_spec))
    assert lib_spec["ok"], lib_spec

    proc_spec = agent_specify_tool(
        s, name="wordcount", input_types=["Str"], output_type="Int",
        kind="process",
        handler={"argv": ["wc", "-w"], "stdin": "{0}"},
        wrap="graph",
        doc="count words in a string via `wc -w` on stdin — authored process")
    print("  PROCESS  wordcount:(Str)->Int  spec:", _brief(proc_spec))
    assert proc_spec["ok"], proc_spec

    # The type-model guard: an unknown type is REJECTED at specification.
    bad = agent_specify_tool(
        s, name="bogus", input_types=["Quaternion"], output_type="Int",
        kind="library", handler={"module": "math", "func": "isqrt"})
    print("  REJECTED unknown-type spec:", bad["error"])
    assert not bad["ok"] and "unknown type" in bad["error"]

    # --- 2. realize both -> handlers wired into BOTH dispatch paths -----------
    print("\n=== realize_tool wires the handlers (mechanical, no rebuild) ===")
    assert realize_tool(s, "isqrt", native) is True
    assert realize_tool(s, "wordcount", native) is True
    print(f"  realized; native handler count = {native.tool_handler_count()}")

    # --- 3. IMMEDIATELY compose in NATIVE UseTool Term-trees -----------------
    print("\n=== compose the JUST-AUTHORED tools in native Term-trees ===")
    fires_before = native.tool_fire_count()

    # Plus(UseTool("isqrt",[16]), 1) == isqrt(16)+1 == 4+1 == 5
    term_lib = Plus([use_tool_term("isqrt", [Lit(16)]), Lit(1)])
    print("  term:", term_lib.to_dict())
    r_lib = s.evaluate(term_lib.to_dict(), {})
    print(f"  Plus(UseTool(isqrt,16), 1) = {r_lib}   (expect 5)")
    assert r_lib == 5, f"expected 5, got {r_lib!r}"

    # The PROCESS tool inside a term -> a correct typed Int result.
    # "a b c d e" has 5 words; +10 == 15.
    term_proc = Plus([use_tool_term("wordcount", [Lit("a b c d e")]), Lit(10)])
    r_proc = s.evaluate(term_proc.to_dict(), {})
    print(f"  Plus(UseTool(wordcount,'a b c d e'), 10) = {r_proc}   (expect 15)")
    assert r_proc == 15, f"expected 15, got {r_proc!r}"

    fired = native.tool_fire_count() - fires_before
    print(f"  handlers fired from INSIDE evaluate(): {fired}   (expect 2)")
    assert fired == 2, f"expected 2 native fires, got {fired}"

    # Proof the process tool actually shelled out to `wc`.
    from domains.tool_use import _HANDLERS
    wc_handler = _HANDLERS["authored::wordcount"]
    print(f"  proof of shell-out -> last argv = {wc_handler._last_argv}, "
          f"returncode = {wc_handler._last_returncode}")
    assert wc_handler._last_argv == ["wc", "-w"]
    assert wc_handler._last_returncode == 0

    # --- 4. select_tool finds the NEW tools by typed signature ---------------
    print("\n=== select_tool finds the agent's NEW tools by typed signature ===")
    chosen_lib = select_tool(
        s, {"output_type": "Int", "op": "isqrt", "input_types": ["Int"]})
    chosen_proc = select_tool(
        s, {"output_type": "Int", "op": "wordcount", "input_types": ["Str"]})
    print(f"  need (Int<-Int, op=isqrt)     -> {chosen_lib}")
    print(f"  need (Int<-Str, op=wordcount) -> {chosen_proc}")
    assert chosen_lib == "isqrt" and chosen_proc == "wordcount"

    # The result is typed + external (via the world-adapter use_tool path).
    wa = use_tool(s, "isqrt", [144])
    print(f"  use_tool(isqrt,144) = {wa['value']}  "
          f"(value_type={wa['value_type']} -> rust_type={wa['rust_type']}, "
          f"external={wa['external']})")
    assert wa["ok"] and wa["value"] == 12 and wa["value_type"] == "Int"
    assert wa["rust_type"] == "i64" and wa["external"] is True

    # --- 5. typecheck guard on an authored tool ------------------------------
    print("\n=== typecheck guard: a wrong-typed arg is REJECTED ===")
    guarded = use_tool(s, "isqrt", ["not-an-int"])
    print(f"  use_tool(isqrt,'not-an-int') -> ok={guarded['ok']}  "
          f"error={guarded['error']}")
    assert not guarded["ok"] and "type error" in guarded["error"]

    # --- the graph view: the agent's own authored boundaries -----------------
    print("\n=== authored_tools (graph query over the agent's boundaries) ===")
    for t in authored_tools(s):
        print(f"  {t['name']}:({','.join(t['input_types'])})->{t['output_type']}"
              f"  kind={t['kind']} realized={t['realized']} "
              f"rust_out={t['rust_output_type']} external={t['external']}")

    # --- THE POINT -----------------------------------------------------------
    print("\n" + "=" * 70)
    print("THE POINT: authoring a tool needed NO Rust emission and NO rebuild.")
    print("The generic native UseTool dispatches by NAME, so a new tool is")
    print("DATA — a typed ToolSpec + a mechanically-built handler — NOT a new")
    print("primitive. The agent authored its own tool boundary from its TYPE")
    print("MODEL and it is LIVE in the same process. Lighter than an")
    print("emitter/rebuild path: tools are graph data + a mechanical handler.")
    print("=" * 70)

    print("\nALL DEMO ASSERTIONS PASSED.")
    return 0


def _brief(spec: dict) -> str:
    return (f"node={spec['spec_node']} {spec['kind']} "
            f"out={spec['output_type']}->{spec['rust_output_type']} "
            f"external={spec['external']}")


if __name__ == "__main__":
    raise SystemExit(main())
