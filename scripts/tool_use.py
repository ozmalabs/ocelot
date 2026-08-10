"""Demonstrate the typed tool-use boundary — the agent works it out.

The agent reasons natively over Term-trees and calls OUT for the rest, like
a mind using instruments. This script shows the whole boundary:

  * the TYPE model (Type ↔ rust_type, type_of_value, typecheck);
  * the agent SELECTING a tool from a typed need + calling it (gcd as an
    external typed tool -> 12, KNOWING it's external + the Rust-side type);
  * a real PROCESS tool (subprocess shell-out, with the argv shown);
  * the TEXT fallback (unstructurable output -> plain text);
  * the TYPECHECK guard (a wrong-typed arg is rejected at the boundary);
  * the payoff: the math tower used as external typed tools, no AST rewrite.

Nothing here is an agent decision in Python — ``select_tool`` is a graph
query, ``use_tool`` is a mechanical typecheck->run->wrap->record pipeline.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native

from domains import type_system as ts
from domains import tool_use as tu


def rule(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main() -> int:
    s = _native.Substrate()
    tu.install_tool_use(s)
    tool_ids = tu.register_real_tools(s)

    # --- TYPE MODEL --------------------------------------------------------
    rule("TYPE MODEL — the agent's understanding of types + their Rust form")
    print(f"{'Type':<14}{'rust_type':<12}{'kind'}")
    print("-" * 36)
    for nid in s.nodes(ts.TYPE_NODE_TYPE):
        a = s.node(nid)["attrs"]
        print(f"{a['name']:<14}{a['rust_type']:<12}{a['kind']}")

    print("\ntype_of_value + typecheck on a few values:")
    for v, expect in [(42, "Int"), (3.14, "Float"), (True, "Bool"),
                      ("hi", "Str"), (b"\x00", "Bytes"), ([1, 2, 3], "List")]:
        actual = ts.type_of_value(v)
        ok = ts.typecheck(v, expect)
        print(f"  value={v!r:<10} type_of_value={actual:<11} "
              f"rust={ts.rust_type_for(actual):<9} typecheck(_, {expect})={ok}")

    # --- AGENT SELECTS + CALLS gcd ----------------------------------------
    rule("AGENT SELECTS + CALLS — a typed need, worked out from the registry")
    need = {"output_type": "Int", "op": "gcd", "input_types": ["Int", "Int"]}
    print(f"need = {need}")
    chosen = tu.select_tool(s, need)
    print(f"agent select_tool -> {chosen!r}   (graph query over typed ToolSpecs)")

    args = [48, 36]
    print(f"typecheck args {args} against input_types ['Int','Int'] -> "
          f"{[ts.typecheck(a, 'Int') for a in args]}")
    res = tu.use_tool(s, chosen, args)
    print(f"use_tool({chosen!r}, {args}) -> {res['value']}")
    print(f"  KNOWS:  external={res['external']}   "
          f"value_type={res['value_type']}   rust_type={res['rust_type']}")
    spec = s.node(tool_ids['gcd'])['attrs']
    print(f"  ToolSpec: kind={spec['kind']} external={spec['external']} "
          f"-> the agent knows gcd is a LIBRARY tool outside the graph")

    # --- PROCESS tool ------------------------------------------------------
    rule("PROCESS tool — a real subprocess shell-out")
    pres = tu.use_tool(s, "upper", ["hi"])
    print(f"use_tool('upper', ['hi']) -> {pres['value']!r}  "
          f"(value_type={pres['value_type']}, external={pres['external']})")
    argv = tu._HANDLERS["proc_upper"]._last_argv
    print(f"  PROOF it shelled out — argv = {argv}")

    # --- TEXT fallback -----------------------------------------------------
    rule("TEXT fallback — unstructurable output wrapped as text")
    tres = tu.use_tool(s, "uname", [])
    print(f"use_tool('uname', []) -> wrap={tres['wrap']}, "
          f"value_type={tres['value_type']}, rust_type={tres['rust_type']}")
    print(f"  value (text) = {tres['value']!r}")

    # --- TYPECHECK guard ---------------------------------------------------
    rule("TYPECHECK guard — the type model makes the boundary safe")
    bad = tu.use_tool(s, "gcd", ["48", 36])   # Str where Int expected
    print(f"use_tool('gcd', ['48', 36]) -> ok={bad['ok']}")
    print(f"  REJECTED at the boundary: {bad['error']}")
    print(f"  (the call is still graph-visible — ToolCall node "
          f"{bad['call_node']} records the rejection)")

    # --- THE PAYOFF --------------------------------------------------------
    rule("THE PAYOFF — the math tower is now EXTERNAL TYPED TOOLS")
    for name, a in [("is_prime", [97]), ("factorial", [5]), ("gcd", [48, 36])]:
        r = tu.use_tool(s, name, a)
        print(f"  {name}({a}) -> {r['value']}  "
              f"[{r['value_type']}->{r['rust_type']}, external={r['external']}]")
    print(
        "\n  gcd / is_prime / factorial are used as EXTERNAL TYPED TOOLS — not\n"
        "  Python-in-the-agent awaiting an AST rewrite. The agent KNOWS they\n"
        "  are external (the `external` flag on every ToolSpec/ToolCall/\n"
        "  ToolResult) and KNOWS the types crossing the boundary (value_type\n"
        "  -> rust_type via the graph-resident type model).")

    # --- HONEST FRAMING ----------------------------------------------------
    rule("HONEST FRAMING")
    print(
        "This realizes the boundary: the agent uses external processes/\n"
        "libraries as TYPED, graph-composable tools it KNOWS are external —\n"
        "no AST->Rust synthesis. Wrapping -> typed graph data, else text.\n"
        "\n"
        "The type model is the enabler: the agent understands types + their\n"
        "Rust-side forms, which makes the boundary safe (typecheck) and\n"
        "composable. select_tool is a graph query over typed signatures;\n"
        "use_tool is typecheck -> run process/library -> wrap -> record,\n"
        "every step graph-visible.\n"
        "\n"
        "NEXT BRICK (named, not built): a NATIVE Rust `UseTool { tool, args }`\n"
        "TermNode so tool calls compose INSIDE engine-evaluated Term-trees\n"
        "(today use_tool dispatches at the world-adapter boundary). It is\n"
        "producible via the specify->emit->validate->activate pipeline already\n"
        "built — it needs the effectful-dispatch shape added to the emitter\n"
        "and a handler table exposed via PyO3.")

    # graph-visibility check: every call landed as a node.
    n_calls = len(s.nodes(tu.TOOLCALL_NODE_TYPE))
    n_specs = len(s.nodes(tu.TOOLSPEC_NODE_TYPE))
    print(f"\n[graph state] {n_specs} ToolSpec nodes, {n_calls} ToolCall nodes "
          f"(every call recorded, incl. the rejected one).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
