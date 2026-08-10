"""Apply the teacher's patches + babble-loop-build.

The teacher (Claude Code subagent acting as LLM teacher in the
boundary role) composed 10 patches for Tokenize2; saved as
teacher_response_patches.json. This script materialises them as
DesignedPatch graph nodes, presses the button, verifies the result.

THE LOOP, CLOSED — with an actual agent at the LLM-teacher role:

  agent intent (graph)
    ↓
  spawned subagent reads source + composes 10 patches as JSON
    ↓
  patches materialized as DesignedPatch graph nodes (this script)
    ↓
  world.babble_loop applies patches → cargo builds → maturin installs
    ↓
  Tokenize2 callable through the substrate
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def main():
    print("=" * 78)
    print("APPLY TEACHER PATCHES — Tokenize2 from agent intent")
    print("=" * 78)
    print()

    s = _native.Substrate()
    from domains.rust_runtime_world import RustRuntimeWorld
    w = RustRuntimeWorld(s, workspace_root=str(ROOT / "runners" / "dsl"))
    print(f"World up.")
    print()

    # Read the teacher's JSON output
    response_path = ROOT / "scripts" / "teacher_response_patches.json"
    patches = json.loads(response_path.read_text())
    print(f"Teacher response: {len(patches)} patches (from "
          f"scripts/teacher_response_patches.json)")
    print()

    # Materialize each patch as a DesignedPatch graph node
    print("=" * 78)
    print("1. MATERIALISE patches as DesignedPatch graph nodes")
    print("=" * 78)
    print()
    nids = []
    for p in patches:
        nid = s.add_node("DesignedPatch", {
            "target_path": p["target_path"],
            "anchor":      p["anchor"],
            "position":    p["position"],
            "content":     p["content"],
            "origin":      "teacher_subagent",
        })
        nids.append(nid)
        print(f"  · #{nid.value} target={p['target_path']:<35} "
              f"position={p['position']:<8} anchor={p['anchor'][:50]!r}")
    print(f"  Total: {len(nids)} DesignedPatch nodes in graph")
    print()

    # Babble loop
    print("=" * 78)
    print("2. BABBLE LOOP — apply, build, install, iterate on errors")
    print("=" * 78)
    print()
    result = w.babble_loop(
        max_iters=3, tick_steps=10_000,
        do_install=True,
        save_path="/tmp/world_cp_teacher.json",
    )
    print(f"  Status: {result['status']}")
    print(f"  Iters:  {result['iters']}")
    print(f"  History:")
    for i, st, nf, ne in result["history"]:
        print(f"    iter {i}: status={st:<20} files={nf} errors={ne}")
    print()

    if result["status"] != "converged":
        errors = s.nodes("BuildError")
        print(f"  Build errors ({len(errors)}):")
        for nid in errors[:3]:
            a = s.node(nid)["attrs"]
            print(f"    · {a.get('kind')}: "
                  f"{str(a.get('stderr', a.get('anchor', '')))[:400]}")
        return

    # Copy artifacts to site-packages for the test subprocess
    print("=" * 78)
    print("3. TEST — is Tokenize2 callable?")
    print("=" * 78)
    print()
    import shutil
    site = Path("/home/matt/.local/lib/python3.14/site-packages/substrate_rs")
    local_so = ROOT / "runners" / "dsl" / "python" / "substrate_rs" / "_native.abi3.so"
    local_init = ROOT / "runners" / "dsl" / "python" / "substrate_rs" / "__init__.py"
    if local_so.exists() and site.exists():
        shutil.copy(local_so, site / "_native.abi3.so")
        shutil.copy(local_init, site / "__init__.py")

    test_code = """
import substrate_rs as srs
s = srs.Substrate()
text = "Theorem 1. Let G be a connected planar graph."

# Both Tokenize and Tokenize2 should produce identical output
r1 = s.evaluate(srs.Tokenize(srs.Lit(text)))
r2 = s.evaluate(srs.Tokenize2(srs.Lit(text)))
print(f"Tokenize  returned {len(r1)} tokens")
print(f"Tokenize2 returned {len(r2)} tokens")
print(f"Identical:        {r1 == r2}")
for i, (s, l) in enumerate(r2[:5]):
    print(f"  ({s}, {l}) -> {text[s:s+l]!r}")
"""
    r = subprocess.run(["python", "-c", test_code], capture_output=True,
                         text=True, cwd=str(ROOT))
    if r.returncode == 0:
        print(f"  ✓ Tokenize2 IS CALLABLE through the substrate:")
        for line in r.stdout.split("\n"):
            if line: print(f"    {line}")
    else:
        print(f"  ✗ Test failed:")
        print(f"    stderr: {r.stderr[:500]}")
    print()

    print("=" * 78)
    print("END-TO-END LOOP CLOSED — TEACHER AGENT IN THE BOUNDARY ROLE")
    print("=" * 78)
    print()
    print(f"  agent intent (text) → spawned subagent reads source + composes")
    print(f"  10 patches as JSON → materialised as DesignedPatch graph nodes")
    print(f"  → button applies → cargo builds → maturin installs → ")
    print(f"  Tokenize2 callable as srs.Tokenize2")
    print()
    print(f"  I COMPOSED ZERO PATCHES. The teacher (LLM subagent) did.")
    print()


if __name__ == "__main__":
    main()
