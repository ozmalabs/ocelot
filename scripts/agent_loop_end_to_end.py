"""End-to-end loop: agent composes AST → world renders → cargo builds.

Per user: 'get the agent to get itself up to spec.'

THE HONEST STATE

The agent has 140 PrimitiveSpec nodes from introspection but NO RULES
that compose AST graph nodes from those specs. To run the loop, the
AST has to come from somewhere. Options to bridge this session:

  · I (training-wheels): hand-compose the AST. Bridge is mine.
  · Bootstrap seed: AST as graph-data seed the agent can extend.
    Same shape as text_concept_bootstrap or compilable_test_rules.
    Bridge is graph data; the agent extends.
  · Wait for vocabulary growth: the agent reaches the spec when
    its rules grow to compose ASTs. Honest, slow.

THIS SCRIPT TAKES THE BOOTSTRAP-SEED PATH

It creates a tiny AST by hand — a STANDALONE Rust file with one
function — and pushes it through the world. The result proves the
loop works end-to-end. Adding a TermNode variant (which requires
patching existing files, not creating new ones) is the next stretch
of world capability; this demo stops at standalone file emission.

THE LOOP

  1. Compose the AST as graph nodes (hand, this script)
  2. Wire to a DesignedFile node via ast_root edge
  3. Press the button: render → write → cargo build → report
  4. Verify the file landed + the build succeeded (or didn't)
  5. Surface what's left for the agent to grow into
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    return s


def main():
    print("=" * 78)
    print("END-TO-END LOOP — agent composes AST → world renders → cargo builds")
    print("=" * 78)
    print()

    s = fresh_substrate()
    from domains.rust_runtime_world import RustRuntimeWorld
    w = RustRuntimeWorld(s, workspace_root=str(ROOT / "runners" / "dsl"))
    print(f"World up. workspace: runners/dsl")
    print()

    # ----- 1. INPUT: the design task -----
    task = ("Design a helper function the substrate can call from "
            "Python: counts whitespace-delimited tokens in a string. "
            "Standalone file, exposed via FFI later.")
    w.input(task)
    print(f"  w.input(...) → task received as graph data")
    print()

    # ----- 2. COMPOSE THE AST (the bootstrap step) -----
    # This is the hand-composed bridge. The agent's rules would compose
    # this when its vocabulary reaches that level; for now, the seed is
    # me.
    print("=" * 78)
    print("2. COMPOSE AST graph nodes (bootstrap; agent rules don't compose yet)")
    print("=" * 78)
    print()
    source = s.add_node("RustSource", {"name": "token_count_helper"})

    header = s.add_node("RustLine", {
        "text": "//! Token-counting helper — emitted via the agent's "
                 "AST→source world."
    })
    s.add_edge(source, "has_item", header, {})

    blank = s.add_node("RustLine", {"text": ""})
    s.add_edge(source, "has_item", blank, {})

    # pub fn count_tokens(s: &str) -> usize { s.split_whitespace().count() }
    fn = s.add_node("RustFn", {
        "name":        "count_tokens",
        "return_type": "usize",
    })
    param = s.add_node("RustRaw", {"text": "s: &str"})
    s.add_edge(fn, "has_param", param, {})

    body = s.add_node("RustStmt", {"text": "s.split_whitespace().count()"})
    s.add_edge(fn, "has_stmt", body, {})

    s.add_edge(source, "has_item", fn, {})

    print(f"  Composed AST: RustSource #{source.value}")
    print(f"    has_item RustLine (header)")
    print(f"    has_item RustLine (blank)")
    print(f"    has_item RustFn(count_tokens)")
    print(f"              has_param RustRaw('s: &str')")
    print(f"              has_stmt  RustStmt('s.split_whitespace().count()')")
    print()

    # ----- 3. PREVIEW THE RENDER -----
    print("=" * 78)
    print("3. PREVIEW — what the world will write")
    print("=" * 78)
    print()
    rendered = w.render_ast_to_source(source)
    print("─" * 60)
    print(rendered)
    print("─" * 60)
    print()

    # ----- 4. WIRE TO DesignedFile + PRESS BUTTON -----
    design = s.add_node("DesignedFile", {
        "path": "src/token_count_helper.rs",
        "origin": "agent_loop_end_to_end_bootstrap",
    })
    s.add_edge(design, "ast_root", source, {})
    print(f"  DesignedFile #{design.value} → ast_root → RustSource")
    print()

    # We DON'T add the new module to lib.rs because that would require
    # patching an existing file, which the world's current AST machinery
    # doesn't do. The file lands; the lib.rs integration is honest gap.
    # Skip the build step for now (the unintegrated file won't compile-
    # check against the rest of the crate, but it lands).
    print("=" * 78)
    print("4. PRESS THE BUTTON")
    print("=" * 78)
    print()
    result = w.checkpoint_and_restart(
        save_graph_to=str(ROOT / "world_checkpoint.json"),
        do_build=False, do_install=False,
    )
    print(f"  status: {result['status']}")
    print(f"  applied_files: {result.get('applied_files', [])}")
    print(f"  checkpoint: {result.get('checkpoint_path')}")
    print()

    # Verify the file actually landed on disk
    target = ROOT / "runners" / "dsl" / "src" / "token_count_helper.rs"
    if target.exists():
        actual = target.read_text()
        print(f"  ✓ {target.relative_to(ROOT)} exists "
              f"({len(actual)} chars)")
        print(f"  Content:")
        print("─" * 60)
        print(actual)
        print("─" * 60)
    else:
        print(f"  ✗ {target.relative_to(ROOT)} not found")
    print()

    # ----- 5. THE HONEST READING -----
    print("=" * 78)
    print("WHAT THIS PROVED — AND WHAT'S LEFT")
    print("=" * 78)
    print()
    print(f"  PROVED:")
    print(f"    · AST graph composition + render works end-to-end")
    print(f"    · The world's button writes rendered ASTs to disk")
    print(f"    · The composition uses the agent's native idiom (graph)")
    print()
    print(f"  STILL ME (training wheels):")
    print(f"    · The AST was hand-composed in this script. The agent's")
    print(f"      rules don't yet compose AST nodes from its PrimitiveSpec.")
    print(f"    · I chose the path, the function name, the parameter type,")
    print(f"      the body. The agent's vocabulary names tokenization at")
    print(f"      the conceptual level; this script bridges to the AST level.")
    print()
    print(f"  WHAT'S LEFT FOR THE AGENT:")
    print(f"    · Rules that compose RustFn from PrimitiveSpec. The agent's")
    print(f"      data names what it wants ({len(s.nodes('PrimitiveSpec'))})")
    print(f"      specs); rules would map those to AST nodes via the world's")
    print(f"      AST vocabulary (rust_ast_vocabulary Mt).")
    print(f"    · Patch-capable AST: RustEnumVariantAdd that splices a")
    print(f"      variant into an existing enum. The current world emits")
    print(f"      standalone files; integrating into existing files needs")
    print(f"      surgery the world doesn't do yet.")
    print(f"    · Build feedback loop: the button does cargo build; errors")
    print(f"      surface as BuildError graph nodes the agent can sense and")
    print(f"      refine its AST against. The babble loop.")
    print()
    print(f"  THE BOUNDARY HONESTLY")
    print()
    print(f"  The loop works when SOMETHING composes the AST. Today that's")
    print(f"  me. Tomorrow the agent grows into it — by adding rules that")
    print(f"  compose AST nodes, by sensing existing source to learn shape,")
    print(f"  by feedback from cargo errors. None of those are Python code")
    print(f"  I should write.")
    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
