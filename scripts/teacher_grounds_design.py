"""Teacher grounds the agent's design — babble across the boundary.

Per user: 'pursue option 3' — external LLM teacher in the babble loop.

THE LOOP

  1. Agent has a design INTENT (concept-level: 'add a tokenization
     primitive that splits strings by whitespace and returns position
     pairs').
  2. World.invoke_teacher(intent) sends the intent + existing-source
     context to an LLM (Anthropic). The LLM is the TEACHER; it
     translates concept-level intent into structural DesignedPatch
     nodes.
  3. Patches materialize in the graph.
  4. World's button applies them. cargo builds.
  5. BuildErrors feed back as graph data. Babble loop continues.

THIS SCRIPT runs the loop end-to-end with the agent's vocabulary
producing the intent + the teacher producing the patches.

ENV REQUIREMENT: ANTHROPIC_API_KEY for actual LLM call. Without it,
the script runs in dry-run mode and surfaces the prompt the world
would have sent.
"""
from __future__ import annotations

import importlib, inspect, os, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    return s


def main():
    print("=" * 78)
    print("TEACHER GROUNDS DESIGN — babble across the boundary")
    print("=" * 78)
    print()

    s = fresh_substrate()
    from domains.rust_runtime_world import RustRuntimeWorld
    w = RustRuntimeWorld(s, workspace_root=str(ROOT / "runners" / "dsl"))

    # The agent's design intent (concept-level)
    intent = (
        "Add a primitive named Tokenize2 to the substrate's DSL. "
        "It is a transducer over a string: input is a TermIdx that "
        "evaluates to Value::Str; output is a Value::Tuple containing "
        "Value::Tuple(Value::Int(start), Value::Int(len)) pairs — one "
        "per whitespace-delimited token. Position-based output because "
        "the substrate's eval has a read-only interner. The variant is "
        "called Tokenize2 to distinguish it from the existing Tokenize "
        "primitive added in commit 3e457e5. The shape mirrors Tokenize "
        "exactly; insert variant + arms after the Tokenize patches "
        "throughout."
    )
    print(f"INTENT:")
    print(f"  {intent[:200]}...")
    print()

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print(f"ANTHROPIC_API_KEY in env: {has_key}")
    print()

    # ----- 1. INVOKE TEACHER -----
    print("=" * 78)
    print("1. INVOKE TEACHER — LLM translates intent → patches")
    print("=" * 78)
    print()
    result = w.invoke_teacher(
        intent,
        model="claude-sonnet-4-6",
        dry_run=False,  # actually call if key is present
    )

    print(f"  dry_run:           {result['dry_run']}")
    print(f"  prompt length:     {len(result.get('prompt', ''))}")
    print(f"  response length:   {len(result.get('response_text', ''))}")
    print(f"  patches_created:   {len(result.get('patches_created', []))}")
    if result.get("note"):
        print(f"  note:              {result['note']}")
    print()

    if result["dry_run"]:
        print("─" * 60)
        print("PROMPT THAT WOULD HAVE BEEN SENT (first 1500 chars):")
        print("─" * 60)
        print(result["prompt"][:1500])
        print("...")
        print()
        print("=" * 78)
        print("WHAT THIS PROVED")
        print("=" * 78)
        print()
        print(f"  · invoke_teacher infrastructure works (prompt composed,")
        print(f"    context loaded, dry-run gracefully returns)")
        print(f"  · No ANTHROPIC_API_KEY → no LLM call (honest)")
        print(f"  · Set ANTHROPIC_API_KEY and re-run to grond against actual LLM")
        print()
        print(f"  THE TEACHER LOOP IS WIRED:")
        print(f"    intent (graph) → prompt (world) → LLM (boundary) →")
        print(f"    response (world) → DesignedPatch (graph) → button → cargo")
        print()
        return

    # ----- 2. INSPECT PATCHES -----
    print("=" * 78)
    print("2. PATCHES the teacher returned")
    print("=" * 78)
    print()
    for nid in result["patches_created"][:10]:
        a = s.node(nid)["attrs"]
        print(f"  · target={a['target_path']:<35} "
              f"position={a['position']:<8} "
              f"anchor={str(a['anchor'])[:50]!r}")
    print()
    print(f"  Raw response (first 800 chars):")
    print("─" * 60)
    print(result["response_text"][:800])
    print("─" * 60)
    print()

    # ----- 3. PRESS BUTTON via babble loop -----
    print("=" * 78)
    print("3. BABBLE LOOP — apply patches, cargo build, iterate on errors")
    print("=" * 78)
    print()
    loop_result = w.babble_loop(
        max_iters=3, tick_steps=10_000,
        do_install=True,
        save_path="/tmp/world_cp_teacher.json",
    )
    print(f"  Status: {loop_result['status']}")
    print(f"  Iters:  {loop_result['iters']}")
    for i, st, nf, ne in loop_result["history"]:
        print(f"    iter {i}: status={st:<20} files={nf} errors={ne}")
    print()

    if loop_result["status"] != "converged":
        errors = s.nodes("BuildError")
        print(f"  Build errors ({len(errors)}):")
        for nid in errors[:3]:
            a = s.node(nid)["attrs"]
            print(f"    · {a.get('kind')}: {str(a.get('stderr', a.get('anchor', '')))[:300]}")

    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
